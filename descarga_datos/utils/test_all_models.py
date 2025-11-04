"""
Script para probar todos los modelos RandomForest guardados
y comparar cuál genera más P&L en backtest
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import shutil

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import load_config_from_yaml
from backtesting.backtester import AdvancedBacktester
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
from core.downloader import AdvancedDataDownloader
from utils.logger import setup_logger

logger = setup_logger("ModelTester", "logs/test_all_models.log")

MODELS_DIR = Path(__file__).parent.parent / "models" / "Volatility 75 Index"


async def test_model(model_path: Path, config) -> dict:
    """Test un modelo específico con backtest"""
    
    model_name = model_path.stem
    logger.info(f"\n{'='*60}")
    logger.info(f"Probando modelo: {model_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Preparar configuración para este modelo
        test_config = config.copy() if isinstance(config, dict) else config
        
        # Descargar datos si es necesario
        downloader = AdvancedDataDownloader(test_config)
        await downloader.ensure_data_availability()
        
        # Crear estrategia
        strategy = UltraDetailedHeikinAshiMLStrategy(
            name="UltraDetailedHeikinAshiML",
            config=test_config,
            model_path=str(model_path)  # ← Usar modelo específico
        )
        
        # Ejecutar backtest
        backtester = AdvancedBacktester(
            strategy=strategy,
            config=test_config,
            symbol="Volatility 75 Index"
        )
        
        logger.info(f"[{model_name}] Iniciando backtest...")
        results = await backtester.run()
        
        if results and isinstance(results, dict):
            pnl = results.get('total_pnl', 0)
            trades = results.get('total_trades', 0)
            win_rate = results.get('win_rate', 0)
            
            logger.info(f"[✓ {model_name}] P&L: ${pnl:.2f} | Trades: {trades} | Win Rate: {win_rate:.1f}%")
            
            return {
                'model': model_name,
                'model_path': str(model_path),
                'pnl': pnl,
                'trades': trades,
                'win_rate': win_rate,
                'status': 'SUCCESS',
                'error': None
            }
        else:
            logger.error(f"[✗ {model_name}] Resultados inválidos: {results}")
            return {
                'model': model_name,
                'model_path': str(model_path),
                'pnl': 0,
                'trades': 0,
                'win_rate': 0,
                'status': 'FAILED',
                'error': 'Resultados inválidos'
            }
            
    except Exception as e:
        logger.error(f"[✗ {model_name}] Error: {str(e)}", exc_info=True)
        return {
            'model': model_name,
            'model_path': str(model_path),
            'pnl': 0,
            'trades': 0,
            'win_rate': 0,
            'status': 'ERROR',
            'error': str(e)
        }
    finally:
        await downloader.close()


async def main():
    """Main - Probar todos los modelos"""
    
    logger.info("🚀 INICIANDO PRUEBA DE TODOS LOS MODELOS")
    logger.info(f"Modelos dir: {MODELS_DIR}")
    
    # Cargar configuración
    config = load_config_from_yaml(Path(__file__).parent.parent / "config" / "config.yaml")
    logger.info(f"Configuración cargada para símbolo: Volatility 75 Index")
    
    # Encontrar todos los modelos .joblib
    model_files = sorted([f for f in MODELS_DIR.glob("RandomForest_*.joblib")])
    logger.info(f"Modelos encontrados: {len(model_files)}")
    for mf in model_files:
        logger.info(f"  - {mf.name}")
    
    if not model_files:
        logger.error("❌ No se encontraron modelos RandomForest")
        return
    
    # Probar cada modelo
    results = []
    for idx, model_path in enumerate(model_files, 1):
        logger.info(f"\n[{idx}/{len(model_files)}] Probando {model_path.name}...")
        result = await test_model(model_path, config)
        results.append(result)
        
        # Pequeña pausa entre modelos
        await asyncio.sleep(1)
    
    # Mostrar resumen
    logger.info(f"\n\n{'='*80}")
    logger.info("📊 RESUMEN COMPARATIVO - TODOS LOS MODELOS")
    logger.info(f"{'='*80}\n")
    
    # Ordenar por P&L (mayor primero)
    results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    for idx, r in enumerate(results_sorted, 1):
        status_icon = "✓" if r['status'] == 'SUCCESS' else "✗"
        logger.info(
            f"{idx}. [{status_icon}] {r['model']:40s} | "
            f"P&L: ${r['pnl']:10,.2f} | "
            f"Trades: {r['trades']:5d} | "
            f"Win%: {r['win_rate']:6.1f}%"
        )
        if r['error']:
            logger.info(f"    Error: {r['error']}")
    
    # Guardar resultados
    results_file = Path(__file__).parent.parent / "data" / "model_comparison_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_models_tested': len(results),
            'results': results_sorted
        }, f, indent=2)
    
    logger.info(f"\n✅ Resultados guardados en: {results_file}")
    
    # Mostrar ganador
    best_model = results_sorted[0]
    logger.info(f"\n🏆 MODELO GANADOR:")
    logger.info(f"  Nombre: {best_model['model']}")
    logger.info(f"  P&L: ${best_model['pnl']:,.2f}")
    logger.info(f"  Trades: {best_model['trades']}")
    logger.info(f"  Win Rate: {best_model['win_rate']:.1f}%")
    logger.info(f"  Path: {best_model['model_path']}")
    
    logger.info("\n✅ Prueba de modelos completada")


if __name__ == "__main__":
    asyncio.run(main())
