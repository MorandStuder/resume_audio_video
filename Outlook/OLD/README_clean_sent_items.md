# Nettoyage des Pièces Jointes des Éléments Envoyés Outlook

Ce script autonome permet de supprimer automatiquement les pièces jointes volumineuses des emails envoyés dans Outlook, selon des critères de taille et d'âge configurables.

## Fonctionnalités

- **Nettoyage ciblé** : Supprime uniquement les pièces jointes des éléments envoyés
- **Critères configurables** : Seuil de taille et âge minimum des emails
- **Unités flexibles** : Taille en Ko, Mo, Go et âge en mois ou années
- **Mode test** : Simulation sans suppression réelle (par défaut)
- **Sauvegarde automatique** : Sauvegarde les PJ avant suppression
- **Logging détaillé** : Journal complet des opérations
- **Interface en ligne de commande** : Paramètres configurables

## Prérequis

1. **Variables d'environnement** : Créez un fichier `.env` avec :
   ```
   OUTLOOK_CLIENT_ID=votre_client_id
   OUTLOOK_CLIENT_SECRET=votre_client_secret
   TENANT_ID=votre_tenant_id
   OUTLOOK_USER_EMAIL=votre_email@domaine.com
   ```

2. **Dépendances Python** :
   ```bash
   pip install azure-identity msgraph-core python-dotenv pandas tqdm
   ```

## Utilisation

### Mode test (recommandé pour commencer)

```bash
# Test avec paramètres par défaut (10 Mo, 2 ans)
python clean_sent_items.py

# Test avec seuil en moo et âge en mois
python clean_sent_items.py --size-threshold 500 --size-unit mo --age-threshold 0 --age-unit mois

# Test avec seuil en Go
python clean_sent_items.py --size-threshold 1 --size-unit go --age-threshold 1 --age-unit ans

# Test sans sauvegarde des PJ
python clean_sent_items.py --no-backup

python clean_sent_items_simple.py --size-threshold-mb 2 --age-threshold-days 0 --subject-filter "Club Data" --limit 50

```

### Mode exécution (suppression réelle)

```bash
# Exécution avec paramètres par défaut
python clean_sent_items.py --execute

# Exécution avec seuil en Ko et âge en mois
python clean_sent_items.py --size-threshold 10000 --size-unit ko --age-threshold 3 --age-unit mois --execute

# Exécution avec seuil en Go
python clean_sent_items.py --size-threshold 2 --size-unit go --age-threshold 5 --age-unit ans --execute
```

## Paramètres

| Paramètre | Description | Défaut | Options |
|-----------|-------------|--------|---------|
| `--size-threshold` | Seuil de taille pour supprimer les PJ | 10 | Nombre positif |
| `--size-unit` | Unité de taille | mo | ko, mo, go |
| `--age-threshold` | Âge minimum pour traiter les emails | 2 | Nombre positif |
| `--age-unit` | Unité d'âge | ans | mois, ans |
| `--no-backup` | Ne pas sauvegarder les PJ avant suppression | False | - |
| `--execute` | Exécuter réellement les suppressions | False | - |

## Exemples d'utilisation

### 1. Analyse préliminaire avec Ko
```bash
# Voir ce qui serait supprimé (fichiers > 5 Ko de plus d'1 mois)
python clean_sent_items.py --size-threshold 5 --size-unit ko --age-threshold 1 --age-unit mois
```

### 2. Nettoyage conservateur avec Go
```bash
# Supprimer seulement les très gros fichiers anciens (> 1 Go, > 5 ans)
python clean_sent_items.py --size-threshold 1 --size-unit go --age-threshold 5 --age-unit ans --execute
```

### 3. Nettoyage agressif avec Mo et mois
```bash
# Supprimer tous les fichiers > 5 Mo de plus d'6 mois
python clean_sent_items.py --size-threshold 5 --size-unit mo --age-threshold 6 --age-unit mois --execute
```

### 4. Nettoyage de petits fichiers
```bash
# Supprimer les fichiers > 100 Ko de plus d'1 an
python clean_sent_items.py --size-threshold 100 --size-unit ko --age-threshold 1 --age-unit ans --execute
```

### 5. Nettoyage sans sauvegarde
```bash
# Suppression directe sans sauvegarde (attention !)
python clean_sent_items.py --no-backup --execute
```

## Fichiers générés

- `clean_sent_items.log` : Journal détaillé des opérations
- `sauvegardes_pj/Elements_envoyes/` : Dossier contenant les PJ sauvegardées

## Sécurité

- **Mode test par défaut** : Aucune suppression sans l'option `--execute`
- **Confirmation requise** : Demande de confirmation en mode exécution
- **Sauvegarde automatique** : Les PJ sont sauvegardées avant suppression
- **Logging complet** : Toutes les actions sont enregistrées

## Statistiques retournées

Le script retourne un dictionnaire avec :
- `emails_processed` : Nombre d'emails traités
- `attachments_found` : Nombre total de pièces jointes trouvées
- `attachments_deleted` : Nombre de pièces jointes supprimées
- `total_size_bytes` : Espace libéré en octets
- `total_size_display` : Espace libéré dans l'unité spécifiée
- `size_unit` : Unité de taille utilisée
- `dry_run` : Indique si c'était un test

## Intégration dans le script principal

Vous pouvez aussi utiliser la fonction directement dans votre code :

```python
from clean_sent_items import clean_sent_items_attachments

# Test avec Ko et mois
stats = clean_sent_items_attachments(
    size_threshold=5000,
    size_unit='ko',
    age_threshold=6,
    age_unit='mois',
    backup_attachments=True,
    dry_run=True
)

# Exécution réelle avec Mo et ans
stats = clean_sent_items_attachments(
    size_threshold=10,
    size_unit='mo',
    age_threshold=2,
    age_unit='ans',
    backup_attachments=True,
    dry_run=False
)
```

## Conversion des unités

Le script gère automatiquement les conversions :

### Unités de taille
- **Ko** : 1 Ko = 1 024 octets
- **Mo** : 1 Mo = 1 048 576 octets
- **Go** : 1 Go = 1 073 741 824 octets

### Unités d'âge
- **Mois** : 1 mois = 30,44 jours (moyenne)
- **Ans** : 1 an = 365,25 jours (moyenne)

## Dépannage

### Erreur d'authentification
- Vérifiez vos variables d'environnement dans le fichier `.env`
- Assurez-vous que votre application Azure a les bonnes permissions

### Erreur de permissions
- Vérifiez que votre application Azure a accès aux emails
- Les permissions nécessaires : `Mail.ReadWrite`

### Fichier de sauvegarde ouvert
- Fermez le fichier Excel s'il est ouvert
- Vérifiez les permissions d'écriture dans le dossier

### Erreur d'unité
- Vérifiez que les unités spécifiées sont correctes : `ko`, `mo`, `go` pour la taille et `mois`, `ans` pour l'âge

## Notes importantes

1. **Testez toujours en mode test** avant d'exécuter réellement
2. **Vérifiez les sauvegardes** avant de supprimer définitivement
3. **Surveillez les logs** pour détecter d'éventuelles erreurs
4. **Adaptez les seuils** selon vos besoins et contraintes
5. **Utilisez les bonnes unités** pour éviter les suppressions non désirées

## Support

En cas de problème, consultez :
- Le fichier `clean_sent_items.log` pour les détails d'erreur
- La documentation Microsoft Graph pour les permissions
- Les logs de l'application Azure dans le portail Microsoft 