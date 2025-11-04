# 🚀 Escalado: De 1 a N Símbolos Simultáneamente

## 🎯 Objetivo

Ir de:
```
Sistema Actual:
├─ 1 símbolo: 'Volatility 75 Index'
├─ 15 minutos timeframe
├─ 1 posición abierta máximo
└─ 5 segundos ciclo
```

A:
```
Sistema Escalado:
├─ N símbolos: ['Volatility 75 Index', 'Volatility 100 Index', 'BTC/USDT', ...]
├─ M timeframes: ['5m', '15m', '1h', ...]
├─ P posiciones: 1-5 simultáneas por símbolo
└─ Ciclos paralelos (threading/async)
```

---

## 📋 Arquitectura de Escalado

```
CICLO ACTUAL (Single Symbol)
┌──────────────────────────────────┐
│ get_live_data('Vol75', '15m')    │
│ _prepare_data(df)                │
│ get_live_signal()                │
│ monitor_positions()              │
│ open_position_if_signal()        │
│ sync_with_mt5()                  │
│ log_metrics()                    │
│ sleep(5s)                        │
└──────────────────────────────────┘

CICLO ESCALADO (Multiple Symbols)
┌─────────────────────────────────────────────────────────┐
│ CICLO MAESTRO (cada 5 segundos)                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────┐               │
│  │ HILO 1: Volatility 75 Index (15m)   │               │
│  ├─────────────────────────────────────┤               │
│  │ get_live_data('Vol75', '15m')       │ ← Paralelo
│  │ _prepare_data(df)                   │               │
│  │ get_live_signal()                   │               │
│  │ monitor_positions()                 │               │
│  └─────────────────────────────────────┘               │
│              ↓                                          │
│  ┌─────────────────────────────────────┐               │
│  │ HILO 2: Volatility 100 Index (15m)  │               │
│  ├─────────────────────────────────────┤               │
│  │ get_live_data('Vol100', '15m')      │ ← Paralelo
│  │ _prepare_data(df)                   │               │
│  │ get_live_signal()                   │               │
│  │ monitor_positions()                 │               │
│  └─────────────────────────────────────┘               │
│              ↓                                          │
│  ┌─────────────────────────────────────┐               │
│  │ HILO 3: BTC/USDT (1h)               │               │
│  ├─────────────────────────────────────┤               │
│  │ get_live_data('BTC/USDT', '1h')     │ ← Paralelo
│  │ _prepare_data(df)                   │               │
│  │ get_live_signal()                   │               │
│  │ monitor_positions()                 │               │
│  └─────────────────────────────────────┘               │
│              ↓                                          │
│  SINCRONIZACIÓN CENTRAL:                               │
│  ├─ Recolectar señales de todos los hilos              │
│  ├─ Validar limites de posiciones totales              │
│  ├─ Ejecutar órdenes (MT5 es single-threaded)         │
│  ├─ Monitorear todas las posiciones                    │
│  ├─ Sync con MT5 (una sola vez por ciclo)             │
│  └─ Log métricas consolidadas                         │
│              ↓                                          │
│  sleep(5s) → Próximo ciclo maestro                     │
└─────────────────────────────────────────────────────────┘

VENTAJAS:
├─ Procesamiento paralelo de datos (3x + rápido)
├─ MT5 sigue siendo single-threaded (sincronizado)
├─ Escalable a N símbolos sin perder rendimiento
├─ Independencia: Fallo en 1 símbolo no afecta otros
└─ Métricas consolidadas por símbolo
```

---

## 💻 Implementación: Versión Multi-Symbol

### Paso 1: Definir Símbolos en Config

```yaml
# descarga_datos/config/config.yaml

trading:
  symbols:
    - symbol: 'Volatility 75 Index'
      timeframe: '15m'
      strategy: 'UltraDetailedHeikinAshiML'
      enabled: true
      risk_per_trade: 0.02  # 2%
      max_positions: 5
      
    - symbol: 'Volatility 100 Index'
      timeframe: '15m'
      strategy: 'UltraDetailedHeikinAshiML'
      enabled: true
      risk_per_trade: 0.02
      max_positions: 5
      
    - symbol: 'BTC/USDT'
      timeframe: '1h'
      strategy: 'UltraDetailedHeikinAshiML'
      enabled: true
      risk_per_trade: 0.01  # 1% (menor para crypto)
      max_positions: 3
      
  # Limites globales
  total_max_positions: 10  # Total en toda la cuenta
  max_simultaneous_threads: 4  # Procesar 4 símbolos en paralelo
```

