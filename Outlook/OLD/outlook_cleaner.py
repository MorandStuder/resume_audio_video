
import os
import logging
from datetime import datetime
import pandas as pd
import sys
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient
from dotenv import load_dotenv
import time
import unicodedata
from tqdm import tqdm

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    filename='outlook_cleaner.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Ajout du logging console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Réduire la verbosité des logs Azure et MSAL
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)


def get_graph_client():
    """Initialise et retourne un client Graph avec authentification."""
    try:
        logging.info("Initialisation du client Graph")
        client_id = os.getenv('OUTLOOK_CLIENT_ID')
        client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        tenant_id = os.getenv('TENANT_ID')

        if not all([client_id, client_secret, tenant_id]):
            raise ValueError(
                "Les variables d'environnement OUTLOOK_CLIENT_ID, "
                "OUTLOOK_CLIENT_SECRET et TENANT_ID doivent être définies."
            )

        # Création des credentials
        credentials = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        # Création du client Graph
        client = GraphClient(credential=credentials)
        logging.info("Client Graph initialisé avec succès")
        return client
    except Exception as e:
        logging.error(
            f"Erreur lors de l'initialisation du client Graph: {str(e)}"
        )
        raise


def get_messages(client, user_id, folder_id='inbox', limit=1000):
    """Récupère les messages d'un dossier pour un utilisateur donné."""
    try:
        endpoint = f"/users/{user_id}/mailFolders/{folder_id}/messages"
        params = {
            '$top': limit,
            '$select': 'subject,receivedDateTime,hasAttachments',
            '$expand': 'attachments'
        }
        all_messages = []
        next_link = None
        
        while True:
            if next_link:
                response = client.get(next_link)
            else:
                response = client.get(endpoint, params=params)
                
            if response.status_code == 200:
                messages = response.json().get('value', [])
                all_messages.extend(messages)
                next_link = response.json().get('@odata.nextLink')
                if not next_link:
                    break
            else:
                logging.error(f"Erreur API: {response.status_code}")
                logging.error(f"Détail erreur API: {response.text}")
                break
                
        return all_messages
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def clean_excel_name(name):
    """Nettoie un nom pour qu'il soit compatible avec Excel."""
    if not name:
        return "Sans nom"
    # Remplace les caractères invalides par des underscores
    invalid_chars = ['\\', '/', '?', '*', ':', '[', ']']
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Limite la longueur à 31 caractères (limite Excel)
    return name[:31]


def create_email_summary(client, user_id):
    """Crée un tableau récapitulatif des emails avec leurs pièces jointes."""
    try:
        logging.info("Création du récapitulatif des emails")
        summary_data = []
        start_time = time.time()

        # Récupération des messages de la boîte de réception
        messages = get_messages(client, user_id)
        logging.debug(f"Nombre d'emails trouvés: {len(messages)}")

        # Affichage de la progression
        for msg in tqdm(messages, desc="Traitement des emails", unit="email"):
            subject = clean_excel_name(msg.get('subject', 'Sans objet'))
            received_str = msg.get('receivedDateTime', '')
            if received_str:
                try:
                    dt = datetime.fromisoformat(
                        received_str.replace('Z', '+00:00')
                    )
                    received_date = dt.replace(tzinfo=None)
                except Exception:
                    received_date = received_str
            else:
                received_date = 'Non renseignée'
            has_attachments = msg.get('hasAttachments', False)

            attachment_names = []
            total_attachment_size = 0

            if has_attachments:
                attachments = msg.get('attachments', [])
                for attachment in attachments:
                    name = clean_excel_name(
                        attachment.get('name', 'Nom inconnu')
                    )
                    size = attachment.get('size', 0)
                    attachment_names.append(name)
                    total_attachment_size += size

            summary_data.append({
                "Dossier": "Boîte de réception",
                "Objet": subject,
                "Date de réception": received_date,
                "A des PJ": "Oui" if has_attachments else "Non",
                "Pièces jointes": ", ".join(attachment_names),
                "Taille PJ (Mo)": round(total_attachment_size / (1024*1024), 2)
            })

        # Création du DataFrame et sauvegarde
        df = pd.DataFrame(summary_data)
        output_file = "recap_emails.xlsx"
        temp_file = "recap_emails_temp.xlsx"

        try:
            df.to_excel(temp_file, index=False)
            if os.path.exists(output_file):
                os.remove(output_file)
            os.rename(temp_file, output_file)
            elapsed_time = time.time() - start_time
            logging.info(
                f"Récapitulatif sauvegardé dans {output_file} "
                f"en {elapsed_time:.1f} secondes"
            )
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
            raise

        return df
    except Exception as e:
        logging.error(f"Erreur lors de la création du récapitulatif: {str(e)}")
        raise


