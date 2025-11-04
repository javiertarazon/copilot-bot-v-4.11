# 🚀 FASE 3: Numba JIT Implementation Starter

## Quick Integration Guide

### Paso 1: Instalar Numba (5 minutos)

```bash
pip install numba
python -c "import numba; print(f'Numba {numba.__version__} installed')"
```

### Paso 2: Warmup al Startup (5 minutos)

**Archivo**: `live_trading_orchestrator.py` (línea ~30)

```python
from v411_optimizations.numba_indicators import (
    calculate_ema_numba,
    calculate_rsi_numba,
    calculate_atr_numba,
    calculate_bb_numba,
    calculate_adx_numba,
    calculate_macd_numba,
    calculate_stochastic_numba,
    warmup_numba_cache
)

class LiveTradingOrchestrator:
    def __init__(self, config):
        logger.info("🔥 Warming up Numba JIT cache...")
        warmup_numba_cache()  # ← AGREGAR
        logger.info("✅ Numba cache ready")
        ...
```

### Paso 3: Reemplazar Indicadores (20 minutos)

**Archivo**: `strategies/ultra_detailed_heikin_ashi_ml_strategy.py`

**Antes (pandas)**:
```python
ema_12 = df['close'].ewm(span=12).mean()
rsi = ta.RSI(df['close'], 14)
atr = ta.ATR(df['high'], df['low'], df['close'], 14)
```

**Después (Numba)**:
```python
ema_12 = calculate_ema_numba(df['close'].values, 12)
rsi = calculate_rsi_numba(df['close'].values, 14)
atr = calculate_atr_numba(df['high'].values, df['low'].values, df['close'].values, 14)
```

Reemplazar estos indicadores en método `_calculate_indicators()`:
- [ ] EMA (todos los períodos)
- [ ] RSI (14)
- [ ] ATR (14)
- [ ] Bollinger Bands (20, 2.0)
- [ ] ADX (14)
- [ ] MACD (12, 26, 9)
- [ ] Stochastic (14, 3)

### Paso 4: Tests de Precisión (10 minutos)

```bash
pytest tests/test_v411_optimizations.py::TestNumbaIndicators -v
```

**Output esperado**:
```
test_ema_calculation PASSED          [ 20%]
test_rsi_calculation PASSED          [ 40%]
test_atr_calculation PASSED          [ 60%]
test_bollinger_bands PASSED          [ 80%]
test_numba_warmup PASSED             [100%]

====== 5 passed in 0.30s ======
```

### Paso 5: Live Validation (24 horas)

```bash
python main.py --live
```

**Validar en logs**:
- Sin errores de NaN o infinity
- Señales correctas (BUY/SELL/HOLD)
- Timing mejorado

### Paso 6: Benchmark (5 minutos)

```bash
python v411_optimizations/numba_indicators.py
```

**Output esperado**:
```
EMA Calculation (12-period, 200 bars)
   First call (compilation): 45.23ms
   Compiled (100 iterations):  0.32ms/call
   Expected speedup:           3-5x faster than pandas

RSI Calculation (14-period, 200 bars)
   Time: 0.28ms (3x faster than TA-Lib)

All Indicators (1 cycle simulation)
   Total time: 28.5ms
   Expected: ~30ms (vs 100ms without Numba)
   Speedup: 3.5x ✓
```

### Paso 7: Commit

```bash
git add -A
git commit -m "OPTIM2: Numba JIT Indicators (3.3x)

- 8 indicators converted to @jit(nopython=True)
- Warmup cache at startup
- Tests: precision validation passing
- Live trading 24h validated
- Benchmark: 100ms → 30ms (3.3x speedup)"
```

---

## ✅ FASE 3 Checklist

- [ ] Numba installed and verified
- [ ] Warmup function added to __init__
- [ ] 8 indicators replaced (EMA, SMA, RSI, ATR, BB, ADX, MACD, Stochastic)
- [ ] Tests: TestNumbaIndicators all pass
- [ ] Precision validation: tolerance < 1e-6
- [ ] Live trading 24h error-free
- [ ] No NaN or infinity in signals
- [ ] Benchmark validates 3.3x
- [ ] Commit made

---

**FASE 3 Starter Guide**
**Expected Duration**: 5 days
**Target**: 100ms → 30ms (3.3x)
**Status**: Ready to implement
