"""
Script para probar TODOS los modelos de forma secuencial
Prueba cada modelo, captura P&L, y muestra resultados en tiempo real
"""

import json
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path("models/Volatility 75 Index")
RESULTS_DIR = Path("data/dashboard_results")
STANDARD_MODEL = MODELS_DIR / "randomforest.pkl"

# Todos los modelos a probar
MODELS = [
    "RandomForest_20251102_090102.joblib",
    "RandomForest_20251102_162529.joblib",
    "RandomForest_20251102_162735.joblib",
    "RandomForest_20251102_194413.joblib",
    "RandomForest_20251102_195423.joblib",
    "RandomForest_20251102_200051.joblib",
]

def extract_pnl_from_summary():
    """Extrae P&L del archivo summary"""
    summary_file = RESULTS_DIR / "global_summary.json"
    if not summary_file.exists():
        return None
    
    try:
        with open(summary_file, 'r') as f:
            data = json.load(f)
            return {
                'pnl': data['metrics']['total_pnl'],
                'trades': data['metrics']['total_trades'],
                'win_rate': data['metrics']['avg_win_rate']
            }
    except:
        return None


def test_model(idx: int, total: int, model_name: str) -> dict:
    """Prueba un modelo individual"""
    
    print(f"\n{'='*70}")
    print(f"[{idx}/{total}] PROBANDO: {model_name}")
    print(f"{'='*70}")
    
    try:
        # Copiar modelo
        source = MODELS_DIR / model_name
        if not source.exists():
            print(f"[ERROR] Modelo no encontrado: {source}")
            return None
        
        shutil.copy2(source, STANDARD_MODEL)
        print(f"[COPY] Modelo copiado a randomforest.pkl")
        
        # Ejecutar backtest
        print(f"[RUN] Ejecutando backtest (max 180s)...")
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "main.py", "--backtest-only"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print(f"[ERROR] Backtest fallo (retorno: {result.returncode})")
            return None
        
        # Extraer P&L
        pnl_data = extract_pnl_from_summary()
        
        if pnl_data:
            print(f"[OK] Tiempo: {elapsed:.1f}s")
            print(f"[RESULT] P&L: ${pnl_data['pnl']:,.2f} | Trades: {pnl_data['trades']} | Win%: {pnl_data['win_rate']:.1f}%")
            
            return {
                'model': model_name,
                'pnl': pnl_data['pnl'],
                'trades': pnl_data['trades'],
                'win_rate': pnl_data['win_rate'],
                'time_s': elapsed,
                'status': 'SUCCESS'
            }
        else:
            print(f"[ERROR] No se pudo extraer P&L de resultados")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout (>180s)")
        return None
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None


def main():
    """Main - Probar todos los modelos"""
    
    print("\n" + "="*70)
    print("COMPARACION COMPLETA DE TODOS LOS MODELOS")
    print("="*70)
    print(f"\nModelos a probar: {len(MODELS)}")
    print(f"Duracion aproximada: {len(MODELS) * 50 / 60:.0f} minutos\n")
    
    results = []
    failed = []
    
    for idx, model_name in enumerate(MODELS, 1):
        result = test_model(idx, len(MODELS), model_name)
        
        if result:
            results.append(result)
            print(f"[TRACKER] {idx}/{len(MODELS)} completados")
        else:
            failed.append(model_name)
            print(f"[TRACKER] {model_name} FALLO")
        
        # Pausa pequeña entre backtests
        if idx < len(MODELS):
            time.sleep(2)
    
    # RESUMEN FINAL
    print(f"\n\n{'='*70}")
    print("RESUMEN FINAL - TODOS LOS MODELOS")
    print(f"{'='*70}\n")
    
    if results:
        results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
        
        print(f"{'Rank':<6} {'Modelo':<35} {'P&L':<15} {'Trades':<10} {'Win%':<10} {'Tiempo':<8}")
        print("-" * 90)
        
        for idx, r in enumerate(results_sorted, 1):
            model_short = r['model'].replace('RandomForest_20251102_', '').replace('.joblib', '')
            print(
                f"{idx:<6} {model_short:<35} ${r['pnl']:>13,.2f} {r['trades']:>10} "
                f"{r['win_rate']:>8.1f}% {r['time_s']:>7.1f}s"
            )
        
        # Ganador
        best = results_sorted[0]
        print(f"\n{'='*70}")
        print(f"GANADOR: {best['model']}")
        print(f"P&L: ${best['pnl']:,.2f}")
        print(f"Trades: {best['trades']}")
        print(f"Win Rate: {best['win_rate']:.1f}%")
        print(f"{'='*70}")
        
        # Guardar resultados
        output_file = RESULTS_DIR / f"all_models_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tested': len(results),
                'total_failed': len(failed),
                'results': results_sorted
            }, f, indent=2)
        
        print(f"\n[OK] Resultados guardados: {output_file}")
    else:
        print("[ERROR] No se pudieron completar backtests")
    
    if failed:
        print(f"\n[ERROR] Modelos fallidos ({len(failed)}):")
        for m in failed:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
