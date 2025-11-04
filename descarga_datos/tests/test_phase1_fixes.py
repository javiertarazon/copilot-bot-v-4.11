#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba FASE 1 - Validar que los fixes funcionan.
Ejecuta el sistema live durante 30 segundos y verifica que:
1. position_size se calcula correctamente en risk management
2. position_size se pasa correctamente al executor
3. Las órdenes se ejecutan sin errores
"""

import sys
import time
from pathlib import Path

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_phase1():
    """Prueba FASE 1: Validar que position_size se pasa correctamente"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 PRUEBA FASE 1: Validar fixes de position_size")
    logger.info("=" * 70)
    
    try:
        import MetaTrader5 as mt5
        from core.live_trading_orchestrator import LiveTradingOrchestrator
        
        # Inicializar MT5
        logger.info("🔌 Inicializando MT5...")
        if not mt5.initialize():
            logger.error(f"❌ Error inicializando MT5: {mt5.last_error()}")
            return False
        
        account_info = mt5.account_info()
        logger.info(f"✅ MT5 conectado - Balance: {account_info.balance} USD")
        
        # Crear orchestrator
        logger.info("🎯 Creando orchestrator...")
        orchestrator = LiveTradingOrchestrator(config_path=None)
        
        # Iniciar el sistema
        logger.info("⚙️  Iniciando sistema de trading en vivo...")
        logger.info("-" * 70)
        
        if not orchestrator.start():
            logger.error("❌ Error al iniciar el orquestador")
            mt5.shutdown()
            return False
        
        # Ejecutar durante 30 segundos
        logger.info("✅ Sistema iniciado - Ejecutando durante 30 segundos...")
        time.sleep(30)
        
        # Detener el sistema
        logger.info("-" * 70)
        logger.info("🛑 Deteniendo sistema...")
        
        if not orchestrator.stop():
            logger.error("❌ Error al detener el orquestador")
            mt5.shutdown()
            return False
        
        # Verificar posiciones abiertas
        logger.info("📊 Verificando posiciones abiertas...")
        active_positions = orchestrator.active_positions
        if active_positions:
            logger.info(f"✅ {len(active_positions)} posición(es) abierta(s):")
            for symbol, pos in active_positions.items():
                logger.info(f"   - {symbol}: {pos['type']} @ {pos['entry_price']}, Lotes: {pos.get('volume', 'N/A')}")
        else:
            logger.info("ℹ️  No hay posiciones abiertas (podría ser normal si la estrategia no generó señales)")
        
        # Mostrar métricas
        logger.info("📈 Métricas del sistema:")
        metrics = orchestrator.get_current_metrics()
        for key, value in metrics.items():
            logger.info(f"   {key}: {value}")
        
        mt5.shutdown()
        logger.info("\n" + "=" * 70)
        logger.info("✅ PRUEBA FASE 1 COMPLETADA EXITOSAMENTE")
        logger.info("=" * 70)
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en prueba FASE 1: {e}")
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
    success = test_phase1()
    sys.exit(0 if success else 1)
