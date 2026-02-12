#!/usr/bin/env python3
"""
Script pour supprimer les pièces jointes >1 Mo et >3 ans du dossier Archive,
en les sauvegardant localement avant suppression (API Graph Outlook 365).
"""

import os
import logging
import argparse
import requests
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
import time
from pathlib import Path
import re
from tqdm import tqdm
import base64

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('clean_archive_attachments.log'),
        logging.StreamHandler()
    ]
)

logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)

SAUVEGARDE_DIR = r"C:\Users\moran\OneDrive - eleven\Sauvegarde_pj"


def get_access_token():
    try:
        client_id = os.getenv('OUTLOOK_CLIENT_ID')
        client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        tenant_id = os.getenv('TENANT_ID')
        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("Variables d'environnement manquantes.")
        credentials = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        token = credentials.get_token("https://graph.microsoft.com/.default")
        return token.token
    except Exception as e:
        logging.error(f"Erreur token: {str(e)}")
        raise


def get_folder_id(user_id, folder_name="Archive"):
    """Trouve l'ID du dossier Archive (ou Archives)."""
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    endpoint = f"https://graph.microsoft.com/v1.0/users/{user_id}/mailFolders"
    response = requests.get(endpoint, headers=headers, timeout=60)
    if response.status_code == 200:
        for folder in response.json().get('value', []):
            if folder['displayName'].lower() in [folder_name.lower(), "archives"]:
                return folder['id']
    raise Exception(f"Dossier {folder_name} introuvable")


