#!/usr/bin/env python3
"""
Script principal amélioré pour le nettoyage Outlook avec toutes les optimisations API apprises.
"""

import os
import logging
import argparse
import requests
import json
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
import time
import pandas as pd
from tqdm import tqdm

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('outlook_cleaner_improved.log'),
        logging.StreamHandler()
    ]
)

logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)

CONFIG_FILE = 'config_clean.json'


def load_config():
    """Charge la configuration depuis le fichier JSON."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    """Sauvegarde la configuration dans le fichier JSON."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_access_token():
    """Obtient le token d'accès à l'API Microsoft Graph."""
    try:
        client_id = os.getenv('OUTLOOK_CLIENT_ID')
        client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        tenant_id = os.getenv('TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            raise ValueError(
                "Les variables d'environnement OUTLOOK_CLIENT_ID, "
                "OUTLOOK_CLIENT_SECRET et TENANT_ID doivent être définies."
            )
        
        credentials = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        token = credentials.get_token("https://graph.microsoft.com/.default")
        return token.token
    except Exception as e:
        logging.error(f"Erreur lors de l'obtention du token: {str(e)}")
        raise


def get_messages_improved(user_id, folder_id='sentitems', limit=1000, 
                         older_than_days=None, subject_filter=None):
    """Récupère les messages avec gestion robuste des erreurs API."""
    try:
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        endpoint = (
            f"https://graph.microsoft.com/v1.0/users/{user_id}/"
            f"mailFolders/{folder_id}/messages"
        )
        
        params = {
            '$top': 50,  # Réduit pour éviter les réponses trop volumineuses
            '$select': 'id,subject,receivedDateTime,hasAttachments',
            '$expand': 'attachments',
            '$orderby': 'receivedDateTime desc'
        }
        
        if older_than_days is not None:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            params['$filter'] = f"receivedDateTime lt {cutoff_str}"
        
        all_messages = []
        next_link = None
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
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logging.error(f"Erreur de parsing JSON: {str(e)}")
                        # Tentative sans expansion des pièces jointes
                        if '$expand' in params:
                            logging.info("Tentative sans expansion des pièces jointes...")
                            params.pop('$expand')
                            response = requests.get(
                                endpoint, headers=headers, params=params, timeout=60
                            )
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                except json.JSONDecodeError:
                                    logging.error("Impossible de parser la réponse JSON")
                                    break
                            else:
                                break
                        else:
                            break
                    
                    messages = data.get('value', [])
                    all_messages.extend(messages)
                    logging.info(
                        f"Récupéré {len(messages)} emails "
                        f"(total: {len(all_messages)})"
                    )
                    
                    next_link = data.get('@odata.nextLink')
                    if not next_link or len(all_messages) >= limit:
                        break
                    retry_count = 0
                    
                elif response.status_code == 504:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count
                        logging.warning(
                            f"Timeout API (504), nouvelle tentative dans {wait_time}s"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error("Trop de timeouts API")
                        break
                else:
                    logging.error(f"Erreur API: {response.status_code}")
                    logging.error(f"Détail erreur: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count
                    logging.warning(
                        f"Timeout connexion, nouvelle tentative dans {wait_time}s"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error("Trop de timeouts de connexion")
                    break
            except Exception as e:
                logging.error(f"Erreur lors de la requête: {str(e)}")
                break
        
        # Filtrage sur l'objet côté Python si demandé
        if subject_filter:
            all_messages = [
                m for m in all_messages 
                if subject_filter.lower() in m.get('subject', '').lower()
            ]
        
        logging.info(f"Total des emails récupérés: {len(all_messages)}")
        return all_messages[:limit]
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def delete_attachment_improved(user_id, message_id, attachment_id):
    """Supprime une pièce jointe avec gestion d'erreur 412."""
    try:
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        endpoint = (
            f"https://graph.microsoft.com/v1.0/users/{user_id}/"
            f"messages/{message_id}/attachments/{attachment_id}"
        )
        
        response = requests.delete(endpoint, headers=headers)
        
        if response.status_code == 204:
            logging.info(f"Pièce jointe {attachment_id} supprimée")
            return True
        elif response.status_code == 412:
            logging.warning(f"Pièce jointe {attachment_id} déjà supprimée ou verrouillée (412)")
            return False
        else:
            logging.error(f"Erreur lors de la suppression: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Erreur lors de la suppression: {str(e)}")
        return False


def create_email_summary_improved(user_id, folder_id='sentitems', limit=1000):
    """Crée un récapitulatif des emails avec gestion robuste."""
    try:
        logging.info("=== CRÉATION DU RÉCAPITULATIF DES EMAILS ===")
        
        messages = get_messages_improved(user_id, folder_id, limit=limit)
        
        if not messages:
            logging.info("Aucun email trouvé")
            return pd.DataFrame()
        
        summary_data = []
        
        for msg in tqdm(messages, desc="Traitement des emails"):
            subject = msg.get('subject', 'Sans objet')
            received_str = msg.get('receivedDateTime', '')
            has_attachments = msg.get('hasAttachments', False)
            
            # Traitement de la date
            if received_str:
                try:
                    received_date = datetime.fromisoformat(
                        received_str.replace('Z', '+00:00')
                    )
                    received_date = received_date.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    received_date = received_str
            else:
                received_date = 'Non renseignée'
            
            # Traitement des pièces jointes
            attachment_names = []
            total_attachment_size = 0
            
            if has_attachments:
                attachments = msg.get('attachments', [])
                for attachment in attachments:
                    if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                        name = attachment.get('name', 'Sans nom')
                        size = attachment.get('size', 0)
                        attachment_names.append(name)
                        total_attachment_size += size
            
            summary_data.append({
                "Dossier": folder_id,
                "Objet": subject,
                "Date de réception": received_date,
                "A des PJ": "Oui" if has_attachments else "Non",
                "Pièces jointes": ", ".join(attachment_names),
                "Taille PJ (Mo)": round(total_attachment_size / (1024*1024), 2),
                "Nombre PJ": len(attachment_names)
            })
        
        # Création du DataFrame
        df = pd.DataFrame(summary_data)
        
        # Sauvegarde
        output_file = f"recap_emails_{folder_id}.xlsx"
        df.to_excel(output_file, index=False)
        
        logging.info(f"Récapitulatif sauvegardé dans {output_file}")
        logging.info(f"Emails traités: {len(summary_data)}")
        
        return df
        
    except Exception as e:
        logging.error(f"Erreur lors de la création du récapitulatif: {str(e)}")
        raise


def clean_attachments_improved(config):
    """Nettoyage amélioré des pièces jointes avec tri par taille."""
    try:
        logging.info("=== NETTOYAGE AMÉLIORÉ DES PIÈCES JOINTES ===")
        
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        
        size_threshold_mb = config.get('size_threshold_mb', 10)
        age_threshold_days = config.get('age_threshold_days', 365)
        subject_filter = config.get('subject_filter', None)
        dry_run = config.get('dry_run', True)
        limit = config.get('limit', 1000)
        folder = config.get('folder', 'sentitems')
        all_attachments = config.get('all_attachments', False)
        
        print(f"Dossier: {folder}")
        print(f"Seuil de taille: {size_threshold_mb} Mo")
        print(f"Âge minimum: {age_threshold_days} jours")
        print(f"Mot-clé objet: {subject_filter if subject_filter else 'Aucun'}")
        print(f"Mode test: {'Oui' if dry_run else 'Non'}")
        print(f"Supprimer TOUTES les PJ: {'Oui' if all_attachments else 'Non'}")
        print()
        
        # Récupération des messages
        messages = get_messages_improved(
            user_id, folder, limit=limit, 
            older_than_days=age_threshold_days, 
            subject_filter=subject_filter
        )
        
        if not messages:
            print("Aucun élément trouvé")
            return
        
        # Collecter toutes les pièces jointes avec leurs informations
        all_attachments_list = []
        emails_processed = 0
        attachments_found = 0
        total_size_mb = 0
        
        for msg in messages:
            subject = msg.get('subject', 'Sans objet')
            attachments = msg.get('attachments', [])
            
            if attachments:
                emails_processed += 1
                attachments_found += len(attachments)
                
                for attachment in attachments:
                    if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                        name = attachment.get('name', 'Sans nom')
                        size = attachment.get('size', 0)
                        size_mb = size / (1024 * 1024)
                        total_size_mb += size_mb
                        
                        all_attachments_list.append({
                            'message_id': msg['id'],
                            'subject': subject,
                            'attachment_id': attachment['id'],
                            'name': name,
                            'size_mb': size_mb
                        })
        
        # Trier les pièces jointes par taille décroissante
        all_attachments_list.sort(key=lambda x: x['size_mb'], reverse=True)
        
        print(f"=== TRI PAR TAILLE (du plus gros au plus petit) ===")
        print(f"Emails traités: {emails_processed}")
        print(f"Pièces jointes trouvées: {attachments_found}")
        print(f"Taille totale: {total_size_mb:.2f} Mo")
        print()
        
        # Traiter les pièces jointes triées
        attachments_deleted = 0
        
        for i, attachment_info in enumerate(all_attachments_list, 1):
            print(f"{i:3d}. Email: {attachment_info['subject']}")
            print(f"     PJ: {attachment_info['name']} ({attachment_info['size_mb']:.2f} Mo)")
            
            # Si all_attachments est True, on supprime toutes les PJ
            # Sinon, on respecte le seuil de taille
            should_delete = all_attachments or attachment_info['size_mb'] >= size_threshold_mb
            
            if should_delete:
                if not dry_run:
                    if delete_attachment_improved(user_id, attachment_info['message_id'], attachment_info['attachment_id']):
                        attachments_deleted += 1
                else:
                    print(f"     [TEST] Serait supprimée")
                    attachments_deleted += 1
            else:
                print(f"     [CONSERVÉE] Taille: {attachment_info['size_mb']:.2f} Mo < {size_threshold_mb} Mo")
        
        # Résumé
        print("\n=== RÉSUMÉ ===")
        print(f"Emails traités: {emails_processed}")
        print(f"Pièces jointes trouvées: {attachments_found}")
        print(f"Pièces jointes supprimées: {attachments_deleted}")
        print(f"Espace libéré: {total_size_mb:.2f} Mo")
        print(f"Mode test: {'Oui' if dry_run else 'Non'}")
        print(f"Tri par taille: Du plus gros au plus petit")
        
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Script principal amélioré pour le nettoyage Outlook"
    )
    parser.add_argument(
        '--action', 
        choices=['summary', 'clean', 'diagnostic'],
        default='summary',
        help='Action à effectuer (summary: récapitulatif, clean: nettoyage, diagnostic: diagnostic)'
    )
    parser.add_argument(
        '--folder', 
        type=str, 
        default='sentitems',
        help='Dossier à traiter (sentitems, inbox, etc.)'
    )
    parser.add_argument(
        '--size-threshold-mb', 
        type=float, 
        help='Seuil de taille en Mo pour supprimer les PJ'
    )
    parser.add_argument(
        '--age-threshold-days', 
        type=int, 
        help='Âge minimum en jours pour traiter les emails'
    )
    parser.add_argument(
        '--subject-filter', 
        type=str, 
        help='Mot-clé à rechercher dans l\'objet'
    )
    parser.add_argument(
        '--execute', 
        action='store_true', 
        help='Exécuter réellement les suppressions (mode test par défaut)'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=1000,
        help='Nombre max d\'emails à traiter'
    )
    parser.add_argument(
        '--all-attachments', 
        action='store_true', 
        help='Supprimer toutes les pièces jointes sans tenir compte du seuil'
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config()
    
    # Mettre à jour la configuration avec les arguments
    if args.size_threshold_mb is not None:
        config['size_threshold_mb'] = args.size_threshold_mb
    if args.age_threshold_days is not None:
        config['age_threshold_days'] = args.age_threshold_days
    if args.subject_filter is not None:
        config['subject_filter'] = args.subject_filter
    if args.execute:
        config['dry_run'] = False
    if args.limit is not None:
        config['limit'] = args.limit
    if args.folder is not None:
        config['folder'] = args.folder
    if args.all_attachments:
        config['all_attachments'] = True
    
    # Sauvegarder la configuration
    save_config(config)
    
    # Exécuter l'action demandée
    if args.action == 'summary':
        create_email_summary_improved(
            os.getenv('OUTLOOK_USER_EMAIL'), 
            args.folder, 
            args.limit
        )
    elif args.action == 'clean':
        # Mode test par défaut pour la sécurité
        dry_run = not args.execute
        
        if not dry_run:
            print("⚠️  ATTENTION: Mode EXÉCUTION RÉELLE activé!")
            print("Les pièces jointes seront définitivement supprimées.")
            confirm = input("Êtes-vous sûr? (tapez 'OUI' pour confirmer): ")
            if confirm != 'OUI':
                print("Opération annulée.")
                return
        
        clean_attachments_improved(config)
    elif args.action == 'diagnostic':
        print("=== DIAGNOSTIC ===")
        print(f"Configuration: {config}")
        print(f"Variables d'environnement:")
        print(f"  OUTLOOK_CLIENT_ID: {'✓' if os.getenv('OUTLOOK_CLIENT_ID') else '✗'}")
        print(f"  OUTLOOK_CLIENT_SECRET: {'✓' if os.getenv('OUTLOOK_CLIENT_SECRET') else '✗'}")
        print(f"  TENANT_ID: {'✓' if os.getenv('TENANT_ID') else '✗'}")
        print(f"  OUTLOOK_USER_EMAIL: {'✓' if os.getenv('OUTLOOK_USER_EMAIL') else '✗'}")


if __name__ == "__main__":
    main() 