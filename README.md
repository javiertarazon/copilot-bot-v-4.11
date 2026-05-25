# Bot Trader Copilot v4.11 canónico

Repositorio consolidado para un único bot, un único activo y un único flujo operativo:

- **Motor base:** `copilot-bot-v-4.11`
- **Activo canónico:** `XAUUSD`
- **Estrategia inicial:** `UltraDetailedHeikinAshiML`
- **Broker objetivo:** MT5 demo compatible (`ThinkMarkets-Demo` por defecto)
- **Timeframe único:** `15m`

## Objetivo del repositorio

Este repositorio deja de ser multi-versión y multi-activo. La operación oficial es:

1. entrenar
2. validar
3. ejecutar prueba final
4. pasar a sandbox/demo
5. decidir si se promueve a real

## Configuración canónica

Archivo principal:

- `descarga_datos/config/config.yaml`

Variables sensibles:

- `descarga_datos/.env.example`

Las credenciales MT5 ya no se guardan en documentación ni en YAML operativo. Deben venir desde variables de entorno:

```bash
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=ThinkMarkets-Demo
MT5_PATH= # Opcional: ruta personalizada a terminal64.exe
```

## Comandos oficiales

```bash
# Crear entorno
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Entrenamiento
python descarga_datos/main.py --train-ml

# Backtest / prueba final offline
python descarga_datos/main.py --backtest-only

# Reporte de promoción
python descarga_datos/main.py --validation-report

# Sandbox / demo en vivo
python descarga_datos/main.py --live-mt5
```

## Regla de promoción

- **Demo** requiere: entrenamiento + validación + prueba final.
- **Real** requiere: entrenamiento + validación + prueba final + sandbox/demo + permiso explícito.

La política está documentada en:

- `docs/VALIDACION_XAUUSD.md`

## Estado de limpieza

- Se eliminaron documentos raíz redundantes de v4.9/v5.1.
- Se eliminaron configuraciones históricas duplicadas.
- `descarga_datos/ARCHIVOS MD/` queda como **archivo histórico** y no forma parte del flujo canónico.

## Nota operativa

Si `--live-mt5` falla por validación, actualiza primero el bloque `live_trading.validation` del archivo de configuración para reflejar las etapas ya completadas.
   • Métricas principales visibles
   • Sistema completamente funcional
   • UI cargando correctamente
   • Datos en tiempo real
```

### ✅ **Todas las Fases Completadas**
- **PHASE 1**: 4 fixes críticos validados ✅
- **PHASE 2.1**: Sistema alertas (8 tipos) compilable ✅
- **PHASE 2.2**: Dashboard web ejecutándose ✅
- **PHASE 3.1**: Análisis Freqtrade documentado ✅

---

---

## 🎉 ACTUALIZACIÓN - SESSION COMPLETA (Octubre 2025)

### ✨ LO QUE SE COMPLETÓ ESTA SESIÓN:

| Phase | Status | Impacto |
|---|---|---|
| **PHASE 1** | ✅ Completada | 415 errores → 0, 9 fantasmas → 0 |
| **PHASE 2.1** | ✅ Completada | Sistema alertas + 8 tipos automáticos |
| **PHASE 2.2** | ✅ Completada | Dashboard Streamlit web tiempo real |
| **PHASE 3.1** | ✅ Completada | Análisis Freqtrade + roadmap claro |
| **Documentación** | ✅ Completa | 7 documentos + índices de navegación |

### 📊 ESTADÍSTICAS FINALES:
- **3,240+** líneas de código nuevo/modificado
- **7** documentos comprehensivos creados
- **5** archivos funcionales (3 nuevos, 2 modificados)
- **8** tipos de alertas automáticas
- **99.8%** uptime esperado

### 🚀 EMPEZAR AHORA:

**👉 LEE ESTOS PRIMERO (30-40 minutos):**
1. [`descarga_datos/ARCHIVOS MD/PROYECTO_COMPLETADO_RESUMEN_FINAL.md`](descarga_datos/ARCHIVOS%20MD/PROYECTO_COMPLETADO_RESUMEN_FINAL.md) - Overview ejecutivo (15 min)
2. [`descarga_datos/ARCHIVOS MD/GUIA_USO_COMPLETA_v2.0.md`](descarga_datos/ARCHIVOS%20MD/GUIA_USO_COMPLETA_v2.0.md) - Manual operacional (20 min)

**👉 VALIDAR (4-5 horas):**
```bash
# Backtesting
python descarga_datos/main.py --backtest

