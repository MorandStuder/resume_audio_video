#!/usr/bin/env python3
"""
Script d'initialisation pour générer les fichiers de configuration.
"""

import os
import json
import pandas as pd
from typing import Dict, Any

def create_env_template() -> None:
    """Crée un fichier .env template."""
    env_content = """# Configuration Microsoft Graph
OUTLOOK_USER_EMAIL=votre.email@domaine.com
OUTLOOK_CLIENT_ID=votre_client_id
OUTLOOK_CLIENT_SECRET=votre_client_secret
TENANT_ID=votre_tenant_id
"""
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("Fichier .env.template créé")

def create_outlook_config() -> None:
    """Crée le fichier de configuration Outlook."""
    config: Dict[str, Any] = {
        'sharepoint': {
            'backup_root': 'sauvegardes_pj',
            'site': 'votre-domaine.sharepoint.com',
            'folder': '/personal/votre_dossier'
        }
    }
    
    with open('outlook_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    print("Fichier outlook_config.json créé")

def create_excel_config() -> None:
    """Crée le fichier de configuration Excel."""
    df = pd.DataFrame({
        'Dossier': [
            'Boîte de réception',
            'Éléments envoyés',
            'Archive'
        ],
        'Action': [
            'Nettoyer',
            'Nettoyer',
            'Nettoyer'
        ],
        'Seuil Taille (Mo)': [
            10,
            10,
            10
        ],
        'Seuil Age (années)': [
            2,
            2,
            5
        ]
    })
    
    df.to_excel('config_nettoyage.xlsx', index=False)
    print("Fichier config_nettoyage.xlsx créé")

def main() -> None:
    """Point d'entrée principal."""
    print("=== Initialisation de la configuration ===\n")
    
    # Création des fichiers
    create_env_template()
    create_outlook_config()
    create_excel_config()
    
    print("\nConfiguration terminée!")
    print("""
Instructions:
1. Copiez .env.template vers .env
2. Modifiez .env avec vos identifiants
3. Modifiez outlook_config.json avec vos paramètres SharePoint
4. Ajustez config_nettoyage.xlsx selon vos besoins
""")

if __name__ == "__main__":
    main() 