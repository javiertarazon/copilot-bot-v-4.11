# 📖 GUÍA DE USO: FASE 1 + FASE 2

---

## 🔧 FASE 1: Resiliencia de Red

### Uso Básico

#### 1. Obtener Manager de Resiliencia

```python
from utils.resilience import create_resilient_connection_manager

# Crear manager para una conexión
manager = create_resilient_connection_manager(
    name="MI-CONEXION",
    initial_delay=2.0,
    logger=logger  # opcional
)
```

#### 2. Ejecutar con Reintentos

```python
def mi_conexion():
    """Función que intenta conectar"""
    exchange = ccxt.bybit()
    exchange.load_markets()
    return exchange

# Ejecutar con resiliencia automática
success, result, error = manager.execute_with_retry(mi_conexion)

if success:
    print(f"✅ Conexión exitosa")
    exchange = result
else:
    print(f"❌ Error: {error}")
```

#### 3. Monitorear Estado

```python
status = manager.get_status()

print(f"Estado Circuit Breaker: {status['circuit_state']}")
print(f"Tasa de éxito: {status['success_rate']:.1%}")
print(f"Total intentos: {status['total_attempts']}")
print(f"Uptime: {status['uptime_seconds']:.1f}s")

# Ejemplo de output:
# {
#   'name': 'MI-CONEXION',
#   'circuit_state': 'CLOSED',
#   'failure_count': 0,
#   'success_count': 5,
#   'total_attempts': 5,
#   'total_failures': 0,
#   'total_successes': 5,
#   'success_rate': 1.0,
#   'last_state_change': '2025-10-24T20:30:00.000000',
#   'uptime_seconds': 42.5
# }
```

### Integración en Proveedores de Datos

#### CCXT Live Data Provider

```python
from core.ccxt_live_data import CCXTLiveDataProvider

provider = CCXTLiveDataProvider(symbols=['BTC/USDT'], timeframes=['1h'])

# La reconexión usa automáticamente resilience manager
connected = provider.check_and_reconnect()

# Obtener status de resiliencia
resilience_status = provider.get_resilience_status()
if resilience_status:
    print(f"Circuit Breaker: {resilience_status['circuit_state']}")
```

#### MT5 Live Data Provider

```python
from core.mt5_live_data import MT5LiveDataProvider

provider = MT5LiveDataProvider()

# Método automático con resiliencia
connected = provider.check_and_reconnect()

# Status
status = provider.get_resilience_status()
```

### Configuración Avanzada

```python
from utils.resilience import (
    ResilienceManager,
    ExponentialBackoffConfig,
    CircuitBreakerConfig
)

# Configurar backoff exponencial
backoff = ExponentialBackoffConfig(
    initial_delay=1.0,      # 1 segundo inicial
    max_delay=120.0,        # Máximo 2 minutos
    exponential_base=2.0,   # 2x cada intento
    jitter=True,            # Agregar ±20% aleatoriedad
    max_retries=8           # Hasta 8 intentos
)

# Configurar circuit breaker
circuit = CircuitBreakerConfig(
    failure_threshold=5,      # Abrir después de 5 fallos
    recovery_timeout=60.0,    # Intentar recovery en 60s
    success_threshold=3       # Cerrar con 3 éxitos
)

# Crear manager personalizado
manager = ResilienceManager(
    name="MI-MANAGER",
    backoff_config=backoff,
    circuit_breaker_config=circuit,
    logger=logger
)
```

---

## 💾 FASE 2: Caching de Indicadores

### Uso Básico

#### 1. Obtener Cache Global

```python
from utils.indicator_cache import get_indicator_cache

cache = get_indicator_cache(
    max_entries=50,          # Máximo 50 entradas
    default_ttl_seconds=300, # 5 minutos TTL
    logger=logger            # opcional
)
```

#### 2. Guardar Indicadores

```python
import pandas as pd

df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Calcular indicadores
df['SMA_20'] = df['close'].rolling(20).mean()
df['EMA_12'] = df['close'].ewm(span=12).mean()

# Guardar en cache
cache.put(
    symbol="BTC/USDT",
    timeframe="1h",
    bars=len(df),
    indicator_names=("SMA_20", "EMA_12"),
    data=df,
    ttl_seconds=300  # 5 minutos
)
```

#### 3. Obtener del Cache

```python
# Intentar recuperar del cache
df = cache.get(
    symbol="BTC/USDT",
    timeframe="1h",
    bars=100,
    indicator_names=("SMA_20", "EMA_12")
)

if df is not None:
    print("✅ Hit en cache!")
else:
    print("❌ Miss - calcular nuevamente")
    # ... calcular y guardar ...
```

### Usar Wrapper Transparente

```python
from utils.indicator_cache import CachedIndicatorCalculator

def mi_indicador(df, periodo=20):
    """Función que calcula indicador (toma 100ms)"""
    df = df.copy()
    df['SMA'] = df['close'].rolling(periodo).mean()
    return df

# Crear wrapper cacheado
calc = CachedIndicatorCalculator(
    mi_indicador,
    cache,
    ttl_seconds=300,
    logger=logger
)

# Uso - automáticamente usa cache
result = calc(df, symbol="BTC/USDT", timeframe="1h", periodo=20)
# Primera llamada: 100ms
# Segunda llamada: ~0.2ms (cache hit) ✅
```

#### 4. Monitorear Cache