def delete_attachment(client, user_id, message_id, attachment_id):
    """Supprime une pièce jointe."""
    try:
        endpoint = (
            f"/users/{user_id}/messages/{message_id}/"
            f"attachments/{attachment_id}"
        )
        response = client.delete(endpoint)
        if response.status_code == 204:
            logging.info(f"Pièce jointe {attachment_id} supprimée")
            return True
        else:
            logging.error(
                f"Erreur lors de la suppression: {response.status_code}"
            )
            logging.error(f"Détail erreur suppression: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la suppression: {str(e)}")
        return False


def get_mail_folders(client, user_id):
    """Récupère tous les dossiers de la boîte mail."""
    try:
        endpoint = f"/users/{user_id}/mailFolders"
        response = client.get(endpoint)
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            logging.error(f"Erreur API: {response.status_code}")
            logging.error(f"Détail erreur API: {response.text}")
            return []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des dossiers: {str(e)}")
        return []


def get_folder_stats(client, user_id, folder_id):
    """Récupère les statistiques d'un dossier."""
    try:
        endpoint = f"/users/{user_id}/mailFolders/{folder_id}"
        params = {
            '$select': 'displayName,totalItemCount,unreadItemCount'
        }
        response = client.get(endpoint, params=params)
        if response.status_code != 200:
            logging.error(
                f"Réponse API NOK pour {folder_id}: "
                f"{response.status_code} {response.text}"
            )
            return 0, 0
        folder = response.json()
        logging.debug(f"Réponse brute dossier {folder_id}: {folder}")
        nb_emails = folder.get('totalItemCount', 0)
        
        # Calcul de la taille totale
        total_size = 0
        messages_endpoint = (
            f"/users/{user_id}/mailFolders/{folder_id}/messages"
        )
        params = {
            '$top': 100,
            '$select': 'size,hasAttachments',
            '$expand': 'attachments($select=size)'
        }
        next_link = None
        count = 0
        while True:
            if next_link:
                response = client.get(next_link)
            else:
                response = client.get(messages_endpoint, params=params)
            if response.status_code != 200:
                break
            data = response.json()
            for msg in data.get('value', []):
                msg_size = msg.get('size', 0)
                total_size += msg_size
                if msg.get('hasAttachments', False):
                    attachments = msg.get('attachments', [])
                    for att in attachments:
                        total_size += att.get('size', 0)
                count += 1
            next_link = data.get('@odata.nextLink')
            if not next_link:
                break
        return nb_emails, total_size
    except Exception as e:
        logging.error(
            "Erreur lors de la récupération des stats du dossier: "
            f"{str(e)}"
        )
        return 0, 0


def get_all_mail_folders(client, user_id, parent_id=None, parent_path=""):
    """Récupère récursivement tous les dossiers et sous-dossiers."""
    folders = []
    try:
        if parent_id:
            endpoint = f"/users/{user_id}/mailFolders/{parent_id}/childFolders"
        else:
            endpoint = f"/users/{user_id}/mailFolders"
        params = {'$top': 100}
        next_link = None
        while True:
            if next_link:
                response = client.get(next_link)
            else:
                response = client.get(endpoint, params=params)
            if response.status_code != 200:
                logging.error(
                    f"Erreur API dossiers: {response.status_code} "
                    f"{response.text}"
                )
                break
            for folder in response.json().get('value', []):
                folder_id = folder.get('id')
                folder_name = folder.get('displayName', 'Sans nom')
                full_path = (
                    f"{parent_path}/{folder_name}" if parent_path 
                    else folder_name
                )
                folders.append({'id': folder_id, 'path': full_path})
                # Appel récursif pour les sous-dossiers
                folders.extend(
                    get_all_mail_folders(client, user_id, folder_id, full_path)
                )
            next_link = response.json().get('@odata.nextLink')
            if not next_link:
                break
    except Exception as e:
        logging.error(
            f"Erreur lors de la récupération récursive des dossiers: "
            f"{str(e)}"
        )
    return folders


