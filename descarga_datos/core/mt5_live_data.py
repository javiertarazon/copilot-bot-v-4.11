#!/usr/bin/env python3
"""
MT5 Live Data Provider - Componente para obtener datos en tiempo real de MetaTrader 5
para operaciones de trading en vivo con actualización continua.
"""

import time
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import get_logger
import threading

logger = get_logger(__name__)

# Intentar importar módulo de resiliencia
try:
    from utils.resilience import create_resilient_connection_manager
    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False

# Intentar importar MT5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 no está disponible. Modo simulado activado.")

class MT5LiveDataProvider:
    def __init__(self, config=None):
        # Inicializar logger primero
        self.logger = get_logger(__name__ + ".MT5LiveDataProvider")
        
        self.config = config
        self.connected = False
        self.connection_lock = threading.Lock()
        self.data_cache = {}  # Cache de datos por símbolo y timeframe
        self.last_candle_timestamp = {}  # Última marca de tiempo procesada por símbolo/timeframe
        self.market_status = {}  # Estado del mercado por símbolo
        
        # Configuración de símbolos y timeframes por defecto
        self.symbols = getattr(config, 'symbols', ['EURUSD', 'GBPUSD', 'USDJPY']) if config else ['EURUSD', 'GBPUSD', 'USDJPY']
        self.timeframes = getattr(config, 'timeframes', ['1m', '5m', '1h']) if config else ['1m', '5m', '1h']
        self.history_bars = getattr(config, 'history_bars', 1000) if config else 1000
        
        # Configuración de reintentos
        self.max_retries = getattr(config, 'max_retries', 3) if hasattr(config, 'max_retries') else 3
        self.retry_delay = getattr(config, 'retry_delay', 5) if hasattr(config, 'retry_delay') else 5
        
        # Gestor de resiliencia con exponential backoff + circuit breaker
        self.resilience_manager = None
        if RESILIENCE_AVAILABLE:
            self.resilience_manager = create_resilient_connection_manager(
                name="MT5",
                initial_delay=self.retry_delay,
                logger=self.logger
            )
        
        # Rutas para almacenamiento de datos en vivo
        self.data_path = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / "data" / "live_data"
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar conexión
        if MT5_AVAILABLE:
            self._initialize_mt5()
    
    def connect(self) -> bool:
        """
        Establece conexión con MT5 y prepara el proveedor para su uso.
        
        Returns:
            bool: True si la conexión se estableció correctamente
        """
        if self._initialize_mt5():
            self.connected = True
            self.logger.info("MT5LiveDataProvider conectado correctamente")
            
            # Pre-cargar datos históricos si se proporcionaron símbolos y timeframes
            if self.symbols and self.timeframes:
                for symbol in self.symbols:
                    for tf in self.timeframes:
                        self.get_historical_data(symbol, tf, self.history_bars)
            
            return True
        
        return False
        
    def disconnect(self) -> bool:
        """
        Desconecta el proveedor de datos de MT5.
        
        Returns:
            bool: True si la desconexión fue exitosa
        """
        with self.connection_lock:
            self.connected = False
            self.logger.info("MT5LiveDataProvider desconectado")
            return True
            
    def is_connected(self) -> bool:
        """
        Verifica si el proveedor está conectado a MT5.
        
        Returns:
            bool: True si está conectado
        """
        return self.connected and MT5_AVAILABLE and mt5.terminal_info() is not None
        
    def get_current_data(self, symbol: str, timeframe: str, bars: int = 100) -> pd.DataFrame:
        """
        Obtiene los datos actuales para un símbolo y timeframe específicos.
        Método optimizado para MT5 que aprovecha las capacidades del broker Deriv.
        
        Args:
            symbol: Símbolo a consultar (ej: "EURUSD")
            timeframe: Timeframe en formato string ("1m", "5m", "1h", "4h", "1d")
            bars: Número de barras a recuperar (solo usado si no hay cache)
            
        Returns:
            DataFrame con datos OHLCV o None si hay error
        """
        return self.get_live_data_efficient(symbol, timeframe, bars)
            
    def get_live_data_efficient(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Método optimizado para obtener datos en vivo desde MT5.
        Aprovecha caché inteligente para detectar candles duplicados.
        
        🔧 FIX v4.10: Retorna None si el candle no ha cambiado (ciclos repetitivos).
        Esto previene el procesamiento de 180+ señales idénticas por candle de 15m.
        
        Estrategia:
        - Primera vez: Obtiene datos históricos y guarda timestamp del último candle
        - Actualizaciones: Solo retorna datos si el timestamp del último candle cambió
        - Si es el mismo candle: Retorna None (sin procesar)
        
        Args:
            symbol: Símbolo a consultar
            timeframe: Timeframe en formato string
            bars: Número de barras para la carga inicial
            
        Returns:
            DataFrame con datos OHLCV actualizados si hay nuevo candle, None si no cambió
        """
        cache_key = f"{symbol}_{timeframe}"
        candle_key = f"{symbol}_{timeframe}_last_candle_ts"
        
        # Convertir timeframe a constante MT5
        tf_map = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
            "1w": mt5.TIMEFRAME_W1,
        }
        
        mt5_tf = tf_map.get(timeframe.lower())
        if mt5_tf is None:
            self.logger.error(f"Timeframe no válido: {timeframe}")
            return None
            
        # Decide whether to aggregate ticks into timeframe bars
        use_ticks = True
        try:
            if isinstance(self.config, dict):
                use_ticks = bool(self.config.get('use_tick_aggregation', True))
            else:
                use_ticks = bool(getattr(self.config, 'use_tick_aggregation', True))
        except Exception:
            use_ticks = True

        try:
            # Obtener datos (agregados por ticks o históricos)
            if use_ticks:
                agg = self.get_aggregated_bars(symbol, timeframe, bars)
                if agg is not None:
                    data = agg
                else:
                    data = self._load_initial_data(symbol, mt5_tf, cache_key, bars)
            else:
                if cache_key not in self.data_cache:
                    data = self._load_initial_data(symbol, mt5_tf, cache_key, bars)
                else:
                    data = self._update_cached_data(symbol, mt5_tf, cache_key)
            
            if data is None or len(data) == 0:
                return None
            
            # 🔧 NUEVA LÓGICA: Detectar candle duplicado
            # Extraer timestamp del último candle (más reciente)
            last_candle_ts = data['time'].max()
            
            # Obtener timestamp del último candle procesado
            stored_ts = self.last_candle_timestamp.get(candle_key)
            
            if stored_ts is not None and stored_ts == last_candle_ts:
                # ⚠️ EL CANDLE NO HA CAMBIADO - Retornar None
                # Esto indica al orquestador que no hay datos nuevos
                self.logger.debug(
                    f"[CACHE HIT] {symbol} {timeframe}: candle no cambió "
                    f"(timestamp: {last_candle_ts}). Retornando None para skipear procesamiento."
                )
                return None
            
            # ✅ NUEVO CANDLE - Guardar timestamp y retornar datos
            self.last_candle_timestamp[candle_key] = last_candle_ts
            self.logger.debug(
                f"[CACHE MISS] {symbol} {timeframe}: candle nuevo detectado "
                f"(anterior: {stored_ts}, actual: {last_candle_ts}). Procesando datos."
            )
            return data.copy()
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos eficientes para {symbol} {timeframe}: {str(e)}")
            return None

    def get_aggregated_bars(self, symbol: str, timeframe: str, bars: int = 200) -> Optional[pd.DataFrame]:
        """
        Construye barras OHLCV para el timeframe dado agrupando ticks recibidos desde MT5.

        Esto garantiza que el orquestador y las estrategias trabajen con velas cerradas
        alineadas al timeframe (por ejemplo 15m) en lugar de usar ticks o barras
        parcialmente construidas.
        """
        # Map timeframe a minutos
        tf_minutes_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }

        tf_min = tf_minutes_map.get(timeframe.lower())
        if tf_min is None:
            self.logger.debug(f"Timeframe no soportado para agregación por ticks: {timeframe}")
            return None

        cache_key = f"{symbol}_{timeframe}_ticks"

        try:
            # Timestamp desde el que pedir ticks: barras * minutos
            from_dt = datetime.utcnow() - timedelta(minutes=bars * tf_min)

            # Intentar obtener ticks desde MT5
            ticks = mt5.copy_ticks_from(symbol, from_dt, mt5.COPY_TICKS_ALL)

            if ticks is None or len(ticks) == 0:
                # Fall back a tasas históricas si no hay ticks disponibles
                self.logger.debug(f"No se obtuvieron ticks para {symbol}, usando rates históricos")
                mt5_tf_map = {
                    "1m": mt5.TIMEFRAME_M1,
                    "5m": mt5.TIMEFRAME_M5,
                    "15m": mt5.TIMEFRAME_M15,
                    "30m": mt5.TIMEFRAME_M30,
                    "1h": mt5.TIMEFRAME_H1,
                    "4h": mt5.TIMEFRAME_H4,
                    "1d": mt5.TIMEFRAME_D1,
                    "1w": mt5.TIMEFRAME_W1,
                }
                return self._load_initial_data(symbol, mt5_tf_map.get(timeframe.lower(), mt5.TIMEFRAME_M1), f"{symbol}_{timeframe}", bars)

            # Convertir ticks a DataFrame
            tdf = pd.DataFrame(ticks)
            if tdf.empty:
                return None

            # Determinar precio medio por tick
            if 'last' in tdf.columns and not tdf['last'].isnull().all():
                tdf['price'] = tdf['last']
            else:
                # Si no hay 'last', usar midpoint bid/ask
                if 'bid' in tdf.columns and 'ask' in tdf.columns:
                    tdf['price'] = (tdf['bid'] + tdf['ask']) / 2.0
                else:
                    # No hay datos utilizables
                    return None

            # Normalizar tiempo
            tdf['time'] = pd.to_datetime(tdf['time'], unit='s')
            tdf = tdf.set_index('time')

            # Contabilizar volumen: usar volumen real si existe y es >0, sino usar conteo de ticks como proxy de actividad
            if 'volume' in tdf.columns and not tdf['volume'].isnull().all() and (tdf['volume'] > 0).any():
                vol_col = 'volume'  # Usar volumen real de ticks
            else:
                # Para índices sintéticos sin volumen real, usar conteo de ticks como proxy
                tdf['tick_count'] = 1
                vol_col = 'tick_count'

            # Resamplear a timeframe
            rule = f"{tf_min}T"
            ohlc = tdf['price'].resample(rule).agg(['first', 'max', 'min', 'last'])
            vol = tdf[vol_col].resample(rule).sum()

            ohlc.columns = ['open', 'high', 'low', 'close']
            bars_df = ohlc.join(vol)
            bars_df = bars_df.dropna(subset=['open'])

            # Evitar usar la barra en construcción: descartar la última barra
            if len(bars_df) > 1:
                bars_df = bars_df.iloc[:-1]

            # Mantener sólo las últimas 'bars' barras
            if len(bars_df) > bars:
                bars_df = bars_df.tail(bars)

            bars_df = bars_df.reset_index().rename(columns={'index': 'time'})
            bars_df = bars_df.rename(columns={vol_col: 'volume'})

            # Guardar en cache
            self.data_cache[f"{symbol}_{timeframe}"] = {
                'data': bars_df,
                'last_update': datetime.now(),
                'last_time': bars_df['time'].max() if len(bars_df) > 0 else None
            }

            self.logger.debug(f"Agregadas {len(bars_df)} barras por ticks para {symbol} {timeframe}")
            return bars_df.copy()

        except Exception as e:
            self.logger.error(f"Error agregando ticks a barras para {symbol} {timeframe}: {e}")
            return None
    
    def _load_initial_data(self, symbol: str, mt5_tf: int, cache_key: str, bars: int) -> pd.DataFrame:
        """
        Carga los datos iniciales para un símbolo/timeframe.
        """
        # Obtener datos históricos recientes
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
        if rates is None or len(rates) == 0:
            self.logger.error(f"No se pudieron obtener datos iniciales para {symbol}")
            return None
            
        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'tick_volume': 'volume'})
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        
        # Almacenar en cache con metadata
        self.data_cache[cache_key] = {
            'data': df,
            'last_update': datetime.now(),
            'last_time': df['time'].max() if len(df) > 0 else None
        }
        
        self.logger.info(f"Datos iniciales cargados: {len(df)} barras para {symbol}")
        return df.copy()
    
    def _is_cache_stale(self, cache_key: str, max_age_seconds: int = 5) -> bool:
        """
        Verifica si el cache para una clave específica está desactualizado (stale).
        
        Args:
            cache_key: Clave del cache (formato: "symbol_timeframe")
            max_age_seconds: Edad máxima permitida en segundos (default: 5)
        
        Returns:
            True si el cache está desactualizado o no existe, False si está fresco
        """
        if cache_key not in self.data_cache:
            return True  # Sin cache = stale
        
        cached_info = self.data_cache[cache_key]
        if not isinstance(cached_info, dict) or 'last_update' not in cached_info:
            return True  # Cache mal formado = stale
        
        last_update = cached_info['last_update']
        age_seconds = (datetime.now() - last_update).total_seconds()
        
        is_stale = age_seconds > max_age_seconds
        
        if is_stale:
            self.logger.debug(f"Cache stale para {cache_key}: {age_seconds:.1f}s > {max_age_seconds}s")
        
        return is_stale
    
    def _update_cached_data(self, symbol: str, mt5_tf: int, cache_key: str) -> pd.DataFrame:
        """
        Actualiza los datos en cache obteniendo solo las barras nuevas.
        """
        cached_info = self.data_cache[cache_key]
        last_time = cached_info['last_time']
        
        if last_time is None:
            # Si no hay tiempo de referencia, recargar todo
            self.logger.warning(f"Sin tiempo de referencia para {cache_key}, recargando...")
            del self.data_cache[cache_key]
            return self.get_live_data_efficient(symbol, mt5_tf, 100)
        
        # Calcular cuántas barras nuevas obtener (máximo 100 para evitar sobrecarga)
        # En MT5 podemos obtener datos desde una fecha específica
        from_date = int(last_time.timestamp())
        
        # Obtener barras nuevas desde la última actualización
        rates = mt5.copy_rates_from(symbol, mt5_tf, from_date, 100)
        
        if rates is None:
            self.logger.warning(f"No se pudieron obtener actualizaciones para {symbol}")
            return cached_info['data'].copy()
            
        if len(rates) <= 1:  # <= 1 porque la última barra puede estar incluida
            # No hay datos nuevos, devolver cache actual
            return cached_info['data'].copy()
        
        # Convertir nuevas barras a DataFrame
        new_df = pd.DataFrame(rates)
        new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
        new_df = new_df.rename(columns={'tick_volume': 'volume'})
        new_df = new_df[['time', 'open', 'high', 'low', 'close', 'volume']]
        
        # Filtrar solo barras más nuevas que la última en cache
        new_bars = new_df[new_df['time'] > last_time]
        
        if len(new_bars) == 0:
            # No hay barras realmente nuevas
            return cached_info['data'].copy()
        
        # Concatenar datos existentes con nuevos
        updated_df = pd.concat([cached_info['data'], new_bars], ignore_index=True)
        
        # Mantener solo las últimas 1000 barras para evitar crecimiento excesivo
        if len(updated_df) > 1000:
            updated_df = updated_df.tail(1000).reset_index(drop=True)
        
        # Actualizar cache
        self.data_cache[cache_key] = {
            'data': updated_df,
            'last_update': datetime.now(),
            'last_time': updated_df['time'].max()
        }
        
        self.logger.debug(f"Cache actualizado para {symbol}: +{len(new_bars)} barras nuevas (total: {len(updated_df)})")
        return updated_df.copy()
    
    def get_data_from_date(self, symbol: str, timeframe: str, from_date: datetime, bars: int = 1000) -> pd.DataFrame:
        """
        Obtiene datos históricos desde una fecha específica.
        Útil para inicializaciones o análisis de períodos específicos.
        
        Args:
            symbol: Símbolo a consultar
            timeframe: Timeframe en formato string
            from_date: Fecha desde la cual obtener datos
            bars: Número máximo de barras a recuperar
            
        Returns:
            DataFrame con datos OHLCV desde la fecha especificada
        """
        # Convertir timeframe a constante MT5
        tf_map = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
            "1w": mt5.TIMEFRAME_W1,
        }
        
        mt5_tf = tf_map.get(timeframe.lower())
        if mt5_tf is None:
            self.logger.error(f"Timeframe no válido: {timeframe}")
            return None
            
        try:
            # Convertir fecha a timestamp
            from_timestamp = int(from_date.timestamp())
            
            # Obtener datos desde la fecha especificada
            rates = mt5.copy_rates_from(symbol, mt5_tf, from_timestamp, bars)
            
            if rates is None or len(rates) == 0:
                self.logger.warning(f"No se encontraron datos para {symbol} {timeframe} desde {from_date}")
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={'tick_volume': 'volume'})
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            self.logger.info(f"Datos obtenidos desde {from_date}: {len(df)} barras para {symbol} {timeframe}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos desde fecha para {symbol} {timeframe}: {str(e)}")
            return None
            
    def get_historical_data(self, symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
        """
        Obtiene datos históricos para un símbolo y timeframe específicos.
        
        Args:
            symbol: Símbolo a consultar (ej: "EURUSD")
            timeframe: Timeframe en formato string ("1m", "5m", "1h", "4h", "1d")
            bars: Número de barras a recuperar
            
        Returns:
            DataFrame con datos OHLCV o None si hay error
        """
        self.logger.info(f"Obteniendo datos históricos para {symbol} {timeframe} ({bars} barras)")
        
        # Convertir timeframe de string a constante MT5
        tf_map = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
            "1w": mt5.TIMEFRAME_W1,
        }
        
        mt5_tf = tf_map.get(timeframe.lower())
        if mt5_tf is None:
            self.logger.error(f"Timeframe no válido: {timeframe}")
            return None
            
        try:
            # Obtener datos históricos recientes
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            if rates is None or len(rates) == 0:
                self.logger.error(f"No se pudieron obtener datos para {symbol} {timeframe}")
                return None
                
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Renombrar columnas para consistencia
            df = df.rename(columns={
                'tick_volume': 'volume'
            })
            
            # Mantener solo columnas necesarias
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # Cachear datos
            cache_key = f"{symbol}_{timeframe}"
            self.data_cache[cache_key] = df
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error al obtener datos para {symbol} {timeframe}: {str(e)}")
            return None
    
    def _initialize_mt5(self) -> bool:
        """
        Inicializa la conexión con MetaTrader 5.
        
        Returns:
            bool: True si la conexión se estableció correctamente
        """
        with self.connection_lock:
            if not MT5_AVAILABLE:
                self.logger.error("MT5 no está disponible. Instale el paquete MetaTrader5.")
                return False
            
            try:
                # Inicializar MT5 si no está inicializado
                if not mt5.initialize():
                    self.logger.error(f"Error al inicializar MT5: {mt5.last_error()}")
                    return False
                
                # Login si se proporcionan credenciales
                if hasattr(self.config, 'login') and self.config.login:
                    if not mt5.login(
                        self.config.login,
                        password=self.config.password,
                        server=self.config.server
                    ):
                        self.logger.error(f"Error en login MT5: {mt5.last_error()}")
                        return False
                
                # Verificar conexión
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.error("No se pudo obtener información de la cuenta MT5")
                    return False
                
                # Almacenar información de la cuenta
                self.account_info = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'leverage': account_info.leverage,
                    'name': account_info.name,
                    'server': account_info.server
                }
                
                self.connected = True
                self.logger.info(f"MT5 conectado: {self.account_info['name']} @ {self.account_info['server']}")
                self.logger.info(f"Balance: {self.account_info['balance']}, Equity: {self.account_info['equity']}")
                
                return True
            
            except Exception as e:
                self.logger.error(f"Error inicializando MT5: {e}")
                return False
    
    def ensure_connection(self) -> bool:
        """
        Asegura que hay una conexión activa con MT5, reconectando si es necesario.
        
        Returns:
            bool: True si la conexión está activa
        """
        with self.connection_lock:
            if self.connected:
                # Verificar si la conexión sigue activa
                if not mt5.terminal_info():
                    self.logger.warning("Conexión MT5 perdida. Intentando reconectar...")
                    self.connected = False
            
            if not self.connected:
                return self._initialize_mt5()
            
            return True
    
    def check_and_reconnect(self) -> bool:
        """
        Verifica el estado de la conexión y reconecta automáticamente si es necesario.
        Usa resilience manager para exponential backoff + circuit breaker.
        Método diseñado para ser llamado periódicamente por el health check.

        Returns:
            bool: True si la conexión está activa (después de reconectar si fue necesario)
        """
        if self.resilience_manager:
            # Usar gestor de resiliencia
            def reconnection_attempt():
                self.logger.info("Intentando reconexión automática a MT5...")
                
                try:
                    if self.connected:
                        self.disconnect()
                    
                    success = self._initialize_mt5()
                    
                    if success:
                        self.logger.info("✅ Reconexión exitosa a MT5")
                        return True
                    else:
                        self.logger.error("❌ Falló reconexión a MT5")
                        raise Exception("Reconexión fallida para MT5")
                
                except Exception as e:
                    self.logger.error(f"Error durante reconexión a MT5: {e}")
                    raise
            
            # Ejecutar con reintentos usando resilience manager
            success, result, error = self.resilience_manager.execute_with_retry(reconnection_attempt)
            
            if success:
                return True
            else:
                self.logger.error(f"Reconexión fallida tras reintentos del resilience manager: {error}")
                return False
        else:
            # Fallback - usar ensure_connection directamente
            return self.ensure_connection()
    
    def get_resilience_status(self) -> Optional[Dict[str, Any]]:
        """
        Retorna el estado del gestor de resiliencia.
        
        Returns:
            Dict con información del estado o None si no está disponible
        """
        if self.resilience_manager:
            return self.resilience_manager.get_status()
        return None
    
    def get_live_data(self, symbol: str, timeframe: str, bars: int = 100, with_indicators: bool = True) -> Optional[pd.DataFrame]:
        """
        Obtiene datos en tiempo real para un símbolo y timeframe específico.
        
        Args:
            symbol: Símbolo para obtener datos (ej: "EURUSD", "AAPL.US")
            timeframe: Timeframe en formato MT5 (ej: "1h", "4h", "1d")
            bars: Número de barras a obtener
            with_indicators: Si es True, calcula indicadores técnicos
        
        Returns:
            DataFrame con datos OHLCV e indicadores técnicos o None si falla
        """
        if not self.ensure_connection():
            self.logger.error("No hay conexión con MT5")
            return None
        
        try:
            # Convertir timeframe a formato MT5
            mt5_timeframe = self._convert_timeframe(timeframe)
            if mt5_timeframe is None:
                self.logger.error(f"Timeframe no soportado: {timeframe}")
                return None
            
            # Obtener datos
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
            if rates is None or len(rates) == 0:
                self.logger.warning(f"No hay datos para {symbol} en timeframe {timeframe}")
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Renombrar columnas para consistencia
            df = df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            })
            
            # Mantener solo columnas necesarias
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # Actualizar caché
            cache_key = f"{symbol}_{timeframe}"
            self.data_cache[cache_key] = {
                'data': df,
                'last_update': datetime.now()
            }
            
            # Logging detallado para debugging
            self.logger.info(f"✅ Datos frescos obtenidos de MT5: {symbol} {timeframe} - {len(df)} barras, Timestamp: {df['time'].iloc[-1] if len(df) > 0 else 'N/A'}")
            
            # Guardar datos para análisis
            self._save_live_data(symbol, timeframe, df)
            
            self.logger.debug(f"Datos en vivo obtenidos: {symbol} {timeframe} - {len(df)} barras")
            return df
        
        except Exception as e:
            self.logger.error(f"Error obteniendo datos en vivo para {symbol} {timeframe}: {e}")
            return None
    
    def get_market_status(self, symbol: str) -> Dict:
        """
        Verifica el estado del mercado para un símbolo.
        
        Args:
            symbol: Símbolo a verificar
        
        Returns:
            Diccionario con información del estado del mercado
        """
        if not self.ensure_connection():
            return {'is_open': False, 'reason': 'No hay conexión con MT5'}
        
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return {
                    'is_open': False,
                    'reason': f"Símbolo {symbol} no encontrado",
                    'next_open': None,
                    'session_remains': 0
                }
            
            # Determinar si el mercado está abierto
            # Verificar si el símbolo está habilitado para trading y si hay precios disponibles
            is_enabled = symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED
            has_prices = symbol_info.bid > 0 and symbol_info.ask > 0
            is_open = is_enabled and has_prices
            
            # Calcular próxima apertura y tiempo restante si está disponible
            current_time = datetime.now()
            next_open = None
            session_remains = 0
            
            # Almacenar resultado
            status = {
                'is_open': is_open,
                'reason': "Mercado abierto" if is_open else "Mercado cerrado",
                'next_open': next_open,
                'session_remains': session_remains,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'spread': symbol_info.spread,
                'digits': symbol_info.digits,
                'last_update': current_time
            }
            
            # Actualizar caché
            self.market_status[symbol] = status
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del mercado para {symbol}: {e}")
            return {'is_open': False, 'reason': f"Error: {str(e)}"}
    
    def get_account_info(self) -> Dict:
        """
        Obtiene información actualizada de la cuenta.
        
        Returns:
            Diccionario con información de la cuenta
        """
        if not self.ensure_connection():
            return self.account_info or {}
        
        try:
            account_info = mt5.account_info()
            if account_info:
                self.account_info = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'leverage': account_info.leverage,
                    'name': account_info.name,
                    'server': account_info.server,
                    'last_update': datetime.now()
                }
            
            return self.account_info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de la cuenta: {e}")
            return self.account_info or {}
    
    def get_symbols_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Obtiene información detallada sobre múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
        
        Returns:
            Diccionario con información de cada símbolo
        """
        if not self.ensure_connection():
            return {}
        
        result = {}
        for symbol in symbols:
            try:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    result[symbol] = {
                        'bid': symbol_info.bid,
                        'ask': symbol_info.ask,
                        'spread': symbol_info.spread,
                        'digits': symbol_info.digits,
                        'min_lot': symbol_info.volume_min,
                        'max_lot': symbol_info.volume_max,
                        'lot_step': symbol_info.volume_step,
                        'point': symbol_info.point,
                        'tick_size': symbol_info.trade_tick_size,
                        'tick_value': symbol_info.trade_tick_value,
                        'contract_size': symbol_info.trade_contract_size,
                        'currency_base': symbol_info.currency_base,
                        'currency_profit': symbol_info.currency_profit
                    }
            except Exception as e:
                self.logger.error(f"Error obteniendo información para {symbol}: {e}")
        
        return result
    
    def _convert_timeframe(self, timeframe: str) -> Optional[int]:
        """
        Convierte timeframe string a constante MT5.
        
        Args:
            timeframe: String con el timeframe (ej: "1m", "5m", "1h", "4h", "1d")
        
        Returns:
            Constante MT5 correspondiente o None si no es válido
        """
        if not MT5_AVAILABLE:
            return None

        mapping = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1M': mt5.TIMEFRAME_MN1
        }
        return mapping.get(timeframe)
    
    def _save_live_data(self, symbol: str, timeframe: str, data: pd.DataFrame) -> None:
        """
        Guarda los datos en vivo para análisis posterior.
        
        Args:
            symbol: Símbolo
            timeframe: Timeframe
            data: DataFrame con datos
        """
        try:
            # Crear nombre de archivo seguro
            safe_symbol = symbol.replace("/", "_").replace(".", "_")
            filename = self.data_path / f"{safe_symbol}_{timeframe}_live.csv"
            
            # Guardar datos
            data.to_csv(filename, index=False)
            
        except Exception as e:
            self.logger.warning(f"Error guardando datos en vivo: {e}")
    
    def shutdown(self) -> None:
        """
        Cierra la conexión con MT5.
        """
        if MT5_AVAILABLE and self.connected:
            with self.connection_lock:
                mt5.shutdown()
                self.connected = False
                self.logger.info("MT5 desconectado")
    
    def __del__(self):
        """
        Asegura que la conexión se cierre al destruir el objeto.
        """
        self.shutdown()
    
    # === Métodos adicionales para facilitar el trading en vivo ===
    
    def get_recent_ohlcv_with_indicators(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Obtiene datos recientes con indicadores calculados para toma de decisiones.
        
        Args:
            symbol: Símbolo
            timeframe: Timeframe
            bars: Número de barras
        
        Returns:
            DataFrame con OHLCV e indicadores o None si falla
        """
        df = self.get_live_data(symbol, timeframe, bars)
        if df is None or len(df) < 20:  # Mínimo necesario para indicadores
            return None
        
        try:
            # Importar calculador de indicadores
            from indicators.technical_indicators import add_indicators
            
            # Añadir indicadores al DataFrame
            df_with_indicators = add_indicators(df)
            
            return df_with_indicators
            
        except Exception as e:
            self.logger.error(f"Error calculando indicadores para {symbol} {timeframe}: {e}")
            return df  # Devolver al menos los datos sin indicadores
    
    def start_data_stream(self, symbols: List[str], timeframe: str, callback=None, 
                         update_interval: int = 10) -> threading.Thread:
        """
        Inicia un stream continuo de datos en segundo plano.
        
        Args:
            symbols: Lista de símbolos
            timeframe: Timeframe
            callback: Función a llamar con nuevos datos (symbol, df)
            update_interval: Intervalo de actualización en segundos
        
        Returns:
            Thread que está ejecutando el stream
        """
        def data_stream_worker():
            while self._streaming_active:
                for symbol in symbols:
                    try:
                        df = self.get_live_data(symbol, timeframe)
                        if df is not None and callback is not None:
                            callback(symbol, df)
                    except Exception as e:
                        self.logger.error(f"Error en stream de datos para {symbol}: {e}")
                
                # Esperar hasta la próxima actualización
                time.sleep(update_interval)
        
        # Iniciar thread
        self._streaming_active = True
        stream_thread = threading.Thread(target=data_stream_worker)
        stream_thread.daemon = True
        stream_thread.start()
        
        self.logger.info(f"Stream de datos iniciado para {symbols} en {timeframe}")
        return stream_thread
    
    def stop_data_stream(self) -> None:
        """
        Detiene el stream de datos.
        """
        self._streaming_active = False
        self.logger.info("Stream de datos detenido")