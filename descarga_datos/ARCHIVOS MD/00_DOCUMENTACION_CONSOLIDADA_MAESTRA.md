# 📖 DOCUMENTACIÓN CONSOLIDADA MAESTRA — Bot Antigravity (Copilot Bot Trader)

**Última actualización**: 13 de febrero de 2026  
**Versión actual del sistema**: v6.1  
**Estado**: ✅ OPERATIVO — Live Trading MT5 + Unificación Live/Backtest + Circuit Breakers  
**Repositorio**: `https://github.com/javiertarazon/ultra_detailed_heikin_ashi_ml_strategy.git`

---

## 📑 TABLA DE CONTENIDOS

1. [¿Qué es este proyecto?](#1-qué-es-este-proyecto)
2. [¿De dónde viene?](#2-de-dónde-viene)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Módulos Principales](#4-módulos-principales)
5. [Estrategia de Trading](#5-estrategia-de-trading)
6. [Evolución por Versiones](#6-evolución-por-versiones)
7. [Errores Críticos Corregidos](#7-errores-críticos-corregidos-lecciones-aprendidas)
8. [Reglas y Estándares de Código](#8-reglas-y-estándares-de-código)
9. [Configuración y Parámetros](#9-configuración-y-parámetros)
10. [Modos de Operación](#10-modos-de-operación)
11. [Dashboard y Monitoreo](#11-dashboard-y-monitoreo)
12. [Resultados Validados](#12-resultados-validados)
13. [Brokers y Exchanges Soportados](#13-brokers-y-exchanges-soportados)
14. [Guía Rápida de Inicio](#14-guía-rápida-de-inicio)
15. [Inventario de Documentación](#15-inventario-de-documentación)
16. [Roadmap Futuro](#16-roadmap-futuro)

---

## 1. ¿QUÉ ES ESTE PROYECTO?

**Bot Antigravity** (nombre técnico: *Copilot Bot Trader*) es un **sistema de trading algorítmico profesional** que combina:

- **Análisis técnico avanzado** (28 indicadores, Heikin-Ashi candles)
- **Machine Learning** (Random Forest, XGBoost, ONNX) para generar señales de alta calidad
- **Gestión de riesgo automatizada** (ATR-based stops, trailing stops dinámicos, circuit breakers diarios)
- **Ejecución automatizada 24/7** en MetaTrader 5 (Deriv/ThinkMarkets)

### Filosofía Central
> **"Data over Hype"** — Toda decisión de trading debe estar respaldada por ML entrenado en datos históricos reales. Sin datos simulados, sin atajos.

### Objetivo Fundamental
Rentabilidad consistente con **Drawdown máximo < 15%** y **Win Rate > 55%**.

---

## 2. ¿DE DÓNDE VIENE?

### Origen
- **Nombre del repositorio original**: `ultra_detailed_heikin_ashi_ml_strategy`
- **Alias del proyecto**: `botcopilot-sar` / `copilot-bot`
- **Creador**: Javier Tarazón
- **Primera versión documentada**: v2.8 (con guía de migración existente)
- **Stack tecnológico**: Python 3.11-3.13, MetaTrader 5, CCXT, TA-Lib, Scikit-learn, Optuna, Streamlit

### Cronología General
| Periodo | Versión | Hito Principal |
|---------|---------|----------------|
| Pre-Oct 2025 | v2.8 → v3.5 | Arquitectura base, backtesting, optimización ML |
| Oct 2025 | v4.0 → v4.6 | Correcciones críticas live trading, CCXT, dashboard |
| Nov 2025 | v4.7 → v4.9 | MT5 operativo, AutoTrading, protecciones de archivos |
| Nov 2025 | v4.10 | Live MT5 estable 24/7, 79.89% win rate |
| Nov 2025 | v4.11 | Optimización 10x rendimiento (5s → 500ms) |
| Ene 2026 | v5.0+ | Migración a ThinkMarkets, tests de conexión completos |
| Feb 2026 | v6.1 | Unificación Live/Backtest, Circuit Breaker 5%, Trailing Stop 65%, ROI +190% validado |

---

## 3. ARQUITECTURA DEL SISTEMA

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (CLI Entry Point)             │
│          --backtest | --optimize | --live-mt5            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Config   │  │ Data Layer   │  │ ML Models         │  │
│  │ (YAML)   │→ │ (SQLite/CSV) │→ │ (RandomForest,    │  │
│  │          │  │ (Live/Hist)  │  │  XGBoost, ONNX)   │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
│        │              │                    │              │
│        ▼              ▼                    ▼              │
│  ┌──────────────────────────────────────────────────┐    │
│  │         Estrategia: UltraDetailedHeikinAshiML     │    │
│  │    28 indicadores técnicos + predicción ML        │    │
│  └──────────────────────────────────────────────────┘    │
│                         │                                │
│        ┌────────────────┼────────────────┐               │
│        ▼                ▼                ▼               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐     │
│  │ Risk     │  │ Position     │  │ Order          │     │
│  │ Manager  │  │ Tracker      │  │ Executor       │     │
│  │ (ATR)    │  │ (Indexed)    │  │ (MT5/CCXT)     │     │
│  └──────────┘  └──────────────┘  └───────────────┘     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │         Dashboard Streamlit (localhost:8520)       │    │
│  │    Métricas, P&L, posiciones, señales en vivo     │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Estructura de Directorios Clave

```
copilot-bot-v-4.11/
├── descarga_datos/               # 🏠 Core del sistema
│   ├── main.py                   # 🚀 ÚNICO punto de entrada
│   ├── config/
│   │   └── config.yaml           # ⚙️ Configuración centralizada
│   ├── core/                     # 🔧 Componentes core
│   │   ├── ccxt_live_data.py     #     Live data CCXT
│   │   ├── live_trading_orchestrator.py  # Orquestador live
│   │   ├── downloader.py         #     Descarga de datos
│   │   ├── mt5_live_data.py      #     Datos desde MT5
│   │   └── exchange_utils.py     #     Utilidades exchange
│   ├── strategies/               # 🎯 Estrategias de trading
│   │   ├── base_strategy.py
│   │   └── ultra_detailed_heikin_ashi_ml_strategy.py
│   ├── indicators/               # 📊 Indicadores técnicos
│   │   ├── technical_indicators.py
│   │   └── talib_wrapper.py
│   ├── models/                   # 🤖 Modelos ML entrenados (.pkl)
│   ├── backtesting/              # 📈 Motor de backtesting
│   ├── optimizacion/             # 🔬 Optimización con Optuna
│   ├── risk_management/          # 🛡️ Gestión de riesgos
│   ├── execution/                # ⚡ Ejecución de órdenes
│   ├── utils/                    # 🛠️ Logger, storage, config loader
│   │   ├── logger.py
│   │   ├── storage.py            # SQLite/CSV storage
│   │   ├── alert_manager.py      # Sistema de alertas (8 tipos)
│   │   └── config_loader.py
│   ├── v411_optimizations/       # 🚀 Módulos de optimización v4.11
│   │   ├── cached_data_provider.py
│   │   ├── numba_indicators.py
│   │   ├── onnx_model_predictor.py
│   │   └── indexed_position_monitor.py
│   ├── dashboard.py              # 📊 Dashboard Streamlit
│   ├── tests/                    # 🧪 Suite de testing
│   └── ARCHIVOS MD/              # 📚 TODA la documentación
├── data/                         # 💾 Datos históricos
├── logs/                         # 📝 Logs del sistema
├── requirements.txt              # 📦 Dependencias Python
└── .env                          # 🔐 Credenciales (NO compartir)
```

---

## 4. MÓDULOS PRINCIPALES

### 4.1 Estrategia: `UltraDetailedHeikinAshiMLStrategy`
- **Archivo**: `strategies/ultra_detailed_heikin_ashi_ml_strategy.py`
- **Indicadores usados (28)**: RSI, MACD, CCI, ATR, Estocástico, Bollinger Bands, EMA, SMA, ADX, y más
- **Candles Heikin-Ashi** para filtrar ruido de mercado
- **ML Confidence mínimo**: 0.52 (optimizado v6.1)
- **Señales**: BUY/SELL basadas en confluencia de indicadores + predicción ML > umbral
- **Filtro ADX (v6.1)**: Evita operaciones en rangos laterales sin tendencia definida

### 4.2 Gestión de Riesgo: `AdvancedRiskManager`
- **Archivo**: `risk_management/`
- **Reglas clave**:
  - Riesgo por trade: 1.5% del capital (sincronizado v6.1)
  - Stop Loss: ATR × 2.5-3.5 (dinámico por volatilidad)
  - Take Profit: ATR × 3.75-5.5
  - Trailing Stop: 65% dinámico (v6.1)
  - Drawdown máximo: < 25% (filtro seguridad)
  - Max posiciones simultáneas: 3
  - **Circuit Breaker Diario (v6.1)**: Detiene operaciones si pérdida diaria > 5.0%

### 4.3 Ejecución: Executors
- **MT5 Executor**: Ejecución nativa via MetaTrader 5 (Simple Bridge EA)
  - Latencia: < 10ms
  - Sin dependencias ZMQ requeridas
- **CCXT Executor**: Para exchanges crypto (Binance, Kraken)
  - Sandbox mode disponible para testing
- **Tipo configurado en**: `config.yaml → live_trading.executor_type`

### 4.4 Machine Learning
- **Modelo primario**: Random Forest (76.8% accuracy)
- **Auto-optimización**: Optuna para búsqueda de hiperparámetros
- **Training Period**: ~1.5 años (2023-2024), Validación (2025)
- **Feature parity**: Garantizada entre Backtest/Live

### 4.5 Optimizaciones v4.11
| Módulo | Función | Speedup |
|--------|---------|---------|
| `cached_data_provider.py` | Cache TTL inteligente de datos | 8.3x |
| `numba_indicators.py` | Compilación JIT de indicadores | 3.3x |
| `onnx_model_predictor.py` | Predicción ML acelerada | 20x |
| `indexed_position_monitor.py` | Tracking O(1) de posiciones | 6.25x |
| **Resultado combinado** | **Ciclo total** | **10x (5s → 500ms)** |

### 4.6 Dashboard Streamlit
- **Archivo**: `dashboard.py`
- **URL**: `http://localhost:8520` (auto-launcher con `--live`)
- **Métricas**: P&L, ROI, Circuit Breaker status, Señales ML tiempo real

---

## 5. ESTRATEGIA DE TRADING

### Nombre
**UltraDetailedHeikinAshiML** — Estrategia basada en Heikin-Ashi con Machine Learning

### Lógica de Decisión

1. **Preparación de datos**: Descarga 200 barras de 15 minutos
2. **Cálculo de indicadores**: 28 indicadores técnicos (RSI, MACD, CCI, ATR, Bollinger, etc.)
3. **Transformación Heikin-Ashi**: Candles suavizados para reducir ruido
4. **Predicción ML**: Random Forest predice dirección con confidence score
5. **Filtro de confluencia**: Señal solo si ML + indicadores técnicos coinciden
6. **Gestión de riesgo**: Position sizing ATR-based, SL/TP dinámicos
7. **Circuit Breaker Check**: Verifica si pérdida diaria < 5%
8. **Ejecución**: Orden enviada a MT5
9. **Monitoreo**: Trailing stop ajusta SL en tiempo real (lock 65% profit)

### Parámetros Optimizados (v6.1)

```yaml
risk_per_trade: 1.5%
max_concurrent_trades: 3
daily_loss_limit: 5.0%
trailing_stop_pct: 65%
ml_threshold: 0.52
atr_period: 17
stop_loss_atr_multiplier: 2.5
take_profit_atr_multiplier: 3.75
```

---

## 6. EVOLUCIÓN POR VERSIONES

### v2.8 — Arquitectura Base
- Arquitectura modular inicial
- Backtesting básico

### v3.5 — Optimización ML
- **1,666 trades**, 76.7% win rate, $41k ganancia
- Factor Profit 2.45
- Drawdown < 15%

### v4.0 — Correcciones Críticas
- Fix serialización JSON
- Live trading estabilizado
- 1,679 trades, 76.8%, $39k

### v4.9 — AutoTrading MT5
- **Error 10027 resuelto**
- `max_positions` aumentado a 5
- Ciclos 24/7 cada 5s

### v4.11 — Optimización 10x
- 5s → 500ms por ciclo
- Caching, Numba, ONNX
- 100% backward compatible
- 26 tests pasando

### v6.1 — Unificación y Protecciones (ACTUAL)
- **Unificación Live/Backtest**: Parámetros idénticos para garantizar consistencia.
- **Circuit Breaker Diario**: Límite de pérdida del 5% detiene operaciones.
- **Trailing Stop Optimizado**: Configurado al 65% de retención de beneficio.
- **Filtro ADX**: Evita reversiones en mercados laterales oscilantes.
- **Validación +190% ROI**: Confirmado en backtest de 1 año.
- **Configuración ZMQ**: Opcional, por defecto usa `Simple Bridge`.

---

## 7. ERRORES CRÍTICOS CORREGIDOS (LECCIONES APRENDIDAS)

### ⚠️ NO VOLVER A COMETER ESTOS ERRORES

| # | Error | Causa Raíz | Solución | Versión |
|---|-------|------------|----------|---------|
| 1 | **JSON serialization** | `datetime` no serializable | `convert_to_json_serializable()` | v4.0 |
| 2 | **Resource leak** | Conexiones no cerradas | `try/except/finally` | v4.0 |
| 3 | **RSI filter crash** | `rsi > 30` incorrecto | Cambiar a `rsi < 60` | v4.8 |
| 4 | **Error 10027** | AutoTrading deshabilitado | Habilitar manual en MT5 | v4.9 |
| 5 | **Solo 1 operación** | `max_positions: 1` | Aumentar a 3-5 | v4.9 |
| 6 | **Reversal Crash** | Whipsaw de mercado | **DESCARTAR** Reversal, usar ADX filter | v4.9/6.1 |
| 7 | **Discrepancia Backtest/Live** | Parámetros distintos | **UNIFICAR** configs en YAML | v6.1 |

### Regla de Oro
> 🔴 **NUNCA** usar datos simulados (`random`, `mock`) para lógica de trading en vivo. Siempre datos reales y parámetros unificados.

---

## 8. REGLAS Y ESTÁNDARES DE CÓDIGO

### Estándares de Copilot
1. **Centralización**: Todo ejecuta a través de `main.py`.
2. **Manejo de errores**: Bloques `try/except` robustos. logger.
3. **No mocking en producción**: Datos reales siempre.
4. **Type hinting y Paths absolutos**.

---

## 9. CONFIGURACIÓN Y PARÁMETROS

### Archivo de Configuración
`descarga_datos/config/config.yaml`

### Credenciales (.env)
Se cargan desde variable de entorno `MT5_LOGIN` y `MT5_PASSWORD`.

### Parámetros Live Trading (v6.1)

| Parámetro | Valor Actual | Notas |
|-----------|-------------|-------|
| Símbolo | TM_VOLATILITY_50/75/100 | ThinkMarkets |
| Timeframe | 15m | Alinear con modelo ML |
| Riesgo por trade | 1.5% | Sincronizado v6.1 |
| Max posiciones | 3 | Por seguridad |
| Circuit Breaker | 5.0% | Diario |
| Max Drawdown | 25.0% | Total cuenta |
| Trailing Stop | 65% | De beneficio |
| Executor type | `simple` | Simple Bridge EA |

---

## 10. MODOS DE OPERACIÓN

### Backtesting 📈
```powershell
python descarga_datos/main.py --backtest
```

### Optimización ML 🔬
```powershell
python descarga_datos/main.py --optimize
```

### Live Trading MT5 🚀
```powershell
python descarga_datos/main.py --live-mt5
```

### Test Mode (30 segundos)
```powershell
python descarga_datos/main.py --test-live-mt5
```

---

## 11. DASHBOARD Y MONITOREO

### Dashboard Streamlit
- **URL**: `http://localhost:8520` (Automático)
- **Features**: P&L en vivo, estado del Circuit Breaker, Señales activas.

### Monitoreo por Logs
```powershell
Get-Content descarga_datos/logs/bot_trader.log -Tail 50 -Wait
```

---

## 12. RESULTADOS VALIDADOS (v6.1)

### Backtest Confirmación
| Métrica | Valor |
|---------|-------|
| ROI 1 Año | +190% |
| Win Rate | ~76-79% |
| Drawdown | Controlado < 25% |
| Circuit Breaker | Activo y probado |

### Live Trading Tests
- **Broker**: ThinkMarkets-Demo
- **Conectividad**: 100% estable (Simple Bridge)
- **Ejecución**: Ticks en tiempo real verificados

---

## 13. BROKERS Y EXCHANGES SOPORTADOS

### Actualmente Activo
| Plataforma | Broker | Tipo | Estado |
|------------|--------|------|--------|
| MetaTrader 5 | ThinkMarkets (Demo) | Volatility Indices | ✅ OPERATIVO |

### 13.1 Credenciales de Demo (Preservadas)
Estas son las cuentas demo configuradas en el sistema para evitar perderlas:

| Broker | Server | Login ID | Password | Status |
|--------|--------|----------|----------|--------|
| **ThinkMarkets** | `ThinkMarkets-Demo` | `174873` | `Jatr28037$` | ✅ Activa (.env) |
| **Deriv** | `Deriv-Demo` | `5899273` | *(Ver config anterior)* | ⏸️ Legacy/backup |

> **Nota**: Las credenciales de exchanges crypto (Binance, Kraken, Bybit) están actualmente vacías en la configuración y desactivadas.

### EA de Conexión MT5
- **Simple Bridge EA** (RECOMENDADO): Sin dependencias externas.

---

## 14. GUÍA RÁPIDA DE INICIO

### Para Live MT5 (v6.1)
1. ✅ **MT5 abierto** con cuenta `174873` (ThinkMarkets).
2. ✅ **AutoTrading habilitado** en MT5.
3. ✅ **Simple Bridge EA** en gráfico (cara feliz).
4. ✅ `.env` correcto.
5. Ejecutar: `python descarga_datos/main.py --live-mt5`

---

## 15. INVENTARIO DE DOCUMENTACIÓN

Todo consolidado en `descarga_datos/ARCHIVOS MD/`.
Documento maestro: **`00_DOCUMENTACION_CONSOLIDADA_MAESTRA.md`**.

---

## 16. ROADMAP FUTURO

### v6.2+
- [ ] Implementar base de datos PostgreSQL.
- [ ] Alertas remotas (Telegram/Discord).
- [ ] Optimización automática continua (Auto-retraining).

---

## 📞 REFERENCIA RÁPIDA DE COMANDOS

```powershell
# Activar entorno virtual
.venv\Scripts\activate

# Backtest
python descarga_datos/main.py --backtest

# Live Trading MT5
python descarga_datos/main.py --live-mt5

# Diagnóstico
python descarga_datos/tests/diagnose_simple.py
```
