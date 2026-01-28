#!/usr/bin/env python3
"""
Comparative Analysis Script
Analiza XAUUSD, NAS100 y BTCUSD para determinar el mejor activo.

Periodos:
- Train: 2021-01-01 a 2022-12-31 (2 años)
- Val:   2023-01-01 a 2023-12-31 (1 año)
- Opt:   2024-01-01 a 2024-12-31 (1 año)
- Test:  2025-01-01 a 2025-12-31 (1 año)
"""
import sys
import os
import asyncio
import pandas as pd
from datetime import datetime

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
descarga_datos = os.path.join(project_root, "descarga_datos")
sys.path.insert(0, descarga_datos)
sys.path.insert(0, project_root)

from optimizacion.run_optimization_pipeline2 import OptimizationPipeline
from utils.logger import setup_logger

logger = setup_logger("comparative_analysis")

SYMBOLS_DEFAULT = ["XAUUSD", "NAS100", "BTCUSD"]
SYMBOLS = SYMBOLS_DEFAULT
if len(sys.argv) > 1:
    target = sys.argv[1].upper()
    if target in SYMBOLS_DEFAULT:
        SYMBOLS = [target]
    else:
        print(f"❌ Error: El símbolo '{target}' no es válido. Opciones: {SYMBOLS_DEFAULT}")
        sys.exit(1)

TIMEFRAME = "15m"
TRIALS = 25  # Optimización ligera para encontrar parámetros base viables

# Fechas estrictas
FECHAS = {
    "train_start": "2021-01-01",
    "train_end":   "2022-12-31",
    "val_start":   "2023-01-01",
    "val_end":     "2023-12-31",
    "opt_start":   "2024-01-01",
    "opt_end":     "2024-12-31",
    # Backtest final se hará sobre esto (implícito en el pipeline final step o manual)
    # El pipeline corre backtest final en OPT_START a OPT_END con params optimizados.
    # Pero queremos probar en UNSEEN data (2025).
    # Como OptimizationPipeline por defecto hace backtest en periodo OPT,
    # tendremos que ejecutar un backtest manual EXTRA para 2025.
    "test_start":  "2025-01-01",
    "test_end":    "2025-12-31"
}

async def run_analysis():
    results = {}
    
    print("\n" + "="*60)
    print(f"🚀 INICIANDO ANÁLISIS COMPARATIVO: {SYMBOLS}")
    print(f"📅 Periodo Total: 2021-2025")
    print("="*60 + "\n")

    for symbol in SYMBOLS:
        print(f"\n👉 Procesando: {symbol} ...")
        
        # 1. Configurar y Ejecutar Pipeline (Train -> Opt)
        pipeline = OptimizationPipeline(
            symbols=[symbol],
            timeframe=TIMEFRAME,
            train_start=FECHAS["train_start"],
            train_end=FECHAS["train_end"],
            val_start=FECHAS["val_start"],
            val_end=FECHAS["val_end"],
            opt_start=FECHAS["opt_start"],
            opt_end=FECHAS["opt_end"],
            n_trials=TRIALS
        )
        
        try:
            # Ejecuta Train ML + Optimizacion (en 2024)
            # Esto nos da los mejores parámetros encontrados en 2024
            pipeline_res = await pipeline.run_complete_pipeline()
            
            symbol_res = pipeline_res.get(symbol, {})
            opt_res = symbol_res.get("optimization_results")
            
            best_params = {}
            if opt_res and isinstance(opt_res, tuple) and opt_res[1]:
                # Extraer mejores params (máximo P&L)
                best_trial = max(opt_res[1], key=lambda t: t.values[3])
                best_params = best_trial.params
                print(f"✅ Optimización 2024 completada. Mejor P&L: ${best_trial.values[3]:.2f}")
            else:
                print(f"⚠️ Fallo en optimización o sin resultados positivos. Usando default.")
            
            # 2. Ejecutar Backtest Final en 2025 (Periodo Test INÉDITO)
            print(f"🧪 Ejecutando Backtest en TEST SET (2025) para {symbol}...")
            
            # Instanciar estrategia y correr en 2025
            from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
            from core.downloader import download_and_cache_data
            
            # Descargar datos 2025 si faltan (el pipeline bajó hasta 2024 probablemente)
            data_test = download_and_cache_data(
                symbol=symbol,
                timeframe=TIMEFRAME,
                start_date=FECHAS["test_start"],
                end_date=FECHAS["test_end"]
            )
            
            if data_test is None or data_test.empty:
                print(f"❌ Error: No hay datos para Test 2025 de {symbol}")
                metrics = {"total_pnl": -9999, "roi": -100}
            else:
                # Config con mejores params
                config_test = pipeline.config  # Base config
                # Actualizar param manager o config object si es posible, o inyectar en estrategia
                # La estrategia toma un dict o config object. Crear dict fusionado.
                import dataclasses
                if dataclasses.is_dataclass(config_test):
                    config_dict = dataclasses.asdict(config_test)
                else:
                    config_dict = dict(config_test)
                
                config_dict.update(best_params)
                
                strategy = UltraDetailedHeikinAshiMLStrategy(config=config_dict)
                backtest_res = strategy.run(data_test, symbol, TIMEFRAME)
                
                metrics = {
                    "total_pnl": backtest_res.get("total_pnl", 0),
                    "roi": backtest_res.get("return_pct", 0),
                    "win_rate": backtest_res.get("win_rate", 0),
                    "max_drawdown": backtest_res.get("max_drawdown", 0),
                    "trades": backtest_res.get("total_trades", 0),
                    "sharpe": backtest_res.get("sharpe_ratio", 0)
                }
                
                print(f"📊 Resultados 2025 {symbol}:")
                print(f"   ROI: {metrics['roi']:.2f}% | P&L: ${metrics['total_pnl']:.2f}")
                print(f"   Trades: {metrics['trades']} | WR: {metrics['win_rate']*100:.1f}%")
            
            results[symbol] = metrics
            
        except Exception as e:
            print(f"❌ Error procesando {symbol}: {e}")
            import traceback
            traceback.print_exc()
            results[symbol] = {"total_pnl": -9999, "error": str(e)}

    # Reporte Final
    print("\n" + "="*60)
    print("🏆 RANKING FINAL (Basado en P&L 2025)")
    print("="*60)
    
    sorted_symbols = sorted(results.items(), key=lambda x: x[1].get("total_pnl", -9999), reverse=True)
    
    for rank, (sym, met) in enumerate(sorted_symbols, 1):
        pnl = met.get("total_pnl", 0)
        roi = met.get("roi", 0)
        print(f"{rank}. {sym}: ${pnl:.2f} (ROI {roi:.1f}%)")
        
    winner = sorted_symbols[0][0]
    print(f"\n✅ RECOMENDACIÓN: Continuar optimización profunda con {winner}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_analysis())
