@echo off
REM Script batch pour exécuter process_gloabl.py avec le bon environnement virtuel
REM Usage: run.bat

cd /d "%~dp0"

REM Vérifier si l'environnement virtuel existe
if not exist "venv\Scripts\python.exe" (
    echo Environnement virtuel non trouvé. Création en cours...
    python -m venv venv
    echo Installation des dépendances...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    goto :run
)

REM Activer l'environnement virtuel et exécuter
call venv\Scripts\activate.bat
python src\process_gloabl.py

:run
pause


