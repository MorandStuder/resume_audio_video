# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).
Versionnement sémantique : [SemVer](https://semver.org/lang/fr/).

---

## [1.1.0] — 2026-03-12

### Sécurité
- Suppression de `config.py` (credentials en clair) : migration vers `.env` + `python-dotenv`
- Ajout de `.env.example` versionné
- Suppression des fichiers de debug HTML du tracking git

### Amélioré
- Typage strict sur toutes les fonctions (type hints Python 3.10+)
- Remplacement de `print()` par `logging` configurable
- Chemins fichiers migrés vers `pathlib.Path`
- Remplacement des sélecteurs CSS invalides (`:contains()`) par des appels BeautifulSoup natifs
- `close()` implémenté réellement (appel `driver.quit()`)
- Mode incrémental : avertissement interactif au lieu d'abandon silencieux en cas d'incohérence
- Sleep post-login remplacé par `WebDriverWait` sur redirection d'URL
- Constantes nommées pour sélecteurs CSS et port de debug

### Ajouté
- Suite de tests unitaires : 13 tests couvrant extraction, CSV, mode incrémental, détection Chrome
- `requirements-dev.txt` pour les dépendances de développement

### Packaging
- Versions des dépendances figées avec `==` dans `requirements.txt`
- Ajout de `python-dotenv==1.0.0` dans les dépendances

---

## [1.0.0] — 2025-04-13

### Ajouté
- Version initiale : scraping des films vus et films à voir depuis Allociné
- Export CSV avec colonnes dynamiques par plateforme de streaming
- Mode incrémental pour `FilmsVusScraper`
- Réutilisation d'une session Chrome existante via port de debug 9222
