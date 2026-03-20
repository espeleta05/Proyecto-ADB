@echo off
echo ================================================
echo   Configuracion inicial - Sistema de Vacunacion
echo ================================================

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
    echo.
    echo [ERROR] No se encontro Python 3.13.
    echo Descargalo desde: https://www.python.org/downloads/
    echo Durante la instalacion marca "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Python 3.13 encontrado: %PY313%
echo.

REM Borrar venvs viejos
IF EXIST venv  rmdir /s /q venv
IF EXIST .venv rmdir /s /q .venv

REM Crear entorno virtual
echo Creando entorno virtual...
IF "%PY313%"=="py -3.13" (
    py -3.13 -m venv venv
) ELSE (
    "%PY313%" -m venv venv
)

echo Actualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

echo Instalando dependencias (PostgreSQL)...
venv\Scripts\pip.exe install -r requirements.txt
IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Fallo la instalacion de dependencias.
    echo Verifica tu conexion a internet e intenta de nuevo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Instalacion completada con exito
echo.
echo   IMPORTANTE: Antes de correr el servidor,
echo   edita el archivo .env con tus credenciales
echo   de PostgreSQL.
echo.
echo   Para iniciar el servidor ejecuta: run.bat
echo ================================================
echo.
pause