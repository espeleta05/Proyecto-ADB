@echo off
setlocal enabledelayedexpansion

cd /d "c:\Users\eugenio\OneDrive\Documentos\C++\vacunas_backend"

echo ============================================
echo Iniciando ambiente virtual...
echo ============================================

call .venv\Scripts\activate.bat

echo.
echo ============================================
echo Verificando conexion a base de datos...
echo ============================================

python -c "from app import db; print('✓ Base de datos OK')" 2>&1

if %errorlevel% neq 0 (
    echo Error: No se pudo conectar a la base de datos
    pause
    exit /b 1
)

echo.
echo ============================================
echo INICIANDO FLASK - NO CIERRES ESTA VENTANA
echo ============================================
echo.
echo Acceso local: http://localhost:5000
echo Acceso en red: http://172.32.216.26:5000
echo.
echo Presiona Ctrl+C para detener
echo.

python app.py

pause
