# Outlook Cleaner

Un outil Python pour nettoyer et gérer votre boîte mail Outlook 365, permettant de supprimer automatiquement les emails et pièces jointes selon des règles personnalisables.

## Fonctionnalités

- Authentification sécurisée avec Microsoft Graph API
- Analyse des dossiers et des emails
- Génération de rapports Excel détaillés
- Nettoyage personnalisable basé sur :
  - Taille des pièces jointes
  - Âge des emails
  - Dossiers spécifiques
- Interface interactive pour la confirmation des suppressions

## Prérequis

- Python 3.8 ou supérieur
- Un compte Microsoft 365
- Une application enregistrée dans Azure AD avec les permissions appropriées

## Installation

1. Clonez le repository :
```bash
git clone https://github.com/votre-username/outlook-cleaner.git
cd outlook-cleaner
```

2. Créez un environnement virtuel et activez-le :
```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Linux/Mac
source venv/bin/activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Créez un fichier `.env` à la racine du projet avec vos identifiants :
```env
OUTLOOK_CLIENT_ID=votre_client_id
OUTLOOK_CLIENT_SECRET=votre_client_secret
OUTLOOK_USER_EMAIL=utilisateur@domaine.com
```

## Configuration

1. Créez une application dans le [Portail Azure](https://portal.azure.com)
2. Configurez les permissions suivantes :
   - Microsoft Graph API
   - Mail.ReadWrite
   - Mail.Send
3. Notez le Client ID et le Client Secret
4. Ajoutez-les dans le fichier `.env`

## Utilisation

1. Lancez le script :
```bash
python outlook_cleaner.py
```

2. Suivez les étapes interactives :
   - Le script générera d'abord un récapitulatif des emails
   - Un fichier Excel de configuration sera créé
   - Modifiez les règles de nettoyage dans le fichier Excel
   - Confirmez les suppressions lors de l'exécution

## Structure des fichiers

```
outlook-cleaner/
├── .env                    # Variables d'environnement (à créer)
├── .gitignore             # Fichiers ignorés par Git
├── README.md              # Documentation
├── requirements.txt       # Dépendances Python
├── outlook_cleaner.py     # Script principal
├── config_nettoyage.xlsx  # Configuration générée
└── recap_emails.xlsx      # Récapitulatif généré
```

## Sécurité

- Les identifiants sont stockés dans un fichier `.env` (non versionné)
- Le token d'authentification est stocké localement
- Les suppressions nécessitent une confirmation manuelle

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 