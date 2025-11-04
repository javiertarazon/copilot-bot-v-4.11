#!/usr/bin/env python3
"""
Script DEFINITIVO: Entrenar Modelo ML + Backtest con Parámetros CORRECTOS

Los parámetros BASE actuales en config.yaml son EXACTAMENTE iguales a los 
que generaron $400,000 en BTC_USDT. Ahora necesitamos:

1. Entrenar modelo ML con estos parámetros
2. Ejecutar backtest para Volatility 75 Index
3. Validar si alcanzamos $400,000 (o cercano)
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    """Ejecución completa: entrenar + backtest"""
    
    print("\n" + "="*80)
    print("🚀 FLUJO COMPLETO: ENTRENAR ML + BACKTEST CON PARÁMETROS CORRECTOS")
    print("="*80)
    print()
    print("Parámetros utilizados: Los CORRECTOS de config_original.yaml")
    print("Símbolo: Volatility 75 Index")
    print("Período: 2025-01-01 a 2025-10-31")
    print("Timeframe: 15m")
    print()
    
    try:
        # Importar funciones
        from main import train_ml_models, run_backtest
        from config.config_loader import load_config_from_yaml
        
        # 1. Mostrar parámetros que se usarán
        print("[1/3] 📋 Verificando parámetros BASE configurados...")
        config = load_config_from_yaml()
        base_params = config.backtesting.base_parameters
        
        print("\n✅ Parámetros BASE (que generaron $400k):")
        print("-" * 80)
        for key in sorted(base_params.keys()):
            print(f"  {key:30s} = {base_params[key]}")
        print("-" * 80)
        
        # 2. Entrenar modelo
        print("\n[2/3] 🧠 Entrenando modelo ML con estos parámetros...")
        print("⏳ Tiempo estimado: 5-10 minutos\n")
        
        success = await train_ml_models()
        if not success:
            print("❌ Error en entrenamiento de modelos")
            return False
        
        print("\n✅ Modelo ML entrenado exitosamente")
        
        # 3. Ejecutar backtest
        print("\n[3/3] 🏃 Ejecutando backtest con modelo nuevo + parámetros BASE...")
        print("⏳ Tiempo estimado: 3-5 minutos\n")
        
        await run_backtest()
        
        print("\n" + "="*80)
        print("✅ EJECUCIÓN COMPLETADA")
        print("="*80)
        print("\n📊 Verifica resultados en:")
        print("  → descarga_datos/data/dashboard_results/global_summary.json")
        print("\n¿P&L >= $400,000? 🎯")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelado por usuario")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔔 NOTA: Este script entrenará modelo e hará backtest.")
    print("   Tiempo total: ~15-20 minutos")
    response = input("\n¿Continuar? (s/n): ").strip().lower()
    
    if response == 's':
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    else:
        print("Cancelado.\n")
        sys.exit(0)