def create_config_file(client, user_id):
    """Crée ou met à jour le fichier Excel de configuration."""
    try:
        output_file = "config_nettoyage.xlsx"
        temp_file = "config_nettoyage_temp.xlsx"
        start_time = time.time()
        
        # Récupération des dossiers
        logging.info("Récupération des dossiers")
        folders = get_all_mail_folders(client, user_id)
        
        # Création du récapitulatif des emails pour avoir les tailles
        logging.info("Création du récapitulatif des emails")
        recap_df = create_email_summary(client, user_id)
        
        # Calcul des statistiques par dossier
        new_config_data = []
        for folder in tqdm(
            folders, desc="Calcul des statistiques", unit="dossier"
        ):
            folder_path = folder['path']
            # Filtrage des emails du dossier dans le récapitulatif
            folder_emails = recap_df[recap_df['Dossier'] == folder_path]
            nb_emails = len(folder_emails)
            total_size = (
                folder_emails['Taille PJ (Mo)'].sum() * (1024*1024)
            )  # Conversion en octets
            
            new_config_data.append({
                "Nom du dossier": folder_path,
                "Nombre d'emails": nb_emails,
                "Taille totale (Go)": round(total_size / (1024*1024*1024), 2),
                "Action": "",  # Sera mis à jour avec les valeurs existantes
                "Seuil Taille PJ (Mo)": "",  # Sera mis à jour
                "Seuil Âge (années)": ""  # Sera mis à jour
            })

        # Création du nouveau DataFrame
        new_df = pd.DataFrame(new_config_data)
        
        # Si le fichier existe, on récupère les règles existantes
        if os.path.exists(output_file):
            try:
                existing_df = pd.read_excel(output_file)
                # Mise à jour des règles pour les dossiers existants
                for idx, row in tqdm(
                    new_df.iterrows(), 
                    desc="Mise à jour des règles", 
                    total=len(new_df)
                ):
                    folder_name = row["Nom du dossier"]
                    existing_row = existing_df[
                        existing_df["Nom du dossier"] == folder_name
                    ]
                    if not existing_row.empty:
                        new_df.at[idx, "Action"] = existing_row.iloc[0]["Action"]
                        new_df.at[idx, "Seuil Taille PJ (Mo)"] = (
                            existing_row.iloc[0]["Seuil Taille PJ (Mo)"]
                        )
                        new_df.at[idx, "Seuil Âge (années)"] = (
                            existing_row.iloc[0]["Seuil Âge (années)"]
                        )
                print(f"\nMise à jour des statistiques dans {output_file}")
            except Exception as e:
                logging.warning(
                    f"Impossible de lire le fichier existant: {str(e)}"
                )
                print(f"\nCréation d'un nouveau fichier {output_file}")
        else:
            print(f"\nCréation du fichier {output_file}")

        # Sauvegarde du fichier
        while True:
            try:
                new_df.to_excel(temp_file, index=False)
                if os.path.exists(output_file):
                    os.remove(output_file)
                os.rename(temp_file, output_file)
                elapsed_time = time.time() - start_time
                logging.info(
                    f"Fichier de configuration sauvegardé dans {output_file} "
                    f"en {elapsed_time:.1f} secondes"
                )
                break
            except PermissionError as e:
                if hasattr(e, 'winerror') and e.winerror == 32:
                    print(
                        f"\nLe fichier {output_file} est ouvert. "
                        f"Veuillez le fermer puis appuyez sur Entrée "
                        f"pour réessayer, ou Ctrl+C pour annuler."
                    )
                    input()
                    continue
                else:
                    logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
                    raise
            except Exception as e:
                logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
                raise

        return new_df
    except Exception as e:
        logging.error(
            f"Erreur lors de la création/mise à jour du fichier "
            f"de configuration: {str(e)}"
        )
        raise


