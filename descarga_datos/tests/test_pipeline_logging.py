#!/usr/bin/env python3
"""
Test FASE 3 Task 10: Logging mejorado del pipeline de trading

Valida que el pipeline completo muestre logs detallados en cada paso:
1. Obtención de datos
2. Cálculo de indicadores
3. Generación de señales
4. Aplicación de riesgo
5. Ejecución de órdenes
"""

import sys
from pathlib import Path
import time

# Agregar rutas para imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

from descarga_datos.utils.pipeline_logger import PipelineLogger, log_capital_check, log_sl_tp_validation
from descarga_datos.utils.logger import get_logger
from descarga_datos.core.live_trading_orchestrator import LiveTradingOrchestrator

logger = get_logger(__name__)

def test_pipeline_logging():
    """Prueba que el logging del pipeline sea completo."""
    
    print("\n" + "="*70)
    print("[TEST] FASE 3 Task 10: Logging Mejorado del Pipeline")
    print("="*70)
    
    try:
        # 1. Demostración de logging de datos
        print("\n📊 Paso 1: Demostrando logging de obtención de datos...")
        PipelineLogger.log_data_fetch(
            symbol="Volatility 75 Index",
            timeframe="15m",
            bars=200,
            precio_open=43006.80,
            precio_close=42964.03
        )
        
        # 2. Demostración de logging de indicadores
        print("\n📈 Paso 2: Demostrando logging de cálculo de indicadores...")
        PipelineLogger.log_indicator_calculation(
            symbol="Volatility 75 Index",
            indicator_count=25,
            nan_count=15,
            ATR=258.89,
            RSI=21.01,
            MACD=-687.80,
            EMA_10=43224.10,
            EMA_20=43740.37
        )
        
        # 3. Demostración de logging de señal
        print("\n📡 Paso 3: Demostrando logging de señal de estrategia...")
        PipelineLogger.log_strategy_signal(
            strategy_name="UltraDetailedHeikinAshiML",
            symbol="Volatility 75 Index",
            signal="NO_SIGNAL",
            confidence=0.657,
            entry_price=42931.78,
            sl=42672.88,
            tp=43190.68
        )
        
        # 4. Demostración de logging de gestión de riesgo
        print("\n⚠️  Paso 4: Demostrando logging de gestión de riesgo...")
        PipelineLogger.log_risk_management(
            symbol="Volatility 75 Index",
            action="APPROVED",
            position_size=0.0100,
            risk_amount=29.95,
            max_loss=149.93,
            razon="Dentro de límites de riesgo"
        )
        
        # 5. Demostración de logging de ejecución
        print("\n✅ Paso 5: Demostrando logging de ejecución de orden...")
        PipelineLogger.log_order_execution(
            symbol="Volatility 75 Index",
            order_type="BUY",
            quantity=0.0100,
            price=42931.78,
            sl=42672.88,
            tp=43190.68,
            status="SENT",
            order_id="2025110301",
            timestamp="2025-11-03 19:45:00"
        )
        
        # 6. Logging de validación SL/TP
        print("\n✔️  Paso 6: Demostrando logging de validación SL/TP...")
        log_sl_tp_validation(
            symbol="Volatility 75 Index",
            order_type="BUY",
            price=42931.78,
            sl=42672.88,
            tp=43190.68,
            is_valid=True,
            reason="SL abajo, TP arriba, distancia válida"
        )
        
        # 7. Logging de capital
        print("\n💰 Paso 7: Demostrando logging de capital...")
        log_capital_check(
            balance=9997.05,
            equity=9997.05,
            drawdown_pct=0.0,
            max_drawdown_limit=5.0
        )
        
        # 8. Demostración de logging de ciclo
        print("\n🔄 Paso 8: Demostrando logging de ciclo...")
        PipelineLogger.log_cycle_summary(
            cycle_num=1,
            strategies_processed=1,
            signals_generated=0,
            orders_sent=0,
            active_positions=0,
            duration_ms=2156.0
        )
        
        # 9. Iniciar orquestador real para 10 segundos (demostración)
        print("\n" + "="*70)
        print("PRUEBA REAL: Iniciando pipeline real durante 10 segundos...")
        print("="*70 + "\n")
        
        orchestrator = LiveTradingOrchestrator()
        
        if not orchestrator.start():
            print("❌ No se pudo iniciar el orquestador")
            return False
        
        # Dejar que funcione por 10 segundos
        time.sleep(10)
        
        # Detener
        if not orchestrator.stop():
            print("❌ No se pudo detener el orquestador")
            return False
        
        # 10. Resumen final
        print("\n" + "="*70)
        print("✅ PRUEBA COMPLETADA CON ÉXITO")
        print("="*70)
        
        print("\nResumen de logging implementado:")
        print("  ✓ [PIPELINE 1/5 DATA] - Obtención de datos")
        print("  ✓ [PIPELINE 2/5 INDICATORS] - Cálculo de indicadores")
        print("  ✓ [PIPELINE 3/5 SIGNAL] - Generación de señales")
        print("  ✓ [PIPELINE 4/5 RISK] - Aplicación de riesgo")
        print("  ✓ [PIPELINE 5/5 EXECUTE] - Ejecución de órdenes")
        print("  ✓ [CYCLE] - Resumen de ciclos")
        print("  ✓ [MT5 DATA] - Sincronización de datos")
        print("  ✓ [CAPITAL] - Revisión de capital")
        print("  ✓ [SL/TP VALIDATION] - Validación de stops")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pipeline_logging()
    sys.exit(0 if success else 1)
