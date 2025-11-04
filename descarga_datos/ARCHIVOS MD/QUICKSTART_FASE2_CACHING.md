# ⚡ QUICK START FASE 2 - Caching Implementation

## 🎯 Objetivo
Integrar `CachedDataProvider` en `core/mt5_live_data.py`  
**Speedup esperado**: 50ms → 6ms (8.3x)  
**Duración**: 4 días  
**Deadline**: 8 de Noviembre, 2025

---

## 📋 Checklist Rápido

```
ANTES DE EMPEZAR:
[ ] Estoy en rama v4.11-performance-optimization
[ ] He leído GUIA_IMPLEMENTACION_V411.md
[ ] Tengo acceso a core/mt5_live_data.py
[ ] Entiendo CachedDataProvider (cached_data_provider.py)

DÍA 1: INTEGRACIÓN
[ ] Agregar import de CachedDataProvider
[ ] Crear instancia en __init__()
[ ] Reemplazar get_live_data() para usar cache
[ ] Test rápido: python main.py --live (5 min)

DÍA 2: TESTS
[ ] Ejecutar: pytest test_v411_optimizations.py::TestCachedDataProvider
[ ] Validar: cache hit rate > 80%
[ ] Revisar logs: "Cache HIT" vs "Cache MISS"

DÍA 3: LIVE TRADING
[ ] Ejecutar: python main.py --live
[ ] Monitorear: 10+ ciclos sin errores
[ ] Revisar P&L: debe ser IDÉNTICO a v4.10

DÍA 4: BENCHMARK
[ ] Ejecutar: python v411_optimizations/cached_data_provider.py
[ ] Validar: 50ms → 6ms (8.3x speedup)
[ ] Commit & merge

DONE: Commit a rama
```

---

## 🔧 DÍA 1: Integración

### Paso 1: Revisar Código Actual

**Archivo**: `core/mt5_live_data.py`

```python
# Buscar línea ~50-100 donde está get_live_data()
def get_live_data(self, symbol, timeframe, count=200):
    """Obtiene datos OHLCV de MT5."""
    
    # Típicamente hace esto:
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        logger.warning(f"No data from MT5 for {symbol}")
        return None
    
    df = pd.DataFrame(rates)
    # ... procesamiento ...
    return df
```

### Paso 2: Agregar CachedDataProvider

**Acción**: Modificar `core/mt5_live_data.py` línea ~1-20 (imports)

```python
# ANTES:
import mt5
import pandas as pd
import logging

# DESPUÉS:
import mt5
import pandas as pd
import logging
from pathlib import Path
import sys

# Agregar v411_optimizations al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v411_optimizations'))
from cached_data_provider import CachedDataProvider

logger = logging.getLogger(__name__)
```

### Paso 3: Crear Instancia en __init__()

**Acción**: Modificar `__init__()` de MT5DataProvider

```python
# ANTES:
class MT5DataProvider:
    def __init__(self, config):
        self.symbol = config.get('symbol', 'EURUSD')
        self.timeframe = config.get('timeframe', 'M15')
        # ...

# DESPUÉS:
class MT5DataProvider:
    def __init__(self, config):
        self.symbol = config.get('symbol', 'EURUSD')
        self.timeframe = config.get('timeframe', 'M15')
        
        # NEW: Inicializar cache
        self.data_cache = CachedDataProvider(
            cache_ttl_seconds=3,  # 3 ciclos (5s each)
            max_cache_size=10  # máx 10 símbolos
        )
        logger.info("✅ CachedDataProvider initialized")
        # ...
```

### Paso 4: Usar Cache en get_live_data()

**Acción**: Reemplazar `get_live_data()` para usar cache

```python
# ANTES:
def get_live_data(self, symbol, timeframe, count=200):
    """Obtiene datos OHLCV de MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        return None
    
    df = pd.DataFrame(rates)
    return df

# DESPUÉS:
def get_live_data(self, symbol, timeframe, count=200):
    """Obtiene datos OHLCV de MT5 (con caching)."""
    
    # USAR CACHE - esto hace el trabajo pesado
    df = self.data_cache.get_bars(
        symbol,
        timeframe,
        count,
        fetch_func=self._fetch_from_mt5  # Función que hace la llamada a MT5
    )
    
    if df is None:
        logger.warning(f"❌ Cache miss & failed to fetch {symbol}")
        return None
    
    return df

def _fetch_from_mt5(self, symbol, timeframe, count):
    """Helper: Obtener datos directamente de MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is None or len(rates) == 0:
        return None
    
    return pd.DataFrame(rates)
```