def read_config_file():
    """Lit le fichier de configuration Excel et retourne un DataFrame."""
    try:
        config_file = "config_nettoyage.xlsx"
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Le fichier {config_file} n'existe pas")
        
        df = pd.read_excel(config_file)
        required_columns = [
            "Nom du dossier", "Action", "Seuil Taille PJ (Mo)", 
            "Seuil Âge (années)"
        ]
        missing_columns = [
            col for col in required_columns if col not in df.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Colonnes manquantes dans le fichier de configuration: "
                f"{missing_columns}"
            )
        
        # Normalisation de la colonne Action
        def normalize_action(val):
            if pd.isna(val):
                return ""
            val_norm = str(val).strip().lower()
            val_norm = ''.join(
                c for c in unicodedata.normalize('NFD', val_norm)
                if unicodedata.category(c) != 'Mn'
            )
            if "mail" in val_norm or "email" in val_norm:
                return "Email"
            if "pj" in val_norm or "piece" in val_norm:
                return "Pièce jointe"
            return val
        df["Action"] = df["Action"].apply(normalize_action)

        # Conversion automatique des virgules en points et en float
        seuil_cols = ["Seuil Taille PJ (Mo)", "Seuil Âge (années)"]
        for col in seuil_cols:
            def convert_seuil(val):
                if pd.isna(val) or val == "":
                    return None
                try:
                    return float(str(val).replace(",", "."))
                except Exception:
                    logging.warning(
                        f"Valeur non numérique dans '{col}': {val}"
                    )
                    return None
            df[col] = df[col].apply(convert_seuil)
        return df
    except Exception as e:
        logging.error(
            f"Erreur lors de la lecture du fichier de configuration: "
            f"{str(e)}"
        )
        raise


def delete_message(client, user_id, message_id):
    """Supprime un email."""
    try:
        endpoint = f"/users/{user_id}/messages/{message_id}"
        response = client.delete(endpoint)
        if response.status_code == 204:
            logging.info(f"Email {message_id} supprimé")
            return True
        else:
            logging.error(
                f"Erreur lors de la suppression: {response.status_code}"
            )
            logging.error(f"Détail erreur suppression: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la suppression: {str(e)}")
        return False