---

### Paso 2: Estructura de Clases Multi-Symbol

```python
# descarga_datos/core/multi_symbol_orchestrator.py

import threading
import concurrent.futures
from typing import Dict, List, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SymbolConfig:
    """Configuración de un símbolo individual"""
    symbol: str
    timeframe: str
    strategy_name: str
    enabled: bool
    risk_per_trade: float
    max_positions: int

class MultiSymbolOrchestrator:
    """Orquestador para múltiples símbolos en paralelo"""
    
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.data_provider = MT5LiveDataProvider()
        self.strategies = {}
        self.position_trackers = {}
        self.results = {}
        
        # Inicializar por símbolo
        self._initialize_symbols()
        
        # Thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.trading.max_simultaneous_threads
        )
    
    def _load_config(self, config_file: str) -> dict:
        """Cargar configuración de múltiples símbolos"""
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_symbols(self):
        """Inicializar estrategia y tracker por cada símbolo"""
        for symbol_config in self.config.trading.symbols:
            if not symbol_config['enabled']:
                continue
            
            symbol = symbol_config['symbol']
            
            # Cargar estrategia
            self.strategies[symbol] = self._load_strategy(
                symbol_config['strategy_name']
            )
            
            # Crear tracker de posiciones
            self.position_trackers[symbol] = PositionTracker(
                symbol=symbol,
                max_positions=symbol_config['max_positions']
            )
            
            logger.info(f"✅ Inicializado símbolo: {symbol}")
    
    def _load_strategy(self, strategy_name: str):
        """Cargar estrategia específica"""
        if strategy_name == 'UltraDetailedHeikinAshiML':
            return UltraDetailedHeikinAshiML()
        # Agregar más estrategias según sea necesario
        raise ValueError(f"Estrategia desconocida: {strategy_name}")
    
    def process_symbol_cycle(self, symbol_config: Dict[str, Any]) -> Dict:
        """
        Procesar UN símbolo en UN ciclo (se ejecuta en thread)
        
        IMPORTANTE: No tiene I/O bloqueante con MT5
        """
        symbol = symbol_config['symbol']
        timeframe = symbol_config['timeframe']
        
        try:
            # 1. Cargar 200 barras (parallelizable)
            logger.debug(f"[{symbol}] Cargando {200} barras {timeframe}...")
            df = self.data_provider.get_live_data(symbol, timeframe, 200)
            
            if df is None or len(df) < 50:
                logger.warning(f"[{symbol}] Datos insuficientes")
                return {'symbol': symbol, 'signal': None, 'error': 'Datos insuficientes'}
            
            # 2. Preparar datos: agregar 25 indicadores (parallelizable)
            logger.debug(f"[{symbol}] Preparando datos con indicadores...")
            df_prepared = self._prepare_data(df)
            
            if df_prepared is None:
                logger.warning(f"[{symbol}] Error preparando datos")
                return {'symbol': symbol, 'signal': None, 'error': 'Error en preparación'}
            
            # 3. Generar señal ML (parallelizable)
            logger.debug(f"[{symbol}] Generando señal ML...")
            strategy = self.strategies[symbol]
            signal_result = strategy.get_live_signal(df_prepared)
            
            if signal_result is None:
                return {'symbol': symbol, 'signal': 'HOLD', 'confidence': 0}
            
            # Retornar resultado (SIN ejecutar orden aún)
            return {
                'symbol': symbol,
                'signal': signal_result.get('signal', 'HOLD'),
                'signal_data': signal_result.get('signal_data', {}),
                'confidence': signal_result.get('signal_data', {}).get('ml_confidence', 0),
                'error': None
            }
        
        except Exception as e:
            logger.error(f"[{symbol}] Error en ciclo: {e}")
            return {'symbol': symbol, 'signal': None, 'error': str(e)}
    
    def run_master_cycle(self):
        """
        CICLO MAESTRO: Ejecuta TODO en paralelo
        
        Flujo:
        1. Lanzar N threads (uno por símbolo)
        2. Esperar a que terminen (barrier)
        3. Recolectar señales
        4. Ejecutar órdenes (serial en MT5)
        5. Monitorear todas (serial)
        6. Sincronizar con MT5 (serial)
        """
        
        logger.info("="*60)
        logger.info(f"CICLO MAESTRO INICIADO - {len(self.config.trading.symbols)} símbolos")
        logger.info("="*60)
        
        start_time = time.time()
        
        # ETAPA 1: PROCESAMIENTO PARALELO
        # ─────────────────────────────
        logger.info("📊 [ETAPA 1] Procesamiento paralelo de símbolos...")
        
        # Lanzar todos los threads
        futures = {}
        for symbol_config in self.config.trading.symbols:
            if not symbol_config['enabled']:
                continue
            
            symbol = symbol_config['symbol']
            future = self.executor.submit(self.process_symbol_cycle, symbol_config)
            futures[symbol] = future
            logger.debug(f"  └─ Thread iniciado para {symbol}")
        
        # Esperar a que terminen todos
        results = {}
        for symbol, future in futures.items():
            try:
                result = future.result(timeout=10)  # Max 10 seg por símbolo
                results[symbol] = result
                logger.debug(f"  └─ {symbol} completado: {result.get('signal')}")
            except concurrent.futures.TimeoutError:
                logger.error(f"  └─ {symbol} TIMEOUT (>10s)")
                results[symbol] = {'symbol': symbol, 'signal': None, 'error': 'Timeout'}
            except Exception as e:
                logger.error(f"  └─ {symbol} ERROR: {e}")
                results[symbol] = {'symbol': symbol, 'signal': None, 'error': str(e)}
        
        etapa1_time = time.time() - start_time
        logger.info(f"✅ ETAPA 1 completada en {etapa1_time:.2f}s")
        
        # ETAPA 2: EJECUCIÓN SERIAL EN MT5
        # ────────────────────────────────
        logger.info("📊 [ETAPA 2] Ejecución de órdenes en MT5 (serial)...")
        
        execution_start = time.time()
        executions = []
        
        for symbol, result in results.items():
            if result['signal'] in ['BUY', 'SELL']:
                logger.info(f"  └─ Ejecutando {result['signal']} para {symbol}")
                
                try:
                    exec_result = self._execute_signal_mt5(symbol, result)
                    executions.append(exec_result)
                    logger.info(f"     ✅ Orden ejecutada: {exec_result.get('ticket')}")
                except Exception as e:
                    logger.error(f"     ❌ Error ejecutando: {e}")
            else:
                logger.debug(f"  └─ Sin señal para {symbol} (HOLD)")
        
        etapa2_time = time.time() - execution_start
        logger.info(f"✅ ETAPA 2 completada en {etapa2_time:.2f}s")
        
        # ETAPA 3: MONITOREO DE TODAS LAS POSICIONES
        # ──────────────────────────────────────────
        logger.info("📊 [ETAPA 3] Monitoreo de posiciones activas...")
        
        monitor_start = time.time()
        
        for symbol in self.position_trackers.keys():
            try:
                self._monitor_symbol_positions(symbol)
            except Exception as e:
                logger.error(f"  └─ Error monitoreando {symbol}: {e}")
        
        etapa3_time = time.time() - monitor_start
        logger.info(f"✅ ETAPA 3 completada en {etapa3_time:.2f}s")
        
        # ETAPA 4: SINCRONIZACIÓN CON MT5 (cada 30s)
        # ──────────────────────────────────────────
        if time.time() % 30 < 5:  # Cada 30 segundos aprox
            logger.info("📊 [ETAPA 4] Sincronización con MT5...")
            
            sync_start = time.time()
            
            for symbol in self.position_trackers.keys():
                try:
                    self._sync_symbol_with_mt5(symbol)
                except Exception as e:
                    logger.error(f"  └─ Error sincronizando {symbol}: {e}")
            
            etapa4_time = time.time() - sync_start
            logger.info(f"✅ ETAPA 4 completada en {etapa4_time:.2f}s")
        
        # RESUMEN DEL CICLO
        # ────────────────
        total_time = time.time() - start_time
        
        logger.info("="*60)
        logger.info("📊 RESUMEN DEL CICLO MAESTRO")
        logger.info("="*60)
        logger.info(f"Total señales: {len([r for r in results.values() if r['signal']])} / {len(results)}")
        logger.info(f"Órdenes ejecutadas: {len(executions)}")
        logger.info(f"Tiempo etapa 1 (paralelo): {etapa1_time:.2f}s")
        logger.info(f"Tiempo etapa 2 (ejecución): {etapa2_time:.2f}s")
        logger.info(f"Tiempo etapa 3 (monitoreo): {etapa3_time:.2f}s")
        logger.info(f"Tiempo total: {total_time:.2f}s")
        logger.info(f"Próximo ciclo en: {5 - (total_time % 5):.1f}s")
        logger.info("="*60)
```

