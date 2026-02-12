#!/usr/bin/env python3
"""
Module de base pour l'interaction avec Microsoft Graph API.
Contient les fonctionnalités essentielles d'authentification et d'accès aux emails.
"""

import os
import logging
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

class OutlookCore:
    """Classe de base pour l'interaction avec Microsoft Graph API."""
    
    def __init__(self):
        """Initialise la connexion à Microsoft Graph."""
        load_dotenv()
        self.user_id = os.getenv('OUTLOOK_USER_EMAIL')
        self.client_id = os.getenv('OUTLOOK_CLIENT_ID')
        self.client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        self.tenant_id = os.getenv('TENANT_ID')
        self._init_auth()
        
    def _init_auth(self) -> None:
        """Initialise l'authentification Microsoft Graph."""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id, self.user_id]):
                raise ValueError(
                    "Variables d'environnement manquantes. Requis: "
                    "OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, TENANT_ID, OUTLOOK_USER_EMAIL"
                )
            
            self.credentials = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            logging.info("Authentification Microsoft Graph initialisée")
            
        except Exception as e:
            logging.error(f"Erreur d'authentification: {str(e)}")
            raise
            
    def _get_headers(self) -> Dict[str, str]:
        """Récupère les en-têtes d'authentification."""
        token = self.credentials.get_token("https://graph.microsoft.com/.default")
        return {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
    def get_messages(self, folder_id: str, 
                    limit: int = 1000,
                    older_than_days: Optional[int] = None,
                    batch_size: int = 50) -> List[Dict]:
        """
        Récupère les messages d'un dossier avec gestion des erreurs et pagination.
        
        Args:
            folder_id: ID du dossier Outlook
            limit: Nombre maximum de messages à récupérer
            older_than_days: Filtre sur l'âge des messages
            batch_size: Nombre de messages par requête
            
        Returns:
            Liste des messages trouvés
        """
        try:
            endpoint = (
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/"
                f"mailFolders/{folder_id}/messages"
            )
            
            params = {
                '$top': batch_size,
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
                            next_link, 
                            headers=self._get_headers(), 
                            timeout=60
                        )
                    else:
                        response = requests.get(
                            endpoint, 
                            headers=self._get_headers(), 
                            params=params, 
                            timeout=60
                        )
                    
                    if response.status_code == 200:
                        data = response.json()
                        messages = data.get('value', [])
                        all_messages.extend(messages)
                        
                        if len(all_messages) >= limit:
                            return all_messages[:limit]
                        
                        next_link = data.get('@odata.nextLink')
                        if not next_link:
                            break
                            
                        retry_count = 0
                        
                    elif response.status_code == 504:  # Timeout
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
                                f"Trop de timeouts API après {max_retries} tentatives"
                            )
                            break
                            
                    else:
                        logging.error(
                            f"Erreur API {response.status_code}: {response.text}"
                        )
                        break
                        
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count
                        logging.warning(
                            f"Timeout connexion, nouvelle tentative dans "
                            f"{wait_time}s (tentative {retry_count}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(
                            f"Trop de timeouts connexion après {max_retries} tentatives"
                        )
                        break
                        
                except Exception as e:
                    logging.error(f"Erreur requête: {str(e)}")
                    break
                    
            return all_messages
            
        except Exception as e:
            logging.error(f"Erreur récupération messages: {str(e)}")
            return []
            
    def get_folder_id(self, folder_path: str) -> Optional[str]:
        """
        Récupère l'ID d'un dossier Outlook à partir de son chemin.
        
        Args:
            folder_path: Chemin du dossier (ex: "Boîte de réception/Archive")
            
        Returns:
            ID du dossier ou None si non trouvé
        """
        try:
            parts = folder_path.split('/')
            current_id = None
            
            for part in parts:
                endpoint = (
                    f"https://graph.microsoft.com/v1.0/users/{self.user_id}/"
                    f"{'mailFolders' if not current_id else f'mailFolders/{current_id}/childFolders'}"
                )
                
                response = requests.get(
                    endpoint,
                    headers=self._get_headers(),
                    params={'$filter': f"displayName eq '{part}'"}
                )
                
                if response.status_code == 200:
                    folders = response.json().get('value', [])
                    if folders:
                        current_id = folders[0]['id']
                    else:
                        logging.error(f"Dossier non trouvé: {part}")
                        return None
                else:
                    logging.error(
                        f"Erreur recherche dossier: {response.status_code}"
                    )
                    return None
                    
            return current_id
            
        except Exception as e:
            logging.error(f"Erreur récupération ID dossier: {str(e)}")
            return None