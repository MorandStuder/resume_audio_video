# Outlook Cleaner - Outils de Nettoyage Outlook 365

Collection d'outils Python pour nettoyer automatiquement votre boîte mail Outlook 365 en fonction de règles configurables, utilisant l'API Microsoft Graph.

## 🚀 Scripts Principaux

### 1. `outlook_cleaner_improved.py` - Script Tout-en-Un (RECOMMANDÉ)
**Script principal avec toutes les fonctionnalités avancées**

**Fonctionnalités :**
- ✅ Analyse et récapitulatif des emails (export Excel)
- ✅ Nettoyage intelligent des pièces jointes avec tri par taille
- ✅ Gestion robuste des erreurs API et timeouts
- ✅ Mode diagnostic complet
- ✅ Configuration flexible via CLI ou fichier JSON
- ✅ Support multi-dossiers (sentitems, inbox, archive, etc.)
- ✅ Filtrage par mot-clé, âge, taille
- ✅ Logs détaillés et progress bars

**Utilisation :**
```bash
# Créer un récapitulatif des emails envoyés
python outlook_cleaner_improved.py --action summary --folder sentitems

# Nettoyage en mode test (par défaut)
python outlook_cleaner_improved.py --action clean --size-threshold-mb 10 --age-threshold-days 365

# Nettoyage réel avec confirmation
python outlook_cleaner_improved.py --action clean --size-threshold-mb 5 --age-threshold-days 30 --execute

# Diagnostic complet
python outlook_cleaner_improved.py --action diagnostic

# Supprimer TOUTES les pièces jointes (attention !)
python outlook_cleaner_improved.py --action clean --all-attachments --execute
```

**Options principales :**
- `--action` : summary/clean/diagnostic
- `--folder` : sentitems/inbox/archive/etc.
- `--size-threshold-mb` : Seuil de taille en Mo
- `--age-threshold-days` : Âge minimum en jours
- `--subject-filter` : Mot-clé dans l'objet
- `--limit` : Nombre max d'emails
- `--execute` : Exécution réelle (mode test par défaut)
- `--all-attachments` : Supprimer toutes les PJ

---

### 2. `clean_sent_items_simple.py` - Nettoyage Simplifié
**Script spécialisé pour les éléments envoyés avec gestion robuste**

**Fonctionnalités :**
- ✅ Nettoyage ciblé des éléments envoyés
- ✅ Gestion automatique des erreurs API et retry
- ✅ Configuration persistante dans `config_clean.json`
- ✅ Mode test par défaut pour la sécurité
- ✅ Logs détaillés avec rotation
- ✅ Filtrage flexible par taille, âge, mot-clé

**Utilisation :**
```bash
# Test basique (mode dry-run)
python clean_sent_items_simple.py

# Nettoyage ciblé avec paramètres
python clean_sent_items_simple.py --size-threshold-mb 5 --age-threshold-days 30 --limit 100

# Exécution réelle (ATTENTION !)
python clean_sent_items_simple.py --size-threshold-mb 10 --age-threshold-days 365 --execute

# Filtrage par mot-clé
python clean_sent_items_simple.py --subject-filter "rapport" --limit 50
```

**Options :**
- `--size-threshold-mb` : Seuil de taille (défaut: 10 Mo)
- `--age-threshold-days` : Âge minimum (défaut: 365 jours, -1 pour tous)
- `--subject-filter` : Mot-clé dans l'objet
- `--limit` : Nombre max d'emails (défaut: 1000)
- `--folder` : Dossier à traiter (défaut: sentitems)
- `--execute` : Exécution réelle (sans = mode test)

---

### 3. `delete_all_attachments.py` - Suppression Complète
**Script pour supprimer TOUTES les pièces jointes de tous les dossiers**

**Fonctionnalités :**
- ✅ Analyse complète de tous les dossiers mail
- ✅ Suppression de toutes les pièces jointes
- ✅ Tri par taille (du plus gros au plus petit)
- ✅ Statistiques détaillées par dossier
- ✅ Mode test par défaut
- ✅ Gestion des dossiers imbriqués

**Utilisation :**
```bash
# Analyse complète de tous les dossiers
python delete_all_attachments.py --analyze

# Suppression en mode test (par défaut)
python delete_all_attachments.py --limit 100

# Suppression réelle (ATTENTION !)
python delete_all_attachments.py --execute --limit 500
```

**Options :**
- `--analyze` : Analyse complète sans suppression
- `--limit` : Nombre max d'emails par dossier
- `--execute` : Exécution réelle (sans = mode test)
- `--folder` : Dossier spécifique (défaut: tous)

---

### 4. `clean_archive_attachments.py` - Nettoyage Archives
**Script spécialisé pour nettoyer les archives avec sauvegarde locale**

**Fonctionnalités :**
- ✅ Nettoyage du dossier Archive uniquement
- ✅ Sauvegarde automatique locale avant suppression
- ✅ Critères : PJ >1 Mo ET >3 ans (paramétrables)
- ✅ Structure de sauvegarde organisée par date/objet
- ✅ Mode test par défaut
- ✅ Gestion des caractères spéciaux dans les noms

**Utilisation :**
```bash
# Nettoyage en mode test (par défaut)
python clean_archive_attachments.py --limit 100

# Nettoyage réel avec critères personnalisés
python clean_archive_attachments.py --execute --limit 500

# Critères personnalisés
python clean_archive_attachments.py --min-size-mb 1 --min-age-days 1730 --execute
```