---

### Paso 3: Loop Principal Multi-Symbol

```python
# descarga_datos/main.py (modificado para multi-symbol)

def run_live_trading_multi_symbol():
    """Modo trading en vivo con múltiples símbolos"""
    
    logger.info("🚀 Iniciando LIVE TRADING MULTI-SYMBOL")
    
    # Cargar orquestador
    orchestrator = MultiSymbolOrchestrator(
        config_file='config/config.yaml'
    )
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            
            # CICLO MAESTRO
            orchestrator.run_master_cycle()
            
            # Esperar hasta próximo ciclo (5 segundos)
            remaining = 5 - (time.time() % 5)
            if remaining > 0:
                logger.debug(f"⏱️  Esperando {remaining:.2f}s hasta próximo ciclo...")
                time.sleep(remaining)
            
            if cycle_count % 10 == 0:
                logger.info(f"✅ Ciclos completados: {cycle_count}")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️  Usuario interrumpió (Ctrl+C)")
        orchestrator.shutdown()
    
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        orchestrator.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--live-multi', action='store_true',
                        help='Modo live trading multi-símbolo')
    
    args = parser.parse_args()
    
    if args.live_multi:
        run_live_trading_multi_symbol()
```

---

## 📊 Comparativa: 1 vs N Símbolos

