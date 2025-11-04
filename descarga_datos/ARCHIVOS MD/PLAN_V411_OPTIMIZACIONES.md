# 🚀 Plan de Optimizaciones v4.11

## 📋 Overview

**Rama**: `v4.11-performance-optimization`  
**Objetivo**: Reducir ciclo de 5000ms → 500ms (10x mejora)  
**Base**: v4.10 (Live MT5 operacional)  
**Fecha inicio**: 2025-11-04  
**Status**: PLANIFICADO

---

## 🎯 Optimizaciones Prioritizadas

### OPTIMIZACIÓN 1: Caching de Datos (8.3x)
**Estado**: ⏳ Por implementar  
**Archivo target**: `core/mt5_live_data.py`  
**Mejora esperada**: 50ms → 6ms  

```python
# Patrón a implementar
class CachedDataProvider:
    def __init__(self):
        self.cache = {}
        self.last_update = None
        self.cache_ttl = 3  # 3 ciclos
    
    def get_bars(self, symbol, timeframe, count=200):
        cache_key = f"{symbol}_{timeframe}"
        
        # Retorna cache si está válido
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Si no, obtiene del servidor
        data = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        self.cache[cache_key] = data
        self.last_update[cache_key] = time.time()
        return data
    
    def _is_cache_valid(self, key):
        if key not in self.cache:
            return False
        age = time.time() - self.last_update[key]
        return age < self.cache_ttl
```

**Implementación**:
- [ ] Crear clase `CachedDataProvider` en `core/cached_data.py`
- [ ] Modificar `get_live_data()` para usar cache
- [ ] Agregar invalidación inteligente
- [ ] Tests: Validar cache hit rate
- [ ] Benchmark: Medir 50ms → 6ms

---

### OPTIMIZACIÓN 2: NumPy Vectorizado + Numba JIT (3.3x)
**Estado**: ⏳ Por implementar  
**Archivo target**: `indicators/technical_indicators.py`  
**Mejora esperada**: 100ms → 30ms  

```python
# Patrón a implementar
import numpy as np
from numba import jit

@jit(nopython=True, cache=True)
def calculate_ema_numba(prices, period):
    """EMA vectorizado con JIT - 3x más rápido"""
    result = np.zeros_like(prices)
    alpha = 2.0 / (period + 1.0)
    result[0] = prices[0]
    
    for i in range(1, len(prices)):
        result[i] = alpha * prices[i] + (1 - alpha) * result[i-1]
    
    return result

@jit(nopython=True, cache=True)
def calculate_rsi_numba(prices, period=14):
    """RSI vectorizado con JIT"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

@jit(nopython=True, cache=True)
def calculate_adx_numba(high, low, close, period=14):
    """ADX vectorizado con JIT"""
    # Implementación JIT compilada
    return np.array([50.0])  # Placeholder
```

**Implementación**:
- [ ] Instalar `numba`: `pip install numba`
- [ ] Vectorizar indicadores principales (EMA, RSI, ADX, ATR)
- [ ] Compilar con `@jit(cache=True)` para evitar recompilación
- [ ] Tests: Validar resultados == indicadores originales
- [ ] Benchmark: Medir 100ms → 30ms
- [ ] Profile: Identificar bottlenecks restantes

---

### OPTIMIZACIÓN 3: ONNX ML Model (20x)
**Estado**: ⏳ Por implementar  
**Archivo target**: `models/ml_model_onnx.py`  
**Mejora esperada**: 20ms → 1ms  

```python
# Patrón a implementar
import onnx
import onnxruntime as rt
import numpy as np

class ONNXModelPredictor:
    def __init__(self, model_path='models/rf_model.onnx'):
        """Cargador de modelo ONNX optimizado"""
        self.sess = rt.InferenceSession(
            model_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name
    
    def predict(self, features):
        """Predicción ultra-rápida con ONNX"""
        # features: array (1, 25) - 25 features normalizadas
        
        # Forzar tipo correcto
        features_np = np.array([features], dtype=np.float32)
        
        # Predicción ONNX (1ms típicamente)
        result = self.sess.run(
            [self.output_name],
            {self.input_name: features_np}
        )
        
        return result[0][0]  # Retorna señal (BUY/SELL/HOLD)
    
    @staticmethod
    def convert_sklearn_to_onnx(sklearn_model, init_types):
        """Convierte RandomForest sklearn a ONNX"""
        from skl2onnx import convert_sklearn
        from onnxmltools.utils import float_model
        
        initial_type = [('float_input', init_types)]
        onx = convert_sklearn(sklearn_model, initial_types=initial_type)
        
        # Optimizar
        onx = float_model(onx)
        return onx
```

