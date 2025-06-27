# Guide d'installation et d'utilisation

## Application de veille et publication LinkedIn pour Eleven Strategy (MVP)

### Prérequis

- Node.js (v14 ou supérieur)
- Python 3.10 ou supérieur
- Clé API OpenAI
- Connexion Internet

### Installation

1. Clonez ou téléchargez le code source de l'application

2. Configuration du backend :
   - Naviguez vers le dossier `eleven-strategy-app/backend`
   - Créez un fichier `.env` basé sur le fichier `.env.example`
   - Ajoutez votre clé API OpenAI dans le fichier `.env` :
     ```
     OPENAI_API_KEY=votre_cle_openai
     ```
   - Installez les dépendances Python :
     ```
     python3 -m venv venv
     source venv/bin/activate
     pip install fastapi uvicorn pydantic python-dotenv requests beautifulsoup4 feedparser openai
     ```

3. Configuration du frontend :
   - Naviguez vers le dossier `eleven-strategy-app/frontend`
   - Installez les dépendances Node.js :
     ```
     npm install
     ```

### Démarrage de l'application

Vous pouvez démarrer l'application de deux façons :

1. Utiliser le script de démarrage automatique :
   ```
   ./eleven-strategy-app/start.sh
   ```

2. Démarrer manuellement les services :
   - Pour le backend :
     ```
     cd eleven-strategy-app/backend
     source venv/bin/activate
     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
     ```
   - Pour le frontend (dans un autre terminal) :
     ```
     cd eleven-strategy-app/frontend
     npm start
     ```

L'application sera accessible à l'adresse : http://localhost:3000

### Utilisation

1. **Collecte d'articles** :
   - Cliquez sur le bouton "Collecter des articles" dans la colonne de gauche
   - Les articles de superhuman.ai seront récupérés et affichés dans la liste

2. **Lecture d'articles** :
   - Sélectionnez un article dans la liste pour le lire dans la colonne centrale
   - Vous pouvez noter l'article de 1 à 5 étoiles en bas de la colonne centrale

3. **Génération de résumés** :
   - Sélectionnez un article et cliquez sur "Générer un résumé" dans la colonne de droite
   - Un résumé de 3 phrases sera généré via l'API OpenAI
   - Vous pouvez modifier le résumé dans l'éditeur WYSIWYG

4. **Publication sur LinkedIn** :
   - Après avoir généré et éventuellement modifié le résumé, cliquez sur "Publier sur LinkedIn"
   - Pour le MVP, la publication est simulée (pas de publication réelle sur LinkedIn)

### Fonctionnalités du MVP

- Interface tri-colonnes (liste, lecture, résumé)
- Collecte d'articles depuis superhuman.ai (simulée pour le MVP)
- Notation basique (1-5 étoiles)
- Génération de résumé IA minimal (3 phrases) via OpenAI
- Publication LinkedIn manuelle (simulée pour le MVP)

### Dépannage

- Si le backend ne démarre pas, vérifiez que le port 8000 est disponible
- Si le frontend ne démarre pas, vérifiez que le port 3000 est disponible
- Si la génération de résumés échoue, vérifiez votre clé API OpenAI dans le fichier `.env`

### Arrêt de l'application

Pour arrêter l'application, utilisez la commande :
```
pkill -f 'node|uvicorn'
```
