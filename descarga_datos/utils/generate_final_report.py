#!/usr/bin/env python3
"""
Script para generar reporte final de comparación de modelos
Ejecutar cuando quick_candidate_test.py haya completado
"""

import json
from pathlib import Path

def generate_report():
    """Genera reporte final"""
    
    results_file = Path("data/dashboard_results/quick_comparison_20251102.json")
    
    if not results_file.exists():
        print("[ERROR] Archivo de resultados no encontrado")
        print(f"Esperado: {results_file}")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("\n" + "="*80)
    print("COMPARACION FINAL - MODELOS RANDOMFOREST")
    print("="*80)
    print()
    
    for idx, r in enumerate(results, 1):
        print(f"{idx}. {r['label']}")
        print(f"   Modelo: {r['model']}")
        print(f"   P&L: ${r['pnl']:,.2f}")
        print(f"   Trades: {r['trades']}")
        print(f"   Win Rate: {r['win_rate']:.2f}%")
        print()
    
    best = results[0]
    print(f"{'='*80}")
    print(f"GANADOR: {best['model']}")
    print(f"P&L: ${best['pnl']:,.2f}")
    print(f"{'='*80}")
    print()
    
    # Recomendación
    print("RECOMENDACION:")
    if "200051" in best['model']:
        print("  Usar RandomForest_20251102_200051.joblib (o cualquiera de 16:25→20:00)")
        print("  Son todos idénticos en validación, así que tienen igual performance")
    elif "090102" in best['model']:
        print("  Usar RandomForest_20251102_090102.joblib")
    
    print()


if __name__ == "__main__":
    generate_report()
