# 🔌 GUÍA DE INTEGRACIÓN - CCXTManager en BotCopilot
## Cómo integrar Auto-Retry, Logging y Timeouts en código existente

**Documento:** INTEGRACION_CCXT_MANAGER.md  
**Fecha:** 26 de Octubre de 2025  
**Versión:** 1.0  
**Status:** ✅ Ready for Implementation

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General](#visión-general)
2. [Cambios en ccxt_order_executor.py](#cambios-en-ccxt_order_executor)
3. [Cambios en ccxt_live_data.py](#cambios-en-ccxt_live_data)
4. [Cambios en ccxt_live_trading_orchestrator.py](#cambios-en-orchestrator)
5. [Testing](#testing)
6. [Migración Gradual](#migración-gradual)

---

## 🎯 VISIÓN GENERAL

### Qué es CCXTManager

**CCXTManager** es un wrapper mejorado para CCXT que proporciona:

1. **Auto-Retry con Exponential Backoff**
   - Reintentos automáticos para errores transitorios
   - Backoff exponencial: 1s, 2s, 4s, etc.
   - Jitter para evitar thundering herd

2. **Logging Detallado**
   - Todos los requests/responses en logs/ccxt_manager.log
   - Timestamps, duración, estados
   - Conteo de errores y éxitos

3. **Timeout Configurable**
   - Global por exchange
   - Override por operación específica
   - Dinámico durante ejecución

### Beneficios para BotCopilot

| Antes | Después |
|-------|---------|
| ❌ Si hay rate limit, falla | ✅ Reintentar automáticamente con backoff |
| ❌ Si exchange está down, falla | ✅ Reintentar con espera exponencial |
| ❌ Sin logging de requests | ✅ Logging detallado en archivo |
| ❌ Timeout fijo | ✅ Timeout configurable por operación |
| ❌ Muchas excepciones en logs | ✅ Manejo robusto de errores |

---

## 🔧 CAMBIOS EN ccxt_order_executor.py

### Antes (Código Actual)

```python
# descarga_datos/core/ccxt_order_executor.py (actual)

class CCXTOrderExecutor:
    def __init__(self, exchange_config, logger):
        self.exchange = ccxt.binance({
            'apiKey': exchange_config['apiKey'],
            'secret': exchange_config['secret'],
            'sandbox': exchange_config.get('sandbox', False),
            'enableRateLimit': True
        })
        self.logger = logger
    
    def create_order(self, symbol, order_type, side, amount, price=None):
        try:
            order = self.exchange.create_order(
                symbol, order_type, side, amount, price
            )
            return order
        except Exception as e:
            self.logger.error(f"Order creation failed: {e}")
            return None
```

### Después (Con CCXTManager)

```python
# descarga_datos/core/ccxt_order_executor.py (mejorado)

from utils.ccxt_manager import create_ccxt_manager

class CCXTOrderExecutor:
    def __init__(self, exchange_config, logger):
        # Reemplazar exchange directo con CCXTManager
        self.manager = create_ccxt_manager(
            exchange_name='binance',
            api_key=exchange_config['apiKey'],
            api_secret=exchange_config['secret'],
            sandbox=exchange_config.get('sandbox', False),
            timeout_ms=30000,
            rate_limit_ms=400,
            verbose=False
        )
        self.logger = logger
    
    def create_order(self, symbol, order_type, side, amount, price=None, timeout_ms=None):
        # Auto-retry automático, logging automático
        client_order_id = f"bot_{int(time.time())}"
        
        order = self.manager.create_order(
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            client_order_id=client_order_id,
            timeout_override=timeout_ms  # 🆕 Timeout por operación
        )
        
        # Si falla, manager ya reintentó automáticamente
        if order:
            self.logger.info(f"✅ Order created: {order['id']}")
        else:
            self.logger.error(f"Order creation failed after retries")
        
        return order
    
    def cancel_order(self, order_id, symbol):
        # Auto-retry automático
        success = self.manager.cancel_order(order_id, symbol)
        return success
    
    def fetch_order(self, order_id, symbol):
        # Auto-retry automático
        order = self.manager.fetch_order(order_id, symbol)
        return order
    
    def get_exchange_stats(self):
        # 🆕 Obtener estadísticas de uso
        return self.manager.get_stats()
```

### Cambios Clave

1. ✅ Reemplazar `ccxt.binance()` con `create_ccxt_manager()`
2. ✅ Auto-retry transparente (sin código de retries)
3. ✅ Logging automático en `logs/ccxt_manager.log`
4. ✅ Timeout override por operación
5. ✅ Estadísticas disponibles

---

## 🔧 CAMBIOS EN ccxt_live_data.py

### Antes (Código Actual)

```python
# descarga_datos/core/ccxt_live_data.py (actual)

class CCXTLiveData:
    def __init__(self, exchange_config, logger):
        self.exchange = ccxt.binance({
            'apiKey': exchange_config['apiKey'],
            'secret': exchange_config['secret'],
            'sandbox': exchange_config.get('sandbox', False),
            'enableRateLimit': True
        })
    
    def fetch_ticker(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"Ticker fetch failed: {e}")
            return None
    
    def fetch_ohlcv(self, symbol, timeframe, limit):
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return candles
        except Exception as e:
            self.logger.error(f"OHLCV fetch failed: {e}")
            return None
```

### Después (Con CCXTManager)

```python
# descarga_datos/core/ccxt_live_data.py (mejorado)

from utils.ccxt_manager import create_ccxt_manager

class CCXTLiveData:
    def __init__(self, exchange_config, logger):
        # Usar CCXTManager
        self.manager = create_ccxt_manager(
            exchange_name='binance',
            api_key=exchange_config['apiKey'],
            api_secret=exchange_config['secret'],
            sandbox=exchange_config.get('sandbox', False),
            timeout_ms=30000,  # 🆕 Timeout para datos rápidos
            rate_limit_ms=400,
            verbose=False
        )
        self.logger = logger
    
    def fetch_ticker(self, symbol, timeout_ms=15000):
        # Auto-retry automático, con timeout override para tickers
        ticker = self.manager.fetch_ticker(
            symbol,
            timeout_override=timeout_ms  # 🆕 Tickers son rápidos
        )
        return ticker
    
    def fetch_ohlcv(self, symbol, timeframe, limit, timeout_ms=30000):
        # Auto-retry automático, con timeout override para OHLCV histórico
        candles = self.manager.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=limit,
            timeout_override=timeout_ms  # 🆕 OHLCV puede ser lento
        )
        return candles
    
    def fetch_balance(self):
        # Auto-retry automático
        balance = self.manager.fetch_balance()
        return balance
    
    def load_markets(self, force=False):
        # Auto-retry automático
        markets = self.manager.load_markets(force=force)
        return markets
```

### Cambios Clave

1. ✅ Reemplazar `ccxt.binance()` con `create_ccxt_manager()`
2. ✅ Auto-retry transparente en todos los fetch_* methods
3. ✅ Timeout override por operación (tickers rápidos vs OHLCV lento)
4. ✅ Logging automático sin código adicional
5. ✅ Manejo de errores robusto

---

## 🔧 CAMBIOS EN ccxt_live_trading_orchestrator.py

### Antes (Código Actual)

```python
# descarga_datos/core/ccxt_live_trading_orchestrator.py (actual)

class CCXTLiveOrchestratorXXX:
    def __init__(self, config):
        self.order_executor = CCXTOrderExecutor(config['exchanges']['binance'], logger)
        self.data_handler = CCXTLiveData(config['exchanges']['binance'], logger)
    
    async def run(self):
        while True:
            try:
                # Fetch datos
                ticker = self.data_handler.fetch_ticker('BTC/USDT')
                if not ticker:
                    self.logger.error("Failed to fetch ticker")
                    continue
                
                # Crear orden
                order = self.order_executor.create_order(...)
                if not order:
                    self.logger.error("Failed to create order")
                    continue
            
            except Exception as e:
                self.logger.error(f"Orchestrator error: {e}")
            
            await asyncio.sleep(60)
```

### Después (Con CCXTManager)

```python
# descarga_datos/core/ccxt_live_trading_orchestrator.py (mejorado)

class CCXTLiveOrchestratorXXX:
    def __init__(self, config):
        self.order_executor = CCXTOrderExecutor(config['exchanges']['binance'], logger)
        self.data_handler = CCXTLiveData(config['exchanges']['binance'], logger)
        self.last_stats_print = 0  # Para imprimir stats periódicamente
    
    async def run(self):
        while True:
            try:
                # Fetch datos (con auto-retry transparente)
                ticker = self.data_handler.fetch_ticker('BTC/USDT')
                if not ticker:
                    self.logger.error("Failed to fetch ticker (after retries)")
                    continue
                
                # Crear orden (con auto-retry transparente)
                order = self.order_executor.create_order(...)
                if not order:
                    self.logger.error("Failed to create order (after retries)")
                    continue
                
                # 🆕 Imprimir estadísticas cada 10 minutos
                now = time.time()
                if now - self.last_stats_print > 600:  # 10 minutos
                    stats = self.order_executor.get_exchange_stats()
                    self.logger.info(f"📊 CCXT Stats: {stats}")
                    self.last_stats_print = now
            
            except Exception as e:
                self.logger.error(f"Orchestrator error: {e}")
            
            await asyncio.sleep(60)
```

### Cambios Clave

1. ✅ Auto-retry transparente en orchestrator
2. ✅ Logging automático de operaciones
3. ✅ 🆕 Imprimir estadísticas periódicamente
4. ✅ Mejor error handling (errores ya reintentados)
5. ✅ Código más limpio (sin bloques try/except adicionales)

---

## 🧪 TESTING

### 1. Verificar CCXTManager funciona

```bash
# Terminal
cd descarga_datos

# Run tests
python -m pytest tests/test_ccxt_manager.py -v

# Expected output:
# test_ccxt_manager.py::TestCCXTManagerInit::test_create_manager_basic PASSED
# test_ccxt_manager.py::TestCCXTManagerTimeout::test_set_timeout PASSED
# etc.
```

### 2. Verificar logging funciona

```bash
# Ver logs generados
tail -f logs/ccxt_manager.log

# Expected output:
# [2025-10-26 10:30:00] INFO - ✅ CCXTManager initialized for binance
# [2025-10-26 10:30:01] DEBUG - Fetching ticker for BTC/USDT...
# [2025-10-26 10:30:01] DEBUG - ✅ Ticker BTC/USDT: $40000.00
# [2025-10-26 10:30:05] WARNING - ⚠️  FetchTicker - Retry 1/3 (waiting 1.23s): DDoSProtection
# [2025-10-26 10:30:06] INFO - ✅ FetchTicker succeeded after 2 attempts
```

### 3. Verificar timeout funciona

```bash
# En código de prueba
manager.set_timeout(10000)  # 10 segundos
result = manager.fetch_ohlcv('BTC/USDT', '1h', limit=1000)

# Si tarda más de 10s:
# [2025-10-26 10:30:01] ERROR - ❌ FetchOHLCV - Timeout after 10000ms
```

### 4. Prueba de integración manual

```bash
# Terminal 1: Crear archivo de prueba
cat > test_integration.py << 'EOF'
from utils.ccxt_manager import create_ccxt_manager
import os
from dotenv import load_dotenv

load_dotenv()
manager = create_ccxt_manager(
    'binance',
    os.getenv('BINANCE_API_KEY'),
    os.getenv('BINANCE_API_SECRET'),
    sandbox=True
)

# Test 1: Fetch ticker
print("Test 1: Fetch ticker...")
ticker = manager.fetch_ticker('BTC/USDT')
print(f"✅ BTC: ${ticker['last']:.2f}" if ticker else "❌ Failed")

# Test 2: Fetch OHLCV
print("\nTest 2: Fetch OHLCV...")
candles = manager.fetch_ohlcv('BTC/USDT', '1h', limit=10)
print(f"✅ {len(candles)} candles" if candles else "❌ Failed")

# Test 3: Ver stats
print("\nTest 3: Stats...")
manager.print_stats()
EOF

# Terminal 2: Ejecutar prueba
python test_integration.py
```

---

## 📊 MIGRACIÓN GRADUAL

### Fase 1: Preparación (Día 1)
```
1. Crear CCXTManager (✅ Ya hecho)
2. Crear tests (✅ Ya hecho)
3. Crear documentación (✅ Ya hecho)
4. Revisar código actual
5. Planificar cambios
```

### Fase 2: Integración en ccxt_order_executor.py (Día 2)
```
1. Reemplazar __init__ con CCXTManager
2. Reemplazar create_order()
3. Reemplazar cancel_order()
4. Reemplazar fetch_order()
5. Agregar get_exchange_stats()
6. Testing local
7. Merge a main
```

### Fase 3: Integración en ccxt_live_data.py (Día 3)
```
1. Reemplazar __init__ con CCXTManager
2. Reemplazar fetch_ticker()
3. Reemplazar fetch_ohlcv()
4. Agregar timeout overrides
5. Testing local
6. Merge a main
```

### Fase 4: Integración en orchestrator (Día 4)
```
1. Agregar stats printing
2. Mejorar error handling
3. Testing completo
4. Merge a main
```

### Fase 5: Validación en Sandbox (Día 5)
```
1. Ejecutar python main.py --live (sandbox=true)
2. Monitorear logs/ccxt_manager.log
3. Verificar auto-retry funciona
4. Verificar logging completo
5. Verificar timeouts funcionan
6. Decision: Go/No-Go para producción
```

---

## 📈 BENEFICIOS ESPERADOS

### Estabilidad
- ✅ Reducción de errores transitorios (DDoS, rate limit)
- ✅ Auto-recovery sin intervención manual
- ✅ Mejor handling de "exchange down"

### Confiabilidad
- ✅ Logging detallado de todas las operaciones
- ✅ Trazabilidad completa de requests
- ✅ Fácil debugging de issues

### Performance
- ✅ Timeout optimizado por tipo de operación
- ✅ Rate limit configurable
- ✅ Menos retries manuales en orchestrator

### Mantenibilidad
- ✅ Código más limpio (sin try/except anidados)
- ✅ Mejor separación de concerns
- ✅ Reutilizable en otros componentes

---

## ✅ CHECKLIST ANTES DE INTEGRAR

- [ ] Leer `ccxt_manager.py` completamente
- [ ] Revisar `ccxt_manager_examples.py`
- [ ] Ejecutar `test_ccxt_manager.py`
- [ ] Revisar esto documento completamente
- [ ] Planificar orden de cambios
- [ ] Hacer backup de archivos actuales
- [ ] Integrar Phase 1 (ccxt_order_executor)
- [ ] Integrar Phase 2 (ccxt_live_data)
- [ ] Integrar Phase 3 (orchestrator)
- [ ] Testing completo en sandbox
- [ ] Validar logs generados
- [ ] Deploy a producción

---

## 🚀 PRÓXIMOS PASOS

1. **Hoy:** Revisar documentación
2. **Mañana:** Integración Phase 1
3. **Pasado:** Testing y validación
4. **Semana:** Deploy a sandbox
5. **2 semanas:** Producción

---

**Documento:** INTEGRACION_CCXT_MANAGER.md  
**Estado:** ✅ Ready for Implementation  
**Reviewed:** 26/10/2025  
**Approved:** Pending Review

**Próxima Acción:** Integrar CCXTManager en ccxt_order_executor.py
