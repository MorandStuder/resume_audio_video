#!/usr/bin/env python3
"""
Script autonome pour nettoyer les pièces jointes des éléments envoyés Outlook.

Ce script permet de supprimer automatiquement les pièces jointes volumineuses
des emails envoyés selon des critères de taille et d'âge configurables.

Usage:
    python clean_sent_items.py [--size-threshold SIZE] [--size-unit UNIT] 
                              [--age-threshold AGE] [--age-unit UNIT]
                              [--no-backup] [--execute]

Arguments:
    --size-threshold SIZE  Seuil de taille (défaut: 10)
    --size-unit UNIT      Unité de taille: ko, mo, go (défaut: mo)
    --age-threshold AGE   Âge minimum (défaut: 2)
    --age-unit UNIT       Unité d'âge: mois, ans (défaut: ans)
    --no-backup          Ne pas sauvegarder les PJ avant suppression
    --execute            Exécuter réellement les suppressions (mode test par défaut)
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from tqdm import tqdm

# Import des fonctions du script principal
from outlook_cleaner import (
    get_graph_client, get_messages, delete_attachment, 
    download_attachment
)

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

# Réduire la verbosité des logs Azure
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)


def convert_size_to_bytes(size, unit):
    """Convertit une taille avec unité en octets."""
    unit = unit.lower()
    if unit == 'ko':
        return size * 1024
    elif unit == 'mo':
        return size * 1024 * 1024
    elif unit == 'go':
        return size * 1024 * 1024 * 1024
    else:
        raise ValueError(f"Unité de taille non reconnue: {unit}")


def convert_age_to_days(age, unit):
    """Convertit un âge avec unité en jours."""
    unit = unit.lower()
    if unit == 'mois':
        return age * 30.44  # Moyenne des jours par mois
    elif unit == 'ans':
        return age * 365.25  # Moyenne des jours par an
    else:
        raise ValueError(f"Unité d'âge non reconnue: {unit}")


def clean_sent_items_attachments(size_threshold=10, size_unit='mo', 
                                age_threshold=2, age_unit='ans',
                                backup_attachments=True, dry_run=True):
    """
    Fonction autonome pour supprimer les pièces jointes des éléments envoyés.
    
    Args:
        size_threshold (float): Seuil de taille pour supprimer les PJ
        size_unit (str): Unité de taille (ko, mo, go)
        age_threshold (float): Âge minimum pour traiter les emails
        age_unit (str): Unité d'âge (mois, ans)
        backup_attachments (bool): Sauvegarder les PJ avant suppression
        dry_run (bool): Mode test (pas de suppression réelle)
    
    Returns:
        dict: Statistiques du nettoyage
    """
    try:
        # Conversion des unités
        size_threshold_bytes = convert_size_to_bytes(size_threshold, size_unit)
        age_threshold_days = convert_age_to_days(age_threshold, age_unit)
        
        logging.info("=== DÉMARRAGE DU NETTOYAGE DES ÉLÉMENTS ENVOYÉS ===")
        logging.info(f"Seuil de taille: {size_threshold} {size_unit.upper()}")
        logging.info(f"Âge minimum: {age_threshold} {age_unit}")
        logging.info(
            f"Sauvegarde des PJ: {'Oui' if backup_attachments else 'Non'}"
        )
        logging.info(f"Mode test: {'Oui' if dry_run else 'Non'}")
        
        # Initialisation du client Graph
        client = get_graph_client()
        user_id = os.getenv('OUTLOOK_USER_EMAIL')
        if not user_id:
            user_id = input("Entrez l'email de l'utilisateur à traiter : ")
        
        # Récupération du dossier des éléments envoyés
        sent_folder_id = 'sentitems'
        logging.info("Récupération des éléments envoyés...")
        
        # Récupération des messages du dossier sentitems
        messages = get_messages(client, user_id, sent_folder_id)
        if not messages:
            logging.info("Aucun élément envoyé trouvé")
            return {
                'emails_processed': 0,
                'attachments_found': 0,
                'attachments_deleted': 0,
                'total_size_bytes': 0,
                'dry_run': dry_run
            }
        
        current_date = datetime.now()
        emails_processed = 0
        attachments_found = 0
        attachments_deleted = 0
        total_size_bytes = 0
        
        logging.info(
            f"Traitement de {len(messages)} éléments envoyés "
            f"(seuil: {size_threshold} {size_unit.upper()}, "
            f"âge: {age_threshold} {age_unit})"
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
                age_days = (current_date - received_date).days
            except Exception:
                continue
            
            # Si l'email est plus récent que le seuil, on passe au suivant
            if age_days < age_threshold_days:
                continue
            
            emails_processed += 1
            
            # Traitement des pièces jointes
            if msg.get('hasAttachments', False):
                attachments = msg.get('attachments', [])
                for attachment in attachments:
                    attachment_size_bytes = attachment.get('size', 0)
                    attachments_found += 1
                    
                    if attachment_size_bytes > size_threshold_bytes:
                        total_size_bytes += attachment_size_bytes
                        
                        # Conversion pour l'affichage
                        if size_unit == 'ko':
                            display_size = attachment_size_bytes / 1024
                        elif size_unit == 'mo':
                            display_size = attachment_size_bytes / (1024*1024)
                        elif size_unit == 'go':
                            display_size = attachment_size_bytes / (1024*1024*1024)
                        
                        # Sauvegarde avant suppression si demandé
                        if backup_attachments:
                            download_attachment(
                                client, user_id, msg['id'], 
                                attachment, "Elements_envoyes"
                            )
                        
                        # Suppression de la pièce jointe
                        if not dry_run:
                            if delete_attachment(
                                    client, user_id, msg['id'], 
                                    attachment['id']
                            ):
                                attachments_deleted += 1
                                logging.info(
                                    f"Pièce jointe supprimée: "
                                    f"{attachment.get('name')} "
                                    f"({display_size:.2f} {size_unit.upper()}) - "
                                    f"Email: {msg.get('subject', 'Sans objet')}"
                                )
                        else:
                            attachments_deleted += 1
                            logging.info(
                                f"[DRY RUN] Pièce jointe à supprimer: "
                                f"{attachment.get('name')} "
                                f"({display_size:.2f} {size_unit.upper()}) - "
                                f"Email: {msg.get('subject', 'Sans objet')}"
                            )
        
        # Conversion de la taille totale pour l'affichage
        if size_unit == 'ko':
            total_size_display = total_size_bytes / 1024
        elif size_unit == 'mo':
            total_size_display = total_size_bytes / (1024*1024)
        elif size_unit == 'go':
            total_size_display = total_size_bytes / (1024*1024*1024)
        
        # Résumé des statistiques
        stats = {
            'emails_processed': emails_processed,
            'attachments_found': attachments_found,
            'attachments_deleted': attachments_deleted,
            'total_size_bytes': total_size_bytes,
            'total_size_display': total_size_display,
            'size_unit': size_unit,
            'dry_run': dry_run
        }
        
        logging.info("=== RÉSUMÉ DU NETTOYAGE ===")
        logging.info(f"Emails traités: {emails_processed}")
        logging.info(f"Pièces jointes trouvées: {attachments_found}")
        logging.info(f"Pièces jointes supprimées: {attachments_deleted}")
        logging.info(
            f"Espace libéré: {total_size_display:.2f} {size_unit.upper()}"
        )
        logging.info(f"Mode test: {'Oui' if dry_run else 'Non'}")
        
        return stats
        
    except Exception as e:
        logging.error(
            f"Erreur lors du nettoyage des éléments envoyés: {str(e)}"
        )
        raise


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Nettoyer les pièces jointes des éléments envoyés Outlook"
    )
    parser.add_argument(
        '--size-threshold', 
        type=float, 
        default=10.0,
        help='Seuil de taille pour supprimer les PJ (défaut: 10)'
    )
    parser.add_argument(
        '--size-unit',
        type=str,
        choices=['ko', 'mo', 'go'],
        default='mo',
        help='Unité de taille: ko, mo, go (défaut: mo)'
    )
    parser.add_argument(
        '--age-threshold', 
        type=float, 
        default=2.0,
        help='Âge minimum pour traiter les emails (défaut: 2)'
    )
    parser.add_argument(
        '--age-unit',
        type=str,
        choices=['mois', 'ans'],
        default='ans',
        help='Unité d\'âge: mois, ans (défaut: ans)'
    )
    parser.add_argument(
        '--no-backup', 
        action='store_true',
        help='Ne pas sauvegarder les PJ avant suppression'
    )
    parser.add_argument(
        '--execute', 
        action='store_true',
        help='Exécuter réellement les suppressions (mode test par défaut)'
    )
    
    args = parser.parse_args()
    
    try:
        # Vérification des variables d'environnement
        required_vars = [
            'OUTLOOK_CLIENT_ID', 'OUTLOOK_CLIENT_SECRET', 'TENANT_ID'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logging.error(
                f"Variables d'environnement manquantes: "
                f"{', '.join(missing_vars)}"
            )
            logging.error(
                "Veuillez créer un fichier .env avec les variables suivantes:"
            )
            for var in missing_vars:
                logging.error(f"  {var}=votre_valeur")
            sys.exit(1)
        
        # Affichage des paramètres
        print("=== PARAMÈTRES DU NETTOYAGE ===")
        print(f"Seuil de taille: {args.size_threshold} {args.size_unit.upper()}")
        print(f"Âge minimum: {args.age_threshold} {args.age_unit}")
        print(f"Sauvegarde des PJ: {'Non' if args.no_backup else 'Oui'}")
        print(f"Mode test: {'Non' if args.execute else 'Oui'}")
        print()
        
        # Confirmation si mode exécution
        if args.execute:
            confirm = input(
                "ATTENTION: Vous êtes en mode EXÉCUTION. "
                "Les suppressions seront effectives. Continuer ? (o/N): "
            )
            if confirm.lower() != 'o':
                print("Opération annulée.")
                sys.exit(0)
        
        # Exécution du nettoyage
        stats = clean_sent_items_attachments(
            size_threshold=args.size_threshold,
            size_unit=args.size_unit,
            age_threshold=args.age_threshold,
            age_unit=args.age_unit,
            backup_attachments=not args.no_backup,
            dry_run=not args.execute
        )
        
        # Affichage du résumé final
        print("\n=== RÉSUMÉ FINAL ===")
        print(f"Emails traités: {stats['emails_processed']}")
        print(f"Pièces jointes trouvées: {stats['attachments_found']}")
        print(f"Pièces jointes supprimées: {stats['attachments_deleted']}")
        print(
            f"Espace libéré: {stats['total_size_display']:.2f} "
            f"{stats['size_unit'].upper()}"
        )
        print(f"Mode test: {'Oui' if stats['dry_run'] else 'Non'}")
        
        if stats['dry_run'] and stats['attachments_deleted'] > 0:
            print(
                "\nPour exécuter réellement les suppressions, "
                "relancez avec l'option --execute"
            )
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erreur fatale: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 