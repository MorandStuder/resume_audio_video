#!/usr/bin/env python3
"""
Script de nettoyage des pièces jointes des emails Outlook.
Utilise la même logique que le diagnostic qui fonctionne.
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

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('clean_sent_items.log'),
        logging.StreamHandler()
    ]
)

logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)

CONFIG_FILE = 'config_clean.json'


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_access_token():
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


def get_messages(user_id, folder_id='sentitems', limit=1000,
                older_than_days=None, subject_filter=None):
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
            '$top': 50,  # Réduit de 100 à 50 pour éviter les réponses trop volumineuses
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
                    response = requests.get(
                        next_link, headers=headers, timeout=60
                    )
                else:
                    response = requests.get(
                        endpoint, headers=headers, params=params, timeout=60
                    )
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logging.error(f"Erreur de parsing JSON: {str(e)}")
                        logging.error(
                            f"Taille de la réponse: {len(response.text)} caractères"
                        )
                        # Si la réponse est trop volumineuse, on essaie sans expand
                        if '$expand' in params:
                            logging.info(
                                "Tentative sans expansion des pièces jointes..."
                            )
                            params.pop('$expand')
                            response = requests.get(
                                endpoint, headers=headers, params=params, 
                                timeout=60
                            )
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                except json.JSONDecodeError:
                                    logging.error(
                                        "Impossible de parser la réponse JSON"
                                    )
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
                            f"Timeout API (504), nouvelle tentative dans "
                            f"{wait_time}s (tentative {retry_count}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(
                            f"Trop de timeouts API, arrêt après "
                            f"{max_retries} tentatives"
                        )
                        break
                else:
                    logging.error(f"Erreur API: {response.status_code}")
                    logging.error(f"Détail erreur API: {response.text}")
                    break
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count
                    logging.warning(
                        f"Timeout de connexion, nouvelle tentative dans "
                        f"{wait_time}s (tentative {retry_count}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(
                        f"Trop de timeouts de connexion, arrêt après "
                        f"{max_retries} tentatives"
                    )
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

def delete_attachment(user_id, message_id, attachment_id):
    try:
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        endpoint = (
            f"https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}/attachments/{attachment_id}"
        )
        response = requests.delete(endpoint, headers=headers)
        if response.status_code == 204:
            logging.info(f"Pièce jointe {attachment_id} supprimée")
            return True
        else:
            logging.error(f"Erreur lors de la suppression: {response.status_code}")
            logging.error(f"Détail erreur suppression: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la suppression: {str(e)}")
        return False

def clean_attachments(config):
    try:
        logging.info("=== DÉMARRAGE DU NETTOYAGE DES ÉLÉMENTS ENVOYÉS ===")
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        size_threshold_mb = config.get('size_threshold_mb', 10)
        age_threshold_days = config.get('age_threshold_days', 365)
        subject_filter = config.get('subject_filter', None)
        backup_attachments = config.get('backup_attachments', True)
        dry_run = config.get('dry_run', True)
        limit = config.get('limit', 1000)
        folder = config.get('folder', 'sentitems')
        all_attachments = config.get('all_attachments', False)  # Nouvelle option
        
        print(f"Dossier: {folder}")
        print(f"Seuil de taille: {size_threshold_mb} Mo")
        print(f"Âge minimum: {age_threshold_days} jours")
        print(f"Mot-clé objet: {subject_filter if subject_filter else 'Aucun'}")
        print(f"Sauvegarde des PJ: {'Oui' if backup_attachments else 'Non'}")
        print(f"Mode test: {'Oui' if dry_run else 'Non'}")
        print(f"Supprimer TOUTES les PJ: {'Oui' if all_attachments else 'Non'}")
        print()
        
        messages = get_messages(user_id, folder, limit=limit, older_than_days=age_threshold_days, subject_filter=subject_filter)
        if not messages:
            print("Aucun élément trouvé")
            return
        current_date = datetime.now()
        emails_processed = 0
        attachments_found = 0
        attachments_deleted = 0
        total_size_mb = 0
        print(f"DEBUG: Nombre d'emails à traiter: {len(messages)}")
        for msg in messages:  # Désactivé tqdm pour voir les debug
            subject = msg.get('subject', 'Sans objet')
            print(f"\nDEBUG: Sujet: {subject}")
            print(f"DEBUG: Clés: {list(msg.keys())}")
            print(f"DEBUG: hasAttachments: {msg.get('hasAttachments', False)}")
            print(f"DEBUG: attachments: {msg.get('attachments', None)}")
            received_str = msg.get('receivedDateTime', '')
            if not received_str:
                continue
            try:
                received_date = datetime.fromisoformat(received_str.replace('Z', '+00:00'))
                age_days = (current_date - received_date).days
            except Exception:
                continue
            
            # Debug forcé pour voir ce qui se passe
            print(f"\nDEBUG: Email: {subject} - Âge: {age_days} jours, Seuil: {age_threshold_days} jours")
            print(f"DEBUG: hasAttachments: {msg.get('hasAttachments', False)}")
            print(f"DEBUG: Clés disponibles: {list(msg.keys())}")
            
            # Si age_threshold_days est négatif, on traite tous les emails
            if age_threshold_days >= 0 and age_days < age_threshold_days:
                print(f"DEBUG: Email ignoré car trop récent")
                continue
            emails_processed += 1
            attachments = msg.get('attachments', [])
            print(f"DEBUG: {len(attachments)} pièces jointes trouvées")
            
            # Traiter les pièces jointes même si hasAttachments est False
            if attachments:
                attachments_found += len(attachments)
                print(f"DEBUG: Traitement de {len(attachments)} pièces jointes")
                
                for attachment in attachments:
                    if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                        name = attachment.get('name', 'Sans nom')
                        size = attachment.get('size', 0)
                        size_mb = size / (1024 * 1024)
                        print(f"DEBUG: PJ: {name} - {size_mb:.2f} Mo")
                        
                        # Si all_attachments est True, on supprime toutes les PJ
                        # Sinon, on respecte le seuil de taille
                        should_delete = all_attachments or size_mb >= size_threshold_mb
                        
                        if should_delete:
                            print(f"DEBUG: PJ {name} sera supprimée (taille: {size_mb:.2f} Mo)")
                            total_size_mb += size_mb
                            
                            if not dry_run:
                                # Supprimer la pièce jointe
                                delete_attachment(user_id, msg['id'], attachment['id'])
                                attachments_deleted += 1
                                print(f"DEBUG: PJ {name} supprimée")
                            else:
                                print(f"DEBUG: PJ {name} serait supprimée (mode test)")
                                attachments_deleted += 1
                        else:
                            print(f"DEBUG: PJ {name} conservée (taille: {size_mb:.2f} Mo < {size_threshold_mb} Mo)")
            else:
                print(f"DEBUG: Aucune pièce jointe à traiter")
        print("\n=== RÉSUMÉ DU NETTOYAGE ===")
        print(f"Emails traités: {emails_processed}")
        print(f"Pièces jointes trouvées: {attachments_found}")
        print(f"Pièces jointes supprimées: {attachments_deleted}")
        print(f"Espace libéré: {total_size_mb:.2f} Mo")
        print(f"Mode test: {'Oui' if dry_run else 'Non'}")
        print(f"Toutes les PJ supprimées: {'Oui' if all_attachments else 'Non'}")
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Nettoyer les pièces jointes des emails Outlook"
    )
    parser.add_argument('--config', type=str, help='Fichier de configuration JSON à utiliser')
    parser.add_argument('--size-threshold-mb', type=float, help='Seuil de taille en Mo pour supprimer les PJ')
    parser.add_argument('--age-threshold-days', type=int, help='Âge minimum en jours pour traiter les emails')
    parser.add_argument('--subject-filter', type=str, help='Mot-clé à rechercher dans l\'objet')
    parser.add_argument('--no-backup', action='store_true', help='Ne pas sauvegarder les PJ avant suppression')
    parser.add_argument('--execute', action='store_true', help='Exécuter réellement les suppressions (mode test par défaut)')
    parser.add_argument('--limit', type=int, help='Nombre max d\'emails à traiter (défaut 1000)')
    parser.add_argument('--folder', type=str, help='Nom du dossier à traiter (sentitems, inbox, etc.)')
    parser.add_argument('--all-attachments', action='store_true', help='Supprimer toutes les pièces jointes sans tenir compte du seuil de taille')
    args = parser.parse_args()
    config = load_config()
    if args.size_threshold_mb is not None:
        config['size_threshold_mb'] = args.size_threshold_mb
    if args.age_threshold_days is not None:
        config['age_threshold_days'] = args.age_threshold_days
    if args.subject_filter is not None:
        config['subject_filter'] = args.subject_filter
    if args.no_backup:
        config['backup_attachments'] = False
    if args.execute:
        config['dry_run'] = False
    if args.limit is not None:
        config['limit'] = args.limit
    if args.folder is not None:
        config['folder'] = args.folder
    if args.all_attachments:
        config['all_attachments'] = True
    save_config(config)
    clean_attachments(config)

if __name__ == "__main__":
    main() 