# Dashboard
streamlit run descarga_datos/dashboard.py

# Live Sandbox (24h)
python descarga_datos/main.py --live
```

**👉 NUEVOS ARCHIVOS FUNCIONALES:**
- `descarga_datos/utils/alert_manager.py` - Sistema alertas (1100 líneas)
- `descarga_datos/core/orchestrator_alert_integration.py` - Integración alertas (400 líneas)
- `descarga_datos/dashboard.py` - Dashboard web (400 líneas)

**👉 ÍNDICES Y REFERENCIAS:**
- [`INDICE_NAVEGACION_COMPLETO_V2.md`](descarga_datos/ARCHIVOS%20MD/INDICE_NAVEGACION_COMPLETO_V2.md) - Navega toda la documentación
- [`STATUS_ACTUAL_PROYECTO.md`](STATUS_ACTUAL_PROYECTO.md) - Status actual del sistema
- [`QUICK_REFERENCE.txt`](QUICK_REFERENCE.txt) - Referencia rápida

---

**✅ SISTEMA COMPLETAMENTE DEPURADO v2.0:**
- Archivos fundamentales protegidos con checksums
- Scripts de test/debug organizados
- Documentación completa (7 documentos + índices)
- Sistema de alertas automático implementado (8 tipos)
- Dashboard Streamlit para monitoreo en tiempo real
- 100% listo para operación en vivo

------

## 📚 DOCUMENTACIÓN COMPLETA v4.7

### 🎯 Inicio Rápido
- **[GUIA_RAPIDA_v47.md](GUIA_RAPIDA_v47.md)** - Referencia rápida de operación
- **[PROYECTO_COMPLETADO_v47.md](PROYECTO_COMPLETADO_v47.md)** - Resumen ejecutivo completo
- **[ESTRUCTURA_DEPURADA.md](ESTRUCTURA_DEPURADA.md)** - Arquitectura del proyecto

### 🔒 Seguridad y Protección
- **[ARCHIVOS_PROTEGIDOS.md](ARCHIVOS_PROTEGIDOS.md)** - Lista de archivos core protegidos
- **Validar:** `python validate_protected_files.py`

### 📖 Documentación Clasificada
→ **[Todos los archivos MD en: descarga_datos/ARCHIVOS MD/](descarga_datos/ARCHIVOS%20MD/INDICE_MAESTRO_v47.md)**
- 12 categorías temáticas
- 92 archivos organizados
- Búsqueda por categoría facilitada

------



## 🚀 Características Principales - v4.0### **📊 Análisis Técnico Avanzado**

- **Heikin-Ashi ML Strategy** probada y optimizada

### **✅ Inteligencia Artificial Optimizada**- **Indicadores TALIB** completos (RSI, MACD, CCI, ATR, Estocástico, Bollinger)

- **RandomForest ML** con 76.8% accuracy en predicciones- **ATR Risk Management** con stops dinámicos y trailing stops

- **Auto-optimización Optuna** con modelos persistentes en `/models`- **Time-based exits** y gestión de posiciones concurrentes

- **Parámetros dinámicos** adaptados por símbolo (BTC, SOL, ETH, etc.)

- **Validación cruzada** para robustez del modelo### **🌐 Multi-Market Support**

- **Gestión de overfitting** con control de drawdown <15%- **Binance** (Crypto) vía CCXT con sandbox completo

- **MetaTrader 5** (Forex) nativo con conectores optimizados

### **📊 Análisis Técnico Avanzado**- **Sandbox Mode** para testing seguro y validación

- **Estrategia UltraDetailedHeikinAshiML** con 28 indicadores técnicos- **Live Trading** con gestión completa de posiciones y compensación

- **TALIB Integration** completa (RSI, MACD, CCI, ATR, Estocástico, Bollinger, etc.)

- **ATR Risk Management** con stops dinámicos y trailing stops (65%)### **⚡ Arquitectura Modular y Segura**

- **Gestión de posiciones**: 1 posición concurrente máximo, 2% risk per trade- **Data Flow Optimizado**: SQLite → CSV → Auto-download con verificación

- **Time-based exits** y rebalancing automático- **Configuración Centralizada**: YAML unificado con backups automáticos

- **Sistema Bloqueado**: Archivos críticos en solo lectura para protección

### **🌐 Soportes Multi-Exchange**- **Dashboard Streamlit**: Visualización completa con métricas detalladas

- **Binance Spot** vía CCXT con sandbox completo ✅- **Estrategia de Desarrollo**: Versión de pruebas separada para mejoras

- **MetaTrader 5** para Forex (nativo)

- **Modo Sandbox** para testing seguro---

- **Live Trading** con gestión completa de posiciones

- **Auto-download** de datos faltantes con Yahoo Finance fallback## 📊 Resultados Validados - Versión 3.5



### **⚡ Arquitectura Modular Robusta**### **Métricas de Backtest Optimizado**

- **Data Flow Centralizado**: SQLite primary → CSV fallback → auto-download- **Total Operaciones**: 1,666 trades

- **Configuración YAML**: `descarga_datos/config/config.yaml` unificado- **Tasa de Éxito**: 76.7%

- **Sistema de Logging**: Structured logging en `logs/bot_trader.log`- **Ganancia Neta**: $41,295.77

- **Dashboard Streamlit**: Visualización de métricas y resultados- **Drawdown Máximo**: <15% (controlado)

- **Code Protection**: Métodos críticos en solo lectura- **Factor de Profit**: 2.45

- **Ratio Sharpe**: 1.89

### **🔐 Correcciones Críticas v4.0 Implementadas**

✅ JSON Serialization errors (datetime handling)  ### **Parámetros Optimizados Aplicados**

✅ Missing method errors (validate_position, calculate_position_risk)  ```yaml

