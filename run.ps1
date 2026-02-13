# Script PowerShell pour exécuter process_gloabl.py avec le bon environnement virtuel
# Usage: .\run.ps1

$ErrorActionPreference = "Stop"

# Déterminer le répertoire du script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Vérifier si l'environnement virtuel existe
$venvPath = Join-Path $scriptDir "venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Environnement virtuel non trouvé dans: $venvPath" -ForegroundColor Red
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv venv
    
    Write-Host "Installation des dépendances..." -ForegroundColor Yellow
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r requirements.txt
}

Write-Host "✅ Utilisation de l'environnement: $pythonExe" -ForegroundColor Green

# Exécuter le script avec le bon environnement
& $pythonExe "src\process_gloabl.py"


