#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimizador de estrategia UltraDetailedHeikinAshi con Optuna
===========================================================

Este script usa Optuna para optimizar los parámetros de la estrategia
UltraDetailedHeikinAshi buscando maximizar el profit factor, minimizar
el drawdown y maximizar el win rate.

Utiliza optimización con múltiples objetivos (Pareto front).
"""

import sys
import os
# Añadir el directorio padre (descarga_datos) al path para importar módulos
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
import pandas as pd
import numpy as np
try:
    import optuna  # type: ignore
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None
from datetime import datetime
from pathlib import Path
import json
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
from typing import Dict, List, Tuple

from config.config_loader import load_config_from_yaml
from core.downloader import AdvancedDataDownloader
from indicators.technical_indicators import TechnicalIndicators
from utils.logger import setup_logger

logger = setup_logger(__name__)

class StrategyOptimizer:
    def __init__(self, 
                 symbol="BTC/USDT", 
                 timeframe="4h", 
                 start_date="2022-01-01", 
                 end_date="2023-12-31",
                 n_trials=100,
                 study_name="ultra_detailed_heikin_ashi",
                 config=None,
                 optimization_targets=None):
        """
        Inicializa el optimizador de estrategia.
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.n_trials = n_trials
        self.study_name = study_name
        self.config = config if config is not None else load_config_from_yaml()
        self.data = None
        
        # Targets de optimización configurables - OBJETIVOS ESPECÍFICOS: ROI +5% y WIN_RATE > 80%
        self.optimization_targets = optimization_targets or {
            'maximize': ['total_pnl', 'win_rate', 'pnl_return'],
            'minimize': ['max_drawdown'],
            'constraints': {
                'min_trades': 50,  # Más trades para mayor robustez
                'max_drawdown_limit': 0.08,  # Máximo 8% drawdown
                'min_win_rate': 0.80,  # WIN_RATE > 80% (objetivo principal)
                'min_pnl_return': 352.79  # ROI +5% sobre baseline (335.99% + 5%)
            }
        }
        
        # Carpeta para guardar resultados
        self.results_dir = Path(__file__).parent.parent / "data" / "optimization_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Inicializando optimización para {symbol} en {timeframe}")
        logger.info(f"Targets de optimización: {self.optimization_targets}")
        
    def download_data(self):
        """Carga los datos históricos para optimización desde SQLite directamente (bypass DataStorage)"""
        logger.info(f"Cargando datos para {self.symbol}...")

        try:
            # Ruta a la base de datos
            db_path = Path(__file__).parent.parent / "data" / "data.db"
            logger.info(f"DB Path: {db_path} (Exists: {db_path.exists()})")
            
            if not db_path.exists():
                raise FileNotFoundError(f"DB no encontrada en {db_path}")

            # Construir nombre de tabla
            table_name = f"{self.symbol.replace('/', '_')}_{self.timeframe}"
            logger.info(f"Buscando tabla: {table_name}")
            
            # Cargar directamente con sqlite3 + pandas
            import sqlite3
            with sqlite3.connect(str(db_path)) as conn:
                # Verificar si existe tabla
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    logger.error(f"Tabla {table_name} no existe en {db_path}")
                    # Listar tablas disponibles para debug
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Tablas disponibles: {tables}")
                    raise ValueError(f"Tabla {table_name} no encontrada")
                
                # Cargar datos
                query = f"SELECT * FROM {table_name}"
                logger.info(f"Ejecutando query: {query}")
                df = pd.read_sql_query(query, conn)
            
            if df is None or df.empty:
                logger.warning(f"Tabla {table_name} vacía")
                raise ValueError("Tabla vacía")
                
            logger.info(f'✅ Datos SQLite cargados: {len(df)} registros')
            
            # Manejar timestamps corruptos (todos 1)
            # Si el std dev de timestamp es 0, son todos iguales -> corruptos
            timestamp_ok = False
            if 'timestamp' in df.columns:
                if df['timestamp'].nunique() <= 1:
                     logger.warning("⚠️ Timestamps corruptos detectados (todos iguales/vacíos). Generando índice sintético.")
                     timestamp_ok = False
                else:
                     timestamp_ok = True
            
            if not timestamp_ok:
                # Generar índice sintético basado en start_date
                start_dt = pd.Timestamp(self.start_date)
                # Parse timeframe interval
                freq_map = {'15m': '15min', '1h': '1h', '4h': '4h', '1d': '1D'}
                freq = freq_map.get(self.timeframe, '15min') # Default 15min
                
                logger.info(f"Generando timestamps sintéticos desde {start_dt} con freq={freq}")
                df.index = pd.date_range(start=start_dt, periods=len(df), freq=freq)
                df['timestamp'] = df.index
            else:
                # Convertir timestamp normal
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df = df.set_index('timestamp').sort_index()

            self.data = df
            logger.info(f"Datos finalizados: {len(self.data)} registros")
            return self.data

        except Exception as e:
            logger.error(f"Error CRÍTICO cargando datos: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Fallo carga de datos: {e}")
    
    def prepare_indicators(self):
        """Prepara los indicadores técnicos utilizando la clase TechnicalIndicators centralizada"""
        if self.data is None:
            self.download_data()

        logger.info("🔧 Usando método centralizado de indicadores técnicos")
        
        # Importar método centralizado
        from indicators.technical_indicators import TechnicalIndicators
        
        # Crear instancia y calcular todos los indicadores
        indicators = TechnicalIndicators()
        df = indicators.calculate_all_indicators_unified(self.data)
        
        # Debug: Verificar NaNs
        nan_counts = df.isna().sum()
        cols_with_nans = nan_counts[nan_counts > 0]
        if not cols_with_nans.empty:
            logger.warning(f"Columnas con NaN antes de limpieza: {cols_with_nans.to_dict()}")
            # Si alguna columna tiene TODOS NaN, la eliminamos para no perder todas las filas
            all_nan_cols = nan_counts[nan_counts == len(df)].index
            if len(all_nan_cols) > 0:
                logger.warning(f"🗑️ Eliminando columnas FULL NaN: {list(all_nan_cols)}")
                df = df.drop(columns=all_nan_cols)
        
        # Limpiar NaN de forma segura
        # Primero forward fill, luego backward fill (para el inicio), luego 0
        df = df.ffill().bfill().fillna(0)
        
        self.data = df
        logger.info(f"✅ Indicadores calculados: {len(df)} filas válidas")

        return self.data
    
    def objective(self, trial):
        """
        Función objetivo para Optuna que devuelve tres métricas:
        - Profit Factor (a maximizar)
        - Max Drawdown (a minimizar)
        - Win Rate (a maximizar)
        """
        # Definir espacio de parámetros CRYPTO-OPTIMIZED
        params = {
            # Parámetros ML - Optimización para Crash/Volatilidad
            # Rango ajustado para Crash 300: 0.35 - 0.55
            "ml_threshold_min": trial.suggest_float("ml_threshold_min", 0.35, 0.55, step=0.01),
            "ml_threshold": trial.suggest_float("ml_threshold", 0.40, 0.60, step=0.02),
            
            # Parámetros de indicadores - Rango amplio para encontrar sweet spot
            "stoch_overbought": trial.suggest_int("stoch_overbought", 60, 90, step=5),
            "stoch_oversold": trial.suggest_int("stoch_oversold", 10, 40, step=5),
            "cci_threshold": trial.suggest_int("cci_threshold", 50, 250, step=10),
            "volume_ratio_min": trial.suggest_float("volume_ratio_min", 0.0, 1.0, step=0.1), # Permitir 0.0 para ignorar
            
            # Parámetros RSI (Críticos para Crash)
            "rsi_overbought": trial.suggest_int("rsi_overbought", 55, 85, step=5),
            "rsi_oversold": trial.suggest_int("rsi_oversold", 15, 45, step=5),

            # Parámetros SAR
            "sar_acceleration": trial.suggest_float("sar_acceleration", 0.02, 0.30, step=0.01),
            "sar_maximum": trial.suggest_float("sar_maximum", 0.10, 0.35, step=0.01),
            
            # Parámetros ATR
            "atr_period": trial.suggest_int("atr_period", 7, 21, step=1),
            "stop_loss_atr_multiplier": trial.suggest_float("stop_loss_atr_multiplier", 1.5, 5.0, step=0.25),
            "take_profit_atr_multiplier": trial.suggest_float("take_profit_atr_multiplier", 2.0, 8.0, step=0.25),
            
            # Parámetros EMA
            "ema_trend_period": trial.suggest_int("ema_trend_period", 15, 120, step=5),
            
            # Filtros de Volumen
            "volume_threshold": trial.suggest_categorical("volume_threshold", [0]), 
            
            # Parámetros de gestión de riesgo
            "max_drawdown": trial.suggest_float("max_drawdown", 0.03, 0.20, step=0.01),
            "max_portfolio_heat": trial.suggest_float("max_portfolio_heat", 0.08, 0.25, step=0.01),
            "max_concurrent_trades": trial.suggest_int("max_concurrent_trades", 3, 15),
            "kelly_fraction": trial.suggest_float("kelly_fraction", 0.25, 0.80, step=0.05),
        }
        
        # Crear instancia de la estrategia con los parámetros a optimizar
        strategy = UltraDetailedHeikinAshiMLStrategy(config=params)

        # ACTIVAR MODO OPTIMIZACIÓN para evitar re-entrenamiento ML en cada trial
        strategy._optimization_mode = True

        # Ejecutar la estrategia
        # IMPORTANTE: Asegurar que se usen los datos cargados previamente
        if self.data is None:  # Safety check
             self.download_data()
        
        results = strategy.run(self.data, self.symbol, self.timeframe)

        
        # Obtener constraints de configuración
        constraints = self.optimization_targets.get('constraints', {})
        min_trades = constraints.get('min_trades', 20)
        max_dd_limit = constraints.get('max_drawdown_limit', 0.15)
        min_wr = constraints.get('min_win_rate', 0.55)
        
        # Si no cumple constraints, penalizar fuertemente
        if results["total_trades"] < min_trades:
            logger.warning(f"Trial penalizado: solo {results['total_trades']} trades (mínimo {min_trades})")
            return tuple([0.0] * 4)  # Devolver 4 valores para multi-objetivo
        
        # Extraer métricas
        profit_factor = results["profit_factor"] if results["profit_factor"] != float("inf") else 10.0
        max_drawdown = abs(results["max_drawdown"])
        win_rate = results["winning_trades"] / results["total_trades"] if results["total_trades"] > 0 else 0.0
        total_pnl = results.get("total_pnl", 0.0)
        pnl_return = results.get("return_pct", 0.0)
        sharpe_ratio = results.get("sharpe_ratio", 0.0)
        
        # Aplicar constraints configurables
        penalty = 1.0
        
        if max_drawdown > max_dd_limit:
            penalty *= 0.1  # Penalización más fuerte para drawdown > 15%
            logger.warning(f"Trial penalizado: DD {max_drawdown:.2%} > límite {max_dd_limit:.2%}")
        
        if win_rate < min_wr:
            penalty *= 0.7
            logger.warning(f"Trial penalizado: WR {win_rate:.2%} < mínimo {min_wr:.2%}")
        
        max_pnl_limit = constraints.get('max_pnl_limit', float('inf'))
        if total_pnl > max_pnl_limit:
            penalty *= 0.5
            logger.warning(f"Trial penalizado: P&L {total_pnl:.2f} > límite {max_pnl_limit:.2f}")
        
        # Construir retorno basado en targets configurados
        maximize_targets = self.optimization_targets.get('maximize', ['total_pnl', 'win_rate'])
        minimize_targets = self.optimization_targets.get('minimize', ['max_drawdown'])
        
        # Mapeo de métricas
        metrics_map = {
            'total_pnl': total_pnl * penalty,
            'win_rate': win_rate * penalty,
            'profit_factor': profit_factor * penalty,
            'sharpe_ratio': sharpe_ratio * penalty,
            'pnl_return': pnl_return * penalty
        }
        
        minimize_map = {
            'max_drawdown': -max_drawdown  # Negativo para minimizar
        }
        
        # Construir tupla de retorno (máximo 4 objetivos para Optuna)
        objectives = []
        for target in maximize_targets[:3]:  # Máximo 3 para maximizar
            objectives.append(metrics_map.get(target, 0.0))
        
        for target in minimize_targets[:1]:  # Máximo 1 para minimizar
            objectives.append(minimize_map.get(target, 0.0))
        
        # Asegurar que siempre devolvemos 4 valores
        while len(objectives) < 4:
            objectives.append(0.0)
        
        return tuple(objectives[:4])
    
    def run_optimization(self):
        """Ejecuta el proceso de optimización"""
        if not OPTUNA_AVAILABLE:
            logger.error("Optuna no está disponible. Instale optuna con: pip install optuna")
            raise ImportError("Optuna es requerido para la optimización. Instale con: pip install optuna")

        logger.info("Preparando datos para optimización...")
        self.prepare_indicators()

        logger.info(f"Iniciando optimización con {self.n_trials} pruebas")

        # Crear estudio multi-objetivo
        study = optuna.create_study(
            study_name=self.study_name,
            directions=["maximize", "maximize", "maximize", "maximize"],  # PF, -DD, WR, P&L
            sampler=optuna.samplers.TPESampler(seed=42)
        )

        # Ejecutar optimización
        study.optimize(self.objective, n_trials=self.n_trials)

        # Obtener mejores trials del frente de Pareto
        pareto_trials = study.best_trials

        # Guardar resultados
        self.save_results(study, pareto_trials)

        return study, pareto_trials
    
    def save_results(self, study, pareto_trials):
        """Guarda los resultados de la optimización"""
        # Crear directorio para este estudio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        study_dir = self.results_dir / f"{self.study_name}_{self.symbol.replace('/', '_')}_{timestamp}"
        study_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Guardando resultados en: {study_dir}")
        
        # Verificar que el directorio existe
        if not study_dir.exists():
            logger.error(f"No se pudo crear el directorio: {study_dir}")
            return
        
        # Guardar los trials de Pareto
        pareto_results = []
        for trial in pareto_trials:
            pareto_results.append({
                "trial_id": trial.number,
                "params": trial.params,
                "values": {
                    "profit_factor": trial.values[0],
                    "max_drawdown": -trial.values[1],  # Deshacer la negación
                    "win_rate": trial.values[2],
                    "total_pnl": trial.values[3]  # Nuevo: P&L total
                }
            })
        
        # Guardar en JSON
        with open(study_dir / "optimization_results.json", "w") as f:
            json.dump(pareto_results, f, indent=2)
            
        # Guardar informe resumen
        with open(study_dir / "optimization_report.md", "w") as f:
            f.write(f"# Reporte de Optimización para {self.symbol}\n\n")
            f.write(f"- **Timeframe:** {self.timeframe}\n")
            f.write(f"- **Periodo:** {self.start_date} a {self.end_date}\n")
            f.write(f"- **Pruebas realizadas:** {self.n_trials}\n\n")
            
            f.write("## Mejores Resultados (Frente Pareto)\n\n")
            
            for i, res in enumerate(pareto_results):
                f.write(f"### Solución {i+1}\n")
                f.write(f"- Profit Factor: {res['values']['profit_factor']:.2f}\n")
                f.write(f"- Max Drawdown: {res['values']['max_drawdown']*100:.2f}%\n")
                f.write(f"- Win Rate: {res['values']['win_rate']*100:.2f}%\n")
                f.write(f"- P&L Total: ${res['values']['total_pnl']:.2f}\n\n")
                f.write("Parámetros:\n```\n")
                for param, value in res["params"].items():
                    f.write(f"{param}: {value}\n")
                f.write("```\n\n")
                
        # Guardar mejores parámetros filtrados por objetivos REALISTAS
        filtered_results = []
        for res in pareto_results:
            # Filtrar según objetivos realistas basados en datos disponibles: 
            # PF > 0.15, DD 0.3%-2%, WR > 50%, P&L > 0.01%
            if (res["values"]["profit_factor"] > 0.15 and 
                res["values"]["max_drawdown"] >= 0.003 and res["values"]["max_drawdown"] <= 0.02 and 
                res["values"]["win_rate"] > 0.5 and
                res["values"]["total_pnl"] > 0.0001):
                filtered_results.append(res)
                
        # Si hay resultados filtrados, guardarlos
        if filtered_results:
            with open(study_dir / "filtered_results.json", "w") as f:
                json.dump(filtered_results, f, indent=2)
                
            # Guardar en informe separado
            with open(study_dir / "filtered_report.md", "w") as f:
                f.write(f"# Configuraciones Óptimas Filtradas para {self.symbol}\n\n")
                f.write("Criterios aplicados (ajustados a datos disponibles):\n")
                f.write("- Profit Factor > 0.15\n")
                f.write("- Max Drawdown entre 0.3% y 2%\n")
                f.write("- Win Rate > 50%\n")
                f.write("- P&L Total > 0.01%\n\n")
                
                for i, res in enumerate(filtered_results):
                    f.write(f"## Configuración {i+1}\n")
                    f.write(f"- Profit Factor: {res['values']['profit_factor']:.2f}\n")
                    f.write(f"- Max Drawdown: {res['values']['max_drawdown']*100:.2f}%\n")
                    f.write(f"- Win Rate: {res['values']['win_rate']*100:.2f}%\n")
                    f.write(f"- P&L Total: ${res['values']['total_pnl']:.2f}\n\n")
                    f.write("Parámetros:\n```\n")
                    for param, value in res["params"].items():
                        f.write(f"{param}: {value}\n")
                    f.write("```\n\n")
        
        logger.info(f"Resultados guardados en {study_dir}")
        
    def plot_optimization_results(self, study):
        """Genera gráficas de visualización de la optimización"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            study_dir = self.results_dir / f"{self.study_name}_{self.symbol.replace('/', '_')}_{timestamp}"
            study_dir.mkdir(parents=True, exist_ok=True)
            
            # Graficar frente de Pareto
            # fig = plot_pareto_front(study)
            # fig.write_html(str(study_dir / "pareto_front.html"))
            
            # Graficar importancia de parámetros
            # fig = plot_param_importances(study)
            # fig.write_html(str(study_dir / "param_importance.html"))
            
            logger.info(f"Gráficas guardadas en {study_dir}")
        except Exception as e:
            logger.error(f"Error al generar gráficas: {e}")

def main():
    """Función principal"""
    import argparse
    parser = argparse.ArgumentParser(description="Optimizador de estrategia UltraDetailedHeikinAshi")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Símbolo a optimizar")
    parser.add_argument("--timeframe", type=str, default="4h", help="Timeframe a usar")
    parser.add_argument("--start", type=str, default="2022-01-01", help="Fecha inicial")
    parser.add_argument("--end", type=str, default="2022-12-31", help="Fecha final")
    parser.add_argument("--trials", type=int, default=50, help="Número de pruebas")
    
    import sys
    print("INICIANDO OPTIMIZACION...", flush=True)
    
    args = parser.parse_args()
    
    optimizer = StrategyOptimizer(
        symbol=args.symbol,
        timeframe=args.timeframe,
        start_date=args.start,
        end_date=args.end,
        n_trials=args.trials
    )
    
    study, pareto_trials = optimizer.run_optimization()
    optimizer.plot_optimization_results(study)
    
    # Mostrar el mejor resultado según profit factor
    best_pf = max(pareto_trials, key=lambda t: t.values[0])
    print(f"\n Mejor resultado por profit factor:")
    print(f"- Profit Factor: {best_pf.values[0]:.2f}")
    print(f"- Max Drawdown: {-best_pf.values[1]*100:.2f}%")
    print(f"- Win Rate: {best_pf.values[2]*100:.2f}%")
    print("\nParámetros:")
    for param, value in best_pf.params.items():
        print(f"  {param}: {value}")

if __name__ == "__main__":
    main()