### Paso 5: Test Rápido

```bash
# Ejecutar live trading por 5 minutos
cd descarga_datos
python main.py --live 2>&1 | grep -E "Cache|HIT|MISS" | head -20

# Esperado ver:
# ✅ Cache HIT: EURUSD_16408 (age=0.12s)
# ✅ Cache HIT: EURUSD_16408 (age=0.23s)
# ❌ Cache MISS: EURUSD_16408
# ... después de 3s ...
# ✅ Cache HIT: EURUSD_16408 (age=0.05s)
```

---

## 🧪 DÍA 2: Tests Unitarios

### Ejecutar Tests

```bash
cd descarga_datos

# Test 1: Cache hit/miss
pytest tests/test_v411_optimizations.py::TestCachedDataProvider::test_cache_hit -v

# Test 2: TTL expiration
pytest tests/test_v411_optimizations.py::TestCachedDataProvider::test_cache_miss_after_ttl -v

# Test 3: Invalidation
pytest tests/test_v411_optimizations.py::TestCachedDataProvider::test_cache_invalidation -v

# Test 4: Hit rate
pytest tests/test_v411_optimizations.py::TestCachedDataProvider::test_cache_hit_rate -v

# Test 5: Multiple symbols
pytest tests/test_v411_optimizations.py::TestCachedDataProvider::test_multiple_symbols -v

# TODOS los tests
pytest tests/test_v411_optimizations.py::TestCachedDataProvider -v
```

### Validación Esperada

```
✅ test_cache_hit PASSED
✅ test_cache_miss_after_ttl PASSED
✅ test_cache_invalidation PASSED
✅ test_cache_hit_rate PASSED
✅ test_multiple_symbols PASSED

5 passed in 2.34s
```

### Si Algún Test Falla

**Problema 1: "ModuleNotFoundError: No module named 'cached_data_provider'"**
```python
# Solución: Verificar path en test_v411_optimizations.py línea ~20:
sys.path.insert(0, str(Path(__file__).parent.parent / 'v411_optimizations'))
```

**Problema 2: "Cache hit rate es 0%"**
```python
# Solución: Revisar que cache_ttl en test sea suficiente
provider = CachedDataProvider(cache_ttl_seconds=10)  # Aumentar TTL
```

---

## 📊 DÍA 3: Validación Live Trading

### Ejecutar Live Trading 24h

```bash
# Terminal 1: Ejecutar live trading
cd descarga_datos
python main.py --live > live_phase2_test.log 2>&1 &

# Terminal 2: Monitorear logs
tail -f live_phase2_test.log | grep -E "Cache|Signal|Order|Error|P&L"
```

### Checklist Validación

```
VALIDACIÓN LIVE (24 horas):
[ ] Sin errores Python en logs
[ ] Cache HIT > 80% de ciclos
[ ] Señales se generan cada 5 segundos
[ ] Órdenes se ejecutan sin demoras
[ ] P&L actualizado correctamente
[ ] Sin memory leaks (memoria estable)

MONITOREO:
Watch:
  grep "Cache HIT" live_phase2_test.log | wc -l      # Hits
  grep "Cache MISS" live_phase2_test.log | wc -l     # Misses
  grep "ERROR" live_phase2_test.log | wc -l          # Errors
  grep "P&L" live_phase2_test.log | tail -5          # P&L actual
```

### Si Hay Problemas

**"Cache hit rate < 80%"**
```python
# Aumentar TTL o revisar si hay múltiples símbolos
cache = CachedDataProvider(cache_ttl_seconds=5)  # Aumentar de 3s a 5s
```

**"Señales lentas (> 500ms/ciclo)"**
```python
# Verificar que cache esté funcionando
# En logs: ✅ Cache HIT debe aparecer en >80% de ciclos
# Si veo ❌ Cache MISS frecuentemente, cache_ttl es demasiado corto
```

**"Errores MT5 connection"**
```python
# No es culpa de cache, es problema de MT5
# Continuar con benchmark cuando MT5 esté estable
```

---

## ⚡ DÍA 4: Benchmark & Validación

### Ejecutar Benchmark

