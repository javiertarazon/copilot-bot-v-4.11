# 🚀 FASE 2: Caching Implementation Starter

## Quick Integration Guide

### Paso 1: Integración Básica (15 minutos)

**Archivo**: `core/mt5_live_data.py`

Agregar al inicio del archivo:
```python
from v411_optimizations.cached_data_provider import CachedDataProvider
```

En la clase `MT5DataProvider` (alrededor de línea 50):
```python
class MT5DataProvider:
    def __init__(self):
        self.mt5 = mt5
        self.cache = CachedDataProvider(cache_ttl_seconds=3)  # ← AGREGAR
        logger.info("✅ MT5DataProvider initialized with cache")
    
    def get_live_data(self, symbol, timeframe, count=200):
        """Get live data with caching."""
        # Antes: return self._fetch_from_mt5(symbol, timeframe, count)
        # Después:
        return self.cache.get_bars(
            symbol,
            timeframe,
            count,
            fetch_func=self._fetch_from_mt5
        )
    
    def _fetch_from_mt5(self, symbol, timeframe, count):
        """Original MT5 fetch (sin cache)."""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                logger.error(f"MT5 fetch failed: {symbol}")
                return None
            return pd.DataFrame(rates)
        except Exception as e:
            logger.error(f"MT5 exception: {e}")
            return None
```

### Paso 2: Validar Tests (5 minutos)

```bash
cd descarga_datos
pytest tests/test_v411_optimizations.py::TestCachedDataProvider -v
```

**Output esperado**:
```
test_cache_hit PASSED                                    [ 20%]
test_cache_miss_after_ttl PASSED                         [ 40%]
test_cache_invalidation PASSED                           [ 60%]
test_cache_hit_rate PASSED                               [ 80%]
test_multiple_symbols PASSED                             [100%]

====== 5 passed in 0.45s ======
```

### Paso 3: Live Trading Validation (24 horas)

```bash
python main.py --live
```

**Monitorear en logs**:
```
✅ Cache HIT: EURUSD_16408 (age=0.5s)
✅ Cache HIT: EURUSD_16408 (age=1.2s)
📦 Cached: GBPUSD_16408 (200 bars)
✅ Cache HIT: GBPUSD_16408 (age=0.8s)
```

### Paso 4: Benchmark (5 minutos)

```bash
python v411_optimizations/cached_data_provider.py
```

**Output esperado**:
```
Test 1: Cold Cache
   Time: 52.3ms (expect ~50ms + overhead)

Test 2: Hot Cache (Cached)
   Time: 6.2ms (expect ~6ms)
   Speedup: 8.4x ✓

Test 3: Multiple Symbols
   Cold: 156.8ms (3 symbols, first time)
   Hot:  18.6ms (3 symbols, cached)
   Speedup: 8.4x ✓

Cache Statistics:
   Hits: 3, Misses: 3, Hit Rate: 50.0%
```

### Paso 5: Commit

```bash
git add -A
git commit -m "OPTIM1: Caching Layer Integrated (8.3x)

- CachedDataProvider in core/mt5_live_data.py
- 5 tests passing (100% hit rate)
- Live trading 24h validated
- Benchmark: 50ms → 6ms (8.3x speedup)"
```

---

## ✅ FASE 2 Checklist

- [ ] CachedDataProvider imported in mt5_live_data.py
- [ ] __init__ has self.cache = CachedDataProvider()
- [ ] get_live_data() uses cache.get_bars()
- [ ] _fetch_from_mt5() is fetch_func
- [ ] Tests: TestCachedDataProvider all pass
- [ ] Live trading 24h error-free
- [ ] Cache hit rate > 80% in logs
- [ ] Benchmark validates 8.3x
- [ ] Commit made with message
- [ ] git log shows new commit

---

**FASE 2 Starter Guide**
**Expected Duration**: 4 days
**Target**: 50ms → 6ms (8.3x)
**Status**: Ready to implement
