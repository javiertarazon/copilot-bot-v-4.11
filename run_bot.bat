@echo off
REM ============================================================================
REM Bot Trader Copilot - Script de Lanzamiento para Windows
REM ============================================================================
REM Este script garantiza que el bot se ejecute con el entorno virtual correcto.
REM Uso: run_bot.bat [argumentos para main.py]
REM Ejemplos:
REM   run_bot.bat --help
REM   run_bot.bat --backtest-only
REM   run_bot.bat --live-mt5
REM ============================================================================

setlocal

REM Obtener el directorio donde está este script
set "SCRIPT_DIR=%~dp0"

REM Ruta al Python del entorno virtual
set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

REM Verificar que el venv existe
if not exist "%VENV_PYTHON%" (
    echo ============================================================
    echo ERROR: Entorno virtual no encontrado
    echo ============================================================
    echo.
    echo El entorno virtual debe estar en:
    echo   %SCRIPT_DIR%.venv
    echo.
    echo Para crear el entorno virtual:
    echo   cd %SCRIPT_DIR%
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    exit /b 1
)

REM Ejecutar main.py con el Python del venv
echo ============================================================
echo Bot Trader Copilot - Ejecutando con entorno virtual
echo ============================================================
echo Python: %VENV_PYTHON%
echo Argumentos: %*
echo.

"%VENV_PYTHON%" "%SCRIPT_DIR%descarga_datos\main.py" %*

endlocal