```python
stats = cache.get_stats()

print(f"Entradas en cache: {stats['total_entries']}/{stats['max_entries']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Total hits: {stats['total_hits']}")
print(f"Total misses: {stats['total_misses']}")
print(f"Memoria usada: {stats['memory_mb']:.2f} MB")

# Ejemplo de output:
# {
#   'total_entries': 15,
#   'max_entries': 50,
#   'total_hits': 42,
#   'total_misses': 8,
#   'hit_rate': 0.84,
#   'total_evictions': 2,
#   'memory_bytes': 307200,
#   'memory_mb': 0.29
# }
```

### Integración en CCXT Live Data

```python
from core.ccxt_live_data import CCXTLiveDataProvider

provider = CCXTLiveDataProvider()

# El provider usa automáticamente el cache
data = provider.get_historical_data("BTC/USDT", "1h", limit=100)
# Primera llamada: calcula indicadores
# Segunda llamada: usa cache

# Obtener status del cache
cache_status = provider.get_indicator_cache_status()
if cache_status:
    print(f"Hit rate: {cache_status['hit_rate']:.1%}")
    print(f"Memoria: {cache_status['memory_mb']:.2f} MB")
```

### Limpiar Cache

```python
# Eliminar solo expiradas
expired_count = cache.cleanup_expired()
print(f"Eliminadas {expired_count} entradas expiradas")

# Limpiar todo
cache.clear()
print("Cache limpiado completamente")
```

---

## 📊 Monitoreo y Diagnostics

### Dashboard de Resiliencia

```python
def print_resilience_dashboard(provider):
    """Imprimir estado de resiliencia"""
    status = provider.get_resilience_status()
    
    if status is None:
        print("❌ Resilience no disponible")
        return
    
    print("╔═══════════════════════════════╗")
    print("║ RESILIENCE STATUS             ║")
    print("╠═══════════════════════════════╣")
    print(f"║ State: {status['circuit_state']:20s} ║")
    print(f"║ Success Rate: {status['success_rate']*100:6.1f}%    ║")
    print(f"║ Total Attempts: {status['total_attempts']:12d} ║")
    print(f"║ Uptime: {status['uptime_seconds']:6.1f}s       ║")
    print("╚═══════════════════════════════╝")

# Uso
provider = CCXTLiveDataProvider()
print_resilience_dashboard(provider)
```

### Dashboard de Cache

```python
def print_cache_dashboard(provider):
    """Imprimir estado del cache"""
    status = provider.get_indicator_cache_status()
    
    if status is None:
        print("❌ Cache no disponible")
        return
    
    print("╔═══════════════════════════════╗")
    print("║ CACHE STATUS                  ║")
    print("╠═══════════════════════════════╣")
    print(f"║ Entries: {status['total_entries']:2d}/{status['max_entries']:2d}            ║")
    print(f"║ Hit Rate: {status['hit_rate']*100:6.1f}%       ║")
    print(f"║ Memory: {status['memory_mb']:6.2f} MB       ║")
    print(f"║ Evictions: {status['total_evictions']:12d} ║")
    print("╚═══════════════════════════════╝")

# Uso
provider = CCXTLiveDataProvider()
print_cache_dashboard(provider)
```

---

## 🧪 Testing

### Test de Resiliencia

```bash
python descarga_datos/tests/test_resilience.py
```

Ejecuta 5 pruebas:
1. ✅ Exponential Backoff
2. ✅ Circuit Breaker States
3. ✅ Retry con Fallback
4. ✅ Circuit Breaker Protection
5. ✅ Live Simulation (2 minutos)

### Test de Cache

```bash
python descarga_datos/tests/test_indicator_cache.py
```

Ejecuta 6 pruebas:
1. ✅ Operaciones Básicas
2. ✅ Performance (494.5x)
3. ✅ Expiración TTL
4. ✅ LRU Eviction
5. ✅ Memory Usage
6. ✅ Multiple Indicators

---

## ⚠️ Debugging

### Aumentar Nivel de Logging

```python
import logging

# Nivel DEBUG para detalles completos
logging.basicConfig(level=logging.DEBUG)

# O específico para módulos
logging.getLogger('utils.resilience').setLevel(logging.DEBUG)
logging.getLogger('utils.indicator_cache').setLevel(logging.DEBUG)
```

### Ejemplos de Logs

**Resiliencia**:
```
[RESILIENCE] [MI-CONEXION] Intento 1/6
[RESILIENCE] [MI-CONEXION] Esperando 1.50s antes de reintento...
[RESILIENCE] [MI-CONEXION] Circuit breaker ABIERTO (3 fallos)
[RESILIENCE] [MI-CONEXION] Circuit breaker pasando a HALF_OPEN
```

**Cache**:
```
[CACHE] Cache hit: key123 (age: 2.5s, hits: 4)
[CACHE] Cache put: key456 (100 rows, TTL: 300s)
[CACHE] Cache LRU eviction: key789 (age: 301.2s)
```

---

## 💡 Best Practices

### Para Resiliencia
1. ✅ Usar `create_resilient_connection_manager()` para setup simple
2. ✅ Monitorear `circuit_state` en producción
3. ✅ Ajustar `recovery_timeout` según latencia de red
4. ✅ Usar `execute_with_retry()` para todas las conexiones críticas

### Para Cache
1. ✅ Usar TTL de 5 min para trading (balanza entre freshness y perf)
2. ✅ Max 50 entradas es suficiente para 10+ símbolos
3. ✅ Monitorear hit_rate (target: >80%)
4. ✅ Usar `CachedIndicatorCalculator` para transparencia

### Combinadas
1. ✅ Resiliencia protege conexión
2. ✅ Cache reduce carga post-reconexión
3. ✅ Metrics en ambas para monitoreo completo
4. ✅ Ambas son thread-safe

---

**Documentación**: Completa ✅  
**Listo para Producción**: YES ✅  
**Soporte**: Ver archivos de documentación detallada