**Implementación**:
- [ ] Instalar `onnx` y `onnxruntime`: `pip install onnx onnxruntime skl2onnx`
- [ ] Convertir modelo RandomForest a ONNX
- [ ] Crear `ONNXModelPredictor` class
- [ ] Reemplazar predicción en `strategies/ultra_detailed_heikin_ashi_ml_strategy.py`
- [ ] Tests: Validar salidas == RandomForest original
- [ ] Benchmark: Medir 20ms → 1ms
- [ ] Validar con CUDA si GPU disponible

---

### OPTIMIZACIÓN 4: Monitoreo Indexado (6.25x)
**Estado**: ⏳ Por implementar  
**Archivo target**: `live_trading_orchestrator.py`  
**Mejora esperada**: 50ms → 8ms  

```python
# Patrón a implementar
from collections import defaultdict
import threading

class ThreadSafePositionTracker:
    def __init__(self):
        """Tracker de posiciones con indexación O(1)"""
        self.positions = {}  # symbol -> position
        self.by_status = defaultdict(set)  # status -> {symbols}
        self.lock = threading.RLock()
    
    def add_position(self, symbol, position):
        """Agregar posición - O(1)"""
        with self.lock:
            self.positions[symbol] = position
            self.by_status[position['status']].add(symbol)
    
    def get_active_positions(self):
        """Obtener posiciones activas - O(1) vs O(n)"""
        with self.lock:
            # Sin índice: iterar todas las posiciones O(n)
            # Con índice: acceso directo a conjunto O(1)
            return [self.positions[s] for s in self.by_status['OPEN']]
    
    def get_by_sl_triggered(self):
        """Obtener posiciones con SL hit - O(1)"""
        with self.lock:
            return [self.positions[s] for s in self.by_status['SL_HIT']]
    
    def update_position_status(self, symbol, new_status):
        """Actualizar status - O(1)"""
        with self.lock:
            old_status = self.positions[symbol]['status']
            self.by_status[old_status].discard(symbol)
            self.positions[symbol]['status'] = new_status
            self.by_status[new_status].add(symbol)

class IndexedPositionMonitor:
    def __init__(self, max_positions=100):
        """Monitor de posiciones con búsqueda indexada"""
        self.tracker = ThreadSafePositionTracker()
        self.max_positions = max_positions
    
    def check_all_positions(self):
        """Monitoreo ultra-rápido de todas las posiciones"""
        # Acceso O(1) a posiciones activas en vez de O(n)
        active = self.tracker.get_active_positions()
        
        for position in active:
            self._check_sl_tp(position)
    
    def _check_sl_tp(self, position):
        """Verificación rápida de SL/TP"""
        current_price = self._get_current_price(position['symbol'])
        
        if self._is_sl_hit(position, current_price):
            self.tracker.update_position_status(position['symbol'], 'SL_HIT')
        elif self._is_tp_hit(position, current_price):
            self.tracker.update_position_status(position['symbol'], 'TP_HIT')
```

**Implementación**:
- [ ] Crear `ThreadSafePositionTracker` en `utils/position_tracker.py`
- [ ] Crear `IndexedPositionMonitor` en `utils/position_monitor.py`
- [ ] Reemplazar monitoreo en `live_trading_orchestrator.py`
- [ ] Tests: Validar thread-safety con race conditions
- [ ] Benchmark: Medir 50ms → 8ms
- [ ] Stress test: 100+ posiciones simultáneas

---

## 📊 Roadmap Implementación

### Fase 1: Fundamentos (Days 1-2)
- [ ] Crear rama `v4.11-performance-optimization`
- [ ] Configurar ambiente de desarrollo
- [ ] Preparar suite de tests
- [ ] Crear benchmarks baseline

### Fase 2: Optimización 1 - Caching (Days 3-4)
- [ ] Implementar `CachedDataProvider`
- [ ] Tests unitarios
- [ ] Benchmark: Validar 8.3x
- [ ] Commit & PR review

### Fase 3: Optimización 2 - Numba JIT (Days 5-7)
- [ ] Vectorizar indicadores principales
- [ ] Compilar con Numba JIT
- [ ] Tests de precisión
- [ ] Benchmark: Validar 3.3x
- [ ] Commit & PR review