```
MÉTRICA                      | 1 SÍMBOLO      | 3 SÍMBOLOS | N SÍMBOLOS
─────────────────────────────┼────────────────┼────────────┼──────────────
Tiempo carga datos           | 50ms           | 50ms       | 50ms
(paralelo no importa)        |                |            |
                             |                |            |
Tiempo cálculo indicadores   | 100ms          | 100ms      | 100ms
(paralelo no importa)        |                |            |
                             |                |            |
Tiempo señal ML              | 20ms           | 20ms       | 20ms
(paralelo no importa)        |                |            |
─────────────────────────────┼────────────────┼────────────┼──────────────
SERIAL (sin paralelismo):    | 170ms + 3×280ms= 3× 170ms = 
Tiempo total sin paralelismo | 170ms          | 510ms      | N×170ms
                             |                |            |
CON PARALELISMO:             |                |            |
Tiempo total con paralelo    | 170ms          | 200ms      | ~250ms
                             | (1 ciclo)      | (1 ciclo)  | (1 ciclo)
                             |                |            |
MEJORA (speedup)             | 1x             | 2.55x      | (N×170)/250
─────────────────────────────┼────────────────┼────────────┼──────────────
Posiciones abiertas          | Max 1-5        | Max 5-15   | Max variable
                             |                |            |
Capital utilizado            | 2-5% balance   | 6-15%      | Configurable
                             |                |            |
P&L flotante                 | ±$17.67        | ±$50-100   | Escalado
─────────────────────────────┼────────────────┼────────────┼──────────────
Consumo CPU                  | ~5%            | ~12%       | ~15-20%
                             | (1 core)       | (2 cores)  | (3+ cores)
                             |                |            |
Consumo memoria              | ~50 MB         | ~120 MB    | ~200+ MB
─────────────────────────────┼────────────────┼────────────┼──────────────
Latencia MT5                 | <1ms           | <1ms       | <1ms
(no afectada)                | (order_send)   | (serial)   | (serial)
```

---

## 🎯 Casos de Uso Prácticos

### Caso 1: Volatilidad Múltiple

```python
# Tradear Volatility 75, 100, 150 en paralelo

config.yaml:
trading:
  symbols:
    - symbol: 'Volatility 75 Index'
      timeframe: '15m'
      risk_per_trade: 0.02
    
    - symbol: 'Volatility 100 Index'
      timeframe: '15m'
      risk_per_trade: 0.02
    
    - symbol: 'Volatility 150 Index'
      timeframe: '15m'
      risk_per_trade: 0.015  # Menos riesgo por símbolo
  
  total_max_positions: 8  # Total de todas

RESULTADO:
├─ Procesamiento paralelo: 3 hilos
├─ Tiempo ciclo: ~200ms (vs 510ms serial)
├─ Posiciones posibles: 2-3 por símbolo
├─ P&L: 3x potencial (pero 3x riesgo)
└─ Decorrelación: Diferentes volatilidades
```

