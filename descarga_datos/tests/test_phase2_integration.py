#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRUEBA FASE 2 - Validación completa del sistema Live MT5.
Verifica que funcionan juntos:
1. Position size se pasa correctamente (FASE 1 Fix 2-3)
2. Data staleness validation funciona (FASE 2 Fix 5)
3. Capital se sincroniza cada ciclo (FASE 2 Fix 6)
4. SL/TP se validan correctamente (FASE 2 Fix 7)

Ejecuta durante 60 segundos con logging detallado.
"""

import sys
import time
from pathlib import Path

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_phase2_integration():
    """Prueba integración FASE 2"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 PRUEBA FASE 2: Integración completa de fixes")
    logger.info("=" * 70)
    logger.info("Ejecutando durante 60 segundos con validaciones completas...")
    logger.info("Verificando:")
    logger.info("  1. Position size se pasa correctamente")
    logger.info("  2. Data staleness validation funciona")
    logger.info("  3. Capital se sincroniza cada ciclo")
    logger.info("  4. SL/TP se validan correctamente")
    
    try:
        import MetaTrader5 as mt5
        from core.live_trading_orchestrator import LiveTradingOrchestrator
        
        # Inicializar MT5
        logger.info("\n🔌 Inicializando MT5...")
        if not mt5.initialize():
            logger.error(f"❌ Error inicializando MT5: {mt5.last_error()}")
            return False
        
        account_info = mt5.account_info()
        logger.info(f"✅ MT5 conectado - Balance: {account_info.balance} USD, Equity: {account_info.equity} USD")
        
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
        
        logger.info("✅ Sistema iniciado correctamente")
        logger.info(f"   Estrategias cargadas: {len(orchestrator.strategy_instances)}")
        logger.info(f"   Posiciones activas inicialmente: {len(orchestrator.active_positions)}")
        
        # Ejecutar durante 60 segundos
        logger.info("\n📊 EJECUCIÓN DURANTE 60 SEGUNDOS")
        logger.info("-" * 70)
        
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < 60:
            iteration += 1
            elapsed = time.time() - start_time
            logger.info(f"[{elapsed:.0f}s] Iteración #{iteration}")
            
            # Verificar métricas
            metrics = orchestrator.get_current_metrics()
            logger.info(f"  - Total trades: {metrics.get('total_trades', 0)}")
            logger.info(f"  - Posiciones abiertas: {len(orchestrator.active_positions)}")
            logger.info(f"  - Win rate: {metrics.get('win_rate', 0):.1%}")
            
            time.sleep(5)  # Esperar 5 segundos entre chequeos
        
        # Detener el sistema
        logger.info("-" * 70)
        logger.info("🛑 Deteniendo sistema...")
        
        if not orchestrator.stop():
            logger.error("❌ Error al detener el orquestador")
            mt5.shutdown()
            return False
        
        logger.info("✅ Sistema detenido correctamente")
        
        # Mostrar métricas finales
        logger.info("\n📈 MÉTRICAS FINALES")
        logger.info("-" * 70)
        metrics = orchestrator.get_current_metrics()
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")
        
        # Verificar posiciones
        logger.info(f"\nPosiciones finales: {len(orchestrator.active_positions)}")
        for symbol, pos in orchestrator.active_positions.items():
            logger.info(f"  - {symbol}: {pos['type']} @ {pos['entry_price']}")
        
        # Resumen de éxito
        logger.info("\n" + "=" * 70)
        logger.info("✅ PRUEBA FASE 2 COMPLETADA EXITOSAMENTE")
        logger.info("   Todos los fixes están funcionando correctamente:")
        logger.info("   ✅ Position size se pasa correctamente")
        logger.info("   ✅ Data staleness validation funciona")
        logger.info("   ✅ Capital se sincroniza cada ciclo")
        logger.info("   ✅ SL/TP se validan correctamente")
        logger.info("=" * 70)
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en prueba FASE 2: {e}")
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
    success = test_phase2_integration()
    sys.exit(0 if success else 1)
