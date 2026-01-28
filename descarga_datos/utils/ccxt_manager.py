# 🔧 CCXT MANAGER - Improved CCXT Integration with Retry & Logging
## Auto-Retry, Timeout Configurable, and Detailed Logging

"""
CCXT Manager: Wrapper mejorado para CCXT con:
1. Auto-Retry con Exponential Backoff
2. Logging detallado de requests/responses
3. Timeout configurable por endpoint
"""

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

import time
import random
import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import os

# Setup logger
logger = logging.getLogger('ccxt_manager')
if not logger.handlers:
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    handler = logging.FileHandler(log_dir / 'ccxt_manager.log')
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class CCXTManager:
    """
    Manager mejorado para CCXT con retry logic y logging
    
    Features:
    - Auto-retry con exponential backoff
    - Timeout configurable
    - Verbose logging de requests
    - Error handling robusto
    """
    
    def __init__(
        self,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        config: Optional[Dict[str, Any]] = None,
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Inicializar CCXT Manager
        
        Args:
            exchange_name: Nombre del exchange (binance, bybit, etc)
            api_key: API key
            api_secret: API secret
            config: Configuración adicional
            logger_instance: Logger personalizado
        """
        self.exchange_name = exchange_name
        self.logger = logger_instance or logger
        
        # Default configuration
        default_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'rateLimit': 400,  # 400ms entre requests
            'timeout': 30000,  # 30 segundos default
            'sandbox': False,
            'verbose': False  # Set to True for debugging
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        self.config = default_config
        self.exchange = None
        self.markets_loaded = False
        self.request_count = 0
        self.error_count = 0
        
        # Initialize exchange
        self._init_exchange()
        
        self.logger.info(f"✅ CCXTManager initialized for {exchange_name}")
        self.logger.info(f"   Config: sandbox={self.config.get('sandbox')}, "
                        f"rateLimit={self.config.get('rateLimit')}ms, "
                        f"timeout={self.config.get('timeout')}ms")
    
    def _init_exchange(self):
        """Inicializar instancia de exchange"""
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            self.exchange = exchange_class(self.config)
            self.logger.debug(f"Exchange instance created: {self.exchange_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    def with_retry(
        self,
        func: Callable,
        max_retries: int = 3,
        base_wait: float = 1.0,
        backoff_factor: float = 2.0,
        operation_name: str = "Operation"
    ) -> Optional[Any]:
        """
        Ejecutar función con retry automático y exponential backoff
        
        Args:
            func: Función a ejecutar
            max_retries: Máximo de reintentos
            base_wait: Espera inicial en segundos
            backoff_factor: Multiplicador de espera (exponencial)
            operation_name: Nombre de la operación (para logging)
        
        Returns:
            Resultado de la función o None si fallan todos los reintentos
        """
        
        for attempt in range(max_retries):
            try:
                self.request_count += 1
                result = func()
                
                if attempt > 0:
                    self.logger.info(
                        f"✅ {operation_name} succeeded after {attempt+1} attempts"
                    )
                
                return result
            
            except (ccxt.DDoSProtection, ccxt.ExchangeNotAvailable, 
                    ccxt.RateLimitExceeded) as e:
                self.error_count += 1
                
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"❌ {operation_name} failed after {max_retries} retries: {e}"
                    )
                    raise
                
                # Exponential backoff + jitter
                wait_time = base_wait * (backoff_factor ** attempt) + random.uniform(0, 1)
                
                self.logger.warning(
                    f"⚠️  {operation_name} - Retry {attempt + 1}/{max_retries} "
                    f"(waiting {wait_time:.2f}s): {type(e).__name__}"
                )
                
                time.sleep(wait_time)
            
            except (ccxt.InvalidNonce, ccxt.AuthenticationError, 
                    ccxt.PermissionDenied) as e:
                self.error_count += 1
                self.logger.error(
                    f"❌ {operation_name} - Unrecoverable error: {type(e).__name__}: {e}"
                )
                raise
            
            except Exception as e:
                self.error_count += 1
                self.logger.error(
                    f"❌ {operation_name} - Unexpected error: {type(e).__name__}: {e}"
                )
                raise
        
        return None
    
    def set_timeout(self, timeout_ms: int):
        """
        Cambiar timeout global
        
        Args:
            timeout_ms: Timeout en milisegundos
        """
        self.config['timeout'] = timeout_ms
        self.exchange.timeout = timeout_ms
        self.logger.info(f"⏱️  Timeout changed to {timeout_ms}ms")
    
    def set_rate_limit(self, rate_limit_ms: int):
        """
        Cambiar rate limit
        
        Args:
            rate_limit_ms: Rate limit en milisegundos
        """
        self.config['rateLimit'] = rate_limit_ms
        self.exchange.rateLimit = rate_limit_ms
        self.logger.info(f"⏱️  Rate limit changed to {rate_limit_ms}ms")
    
    def enable_verbose(self, verbose: bool = True):
        """
        Habilitar/deshabilitar verbose logging
        
        Args:
            verbose: True para habilitar
        """
        self.exchange.verbose = verbose
        self.config['verbose'] = verbose
        self.logger.info(f"🔍 Verbose logging: {'ENABLED' if verbose else 'DISABLED'}")
    
    def load_markets(self, force: bool = False):
        """
        Cargar markets (una sola vez por defecto)
        
        Args:
            force: Forzar recarga
        
        Returns:
            Markets dictionary
        """
        
        def _load():
            self.logger.debug("Loading markets...")
            markets = self.exchange.load_markets()
            self.logger.info(f"✅ Markets loaded: {len(markets)} symbols")
            return markets
        
        if self.markets_loaded and not force:
            return self.exchange.markets
        
        try:
            result = self.with_retry(
                _load,
                max_retries=3,
                operation_name="LoadMarkets"
            )
            self.markets_loaded = True
            return result
        except Exception as e:
            self.logger.error(f"Failed to load markets: {e}")
            raise
    
    def fetch_balance(self) -> Optional[Dict]:
        """
        Obtener balance con retry
        
        Returns:
            Balance dictionary o None
        """
        
        def _fetch():
            self.logger.debug("Fetching balance...")
            balance = self.exchange.fetch_balance()
            self.logger.debug(f"✅ Balance fetched: {len(balance)} currencies")
            return balance
        
        try:
            return self.with_retry(
                _fetch,
                max_retries=3,
                operation_name="FetchBalance"
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            return None
    
    def fetch_ticker(self, symbol: str, timeout_override: Optional[int] = None) -> Optional[Dict]:
        """
        Obtener ticker con retry
        
        Args:
            symbol: Símbolo (BTC/USDT)
            timeout_override: Timeout específico para este request
        
        Returns:
            Ticker dictionary o None
        """
        
        if timeout_override:
            original_timeout = self.exchange.timeout
            self.exchange.timeout = timeout_override
        
        def _fetch():
            self.logger.debug(f"Fetching ticker for {symbol}...")
            ticker = self.exchange.fetch_ticker(symbol)
            self.logger.debug(f"✅ Ticker {symbol}: ${ticker['last']:.2f}")
            return ticker
        
        try:
            result = self.with_retry(
                _fetch,
                max_retries=3,
                operation_name=f"FetchTicker({symbol})"
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            return None
        finally:
            if timeout_override:
                self.exchange.timeout = original_timeout
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
        timeout_override: Optional[int] = None
    ) -> Optional[list]:
        """
        Obtener OHLCV con retry
        
        Args:
            symbol: Símbolo
            timeframe: Timeframe (1m, 5m, 1h, etc)
            limit: Número de velas
            timeout_override: Timeout específico
        
        Returns:
            Lista de velas o None
        """
        
        if timeout_override:
            original_timeout = self.exchange.timeout
            self.exchange.timeout = timeout_override
        
        def _fetch():
            self.logger.debug(f"Fetching OHLCV {symbol} {timeframe} (limit={limit})...")
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            self.logger.debug(f"✅ OHLCV fetched: {len(candles)} candles")
            return candles
        
        try:
            result = self.with_retry(
                _fetch,
                max_retries=3,
                operation_name=f"FetchOHLCV({symbol},{timeframe})"
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV: {e}")
            return None
        finally:
            if timeout_override:
                self.exchange.timeout = original_timeout
    
    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        timeout_override: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Crear orden con retry y validación
        
        Args:
            symbol: Símbolo
            order_type: 'market' o 'limit'
            side: 'buy' o 'sell'
            amount: Cantidad
            price: Precio (requerido para limit orders)
            client_order_id: ID único para tracking
            timeout_override: Timeout específico
        
        Returns:
            Order dictionary o None
        """
        
        if timeout_override:
            original_timeout = self.exchange.timeout
            self.exchange.timeout = timeout_override
        
        def _create():
            self.logger.debug(
                f"Creating order: {side.upper()} {amount} {symbol} @ "
                f"{f'${price}' if price else 'MARKET'}"
            )
            
            params = {}
            if client_order_id:
                params['clientOrderId'] = client_order_id
            
            order = self.exchange.create_order(
                symbol, order_type, side, amount, price, params
            )
            
            self.logger.info(
                f"✅ Order created: {order['id']} ({side.upper()} {amount} {symbol})"
            )
            return order
        
        try:
            result = self.with_retry(
                _create,
                max_retries=3,
                operation_name=f"CreateOrder({side},{amount},{symbol})"
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to create order: {e}")
            return None
        finally:
            if timeout_override:
                self.exchange.timeout = original_timeout
    
    def cancel_order(
        self,
        order_id: str,
        symbol: str,
        timeout_override: Optional[int] = None
    ) -> bool:
        """
        Cancelar orden con retry
        
        Args:
            order_id: ID de la orden
            symbol: Símbolo
            timeout_override: Timeout específico
        
        Returns:
            True si se canceló, False si no
        """
        
        if timeout_override:
            original_timeout = self.exchange.timeout
            self.exchange.timeout = timeout_override
        
        def _cancel():
            self.logger.debug(f"Canceling order {order_id} ({symbol})...")
            result = self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"✅ Order canceled: {order_id}")
            return result
        
        try:
            self.with_retry(
                _cancel,
                max_retries=3,
                operation_name=f"CancelOrder({order_id})"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
        finally:
            if timeout_override:
                self.exchange.timeout = original_timeout
    
    def fetch_order(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        Obtener estado de orden con retry
        
        Args:
            order_id: ID de la orden
            symbol: Símbolo
        
        Returns:
            Order dictionary o None
        """
        
        def _fetch():
            self.logger.debug(f"Fetching order {order_id} ({symbol})...")
            order = self.exchange.fetch_order(order_id, symbol)
            self.logger.debug(f"✅ Order {order_id} status: {order['status']}")
            return order
        
        try:
            return self.with_retry(
                _fetch,
                max_retries=3,
                operation_name=f"FetchOrder({order_id})"
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch order {order_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso"""
        return {
            'exchange': self.exchange_name,
            'requests': self.request_count,
            'errors': self.error_count,
            'error_rate': f"{(self.error_count / max(self.request_count, 1) * 100):.1f}%",
            'sandbox': self.config.get('sandbox'),
            'timeout_ms': self.config.get('timeout'),
            'rate_limit_ms': self.config.get('rateLimit')
        }
    
    def print_stats(self):
        """Imprimir estadísticas"""
        stats = self.get_stats()
        self.logger.info("📊 CCXT Manager Stats:")
        for key, value in stats.items():
            self.logger.info(f"   {key}: {value}")


# Wrapper function para uso fácil
def create_ccxt_manager(
    exchange_name: str,
    api_key: str,
    api_secret: str,
    sandbox: bool = True,
    timeout_ms: int = 30000,
    rate_limit_ms: int = 400,
    verbose: bool = False
) -> CCXTManager:
    """
    Crear un CCXTManager listo para usar
    
    Args:
        exchange_name: Nombre del exchange
        api_key: API key
        api_secret: API secret
        sandbox: Modo sandbox (defecto: True)
        timeout_ms: Timeout en ms
        rate_limit_ms: Rate limit en ms
        verbose: Verbose logging
    
    Returns:
        CCXTManager instance
    """
    
    config = {
        'sandbox': sandbox,
        'timeout': timeout_ms,
        'rateLimit': rate_limit_ms,
        'verbose': verbose,
        'enableRateLimit': True
    }
    
    return CCXTManager(exchange_name, api_key, api_secret, config)


if __name__ == "__main__":
    # Example usage
    print("CCXTManager loaded - use in your code with create_ccxt_manager()")