### Fase 4: Optimización 3 - ONNX (Days 8-10)
- [ ] Convertir modelo a ONNX
- [ ] Implementar `ONNXModelPredictor`
- [ ] Tests de predicción
- [ ] Benchmark: Validar 20x
- [ ] Commit & PR review

### Fase 5: Optimización 4 - Indexing (Days 11-12)
- [ ] Implementar indexadores
- [ ] Tests thread-safety
- [ ] Benchmark: Validar 6.25x
- [ ] Commit & PR review

### Fase 6: Integración & Validación (Days 13-15)
- [ ] Integrar todas las optimizaciones
- [ ] Validar ciclo completo: 5000ms → 500ms
- [ ] Tests de regresión
- [ ] Live trading validation
- [ ] Merge a master

---

## 🧪 Tests Requeridos

### Test Suite para v4.11

```python
# tests/test_v411_optimizations.py

class TestCachedDataProvider:
    def test_cache_hit_returns_cached_data(self):
        pass
    
    def test_cache_invalidation(self):
        pass
    
    def test_cache_performance_8x(self):
        pass

class TestNumbaIndicators:
    def test_ema_numba_equals_original(self):
        pass
    
    def test_rsi_numba_equals_original(self):
        pass
    
    def test_indicators_performance_3x(self):
        pass

class TestONNXModel:
    def test_onnx_predictions_match_sklearn(self):
        pass
    
    def test_onnx_performance_20x(self):
        pass

class TestIndexedPositionMonitor:
    def test_position_tracking_o1(self):
        pass
    
    def test_thread_safety(self):
        pass
    
    def test_position_monitor_performance_6x(self):
        pass

class TestIntegration:
    def test_full_cycle_5000ms_to_500ms(self):
        pass
    
    def test_live_trading_after_optimization(self):
        pass
```

---

## 📈 Métricas de Éxito

| Métrica | Baseline v4.10 | Target v4.11 | Validación |
|---------|---|---|---|
| Ciclo total | 5000ms | 500ms | Profiler |
| Cache hit rate | N/A | >80% | Logs |
| Predicción ML | 20ms | 1ms | Benchmark |
| Indicadores | 100ms | 30ms | Numba profile |
| Monitoreo | 50ms | 8ms | Thread monitor |
| Backtest trades | 7,896 | >= 7,896 | Regression |
| Win rate | 79.89% | >= 79.89% | Stats |

---

## 📝 Archivos a Crear/Modificar

### Nuevos Archivos
```
descarga_datos/
├── utils/
│   ├── cached_data.py          (Caching)
│   ├── position_tracker.py      (Thread-safe tracker)
│   └── position_monitor.py      (Indexed monitor)
├── models/
│   ├── ml_model_onnx.py         (ONNX predictor)
│   └── rf_model.onnx            (Modelo convertido)
└── tests/
    └── test_v411_optimizations.py (Suite completa)
```

### Archivos Modificados
```
descarga_datos/
├── core/
│   ├── mt5_live_data.py         (Usar CachedDataProvider)
│   └── live_trading_orchestrator.py (Usar IndexedMonitor)
├── indicators/
│   └── technical_indicators.py  (Numba JIT decorators)
└── strategies/
    └── ultra_detailed_heikin_ashi_ml_strategy.py (ONNX predictor)
```

---

## 🔄 Git Workflow

```bash
# Rama actual
git branch
# * v4.11-performance-optimization
# master

# Commits por optimización
git log --oneline origin/master..HEAD

# Al finalizar, PR a master
git push origin v4.11-performance-optimization
# Crear PR: v4.11 → master
# Code review & merge
```

---

## ⚠️ Riesgos & Mitigación

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Cache invalidation bugs | Alta | Validar con race conditions, use TTL |
| Numba compilation lenta | Media | Usar `cache=True`, compilar una sola vez |
| ONNX model precision loss | Alta | Comparar outputs, tolerance 1e-6 |
| Thread race conditions | Alta | Use RLock, validar con Thread Sanitizer |
| Performance no alcanza 500ms | Media | Perfilar más, identificar cuello de botella |

---

## 📞 Contacto

**Rama**: `v4.11-performance-optimization`  
**Owner**: Javier Tarazon  
**Reviewers**: [Por definir]  
**Status**: PLANIFICADO  
**Inicio**: 2025-11-04  
**ETA**: 15 días

---

**v4.11 Optimization Plan**  
**Created**: 2025-11-04  
**Version**: 1.0  
**Status**: READY TO IMPLEMENT
