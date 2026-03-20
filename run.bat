@echo off
echo ================================
echo Iniciando sistema de la clinica
echo ================================

REM Si ya existe el venv, solo activar y correr
IF EXIST venv\Scripts\python.exe (
    echo Entorno virtual encontrado, iniciando servidor...
    echo.
    echo ================================
    echo Ejecutando servidor...
    echo ================================
    venv\Scripts\python.exe app.py
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
    py -3.13 -m venv venv
) ELSE (
    "%PY313%" -m venv venv
)

echo Entorno virtual creado
venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

echo Instalando dependencias...
venv\Scripts\pip.exe install -r requirements.txt
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

venv\Scripts\python.exe app.py

echo.
echo El servidor se detuvo.
pause