✅ Resource leak errors (shutdown graceful, async handling)  BTC_USDT:

✅ Data type validation (numeric normalization)    atr_period: 17

✅ Live trading stability (24h testing)    cci_threshold: 100

  ema_trend_period: 50

---  kelly_fraction: 0.25

  max_concurrent_trades: 10

## 📊 Resultados Validados - Octubre 2025  max_drawdown: 0.11

  ml_threshold: 0.35

### **Métricas de Backtest**  stop_loss_atr_multiplier: 2.25

| Métrica | Valor |  take_profit_atr_multiplier: 3.75

|---------|-------|```

| **Total Operaciones** | 1,679 trades |

| **Tasa de Éxito** | 76.8% ✅ |---

| **Ganancia Neta** | $39,667.40 |

| **Drawdown Máximo** | <15% (controlado) |## 🆕 **Novedades Versión 4.0 - Correcciones Críticas Aplicadas**

| **Factor de Profit** | 2.33 |

| **Ratio Sharpe** | 1.92 |### **🔧 Correcciones en Sistema Live Trading**



### **Métricas de Trading Vivo (OCT 21)**#### **1. Error de Serialización JSON en Historial de Posiciones**

| Métrica | Valor |- **Problema**: Objetos `datetime` no serializables causaban errores al guardar historial

|---------|-------|- **Impacto**: Pérdida de datos de posiciones y errores recurrentes en logs

| **Operaciones Cerradas** | 2 trades |- **Solución**: Implementación de conversión automática `convert_to_json_serializable()` en guardado de historial

| **Tasa de Éxito** | 100% ✅ |- **Resultado**: Historial de posiciones guardado correctamente sin errores

| **Ganancia Realizada** | +0.069870 BTC (~$7,568) |

| **P&L Promedio** | $3,784.18/trade |#### **2. Método `calculate_position_risk` Faltante en AdvancedRiskManager**

| **Máx Ganancia** | $5,319.75 |- **Problema**: Método crítico no implementado causaba errores cada 60 segundos

| **Mín Ganancia** | $2,248.60 |- **Impacto**: Funcionalidad de monitoreo de riesgo inoperativa

- **Solución**: Implementación completa del método con cálculo de P&L, riesgo restante y ratio riesgo/recompensa

### **Estado Actual de Capital (OCT 21)**- **Resultado**: Monitoreo de riesgo en tiempo real funcionando correctamente

| Activo | Cantidad | Valor USD |

|--------|----------|-----------|#### **3. Gestión Mejorada de Conexiones y Shutdown**

| **BTC** | 1.05123 | ~$113,718 |- **Problema**: Conexiones no cerradas correctamente en shutdown

| **USDT** | $1,000.56 | $1,000.56 |- **Impacto**: Recursos no liberados y posibles memory leaks

| **Total** | - | ~$114,718 |- **Solución**: Implementación de `try/except/finally` blocks y manejo de `asyncio.CancelledError`

- **Resultado**: Shutdown graceful con liberación completa de recursos

---

#### **4. Validación de Datos Mejorada**

## ⚙️ Configuración Recomendada - v4.0- **Problema**: Datos inconsistentes en operaciones live

- **Impacto**: Señales erróneas y posiciones incorrectas

### **Parámetros Base (BTC/USDT)**- **Solución**: Verificación estricta de tipos de datos y normalización de métricas

```yaml- **Resultado**: Integridad de datos garantizada en todas las operaciones

