import os
import logging
from datetime import datetime
import pandas as pd
import sys
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient
from dotenv import load_dotenv

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


def main():
    """Fonction principale."""
    try:
        logging.info("Démarrage du programme")
        client = get_graph_client()
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")

        # Création du récapitulatif
        recap_df = create_email_summary(client, user_id)
        print(
            f"\nRécapitulatif des emails créé ({len(recap_df)} emails trouvés). "
            "Veuillez vérifier le fichier recap_emails.xlsx"
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