def download_attachment(client, user_id, message_id, attachment, folder_name):
    """Télécharge et sauvegarde une pièce jointe."""
    try:
        # Création du dossier de sauvegarde s'il n'existe pas
        backup_dir = "sauvegardes_pj"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Création du sous-dossier pour le dossier mail
        folder_backup_dir = os.path.join(
            backup_dir, clean_excel_name(folder_name)
        )
        if not os.path.exists(folder_backup_dir):
            os.makedirs(folder_backup_dir)
        
        # Récupération de la pièce jointe
        endpoint = (
            f"/users/{user_id}/messages/{message_id}/"
            f"attachments/{attachment['id']}/$value"
        )
        response = client.get(endpoint)
        
        if response.status_code == 200:
            # Construction du chemin de sauvegarde
            filename = clean_excel_name(attachment.get('name', 'sans_nom'))
            backup_path = os.path.join(folder_backup_dir, filename)
            
            # Sauvegarde du fichier
            with open(backup_path, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Pièce jointe sauvegardée: {backup_path}")
            return True
        else:
            logging.error(
                f"Erreur lors du téléchargement: {response.status_code}"
            )
            logging.error(f"Détail erreur: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
        return False


def apply_cleaning_rules(client, user_id, folder_id, folder_name, 
                        action, size_threshold, age_threshold):
    """Applique les règles de nettoyage pour un dossier donné."""
    try:
        logging.info(
            f"Application des règles de nettoyage pour le dossier: "
            f"{folder_name}"
        )
        start_time = time.time()
        
        # Récupération des messages du dossier
        messages = get_messages(client, user_id, folder_id)
        if not messages:
            logging.info(f"Aucun message trouvé dans le dossier {folder_name}")
            return
        
        current_date = datetime.now()
        cleaned_count = 0
        
        for msg in tqdm(
                messages, desc=f"Nettoyage de {folder_name}", unit="email"
        ):
            # Vérification de l'âge
            received_str = msg.get('receivedDateTime', '')
            if not received_str:
                continue
                
            try:
                received_date = datetime.fromisoformat(
                    received_str.replace('Z', '+00:00')
                )
                age_years = (current_date - received_date).days / 365
            except Exception:
                continue
            
            # Si l'email est plus récent que le seuil, on passe au suivant
            if age_years < age_threshold:
                continue
            
            if action == "Pièce jointe":
                # Nettoyage des pièces jointes
                if msg.get('hasAttachments', False):
                    attachments = msg.get('attachments', [])
                    for attachment in attachments:
                        size_mb = attachment.get('size', 0) / (1024*1024)
                        if size_mb > size_threshold:
                            # Sauvegarde avant suppression
                            download_attachment(
                                client, user_id, msg['id'], 
                                attachment, folder_name
                            )
                            # SUPPRESSION DÉSACTIVÉE POUR TEST
                            # if delete_attachment(client, user_id, msg['id'], 
                            #                    attachment['id']):
                            #     cleaned_count += 1
                            #     logging.info(
                            #         f"Pièce jointe supprimée: "
                            #         f"{attachment.get('name')} "
                            #         f"({size_mb:.2f} Mo) dans {folder_name}"
                            #     )
            
            elif action == "Email":
                # Nettoyage des emails
                total_size = 0
                if msg.get('hasAttachments', False):
                    attachments = msg.get('attachments', [])
                    """ Sauvegarde des pièces jointes avant suppression
                    for attachment in attachments:
                        download_attachment(
                            client, user_id, msg['id'], 
                            attachment, folder_name
                        )"""
                    total_size = sum(att.get('size', 0) for att in attachments)
                
                size_mb = total_size / (1024*1024)
                if size_mb > size_threshold:
                    # SUPPRESSION DÉSACTIVÉE POUR TEST
                    # if delete_message(client, user_id, msg['id']):
                    #     cleaned_count += 1
                    #     logging.info(
                    #         f"Email supprimé: {msg.get('subject')} "
                    #         f"({size_mb:.2f} Mo) dans {folder_name}"
                    #     )
                    pass
        
        elapsed_time = time.time() - start_time
        logging.info(
            f"Nettoyage terminé pour {folder_name}: {cleaned_count} "
            f"éléments nettoyés en {elapsed_time:.1f} secondes"
        )
        
    except Exception as e:
        logging.error(
            f"Erreur lors du nettoyage du dossier {folder_name}: {str(e)}"
        )


def calculate_cleaning_stats(client, user_id, folder_id, folder_name, 
                           action, size_threshold, age_threshold):
    """Calcule les statistiques de nettoyage pour un dossier."""
    try:
        messages = get_messages(client, user_id, folder_id)
        if not messages:
            return 0, 0, 0  # emails, pièces jointes, taille totale
        
        current_date = datetime.now()
        emails_to_delete = 0
        attachments_to_delete = 0
        total_size_mb = 0
        
        for msg in messages:
            # Vérification de l'âge
            received_str = msg.get('receivedDateTime', '')
            if not received_str:
                continue
                
            try:
                received_date = datetime.fromisoformat(
                    received_str.replace('Z', '+00:00')
                )
                age_years = (current_date - received_date).days / 365
            except Exception:
                continue
            
            if age_years < age_threshold:
                continue
            
            if action == "Pièce jointe":
                if msg.get('hasAttachments', False):
                    attachments = msg.get('attachments', [])
                    for attachment in attachments:
                        size_mb = attachment.get('size', 0) / (1024*1024)
                        if size_mb > size_threshold:
                            attachments_to_delete += 1
                            total_size_mb += size_mb
            
            elif action == "Email":
                total_size = 0
                if msg.get('hasAttachments', False):
                    attachments = msg.get('attachments', [])
                    total_size = sum(att.get('size', 0) for att in attachments)
                
                size_mb = total_size / (1024*1024)
                if size_mb > size_threshold:
                    emails_to_delete += 1
                    total_size_mb += size_mb
        
        return emails_to_delete, attachments_to_delete, total_size_mb
        
    except Exception as e:
        logging.error(
            f"Erreur lors du calcul des stats pour {folder_name}: {str(e)}"
        )
        return 0, 0, 0


def clean_sent_items_attachments(size_threshold_mb=10, age_threshold_years=2, 
                                backup_attachments=True, dry_run=True):
    """
    Fonction autonome pour supprimer les pièces jointes des éléments envoyés.
    
    Args:
        size_threshold_mb (float): Seuil de taille en Mo pour supprimer les PJ
        age_threshold_years (float): Âge minimum en années pour traiter les emails
        backup_attachments (bool): Sauvegarder les PJ avant suppression
        dry_run (bool): Mode test (pas de suppression réelle)
    
    Returns:
        dict: Statistiques du nettoyage
    """
    try:
        logging.info("Démarrage du nettoyage des éléments envoyés")
        
        # Initialisation du client Graph
        client = get_graph_client()
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        
        # Récupération du dossier des éléments envoyés
        sent_folder_id = 'sentitems'
        logging.info("Récupération des éléments envoyés")
        
        # Récupération des messages du dossier sentitems
        messages = get_messages(client, user_id, sent_folder_id)
        if not messages:
            logging.info("Aucun élément envoyé trouvé")
            return {
                'emails_processed': 0,
                'attachments_found': 0,
                'attachments_deleted': 0,
                'total_size_mb': 0,
                'dry_run': dry_run
            }
        
        current_date = datetime.now()
        emails_processed = 0
        attachments_found = 0
        attachments_deleted = 0
        total_size_mb = 0
        
        logging.info(
            f"Traitement de {len(messages)} éléments envoyés "
            f"(seuil: {size_threshold_mb} Mo, âge: {age_threshold_years} ans)"
        )
        
        # Traitement des messages
        for msg in tqdm(
                messages, desc="Nettoyage des éléments envoyés", 
                unit="email"
        ):
            # Vérification de l'âge
            received_str = msg.get('receivedDateTime', '')
            if not received_str:
                continue
                
            try:
                received_date = datetime.fromisoformat(
                    received_str.replace('Z', '+00:00')
                )
                age_years = (current_date - received_date).days / 365
            except Exception:
                continue
            
            # Si l'email est plus récent que le seuil, on passe au suivant
            if age_years < age_threshold_years:
                continue
            
            emails_processed += 1
            
            # Traitement des pièces jointes
            if msg.get('hasAttachments', False):
                attachments = msg.get('attachments', [])
                for attachment in attachments:
                    size_mb = attachment.get('size', 0) / (1024*1024)
                    attachments_found += 1
                    
                    if size_mb > size_threshold_mb:
                        total_size_mb += size_mb
                        
                        # Sauvegarde avant suppression si demandé
                        if backup_attachments:
                            download_attachment(
                                client, user_id, msg['id'], 
                                attachment, "Elements_envoyes"
                            )
                        
                        # Suppression de la pièce jointe
                        if not dry_run:
                            if delete_attachment(
                                    client, user_id, msg['id'], attachment['id']
                            ):
                                attachments_deleted += 1
                                logging.info(
                                    f"Pièce jointe supprimée: "
                                    f"{attachment.get('name')} "
                                    f"({size_mb:.2f} Mo) - "
                                    f"Email: {msg.get('subject', 'Sans objet')}"
                                )
                        else:
                            attachments_deleted += 1
                            logging.info(
                                f"[DRY RUN] Pièce jointe à supprimer: "
                                f"{attachment.get('name')} "
                                f"({size_mb:.2f} Mo) - "
                                f"Email: {msg.get('subject', 'Sans objet')}"
                            )
        
        # Résumé des statistiques
        stats = {
            'emails_processed': emails_processed,
            'attachments_found': attachments_found,
            'attachments_deleted': attachments_deleted,
            'total_size_mb': total_size_mb,
            'dry_run': dry_run
        }
        
        logging.info("=== RÉSUMÉ DU NETTOYAGE ===")
        logging.info(f"Emails traités: {emails_processed}")
        logging.info(f"Pièces jointes trouvées: {attachments_found}")
        logging.info(f"Pièces jointes supprimées: {attachments_deleted}")
        logging.info(f"Espace libéré: {total_size_mb:.2f} Mo")
        logging.info(f"Mode test: {'Oui' if dry_run else 'Non'}")
        
        return stats
        
    except Exception as e:
        logging.error(
            f"Erreur lors du nettoyage des éléments envoyés: {str(e)}"
        )
        raise


def main():
    """Fonction principale."""
    try:
        logging.info("Démarrage du programme")
        client = get_graph_client()
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")

        # Création du récapitulatif des emails
        recap_df = create_email_summary(client, user_id)
        print(
            f"\nRécapitulatif des emails créé ({len(recap_df)} emails trouvés). "
            "Veuillez vérifier le fichier recap_emails.xlsx"
        )

        # Création du fichier de configuration
        config_df = create_config_file(client, user_id)
        print(
            f"\nFichier de configuration créé ({len(config_df)} dossiers trouvés). "
            "Veuillez configurer les règles de nettoyage dans "
            "config_nettoyage.xlsx"
        )

        # Lecture du fichier de configuration
        config_df = read_config_file()
        print("\nAperçu du DataFrame de configuration :")
        print(config_df.head(30))
        print("\nTypes des colonnes :")
        print(config_df.dtypes)

        # Demande de confirmation pour le nettoyage
        if input("\nVoulez-vous procéder au nettoyage ? (o/n): ").lower() == 'o':
            # Calcul des statistiques de nettoyage
            total_emails = 0
            total_attachments = 0
            total_size = 0
            folder_stats = []
            
            for _, row in config_df.iterrows():
                folder_name = row["Nom du dossier"]
                action = row["Action"]
                size_threshold = row["Seuil Taille PJ (Mo)"]
                age_threshold = row["Seuil Âge (années)"]
                
                if (pd.isna(action) or pd.isna(size_threshold) or 
                        pd.isna(age_threshold)):
                    continue
                
                folders = get_all_mail_folders(client, user_id)
                folder_id = next(
                    (f['id'] for f in folders if f['path'] == folder_name), 
                    None
                )
                
                if folder_id:
                    emails, attachments, size = calculate_cleaning_stats(
                        client, user_id, folder_id, folder_name,
                        action, size_threshold, age_threshold
                    )
                    if emails > 0 or attachments > 0:
                        folder_stats.append({
                            'folder': folder_name,
                            'action': action,
                            'emails': emails,
                            'attachments': attachments,
                            'size': size
                        })
                        total_emails += emails
                        total_attachments += attachments
                        total_size += size
            
            # Affichage des statistiques et demande de confirmation
            if folder_stats:
                print("\nRésumé des actions de nettoyage à effectuer :")
                print("-" * 80)
                for stat in folder_stats:
                    if stat['action'] == "Email":
                        print(f"Dossier {stat['folder']}:")
                        print(f"  - {stat['emails']} emails à supprimer "
                              f"({stat['size']:.2f} Mo)")
                    else:
                        print(f"Dossier {stat['folder']}:")
                        print(f"  - {stat['attachments']} pièces jointes "
                              f"à supprimer ({stat['size']:.2f} Mo)")
                print("-" * 80)
                print(f"Total : {total_emails} emails et {total_attachments} "
                      f"pièces jointes à supprimer ({total_size:.2f} Mo)")
                
                if input("\nConfirmez-vous ces suppressions ? (o/n): ").lower() == 'o':
                    # Application des règles de nettoyage
                    for _, row in config_df.iterrows():
                        folder_name = row["Nom du dossier"]
                        action = row["Action"]
                        size_threshold = row["Seuil Taille PJ (Mo)"]
                        age_threshold = row["Seuil Âge (années)"]
                        
                        if (pd.isna(action) or pd.isna(size_threshold) or 
                                pd.isna(age_threshold)):
                            logging.warning(
                                f"Configuration incomplète pour {folder_name}"
                            )
                            continue
                        
                        folders = get_all_mail_folders(client, user_id)
                        folder_id = next(
                            (f['id'] for f in folders if f['path'] == folder_name), 
                            None
                        )
                        
                        if folder_id:
                            apply_cleaning_rules(
                                client, user_id, folder_id, folder_name,
                                action, size_threshold, age_threshold
                            )
                        else:
                            logging.error(f"Dossier non trouvé: {folder_name}")
                    
                    logging.info("Nettoyage terminé")
                else:
                    logging.info("Nettoyage annulé par l'utilisateur")
            else:
                print("\nAucune action de nettoyage à effectuer selon la "
                      "configuration.")
        else:
            logging.info("Nettoyage annulé par l'utilisateur")

    except Exception as e:
        logging.error(f"Erreur dans le programme principal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 