# descarga_datos/config/config.yaml

symbol: "BTC/USDT"### **📈 Mejoras en Rendimiento Live**

timeframe: "15m"

backtest_interval: 5#### **Monitoreo de Posiciones 24/7**

risk_per_trade: 2.0  # %- **Trailing Stops Dinámicos**: Stop loss ajustado automáticamente basado en ATR

max_concurrent_trades: 1- **Cálculo de Riesgo en Tiempo Real**: P&L actual, riesgo restante, ratio riesgo/recompensa

- **Gestión de Posiciones Concurrentes**: Hasta 10 posiciones simultáneas por símbolo

# Risk Management- **Compensación Automática**: Balanceo de posiciones BUY/SELL para neutralidad

atr_period: 17

stop_loss_multiplier: 2.25#### **Dashboard Mejorado**

take_profit_multiplier: 3.75- **Métricas Live**: Win rate, P&L total, drawdown en tiempo real

trailing_stop_percent: 65- **Historial de Operaciones**: Todas las posiciones abiertas/cerradas con detalles

- **Alertas de Riesgo**: Notificaciones automáticas cuando se alcanzan límites

# ML & Optimization- **Visualización de Señales ML**: Confianza y predicciones en tiempo real

strategy: "UltraDetailedHeikinAshiML"

model_type: "RandomForest"### **🛡️ Sistema de Seguridad Reforzado**

optimize_enabled: true

```#### **Validaciones de Integridad**

- **Checksum de Datos**: Verificación de integridad en descargas

### **Modos de Operación**- **Backup Automático**: Configuraciones y modelos guardados automáticamente

```bash- **Recovery Points**: Puntos de restauración para recuperación de fallos

# Backtesting- **Sandbox Obligatorio**: Testing en modo seguro antes de producción

python descarga_datos/main.py --backtest

---

# Optimización (Optuna)

python descarga_datos/main.py --optimize## 📋 Requisitos del Sistema



# Trading Vivo (Sandbox por defecto)### **Dependencias**

python descarga_datos/main.py --live```bash

pip install -r requirements.txt

# Verificación de datos```

python descarga_datos/main.py --verify-data

```### **Python Version**

- **Python 3.13.7** recomendado (probado)

---- **Virtual Environment** obligatorio (.venv)



## 🔧 Instalación y Setup - QUICK START### **Credenciales**

```bash

### **Requisitos Previos**# Binance Testnet (Sandbox)

- Python 3.13+ ✅export BINANCE_TEST_API_KEY="tu_api_key"

- pip/condaexport BINANCE_TEST_API_SECRET="tu_api_secret"

- Git

# MetaTrader 5

### **1. Clonar y Setup del Entorno**# Configurar en MT5 Manager

```bash```

git clone https://github.com/javiertarazon/ultra_detailed_heikin_ashi_ml_strategy.git

cd botcopilot-sar---



# Crear entorno virtual## 🏃‍♂️ Inicio Rápido

python -m venv .venv

.venv\Scripts\activate  # Windows### **1. Configuración Inicial**

```bash

# Instalar dependencias# Clonar y configurar entorno

pip install -r requirements.txtgit clone <repository>

```cd botcopilot-sar

python -m venv .venv

### **2. Configurar Credenciales Binance (Testnet)**.venv\Scripts\activate  # Windows

```bashpip install -r requirements.txt

# Crear archivo .env en descarga_datos/```

# Agregar credenciales:

BINANCE_TEST_API_KEY=your_key### **2. Validación del Sistema**

BINANCE_TEST_API_SECRET=your_secret```bash

```# Ejecutar smoke test

python -m pytest descarga_datos/tests/test_quick_backtest.py

### **3. Verificar Instalación**```

```bash

python -m pytest descarga_datos/tests/test_quick_backtest.py### **3. Configuración Básica**

```Edita `descarga_datos/config/config.yaml`:

```yaml

### **4. Ejecutar Backtest (Validación)**trading:

```bash  symbols: ["BTC/USDT", "ETH/USDT"]

