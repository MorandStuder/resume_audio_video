#!/usr/bin/env python3
"""
Script simple pour supprimer TOUTES les pièces jointes du dossier éléments envoyés.
"""

import os
import logging
import argparse
import requests
import json
from datetime import datetime
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
        logging.FileHandler('delete_all_attachments.log'),
        logging.StreamHandler()
    ]
)

logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)


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


def get_all_mail_folders(user_id, parent_id=None, parent_path=""):
    """Récupère récursivement tous les dossiers et sous-dossiers."""
    folders = []
    try:
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        if parent_id:
            endpoint = (
                f"https://graph.microsoft.com/v1.0/users/{user_id}/"
                f"mailFolders/{parent_id}/childFolders"
            )
        else:
            endpoint = f"https://graph.microsoft.com/v1.0/users/{user_id}/mailFolders"
        
        params = {'$top': 100}
        next_link = None
        
        while True:
            try:
                if next_link:
                    response = requests.get(next_link, headers=headers, timeout=60)
                else:
                    response = requests.get(endpoint, headers=headers, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    for folder in data.get('value', []):
                        folder_id = folder.get('id')
                        folder_name = folder.get('displayName', 'Sans nom')
                        full_path = (
                            f"{parent_path}/{folder_name}" if parent_path 
                            else folder_name
                        )
                        folders.append({
                            'id': folder_id, 
                            'name': folder_name,
                            'path': full_path,
                            'totalItemCount': folder.get('totalItemCount', 0),
                            'unreadItemCount': folder.get('unreadItemCount', 0)
                        })
                        
                        # Appel récursif pour les sous-dossiers
                        child_folders = get_all_mail_folders(user_id, folder_id, full_path)
                        folders.extend(child_folders)
                    
                    next_link = data.get('@odata.nextLink')
                    if not next_link:
                        break
                else:
                    logging.error(f"Erreur API dossiers: {response.status_code}")
                    break
                    
            except Exception as e:
                logging.error(f"Erreur lors de la récupération des dossiers: {str(e)}")
                break
                
    except Exception as e:
        logging.error(f"Erreur lors de la récupération récursive des dossiers: {str(e)}")
    
    return folders


def get_folder_size_stats(user_id, folder_id, folder_name):
    """Calcule la taille totale d'un dossier en analysant ses messages."""
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
            '$top': 50,
            '$select': 'size,hasAttachments',
            '$expand': 'attachments($select=size)'
        }
        
        total_size = 0
        message_count = 0
        attachment_count = 0
        attachment_size = 0
        next_link = None
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                if next_link:
                    response = requests.get(next_link, headers=headers, timeout=60)
                else:
                    response = requests.get(endpoint, headers=headers, params=params, timeout=60)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        # Tentative sans expansion des pièces jointes
                        if '$expand' in params:
                            logging.info(f"Tentative sans expansion pour {folder_name}...")
                            params.pop('$expand')
                            response = requests.get(endpoint, headers=headers, params=params, timeout=60)
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                except json.JSONDecodeError:
                                    logging.error(f"Impossible de parser la réponse pour {folder_name}")
                                    break
                            else:
                                break
                        else:
                            break
                    
                    messages = data.get('value', [])
                    for msg in messages:
                        msg_size = msg.get('size', 0)
                        total_size += msg_size
                        message_count += 1
                        
                        if msg.get('hasAttachments', False):
                            attachments = msg.get('attachments', [])
                            for att in attachments:
                                att_size = att.get('size', 0)
                                attachment_size += att_size
                                attachment_count += 1
                    
                    next_link = data.get('@odata.nextLink')
                    if not next_link:
                        break
                    retry_count = 0
                    
                elif response.status_code == 504:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count
                        logging.warning(f"Timeout API pour {folder_name}, nouvelle tentative dans {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(f"Trop de timeouts API pour {folder_name}")
                        break
                else:
                    logging.error(f"Erreur API pour {folder_name}: {response.status_code}")
                    break
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count
                    logging.warning(f"Timeout connexion pour {folder_name}, nouvelle tentative dans {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"Trop de timeouts de connexion pour {folder_name}")
                    break
            except Exception as e:
                logging.error(f"Erreur lors de l'analyse de {folder_name}: {str(e)}")
                break
        
        return {
            'message_count': message_count,
            'total_size_bytes': total_size,
            'attachment_count': attachment_count,
            'attachment_size_bytes': attachment_size
        }
        
    except Exception as e:
        logging.error(f"Erreur lors du calcul de la taille pour {folder_name}: {str(e)}")
        return {
            'message_count': 0,
            'total_size_bytes': 0,
            'attachment_count': 0,
            'attachment_size_bytes': 0
        }


def analyze_all_folders(user_id):
    """Analyse tous les dossiers de la boîte mail et exporte les résultats."""
    try:
        logging.info("=== ANALYSE DE TOUS LES DOSSIERS DE LA BOÎTE MAIL ===")
        
        # Récupération de tous les dossiers
        print("Récupération de tous les dossiers...")
        folders = get_all_mail_folders(user_id)
        
        if not folders:
            print("Aucun dossier trouvé")
            return pd.DataFrame()
        
        print(f"Trouvé {len(folders)} dossiers")
        
        # Analyse de chaque dossier
        folder_stats = []
        
        for folder in tqdm(folders, desc="Analyse des dossiers"):
            folder_id = folder['id']
            folder_name = folder['name']
            folder_path = folder['path']
            
            # Calcul des statistiques de taille
            stats = get_folder_size_stats(user_id, folder_id, folder_path)
            
            # Conversion en Mo/Go
            total_size_mb = stats['total_size_bytes'] / (1024 * 1024)
            attachment_size_mb = stats['attachment_size_bytes'] / (1024 * 1024)
            
            folder_stats.append({
                'Nom du dossier': folder_name,
                'Chemin complet': folder_path,
                'ID du dossier': folder_id,
                'Nombre d\'emails': stats['message_count'],
                'Nombre d\'emails non lus': folder.get('unreadItemCount', 0),
                'Taille totale (Mo)': round(total_size_mb, 2),
                'Taille totale (Go)': round(total_size_mb / 1024, 3),
                'Nombre de pièces jointes': stats['attachment_count'],
                'Taille des pièces jointes (Mo)': round(attachment_size_mb, 2),
                'Taille des pièces jointes (Go)': round(attachment_size_mb / 1024, 3),
                'Taille des emails sans PJ (Mo)': round(total_size_mb - attachment_size_mb, 2),
                'Date d\'analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Création du DataFrame
        df = pd.DataFrame(folder_stats)
        
        # Tri par taille décroissante
        df = df.sort_values('Taille totale (Mo)', ascending=False)
        
        # Sauvegarde dans Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"analyse_dossiers_mail_{timestamp}.xlsx"
        
        # Création d'un fichier Excel avec plusieurs onglets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Onglet principal avec tous les dossiers
            df.to_excel(writer, sheet_name='Tous les dossiers', index=False)
            
            # Onglet avec seulement les dossiers avec des pièces jointes
            df_with_attachments = df[df['Nombre de pièces jointes'] > 0].copy()
            if not df_with_attachments.empty:
                df_with_attachments.to_excel(writer, sheet_name='Dossiers avec PJ', index=False)
            
            # Onglet avec les plus gros dossiers (> 100 Mo)
            df_large = df[df['Taille totale (Mo)'] > 100].copy()
            if not df_large.empty:
                df_large.to_excel(writer, sheet_name='Dossiers > 100 Mo', index=False)
            
            # Onglet résumé
            summary_data = {
                'Métrique': [
                    'Nombre total de dossiers',
                    'Nombre de dossiers avec PJ',
                    'Nombre de dossiers > 100 Mo',
                    'Taille totale (Go)',
                    'Taille totale des PJ (Go)',
                    'Nombre total d\'emails',
                    'Nombre total de PJ',
                    'Dossier le plus volumineux',
                    'Dossier avec le plus de PJ'
                ],
                'Valeur': [
                    len(df),
                    len(df[df['Nombre de pièces jointes'] > 0]),
                    len(df[df['Taille totale (Mo)'] > 100]),
                    round(df['Taille totale (Go)'].sum(), 3),
                    round(df['Taille des pièces jointes (Go)'].sum(), 3),
                    df['Nombre d\'emails'].sum(),
                    df['Nombre de pièces jointes'].sum(),
                    df.iloc[0]['Nom du dossier'] if not df.empty else 'Aucun',
                    df.loc[df['Nombre de pièces jointes'].idxmax(), 'Nom du dossier'] if not df.empty and df['Nombre de pièces jointes'].max() > 0 else 'Aucun'
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
        
        print(f"\n=== RÉSULTATS EXPORTÉS ===")
        print(f"Fichier Excel créé: {output_file}")
        print(f"Dossiers analysés: {len(folder_stats)}")
        print(f"Taille totale: {df['Taille totale (Go)'].sum():.3f} Go")
        print(f"Taille des PJ: {df['Taille des pièces jointes (Go)'].sum():.3f} Go")
        print(f"Emails totaux: {df['Nombre d\'emails'].sum():,}")
        print(f"Pièces jointes totales: {df['Nombre de pièces jointes'].sum():,}")
        
        # Affichage des 10 plus gros dossiers
        print(f"\n=== TOP 10 DES DOSSIERS LES PLUS VOLUMINEUX ===")
        for i, (_, row) in enumerate(df.head(10).iterrows(), 1):
            print(f"{i:2d}. {row['Nom du dossier']:<30} {row['Taille totale (Mo)']:>8.1f} Mo "
                  f"({row['Nombre d\'emails']:>6} emails, {row['Nombre de pièces jointes']:>3} PJ)")
        
        return df
        
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse des dossiers: {str(e)}")
        raise


def get_messages_with_attachments(user_id, limit=1000):
    """Récupère les messages avec pièces jointes."""
    try:
        access_token = get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        endpoint = (
            f"https://graph.microsoft.com/v1.0/users/{user_id}/"
            f"mailFolders/sentitems/messages"
        )
        
        params = {
            '$top': 50,
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
                    response = requests.get(next_link, headers=headers, timeout=60)
                else:
                    response = requests.get(
                        endpoint, headers=headers, params=params, timeout=60
                    )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        logging.error("Erreur de parsing JSON")
                        break
                    
                    messages = data.get('value', [])
                    # Filtrer côté Python les messages avec pièces jointes
                    messages_with_attachments = [
                        msg for msg in messages 
                        if msg.get('hasAttachments', False) or 
                        (msg.get('attachments') and len(msg.get('attachments', [])) > 0)
                    ]
                    
                    all_messages.extend(messages_with_attachments)
                    logging.info(
                        f"Récupéré {len(messages)} emails, "
                        f"{len(messages_with_attachments)} avec PJ "
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
                            f"Timeout API, nouvelle tentative dans {wait_time}s"
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
        
        logging.info(f"Total des emails avec PJ récupérés: {len(all_messages)}")
        return all_messages[:limit]
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def delete_attachment(user_id, message_id, attachment_id):
    """Supprime une pièce jointe."""
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
        else:
            logging.error(
                f"Erreur lors de la suppression: {response.status_code}"
            )
            return False
            
    except Exception as e:
        logging.error(f"Erreur lors de la suppression: {str(e)}")
        return False


def delete_all_attachments(dry_run=True, limit=1000):
    """Supprime toutes les pièces jointes du dossier éléments envoyés."""
    try:
        logging.info("=== SUPPRESSION DE TOUTES LES PIÈCES JOINTES ===")
        
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        
        print(f"Mode test: {'Oui' if dry_run else 'Non'}")
        print(f"Limite d'emails: {limit}")
        print()
        
        # Récupérer les messages avec pièces jointes
        messages = get_messages_with_attachments(user_id, limit=limit)
        
        if not messages:
            print("Aucun email avec pièces jointes trouvé")
            return
        
        # Collecter toutes les pièces jointes avec leurs informations
        all_attachments = []
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
                        
                        all_attachments.append({
                            'message_id': msg['id'],
                            'subject': subject,
                            'attachment_id': attachment['id'],
                            'name': name,
                            'size_mb': size_mb
                        })
        
        # Trier les pièces jointes par taille décroissante
        all_attachments.sort(key=lambda x: x['size_mb'], reverse=True)
        
        print(f"=== TRI PAR TAILLE (du plus gros au plus petit) ===")
        print(f"Emails traités: {emails_processed}")
        print(f"Pièces jointes trouvées: {attachments_found}")
        print(f"Taille totale: {total_size_mb:.2f} Mo")
        print()
        
        # Traiter les pièces jointes triées
        attachments_deleted = 0
        
        for i, attachment_info in enumerate(all_attachments, 1):
            print(f"{i:3d}. Email: {attachment_info['subject']}")
            print(f"     PJ: {attachment_info['name']} ({attachment_info['size_mb']:.2f} Mo)")
            
            if not dry_run:
                if delete_attachment(user_id, attachment_info['message_id'], attachment_info['attachment_id']):
                    attachments_deleted += 1
            else:
                print(f"     [TEST] Serait supprimée")
                attachments_deleted += 1
        
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
        description="Script pour analyser les dossiers et supprimer les pièces jointes"
    )
    parser.add_argument(
        '--action',
        choices=['clean', 'analyze'],
        default='clean',
        help='Action à effectuer: clean (nettoyage PJ) ou analyze (analyse dossiers)'
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
        help='Nombre max d\'emails à traiter (défaut: 1000)'
    )
    
    args = parser.parse_args()
    
    user_id = os.getenv('OUTLOOK_USER_EMAIL')
    if not user_id:
        user_id = input("Entrez l'email de l'utilisateur à traiter : ")
    
    if args.action == 'analyze':
        print("=== ANALYSE DE TOUS LES DOSSIERS DE LA BOÎTE MAIL ===")
        print(f"Utilisateur: {user_id}")
        print("Cette opération peut prendre plusieurs minutes...")
        print()
        analyze_all_folders(user_id)
    else:
        # Mode test par défaut pour la sécurité
        dry_run = not args.execute
        
        if not dry_run:
            print("⚠️  ATTENTION: Mode EXÉCUTION RÉELLE activé!")
            print("Les pièces jointes seront définitivement supprimées.")
            confirm = input("Êtes-vous sûr? (tapez 'OUI' pour confirmer): ")
            if confirm != 'OUI':
                print("Opération annulée.")
                return
        
        delete_all_attachments(dry_run=dry_run, limit=args.limit)


if __name__ == "__main__":
    main() 