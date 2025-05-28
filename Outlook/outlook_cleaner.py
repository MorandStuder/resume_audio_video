import os
import logging
from datetime import datetime
import pandas as pd
import sys
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient
from dotenv import load_dotenv
import time

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
        logging.error(f"Erreur lors de l'initialisation du client Graph: {str(e)}")
        raise


def get_messages(client, user_id, folder_id='inbox', limit=100):
    """Récupère les messages d'un dossier pour un utilisateur donné."""
    try:
        endpoint = f"/users/{user_id}/mailFolders/{folder_id}/messages"
        params = {
            '$top': limit,
            '$select': 'subject,receivedDateTime,hasAttachments',
            '$expand': 'attachments'
        }
        response = client.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            logging.error(f"Erreur API: {response.status_code}")
            logging.error(f"Détail erreur API: {response.text}")
            return []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def create_email_summary(client, user_id):
    """Crée un tableau récapitulatif des emails avec leurs pièces jointes."""
    try:
        logging.info("Création du récapitulatif des emails")
        summary_data = []

        # Récupération des messages de la boîte de réception
        messages = get_messages(client, user_id)
        logging.info(f"Nombre d'emails trouvés: {len(messages)}")

        for msg in messages:
            subject = msg.get('subject', 'Sans objet')
            received_str = msg.get('receivedDateTime', '')
            if received_str:
                try:
                    dt = datetime.fromisoformat(received_str.replace('Z', '+00:00'))
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
                    name = attachment.get('name', 'Nom inconnu')
                    size = attachment.get('size', 0)
                    attachment_names.append(name)
                    total_attachment_size += size
                    logging.info(
                        f"Pièce jointe trouvée: {name} "
                        f"({size / (1024*1024):.2f} Mo)"
                    )

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
            logging.info(f"Récapitulatif sauvegardé dans {output_file}")
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
        endpoint = f"/users/{user_id}/messages/{message_id}/attachments/{attachment_id}"
        response = client.delete(endpoint)
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
    """Récupère les statistiques d'un dossier (nombre d'emails)."""
    try:
        endpoint = f"/users/{user_id}/mailFolders/{folder_id}"
        params = {
            '$select': 'displayName,totalItemCount,unreadItemCount'
        }
        response = client.get(endpoint, params=params)
        if response.status_code != 200:
            logging.error(f"Réponse API NOK pour {folder_id}: {response.status_code} {response.text}")
            return 0, 0
        folder = response.json()
        logging.info(f"Réponse brute dossier {folder_id}: {folder}")
        nb_emails = folder.get('totalItemCount', 0)
        total_size = 0  # Taille non calculée
        return nb_emails, total_size
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des stats du dossier: {str(e)}")
        return 0, 0


def get_all_mail_folders(client, user_id, parent_id=None, parent_path=""):
    """Récupère récursivement tous les dossiers et sous-dossiers de la boîte mail."""
    folders = []
    try:
        if parent_id:
            endpoint = f"/users/{user_id}/mailFolders/{parent_id}/childFolders"
        else:
            endpoint = f"/users/{user_id}/mailFolders"
        response = client.get(endpoint)
        if response.status_code != 200:
            logging.error(f"Erreur API dossiers: {response.status_code} {response.text}")
            return folders
        for folder in response.json().get('value', []):
            folder_id = folder.get('id')
            folder_name = folder.get('displayName', 'Sans nom')
            full_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
            folders.append({'id': folder_id, 'path': full_path})
            # Appel récursif pour les sous-dossiers
            folders.extend(get_all_mail_folders(client, user_id, folder_id, full_path))
    except Exception as e:
        logging.error(f"Erreur lors de la récupération récursive des dossiers: {str(e)}")
    return folders


def create_config_file(client, user_id):
    """Crée le fichier Excel de configuration pour le nettoyage (tous dossiers et sous-dossiers)."""
    try:
        logging.info("Création du fichier de configuration")
        folders = get_all_mail_folders(client, user_id)
        config_data = []

        for folder in folders:
            folder_id = folder['id']
            folder_path = folder['path']
            nb_emails, total_size = get_folder_stats(client, user_id, folder_id)
            config_data.append({
                "Nom du dossier": folder_path,
                "Nombre d'emails": nb_emails,
                "Taille totale (Go)": round(total_size / (1024*1024*1024), 2),
                "Action": "",  # À remplir manuellement
                "Seuil Taille PJ (Mo)": "",  # À remplir manuellement
                "Seuil Âge (années)": ""  # À remplir manuellement
            })

        # Création du DataFrame et sauvegarde
        df = pd.DataFrame(config_data)
        output_file = "config_nettoyage.xlsx"
        temp_file = "config_nettoyage_temp.xlsx"

        while True:
            try:
                df.to_excel(temp_file, index=False)
                if os.path.exists(output_file):
                    os.remove(output_file)
                os.rename(temp_file, output_file)
                logging.info(f"Fichier de configuration sauvegardé dans {output_file}")
                break
            except PermissionError as e:
                if hasattr(e, 'winerror') and e.winerror == 32:
                    print(f"\nLe fichier {output_file} est ouvert. Veuillez le fermer puis appuyez sur Entrée pour réessayer, ou Ctrl+C pour annuler.")
                    input()
                    continue
                else:
                    logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
                    raise
            except Exception as e:
                logging.error(f"Erreur lors de la sauvegarde: {str(e)}")
                raise

        return df
    except Exception as e:
        logging.error(f"Erreur lors de la création du fichier de configuration: {str(e)}")
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
            "Veuillez configurer les règles de nettoyage dans config_nettoyage.xlsx"
        )

        # Demande de confirmation pour le nettoyage
        if input("\nVoulez-vous procéder au nettoyage ? (o/n): ").lower() == 'o':
            # TODO: Implémenter la logique de nettoyage
            logging.info("Nettoyage terminé")
        else:
            logging.info("Nettoyage annulé par l'utilisateur")

    except Exception as e:
        logging.error(f"Erreur dans le programme principal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 