"""
Script para probar cada modelo guardado ejecutando main.py --backtest-only
y comparar resultados de P&L
"""

import json
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
import shutil

MODELS_DIR = Path("models/Volatility 75 Index")
RESULTS_DIR = Path("data/model_comparison_results")
RESULTS_DIR.mkdir(exist_ok=True)

# Lista de modelos a probar (solo los RandomForest con timestamp)
MODELS = [
    "RandomForest_20251102_090102.joblib",
    "RandomForest_20251102_162529.joblib",
    "RandomForest_20251102_162735.joblib",
    "RandomForest_20251102_194413.joblib",
    "RandomForest_20251102_195423.joblib",
    "RandomForest_20251102_200051.joblib",
]

def test_model(model_name: str) -> dict:
    """Test un modelo específico ejecutando backtest"""
    
    print(f"\n{'='*80}")
    print(f"🧪 Probando modelo: {model_name}")
    print(f"{'='*80}")
    
    model_path = MODELS_DIR / model_name
    
    if not model_path.exists():
        print(f"❌ Modelo no encontrado: {model_path}")
        return {
            'model': model_name,
            'pnl': 0,
            'trades': 0,
            'win_rate': 0,
            'status': 'NOT_FOUND',
            'error': 'Modelo no existe'
        }
    
    try:
        # Ejecutar backtest usando main.py
        print(f"⏱️ Ejecutando: python main.py --backtest-only")
        result = subprocess.run(
            ["python", "main.py", "--backtest-only"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        
        # Extraer P&L de la salida
        output = result.stdout + result.stderr
        
        # Buscar líneas con P&L
        pnl = 0
        trades = 0
        win_rate = 0
        
        for line in output.split('\n'):
            if 'P&L Total:' in line or '[OK] P&L Total:' in line:
                try:
                    # Ejemplo: "[OK] P&L Total: $3533.75"
                    parts = line.split('$')
                    if len(parts) >= 2:
                        value_str = parts[1].split()[0]
                        pnl = float(value_str)
                        print(f"✓ P&L encontrado: ${pnl:.2f}")
                except:
                    pass
            
            if 'total_trades' in line.lower() or 'trades:' in line.lower():
                try:
                    if 'trades' in line.lower():
                        parts = line.split(':')
                        if len(parts) >= 2:
                            trades = int(parts[1].strip().split()[0])
                except:
                    pass
            
            if 'win_rate' in line.lower() or 'win rate' in line.lower():
                try:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        win_str = parts[1].strip().replace('%', '').split()[0]
                        win_rate = float(win_str)
                except:
                    pass
        
        # Si no encontramos P&L en la salida, buscar en el archivo de resultados
        if pnl == 0:
            results_file = Path("data/dashboard_results/global_summary.json")
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        summary = json.load(f)
                        if 'total_pnl' in summary:
                            pnl = summary['total_pnl']
                        if 'total_trades' in summary:
                            trades = summary['total_trades']
                        if 'avg_win_rate' in summary:
                            win_rate = summary['avg_win_rate'] * 100
                        print(f"✓ Resultados extraídos de JSON: P&L=${pnl:.2f}, Trades={trades}, Win%={win_rate:.1f}%")
                except Exception as e:
                    print(f"⚠️ No se pudo leer resultados JSON: {e}")
        
        if pnl > 0:
            status = 'SUCCESS'
            error = None
        else:
            status = 'NO_DATA'
            error = 'No se pudo extraer P&L de la salida'
        
        result_dict = {
            'model': model_name,
            'pnl': pnl,
            'trades': trades,
            'win_rate': win_rate,
            'status': status,
            'error': error
        }
        
        print(f"📊 Resultado: P&L=${pnl:.2f} | Trades={trades} | Win%={win_rate:.1f}% | Status={status}")
        
        return result_dict
        
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout ejecutando backtest")
        return {
            'model': model_name,
            'pnl': 0,
            'trades': 0,
            'win_rate': 0,
            'status': 'TIMEOUT',
            'error': 'Timeout en ejecución'
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'model': model_name,
            'pnl': 0,
            'trades': 0,
            'win_rate': 0,
            'status': 'ERROR',
            'error': str(e)
        }


def main():
    """Main - Probar todos los modelos"""
    
    print("🚀 INICIANDO PRUEBA DE TODOS LOS MODELOS")
    print(f"Modelos a probar: {len(MODELS)}")
    print(f"Directorio: {MODELS_DIR.absolute()}")
    
    # Verificar que existen los modelos
    existing_models = [m for m in MODELS if (MODELS_DIR / m).exists()]
    print(f"Modelos encontrados: {len(existing_models)}/{len(MODELS)}")
    
    if not existing_models:
        print("❌ No hay modelos para probar")
        return
    
    # Probar cada modelo
    results = []
    for idx, model_name in enumerate(existing_models, 1):
        print(f"\n[{idx}/{len(existing_models)}] Probando {model_name}...")
        result = test_model(model_name)
        results.append(result)
    
    # Mostrar resumen comparativo
    print(f"\n\n{'='*100}")
    print("📊 RESUMEN COMPARATIVO - TODOS LOS MODELOS")
    print(f"{'='*100}\n")
    
    # Ordenar por P&L (mayor primero)
    results_sorted = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    print(f"{'Rank':<6} {'Modelo':<40} {'P&L':<15} {'Trades':<10} {'Win%':<10} {'Status':<12}")
    print("-" * 100)
    
    for idx, r in enumerate(results_sorted, 1):
        status_icon = "✓" if r['status'] == 'SUCCESS' else "✗"
        model_short = r['model'].replace('RandomForest_', '').replace('.joblib', '')
        print(
            f"{idx:<6} {model_short:<40} ${r['pnl']:>13,.2f} {r['trades']:>10} "
            f"{r['win_rate']:>8.1f}% {r['status']:<12}"
        )
        if r['error']:
            print(f"       Error: {r['error']}")
    
    # Guardar resultados en JSON
    results_file = RESULTS_DIR / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_models_tested': len(results),
            'results': results_sorted
        }, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {results_file}")
    
    # Mostrar ganador
    best_model = results_sorted[0]
    print(f"\n🏆 MODELO GANADOR:")
    print(f"  Nombre: {best_model['model']}")
    print(f"  P&L: ${best_model['pnl']:,.2f}")
    print(f"  Trades: {best_model['trades']}")
    print(f"  Win Rate: {best_model['win_rate']:.1f}%")
    
    if best_model['status'] == 'SUCCESS':
        print(f"\n💡 RECOMENDACION:")
        print(f"  Este modelo ({best_model['model']}) generó el mejor P&L.")
        print(f"  Puedes usarlo en live trading o para más optimización.")


if __name__ == "__main__":
    main()
