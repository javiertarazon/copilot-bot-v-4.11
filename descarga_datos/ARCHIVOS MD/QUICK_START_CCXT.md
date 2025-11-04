# ⚡ QUICK START - CCXTManager en 5 minutos

**Fecha:** 26 de Octubre de 2025  
**Tiempo Total:** 5 minutos  
**Status:** ✅ Ready Now

---

## 🎯 En 5 Pasos

### Paso 1: Verificar que existe (1 min)

```bash
# Terminal
ls -la descarga_datos/utils/ccxt_manager.py
ls -la descarga_datos/tests/test_ccxt_manager.py

# Esperado:
# -rw-r--r-- ... ccxt_manager.py (1200+ líneas)
# -rw-r--r-- ... test_ccxt_manager.py (300+ líneas)
```

### Paso 2: Ejecutar tests (1 min)

```bash
# Terminal
cd descarga_datos
python -m pytest tests/test_ccxt_manager.py -v

# Esperado:
# test_ccxt_manager.py::TestCCXTManagerInit::test_create_manager_basic PASSED
# ... 12 más ...
# ===================== 13 passed in 0.45s =====================
```

### Paso 3: Ver ejemplos (1 min)

```bash
# Terminal
head -50 utils/ccxt_manager_examples.py

# O ejecutar:
# python utils/ccxt_manager_examples.py
```

### Paso 4: Usar en tu código (2 min)

```python
# Ejemplo básico
from utils.ccxt_manager import create_ccxt_manager

manager = create_ccxt_manager(
    'binance',
    api_key='tu_key',
    api_secret='tu_secret',
    sandbox=True
)

# Auto-retry automático
ticker = manager.fetch_ticker('BTC/USDT')
print(f"BTC: ${ticker['last']}")

# Ver stats
manager.print_stats()
```

### Paso 5: Revisar logs (1 min)

```bash
# Terminal
tail -f logs/ccxt_manager.log

# Verás:
# [2025-10-26 10:30:00] INFO - ✅ CCXTManager initialized
# [2025-10-26 10:30:01] DEBUG - Fetching ticker...
# [2025-10-26 10:30:02] INFO - ✅ FetchTicker succeeded after 1 attempts
```

---

## ✅ HECHO EN 5 MINUTOS

- ✅ Tests pasados
- ✅ Ejemplos revisados
- ✅ Código funcionando
- ✅ Logs generados

---

## 🚀 PRÓXIMO PASO

Integración en ccxt_order_executor.py:

```python
# ANTES
class CCXTOrderExecutor:
    def __init__(self, config):
        self.exchange = ccxt.binance({...})

# DESPUÉS
class CCXTOrderExecutor:
    def __init__(self, config):
        from utils.ccxt_manager import create_ccxt_manager
        self.manager = create_ccxt_manager(
            'binance',
            config['apiKey'],
            config['secret'],
            sandbox=config.get('sandbox', False)
        )
```

---

## 📚 Para Más Información

- **Visión General:** `RESUMEN_IMPLEMENTACION_CCXT.md`
- **Integración Completa:** `INTEGRACION_CCXT_MANAGER.md`
- **Todos los Ejemplos:** `ccxt_manager_examples.py`
- **Índice de Navegación:** `INDICE_CCXT.md`

---

**¡Listo para comenzar!** ⚡
