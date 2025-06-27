# Outlook Cleaner

Un outil pour nettoyer automatiquement votre boîte mail Outlook 365 en fonction de règles configurables.

## Fonctionnalités

- Analyse de la boîte mail et création d'un récapitulatif des emails
- Configuration des règles de nettoyage via un fichier Excel
- Sauvegarde automatique des pièces jointes avant suppression
- Nettoyage des pièces jointes trop volumineuses
- Nettoyage des emails avec pièces jointes trop volumineuses
- Mise à jour automatique des statistiques tout en préservant les règles

## Scripts disponibles

### 1. `clean_sent_items_simple.py` (RECOMMANDÉ)
Script simplifié et robuste pour nettoyer les pièces jointes des éléments envoyés.

**Avantages :**
- Gestion robuste des erreurs API
- Mode test par défaut (dry-run)
- Configuration flexible via ligne de commande ou fichier JSON
- Logs détaillés
- Retry automatique en cas de timeout

**Utilisation :**
```bash
# Test basique (mode dry-run)
python clean_sent_items_simple.py

# Avec paramètres personnalisés
python clean_sent_items_simple.py --size-threshold-mb 5 --age-threshold-days 30 --limit 100

# Exécution réelle (ATTENTION !)
python clean_sent_items_simple.py --size-threshold-mb 10 --age-threshold-days 365 --execute

# Filtrage par mot-clé dans l'objet
python clean_sent_items_simple.py --subject-filter "rapport" --limit 50
```

**Options disponibles :**
- `--size-threshold-mb` : Seuil de taille en Mo (défaut: 10)
- `--age-threshold-days` : Âge minimum en jours (défaut: 365, -1 pour tous)
- `--subject-filter` : Mot-clé dans l'objet
- `--limit` : Nombre max d'emails à traiter (défaut: 1000)
- `--folder` : Dossier à traiter (défaut: sentitems)
- `--execute` : Exécuter réellement (sans ce flag = mode test)
- `--no-backup` : Ne pas sauvegarder les PJ

### 2. `diagnostic_emails.py`
Script de diagnostic pour analyser les emails et leurs pièces jointes.

**Utilisation :**
```bash
python diagnostic_emails.py
```

### 3. `outlook_cleaner.py`
Script principal avec interface Excel (plus complexe).

## Prérequis

- Python 3.8 ou supérieur
- Un compte Microsoft 365 avec accès à l'API Graph
- Les permissions nécessaires pour l'application Azure AD

## Installation

1. Clonez ce dépôt :
```bash
git clone https://github.com/votre-username/outlook-cleaner.git
cd outlook-cleaner
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Créez un fichier `.env` avec vos identifiants :
```
OUTLOOK_CLIENT_ID=votre_client_id
OUTLOOK_CLIENT_SECRET=votre_client_secret
TENANT_ID=votre_tenant_id
OUTLOOK_USER_EMAIL=votre_email
```

## Utilisation recommandée

### Démarrage rapide avec `clean_sent_items_simple.py`

1. **Test initial** (recommandé) :
```bash
python clean_sent_items_simple.py --limit 10
```

2. **Analyse avec diagnostic** :
```bash
python diagnostic_emails.py
```

3. **Nettoyage ciblé** :
```bash
# Test sur emails de plus de 30 jours avec PJ > 5 Mo
python clean_sent_items_simple.py --age-threshold-days 30 --size-threshold-mb 5 --limit 100

# Exécution réelle si le test convient
python clean_sent_items_simple.py --age-threshold-days 30 --size-threshold-mb 5 --limit 100 --execute
```

### Configuration avancée

Le script sauvegarde automatiquement la configuration dans `config_clean.json`. Vous pouvez modifier ce fichier ou utiliser les paramètres en ligne de commande.

## Structure des fichiers

- `clean_sent_items_simple.py` : Script de nettoyage simplifié (RECOMMANDÉ)
- `diagnostic_emails.py` : Script de diagnostic
- `outlook_cleaner.py` : Programme principal avec interface Excel
- `config_clean.json` : Configuration du script simplifié
- `config_nettoyage.xlsx` : Configuration des règles de nettoyage
- `recap_emails.xlsx` : Récapitulatif des emails
- `sauvegardes_pj/` : Dossier de sauvegarde des pièces jointes
- `*.log` : Fichiers de log

## Sécurité

- Les identifiants sont stockés dans le fichier `.env` (non versionné)
- Mode test par défaut (dry-run) pour éviter les suppressions accidentelles
- Les pièces jointes sont sauvegardées avant suppression
- Confirmation requise avant toute suppression réelle

## Dépannage

### Erreurs courantes

1. **"Unterminated string starting at line 1"** : Résolu dans `clean_sent_items_simple.py`
2. **"Pièces jointes trouvées: 0"** : Vérifiez les paramètres de filtrage
3. **Timeout API** : Le script gère automatiquement les retry

### Conseils

- Commencez toujours par un test avec `--limit 10`
- Utilisez `diagnostic_emails.py` pour analyser vos emails
- Vérifiez les logs dans `clean_sent_items.log`
- Testez d'abord en mode dry-run (sans `--execute`)

## Licence

MIT 