"""
Test rápido de los 2 modelos candidatos:
1. RandomForest_20251102_200051 (más reciente, mejor F1)
2. RandomForest_20251102_090102 (primer modelo)
"""

import json
import subprocess
import shutil
import time
from pathlib import Path

MODELS_DIR = Path("models/Volatility 75 Index")
RESULTS_DIR = Path("data/dashboard_results")
STANDARD_MODEL = MODELS_DIR / "randomforest.pkl"

CANDIDATES = [
    ("RandomForest_20251102_200051.joblib", "20:00:51 (RECOMENDADO - Mejor F1)"),
    ("RandomForest_20251102_090102.joblib", "09:01:02 (PRIMERO)"),
]

def copy_and_test(model_name: str, label: str) -> dict:
    """Copia modelo, ejecuta backtest, captura P&L"""
    
    print(f"\n[TEST] {label}")
    print("=" * 70)
    
    try:
        # Copiar modelo
        source = MODELS_DIR / model_name
        shutil.copy2(source, STANDARD_MODEL)
        print(f"[COPY] {model_name} copiado")
        
        # Ejecutar backtest
        print(f"[RUN] Ejecutando backtest (timeout: 180s)...")
        result = subprocess.run(
            ["python", "main.py", "--backtest-only"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print(f"[ERROR] Backtest retorno codigo: {result.returncode}")
            return None
        
        # Leer resultado
        summary_file = RESULTS_DIR / "global_summary.json"
        if not summary_file.exists():
            print(f"[ERROR] No existe: {summary_file}")
            return None
        
        with open(summary_file, 'r') as f:
            data = json.load(f)
            pnl = data['metrics']['total_pnl']
            trades = data['metrics']['total_trades']
            win_rate = data['metrics']['avg_win_rate']
        
        print(f"[RESULT] P&L: ${pnl:,.2f} | Trades: {trades} | Win%: {win_rate:.1f}%")
        
        return {
            'model': model_name,
            'label': label,
            'pnl': pnl,
            'trades': trades,
            'win_rate': win_rate
        }
        
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout en backtest")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def main():
    print("\n" + "="*70)
    print("[TEST] COMPARACION RAPIDA DE 2 MODELOS CANDIDATOS")
    print("="*70)
    
    results = []
    
    for model_name, label in CANDIDATES:
        result = copy_and_test(model_name, label)
        if result:
            results.append(result)
        time.sleep(1)
    
    # Resumen
    print(f"\n\n{'='*70}")
    print("[SUMMARY] RESULTADOS COMPARATIVOS")
    print("="*70)
    print()
    
    if not results:
        print("[ERROR] No se pudieron ejecutar backtests")
        return
    
    results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    for idx, r in enumerate(results_sorted, 1):
        print(f"{idx}. {r['label']:<40} P&L: ${r['pnl']:>10,.2f}")
    
    best = results_sorted[0]
    worst = results_sorted[-1]
    
    print(f"\n[WINNER] Mejor modelo: {best['model']}")
    print(f"  P&L: ${best['pnl']:,.2f}")
    print(f"  Diferencia: ${best['pnl'] - worst['pnl']:+,.2f}")
    
    # Guardar
    output_file = RESULTS_DIR / "quick_comparison_20251102.json"
    with open(output_file, 'w') as f:
        json.dump(results_sorted, f, indent=2)
    
    print(f"\n[OK] Resultados guardados en: {output_file}")


if __name__ == "__main__":
    main()
