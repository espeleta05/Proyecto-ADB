@echo off
echo ================================
echo Iniciando sistema de la clinica
echo ================================

set "APP_PORT=5000"
set "APP_HOST=0.0.0.0"

REM Si ya existe el venv, solo activar y correr
IF EXIST .venv\Scripts\python.exe (
    echo Entorno virtual encontrado, iniciando servidor...
    netsh advfirewall firewall add rule name="Vacunas Backend 5000" dir=in action=allow protocol=TCP localport=%APP_PORT% >nul 2>&1
    for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"Direccion IPv4"') do (
        set "LAN_IP=%%A"
        goto :show_url
    )
    :show_url
    set "LAN_IP=%LAN_IP: =%"
    echo.
    echo ================================
    echo Ejecutando servidor...
    echo ================================
    if not "%LAN_IP%"=="" echo URL de acceso LAN: http://%LAN_IP%:%APP_PORT%
    echo URL local: http://127.0.0.1:%APP_PORT%
    set "USE_WAITRESS=1"
    set "APP_HOST=%APP_HOST%"
    set "APP_PORT=%APP_PORT%"
    .venv\Scripts\python.exe app.py
    echo.
    echo El servidor se detuvo.
    pause
    exit /b 0
)

REM Si no existe el venv, crearlo desde cero
echo Creando entorno virtual...

REM Buscar Python 3.13
SET PY313=
IF EXIST "C:\Python313\python.exe" SET PY313=C:\Python313\python.exe
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" SET PY313=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
IF EXIST "%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe" SET PY313=%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe

IF "%PY313%"=="" (
    py -3.13 --version >nul 2>&1
    IF NOT ERRORLEVEL 1 SET PY313=py -3.13
)

IF "%PY313%"=="" (
    echo [ERROR] No se encontro Python 3.13.
    echo Descargalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

IF "%PY313%"=="py -3.13" (
    py -3.13 -m venv .venv
) ELSE (
    "%PY313%" -m venv .venv
)

echo Entorno virtual creado
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

echo Instalando dependencias...
.venv\Scripts\pip.exe install -r requirements.txt
IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo.
echo ================================
echo Ejecutando servidor...
echo ================================

netsh advfirewall firewall add rule name="Vacunas Backend 5000" dir=in action=allow protocol=TCP localport=%APP_PORT% >nul 2>&1
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"Direccion IPv4"') do (
    set "LAN_IP=%%A"
    goto :show_url2
)
:show_url2
set "LAN_IP=%LAN_IP: =%"
if not "%LAN_IP%"=="" echo URL de acceso LAN: http://%LAN_IP%:%APP_PORT%
echo URL local: http://127.0.0.1:%APP_PORT%

set "USE_WAITRESS=1"
set "APP_HOST=%APP_HOST%"
set "APP_PORT=%APP_PORT%"

.venv\Scripts\python.exe app.py

echo.
echo El servidor se detuvo.
pause