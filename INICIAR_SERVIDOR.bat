@echo off
REM Script simple para iniciar el servidor con tunnel automaticamente

echo.
echo ====================================================
echo    SERVIDOR DE VACUNAS - ACCESO PUBLICO
echo ====================================================
echo.

cd /d "c:\Users\eugenio\OneDrive\Documentos\C++\vacunas_backend"

REM Abrir terminal 1 con Flask
echo Abriendo Terminal 1: Flask...
start "Flask Server" cmd /k "call .venv\Scripts\activate.bat && python app.py"

REM Esperar a que Flask arranque
timeout /t 3 /nobreak

REM Abrir terminal 2 con SSH tunnel
echo Abriendo Terminal 2: SSH Tunnel...
start "Public Tunnel" cmd /k "ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=10 -R 80:localhost:5000 nokey@localhost.run"

echo.
echo ====================================================
echo Ambas terminales estan abiertas.
echo Ambas deben mantenerse ABIERTAS para que funcione.
echo.
echo - Terminal 1: Flask Server
echo - Terminal 2: SSH Tunnel -> URL publica
echo ====================================================
echo.

pause
