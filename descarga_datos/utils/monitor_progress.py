#!/usr/bin/env python3
"""
Monitor de progreso de test_all_models_complete.py
Ejecutar en otra terminal para ver progreso en tiempo real
"""

import json
from pathlib import Path
import time

def check_progress():
    """Verifica y muestra el progreso actual"""
    
    # Buscar el archivo más reciente de comparación
    results_dir = Path("data/dashboard_results")
    comparison_files = list(results_dir.glob("all_models_comparison_*.json"))
    
    if comparison_files:
        latest_file = max(comparison_files, key=lambda p: p.stat().st_mtime)
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            results = data['results']
            print(f"\n[PROGRESO] {len(results)}/6 modelos completados")
            print(f"{'='*70}")
            
            for idx, r in enumerate(results, 1):
                model_short = r['model'].replace('RandomForest_20251102_', '').replace('.joblib', '')
                print(f"{idx}. {model_short}: ${r['pnl']:,.2f}")
            
            if len(results) == 6:
                print(f"\n[OK] COMPLETO - Ver resultados con: python utils/show_results.py")
            
        except:
            pass


if __name__ == "__main__":
    while True:
        check_progress()
        time.sleep(60)  # Actualizar cada 60 segundos
