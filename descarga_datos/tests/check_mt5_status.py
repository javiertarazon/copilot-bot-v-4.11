#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar estado de MT5 y sistemas relacionados.
Ejecuta verificaciones rápidas para identificar qué está funcionando y qué no.
"""

import sys
import os
from pathlib import Path
import time

# Agregar rutas para imports
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_mt5_connection():
    """Verifica conexión a MT5"""
    logger.info("=" * 60)
    logger.info("🔍 VERIFICANDO CONEXIÓN MT5")
    logger.info("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        
        # Inicializar MT5
        initialized = mt5.initialize()
        
        if not initialized:
            logger.error(f"❌ MT5 no se inicializó. Error: {mt5.last_error()}")
            return False
        
        logger.info("✅ MT5 INICIALIZADO CORRECTAMENTE")
        
        # Obtener información de la cuenta
        account_info = mt5.account_info()
        if account_info:
            logger.info(f"✅ Información de cuenta obtenida:")
            logger.info(f"  - Número de cuenta: {account_info.login}")
            logger.info(f"  - Balance: {account_info.balance} USD")
            logger.info(f"  - Equity: {account_info.equity} USD")
            logger.info(f"  - Margen: {account_info.margin} USD")
            logger.info(f"  - Margen libre: {account_info.margin_free} USD")
            logger.info(f"  - Nivel de margen: {account_info.margin_level:.2f}%")
        else:
            logger.error(f"❌ No se pudo obtener info de cuenta. Error: {mt5.last_error()}")
            return False
        
        mt5.shutdown()
        return True
        
    except ImportError:
        logger.error("❌ MetaTrader5 no está instalado")
        logger.info("   Instala con: pip install MetaTrader5")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando MT5: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_data_provider():
    """Verifica que el proveedor de datos funciona"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 VERIFICANDO PROVEEDOR DE DATOS")
    logger.info("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        from config.config_loader import ConfigLoader
        
        config = ConfigLoader().config
        
        # Inicializar MT5
        if not mt5.initialize():
            logger.error(f"❌ MT5 no se inicializó. Error: {mt5.last_error()}")
            return False
        
        # Obtener datos para Volatility 75 Index
        symbol = "Volatility_75_Index"
        
        # Copiar últimas barras
        bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 10)
        
        if bars is not None and len(bars) > 0:
            logger.info(f"✅ DATOS OBTENIDOS para {symbol}")
            logger.info(f"Candles récibidos: {len(bars)}")
            
            # Mostrar última vela
            last_bar = bars[-1]
            logger.info(f"Última vela OHLCV:")
            logger.info(f"  - Open:  {last_bar['open']}")
            logger.info(f"  - High:  {last_bar['high']}")
            logger.info(f"  - Low:   {last_bar['low']}")
            logger.info(f"  - Close: {last_bar['close']}")
            logger.info(f"  - Volume: {last_bar['tick_volume']}")
            logger.info(f"  - Time:  {last_bar['time']}")
            
            mt5.shutdown()
            return True
        else:
            logger.error(f"❌ NO SE OBTUVIERON DATOS para {symbol}")
            logger.error(f"Error: {mt5.last_error()}")
            mt5.shutdown()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en proveedor de datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except:
            pass

def check_risk_management():
    """Verifica que el módulo de risk management funciona"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 VERIFICANDO RISK MANAGEMENT")
    logger.info("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        from risk_management.risk_management import apply_risk_management
        from config.config_loader import ConfigLoader
        
        config = ConfigLoader().config
        
        # Inicializar MT5 para obtener balance
        if not mt5.initialize():
            logger.error(f"❌ MT5 no se inicializó. Error: {mt5.last_error()}")
            return False
        
        account_info = mt5.account_info()
        if not account_info:
            logger.error("❌ No se pudo obtener info de cuenta")
            mt5.shutdown()
            return False
        
        balance = account_info.balance
        logger.info(f"Balance actual de MT5: {balance} USD")
        
        # Simular una señal
        symbol = "Volatility_75_Index"
        current_price = 2000.0
        entry_price = 2000.0
        
        test_signal = {
            'symbol': symbol,
            'signal': 'BUY',
            'entry_price': entry_price,
            'stop_loss': 1900.0,
            'take_profit': 2100.0,
            'current_price': current_price,
            'risk_per_trade': 0.02
        }
        
        # Aplicar risk management
        result_signal = apply_risk_management(test_signal, balance, config)
        
        if 'position_size' in result_signal:
            logger.info(f"✅ RISK MANAGEMENT FUNCIONANDO")
            logger.info(f"  - Position size: {result_signal['position_size']:.6f}")
            logger.info(f"  - Risk amount: {result_signal.get('risk_amount', 'N/A')} USD")
            logger.info(f"  - Risk percent: {result_signal.get('max_risk_percent', 'N/A')}%")
            
            mt5.shutdown()
            return True
        else:
            logger.error("❌ No se calculó position_size")
            mt5.shutdown()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en risk management: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except:
            pass

def check_order_executor():
    """Verifica que el executor de órdenes puede calcular lotes"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 VERIFICANDO ORDER EXECUTOR")
    logger.info("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        from core.mt5_order_executor import MT5OrderExecutor
        from config.config_loader import ConfigLoader
        
        config = ConfigLoader().config
        
        # Inicializar MT5
        if not mt5.initialize():
            logger.error(f"❌ MT5 no se inicializó. Error: {mt5.last_error()}")
            return False
        
        executor = MT5OrderExecutor(config)
        
        # Testear cálculo de lote
        symbol = "Volatility_75_Index"
        risk_percent = 2.0
        stop_distance = 100.0
        
        lot_size = executor.calculate_optimal_lot_size(symbol, risk_percent, stop_distance)
        
        logger.info(f"✅ CALCULO DE LOTES FUNCIONA")
        logger.info(f"  - Lot size calculado: {lot_size:.6f}")
        
        if lot_size > 0 and lot_size != 0.0:
            logger.info("✅ Lot size es válido (no es 0.00)")
            mt5.shutdown()
            return True
        else:
            logger.error(f"❌ Lot size INVÁLIDO: {lot_size}")
            mt5.shutdown()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en order executor: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except:
            pass

def main():
    """Ejecuta todos los chequeos"""
    logger.info("\n\n")
    logger.info("🚀 INICIANDO DIAGNÓSTICO DEL SISTEMA LIVE MT5")
    logger.info("=" * 60)
    
    checks = [
        ("Conexión MT5", check_mt5_connection),
        ("Proveedor de Datos", check_data_provider),
        ("Risk Management", check_risk_management),
        ("Order Executor", check_order_executor),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = result
            time.sleep(1)  # Pequeña pausa entre chequeos
        except Exception as e:
            logger.error(f"❌ Excepción no manejada en {check_name}: {e}")
            results[check_name] = False
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE CHEQUEOS")
    logger.info("=" * 60)
    
    for check_name, result in results.items():
        status = "✅ OK" if result else "❌ FALLO"
        logger.info(f"{status} - {check_name}")
    
    all_passed = all(results.values())
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ TODOS LOS CHEQUEOS PASARON - SISTEMA LISTO")
    else:
        logger.info("❌ ALGUNOS CHEQUEOS FALLARON - Ver errores arriba")
    logger.info("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