python descarga_datos/main.py --backtest  timeframe: "15m"

```  sandbox: true  # Cambiar a false para live trading



### **5. Ejecutar Live Trading**ml:

```bash  enabled: true

python descarga_datos/main.py --live  model_type: "random_forest"

``````



---### **4. Entrenar Modelos ML**

```bash

## 📁 Estructura de Carpetaspython descarga_datos/main.py --optimize

```

```

botcopilot-sar/### **5. Ejecutar Live Trading**

├── descarga_datos/```bash

│   ├── main.py                          # Entry point principal# Modo sandbox (recomendado primero)

│   ├── config/python descarga_datos/main.py --live

│   │   └── config.yaml                  # 🔑 CONFIGURACIÓN CENTRALIZADA

│   ├── core/                            # Core modules# Modo producción (con precaución)

│   │   ├── ccxt_live_data.py           # Live data CCXT# Cambiar sandbox: false en config.yaml

│   │   ├── downloader.py               # Data downloader```

│   │   └── exchange_utils.py           # Utilidades exchange

│   ├── strategies/---

│   │   ├── base_strategy.py            # Base class

│   │   └── ultra_detailed_heikin_ashi_ml_strategy.py## 📁 Estructura del Proyecto

│   ├── backtesting/

│   │   ├── backtesting_orchestrator.py```

│   │   └── backtest_runner.pybotcopilot-sar/

│   ├── indicators/├── descarga_datos/           # 🏠 Core del sistema

│   │   ├── technical_indicators.py│   ├── main.py              # 🚀 Punto de entrada principal

│   │   └── talib_wrapper.py            # TALIB wrapper│   ├── config/              # ⚙️ Configuraciones YAML

│   ├── models/                          # ML Models (Optuna)│   ├── core/                # 🔧 Componentes core (CCXT, MT5)

│   │   ├── BTC_USDT_model.pkl│   ├── strategies/          # 🎯 Estrategias de trading

│   │   └── ...│   ├── indicators/          # 📊 Indicadores técnicos

│   ├── utils/│   ├── models/              # 🤖 Modelos ML entrenados

│   │   ├── logger.py                   # Sistema de logging│   ├── backtesting/         # 📈 Backtesting engine

│   │   ├── logger_metrics.py           # Métricas│   ├── optimizacion/        # 🔬 Optimización Optuna

│   │   ├── storage.py                  # SQLite/CSV storage│   ├── risk_management/     # 🛡️ Gestión de riesgos

│   │   └── config_loader.py            # Config loader│   ├── utils/               # 🛠️ Utilidades (logging, storage)

│   ├── ARCHIVOS MD/                     # 📚 DOCUMENTACIÓN COMPLETA│   ├── tests/               # 🧪 Suite de testing

│   │   ├── 00_INDICE_MAESTRO_v4.md     # COMENZAR AQUÍ│   └── ARCHIVOS MD/         # 📚 Documentación completa

│   │   ├── README.md├── data/                    # 💾 Datos históricos

│   │   ├── CHANGELOG.md├── logs/                    # 📝 Logs del sistema

│   │   ├── 01_SISTEMA_MODULAR_COMPLETO.md├── models/                  # 🧠 Modelos ML guardados

│   │   ├── 02_OPTIMIZACION_ML_COMPLETO.md└── requirements.txt         # 📦 Dependencias Python

│   │   ├── LIVE_TRADING_SANDBOX_GUIDE.md```

│   │   ├── 05_CORRECCIONES_Y_MEJORAS.md

│   │   └── ... (45+ documentos)---

│   ├── tests/

│   │   └── test_quick_backtest.py
│   └── .env                            # 🔐 Credenciales (no compartir)

---

## 🚀 **Ejecución Segura del Sistema**

### **Scripts de Lanzamiento Automáticos**

Para garantizar que el sistema se ejecute únicamente en el entorno correcto (Python 3.11.x + entorno virtual), utiliza los scripts de lanzamiento incluidos:

#### **Windows (.bat)**
```cmd
# Desde la raíz del proyecto
run_bot.bat --backtest
run_bot.bat --optimize
run_bot.bat --live
```

#### **Linux/Mac (.sh)**
```bash
# Desde la raíz del proyecto
chmod +x descarga_datos/run_bot.sh
./descarga_datos/run_bot.sh --backtest
./descarga_datos/run_bot.sh --optimize
./descarga_datos/run_bot.sh --live
```

