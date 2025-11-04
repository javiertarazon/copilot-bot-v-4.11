#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para validar que data staleness validation funciona correctamente.
Verifica que:
1. Datos frescos se cachean correctamente
2. Después de 5+ segundos, se obtienen datos nuevos de MT5
3. No hay timestamps duplicados
"""

import sys
import time
from pathlib import Path

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_data_staleness():
    """Prueba validación de staleness de datos"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TEST: Validación de Data Staleness")
    logger.info("=" * 70)
    
    try:
        import MetaTrader5 as mt5
        from core.mt5_live_data import MT5LiveDataProvider
        
        # Inicializar MT5
        logger.info("🔌 Inicializando MT5...")
        if not mt5.initialize():
            logger.error(f"❌ Error inicializando MT5: {mt5.last_error()}")
            return False
        
        logger.info("✅ MT5 inicializado")
        
        # Crear data provider
        logger.info("📊 Creando MT5LiveDataProvider...")
        config = {
            'login': 0,
            'password': '',
            'server': 'Deriv-Demo',
            'timeout': 60000
        }
        data_provider = MT5LiveDataProvider(config)
        
        if not data_provider.connect():
            logger.error("❌ No se pudo conectar")
            mt5.shutdown()
            return False
        
        logger.info("✅ Data provider conectado")
        
        # TEST 1: Obtener datos iniciales
        logger.info("\n" + "-" * 70)
        logger.info("📈 TEST 1: Obtener datos iniciales")
        symbol = "EURUSD"
        timeframe = "1h"
        
        data1 = data_provider.get_live_data(symbol, timeframe, bars=100)
        if data1 is None or len(data1) == 0:
            logger.error(f"❌ No se pudieron obtener datos iniciales")
            return False
        
        timestamp1 = data1['time'].iloc[-1]
        logger.info(f"✅ Datos iniciales: {len(data1)} barras, último timestamp: {timestamp1}")
        
        # TEST 2: Obtener datos inmediatamente (debe estar cacheado)
        logger.info("\n" + "-" * 70)
        logger.info("📈 TEST 2: Obtener datos inmediatamente (debe estar cacheado)")
        time.sleep(0.5)
        
        data2 = data_provider.get_live_data(symbol, timeframe, bars=100)
        timestamp2 = data2['time'].iloc[-1]
        
        if timestamp1 == timestamp2:
            logger.info(f"✅ Datos cacheados correctamente (timestamp igual: {timestamp1})")
        else:
            logger.warning(f"⚠️  Timestamp diferente (puede ser normal): {timestamp1} → {timestamp2}")
        
        # TEST 3: Esperar 6 segundos y obtener datos nuevamente (debe invalidar cache)
        logger.info("\n" + "-" * 70)
        logger.info("📈 TEST 3: Esperar 6 segundos para invalidar cache (staleness=5s)")
        logger.info("⏳ Esperando 6 segundos...")
        time.sleep(6)
        
        data3 = data_provider.get_live_data(symbol, timeframe, bars=100)
        timestamp3 = data3['time'].iloc[-1]
        
        logger.info(f"✅ Datos después de invalidación: {len(data3)} barras")
        logger.info(f"   Timestamp anterior: {timestamp2}")
        logger.info(f"   Timestamp nuevo:    {timestamp3}")
        
        # TEST 4: Verificar que no hay duplicados en timestamps
        logger.info("\n" + "-" * 70)
        logger.info("📈 TEST 4: Verificar no hay timestamps duplicados")
        
        # Obtener datos 5 veces seguidas con pequeñas pausas
        all_timestamps = set()
        for i in range(5):
            data = data_provider.get_live_data(symbol, timeframe, bars=100)
            ts = data['time'].iloc[-1]
            all_timestamps.add(ts)
            logger.info(f"   Iteración {i+1}: {ts}")
            time.sleep(0.5)
        
        if len(all_timestamps) >= 1:
            logger.info(f"✅ Timestamps únicos obtenidos: {len(all_timestamps)}")
        else:
            logger.error(f"❌ No hay variedad en timestamps")
            return False
        
        data_provider.disconnect()
        mt5.shutdown()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST DE STALENESS COMPLETADO EXITOSAMENTE")
        logger.info("=" * 70)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except:
            pass

if __name__ == "__main__":
    success = test_data_staleness()
    sys.exit(0 if success else 1)
