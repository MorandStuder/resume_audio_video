#!/usr/bin/env python3
"""
Interface principale pour le nettoyage des pièces jointes Outlook.
Utilise une configuration Excel et les classes de base.
"""

import logging
import pandas as pd
from typing import Dict, List, Tuple
from tqdm import tqdm
from attachment_manager import AttachmentManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class OutlookCleaner:
    """Interface principale pour le nettoyage des pièces jointes."""
    
    def __init__(self):
        """Initialise le gestionnaire de nettoyage."""
        self.manager = AttachmentManager()
        self.config_file = "config_nettoyage.xlsx"
    
    def read_config(self) -> pd.DataFrame:
        """
        Lit la configuration depuis Excel.
        
        Returns:
            DataFrame avec les règles de nettoyage
        """
        try:
            df = pd.read_excel(self.config_file)
            required_cols = [
                'Dossier',
                'Action',
                'Seuil Taille (Mo)',
                'Seuil Age (années)'
            ]
            
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(
                    f"Colonnes manquantes dans Excel: {', '.join(missing)}"
                )
            
            logging.info(f"Configuration lue: {len(df)} règles")
            return df
            
        except Exception as e:
            logging.error(f"Erreur lecture configuration: {str(e)}")
            return pd.DataFrame()
    
    def process_folder(self, folder_path: str, config: Dict,
                      is_test: bool = True) -> Tuple[int, int, float]:
        """
        Traite un dossier selon sa configuration.
        
        Args:
            folder_path: Chemin du dossier Outlook
            config: Configuration pour ce dossier
            is_test: Si True, simule les actions
            
        Returns:
            (nb_emails, nb_pj, taille_mo)
        """
        try:
            # Récupération de l'ID du dossier
            folder_id = self.manager.get_folder_id(folder_path)
            if not folder_id:
                logging.error(f"Dossier non trouvé: {folder_path}")
                return 0, 0, 0.0
            
            # Récupération des messages
            age_days = int(config['Seuil Age (années)'] * 365)
            messages = self.manager.get_messages(
                folder_id,
                older_than_days=age_days
            )
            
            emails_processed = 0
            attachments_processed = 0
            total_size_mb = 0.0
            
            # Traitement des messages avec barre de progression
            with tqdm(
                total=len(messages),
                desc=f"Traitement de {folder_path}",
                unit="email"
            ) as pbar:
                for msg in messages:
                    attachments = msg.get('attachments', [])
                    
                    for att in attachments:
                        if att.get('@odata.type') == '#microsoft.graph.fileAttachment':
                            size = att.get('size', 0) / (1024 * 1024)
                            
                            if size >= config['Seuil Taille (Mo)']:
                                success, size_mb = self.manager.process_attachment(
                                    msg['id'],
                                    att,
                                    folder_path,
                                    backup=True,
                                    is_test=is_test
                                )
                                
                                if success:
                                    attachments_processed += 1
                                    total_size_mb += size_mb
                    
                    emails_processed += 1
                    pbar.update(1)
            
            return emails_processed, attachments_processed, total_size_mb
            
        except Exception as e:
            logging.error(f"Erreur traitement dossier: {str(e)}")
            return 0, 0, 0.0
    
    def run(self, is_test: bool = True):
        """
        Exécute le nettoyage selon la configuration Excel.
        
        Args:
            is_test: Si True, simule les actions
        """
        try:
            # Lecture de la configuration
            config_df = self.read_config()
            if config_df.empty:
                return
            
            # Variables pour le résumé
            total_emails = 0
            total_attachments = 0
            total_size_mb = 0.0
            
            # Traitement de chaque règle
            for _, rule in config_df.iterrows():
                if pd.notna(rule['Action']):
                    folder_path = rule['Dossier']
                    emails, attachments, size = self.process_folder(
                        folder_path,
                        rule,
                        is_test
                    )
                    
                    total_emails += emails
                    total_attachments += attachments
                    total_size_mb += size
            
            # Affichage du résumé
            print("\n=== RÉSUMÉ DU NETTOYAGE ===")
            print(f"Emails traités: {total_emails}")
            print(f"Pièces jointes traitées: {total_attachments}")
            print(f"Espace libéré: {total_size_mb:.2f} Mo")
            print(f"Mode: {'TEST' if is_test else 'RÉEL'}")
            
        except Exception as e:
            logging.error(f"Erreur exécution: {str(e)}")

def main():
    """Point d'entrée principal."""
    cleaner = OutlookCleaner()
    
    while True:
        print("\nMenu principal:")
        print("1. Mettre à jour la configuration Excel")
        print("2. Exécuter les actions (TEST)")
        print("3. Exécuter les actions (RÉEL)")
        print("4. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == "1":
            print("Ouvrez et modifiez le fichier config_nettoyage.xlsx")
        elif choice == "2":
            cleaner.run(is_test=True)
        elif choice == "3":
            confirm = input("Êtes-vous sûr de vouloir exécuter en mode RÉEL ? (o/N) ")
            if confirm.lower() == 'o':
                cleaner.run(is_test=False)
        elif choice == "4":
            break
        else:
            print("Choix invalide")

if __name__ == "__main__":
    main() 