#!/usr/bin/env python3
"""
Script automático para monitorear y mostrar resultados de la prueba de modelos
Ejecutar en otra terminal para ver progreso en tiempo real
"""

import json
import time
from pathlib import Path
from datetime import datetime

def monitor_and_show():
    """Monitorea el progreso y muestra resultados cuando estén disponibles"""
    
    print("[MONITOR] Esperando resultados de test_all_models_complete.py...")
    print("[MONITOR] Actualizando cada 30 segundos...\n")
    
    results_dir = Path("data/dashboard_results")
    last_file = None
    
    while True:
        try:
            # Buscar archivo más reciente
            comparison_files = list(results_dir.glob("all_models_comparison_*.json"))
            
            if comparison_files:
                latest_file = max(comparison_files, key=lambda p: p.stat().st_mtime)
                
                # Si es nuevo, mostrar
                if latest_file != last_file:
                    last_file = latest_file
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    
                    results = data['results']
                    total = data['total_tested']
                    failed = data['total_failed']
                    
                    print(f"\n[UPDATE {datetime.now().strftime('%H:%M:%S')}] Progreso: {len(results)}/{total}")
                    print("="*70)
                    
                    for idx, r in enumerate(results, 1):
                        model_short = r['model'].replace('RandomForest_20251102_', '').replace('.joblib', '')
                        print(
                            f"{idx}. {model_short:<20} P&L: ${r['pnl']:>10,.2f} "
                            f"Trades: {r['trades']:<6} Win%: {r['win_rate']:>6.1f}%"
                        )
                    
                    if len(results) == total:
                        print("\n[COMPLETO] Todos los modelos han sido probados!")
                        print("\nPara ver resultados detallados:")
                        print("  python utils/show_results.py")
                        break
            
            time.sleep(30)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(30)


if __name__ == "__main__":
    monitor_and_show()
