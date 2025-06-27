#!/bin/bash

# Script de démarrage pour l'application Eleven Strategy LinkedIn
# Ce script lance le backend FastAPI et le frontend React

# Démarrer le backend
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo "Backend FastAPI démarré sur http://localhost:8000"

# Attendre que le backend soit prêt
Start-Sleep -Seconds 5

# Démarrer le frontend
cd ../frontend
npm start &
echo "Frontend React démarré sur http://localhost:3000"

echo "Application Eleven Strategy LinkedIn démarrée avec succès!"
echo "Accédez à l'application via http://localhost:3000"
echo "Pour arrêter l'application, utilisez la commande: Stop-Process -Name 'node','uvicorn'"
