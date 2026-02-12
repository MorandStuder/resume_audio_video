# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.1.0] - 2026-02-11

### Ajouté

- Scripts de lancement automatique (start.ps1, start.sh, stop.ps1, stop.sh)
- Validation automatique de la configuration au démarrage
- 9 nouveaux tests (couverture passée de 23% à 35%)
- Fichier .env.example pour faciliter la configuration
- Documentation enrichie avec changelog et liens rapides

### Corrigé

- ChromeDriver : Problème d'initialisation du driver Selenium résolu
- Configuration : Encodage UTF-8, espaces blancs, BOM supprimés
- FastAPI : Migration de @app.on_event() vers lifespan handlers modernes
- TypeScript : Tous les warnings résolus (types de retour ajoutés)
- Tests : test_login_success corrigé et passe avec succès

### Améliorations

- Tests : 4/5 (80%) → 14/14 (100%) passants
- Couverture : 23% → 35% (+52%)
- Build : 7 warnings → 0 warning
- Expérience utilisateur : Démarrage en une commande

Pour plus de détails, consultez le README.md section "Changelog Détaillé".

## [1.0.0] - Version initiale

- Application de téléchargement de factures Amazon
- Backend FastAPI + Frontend React/TypeScript
- Support Selenium (Chrome/Firefox)
- Authentification Amazon avec 2FA
- Tests unitaires de base
