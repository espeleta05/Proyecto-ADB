# Script para iniciar la app y el túnel público

Write-Host "=== INICIANDO APLICACIÓN FLASK ===" -ForegroundColor Green

# Activar venv e iniciar Flask en background
$flaskJob = Start-Job -ScriptBlock {
    Set-Location "c:\Users\eugenio\OneDrive\Documentos\C++\vacunas_backend"
    & .\.venv\Scripts\Activate.ps1
    python app.py 2>&1 | Tee-Object -FilePath "flask.log"
}

Write-Host "✓ Flask iniciándose..." -ForegroundColor Green
Start-Sleep -Seconds 3

# Verificar que Flask está corriendo
$result = Test-NetConnection 127.0.0.1 -Port 5000
if ($result.TcpTestSucceeded) {
    Write-Host "✓ Flask está escuchando en puerto 5000" -ForegroundColor Green
} else {
    Write-Host "✗ Error: Flask no está respondiendo en puerto 5000" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== ABRIENDO TÚNEL PÚBLICO ===" -ForegroundColor Green
Write-Host "Manteniendo esta ventana abierta..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar SSH tunnel (sin -N para ver el output con la URL)
ssh -R 80:localhost:5000 nokey@localhost.run

Write-Host ""
Write-Host "Túnel cerrado. Para volver a abrir, ejecuta este script de nuevo." -ForegroundColor Yellow
