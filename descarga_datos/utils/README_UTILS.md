# 📦 Módulos Disponibles en `utils/`

Documentación de módulos de utilidad activamente usados en el sistema.

## ✅ Módulos Esenciales (23 módulos)

### 🗄️ **Core Storage & Data** (2 módulos)

#### `storage.py` - Gestor de Base de Datos SQLite
- **Propósito**: Interfaz principal para almacenamiento de datos
- **Funciones principales**:
  - `DataStorage` - Clase principal para BD
  - CRUD operations en SQLite
  - Gestión de transacciones
- **Usado por**: 12 módulos del sistema
- **Ejemplo**:
  ```python
  from utils.storage import DataStorage
  db = DataStorage()
  trades = db.get_trades()
  ```

#### `market_data_validator.py` - Validador de Datos de Mercado
- **Propósito**: Validación de autenticidad de datos
- **Métodos**: Detección de datos sintéticos, auditoría
- **Usado por**: 2 módulos
- **Ejemplo**:
  ```python
  from utils.market_data_validator import MarketDataValidator
  validator = MarketDataValidator()
  is_real = validator.validate_data(prices)
  ```

---

### 🧠 **ML & Indicadores** (2 módulos)

#### `talib_wrapper.py` - Envoltorio para TA-Lib
- **Propósito**: Interfaz consistente para cálculo de indicadores técnicos
- **Indicadores**: RSI, MACD, ATR, Stochastic, CCI, ADX, EMA, etc.
- **Usado por**: 2 módulos
- **Ejemplo**:
  ```python
  from utils.talib_wrapper import TaLibWrapper
  wrapper = TaLibWrapper()
  rsi = wrapper.RSI(prices, period=14)
  ```

#### `indicator_cache.py` - Cache de Indicadores
- **Propósito**: Cacheo de indicadores para optimizar performance
- **Mejora**: Evita recalcular indicadores idénticos
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.indicator_cache import IndicatorCache
  cache = IndicatorCache()
  rsi = cache.get_or_calculate('RSI', prices, period=14)
  ```

---

### 💰 **Trading Operations** (3 módulos)

#### `order_persistence.py` - Persistencia de Órdenes
- **Propósito**: Almacenamiento y recuperación de histórico de órdenes
- **Funciones**: Guardado de órdenes, estado de posiciones
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.order_persistence import OrderPersistence
  persistence = OrderPersistence()
  persistence.save_order(order_data)
  ```

#### `pnl_calculator.py` - Calculador de P&L
- **Propósito**: Cálculo de ganancias y pérdidas
- **Métricas**: Win rate, Sharpe ratio, drawdown, etc.
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.pnl_calculator import PnLCalculator
  calc = PnLCalculator()
  metrics = calc.calculate_metrics(trades)
  ```

#### `position_synchronizer.py` - Sincronizador de Posiciones
- **Propósito**: Sincronización de posiciones entre broker y local
- **Función**: Reconciliación de estado
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.position_synchronizer import PositionSynchronizer
  sync = PositionSynchronizer()
  sync.sync_positions()
  ```

---

### 📊 **Live Trading** (2 módulos)

#### `live_trading_tracker.py` - Tracker de Trading Live
- **Propósito**: Monitoreo de operaciones en tiempo real
- **Funciones**: Captura de ticks, seguimiento de P&L vivo
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.live_trading_tracker import LiveTradingTracker
  tracker = LiveTradingTracker()
  tracker.on_tick(tick_data)
  ```

#### `live_trading_data_reader.py` - Lector de Datos Live
- **Propósito**: Lectura de datos en tiempo real desde broker
- **Fuente**: Streams de MT5, CCXT, etc.
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.live_trading_data_reader import LiveTradingDataReader
  reader = LiveTradingDataReader()
  ticks = reader.get_latest_ticks(symbol)
  ```

---

### 🛡️ **Risk Management** (1 módulo)

#### `graceful_shutdown.py` - Cierre Elegante del Sistema
- **Propósito**: Manejo de señales de cierre
- **Funciones**: Guardado de estado, cierre de conexiones, limpieza
- **Usado por**: 3 módulos
- **Ejemplo**:
  ```python
  from utils.graceful_shutdown import GracefulShutdownHandler
  handler = GracefulShutdownHandler(orchestrator)
  handler.setup_signals()
  ```

---

### 📋 **Monitoring & Logging** (4 módulos)

#### `logger.py` - Logger Principal
- **Propósito**: Sistema centralizado de logging
- **Nivel**: Usado por 38 módulos (crítico)
- **Funciones**: INFO, DEBUG, WARNING, ERROR, CRITICAL
- **Ejemplo**:
  ```python
  from utils.logger import logger
  logger.info("Mensaje de información")
  ```

#### `logger_metrics.py` - Logger de Métricas
- **Propósito**: Captura de métricas del sistema
- **Métricas**: Latencia, throughput, errores
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.logger_metrics import MetricsLogger
  metrics = MetricsLogger()
  metrics.record_latency(100)
  ```

#### `signal_logger.py` - Logger de Señales
- **Propósito**: Registro de señales de trading generadas
- **Datos**: Timestamp, price, signal, indicadores
- **Usado por**: 2 módulos
- **Ejemplo**:
  ```python
  from utils.signal_logger import SignalLogger
  sig_logger = SignalLogger()
  sig_logger.log_signal(signal_data)
  ```

#### `alert_manager.py` - Gestor de Alertas
- **Propósito**: Sistema de alertas (email, SMS, etc.)
- **Eventos**: Errores, cambios de estado, límites de riesgo
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.alert_manager import AlertManager
  alerts = AlertManager()
  alerts.send_alert("Sistema iniciado")
  ```

---

### ✅ **Validation** (2 módulos)

