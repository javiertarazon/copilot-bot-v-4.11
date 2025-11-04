"""
Script ÓPTIMO para comparar modelos:
1. Copia cada modelo al nombre estándar (randomforest.pkl)
2. Ejecuta main.py --backtest-only
3. Captura P&L del resultado
4. Compara todos
"""

import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import time

MODELS_DIR = Path("models/Volatility 75 Index")
RESULTS_DIR = Path("data/dashboard_results")

MODELS = [
    "RandomForest_20251102_090102.joblib",
    "RandomForest_20251102_162529.joblib",
    "RandomForest_20251102_162735.joblib",
    "RandomForest_20251102_194413.joblib",
    "RandomForest_20251102_195423.joblib",
    "RandomForest_20251102_200051.joblib",
]

# El modelo estándar que carga el sistema
STANDARD_MODEL = MODELS_DIR / "randomforest.pkl"

def copy_model_to_standard(source_model: str):
    """Copia un modelo al nombre estándar para que lo cargue el sistema"""
    source = MODELS_DIR / source_model
    
    # Respaldar el anterior si existe
    if STANDARD_MODEL.exists():
        backup = MODELS_DIR / f"randomforest_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        shutil.copy2(STANDARD_MODEL, backup)
    
    # Copiar nuevo modelo
    shutil.copy2(source, STANDARD_MODEL)
    print(f"[COPY] Modelo copiado: {source_model} -> randomforest.pkl")


def run_backtest() -> dict:
    """Ejecuta un backtest y retorna P&L"""
    
    try:
        print(f"  [RUN] Ejecutando backtest...")
        result = subprocess.run(
            ["python", "main.py", "--backtest-only"],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            print(f"  [ERROR] Error en ejecucion")
            return None
        
        # Extraer P&L de la salida
        output = result.stdout + result.stderr
        
        pnl = 0
        trades = 0
        win_rate = 0
        
        # Buscar en la salida
        for line in output.split('\n'):
            if 'P&L Total:' in line or '[OK] P&L Total:' in line:
                try:
                    parts = line.split('$')
                    if len(parts) >= 2:
                        value_str = parts[1].split()[0]
                        pnl = float(value_str)
                except:
                    pass
            
            if '[BACKTEST]' in line and 'P&L:' in line:
                try:
                    # Ejemplo: "[BACKTEST] UltraDetailedHeikinAshiML: 7659 trades | P&L: $3533.75"
                    if '$' in line:
                        parts = line.split('$')
                        value_str = parts[-1].split()[0]
                        pnl = float(value_str)
                except:
                    pass
            
            if 'Trades:' in line and 'Win Rate:' in line:
                try:
                    # Ejemplo: "Trades: 7659, P&L: $3533.75, Compensaciones: 0"
                    parts = line.split(',')
                    for part in parts:
                        if 'Trades:' in part:
                            trades = int(part.split(':')[1].strip())
                        if 'Win Rate:' in part:
                            win_str = part.split(':')[1].strip().replace('%', '')
                            win_rate = float(win_str)
                except:
                    pass
        
        # Si no encontramos en salida, leer JSON
        if pnl == 0:
            summary_file = RESULTS_DIR / "global_summary.json"
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        data = json.load(f)
                        pnl = data.get('total_pnl', 0)
                        trades = data.get('total_trades', 0)
                        win_rate = data.get('avg_win_rate', 0) * 100
                except:
                    pass
        
        return {
            'pnl': pnl,
            'trades': trades,
            'win_rate': win_rate
        }
        
    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Timeout")
        return None
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return None


def main():
    """Main"""
    
    print("\n" + "="*80)
    print("[TEST] COMPARACION RAPIDA DE TODOS LOS MODELOS")
    print("="*80)
    print(f"\nModelos a probar: {len(MODELS)}")
    print(f"Directorio: {MODELS_DIR.absolute()}\n")
    
    results = []
    
    for idx, model_name in enumerate(MODELS, 1):
        print(f"\n[{idx}/{len(MODELS)}] {model_name}")
        
        try:
            # Copiar modelo
            copy_model_to_standard(model_name)
            
            # Ejecutar backtest
            backtest_result = run_backtest()
            
            if backtest_result:
                print(f"  [OK] P&L: ${backtest_result['pnl']:,.2f} | "
                      f"Trades: {backtest_result['trades']} | "
                      f"Win%: {backtest_result['win_rate']:.1f}%")
                results.append({
                    'model': model_name,
                    'pnl': backtest_result['pnl'],
                    'trades': backtest_result['trades'],
                    'win_rate': backtest_result['win_rate']
                })
            else:
                print(f"  [ERROR] No se pudo ejecutar backtest")
            
            # Pequeña pausa entre backtests
            time.sleep(2)
            
        except Exception as e:
            print(f"  [ERROR] Error: {e}")
    
    # Resumen
    print(f"\n\n{'='*80}")
    print("[SUMMARY] RESUMEN COMPARATIVO - TODOS LOS MODELOS")
    print(f"{'='*80}\n")
    
    if not results:
        print("[ERROR] No se pudieron ejecutar backtests")
        return
    
    results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    print(f"{'Rank':<6} {'Modelo':<45} {'P&L':<15} {'Trades':<10} {'Win%':<10}")
    print("-" * 80)
    
    for idx, r in enumerate(results_sorted, 1):
        model_short = r['model'].replace('RandomForest_20251102_', '').replace('.joblib', '')
        print(
            f"{idx:<6} {model_short:<45} ${r['pnl']:>13,.2f} {r['trades']:>10} "
            f"{r['win_rate']:>8.1f}%"
        )
    
    # Mostrar ganador
    best = results_sorted[0]
    print(f"\n{'='*80}")
    print(f"[WINNER] MODELO GANADOR")
    print(f"{'='*80}")
    print(f"Nombre: {best['model']}")
    print(f"P&L: ${best['pnl']:,.2f}")
    print(f"Trades: {best['trades']}")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    print(f"\nVentaja sobre 2do lugar: ${best['pnl'] - results_sorted[1]['pnl']:,.2f}")
    
    # Guardar resultados
    output_file = RESULTS_DIR / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_models': len(results),
            'results': results_sorted
        }, f, indent=2)
    
    print(f"\n[OK] Comparacion completa. Resultados guardados en:")
    print(f"   {output_file}")


if __name__ == "__main__":
    main()
