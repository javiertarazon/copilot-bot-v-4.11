# 🔐 CCXT BEST PRACTICES PARA TRADING EN VIVO
## Guía de Seguridad, Optimización y Escalabilidad

**Documento:** `CCXT_BEST_PRACTICES_LIVE_TRADING.md`  
**Versión:** 1.0  
**Aplicable a:** BotCopilot v2.0 y futuros  
**Clasificación:** Proyecto Privado

---

## 📋 TABLA DE CONTENIDOS

1. [Configuración Segura](#configuración-segura)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Order Management](#order-management)
5. [Data Integrity](#data-integrity)
6. [Performance](#performance)
7. [Monitoring](#monitoring)
8. [Checklist Pre-Producción](#checklist-pre-producción)

---

## 🔐 CONFIGURACIÓN SEGURA

### Initialización Correcta

```python
import ccxt
from pathlib import Path
import json

# ✅ CORRECTO: Una sola instancia, reutilizable
class ExchangeManager:
    def __init__(self, exchange_id, config_file):
        self.exchange_id = exchange_id
        self.config = self._load_config(config_file)
        self.exchange = self._init_exchange()
        self.markets_loaded = False
    
    def _load_config(self, config_file):
        """Cargar credenciales desde config file seguro"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validar credenciales no están vacías
        if not config.get('apiKey') or not config.get('secret'):
            raise ValueError("API credentials missing in config")
        
        return config
    
    def _init_exchange(self):
        """Inicializar exchange con settings seguras"""
        exchange = ccxt.__dict__[self.exchange_id]({
            'apiKey': self.config['apiKey'],
            'secret': self.config['secret'],
            'uid': self.config.get('uid'),  # Si es necesario
            'password': self.config.get('password'),
            
            # Rate limiting
            'enableRateLimit': True,
            'rateLimit': 500,  # 500ms entre requests
            
            # Timeouts
            'timeout': 30000,  # 30 segundos default
            
            # Sandbox
            'sandbox': self.config.get('sandbox', True),
            
            # Verbose logging (solo desarrollo)
            'verbose': self.config.get('verbose', False)
        })
        
        return exchange
    
    def load_markets(self):
        """Cargar markets una sola vez"""
        if not self.markets_loaded:
            self.exchange.load_markets()
            self.markets_loaded = True
        return self.exchange.symbols

# Uso
manager = ExchangeManager('binance', 'config.json')
symbols = manager.load_markets()  # Cargar una vez
```

### Credenciales Seguras

```python
# ❌ INSEGURO: Credenciales hardcodeadas
exchange = ccxt.binance({
    'apiKey': 'your_key_12345',
    'secret': 'your_secret_abcde'
})

# ✅ SEGURO: Variables de entorno
import os

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'uid': os.getenv('BINANCE_UID'),  # Si existe
    'password': os.getenv('BINANCE_PASSWORD')
})

# ✅ SEGURO: Archivo .env (no versionado)
from dotenv import load_dotenv

load_dotenv('.env')  # Cargar .env (NUNCA en git)
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET')
})

# .env (archivo)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_SANDBOX=true
```

### Permisos de API Recomendados

```
✅ PERMISOS RECOMENDADOS:
  ├─ Spot Trading: Habilitado
  ├─ Futures Trading: Habilitado (si usas)
  ├─ Margin Trading: Deshabilitado (opcional)
  ├─ Reading: Habilitado
  ├─ Withdrawing: Deshabilitado (CRÍTICO)
  ├─ IP Whitelist: Tu IP de servidor
  └─ Device Binding: Habilitado

❌ NUNCA HABILITAR:
  ├─ Withdraw (retiros)
  ├─ Transfer (transferencias entre accounts)
  └─ Sin IP whitelist
```

---

## ⚠️ ERROR HANDLING

### Errores CCXT Comunes

```python
import ccxt

# Estructura de errores CCXT
class CCXTErrorHandler:
    """Manejar todos los tipos de error de CCXT"""
    
    def safe_fetch_ticker(self, exchange, symbol):
        """Fetch ticker con manejo de errores"""
        try:
            ticker = exchange.fetch_ticker(symbol)
            return ticker
        
        except ccxt.DDoSProtection as e:
            # Exchange bajo DDoS o rate limit
            self.logger.warning(f"DDoS Protection: {e}")
            return None  # Retry después
        
        except ccxt.ExchangeNotAvailable as e:
            # Exchange offline o en mantenimiento
            self.logger.error(f"Exchange unavailable: {e}")
            return None  # Retry después
        
        except ccxt.ExchangeError as e:
            # Error general del exchange
            self.logger.error(f"Exchange error: {e}")
            return None
        
        except ccxt.NetworkError as e:
            # Problema de conectividad
            self.logger.error(f"Network error: {e}")
            return None
        
        except ccxt.InvalidNonce as e:
            # Nonce inválido (reloj desincronizado)
            self.logger.error(f"Invalid nonce: {e}")
            return None
        
        except Exception as e:
            # Error inesperado
            self.logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            return None
    
    def safe_create_order(self, exchange, symbol, order_type, side, amount, price=None):
        """Crear orden con manejo robusto de errores"""
        try:
            order = exchange.create_order(
                symbol, order_type, side, amount, price,
                params={'clientOrderId': f'order_{int(time.time())}'}
            )
            self.logger.info(f"Order created: {order['id']}")
            return order
        
        except ccxt.InsufficientFunds:
            self.logger.error(f"Insufficient balance for {symbol}")
            return None
        
        except ccxt.InvalidOrder as e:
            # Precio, cantidad, etc inválida
            self.logger.error(f"Invalid order: {e}")
            return None
        
        except ccxt.OrderNotFound:
            # Orden no encontrada (ya cancelada?)
            self.logger.error(f"Order not found")
            return None
        
        except ccxt.ExchangeNotAvailable:
            self.logger.error("Exchange not available, retry")
            return None
        
        except ccxt.RateLimitExceeded:
            self.logger.warning("Rate limit exceeded, back off")
            return None
        
        except Exception as e:
            self.logger.error(f"Order creation failed: {e}")
            return None
```

### Retry Logic con Exponential Backoff

```python
import time
import random
from typing import Callable, Any, Optional

def with_retry(
    func: Callable,
    max_retries: int = 3,
    base_wait: float = 1.0,
    backoff_factor: float = 2.0,
    logger = None
) -> Optional[Any]:
    """
    Ejecutar función con retry automático y backoff exponencial
    
    Args:
        func: Función a ejecutar
        max_retries: Máximo de reintentos
        base_wait: Espera inicial en segundos
        backoff_factor: Multiplicador de espera
        logger: Logger para logs
    
    Returns:
        Resultado de función o None si fallan todos los reintentos
    """
    
    for attempt in range(max_retries):
        try:
            return func()
        
        except (ccxt.DDoSProtection, ccxt.ExchangeNotAvailable, ccxt.RateLimitExceeded) as e:
            if attempt == max_retries - 1:
                if logger:
                    logger.error(f"Max retries exceeded: {e}")
                raise  # Lanzar en último intento
            
            wait_time = base_wait * (backoff_factor ** attempt) + random.uniform(0, 1)
            if logger:
                logger.warning(f"Retry {attempt + 1}/{max_retries}, waiting {wait_time:.2f}s: {e}")
            
            time.sleep(wait_time)
        
        except (ccxt.InvalidNonce, ccxt.AuthenticationError, ccxt.PermissionDenied) as e:
            # Errores irrecuperables
            if logger:
                logger.error(f"Unrecoverable error: {e}")
            raise
        
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            raise
    
    return None

# Uso
def fetch_ticker_safe():
    return exchange.fetch_ticker('BTC/USDT')

ticker = with_retry(fetch_ticker_safe, max_retries=3, logger=logger)
```

---

## ⏱️ RATE LIMITING

### Rate Limiter Automático

```python
# ✅ HABILITADO AUTOMÁTICO (CCXT 4.5+)
exchange = ccxt.binance({
    'enableRateLimit': True,
    'rateLimit': 400  # 400ms entre requests
})

# La siguiente llamada ESPERA automáticamente si es necesario
ticker1 = exchange.fetch_ticker('BTC/USDT')
ticker2 = exchange.fetch_ticker('ETH/USDT')  # Espera 400ms si es necesario
# Total: ~800ms si se hace secuencialmente
```

### Rate Limit Manual (Si deshabilitado)

```python
import time
from collections import deque

class RateLimiter:
    """Manual rate limiter si lo necesitas"""
    
    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait(self):
        """Esperar si es necesario antes de siguiente request"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

limiter = RateLimiter(requests_per_second=2.0)

while True:
    limiter.wait()  # Esperar si es necesario
    ticker = exchange.fetch_ticker('BTC/USDT')
```

### Límites Binance

```python
# BINANCE RATE LIMITS:
# ├─ Spot: 1200 weight/minute
# ├─ Futures: 2400 weight/minute
# ├─ Fetch ticker: ~1 weight
# ├─ Create order: ~1 weight
# ├─ Fetch order: ~1 weight
# ├─ Fetch balance: ~1 weight
# └─ Fetch OHLCV: ~1 weight

# CÁLCULO WEIGHT:
# - 100 fetch_ticker/min = 100 weight = OK (1200 disponible)
# - 1200 create_order/min = 1200 weight = MAX
# - 1000 fetch_orders/min = 1000 weight = OK

# CONSEJO: Siempre deja margen (80% max)
```

---

## 📦 ORDER MANAGEMENT

### Creación Segura de Órdenes

```python
def create_order_safe(
    exchange,
    symbol: str,
    order_type: str,
    side: str,
    amount: float,
    price: float = None,
    client_order_id: str = None,
    logger = None
) -> dict or None:
    """
    Crear orden con validaciones y manejo de errores
    
    Args:
        exchange: CCXT exchange instance
        symbol: Símbolo (BTC/USDT, ETH/USDT, etc)
        order_type: 'limit' o 'market'
        side: 'buy' o 'sell'
        amount: Cantidad en base currency
        price: Precio (requerido para limit)
        client_order_id: ID único para rastrear
        logger: Logger instance
    
    Returns:
        Order dict or None if failed
    """
    
    try:
        # 1. Validar markets cargados
        if not hasattr(exchange, 'markets') or not exchange.markets:
            exchange.load_markets()
        
        # 2. Validar símbolo existe
        if symbol not in exchange.symbols:
            if logger:
                logger.error(f"Symbol {symbol} not in {exchange.id}")
            return None
        
        # 3. Obtener mercado
        market = exchange.market(symbol)
        
        # 4. Validar y ajustar cantidad
        limits = market['limits']['amount']
        if amount < limits['min']:
            if logger:
                logger.warning(f"Amount {amount} < min {limits['min']}, using min")
            amount = limits['min']
        if amount > limits['max']:
            if logger:
                logger.warning(f"Amount {amount} > max {limits['max']}, using max")
            amount = limits['max']
        
        # 5. Validar precio (si limit order)
        if order_type == 'limit' and price is None:
            if logger:
                logger.error("Price required for limit orders")
            return None
        
        if price is not None:
            price_limits = market['limits']['price']
            if price < price_limits['min']:
                if logger:
                    logger.warning(f"Price {price} < min {price_limits['min']}")
                price = price_limits['min']
            if price > price_limits['max']:
                if logger:
                    logger.warning(f"Price {price} > max {price_limits['max']}")
                price = price_limits['max']
        
        # 6. Validar cost (amount * price)
        if price is not None:
            cost = amount * price
            cost_limits = market['limits']['cost']
            if cost < cost_limits['min']:
                if logger:
                    logger.warning(f"Cost {cost} < min {cost_limits['min']}")
                return None
        
        # 7. Crear orden con ID único
        params = {}
        if client_order_id:
            params['clientOrderId'] = client_order_id
        
        order = exchange.create_order(
            symbol, order_type, side, amount, price, params
        )
        
        if logger:
            logger.info(f"Order created: {order['id']} ({side} {amount} {symbol})")
        
        return order
    
    except ccxt.InsufficientFunds:
        if logger:
            logger.error(f"Insufficient balance for {symbol}")
        return None
    
    except ccxt.InvalidOrder as e:
        if logger:
            logger.error(f"Invalid order: {e}")
        return None
    
    except Exception as e:
        if logger:
            logger.error(f"Order creation failed: {type(e).__name__}: {e}")
        return None

# Uso
order = create_order_safe(
    exchange,
    'BTC/USDT',
    'limit',
    'buy',
    0.01,
    40000.0,
    client_order_id='my_order_123',
    logger=logger
)
```

### Verificar Orden Antes de Cancelar

```python
def cancel_order_safe(
    exchange,
    order_id: str,
    symbol: str = None,
    logger = None
) -> bool:
    """
    Cancelar orden verificando primero que existe
    
    Args:
        exchange: CCXT exchange instance
        order_id: ID de orden a cancelar
        symbol: Símbolo (requerido en algunas exchanges)
        logger: Logger instance
    
    Returns:
        True si cancelada, False si no
    """
    
    try:
        # 1. Verificar orden existe y está open
        if symbol is None:
            # Si no tenemos símbolo, hay que buscarlo
            orders = exchange.fetch_open_orders()
            order = next((o for o in orders if o['id'] == order_id), None)
        else:
            order = exchange.fetch_order(order_id, symbol)
        
        if order is None:
            if logger:
                logger.warning(f"Order {order_id} not found (may be closed)")
            return False
        
        if order['status'] != 'open':
            if logger:
                logger.info(f"Order {order_id} already {order['status']}")
            return False
        
        # 2. Cancelar orden
        symbol = symbol or order['symbol']
        result = exchange.cancel_order(order_id, symbol)
        
        if logger:
            logger.info(f"Order {order_id} canceled")
        
        return True
    
    except ccxt.OrderNotFound:
        if logger:
            logger.info(f"Order {order_id} not found (already canceled/filled)")
        return False
    
    except Exception as e:
        if logger:
            logger.error(f"Cancel failed: {type(e).__name__}: {e}")
        return False
```

---

## 📊 DATA INTEGRITY

### Validar OHLCV

```python
def validate_ohlcv(candles: list, symbol: str, logger = None) -> bool:
    """
    Validar velas OHLCV para integridad de datos
    
    Checkea:
    - Sin duplicados
    - Sin gaps entre velas
    - Precios válidos (high >= low)
    - Volumen positivo
    """
    
    if not candles:
        if logger:
            logger.error(f"No candles for {symbol}")
        return False
    
    timestamps = set()
    expected_gap = 3600000  # 1 hora en ms (asume 1h timeframe)
    
    for i, candle in enumerate(candles):
        timestamp, open_p, high, low, close, volume = candle
        
        # 1. Validar timestamp único
        if timestamp in timestamps:
            if logger:
                logger.error(f"Duplicate timestamp {timestamp}")
            return False
        timestamps.add(timestamp)
        
        # 2. Validar precios válidos
        if high < low:
            if logger:
                logger.error(f"Invalid prices: high {high} < low {low}")
            return False
        
        if open_p > high or open_p < low:
            if logger:
                logger.error(f"Open {open_p} outside high/low range")
            return False
        
        if close > high or close < low:
            if logger:
                logger.error(f"Close {close} outside high/low range")
            return False
        
        # 3. Validar volumen no negativo
        if volume < 0:
            if logger:
                logger.error(f"Negative volume {volume}")
            return False
        
        # 4. Validar no hay gaps (si no es primera vela)
        if i > 0:
            prev_timestamp = candles[i-1][0]
            gap = timestamp - prev_timestamp
            if gap != expected_gap:
                if logger:
                    logger.warning(f"Gap detected: {gap}ms instead of {expected_gap}ms")
                # No es error fatal, pero avisar
    
    if logger:
        logger.info(f"OHLCV validation passed for {symbol} ({len(candles)} candles)")
    
    return True

# Uso
candles = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
if validate_ohlcv(candles, 'BTC/USDT', logger):
    # Usar candles confiadas
    process_candles(candles)
```

### Validar Balance

```python
def validate_balance(balance: dict, logger = None) -> bool:
    """Validar que balance.free + balance.used = balance.total"""
    
    for currency, amounts in balance.items():
        if isinstance(amounts, dict) and 'free' in amounts:
            free = amounts.get('free', 0)
            used = amounts.get('used', 0)
            total = amounts.get('total', 0)
            
            # Validar suma
            calculated_total = free + used
            if abs(calculated_total - total) > 0.00001:  # Permitir pequeño error de redondeo
                if logger:
                    logger.error(f"Balance mismatch for {currency}: {free} + {used} = {calculated_total}, but total = {total}")
                return False
    
    if logger:
        logger.info("Balance validation passed")
    
    return True
```

---

## ⚡ PERFORMANCE

### Parallelizar Requests

```python
import asyncio
from ccxt.async_support import binance

async def fetch_multiple_tickers(exchange, symbols: list):
    """Fetch múltiples tickers en paralelo (faster)"""
    
    tasks = [exchange.fetch_ticker(symbol) for symbol in symbols]
    tickers = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = {}
    for symbol, ticker in zip(symbols, tickers):
        if isinstance(ticker, Exception):
            logger.error(f"Error fetching {symbol}: {ticker}")
        else:
            results[symbol] = ticker
    
    return results

# Uso (con async)
async def main():
    exchange = binance({'enableRateLimit': True})
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']
    tickers = await fetch_multiple_tickers(exchange, symbols)
    
    await exchange.close()

# asyncio.run(main())  # En Python 3.7+
```

### Cache de Markets

```python
class CachedExchange:
    """Exchange wrapper con cache de markets"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self._markets_cache = None
        self._markets_timestamp = 0
        self._cache_ttl = 3600  # 1 hora
    
    def get_market(self, symbol: str):
        """Obtener market info (cached)"""
        
        # Recargar si cache expiró
        if time.time() - self._markets_timestamp > self._cache_ttl:
            self.exchange.load_markets()
            self._markets_cache = self.exchange.markets
            self._markets_timestamp = time.time()
        
        if symbol in self._markets_cache:
            return self._markets_cache[symbol]
        
        return None

# Uso
cached = CachedExchange(exchange)
market = cached.get_market('BTC/USDT')
# Siguiente llamada usará cache (sin API call)
market2 = cached.get_market('BTC/USDT')
```

---

## 📡 MONITORING

### Logging Estructura

```python
import logging
from datetime import datetime

def setup_trading_logger(log_file: str):
    """Configurar logger para trading"""
    
    logger = logging.getLogger('trading')
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# Uso
logger = setup_trading_logger('logs/trading.log')
logger.info("Bot started")
logger.error("Order failed")
```

### Alertas Críticas

```python
def send_alert(message: str, level: str = 'info'):
    """Enviar alerta (Telegram, email, etc)"""
    
    if level == 'error':
        # Enviar error crítico a Telegram
        send_telegram_message(f"🚨 ERROR: {message}")
    elif level == 'warning':
        # Enviar warning
        send_telegram_message(f"⚠️  WARNING: {message}")
    elif level == 'info':
        # Solo log
        logger.info(message)

def send_telegram_message(message: str):
    """Enviar mensaje a Telegram"""
    # Implementar con BOT_TOKEN y CHAT_ID
    pass
```

---

## ✅ CHECKLIST PRE-PRODUCCIÓN

### Antes de Deployear en Vivo

```
CONFIGURACIÓN:
  [ ] Credenciales en variables de entorno (.env)
  [ ] API key con IP whitelist
  [ ] Permisos: solo trading, sin withdraw
  [ ] Sandbox mode = false
  [ ] Rate limit ajustado (400ms mínimo)

ERROR HANDLING:
  [ ] DDoSProtection: retry con backoff
  [ ] ExchangeNotAvailable: retry con backoff
  [ ] InvalidNonce: log y alert
  [ ] InsufficientFunds: check antes de order
  [ ] InvalidOrder: validar precios/cantidad

RATE LIMITING:
  [ ] enableRateLimit = true
  [ ] rateLimit = 400ms o mayor
  [ ] Monitorear weight/min en logs
  [ ] No exceder 80% de límite

ORDER MANAGEMENT:
  [ ] Validar markets antes de orden
  [ ] Validar precision/límites
  [ ] Usar clientOrderId único
  [ ] Verificar orden antes de cancelar
  [ ] Track trades en BD local

DATA INTEGRITY:
  [ ] Validar OHLCV (no gaps, no duplicados)
  [ ] Validar balance (free + used = total)
  [ ] Backup de ordenes en BD
  [ ] Logs de todas las transacciones

PERFORMANCE:
  [ ] Cache markets (reload cada 1h)
  [ ] No recrear exchange instance
  [ ] Parallelizar requests con async
  [ ] Monitor de latency (promedio ms)

MONITORING:
  [ ] Logger configurado (file + console)
  [ ] Alertas críticas a Telegram
  [ ] Health check cada 5 minutos
  [ ] Graceful shutdown handler

TESTING:
  [ ] Backtest: mínimo 1 año de datos
  [ ] Sandbox: mínimo 24-48 horas
  [ ] Small position: primeras 24-48h
  [ ] Monitoring 24/7 primeras semanas

DOCUMENTACIÓN:
  [ ] README con instrucciones
  [ ] Credenciales no en repos
  [ ] Logs guardados por fecha
  [ ] Proceso de recuperación ante error
```

---

## 🎯 CONCLUSIÓN

**Puntos Clave:**
1. ✅ Una sola instancia de exchange
2. ✅ Rate limiting habilitado
3. ✅ Sandbox mode para testing
4. ✅ Error handling robusto con retry
5. ✅ Validar datos antes de usar
6. ✅ Logging y alerts configurados
7. ✅ Credenciales seguras (env vars)
8. ✅ Checklist pre-producción completo

**BotCopilot está listo para producción si sigues estas prácticas.**

---

**Documento:** CCXT_BEST_PRACTICES_LIVE_TRADING.md  
**Estado:** ✅ Completo  
**Aplicable:** BotCopilot v2.0+  
**Revisar:** Antes de cada deployment  
**Última actualización:** 26/10/2025  