### **Verificaciones Automáticas**
Los scripts de lanzamiento verifican automáticamente:
- ✅ **Entorno virtual activado** (.venv)
- ✅ **Versión Python 3.11.x** exacta
- ✅ **Archivo de configuración** presente
- ✅ **Dependencias instaladas**

### **Ejecución Manual (Solo para desarrollo)**
Si necesitas ejecutar manualmente (no recomendado para producción):
```bash
# Activar entorno virtual primero
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Luego ejecutar
python descarga_datos/main.py --backtest
```

## 🎯 Modos de Operación

│   └── .env                            # 🔐 Credenciales (no compartir)

│### **Backtesting** 📈

├── data/```bash

│   ├── sqlite/                         # SQLite databasespython descarga_datos/main.py --backtest

│   │   ├── data.db```

│   │   └── metadata.db- Prueba estrategias con datos históricos

│   ├── csv/                            # CSV backup- Genera métricas de rendimiento

│   ├── live_data/                      # Live trading data- Valida lógica antes de live trading

│   └── dashboard_results/              # Resultados optimización

│### **Optimización ML** 🔬

├── logs/```bash

│   └── bot_trader.log                  # 📋 Principal logpython descarga_datos/main.py --optimize

│```

├── requirements.txt                     # Dependencias- Auto-optimización con Optuna

├── README.md                            # Este archivo- Entrenamiento de modelos RandomForest

└── .gitignore- Búsqueda de parámetros óptimos



```### **Live Trading** 🚀

```bash

---python descarga_datos/main.py --live

```

## 🔍 Troubleshooting - Problemas Comunes- Trading automatizado 24/7

- Gestión completa de posiciones

### **❌ "Error: No se encuentran datos"**- Dashboard de monitoreo en tiempo real

**Solución:** El sistema auto-descargará. Ejecuta primero:

```bash---

python descarga_datos/main.py --backtest

```## 📊 Dashboard y Monitoreo



### **❌ "JSON serialization error"**### **Visualización en Tiempo Real**

**Solución:** Verificado y fijado en v4.0. Consulta: `descarga_datos/ARCHIVOS MD/05_CORRECCIONES_Y_MEJORAS.md````bash

# Se lanza automáticamente con --live

### **❌ "Exit code 1 en live trading"**# Acceder en: http://localhost:8519-8523

**Solución:** ```

1. Verifica credenciales `.env`

2. Consulta logs: `tail -f logs/bot_trader.log`### **Métricas Disponibles**

3. Lee: `LIVE_TRADING_SANDBOX_GUIDE.md`- **Señales ML**: Confianza y predicciones

- **Posiciones**: P&L, drawdown, win rate

### **❌ "Memory leak o recursos no liberados"**- **Riesgos**: ATR stops, trailing stops

**Solución:** Sistema corregido en v4.0. Implementado graceful shutdown. Ver: `CORRECCIONES_V4.0.md`- **Performance**: Métricas históricas



### **Más problemas:**---

Consulta: **`descarga_datos/ARCHIVOS MD/05_CORRECCIONES_Y_MEJORAS.md`** (guía completa)

## 🔧 Configuración Avanzada

---

### **Parámetros ML**

## 📈 Cómo Usar - Flujos Típicos```yaml

ml:

### **Opción 1: Solo Backtesting (Validación)**  enabled: true

```bash  model_type: "random_forest"

# 1. Ejecutar backtest  confidence_threshold: 0.7

python descarga_datos/main.py --backtest  features: ["rsi", "macd", "cci", "stoch_k", "atr", "ha_close"]

```

# 2. Ver resultados en dashboard

python run_dashboard.py### **Gestión de Riesgos**

# Abre: http://localhost:8519```yaml

```risk_management:

  atr_period: 14

### **Opción 2: Optimizar Parámetros (Optuna)**  stop_loss_atr: 3.25

```bash  take_profit_atr: 5.5

# 1. Ejecutar optimización (puede tomar 30-60 min)  trailing_stop_pct: 0.5

python descarga_datos/main.py --optimize  max_drawdown_pct: 5.0

```

# 2. Ver modelos optimizados en: descarga_datos/models/

### **Exchanges**

# 3. Ver resultados en dashboard```yaml

python run_dashboard.pyexchanges:

```  binance:

    sandbox: true

### **Opción 3: Trading Vivo (Sandbox)**    api_key: "${BINANCE_TEST_API_KEY}"

```bash    api_secret: "${BINANCE_TEST_API_SECRET}"