```bash
cd descarga_datos
python v411_optimizations/cached_data_provider.py
```

### Salida Esperada

```
🚀 v4.11 Optimization 1: Caching
======================================================================

📊 Test 1: Cold Cache (First Call)
   Time: 50.5ms (expect ~50ms + overhead)

📊 Test 2: Hot Cache (Cached)
   Time: 6.2ms (expect ~6ms)
   Speedup: 8.1x

📊 Test 3: Multiple Symbols
   Cold: 151.3ms (3 symbols, first time)
   Hot:  18.9ms (3 symbols, cached)
   Speedup: 8.0x

📈 Cache Statistics:
   Hits: 6, Misses: 3, Hit Rate: 66.7%, Cached: 3/100
```

### Validación Métricas

```
✅ Cold call: ~50ms (puede ser 45-55ms)
✅ Hot call: <10ms (target 6ms)
✅ Speedup: ≥ 5x (target 8.3x)
✅ Hit rate: > 60% en primeras llamadas

RESULTADO: ✅ VALIDADO - Pasar a siguiente
```

---

## 💾 Commit y Merge

### Crear Commit

```bash
git add descarga_datos/core/mt5_live_data.py

git commit -m "OPTIM1: Caching implemented (8.3x speedup)

IMPLEMENTATION:
- Integrated CachedDataProvider in mt5_live_data.py
- Cache TTL: 3 seconds (1 cycle)
- Max symbols: 10
- Fallback: Direct MT5 call if cache miss

VALIDATION:
✓ CachedDataProvider tests: 5/5 passing
✓ Cache hit rate: >80% in live trading
✓ Benchmark: 50ms → 6ms (8.3x)
✓ Live trading: 24h error-free
✓ P&L: Identical to v4.10

PERFORMANCE:
  Before: 50ms API call per cycle
  After:  6ms cached lookup
  Improvement: 8.3x faster data retrieval

Next: PHASE 3 - Numba JIT Indicators"
```

### Actualizar Progress

```bash
python v411_checklist.py complete PHASE2 dia1_integracion
python v411_checklist.py complete PHASE2 dia2_tests
python v411_checklist.py complete PHASE2 dia3_live
python v411_checklist.py complete PHASE2 dia4_benchmark
python v411_checklist.py complete PHASE2 tasks_checklist
```

### Ver Progreso

```bash
python v411_checklist.py status
python v411_checklist.py phase PHASE2
```

---

## 📞 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| ModuleNotFoundError: cached_data_provider | Verificar sys.path en mt5_live_data.py línea 1-15 |
| Cache hit rate < 50% | Aumentar cache_ttl_seconds de 3s a 5s |
| "Cache miss" frecuentes | TTL muy corto, aumentar o check sync issues |
| Signals lentos (>500ms) | Cache no integrado correctamente, revisar get_live_data() |
| MT5 connection errors | No es problema de cache, revisar MT5 setup |
| Tests fallan | Ejecutar: pytest --tb=short para ver errores |
| Memory leak | Revisar que cache_max_size no sea demasiado grande |

---

## ✅ Checklist Final FASE 2

```
COMPLETITUD REQUERIDA:
[ ] CachedDataProvider integrado en mt5_live_data.py
[ ] Todos 5 tests pasan
[ ] Cache hit rate > 80% validado
[ ] Live trading 24h error-free
[ ] Benchmark valida 8.3x speedup
[ ] Commit exitoso con mensaje descriptivo
[ ] Progress tracker actualizado
[ ] Listo para FASE 3

MÉTRICAS FINALES:
✓ Cold call: 50ms
✓ Hot call: 6ms
✓ Speedup: 8.3x
✓ Win rate: 79.89% (same as v4.10)
✓ Trades: 7,896 (same as v4.10)
```

---

## 🎯 Próximo: FASE 3

Una vez completada FASE 2:

```bash
# 1. Leer guía FASE 3
cat ARCHIVOS\ MD/GUIA_IMPLEMENTACION_V411.md | grep -A 100 "FASE 3"

# 2. Instalar Numba
pip install numba

# 3. Empezar integración de indicadores
# Editar: indicators/technical_indicators.py
```

---

**FASE 2 Quick Start Guide**  
**Duration**: 4 días (5-8 Nov)  
**Target**: 8.3x speedup (50ms → 6ms)  
**Status**: ✅ READY TO START
