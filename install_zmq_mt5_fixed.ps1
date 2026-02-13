# Script de instalaci?n autom?tica de ZMQ Bridge para MT5
# Bot Trader Copilot v4.11

$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  INSTALADOR AUTOM?TICO ZMQ BRIDGE PARA MT5" -ForegroundColor Cyan
Write-Host "  Bot Trader Copilot v4.11" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Detectar directorio de MT5
Write-Host "[1/6] Detectando MetaTrader 5..." -ForegroundColor Yellow

$MT5Paths = @(
    "$env:APPDATA\MetaQuotes\Terminal",
    "C:\Program Files\MetaTrader 5",
    "C:\Program Files (x86)\MetaTrader 5"
)

$MT5Root = $null
foreach ($path in $MT5Paths) {
    if (Test-Path $path) {
        if ($path -like "*Terminal*") {
            # Buscar subdirectorios con hash
            $terminals = Get-ChildItem -Path $path -Directory | Where-Object { $_.Name -match '^[A-F0-9]{32}$' }
            if ($terminals) {
                $MT5Root = $terminals[0].FullName
                break
            }
        } else {
            $MT5Root = $path
            break
        }
    }
}

if (-not $MT5Root) {
    Write-Host "ERROR: No se encontr? MetaTrader 5" -ForegroundColor Red
    Write-Host "Por favor instala MT5 desde: https://www.metatrader5.com/es/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "   MT5 encontrado en: $MT5Root" -ForegroundColor Green

# Directorios de destino
$MQL5Root = Join-Path $MT5Root "MQL5"
$ExpertsDir = Join-Path $MQL5Root "Experts"
$IncludeDir = Join-Path $MQL5Root "Include"
$LibrariesDir = Join-Path $MQL5Root "Libraries"

# Crear directorios si no existen
@($ExpertsDir, $IncludeDir, $LibrariesDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Copiar archivos del proyecto
Write-Host ""
Write-Host "[2/6] Copiando archivos del EA..." -ForegroundColor Yellow

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MQL5SourceDir = Join-Path $ProjectRoot "descarga_datos\mql5"

# Copiar EA
$EASource = Join-Path $MQL5SourceDir "Experts\ZMQ_Bridge_EA.mq5"
$EADest = Join-Path $ExpertsDir "ZMQ_Bridge_EA.mq5"

if (Test-Path $EASource) {
    Copy-Item -Path $EASource -Destination $EADest -Force
    Write-Host "   EA copiado: ZMQ_Bridge_EA.mq5" -ForegroundColor Green
} else {
    Write-Host "   ERROR: No se encontr? $EASource" -ForegroundColor Red
    exit 1
}

# Copiar librer?a JSON
$JSONSource = Join-Path $MQL5SourceDir "Include\JAson.mqh"
$JSONDest = Join-Path $IncludeDir "JAson.mqh"

if (Test-Path $JSONSource) {
    Copy-Item -Path $JSONSource -Destination $JSONDest -Force
    Write-Host "   Librer?a JSON copiada: JAson.mqh" -ForegroundColor Green
} else {
    Write-Host "   ERROR: No se encontr? $JSONSource" -ForegroundColor Red
    exit 1
}

# Descargar librer?a ZMQ para MQL5
Write-Host ""
Write-Host "[3/6] Descargando librer?a ZMQ para MQL5..." -ForegroundColor Yellow

$ZMQUrl = "https://github.com/dingmaotu/mql-zmq/archive/refs/heads/master.zip"
$ZMQZip = Join-Path $env:TEMP "mql-zmq-master.zip"
$ZMQExtract = Join-Path $env:TEMP "mql-zmq-master"

try {
    # Descargar
    Write-Host "   Descargando desde GitHub..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $ZMQUrl -OutFile $ZMQZip -UseBasicParsing
    
    # Extraer
    Write-Host "   Extrayendo archivos..." -ForegroundColor Gray
    Expand-Archive -Path $ZMQZip -DestinationPath $env:TEMP -Force
    
    # Copiar archivos Include
    $ZMQIncludeSource = Join-Path $ZMQExtract "mql-zmq-master\Include\Zmq"
    $ZMQIncludeDest = Join-Path $IncludeDir "Zmq"
    
    if (Test-Path $ZMQIncludeSource) {
        Copy-Item -Path $ZMQIncludeSource -Destination $ZMQIncludeDest -Recurse -Force
        Write-Host "   Headers ZMQ copiados" -ForegroundColor Green
    }
    
    # Copiar DLLs
    $ZMQLibSource = Join-Path $ZMQExtract "mql-zmq-master\Library\MT5"
    if (Test-Path $ZMQLibSource) {
        Get-ChildItem -Path $ZMQLibSource -Filter "*.dll" | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $LibrariesDir -Force
            Write-Host "   DLL copiado: $($_.Name)" -ForegroundColor Green
        }
    }
    
    # Limpiar
    Remove-Item -Path $ZMQZip -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $ZMQExtract -Recurse -Force -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "   ADVERTENCIA: No se pudo descargar ZMQ autom?ticamente" -ForegroundColor Yellow
    Write-Host "   Descarga manual desde: https://github.com/dingmaotu/mql-zmq" -ForegroundColor Yellow
}

# Habilitar configuraciones en MT5
Write-Host ""
Write-Host "[4/6] Configurando MT5..." -ForegroundColor Yellow

$ConfigFile = Join-Path $MT5Root "config\common.ini"
if (Test-Path $ConfigFile) {
    # Leer configuraci?n actual
    $config = Get-Content $ConfigFile
    
    # Habilitar DLL y trading algor?tmico
    $modified = $false
    $newConfig = $config | ForEach-Object {
        if ($_ -match "^AllowDllImports=") {
            $modified = $true
            "AllowDllImports=1"
        } elseif ($_ -match "^EnableAlgoTrading=") {
            $modified = $true
            "EnableAlgoTrading=1"
        } else {
            $_
        }
    }
    
    if ($modified) {
        $newConfig | Set-Content $ConfigFile
        Write-Host "   Configuraci?n actualizada" -ForegroundColor Green
    }
} else {
    Write-Host "   Archivo de configuraci?n no encontrado (se configurar? manualmente)" -ForegroundColor Yellow
}

# Actualizar config.yaml del bot
Write-Host ""
Write-Host "[5/6] Actualizando configuraci?n del bot..." -ForegroundColor Yellow

$ConfigYaml = Join-Path $ProjectRoot "descarga_datos\config\config.yaml"
if (Test-Path $ConfigYaml) {
    $yamlContent = Get-Content $ConfigYaml -Raw
    
    # Habilitar ZMQ
    $yamlContent = $yamlContent -replace "(?m)^(\s*enabled:\s*)false(\s*# Cambiar a true)", '${1}true${2}'
    $yamlContent = $yamlContent -replace "(?m)^(\s*executor_type:\s*)'mt5'", '${1}''zmq'''
    
    Set-Content -Path $ConfigYaml -Value $yamlContent
    Write-Host "   config.yaml actualizado (ZMQ habilitado)" -ForegroundColor Green
}

# Resumen
Write-Host ""
Write-Host "[6/6] INSTALACI?N COMPLETADA" -ForegroundColor Green
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  PASOS FINALES (MANUAL)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Abre MetaTrader 5" -ForegroundColor White
Write-Host ""
Write-Host "2. Abre MetaEditor (presiona F4 en MT5)" -ForegroundColor White
Write-Host ""
Write-Host "3. Navega a: Experts - ZMQ_Bridge_EA.mq5" -ForegroundColor White
Write-Host ""
Write-Host "4. Compila el EA (presiona F7)" -ForegroundColor White
Write-Host "   - Si hay error de ZMQ, descarga manual desde:" -ForegroundColor Gray
Write-Host "     https://github.com/dingmaotu/mql-zmq/releases" -ForegroundColor Gray
Write-Host ""
Write-Host "5. En MT5, ve a: Herramientas - Opciones - Expert Advisors" -ForegroundColor White
Write-Host "   [X] Permitir trading algor?tmico" -ForegroundColor Yellow
Write-Host "   [X] Permitir importar DLL" -ForegroundColor Yellow
Write-Host ""
Write-Host "6. Arrastra ZMQ_Bridge_EA a cualquier gr?fico" -ForegroundColor White
Write-Host ""
Write-Host "7. Configurar par?metros:" -ForegroundColor White
Write-Host "   InpOrdersPort:    5555" -ForegroundColor Gray
Write-Host "   InpTicksPort:     5556" -ForegroundColor Gray
Write-Host "   InpMagicNumber:   20260129" -ForegroundColor Gray
Write-Host "   InpEnableTicks:   true" -ForegroundColor Gray
Write-Host ""
Write-Host "8. Marcar [X] Permitir trading en vivo" -ForegroundColor White
Write-Host ""
Write-Host "9. Verificar conexi?n:" -ForegroundColor White
Write-Host "   cd copilot-bot-v-4.11" -ForegroundColor Gray
Write-Host "   .\.venv\Scripts\python.exe descarga_datos\tests\test_zmq_connection.py" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Abrir MetaEditor si MT5 est? instalado
$response = Read-Host "Desea abrir MetaEditor ahora para compilar el EA? (S/N)"
if ($response -eq "S" -or $response -eq "s") {
    $metaeditor = Join-Path (Split-Path $MT5Root) "metaeditor64.exe"
    if (Test-Path $metaeditor) {
        Start-Process $metaeditor -ArgumentList "/compile:`"$EADest`""
        Write-Host "MetaEditor abierto. Compilando EA..." -ForegroundColor Green
    } else {
        Write-Host "No se encontro MetaEditor" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..."
Read-Host
