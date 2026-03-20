# Script automatizado para iniciar Flask + SSH Tunnel
# Solo ejecuta este script y todo funciona automáticamente

$SCRIPT_DIR = "c:\Users\eugenio\OneDrive\Documentos\C++\vacunas_backend"
Set-Location $SCRIPT_DIR

Write-Host "
╔════════════════════════════════════════════════════════════╗
║         INICIANDO SERVIDOR DE VACUNAS                      ║
╚════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# Activar environment
& .\.venv\Scripts\Activate.ps1

# Iniciar Flask en background
Write-Host "▶ Iniciando Flask..." -ForegroundColor Green
$FlaskProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$SCRIPT_DIR'; & .\.venv\Scripts\Activate.ps1; python app.py" -PassThru
Start-Sleep -Seconds 3

# Verificar que Flask está funcionando
$TestConnection = Test-NetConnection 127.0.0.1 -Port 5000 -WarningAction SilentlyContinue
if ($TestConnection.TcpTestSucceeded) {
    Write-Host "✓ Flask corriendo en http://localhost:5000" -ForegroundColor Green
} else {
    Write-Host "✗ Error: Flask no está respondiendo" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "▶ Iniciando SSH Tunnel..." -ForegroundColor Green
Write-Host "Esperando URL pública..." -ForegroundColor Yellow
Write-Host ""

# Iniciar SSH tunnel con keep-alive
& {
    ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=10 -R 80:localhost:5000 nokey@localhost.run
}

