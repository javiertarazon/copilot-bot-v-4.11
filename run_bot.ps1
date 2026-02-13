# ============================================================================
# Bot Trader Copilot - Script de Lanzamiento para PowerShell
# ============================================================================
# Este script garantiza que el bot se ejecute con el entorno virtual correcto.
# Uso: .\run_bot.ps1 [argumentos para main.py]
# Ejemplos:
#   .\run_bot.ps1 --help
#   .\run_bot.ps1 --backtest-only
#   .\run_bot.ps1 --live-mt5
# ============================================================================

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Obtener el directorio donde está este script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Ruta al Python del entorno virtual
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

# Verificar que el venv existe
if (-not (Test-Path $VenvPython)) {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "El entorno virtual debe estar en:"
    Write-Host "  $(Join-Path $ScriptDir '.venv')"
    Write-Host ""
    Write-Host "Para crear el entorno virtual:"
    Write-Host "  cd $ScriptDir"
    Write-Host "  python -m venv .venv"
    Write-Host "  .venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    Write-Host ""
    exit 1
}

# Ruta a main.py
$MainPy = Join-Path $ScriptDir "descarga_datos\main.py"

# Mostrar información
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Bot Trader Copilot - Ejecutando con entorno virtual" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Python: $VenvPython" -ForegroundColor Gray
Write-Host "Argumentos: $Arguments" -ForegroundColor Gray
Write-Host ""

# Ejecutar main.py con el Python del venv
& $VenvPython $MainPy @Arguments