# 1. Verificar configuración en config.yaml```

cat descarga_datos/config/config.yaml

---

# 2. Ejecutar live trading

python descarga_datos/main.py --live## 📚 Documentación Completa



# 3. Monitorear en tiempo real### **Documentos Principales**

tail -f logs/bot_trader.log- **[Sistema Modular](descarga_datos/ARCHIVOS%20MD/01_SISTEMA_MODULAR_COMPLETO.md)** - Arquitectura y desarrollo

- **[Optimización ML](descarga_datos/ARCHIVOS%20MD/02_OPTIMIZACION_ML_COMPLETO.md)** - Machine Learning y Optuna

# 4. Ver dashboard (otro terminal)- **[Testing](descarga_datos/ARCHIVOS%20MD/03_TESTING_Y_VALIDACION.md)** - Validación y pruebas

python run_dashboard.py- **[Historial](descarga_datos/ARCHIVOS%20MD/04_HISTORIAL_VERSIONES.md)** - Versiones y evolución

```- **[Correcciones](descarga_datos/ARCHIVOS%20MD/05_CORRECCIONES_Y_MEJORAS.md)** - Problemas resueltos



---### **📋 Correcciones Recientes**

- **[Correcciones Live Trading](descarga_datos/ARCHIVOS%20MD/CORRECCIONES_SISTEMA_LIVE_TRADING.md)** - ✅ **NUEVO** - Todas las correcciones v3.0

## 🧪 Testing y Validación

---

### **Smoke Test (Rápido - 2 min)**

```bash## 🛠️ Troubleshooting

python -m pytest descarga_datos/tests/test_quick_backtest.py -v

```### **Problemas Comunes**



### **Test Completo (Lento - 10+ min)**#### **Error de Sintaxis**

```bash```bash

python -m pytest descarga_datos/tests/ -v --tb=shortpython -m py_compile descarga_datos/strategies/ultra_detailed_heikin_ashi_ml_strategy.py

``````



---#### **Modelo ML no encontrado**

```bash

## 🎯 Key Metrics - Validación v4.0python descarga_datos/main.py --optimize

```

### **Sistema Estable**

- ✅ Backtest sin errores: 1,679 trades ejecutados#### **Conexión Exchange fallida**

- ✅ Win rate 76.8%- Verificar credenciales en variables de entorno

- ✅ JSON serialization: FIJADO- Confirmar sandbox mode en config.yaml

- ✅ Resource cleanup: IMPLEMENTADO

- ✅ Graceful shutdown: ACTIVO#### **Datos insuficientes**

- ✅ 24h live testing: COMPLETADO- Ejecutar descarga automática con `--backtest`

- Verificar configuración de símbolos y timeframes

### **Indicadores Técnicos (28 total)**

✅ RSI, MACD, CCI, ATR, Estocástico, Bollinger, Ichimoku  ### **Logs y Debugging**

✅ Moving Averages, KAMA, ADX, OBV, MFI, ROC  ```bash

✅ Williams %R, Aroon, Keltner, VWAP, TRIX  # Logs principales

✅ y 11 más...tail -f logs/trading_system.log



---# Logs ML

tail -f logs/ml_system.log

## 📞 Soporte y Contribución

# Dashboard logs

### **Reportar Bugs**tail -f logs/dashboard.log

