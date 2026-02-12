#!/usr/bin/env python3
"""
Module de gestion des pièces jointes Outlook.
Gère la sauvegarde et la suppression des pièces jointes.
"""

import os
import json
import logging
import requests
import msal
from typing import Dict, Optional, Tuple
from outlook_core import OutlookCore

class AttachmentManager(OutlookCore):
    """Gestionnaire de pièces jointes Outlook."""
    
    def __init__(self):
        """Initialise le gestionnaire de pièces jointes."""
        super().__init__()
        self._load_config()
        
        if not os.path.exists(self.backup_root):
            os.makedirs(self.backup_root)
    
    def _load_config(self):
        """Charge la configuration depuis le fichier JSON."""
        try:
            with open('outlook_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                sharepoint_config = config.get('sharepoint', {})
                self.backup_root = sharepoint_config.get('backup_root', 'sauvegardes_pj')
                self.sharepoint_site = sharepoint_config.get('site')
                self.sharepoint_folder = sharepoint_config.get('folder')
                
                if not all([self.sharepoint_site, self.sharepoint_folder]):
                    raise ValueError(
                        "Configuration SharePoint incomplète dans outlook_config.json"
                    )
        except FileNotFoundError:
            # Créer un fichier de configuration par défaut
            default_config = {
                'sharepoint': {
                    'backup_root': 'sauvegardes_pj',
                    'site': 'oneleven-my.sharepoint.com',
                    'folder': '/personal/morand_studer_eleven-strategy_com/EoXScuP8bGtCrZHBrGKGB4sBtcaplSLVHsDcH7BalWGTkQ'
                }
            }
            with open('outlook_config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            
            self.backup_root = default_config['sharepoint']['backup_root']
            self.sharepoint_site = default_config['sharepoint']['site']
            self.sharepoint_folder = default_config['sharepoint']['folder']
            logging.info("Fichier de configuration créé avec les valeurs par défaut")
    
    def _get_sharepoint_token(self) -> Optional[str]:
        """
        Obtient un token d'accès pour SharePoint.
        
        Returns:
            Token d'accès ou None si échec
        """
        try:
            # Utiliser le même client_id et secret que pour Outlook
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            
            scopes = ["https://oneleven-my.sharepoint.com/.default"]
            result = app.acquire_token_silent(scopes, account=None)
            
            if not result:
                result = app.acquire_token_for_client(scopes)
                
            if "access_token" in result:
                return result["access_token"]
            else:
                logging.error(f"Erreur token SharePoint: {result.get('error')}")
                return None
                
        except Exception as e:
            logging.error(f"Erreur authentification SharePoint: {str(e)}")
            return None
    
    def backup_attachment(self, message_id: str, attachment: Dict, 
                         folder_path: str) -> Tuple[bool, float]:
        """
        Sauvegarde une pièce jointe sur SharePoint.
        
        Args:
            message_id: ID du message
            attachment: Dictionnaire contenant les infos de la pièce jointe
            folder_path: Chemin du dossier Outlook source
            
        Returns:
            (succès, taille_mo)
        """
        try:
            # Obtention du token SharePoint
            token = self._get_sharepoint_token()
            if not token:
                return False, 0.0
            
            # Création du sous-dossier pour le dossier mail
            folder_name = folder_path.replace('/', '_').replace('\\', '_')
            
            # Nettoyage du nom de fichier
            name = attachment.get('name', 'sans_nom')
            safe_name = "".join(
                c for c in name 
                if c.isalnum() or c in (' ', '-', '_', '.')
            )
            
            # Récupération du contenu de la pièce jointe depuis Outlook
            outlook_endpoint = (
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/"
                f"messages/{message_id}/attachments/{attachment['id']}/$value"
            )
            
            response = requests.get(
                outlook_endpoint,
                headers=self._get_headers(),
                stream=True
            )
            
            if response.status_code != 200:
                logging.error(
                    f"Erreur téléchargement PJ: {response.status_code}"
                )
                return False, 0.0
                
            # Upload sur SharePoint
            sharepoint_endpoint = (
                f"https://{self.sharepoint_site}/_api/web/GetFolderByServerRelativeUrl"
                f"('{self.sharepoint_folder}/{folder_name}')/Files/add(url='{safe_name}',overwrite=true)"
            )
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose',
            }
            
            upload_response = requests.post(
                sharepoint_endpoint,
                headers=headers,
                data=response.content
            )
            
            if upload_response.status_code in [200, 201]:
                size_mb = len(response.content) / (1024 * 1024)
                logging.info(
                    f"PJ sauvegardée sur SharePoint: {folder_name}/{safe_name} "
                    f"({size_mb:.2f} Mo)"
                )
                return True, size_mb
            else:
                logging.error(
                    f"Erreur upload SharePoint: {upload_response.status_code}"
                )
                return False, 0.0
                
        except Exception as e:
            logging.error(f"Erreur sauvegarde PJ: {str(e)}")
            return False, 0.0
    
    def delete_attachment(self, message_id: str, attachment_id: str) -> bool:
        """
        Supprime une pièce jointe.
        
        Args:
            message_id: ID du message
            attachment_id: ID de la pièce jointe
            
        Returns:
            True si suppression réussie
        """
        try:
            endpoint = (
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/"
                f"messages/{message_id}/attachments/{attachment_id}"
            )
            
            response = requests.delete(
                endpoint,
                headers=self._get_headers()
            )
            
            if response.status_code == 204:
                logging.info(f"PJ {attachment_id} supprimée")
                return True
            else:
                logging.error(
                    f"Erreur suppression PJ: {response.status_code}"
                )
                return False
                
        except Exception as e:
            logging.error(f"Erreur suppression PJ: {str(e)}")
            return False
    
    def process_attachment(self, message_id: str, attachment: Dict,
                         folder_path: str, backup: bool = True,
                         is_test: bool = True) -> Tuple[bool, float]:
        """
        Traite une pièce jointe (sauvegarde et/ou suppression).
        
        Args:
            message_id: ID du message
            attachment: Dictionnaire contenant les infos de la pièce jointe
            folder_path: Chemin du dossier Outlook source
            backup: Si True, sauvegarde la PJ avant suppression
            is_test: Si True, simule les actions sans les exécuter
            
        Returns:
            (succès, taille_mo)
        """
        try:
            size = attachment.get('size', 0)
            size_mb = size / (1024 * 1024)
            
            if is_test:
                logging.info(
                    f"[TEST] PJ {attachment.get('name')} "
                    f"({size_mb:.2f} Mo) serait traitée"
                )
                return True, size_mb
            
            if backup:
                success, _ = self.backup_attachment(
                    message_id, attachment, folder_path
                )
                if not success:
                    logging.warning(
                        f"Échec sauvegarde PJ {attachment.get('name')}"
                    )
                    return False, 0.0
            
            if self.delete_attachment(message_id, attachment['id']):
                return True, size_mb
            else:
                return False, 0.0
                
        except Exception as e:
            logging.error(f"Erreur traitement PJ: {str(e)}")
            return False, 0.0 