def get_old_large_emails(user_id, folder_id, min_size_mb=1, min_age_days=1095, 
                         limit=500):
    """Récupère les emails du dossier avec PJ >1Mo et >3 ans."""
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    cutoff_date = (datetime.now() - timedelta(days=min_age_days))
    cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    endpoint = (f"https://graph.microsoft.com/v1.0/users/{user_id}/"
               f"mailFolders/{folder_id}/messages")
    params = {
        '$top': 50,
        '$select': 'id,subject,receivedDateTime,hasAttachments',
        '$expand': 'attachments',
        '$orderby': 'receivedDateTime desc',
        '$filter': f"receivedDateTime lt {cutoff_str} and hasAttachments eq true"
    }
    all_messages = []
    next_link = None
    while True:
        retry_count = 0
        max_retries = 3
        while True:
            try:
                if next_link:
                    response = requests.get(next_link, headers=headers, timeout=60)
                else:
                    response = requests.get(
                        endpoint, headers=headers, params=params, timeout=60
                    )
                
                # Vérifier le code de statut avant de lire le contenu
                if response.status_code == 200:
                    try:
                        data = response.json()
                        for msg in data.get('value', []):
                            # Filtrer côté Python les PJ >1Mo
                            attachments = [
                                a for a in msg.get('attachments', [])
                                if (a.get('@odata.type') == '#microsoft.graph.fileAttachment' 
                                    and a.get('size', 0) > min_size_mb * 1024 * 1024)
                            ]
                            if attachments:
                                msg['attachments'] = attachments
                                all_messages.append(msg)
                        next_link = data.get('@odata.nextLink')
                        break  # sortie du retry
                    except (ValueError, requests.exceptions.JSONDecodeError) as e:
                        logging.error(f"Erreur de parsing JSON: {str(e)}")
                        if retry_count < max_retries:
                            retry_count += 1
                            wait_time = 2 ** retry_count
                            logging.warning(
                                f"Tentative {retry_count}/{max_retries} dans {wait_time}s..."
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            logging.error("Échec du parsing JSON après plusieurs tentatives")
                            break
                elif response.status_code == 504:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count
                        logging.warning(
                            f"Timeout API (504), tentative {retry_count}/{max_retries}, "
                            f"attente {wait_time}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error("Trop de timeouts API (504)")
                        break
                else:
                    logging.error(
                        f"Erreur API: {response.status_code} - {response.text}"
                    )
                    break
            
            except (requests.exceptions.ChunkedEncodingError,
                   requests.exceptions.ConnectionError,
                   requests.exceptions.Timeout) as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count
                    logging.warning(
                        f"Erreur de connexion ({type(e).__name__}), "
                        f"tentative {retry_count}/{max_retries} dans {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    # Renouveler le token en cas d'erreur de connexion
                    if retry_count == max_retries:
                        logging.info("Renouvellement du token...")
                        access_token = get_access_token()
                        headers['Authorization'] = f'Bearer {access_token}'
                    continue
                else:
                    logging.error(f"Échec après {max_retries} tentatives: {str(e)}")
                    break
            
            except Exception as e:
                logging.error(f"Erreur inattendue: {str(e)}")
                break
        
        if not next_link or len(all_messages) >= limit:
            break
    
    return all_messages[:limit]


def sanitize_filename(name: str) -> str:
    """Supprime les caractères interdits pour Windows dans un nom de fichier."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def save_attachment_locally(attachment, msg, base_dir=SAUVEGARDE_DIR):
    """Sauvegarde la pièce jointe dans un dossier local structuré."""
    subject = sanitize_filename(msg.get('subject', 'Sans objet'))[:50]
    date_str = msg.get('receivedDateTime', '').split('T')[0]
    msg_id = msg.get('id')[:8]
    att_name = sanitize_filename(attachment.get('name', 'pj'))
    att_id = attachment.get('id')[:8]
    dir_path = Path(base_dir) / f"{date_str}_{subject}_{msg_id}"
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{att_id}_{att_name}"
    content_bytes = attachment.get('contentBytes')
    if content_bytes:
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(content_bytes))
        return str(file_path)
    return None


def delete_attachment(user_id, message_id, attachment_id):
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    endpoint = (f"https://graph.microsoft.com/v1.0/users/{user_id}/"
               f"messages/{message_id}/attachments/{attachment_id}")
    response = requests.delete(endpoint, headers=headers)
    return response.status_code == 204


def process_archive_attachments(dry_run=True, min_size_mb=1, min_age_days=1095, 
                              limit=500):
    user_id = os.getenv('OUTLOOK_USER_EMAIL')
    if not user_id:
        user_id = input("Entrez l'email de l'utilisateur à traiter : ")
    folder_id = get_folder_id(user_id, folder_name="Archive")
    print(f"Recherche des emails dans le dossier Archive...")
    messages = get_old_large_emails(
        user_id, folder_id, min_size_mb, min_age_days, limit
    )
    print(
        f"{len(messages)} emails trouvés avec PJ >{min_size_mb}Mo "
        f"et >{min_age_days//365} ans."
    )
    total_pj = 0
    total_size_mb = 0
    for msg in tqdm(messages, desc="Traitement des emails"):
        subject = msg.get('subject', 'Sans objet')
        date = msg.get('receivedDateTime', '')
        for att in msg.get('attachments', []):
            total_pj += 1
            size_bytes = att.get('size', 0)
            size_kb = size_bytes // 1024
            total_size_mb += size_bytes / (1024 * 1024)
            print(
                f"Email: {subject[:40]} | Date: {date[:10]} | "
                f"PJ: {att.get('name')} ({size_kb} Ko)"
            )
            # Sauvegarde
            path = save_attachment_locally(att, msg)
            print(f"   → Sauvegardée sous: {path}")
            # Suppression
            if not dry_run:
                ok = delete_attachment(user_id, msg['id'], att['id'])
                if ok:
                    print("   ✓ Supprimée")
                else:
                    print("   ⚠ Erreur suppression")
            else:
                print("   [TEST] Serait supprimée")
    print(f"\nRÉSUMÉ: {total_pj} pièces jointes traitées.")
    print(f"Taille totale : {total_size_mb:.1f} Mo")
    print(f"Mode test: {'Oui' if dry_run else 'Non'}")


def main():
    parser = argparse.ArgumentParser(description="Nettoyage PJ Archives Outlook 365")
    parser.add_argument(
        '--execute', action='store_true', 
        help='Exécuter réellement la suppression'
    )
    parser.add_argument(
        '--limit', type=int, default=500,
        help='Nombre max d\'emails à traiter'
    )
    parser.add_argument(
        '--min-size-mb', type=float, default=1.0,
        help='Taille minimum des PJ en Mo (défaut: 1)'
    )
    parser.add_argument(
        '--min-age-days', type=int, default=1095,
        help='Âge minimum des emails en jours (défaut: 1095 = 3 ans)'
    )
    args = parser.parse_args()
    
    dry_run = not args.execute
    if not dry_run:
        print("⚠️  ATTENTION: Mode EXÉCUTION RÉELLE activé!")
        print("Les pièces jointes seront définitivement supprimées.")
        print(f"Critères : PJ >{args.min_size_mb}Mo et >{args.min_age_days//365} ans")
        confirm = input("Êtes-vous sûr? (tapez 'OUI' pour confirmer): ")
        if confirm != 'OUI':
            print("Opération annulée.")
            return
    
    process_archive_attachments(
        dry_run=dry_run, 
        limit=args.limit,
        min_size_mb=args.min_size_mb,
        min_age_days=args.min_age_days
    )

if __name__ == "__main__":
    main() 