### Caso 2: Multi-Timeframe

```python
# Mismo símbolo en 3 timeframes

config.yaml:
trading:
  symbols:
    - symbol: 'Volatility 75 Index'
      timeframe: '5m'
      risk_per_trade: 0.01
    
    - symbol: 'Volatility 75 Index'
      timeframe: '15m'
      risk_per_trade: 0.02
    
    - symbol: 'Volatility 75 Index'
      timeframe: '1h'
      risk_per_trade: 0.015
  
  total_max_positions: 5  # Compartidas

VENTAJAS:
├─ Diversificación temporal
├─ Señales corto, medio, largo plazo
├─ Filtros cruzados (1h confirma 15m)
├─ Mayor precisión de entrada
└─ Menos falsas señales
```

### Caso 3: Múltiples Activos + Timeframes

```python
# Combinación completa

config.yaml:
trading:
  symbols:
    # Synthetics (alta volatilidad)
    - symbol: 'Volatility 75 Index'
      timeframe: '15m'
      risk_per_trade: 0.02
    
    - symbol: 'Volatility 100 Index'
      timeframe: '15m'
      risk_per_trade: 0.02
    
    # Crypto (media volatilidad)
    - symbol: 'BTC/USDT'
      timeframe: '1h'
      risk_per_trade: 0.015
    
    # Forex (baja volatilidad, requiere más barras)
    - symbol: 'EURUSD'
      timeframe: '15m'
      risk_per_trade: 0.01
  
  total_max_positions: 10
  max_simultaneous_threads: 4

ESTADÍSTICAS:
├─ Procesamiento paralelo: 4 hilos
├─ Tiempo ciclo: ~200-250ms
├─ Posiciones activas: 2-3 simultáneas
├─ P&L diversificado: No correlacionado
├─ Resiliencia: Fallo en 1 ≠ afecta otros
└─ Escalabilidad: Agregar símbolos sin overhead
```

---

## ⚠️ Consideraciones Críticas

### 1. MT5 es Single-Threaded

```python
# ❌ INCORRECTO: Múltiples threads llamando a MT5 simultáneamente
def bad_approach(symbols):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for symbol in symbols:
            # ❌ FALLO: Múltiples threads en MT5.order_send()
            future = executor.submit(mt5.order_send, request)
            futures.append(future)

# ✅ CORRECTO: Threads en paralelo, pero MT5 serial
def good_approach(symbols):
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Hilos procesan datos
        results = [executor.submit(get_signal, symbol) for symbol in symbols]
        
        # Esperar
        signals = [f.result() for f in results]
        
        # LUEGO: Ejecutar en MT5 (serial)
        for signal in signals:
            mt5.order_send(signal)  # ← Una llamada a la vez
```

### 2. Limites de Posiciones

```python
# Validación antes de ejecutar
class PositionValidator:
    def can_open_position(self, symbol: str, volume: float) -> bool:
        """¿Podemos abrir posición?"""
        
        # Check 1: Máximo por símbolo
        symbol_positions = self.get_positions_for_symbol(symbol)
        if len(symbol_positions) >= self.config.max_positions_per_symbol:
            logger.warning(f"Máximo de posiciones para {symbol} alcanzado")
            return False
        
        # Check 2: Máximo global
        total_positions = self.get_all_open_positions()
        if len(total_positions) >= self.config.total_max_positions:
            logger.warning("Máximo de posiciones globales alcanzado")
            return False
        
        # Check 3: Margen disponible
        account = mt5.account_info()
        required_margin = self.calculate_margin(symbol, volume)
        if account.free_margin < required_margin:
            logger.warning("Margen insuficiente")
            return False
        
        return True
```

### 3. Sincronización Segura

```python
import threading

class ThreadSafePositionTracker:
    def __init__(self):
        self.positions = {}
        self.lock = threading.RLock()  # Recursive lock
    
    def add_position(self, symbol: str, position: dict) -> bool:
        """Agregar posición de forma thread-safe"""
        with self.lock:  # ← Protege el acceso
            if symbol not in self.positions:
                self.positions[symbol] = []
            
            self.positions[symbol].append(position)
            logger.info(f"✅ Posición agregada: {symbol}")
            return True
    
    def get_positions_for_symbol(self, symbol: str) -> List[dict]:
        """Obtener posiciones para símbolo"""
        with self.lock:  # ← Thread-safe
            return self.positions.get(symbol, []).copy()
    
    def get_all_positions(self) -> int:
        """Contador total de posiciones"""
        with self.lock:  # ← Thread-safe
            return sum(len(p) for p in self.positions.values())
```

