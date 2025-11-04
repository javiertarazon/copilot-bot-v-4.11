"""
Script RÁPIDO para probar modelos:
- Cada modelo ya tiene su P&L almacenado en dashboard_results/global_summary.json
- Solo necesitamos leer los últimos resultados después de cada backtest
- Y vincularlos con el timestamp del modelo
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path("models/Volatility 75 Index")
RESULTS_DIR = Path("data/dashboard_results")

MODELS = [
    ("RandomForest_20251102_090102.joblib", "09:01:02"),
    ("RandomForest_20251102_162529.joblib", "16:25:29"),
    ("RandomForest_20251102_162735.joblib", "16:27:35"),
    ("RandomForest_20251102_194413.joblib", "19:44:13"),
    ("RandomForest_20251102_195423.joblib", "19:54:23"),
    ("RandomForest_20251102_200051.joblib", "20:00:51"),
]

def extract_pnl_from_results():
    """Lee el último archivo de resultados y extrae P&L"""
    
    summary_file = RESULTS_DIR / "global_summary.json"
    if not summary_file.exists():
        return None
    
    try:
        with open(summary_file, 'r') as f:
            data = json.load(f)
            return {
                'pnl': data.get('total_pnl', 0),
                'trades': data.get('total_trades', 0),
                'win_rate': data.get('avg_win_rate', 0) * 100,  # Convertir a porcentaje
            }
    except:
        return None


def run_backtest_and_get_pnl(model_name: str, time_str: str) -> dict:
    """Ejecuta backtest y retorna P&L extraído de resultados"""
    
    print(f"\n{'='*70}")
    print(f"🧪 Modelo [{time_str}]: {model_name}")
    print(f"{'='*70}")
    
    try:
        # Ejecutar backtest
        print(f"⏱️  Ejecutando backtest...")
        result = subprocess.run(
            ["python", "main.py", "--backtest-only"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print(f"❌ Error en ejecución: {result.stderr[:200]}")
            return None
        
        # Leer resultados
        print(f"📊 Leyendo resultados...")
        pnl_data = extract_pnl_from_results()
        
        if pnl_data:
            print(f"✅ P&L: ${pnl_data['pnl']:.2f} | Trades: {pnl_data['trades']} | Win%: {pnl_data['win_rate']:.1f}%")
            return {
                'model': model_name,
                'time': time_str,
                **pnl_data,
                'status': 'SUCCESS'
            }
        else:
            print(f"⚠️ No se pudieron leer resultados")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Main"""
    
    print("🚀 PRUEBA RÁPIDA DE MODELOS")
    print(f"Modelos: {len(MODELS)}")
    
    results = []
    
    for idx, (model_name, time_str) in enumerate(MODELS, 1):
        print(f"\n[{idx}/{len(MODELS)}]")
        result = run_backtest_and_get_pnl(model_name, time_str)
        if result:
            results.append(result)
    
    # Resumen
    print(f"\n\n{'='*70}")
    print("📊 RESUMEN COMPARATIVO")
    print(f"{'='*70}\n")
    
    results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    print(f"{'Rank':<6} {'Hora':<12} {'P&L':<15} {'Trades':<10} {'Win%':<10}")
    print("-" * 70)
    
    for idx, r in enumerate(results_sorted, 1):
        print(
            f"{idx:<6} {r['time']:<12} ${r['pnl']:>13,.2f} {r['trades']:>10} "
            f"{r['win_rate']:>8.1f}%"
        )
    
    best = results_sorted[0]
    print(f"\n🏆 MEJOR MODELO: {best['model']} ({best['time']})")
    print(f"   P&L: ${best['pnl']:,.2f}")


if __name__ == "__main__":
    main()
