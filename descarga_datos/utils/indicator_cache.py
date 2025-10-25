#!/usr/bin/env python3
"""
Módulo de Caching de Indicadores - Optimización de CPU

Proporciona un sistema de cache eficiente para indicadores técnicos,
evitando recálculos innecesarios y reduciendo consumo de CPU.
"""

import hashlib
import logging
import pickle
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np


class IndicatorCacheEntry:
    """Entrada individual en el cache"""
    
    def __init__(self, data: pd.DataFrame, timestamp: datetime = None, ttl_seconds: int = 300):
        """
        Args:
            data: DataFrame con indicadores calculados
            timestamp: Timestamp de creación (default: ahora)
            ttl_seconds: Time To Live en segundos (default: 5 min)
        """
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.ttl_seconds = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0
    
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def get_age_seconds(self) -> float:
        """Obtener edad de la entrada en segundos"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def mark_hit(self):
        """Marcar como acceso exitoso"""
        self.hit_count += 1
    
    def mark_miss(self):
        """Marcar como acceso fallido"""
        self.miss_count += 1
    
    def get_hit_rate(self) -> float:
        """Obtener hit rate (0.0 a 1.0)"""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total


class IndicatorCache:
    """
    Cache de indicadores técnicos con LRU eviction.
    
    Reduce recálculos de indicadores al mantener en memoria
    los resultados de cálculos recientes. Útil para trading
    donde se procesan múltiples símbolos/timeframes repetidamente.
    """
    
    def __init__(
        self,
        max_entries: int = 100,
        default_ttl_seconds: int = 300,
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            max_entries: Máximo número de entradas en cache
            default_ttl_seconds: TTL default para nuevas entradas
            logger: Logger personalizado (opcional)
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl_seconds
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache dictionary: key -> IndicatorCacheEntry
        self.cache: Dict[str, IndicatorCacheEntry] = {}
        
        # Métricas
        self.total_hits = 0
        self.total_misses = 0
        self.total_evictions = 0
    
    def _generate_key(self, symbol: str, timeframe: str, bars: int, indicator_names: Tuple[str, ...]) -> str:
        """
        Genera una clave única para una combinación de parámetros.
        
        Args:
            symbol: Símbolo del par
            timeframe: Timeframe
            bars: Número de barras
            indicator_names: Nombres de indicadores (sorted tuple)
            
        Returns:
            Clave hash única
        """
        # Crear un string con todos los parámetros
        key_str = f"{symbol}|{timeframe}|{bars}|{','.join(sorted(indicator_names))}"
        # Usar hash para clave corta y eficiente
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _evict_lru(self):
        """Elimina la entrada menos recientemente usada (LRU eviction)"""
        if len(self.cache) == 0:
            return
        
        # Encontrar la entrada con el timestamp más antiguo o expirada
        oldest_key = None
        oldest_time = None
        
        for key, entry in self.cache.items():
            if entry.is_expired():
                oldest_key = key
                break
            
            if oldest_time is None or entry.timestamp < oldest_time:
                oldest_time = entry.timestamp
                oldest_key = key
        
        if oldest_key:
            age = self.cache[oldest_key].get_age_seconds()
            self.logger.debug(
                f"Cache LRU eviction: {oldest_key} (age: {age:.1f}s)"
            )
            del self.cache[oldest_key]
            self.total_evictions += 1
    
    def get(
        self,
        symbol: str,
        timeframe: str,
        bars: int,
        indicator_names: Tuple[str, ...],
        data_hash: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene indicadores del cache.
        
        Args:
            symbol: Símbolo del par
            timeframe: Timeframe
            bars: Número de barras
            indicator_names: Nombres de indicadores
            data_hash: Hash opcional de los datos OHLCV para validación
            
        Returns:
            DataFrame con indicadores si existe y es válido, None si no
        """
        key = self._generate_key(symbol, timeframe, bars, indicator_names)
        
        if key not in self.cache:
            self.total_misses += 1
            return None
        
        entry = self.cache[key]
        
        # Verificar si ha expirado
        if entry.is_expired():
            self.logger.debug(f"Cache miss (expired): {key}")
            del self.cache[key]
            self.total_misses += 1
            return None
        
        # Hit
        entry.mark_hit()
        self.total_hits += 1
        
        self.logger.debug(
            f"Cache hit: {key} (age: {entry.get_age_seconds():.1f}s, "
            f"hits: {entry.hit_count})"
        )
        
        return entry.data.copy()
    
    def put(
        self,
        symbol: str,
        timeframe: str,
        bars: int,
        indicator_names: Tuple[str, ...],
        data: pd.DataFrame,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Almacena indicadores en el cache.
        
        Args:
            symbol: Símbolo del par
            timeframe: Timeframe
            bars: Número de barras
            indicator_names: Nombres de indicadores
            data: DataFrame con indicadores
            ttl_seconds: TTL override (optional)
        """
        key = self._generate_key(symbol, timeframe, bars, indicator_names)
        
        # Aplicar LRU eviction si necesario
        if len(self.cache) >= self.max_entries:
            self._evict_lru()
        
        # Crear entrada
        ttl = ttl_seconds or self.default_ttl
        entry = IndicatorCacheEntry(data.copy(), ttl_seconds=ttl)
        
        self.cache[key] = entry
        
        self.logger.debug(
            f"Cache put: {key} ({len(data)} rows, TTL: {ttl}s)"
        )
    
    def clear(self):
        """Limpia todo el cache"""
        count = len(self.cache)
        self.cache.clear()
        self.logger.info(f"Cache cleared ({count} entries)")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del cache.
        
        Returns:
            Dict con métricas de uso
        """
        total_requests = self.total_hits + self.total_misses
        hit_rate = (
            self.total_hits / total_requests 
            if total_requests > 0 
            else 0.0
        )
        
        # Calcular memoria aproximada
        memory_bytes = 0
        for entry in self.cache.values():
            if isinstance(entry.data, pd.DataFrame):
                memory_bytes += entry.data.memory_usage(deep=True).sum()
        
        return {
            "total_entries": len(self.cache),
            "max_entries": self.max_entries,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "hit_rate": hit_rate,
            "total_evictions": self.total_evictions,
            "memory_bytes": memory_bytes,
            "memory_mb": memory_bytes / (1024 * 1024)
        }
    
    def cleanup_expired(self) -> int:
        """
        Elimina todas las entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.logger.debug(f"Cleanup: removed {len(expired_keys)} expired entries")
        
        return len(expired_keys)


class CachedIndicatorCalculator:
    """
    Wrapper para cálculos de indicadores con caching automático.
    
    Integración simple: reemplaza llamadas a funciones de indicadores
    con versiones cacheadas.
    """
    
    def __init__(
        self,
        indicator_func,
        cache: IndicatorCache,
        ttl_seconds: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            indicator_func: Función que calcula indicadores
            cache: Instancia de IndicatorCache
            ttl_seconds: TTL para esta función (optional)
            logger: Logger (optional)
        """
        self.indicator_func = indicator_func
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.logger = logger or logging.getLogger(__name__)
    
    def __call__(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        *args,
        **kwargs
    ) -> pd.DataFrame:
        """
        Calcula indicadores con caching.
        
        Args:
            df: DataFrame OHLCV
            symbol: Símbolo del par
            timeframe: Timeframe
            *args, **kwargs: Argumentos adicionales para indicator_func
            
        Returns:
            DataFrame con indicadores
        """
        bars = len(df)
        indicator_name = (self.indicator_func.__name__,)  # Tuple de nombres
        
        # Intentar obtener del cache
        cached = self.cache.get(symbol, timeframe, bars, indicator_name)
        if cached is not None:
            return cached
        
        # Calcular indicadores
        result = self.indicator_func(df, *args, **kwargs)
        
        # Guardar en cache
        self.cache.put(
            symbol, timeframe, bars, indicator_name,
            result, ttl_seconds=self.ttl_seconds
        )
        
        return result


# Singleton global de cache
_global_cache: Optional[IndicatorCache] = None


def get_indicator_cache(
    max_entries: int = 100,
    default_ttl: int = 300,
    logger: Optional[logging.Logger] = None
) -> IndicatorCache:
    """
    Obtiene o crea la instancia global de cache.
    
    Args:
        max_entries: Máximo de entradas (solo si se crea nueva)
        default_ttl: TTL default (solo si se crea nueva)
        logger: Logger personalizado
        
    Returns:
        Instancia de IndicatorCache
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = IndicatorCache(
            max_entries=max_entries,
            default_ttl_seconds=default_ttl,
            logger=logger
        )
    
    return _global_cache


def reset_indicator_cache():
    """Resetea la instancia global de cache"""
    global _global_cache
    if _global_cache:
        _global_cache.clear()
    _global_cache = None
