#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les emails et leurs pièces jointes.
"""

import os
import sys
import logging
import requests
from datetime import datetime
from tqdm import tqdm
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
        logging.FileHandler('diagnostic_emails.log'),
        logging.StreamHandler()
    ]
)

# Réduire la verbosité des logs Azure
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)


def get_access_token():
    """Obtient un token d'accès pour l'API Microsoft Graph."""
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


def get_messages(user_id, folder_id='sentitems', limit=100):
    """Récupère les messages avec possibilité de recherche."""
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
            '$top': limit,
            '$select': 'id,subject,receivedDateTime,hasAttachments',
            '$expand': 'attachments',
            '$orderby': 'receivedDateTime desc'
        }
        
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
                    data = response.json()
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
                            f"Timeout API (504), nouvelle tentative dans {wait_time}s "
                            f"(tentative {retry_count}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(
                            f"Trop de timeouts API, arrêt après {max_retries} "
                            f"tentatives"
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
                        f"Timeout de connexion, nouvelle tentative dans {wait_time}s "
                        f"(tentative {retry_count}/{max_retries})"
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
                
        logging.info(f"Total des emails récupérés: {len(all_messages)}")
        return all_messages[:limit]
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def analyze_emails(messages):
    """Analyse les emails et leurs pièces jointes."""
    print("\n=== 100 PREMIERS EMAILS (objet, date, pièces jointes) ===")
    if not messages:
        print("Aucun email trouvé.")
        return
    for i, msg in enumerate(messages[:100]):
        subject = msg.get('subject', 'Sans objet')
        received_str = msg.get('receivedDateTime', '')
        has_attachments = msg.get('hasAttachments', False)
        try:
            received_date = datetime.fromisoformat(
                received_str.replace('Z', '+00:00')
            )
            date_str = received_date.strftime('%Y-%m-%d %H:%M')
        except:
            date_str = received_str
        print(f"{i+1:3d}. [{date_str}] {subject}")
        if has_attachments:
            attachments = msg.get('attachments', [])
            if attachments:
                for att in attachments:
                    att_name = att.get('name', 'Sans nom')
                    att_size = att.get('size', 0)
                    att_size_mb = att_size / (1024*1024)
                    print(f"    - {att_name} ({att_size_mb:.2f} Mo)")
            else:
                print("    - Pièces jointes non chargées")
        else:
            print("    - Aucune pièce jointe")
        print()


def search_club_data_emails(messages):
    """Recherche spécifiquement les emails avec 'Club Data' dans l'objet."""
    print("\n=== EMAILS AVEC 'CLUB DATA' DANS L'OBJET ===")
    found = 0
    for i, msg in enumerate(messages):
        subject = msg.get('subject', '')
        if 'club data' in subject.lower():
            found += 1
            received_str = msg.get('receivedDateTime', '')
            try:
                received_date = datetime.fromisoformat(
                    received_str.replace('Z', '+00:00')
                )
                date_str = received_date.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = received_str
            print(f"{i+1:3d}. [{date_str}] {subject}")
            if msg.get('hasAttachments', False):
                attachments = msg.get('attachments', [])
                if attachments:
                    for att in attachments:
                        att_name = att.get('name', 'Sans nom')
                        att_size = att.get('size', 0)
                        att_size_mb = att_size / (1024*1024)
                        print(f"    - {att_name} ({att_size_mb:.2f} Mo)")
                else:
                    print("    - Pièces jointes non chargées")
            else:
                print("    - Aucune pièce jointe")
            print()
    if found == 0:
        print("Aucun email avec 'Club Data' trouvé dans les 100 premiers emails.")


def main():
    """Fonction principale."""
    try:
        logging.info("Démarrage du diagnostic des emails")
        
        # Récupération de l'utilisateur
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        
        print("=== DIAGNOSTIC DES EMAILS ENVOYÉS ===")
        print(f"Utilisateur: {user_id}")
        
        # 1. Analyse des 100 premiers emails
        print("\n1. Récupération des 100 premiers emails...")
        messages = get_messages(user_id, limit=100)
        analyze_emails(messages)
        
        # 2. Recherche des emails "Club Data"
        print("\n2. Recherche des emails 'Club Data' dans l'objet...")
        search_club_data_emails(messages)
        
        print("\n=== DIAGNOSTIC TERMINÉ ===")
        
    except Exception as e:
        logging.error(f"Erreur fatale: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 