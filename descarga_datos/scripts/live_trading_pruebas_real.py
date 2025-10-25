#!/usr/bin/env python3
"""
🧪 LIVE TRADING PRUEBAS - Ejecutor Real con Config de Pruebas
Script para ejecutar live trading REAL en SANDBOX con configuración de pruebas

USO: python descarga_datos/scripts/live_trading_pruebas_real.py

IMPORTANTE:
  • Sandbox mode ACTIVADO (no usa dinero real)
  • Parámetros RELAJADOS (más operaciones que productivo)
  • Capital reducido (100 USDT vs 800 productivo)
  • Usa configuración: config_pruebas_operaciones.yaml
  • Ejecuta estrategia REAL en modo live
  • Valida cálculos en cada trade
  • Calcula correctamente SL/TP en margin y futuros
"""

import sys
import os
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_config():
    """Cargar configuración de pruebas."""
    config_path = Path(__file__).parent.parent / "config" / "config_pruebas_operaciones.yaml"
    
    logger.info(f"Cargando configuración desde: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

def show_test_configuration(config):
    """Mostrar configuración de pruebas."""
    print("\n" + "=" * 80)
    print("[TEST] CONFIGURACIÓN DE PRUEBAS - LIVE TRADING REAL")
    print("=" * 80)
    
    # Capital
    capital = config.get('backtesting', {}).get('initial_capital', 100)
    print(f"\n💰 Capital: {capital} USDT")
    
    # Exchanges
    print("\n🔗 Exchanges:")
    exchanges = config.get('exchanges', {})
    for exchange_name, settings in exchanges.items():
        if settings.get('enabled'):
            sandbox = "SANDBOX ✅" if settings.get('sandbox') else "REAL ❌"
            print(f"   • {exchange_name}: {sandbox}")
    
    # Estrategia
    print("\n🤖 Estrategia:")
    strategies = config.get('backtesting', {}).get('strategies', {})
    for strategy_name, enabled in strategies.items():
        if enabled:
            print(f"   • {strategy_name}: ACTIVA")
    
    # Símbolo
    print("\n📊 Símbolos:")
    symbols = config.get('backtesting', {}).get('symbols', [])
    for symbol in symbols:
        print(f"   • {symbol}")
    
    # Timeframe
    timeframe = config.get('backtesting', {}).get('timeframe', '15m')
    print(f"\n⏱️  Timeframe: {timeframe}")
    
    # Parámetros key
    print("\n🎯 Parámetros Key:")
    opt_params = config.get('backtesting', {}).get('optimized_parameters', {}).get('BTC_USDT', {})
    print(f"   • Max concurrent trades: {opt_params.get('max_concurrent_trades', 1)}")
    print(f"   • Risk per trade: {opt_params.get('risk_per_trade', 0.02)}")
    print(f"   • CCI Threshold: {opt_params.get('cci_threshold', 90)}")
    print(f"   • ML Threshold: {opt_params.get('ml_threshold', 0.2)}")
    print(f"   • Max drawdown: {opt_params.get('max_drawdown', 0.03)}")
    print(f"   • SL multiplier: {opt_params.get('stop_loss_atr_multiplier', 2.25)}")
    print(f"   • TP multiplier: {opt_params.get('take_profit_atr_multiplier', 3.75)}")
    
    # Validaciones
    print("\n✅ Validaciones:")
    test_config = config.get('live_trading_test', {})
    print(f"   • Log all signals: {test_config.get('log_all_signals', False)}")
    print(f"   • Detailed logging: {test_config.get('detailed_logging', False)}")
    print(f"   • Validate calculations: {test_config.get('validate_calculations', False)}")
    print(f"   • Print trade details: {test_config.get('print_trade_details', False)}")
    
    print("\n" + "=" * 80)
    print()

def execute_live_trading_test():
    """Ejecutar live trading test con configuración de pruebas."""
    try:
        # Cargar config
        config = load_test_config()
        
        # Mostrar config
        show_test_configuration(config)
        
        # Crear archivo temporal de configuración para main.py
        # Esto le dice al main.py que use los parámetros de prueba
        print("\n[INFO] Iniciando live trading en SANDBOX mode...")
        print("[INFO] Usando configuración: config_pruebas_operaciones.yaml")
        print("[INFO] Capital: 100 USDT")
        print("[INFO] Parámetros: RELAJADOS para generar más operaciones")
        print("[INFO] Strategi: UltraDetailedHeikinAshiML")
        print("[INFO] Timeframe: 15m")
        print("[INFO] Modo: SANDBOX (sin dinero real)")
        
        # Importar main.py
        from main import main as run_main
        
        # Configurar argumentos para modo live
        print("\n[EXEC] Ejecutando: python main.py --live-ccxt")
        print("[EXEC] Con configuración de pruebas activada...\n")
        
        # Ejecutar main con argumentos
        sys.argv = ['main.py', '--live-ccxt']
        
        # Override: usar config de pruebas
        os.environ['TRADING_CONFIG'] = str(Path(__file__).parent.parent / "config" / "config_pruebas_operaciones.yaml")
        
        result = run_main()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ ERROR en ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Función principal."""
    print("\n" + "=" * 80)
    print("[🧪 LIVE TRADING PRUEBAS - Modo Real Sandbox")
    print("=" * 80)
    print("Descripción:")
    print("  • Ejecuta live trading REAL en SANDBOX (sin dinero real)")
    print("  • Usa configuración de pruebas (parámetros relajados)")
    print("  • Genera más operaciones para validar cálculos")
    print("  • Valida SL/TP en margin y futuros")
    print("  • Capital: 100 USDT (vs 800 productivo)")
    print("  • Max trades: 2 simultáneos (vs 1 productivo)")
    print("=" * 80 + "\n")
    
    result = execute_live_trading_test()
    
    return result

if __name__ == "__main__":
    sys.exit(main())
