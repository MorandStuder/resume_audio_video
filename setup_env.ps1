# Script pour configurer/réparer l'environnement virtuel
# Usage: .\setup_env.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "=== Configuration de l'environnement virtuel ===" -ForegroundColor Cyan

# Vérifier ou créer l'environnement virtuel
$venvPath = Join-Path $scriptDir "venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Mise à jour de pip..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip

Write-Host "Installation des dépendances (cela peut prendre plusieurs minutes)..." -ForegroundColor Yellow
& $pythonExe -m pip install -r requirements.txt

Write-Host "`n✅ Environnement configuré avec succès!" -ForegroundColor Green
Write-Host "Pour exécuter le script:" -ForegroundColor Cyan
Write-Host "  .\run.ps1" -ForegroundColor White
Write-Host "  ou" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\python.exe src\process_gloabl.py" -ForegroundColor White


