#!/usr/bin/env python3
"""
Script: Entrenar modelo ML + Backtest con Parámetros BASE

Este script realiza el flujo completo:
1. Descargar datos más recientes
2. Entrenar modelo ML RandomForest con los datos
3. Ejecutar backtest con el modelo nuevo + parámetros BASE
4. Mostrar resultados y comparar con objetivo $400,000

Nota: El entrenamiento toma ~5-10 minutos
"""

import sys
import asyncio
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def train_and_backtest_with_base_params():
    """Entrena modelo y ejecuta backtest con parámetros BASE"""
    
    print("\n" + "="*80)
    print("🧠 ENTRENAMIENTO DE MODELO ML + BACKTEST CON PARÁMETROS BASE")
    print("="*80)
    
    try:
        from config.config_loader import load_config_from_yaml
        from main import train_ml_models, run_backtest
        
        print("\n[1/3] 📥 Descargando y preparando datos...")
        print("  Esto puede tomar 2-3 minutos...")
        print()
        
        # Entrenar modelos
        print("[2/3] 🧠 Entrenando modelo ML RandomForest...")
        print("  Esto puede tomar 5-10 minutos...")
        print()
        
        success = await train_ml_models()
        
        if not success:
            print("\n❌ Error durante entrenamiento de modelos ML")
            return False
        
        print("\n✅ Modelo ML entrenado exitosamente")
        
        # Cargar config para mostrar parámetros
        config = load_config_from_yaml()
        print("\n📋 Parámetros BASE que se usarán en backtest:")
        print("-" * 80)
        base_params = config.backtesting.base_parameters
        for key, value in base_params.items():
            print(f"  • {key:30s} = {value}")
        print("-" * 80)
        
        print("\n[3/3] 🏃 Ejecutando backtest con modelo nuevo + parámetros BASE...")
        print("  Esto puede tomar 2-5 minutos...")
        print()
        
        # Ejecutar backtest (esto usará el modelo recién entrenado)
        await run_backtest()
        
        print("\n" + "="*80)
        print("✅ FLUJO COMPLETADO")
        print("="*80)
        print("\n📊 Próximos pasos:")
        print("  1. Verificar P&L resultado en descarga_datos/data/dashboard_results/")
        print("  2. Si P&L >= $400,000: ✅ Sistema configurado correctamente")
        print("  3. Si P&L < $400,000: Revisar parámetros BASE en config.yaml")
        print()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Entrenamiento interrumpido por usuario")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    success = await train_and_backtest_with_base_params()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
