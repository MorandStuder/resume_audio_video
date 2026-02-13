# Script PowerShell pour arrêter le backend et le frontend
# Usage: .\stop.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Amazon Invoice Downloader - Stop     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Fonction pour tuer les processus sur un port
function Kill-ProcessOnPort {
    param($Port, $Name)
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            $processes = $connections | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($procId in $processes) {
                Write-Host "→ Arrêt du $Name (PID: $procId)..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
            Write-Host "✓ $Name arrêté" -ForegroundColor Green
        } else {
            Write-Host "ℹ Aucun processus trouvé sur le port $Port" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠ Erreur lors de l'arrêt du $Name : $_" -ForegroundColor Yellow
    }
}

# Arrêter le backend (port 8000)
Kill-ProcessOnPort 8000 "Backend"

# Arrêter le frontend (port 3000)
Kill-ProcessOnPort 3000 "Frontend"

Write-Host ""
Write-Host "✓ Application arrêtée avec succès!" -ForegroundColor Green
Write-Host ""
