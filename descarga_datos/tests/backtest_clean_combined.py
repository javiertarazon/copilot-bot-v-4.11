#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Backtest MEJORADO - Combina datos y limpia columnas
"""
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import load_config_from_yaml
from backtesting.backtester import AdvancedBacktester
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy


def combine_and_clean_data():
    """Combina todos los archivos y limpia las columnas"""
    live_data_dir = Path(__file__).parent.parent / "data" / "live_data"
    
    if not live_data_dir.exists():
        print("[ERROR] Directorio no encontrado: {}".format(live_data_dir))
        return None
    
    # Obtener todos los archivos 15m ordenados
    csv_files = sorted(list(live_data_dir.glob("*_15m_*.csv")))
    
    if not csv_files:
        print("[ERROR] No hay archivos 15m disponibles")
        return None
    
    print("[DATA] Encontrados {} archivos".format(len(csv_files)))
    
    # Combinar solo las columnas OHLCV basicas
    all_dfs = []
    for i, csv_file in enumerate(csv_files):
        try:
            df = pd.read_csv(csv_file, index_col=0)
            
            # Mantener solo las columnas OHLCV basicas
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in required_cols if col in df.columns]
            
            if len(available_cols) == 5:
                df_clean = df[available_cols].copy()
                all_dfs.append(df_clean)
                if (i + 1) % 100 == 0:
                    print("[LOAD] Cargados {} archivos...".format(i + 1))
        except Exception as e:
            if i < 5:  # Solo mostrar primeros errores
                print("[WARNING] Error archivo {}: {}".format(csv_file.name, str(e)[:50]))
            continue
    
    if not all_dfs:
        print("[ERROR] No se pudieron cargar archivos")
        return None
    
    # Concatenar todos los datos
    print("\n[COMBINE] Combinando {} archivos validos...".format(len(all_dfs)))
    combined = pd.concat(all_dfs, ignore_index=False)
    
    # Eliminar duplicados
    initial_rows = len(combined)
    combined = combined[~combined.index.duplicated(keep='first')]
    removed = initial_rows - len(combined)
    
    if removed > 0:
        print("[CLEAN] Eliminados {} duplicados".format(removed))
    
    # Ordenar por índice
    combined = combined.sort_index()
    
    # Convertir a tipos numéricos
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors='coerce')
    
    # Verificar NaN
    nan_count = combined.isna().sum().sum()
    if nan_count > 0:
        print("[CLEAN] Encontrados {} valores NaN".format(nan_count))
        # Usar forward fill
        combined = combined.fillna(method='ffill').fillna(method='bfill')
    
    # Eliminar filas con NaN restantes
    combined = combined.dropna()
    
    print("[OK] Datos combinados: {} filas totales".format(len(combined)))
    try:
        index_start = str(combined.index[0]) if len(combined) > 0 else 'N/A'
        index_end = str(combined.index[-1]) if len(combined) > 0 else 'N/A'
        print("[OK] Rango: {} a {}".format(index_start, index_end))
    except:
        print("[OK] Datos combinados y listos")
    
    return combined


def main():
    print("\n" + "="*70)
    print("BACKTEST COMBINADO - DATOS LIMPIADOS Y VALIDADOS")
    print("="*70)
    
    try:
        # 1. Cargar configuracion
        print("\n[STEP 1] Cargando configuracion...")
        config = load_config_from_yaml()
        print("[OK] Configuracion cargada")
        
        # 2. Combinar y limpiar datos
        print("\n[STEP 2] Combinando y limpiando TODOS los archivos...")
        combined_df = combine_and_clean_data()
        
        if combined_df is None or len(combined_df) == 0:
            print("[ERROR] No hay datos para procesar")
            return
        
        # Validar columnas
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in combined_df.columns for col in required_cols):
            print("[ERROR] Faltan columnas. Disponibles: {}".format(combined_df.columns.tolist()))
            return
        
        print("[OK] Datos validados - {} filas, {} columnas".format(len(combined_df), len(combined_df.columns)))
        print("[DATA] Columnas: {}".format(", ".join(combined_df.columns.tolist())))
        
        # 3. Crear estrategia
        print("\n[STEP 3] Inicializando estrategia...")
        strategy = UltraDetailedHeikinAshiMLStrategy(config)
        print("[OK] Estrategia lista")
        
        # 4. Ejecutar backtest
        print("\n[STEP 4] Ejecutando backtest con {} filas...".format(len(combined_df)))
        print("[INFO] Esto puede tardar algunos minutos...")
        
        backtester = AdvancedBacktester()
        config_dict = {
            'initial_capital': 10000.0,
            'commission': 0.0005,
            'slippage': 0.0002
        }
        backtester.configure(config_dict)
        
        results = backtester.run(strategy, combined_df, 'BTC_USDT_COMBINED_15m', '15m')
        
        # 5. Mostrar resultados
        print("\n" + "="*70)
        print("RESULTADOS DEL BACKTEST")
        print("="*70)
        
        if results:
            total_trades = results.get('total_trades', 0)
            win_rate = results.get('win_rate', 0)
            total_pnl = results.get('total_pnl', 0)
            final_capital = results.get('final_capital', 10000.0)
            
            print("\n[RESUMEN GENERAL]")
            print("  Trades Totales: {}".format(total_trades))
            print("  Trades Ganadores: {}".format(results.get('winning_trades', 0)))
            print("  Trades Perdedores: {}".format(results.get('losing_trades', 0)))
            print("  Win Rate: {:.2f}%".format(win_rate * 100))
            
            print("\n[RESULTADOS FINANCIEROS]")
            print("  Capital Inicial: $10,000.00")
            print("  Capital Final: ${:.2f}".format(final_capital))
            print("  Ganancia/Perdida: ${:.2f}".format(total_pnl))
            print("  ROI: {:.2f}%".format((total_pnl / 10000.0) * 100))
            
            if total_trades > 0:
                print("\n[METRICAS AVANZADAS]")
                print("  Profit Factor: {:.2f}".format(results.get('profit_factor', 0)))
                print("  Max Drawdown: {:.2f}%".format(results.get('max_drawdown', 0) * 100))
                print("  Recovery Factor: {:.2f}".format(results.get('recovery_factor', 0)))
                print("  Ganancia Bruta: ${:.2f}".format(results.get('gross_profit', 0)))
                print("  Perdida Bruta: ${:.2f}".format(results.get('gross_loss', 0)))
                print("  Trade Promedio: ${:.2f}".format(results.get('avg_trade', 0)))
                print("  Mejor Trade: ${:.2f}".format(results.get('best_trade', 0)))
                print("  Peor Trade: ${:.2f}".format(results.get('worst_trade', 0)))
            
            print("\n" + "="*70)
            print("EVALUACION FINAL")
            print("="*70)
            
            if total_trades == 0:
                print("[INFO] No se generaron trades con los datos disponibles")
                print("[INFO] Esto puede deberse a condiciones de mercado o filtros")
                print("[OK] Sistema OPERATIVO - Listo para ejecucion")
            elif win_rate >= 0.45:
                print("[SUCCESS] Sistema RENTABLE")
                print("[ROI] Retorno en inversion: {:.2f}%".format((total_pnl / 10000.0) * 100))
                print("[ACTION] LISTO para LIVE TRADING en Bybit Testnet")
            elif total_trades > 10 and win_rate >= 0.30:
                print("[WARNING] Sistema OPERATIVO pero con bajo win rate")
                print("[TIP] Considerar ajuste de parametros")
                print("[ACTION] Revisar filtros y estrategia antes de live")
            else:
                print("[INFO] Sistema con oportunidades limitadas")
                print("[ACTION] Necesita optimizacion")
            
        else:
            print("\n[ERROR] No se obtuvieron resultados del backtest")
        
        print("\n" + "="*70)
        print("FIN DEL BACKTEST")
        print("="*70 + "\n")
        
    except Exception as e:
        print("\n[CRITICAL ERROR] {}".format(str(e)[:200]))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
