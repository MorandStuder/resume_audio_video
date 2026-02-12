# Script PowerShell pour lancer automatiquement le backend et le frontend
# Usage: .\start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Amazon Invoice Downloader - Startup  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que nous sommes dans le bon dossier
if (-not (Test-Path ".\backend\main.py")) {
    Write-Host "ERREUR: Ce script doit être exécuté depuis la racine du projet Get-Invoices" -ForegroundColor Red
    exit 1
}

# Vérifier que le fichier .env existe
if (-not (Test-Path ".\.env")) {
    Write-Host "ERREUR: Fichier .env non trouvé!" -ForegroundColor Red
    Write-Host "Veuillez copier .env.example vers .env et configurer vos identifiants" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commande: Copy-Item .env.example .env" -ForegroundColor Yellow
    exit 1
}

# Vérifier que Python est installé
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Vérifier que Node.js est installé
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js détecté: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Démarrage des serveurs..." -ForegroundColor Cyan
Write-Host ""

# Fonction pour tuer les processus sur un port
function Kill-ProcessOnPort {
    param($Port)
    $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($process) {
        Write-Host "Arrêt du processus existant sur le port $Port..." -ForegroundColor Yellow
        Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Libérer les ports si nécessaire
Kill-ProcessOnPort 8000
Kill-ProcessOnPort 3000

# Créer un fichier de log
$logDir = "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# Démarrer le backend dans une nouvelle fenêtre PowerShell
Write-Host "→ Démarrage du backend FastAPI (port 8000)..." -ForegroundColor Yellow
$backendScript = @"
Set-Location '$PWD'
`$env:PYTHONPATH = '.'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Backend FastAPI - Port 8000          ' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API: http://localhost:8000' -ForegroundColor Green
Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor Green
Write-Host ''
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# Attendre que le backend démarre
Write-Host "Attente du démarrage du backend..." -ForegroundColor Yellow
$maxRetries = 30
$retries = 0
$backendReady = $false

while ($retries -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Ignorer les erreurs et réessayer
    }
    Start-Sleep -Seconds 1
    $retries++
    Write-Host "." -NoNewline
}

Write-Host ""

if (-not $backendReady) {
    Write-Host "✗ Le backend n'a pas démarré correctement" -ForegroundColor Red
    Write-Host "Vérifiez la fenêtre du backend pour les erreurs" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Backend démarré avec succès!" -ForegroundColor Green
Write-Host ""

# Démarrer le frontend dans une nouvelle fenêtre PowerShell
Write-Host "→ Démarrage du frontend React (port 3000)..." -ForegroundColor Yellow
$frontendScript = @"
Set-Location '$PWD\frontend'
`$env:BROWSER = 'none'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Frontend React - Port 3000           ' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Application: http://localhost:3000' -ForegroundColor Green
Write-Host ''
npm start
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

# Attendre que le frontend démarre
Write-Host "Attente du démarrage du frontend..." -ForegroundColor Yellow
$retries = 0
$frontendReady = $false

while ($retries -lt 60) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }
    } catch {
        # Ignorer les erreurs et réessayer
    }
    Start-Sleep -Seconds 1
    $retries++
    if ($retries % 5 -eq 0) {
        Write-Host "." -NoNewline
    }
}

Write-Host ""

if ($frontendReady) {
    Write-Host "✓ Frontend démarré avec succès!" -ForegroundColor Green
} else {
    Write-Host "⚠ Le frontend prend plus de temps que prévu à démarrer" -ForegroundColor Yellow
    Write-Host "Vérifiez la fenêtre du frontend pour le statut" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Application démarrée avec succès!    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs disponibles:" -ForegroundColor White
Write-Host "  • Frontend:      http://localhost:3000" -ForegroundColor Green
Write-Host "  • Backend API:   http://localhost:8000" -ForegroundColor Green
Write-Host "  • API Docs:      http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Pour arrêter l'application, fermez les fenêtres PowerShell du backend et du frontend" -ForegroundColor Yellow
Write-Host ""

# Ouvrir le navigateur
Write-Host 'Ouverture du navigateur...' -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process 'http://localhost:3000'

Write-Host ""
Write-Host 'Appuyez sur une touche pour fermer cette fenetre...' -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
