# Système de Traitement Audio et Transcription

Ce projet est un ensemble d'outils pour le traitement audio, la transcription et l'analyse de contenu. Il permet de :
1. Découper des fichiers audio/vidéo en segments
2. Transcrire automatiquement le contenu
3. Générer des résumés avec différents modèles d'IA

## Structure du Projet

### Répertoires
- `src/` : Package Python contenant tous les scripts
- `segments_audio/` : Stockage des segments audio découpés
- `transcriptions/` : Stockage des transcriptions
- `resumes/` : Stockage des résumés générés

### Fichiers Principaux (dans src/)
- `process_gloabl.py` : Script principal qui orchestre tout le processus
- `resume.py` : Script pour générer uniquement le résumé des transcriptions existantes
- `Split.py` : Module de découpage audio
- `Whisper.py` : Module de transcription
- `Concatene.py` : Module de concaténation des transcriptions
- `test_summary.py` : Module de test des différents modèles de résumé

### Configuration et Développement
- `config.json` : Configuration des clés API (non versionné)
- `setup.py` : Configuration du package Python
- `pyproject.toml` : Configuration moderne du projet
- `LICENSE` : Licence MIT du projet

## Prérequis

### ffmpeg (obligatoire pour l'audio)
Ce projet nécessite [ffmpeg](https://ffmpeg.org/) pour l'extraction et l'encodage audio (MP3, WAV, etc.).

- **Windows** :
  1. (Recommandé) Installer via winget :
     ```bash
     winget install ffmpeg
     ```
     (ou `winget install Gyan.FFmpeg` selon le catalogue)
     > Le PATH est configuré automatiquement.
  2. (Alternative manuelle) Télécharger la version statique sur https://www.gyan.dev/ffmpeg/builds/
  3. Décompresser (ex : `C:\ffmpeg`)
  4. Ajouter `C:\ffmpeg\bin` à la variable d'environnement `PATH`
  5. Vérifier dans un terminal : `ffmpeg -version`
- **macOS** :
  ```bash
  brew install ffmpeg
  ```
- **Linux** :
  ```bash
  sudo apt install ffmpeg
  ```

## Installation

### Installation via pip
```bash
pip install -e .
```
Création env
python -m venv venv
  .\venv\Scripts\activate

### Installation des Dépendances
```bash
pip install -r requirements.txt
```

### Découpage Audio (NOUVEAU)
Le découpage audio/vidéo utilise maintenant le script `src/Split.py` (plus de pydub, compatible Python 3.13+).

> Le découpage fonctionne aussi bien pour les fichiers audio (MP3, WAV, etc.) que vidéo (MP4, AVI, etc.).

- **En ligne de commande** :
  ```bash
  python src/Split.py chemin/vers/ta_video.mp4 -d 30 -o segments_audio
  ```
  - `-d` : durée des segments en minutes (défaut : 30)
  - `-o` : dossier de sortie (défaut : segments_audio)

- **Dans le pipeline complet** :
  Le script principal `process_gloabl.py` utilise automatiquement cette méthode.

### Configuration
1. Créer un fichier `config.json` à la racine du projet avec vos clés API :
```json
{
    "OPENAI_API_KEY": "votre_clé_openai",
    "MISTRAL_API_KEY": "votre_clé_mistral"
}
```
Note : Le fichier `config.json` est exclu du versionnement pour des raisons de sécurité.

## Développement

### Formatage du Code
Le projet utilise :
- `black` pour le formatage du code
- `isort` pour l'organisation des imports

Pour formater le code :
```bash
black src/
isort src/
```

### Installation en Mode Développement
```bash
pip install -e ".[dev]"
```

## Mode d'Emploi

### 1. Processus Complet
Le script principal `process_gloabl.py` exécute toutes les étapes :
```bash
python src/process_gloabl.py
```
Étapes automatiques :
- Sélection du fichier audio/vidéo
- Découpage en segments
- Transcription avec Whisper
- Génération de résumés avec GPT-3.5

### 2. Résumé des Transcriptions
Le script `resume.py` permet de générer uniquement le résumé des transcriptions existantes :
```bash
python src/resume.py
```
Ce script est utile quand :
- Vous avez déjà des transcriptions dans le dossier `transcriptions/`
- Vous souhaitez uniquement générer un résumé sans refaire la transcription
- Vous voulez tester différents modèles de résumé

### 3. Utilisation des Modules Individuels

#### Découpage Audio (Split.py)
```bash
python src/Split.py
```
- Sélectionne un fichier audio ou vidéo
- Découpe en segments de 30 minutes
- Exporte en MP3 dans `segments_audio/`

#### Transcription (Whisper.py)
```bash
python src/Whisper.py
```
- Utilise le modèle Whisper "base"
- Transcrit tous les MP3 du dossier `segments_audio/`
- Sauvegarde les transcriptions dans `transcriptions/`

#### Concaténation (Concatene.py)
```bash
python src/Concatene.py
```
- Combine toutes les transcriptions
- Ajoute des horodatages
- Génère un fichier final structuré

#### Test des Résumés (test_summary.py)
```bash
python src/test_summary.py
```
Options de modèles :
1. GPT-3.5-turbo (OpenAI)
2. Claude-2 (Anthropic)
3. BART (Hugging Face)
4. GPT-3.5-turbo-16k
5. Mistral Large
6. Google PaLM 2

## Structure des Données

### Fichiers Audio
```
segments_audio/
    ├── segment_01.mp3
    ├── segment_02.mp3
    └── ...
```

### Transcriptions
```
transcriptions/
    ├── transcription_01.txt
    ├── transcription_02.txt
    └── transcription_complete.txt
```

### Résumés
```
resumes/
    ├── resume_01.txt
    ├── resume_02.txt
    └── resume_global.txt
```

## Notes Importantes
- Les clés API sont stockées uniquement dans `config.json` (non versionné)
- Le découpage audio utilise une durée fixe de 30 minutes par défaut
- La transcription utilise le modèle Whisper "base" (paramétrable)
- Les résumés peuvent être générés avec différents modèles d'IA
- Tous les fichiers sont encodés en UTF-8
- ffmpeg doit être installé et accessible dans le PATH
- Le découpage audio ne dépend plus de pydub/audioop (compatible Python 3.13+)
- Les autres scripts (transcription, résumé, concaténation) restent inchangés

## Dépannage
- Vérifier que le fichier `config.json` existe avec les clés API correctes
- S'assurer que les dossiers nécessaires existent
- Vérifier les formats de fichiers supportés
- En cas d'erreur, consulter les messages dans la console

## Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 