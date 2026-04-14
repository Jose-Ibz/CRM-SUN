@echo off
REM ============================================================================
REM CRM VISITAS - Nautica Viamar
REM Lanzador automatico para Windows
REM ============================================================================

title CRM Visitas Comerciales - Viamar

echo.
echo ========================================
echo   CRM VISITAS - Nautica Viamar
echo   Control de visitas comerciales + IA
echo ========================================
echo.

REM Ir al directorio raiz del proyecto (un nivel arriba de CRM\)
cd /d "%~dp0.."

REM Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [!] No se encontro el entorno virtual.
    echo [i] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Error al crear el entorno virtual.
        echo [i] Asegurate de tener Python 3.8+ instalado.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
    echo.
)

REM Activar entorno virtual
echo [i] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Verificar dependencias
python -c "import streamlit, anthropic, plotly, psycopg2" 2>nul
if errorlevel 1 (
    echo [!] Faltan dependencias. Instalando...
    echo.
    pip install streamlit anthropic plotly pandas psycopg2-binary
    if errorlevel 1 (
        echo [X] Error al instalar dependencias.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencias instaladas.
    echo.
)

REM Lanzar CRM
echo [i] Iniciando CRM Visitas...
echo [i] Se abrira automaticamente en el navegador.
echo [i] Para detener: presiona Ctrl+C en esta ventana.
echo.
echo ========================================
echo.

cd /d "%~dp0"
streamlit run crm.py --server.port 8502

if errorlevel 1 (
    echo.
    echo [X] Error al ejecutar el CRM.
    echo [i] Verifica que crm.py este en la carpeta CRM\
    pause
)