---

## 📊 Monitoreo Multi-Symbol

```python
class MultiSymbolMetrics:
    """Métricas consolidadas para múltiples símbolos"""
    
    def calculate_metrics(self) -> dict:
        """Calcular métricas globales"""
        
        all_positions = self.get_all_positions()
        
        metrics = {
            'total_positions': len(all_positions),
            'total_pl_floating': sum(p.get('pl_floating', 0) for p in all_positions),
            'total_pl_closed': self.get_closed_trades_pl(),
            'account_balance': mt5.account_info().balance,
            'account_equity': mt5.account_info().equity,
            
            'por_simbolo': {
                symbol: {
                    'posiciones': len(self.get_positions_for_symbol(symbol)),
                    'pl_floating': sum(p.get('pl_floating', 0) for p in self.get_positions_for_symbol(symbol)),
                    'señales_ciclo': self.last_signals.get(symbol, 'HOLD'),
                    'confianza': self.last_confidences.get(symbol, 0),
                }
                for symbol in self.symbols
            },
            
            'riesgo': {
                'max_drawdown': self.calculate_max_drawdown(),
                'margem_utilizado': self.calculate_margin_usage(),
                'riesgo_total': sum(p.get('position_risk', 0) for p in all_positions),
            },
            
            'rendimiento': {
                'win_rate': self.calculate_win_rate(),
                'profit_factor': self.calculate_profit_factor(),
                'sharpe_ratio': self.calculate_sharpe_ratio(),
            }
        }
        
        return metrics
    
    def log_metrics(self):
        """Loguear métricas consolidadas"""
        metrics = self.calculate_metrics()
        
        logger.info("="*70)
        logger.info("📊 MÉTRICAS MULTI-SYMBOL")
        logger.info("="*70)
        logger.info(f"Posiciones totales: {metrics['total_positions']}")
        logger.info(f"P&L flotante: ${metrics['total_pl_floating']:.2f}")
        logger.info(f"Balance: ${metrics['account_balance']:.2f}")
        logger.info(f"Equity: ${metrics['account_equity']:.2f}")
        
        logger.info("\nPor símbolo:")
        for symbol, data in metrics['por_simbolo'].items():
            logger.info(f"  {symbol:20s} | Pos: {data['posiciones']} | P&L: ${data['pl_floating']:8.2f} | Señal: {data['señales_ciclo']}")
        
        logger.info("\nRiesgo:")
        logger.info(f"  Max Drawdown: {metrics['riesgo']['max_drawdown']:.2f}%")
        logger.info(f"  Margen usado: {metrics['riesgo']['margem_utilizado']:.1f}%")
        logger.info(f"  Riesgo total: ${metrics['riesgo']['riesgo_total']:.2f}")
```

---

## 🚀 Roadmap: Escalado a Producción

```
FASE 1: Validación (1-2 semanas)
├─ Implementar orquestador multi-symbol
├─ Ejecutar 3 símbolos en paralelo
├─ Validar sincronización MT5
├─ Validar pos limits y margen
└─ ✅ Producción simulada

FASE 2: Optimización (1 semana)
├─ Perfilar performance (CPU, memory)
├─ Ajustar pool de threads
├─ Optimizar cálculo de indicadores
├─ Implementar caching de datos
└─ ✅ Performance objetivo: <300ms/ciclo

FASE 3: Monitoreo (1 semana)
├─ Implementar alertas por símbolo
├─ Dashboard de métricas consolidadas
├─ Health check automático
├─ Auto-shutdown en condiciones extremas
└─ ✅ Sistema robusto

FASE 4: Escalado (2 semanas)
├─ Agregar 5-10 símbolos más
├─ Escalar a 8+ threads
├─ Distribuir en múltiples máquinas
├─ Replicación de datos
└─ ✅ Sistema empresarial
```

---

**Documento**: Arquitectura Multi-Symbol  
**Versión**: v4.10  
**Status**: ✅ Listo para Implementación  
**Speedup Esperado**: 2-3x con 3-4 símbolos
