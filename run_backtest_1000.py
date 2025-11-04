#!/usr/bin/env python3
"""
Script simple para ejecutar backtest con 1000 USD de capital inicial
"""

import sys
from pathlib import Path

# Agregar rutas
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

from descarga_datos.config.config_loader import load_config_from_yaml
from descarga_datos.backtesting.backtesting_orchestrator import run_backtest_orchestrator
from descarga_datos.utils.logger import setup_logging, get_logger

# Inicializar logging
setup_logging({'level': 'INFO', 'file': 'descarga_datos/logs/backtest_1000usd.log'})
logger = get_logger('backtest_1000')

print("\n" + "="*70)
print("🚀 BACKTEST CON 1000 USD DE CAPITAL INICIAL")
print("="*70 + "\n")

try:
    # 1. Cargar configuración
    logger.info("📋 Cargando configuración...")
    config = load_config_from_yaml()
    logger.info(f"✅ Configuración cargada")
    logger.info(f"   Capital inicial: {config.backtesting.initial_capital} USD")
    
    # 2. Ejecutar backtest
    logger.info("\n▶️  Ejecutando backtest...")
    results = run_backtest_orchestrator(config=config)
    
    # 4. Mostrar resultados
    print("\n" + "="*70)
    print("📊 RESULTADOS DEL BACKTEST")
    print("="*70)
    
    if results:
        if isinstance(results, dict):
            print(f"\n✅ Backtest completado exitosamente")
            print(f"\nCapital inicial: 1000 USD")
            print(f"Capital final: ${results.get('final_capital', 'N/A')}")
            print(f"PnL: ${results.get('pnl', 'N/A')}")
            print(f"Return: {results.get('return_pct', 'N/A')}%")
            print(f"Total trades: {results.get('total_trades', 0)}")
            print(f"Win rate: {results.get('win_rate', 'N/A')}%")
            print(f"Sharpe ratio: {results.get('sharpe_ratio', 'N/A')}")
            print(f"Max drawdown: {results.get('max_drawdown', 'N/A')}%")
        else:
            print(f"\n✅ Backtest completado")
            print(f"Resultado: {results}")
    else:
        print("\n❌ El backtest no retornó resultados")
    
    print("\n" + "="*70)
    print("📁 Logs guardados en: descarga_datos/logs/backtest_1000usd.log")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error durante backtest: {e}")
    import traceback
    traceback.print_exc()
    logger.error(f"Error: {e}", exc_info=True)
    sys.exit(1)