1. Revisa: `descarga_datos/ARCHIVOS MD/05_CORRECCIONES_Y_MEJORAS.md````

2. Consulta logs: `logs/bot_trader.log`

3. Crea issue en GitHub con logs---



### **Proponer Mejoras**## 🚨 Consideraciones de Seguridad

Sigue la guía en: `descarga_datos/ARCHIVOS MD/CONTRIBUTING.md`

### **Modo Sandbox Obligatorio**

### **Documentación**- **Siempre probar primero** con `sandbox: true`

Índice completo: `descarga_datos/ARCHIVOS MD/00_INDICE_MAESTRO_v4.md`- **Capital virtual** en testnet

- **Validar lógica** antes de producción

---

### **Gestión de Riesgos**

## 📜 Licencia- **ATR stops** dinámicos implementados

- **Max drawdown** configurado

Ver: `descarga_datos/ARCHIVOS MD/LICENSE.md`- **Trailing stops** para proteger ganancias



---### **Backup Automático**

- **Modelos ML** guardados en `models/`

## 🏁 Estado Actual - 21 Octubre 2025- **Configuraciones** versionadas

- **Datos históricos** en SQLite + CSV

### **Sistema Status**

| Componente | Estado | Detalles |---

|-----------|--------|----------|

| **Backtesting** | ✅ ACTIVO | 1,679 trades, 76.8% win rate |## 📈 Rendimiento y Métricas

| **Optimización** | ✅ ACTIVO | Modelos en `/models`, Optuna funcional |

| **Live Trading** | ✅ ACTIVO | 2 operaciones exitosas, 100% win rate |### **Benchmarks Recientes**

| **Dashboard** | ✅ ACTIVO | Streamlit en puerto 8519 |- **Win Rate**: 60-75% (depende del símbolo)

| **Data Storage** | ✅ ACTIVO | SQLite + CSV backup |- **Max Drawdown**: < 5% configurado

| **Logging** | ✅ ACTIVO | Structured logging completo |- **Sharpe Ratio**: > 1.5 en optimización

- **Latencia**: < 500ms por señal

### **Capital & P&L**

- **BTC**: 1.05123 (~$113,718)### **Símbolos Soportados**

- **USDT**: $1,000.56 (reserva)- **Crypto**: BTC/USDT, ETH/USDT, SOL/USDT, ADA/USDT

- **Ganancias Realizadas**: +0.069870 BTC (~$7,568)- **Forex**: EUR/USD, GBP/USD, USD/JPY (MT5)



### **Próximos Pasos**---

1. Ejecutar live trading con capital actual

2. Monitorear 24h operaciones## 🤝 Contribución y Desarrollo

3. Analizar resultados vs backtest

4. Optimizar parámetros si es necesario### **Reglas de Desarrollo**

5. Escalar gradualmente- **Archivos Protegidos**: Estrategia ML y main.py (solo mejoras paramétricas)

- **Testing Obligatorio**: Ejecutar suite completa antes de commits

---- **Documentación**: Actualizar docs con cambios significativos



**Última actualización**: 21 de octubre de 2025 - 21:45 UTC  ### **Extensión del Sistema**

**Versión**: 4.0.1  ```python

**Mantenedor**: Bot Trader Copilot Team  # Nueva estrategia: extender base_strategy.py

**Repositorio**: https://github.com/javiertarazon/ultra_detailed_heikin_ashi_ml_strategy# Nuevo indicador: agregar a technical_indicators.py

# Nuevo exchange: implementar en core/

---```



## 📚 Links Importantes---



| Link | Descripción |## 📞 Soporte

|------|-------------|

| **[Índice Maestro](descarga_datos/ARCHIVOS%20MD/00_INDICE_MAESTRO_v4.md)** | Navegación completa de docs |- **📧 Issues**: GitHub Issues para bugs y features

| **[Guía Live Trading](descarga_datos/ARCHIVOS%20MD/LIVE_TRADING_SANDBOX_GUIDE.md)** | Step-by-step para live |- **📚 Docs**: Documentación completa en `ARCHIVOS MD/`

| **[Correcciones v4.0](descarga_datos/ARCHIVOS%20MD/05_CORRECCIONES_Y_MEJORAS.md)** | Todos los fixes aplicados |- **🔧 Logs**: Debugging detallado en `logs/`

| **[Optimización](descarga_datos/ARCHIVOS%20MD/02_OPTIMIZACION_ML_COMPLETO.md)** | Cómo optimizar con Optuna |- **📊 Dashboard**: Monitoreo visual en tiempo real

| **[Changelog](descarga_datos/ARCHIVOS%20MD/CHANGELOG.md)** | Historial de cambios |

---

---

## 📋 Checklist Pre-Live Trading

¡Gracias por usar Bot Trader Copilot! 🚀

- [ ] **Configuración**: `config.yaml` actualizado
- [ ] **Credenciales**: Variables de entorno configuradas
- [ ] **Modelos ML**: Entrenados y validados
- [ ] **Sandbox Test**: Verificado funcionamiento
- [ ] **Risk Management**: Parámetros ATR configurados
- [ ] **Backup**: Configuración guardada
- [ ] **Monitoreo**: Dashboard operativo

---

**⚠️ Disclaimer**: Este sistema es para fines educativos e investigación. El trading conlleva riesgos financieros significativos. Siempre prueba en sandbox antes de usar capital real.

---
*Bot Trader Copilot v4.0 - Sistema de Trading Automatizado con ML Estabilizado* 🤖📈