#### `backtest_validator.py` - Validador de Backtest
- **Propósito**: Validación de integridad de resultados de backtest
- **Checks**: Métricas, consistencia de datos, sanidad
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.backtest_validator import BacktestValidator
  validator = BacktestValidator()
  is_valid = validator.validate(results)
  ```

#### `trace_comparator.py` - Comparador de Trazas
- **Propósito**: Comparación de ejecución backtest vs live
- **Objetivo**: Detectar divergencias
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.trace_comparator import TraceComparator
  comparator = TraceComparator()
  comparison = comparator.compare(backtest_trace, live_trace)
  ```

---

### 🔗 **CCXT/Brokers** (1 módulo)

#### `ccxt_manager.py` - Gestor de Conexiones CCXT
- **Propósito**: Interfaz unificada para brokers cripto
- **Soporta**: Binance, Bybit, Kraken, etc.
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.ccxt_manager import CCXTManager
  ccxt = CCXTManager(exchange='binance')
  ticker = ccxt.fetch_ticker('BTC/USDT')
  ```

---

### 🛠️ **Utilidades** (3 módulos)

#### `retry_manager.py` - Gestor de Reintentos
- **Propósito**: Manejo de reintentos con backoff exponencial
- **Usado por**: 2 módulos
- **Ejemplo**:
  ```python
  from utils.retry_manager import RetryManager
  retry = RetryManager(max_retries=3)
  result = retry.execute(function, args)
  ```

#### `normalization.py` - Normalización de Datos
- **Propósito**: Escalado y normalización de precios/indicadores
- **Métodos**: MinMax, Z-score
- **Usado por**: 2 módulos
- **Ejemplo**:
  ```python
  from utils.normalization import normalize
  normalized = normalize(prices, method='minmax')
  ```

#### `market_sessions.py` - Sesiones de Mercado
- **Propósito**: Información de horarios de mercado
- **Datos**: Apertura, cierre, horas de trading
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.market_sessions import MarketSessions
  sessions = MarketSessions()
  is_open = sessions.is_market_open('NYSE')
  ```

---

### 🔧 **Otros** (2 módulos)

#### `monitoring.py` - Monitoreo del Sistema
- **Propósito**: Monitoreo de salud del sistema
- **Métricas**: CPU, memoria, conexiones
- **Usado por**: 1 módulo
- **Ejemplo**:
  ```python
  from utils.monitoring import Monitoring
  monitor = Monitoring()
  health = monitor.get_system_health()
  ```

#### `resilience.py` - Resiliencia y Recuperación
- **Propósito**: Mecanismos de tolerancia a fallos
- **Funciones**: Circuit breaker, fallback
- **Usado por**: 3 módulos
- **Ejemplo**:
  ```python
  from utils.resilience import Resilience
  resilience = Resilience()
  resilience.handle_failure(error)
  ```

#### `stop_loss_calculator.py` - Calculador de SL/TP
- **Propósito**: Cálculo de stop loss y take profit con validación broker
- **Validación**: Distancia mínima requerida por broker
- **Usado por**: 1 módulo (test_deriv_complete)
- **Ejemplo**:
  ```python
  from utils.stop_loss_calculator import StopLossTakeProfitCalculator
  calc = StopLossTakeProfitCalculator()
  constraints = calc.get_broker_constraints(symbol)
  sl, tp = calc.calculate_valid_sl_tp(price, 'BUY', sl_pts, tp_pts, constraints)
  ```

---

## 📊 Estadísticas

| Categoría | Módulos | Descripción |
|-----------|---------|-------------|
| Storage & Data | 2 | BD y validación |
| ML & Indicators | 2 | Indicadores y caché |
| Trading | 3 | Órdenes y P&L |
| Live Trading | 2 | Tracker y reader |
| Risk Mgmt | 1 | Graceful shutdown |
| Monitoring | 4 | Logging, alertas |
| Validation | 2 | Backtest, comparación |
| CCXT/Brokers | 1 | Conexiones |
| Utilities | 3 | Reintentos, normalización |
| Other | 2 | Sistema general |
| **TOTAL** | **23** | Módulos activos |

---

## 🎯 Módulos Críticos (más usados)

1. **logger.py** - Usado en 38 módulos ⭐⭐⭐⭐⭐
2. **storage.py** - Usado en 12 módulos ⭐⭐⭐⭐
3. **graceful_shutdown.py** - Usado en 3 módulos ⭐⭐⭐
4. **resilience.py** - Usado en 3 módulos ⭐⭐⭐

---

## 🗑️ Módulos Eliminados (Backup)

Los siguientes 18 módulos fueron archivados por no estar en uso:
- `analizar_uso_utils.py`
- `ccxt_manager_examples.py`
- `check_binance_balance.py`
- `check_bybit_balance.py`
- `consolidation_validator.py`
- `convert_btc_to_usdt.py`
- `dashboard.py`, `dashboard_old_backup.py`, `dashboard_quick.py`
- `divergence_analyzer.py`
- `enhanced_cache.py`
- `enhanced_validator.py`
- `mt5_download_runner.py`
- `order_executor_integration.py`
- `threshold_adjuster.py`
- `verify_bybit_credentials.py`
- `verify_kraken_credentials.py`
- `verify_sync_issues.py`

**Ubicación del backup**: `utils/BACKUP_UNUSED_20251102_1556/`

---

## 💡 Cómo Usar Este Documento

1. **Buscar un módulo**: Usa la búsqueda (Ctrl+F) por nombre
2. **Entender funcionalidad**: Lee el descripción y ejemplo
3. **Importar**: Copia el import de ejemplo
4. **Consultar**: Lee la documentación en el código fuente

---

**Generado**: 2 de noviembre de 2025  
**Status**: ✅ 23 módulos activos, optimizado y limpio
