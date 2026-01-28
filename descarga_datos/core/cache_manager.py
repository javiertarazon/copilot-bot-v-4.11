"""
Caché optimizado para mejorar rendimiento y reducir llamadas redundantes.
Implementa múltiples estrategias de caché según el tipo de datos.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple
import hashlib
import pickle
import json
import os
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("CacheManager")

class MemoryCache:
    """Implementación simple de caché en memoria con TTL"""
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            # Verificar TTL (si se implementa expiración por tiempo)
            timestamp, ttl_minutes = self._timestamps.get(key, (0, 0))
            if ttl_minutes > 0:
                if (time.time() - timestamp) / 60 > ttl_minutes:
                    self.delete(key)
                    return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_minutes: int = 0) -> bool:
        try:
            self._cache[key] = value
            self._timestamps[key] = (time.time(), ttl_minutes)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo en memoria: {e}")
            return False
            
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_entries': len(self._cache),
            'keys': list(self._cache.keys())
        }

class FileCache:
    """Implementación de caché en disco usando pickle"""
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if path.exists():
            try:
                # Verificar TTL basado en modificación del archivo
                # (Aquí asumimos que si existe es válido, la lógica de expiración
                # puede ser manejada por quien llama o metadata)
                with open(path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error leyendo caché de disco {key}: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl_minutes: int = 60) -> bool:
        try:
            path = self._get_path(key)
            with open(path, 'wb') as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo caché de disco {key}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        count = len(list(self.cache_dir.glob("*.pkl")))
        return {'total_entries': count}

class CacheManager:
    """Gestor principal de caché"""
    def __init__(self):
        self.memory_cache = MemoryCache()
        self.file_cache = FileCache()
        logger.info("CacheManager inicializado")

    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """Obtiene un DataFrame con caché inteligente"""
        # Intentar memoria primero
        result = self.memory_cache.get(key)
        if result is not None:
            return result
        
        # Intentar disco
        result = self.file_cache.get(key)
        if result is not None:
            # Almacenar en memoria para acceso rápido
            self.memory_cache.set(key, result, ttl_minutes=10)
            return result
        
        return None
    
    def set_dataframe(self, key: str, df: pd.DataFrame, persist: bool = True) -> bool:
        """Almacena un DataFrame con estrategia inteligente"""
        # Siempre en memoria para acceso rápido
        memory_success = self.memory_cache.set(key, df, ttl_minutes=15)
        
        # En disco solo si se solicita persistencia
        disk_success = True
        if persist and len(df) > 100:  # Solo DataFrames grandes
            disk_success = self.file_cache.set(key, df, ttl_minutes=60)
        
        return memory_success or disk_success
    
    def get_cache_key(self, symbol: str, timeframe: str, start_date: str, end_date: str, 
                     indicators: bool = False) -> str:
        """Genera una clave de caché única"""
        key_parts = [symbol, timeframe, str(start_date), str(end_date)]
        if indicators:
            key_parts.append("indicators")
        
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas combinadas"""
        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.file_cache.get_stats()
        
        return {
            'memory_cache': memory_stats,
            'disk_cache': disk_stats,
            'total_entries': memory_stats['total_entries'] + disk_stats['total_entries']
        }
