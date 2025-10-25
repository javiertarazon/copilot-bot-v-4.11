#!/usr/bin/env python3
"""
Test de Caching de Indicadores

Valida que el sistema de cache funciona correctamente,
reduciendo CPU mediante reutilización de cálculos.
"""

import time
import logging
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.indicator_cache import (
    IndicatorCache,
    CachedIndicatorCalculator,
    get_indicator_cache,
    reset_indicator_cache
)


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_ohlcv_data(n_bars: int = 100) -> pd.DataFrame:
    """Crea datos OHLCV de prueba"""
    dates = pd.date_range(end=datetime.now(), periods=n_bars, freq='1h')
    
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(n_bars) * 2)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.randn(n_bars) * 0.5,
        'high': close_prices + np.abs(np.random.randn(n_bars) * 1.5),
        'low': close_prices - np.abs(np.random.randn(n_bars) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, n_bars)
    })
    
    return df


def expensive_indicator_calculation(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Simulación de cálculo costoso de indicador (SMA).
    Agrega latencia artificial para simular cálculos reales.
    """
    # Simular cálculo costoso
    time.sleep(0.1)  # 100ms de "cálculo"
    
    df_copy = df.copy()
    df_copy['SMA'] = df_copy['close'].rolling(window=period).mean()
    df_copy['EMA'] = df_copy['close'].ewm(span=period).mean()
    df_copy['BBU'] = df_copy['SMA'] + 2 * df_copy['close'].rolling(period).std()
    df_copy['BBL'] = df_copy['SMA'] - 2 * df_copy['close'].rolling(period).std()
    
    return df_copy


def test_basic_cache_operations():
    """Prueba 1: Operaciones básicas de cache"""
    logger.info("=" * 80)
    logger.info("PRUEBA 1: Operaciones Básicas de Cache")
    logger.info("=" * 80)
    
    cache = IndicatorCache(max_entries=10, default_ttl_seconds=10)
    df = create_sample_ohlcv_data(100)
    
    # Inicial: cache vacío
    result = cache.get("BTC/USDT", "1h", 100, ("SMA",))
    assert result is None, "Cache debe estar vacío inicialmente"
    logger.info("✓ Cache inicia vacío")
    
    # Put
    df_with_indicators = expensive_indicator_calculation(df)
    cache.put("BTC/USDT", "1h", 100, ("SMA",), df_with_indicators)
    logger.info("✓ Datos guardados en cache")
    
    # Get - debe estar disponible
    cached_result = cache.get("BTC/USDT", "1h", 100, ("SMA",))
    assert cached_result is not None, "Debe encontrar datos en cache"
    assert len(cached_result) == 100, "Debe tener 100 filas"
    logger.info("✓ Datos recuperados del cache correctamente")
    
    # Verificar independencia (no debe modificar original)
    original_cols = set(df_with_indicators.columns)
    logger.info(f"✓ Columnas originales: {original_cols}")
    
    logger.info("✅ PRUEBA 1 PASSOU\n")


def test_cache_hit_performance():
    """Prueba 2: Mejora de performance con cache hits"""
    logger.info("=" * 80)
    logger.info("PRUEBA 2: Performance de Cache Hits")
    logger.info("=" * 80)
    
    cache = IndicatorCache(max_entries=20, default_ttl_seconds=60)
    cached_calc = CachedIndicatorCalculator(
        expensive_indicator_calculation,
        cache,
        ttl_seconds=60,
        logger=logger
    )
    
    df = create_sample_ohlcv_data(100)
    
    # Primer cálculo - SIN cache
    logger.info("Cálculo 1 (sin cache)...")
    start = time.time()
    result1 = cached_calc(df, "BTC/USDT", "1h", period=20)
    time1 = time.time() - start
    logger.info(f"  Tiempo: {time1:.3f}s")
    
    # Segundo cálculo - CON cache (debe ser rápido)
    logger.info("Cálculo 2 (con cache)...")
    start = time.time()
    result2 = cached_calc(df, "BTC/USDT", "1h", period=20)
    time2 = time.time() - start
    logger.info(f"  Tiempo: {time2:.3f}s")
    
    # Verificar mejora
    improvement_ratio = time1 / time2 if time2 > 0 else float('inf')
    logger.info(f"  Mejora: {improvement_ratio:.1f}x más rápido")
    
    assert time2 < time1 / 2, f"Cache hit debe ser >50% más rápido ({time1:.3f}s → {time2:.3f}s)"
    logger.info("✓ Cache hit proporciona mejora significativa")
    
    # Verificar estadísticas
    stats = cache.get_stats()
    logger.info(f"  Hit rate: {stats['hit_rate']*100:.1f}%")
    logger.info(f"  Hits: {stats['total_hits']}, Misses: {stats['total_misses']}")
    
    assert stats['total_hits'] == 1, "Debe haber 1 hit"
    assert stats['total_misses'] == 1, "Debe haber 1 miss"
    logger.info("✅ PRUEBA 2 PASSOU\n")


def test_cache_expiration():
    """Prueba 3: Expiración de entradas en cache"""
    logger.info("=" * 80)
    logger.info("PRUEBA 3: Expiración de Cache")
    logger.info("=" * 80)
    
    # TTL corto para prueba rápida
    cache = IndicatorCache(max_entries=10, default_ttl_seconds=2)
    df = create_sample_ohlcv_data(100)
    df_with_indicators = expensive_indicator_calculation(df)
    
    # Guardar en cache
    cache.put("BTC/USDT", "1h", 100, ("SMA",), df_with_indicators)
    logger.info("✓ Datos guardados con TTL=2s")
    
    # Acceso inmediato - debe estar disponible
    result = cache.get("BTC/USDT", "1h", 100, ("SMA",))
    assert result is not None, "Debe estar disponible inmediatamente"
    logger.info("✓ Acceso inmediato: OK")
    
    # Esperar expiración
    logger.info("Esperando expiración (3 segundos)...")
    time.sleep(3)
    
    # Acceso después de expiración - debe estar vacío
    result = cache.get("BTC/USDT", "1h", 100, ("SMA",))
    assert result is None, "Debe estar expirado después de TTL"
    logger.info("✓ Entrada expirada correctamente")
    
    logger.info("✅ PRUEBA 3 PASSOU\n")


def test_cache_lru_eviction():
    """Prueba 4: LRU eviction cuando se alcanza max_entries"""
    logger.info("=" * 80)
    logger.info("PRUEBA 4: LRU Eviction")
    logger.info("=" * 80)
    
    cache = IndicatorCache(max_entries=5, default_ttl_seconds=300)
    df = create_sample_ohlcv_data(100)
    
    # Llenar cache con 5 símbolos
    logger.info("Llenando cache con 5 entradas...")
    for i in range(5):
        symbol = f"SYM{i}/USDT"
        df_copy = df.copy()
        df_copy['close'] = df_copy['close'] * (1 + i * 0.01)
        
        df_with_indicators = expensive_indicator_calculation(df_copy)
        cache.put(symbol, "1h", 100, ("SMA",), df_with_indicators)
        logger.info(f"  ✓ Entrada {i+1}/5: {symbol}")
    
    stats = cache.get_stats()
    assert stats['total_entries'] == 5, "Debe tener 5 entradas"
    logger.info(f"✓ Cache lleno: {stats['total_entries']}/{stats['max_entries']} entradas")
    
    # Agregar sexta entrada - debe desalojar la más antigua
    logger.info("Agregando sexta entrada (debe evictar)...")
    df_copy = df.copy()
    df_copy['close'] = df_copy['close'] * 1.1
    df_with_indicators = expensive_indicator_calculation(df_copy)
    
    initial_evictions = stats['total_evictions']
    cache.put("SYM5/USDT", "1h", 100, ("SMA",), df_with_indicators)
    
    stats = cache.get_stats()
    assert stats['total_entries'] == 5, "Debe mantener máx 5 entradas"
    assert stats['total_evictions'] > initial_evictions, "Debe haber ocurrido eviction"
    logger.info(f"✓ LRU eviction: total_evictions={stats['total_evictions']}")
    
    logger.info("✅ PRUEBA 4 PASSOU\n")


def test_memory_usage():
    """Prueba 5: Monitoreo de uso de memoria"""
    logger.info("=" * 80)
    logger.info("PRUEBA 5: Monitoreo de Memoria")
    logger.info("=" * 80)
    
    cache = IndicatorCache(max_entries=50, default_ttl_seconds=300)
    
    logger.info("Llenando cache con 20 entradas...")
    for i in range(20):
        symbol = f"SYM{i:02d}/USDT"
        df = create_sample_ohlcv_data(100 + i * 10)
        df_with_indicators = expensive_indicator_calculation(df)
        cache.put(symbol, "1h", len(df), ("SMA",), df_with_indicators)
    
    stats = cache.get_stats()
    
    logger.info(f"✓ Entradas en cache: {stats['total_entries']}")
    logger.info(f"✓ Memoria usada: {stats['memory_mb']:.2f} MB")
    logger.info(f"  (Bytes: {stats['memory_bytes']:,})")
    
    # Verificar que sea razonable (menos de 100 MB para 20 entradas de 100-290 filas)
    assert stats['memory_mb'] < 100, "Uso de memoria debe ser razonable"
    logger.info("✓ Uso de memoria es razonable")
    
    # Cleanup de expirados (ninguno en este caso)
    cleaned = cache.cleanup_expired()
    logger.info(f"✓ Cleanup: {cleaned} entradas eliminadas")
    
    logger.info("✅ PRUEBA 5 PASSOU\n")


def test_multiple_indicators():
    """Prueba 6: Cache con múltiples indicadores"""
    logger.info("=" * 80)
    logger.info("PRUEBA 6: Múltiples Indicadores")
    logger.info("=" * 80)
    
    cache = IndicatorCache(max_entries=20, default_ttl_seconds=300)
    df = create_sample_ohlcv_data(100)
    df_with_indicators = expensive_indicator_calculation(df)
    
    # Mismo símbolo/timeframe, diferentes indicadores
    indicators_v1 = ("SMA", "EMA")
    indicators_v2 = ("SMA", "EMA", "BBU", "BBL")
    
    # Guardar versión 1
    cache.put("BTC/USDT", "1h", 100, indicators_v1, df_with_indicators)
    logger.info("✓ Versión 1 guardada: SMA, EMA")
    
    # Guardar versión 2 (mismos datos, indicadores diferentes)
    cache.put("BTC/USDT", "1h", 100, indicators_v2, df_with_indicators)
    logger.info("✓ Versión 2 guardada: SMA, EMA, BBU, BBL")
    
    # Recuperar ambas
    result1 = cache.get("BTC/USDT", "1h", 100, indicators_v1)
    result2 = cache.get("BTC/USDT", "1h", 100, indicators_v2)
    
    assert result1 is not None, "Versión 1 debe existir"
    assert result2 is not None, "Versión 2 debe existir"
    logger.info("✓ Ambas versiones recuperadas")
    
    stats = cache.get_stats()
    logger.info(f"✓ Entradas en cache: {stats['total_entries']}")
    logger.info(f"✓ Hit rate: {stats['hit_rate']*100:.1f}%")
    
    logger.info("✅ PRUEBA 6 PASSOU\n")


def main():
    """Ejecuta todas las pruebas"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  TEST SUITE: CACHING DE INDICADORES".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    
    try:
        # Ejecutar pruebas
        test_basic_cache_operations()
        test_cache_hit_performance()
        test_cache_expiration()
        test_cache_lru_eviction()
        test_memory_usage()
        test_multiple_indicators()
        
        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 78 + "║")
        logger.info("║" + "  ✅ TODAS LAS PRUEBAS PASSOU".center(78) + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("")
        
        return 0
    
    except AssertionError as e:
        logger.error(f"\n❌ ERROR EN PRUEBA: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n❌ ERROR INESPERADO: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