**Options :**
- `--execute` : Exécution réelle (sans = mode test)
- `--limit` : Nombre max d'emails (défaut: 500)
- `--min-size-mb` : Taille minimum en Mo (défaut: 1)
- `--min-age-days` : Âge minimum en jours (défaut: 1095 = 3 ans)

Note : Les critères de taille (1 Mo) et d'âge (3 ans) sont fixés dans le code.
Pour les modifier, éditer les valeurs par défaut dans la fonction `process_archive_attachments()`.

---

### 5. `folder_analyzer.py` - Analyse et Configuration des Dossiers
**Script d'analyse avancée avec gestion des actions par dossier**

**Fonctionnalités :**
- ✅ Analyse récursive de tous les dossiers Outlook
- ✅ Génération d'un rapport Excel détaillé
- ✅ Configuration des actions par dossier
- ✅ Héritage automatique des actions pour les sous-dossiers
- ✅ Historique des actions effectuées
- ✅ Persistance de la configuration (JSON)

**Utilisation :**
```bash
# Analyse complète et génération du rapport
python folder_analyzer.py

# Configuration via Python :
from folder_analyzer import OutlookFolderAnalyzer

analyzer = OutlookFolderAnalyzer()

# Définir des actions pour un dossier
analyzer.set_folder_action(
    folder_name="Boîte de réception",
    delete_attachments=True,
    max_age_days=365,
    min_size_mb=10.0
)

# Enregistrer une action effectuée
analyzer.record_action(
    folder_name="Boîte de réception",
    action="delete_attachments",
    count=50,
    size_mb=500.0
)
```

**Fichiers générés :**
- `folder_analysis.xlsx` : Rapport détaillé avec statistiques et actions
- `folder_config.json` : Configuration et historique des actions

**Colonnes du rapport :**
- Dossier : Nom du dossier
- Chemin : Hiérarchie du dossier
- Nombre d'emails : Total des emails
- Taille totale (Mo) : Espace total utilisé
- Nombre de PJ : Nombre de pièces jointes
- Taille PJ (Mo) : Espace utilisé par les PJ
- Supprimer PJ : Action configurée
- Age max (jours) : Limite d'âge configurée
- Taille min PJ (Mo) : Taille minimum configurée
- Hérité de : Dossier parent si hérité
- Dernière action : Type de la dernière action
- Date dernière action : Date de la dernière action

---

## 📋 Prérequis

### Variables d'environnement (fichier `.env`)
```bash
OUTLOOK_CLIENT_ID=votre_client_id
OUTLOOK_CLIENT_SECRET=votre_client_secret
TENANT_ID=votre_tenant_id
OUTLOOK_USER_EMAIL=votre_email@domaine.com
```

### Dépendances Python
```bash
pip install -r requirements.txt
```

**Packages requis :**
- `azure-identity` : Authentification Microsoft Graph
- `requests` : Appels API HTTP
- `python-dotenv` : Gestion des variables d'environnement
- `pandas` : Export Excel et manipulation de données
- `tqdm` : Barres de progression
- `openpyxl` : Support Excel

---

## 🔧 Installation

1. **Cloner le dépôt :**
```bash
git clone https://github.com/votre-username/outlook-cleaner.git
cd outlook-cleaner
```

2. **Installer les dépendances :**
```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement :**
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos identifiants
notepad .env
```

4. **Tester la configuration :**
```bash
python outlook_cleaner_improved.py --action diagnostic
```

---

## 🛡️ Sécurité

### Fonctionnalités de sécurité intégrées :
- ✅ **Mode test par défaut** : Aucune suppression sans confirmation
- ✅ **Confirmation obligatoire** : Taper 'OUI' pour les suppressions réelles
- ✅ **Logs détaillés** : Traçabilité complète des actions
- ✅ **Sauvegarde automatique** : PJ sauvegardées avant suppression (Archive)
- ✅ **Gestion des erreurs** : Retry automatique et gestion des timeouts
- ✅ **Configuration persistante** : Paramètres sauvegardés dans JSON

### Bonnes pratiques :
1. **Toujours commencer par un test** avec `--limit 10`
2. **Vérifier les logs** avant toute exécution réelle
3. **Utiliser le diagnostic** pour analyser l'impact
4. **Sauvegarder manuellement** les PJ importantes avant nettoyage

---

## 📊 Utilisation Recommandée

### Démarrage rapide :
```bash
# 1. Diagnostic initial
python outlook_cleaner_improved.py --action diagnostic

# 2. Test sur un petit échantillon
python outlook_cleaner_improved.py --action clean --limit 10 --size-threshold-mb 5

# 3. Nettoyage progressif
python outlook_cleaner_improved.py --action clean --size-threshold-mb 10 --age-threshold-days 365 --limit 100

# 4. Nettoyage complet si satisfait
python outlook_cleaner_improved.py --action clean --size-threshold-mb 10 --age-threshold-days 365 --execute
```

### Scénarios d'usage :

**Nettoyage régulier des éléments envoyés :**
```bash
python clean_sent_items_simple.py --size-threshold-mb 5 --age-threshold-days 30 --execute
```

**Nettoyage des archives anciennes :**
```bash
python clean_archive_attachments.py --execute --limit 200
```

**Analyse complète de la boîte mail :**
```bash
python delete_all_attachments.py --analyze
```