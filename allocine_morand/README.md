# Allocine Morand

Script Python pour récupérer automatiquement les films vus et à voir depuis Allociné.

## Installation

1. Cloner le repository
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```
3. Créer un fichier `config.py` avec vos identifiants Allociné :
```python
ALLOCINE_EMAIL = "votre.email@example.com"
ALLOCINE_PASSWORD = "votre_mot_de_passe"
```

## Utilisation

Lancer le script principal :
```bash
python main.py
```

Les fichiers CSV seront sauvegardés dans le répertoire `output/`.

## Fonctionnalités

- Récupération de la liste des films vus avec les notes utilisateur
- Récupération de la liste des films à voir
- Sauvegarde au format CSV avec les informations détaillées :
  - Titre
  - Réalisateur
  - Date de sortie
  - Synopsis
  - Notes (presse, spectateurs, utilisateur)
  - Score de recommandation
  - Plateformes de streaming disponibles

## Fonctionnalités à développer

- Sauvegarde incrémentale des films vus (ne sauvegarder que les nouveaux films)
- Ajout d'une interface graphique
- Support de plusieurs comptes utilisateurs

## Prérequis

- Python 3.7 ou supérieur
- Un compte Allociné
- Les dépendances Python listées dans `requirements.txt`

## Format des fichiers CSV

Les fichiers CSV générés contiennent les colonnes suivantes :
- Titre
- Réalisateur
- Date de sortie
- Synopsis
- Note Presse
- Note Spectateurs
- Ma Note (uniquement pour les films vus)
- Score Recommandation
- Colonnes pour chaque plateforme de streaming (avec 'X' si disponible)
- URL du film

## Notes importantes

- Le script utilise Selenium pour automatiser le navigateur
- Un navigateur Chrome s'ouvrira automatiquement pendant l'exécution
- Le processus peut prendre plusieurs minutes selon le nombre de films
- En cas d'échec de la connexion automatique, vous pourrez vous connecter manuellement

## Sécurité

- Ne partagez jamais votre fichier `config.py` contenant vos identifiants
- Le fichier `config.py` est déjà dans le `.gitignore` pour éviter tout commit accidentel

## Dépannage

Si vous rencontrez des erreurs :
1. Vérifiez que Python est correctement installé et dans le PATH
2. Vérifiez que Chrome est installé sur votre machine
3. Assurez-vous que vos identifiants dans `config.py` sont corrects
4. Vérifiez votre connexion internet
5. Si le script échoue, vous pouvez le relancer, il reprendra là où il s'était arrêté 