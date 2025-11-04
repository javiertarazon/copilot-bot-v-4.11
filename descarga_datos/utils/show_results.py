#!/usr/bin/env python3
"""
Script para mostrar los resultados de la comparación de modelos
Ejecutar DESPUÉS de que test_all_models_complete.py haya terminado
"""

import json
from pathlib import Path
from datetime import datetime

def show_results():
    """Muestra los resultados en formato legible"""
    
    results_dir = Path("data/dashboard_results")
    
    # Buscar el archivo más reciente de comparación
    comparison_files = list(results_dir.glob("all_models_comparison_*.json"))
    
    if not comparison_files:
        print("[ERROR] No hay archivos de comparación disponibles")
        print("Por favor, ejecuta primero: python utils/test_all_models_complete.py")
        return
    
    # Usar el más reciente
    latest_file = max(comparison_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    results = data['results']
    
    print("\n" + "="*100)
    print("RESULTADOS FINALES - COMPARACION DE TODOS LOS MODELOS")
    print("="*100)
    print(f"\nTotal probados: {data['total_tested']}")
    if data['total_failed'] > 0:
        print(f"Fallidos: {data['total_failed']}")
    print(f"Timestamp: {data['timestamp']}\n")
    
    print(f"{'Rank':<6} {'Timestamp':<20} {'P&L':<15} {'Trades':<10} {'Win%':<10} {'Tiempo':<8}")
    print("-" * 100)
    
    for idx, r in enumerate(results, 1):
        timestamp = r['model'].replace('RandomForest_', '').replace('.joblib', '')
        print(
            f"{idx:<6} {timestamp:<20} ${r['pnl']:>13,.2f} {r['trades']:>10} "
            f"{r['win_rate']:>8.1f}% {r['time_s']:>7.1f}s"
        )
    
    # Resumen estadístico
    print("\n" + "="*100)
    print("ESTADISTICAS")
    print("="*100)
    
    best = results[0]
    worst = results[-1]
    avg_pnl = sum(r['pnl'] for r in results) / len(results)
    
    print(f"\nMEJOR MODELO:")
    print(f"  Nombre: {best['model']}")
    print(f"  P&L: ${best['pnl']:,.2f}")
    print(f"  Trades: {best['trades']}")
    print(f"  Win Rate: {best['win_rate']:.2f}%")
    
    print(f"\nPEOR MODELO:")
    print(f"  Nombre: {worst['model']}")
    print(f"  P&L: ${worst['pnl']:,.2f}")
    
    print(f"\nPROMEDIO:")
    print(f"  P&L Promedio: ${avg_pnl:,.2f}")
    print(f"  Diferencia (Mejor - Promedio): ${best['pnl'] - avg_pnl:+,.2f}")
    
    # Recomendación
    print(f"\n" + "="*100)
    print("RECOMENDACION")
    print("="*100)
    
    if best['pnl'] > avg_pnl * 1.05:
        print(f"\n✓ USAR: {best['model']}")
        print(f"  Genera ${best['pnl'] - avg_pnl:,.2f} MAS que el promedio")
    else:
        print(f"\n⚠️ NOTA: Todos los modelos tienen rendimiento similar")
        print(f"  Diferencia maxima: ${best['pnl'] - worst['pnl']:,.2f}")
        print(f"  Desviacion: {((best['pnl'] - worst['pnl']) / avg_pnl * 100):.1f}%")
    
    print()


if __name__ == "__main__":
    show_results()
