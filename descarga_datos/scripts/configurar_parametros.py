#!/usr/bin/env python3
"""
Script: Configurar Parámetros BASE Manualmente + Entrenar + Backtest

Este script permite:
1. Reemplazar los parámetros BASE en config.yaml con valores nuevos
2. Entrenar modelo ML con esos parámetros
3. Ejecutar backtest
4. Mostrar resultados
"""

import sys
import json
from pathlib import Path

def show_current_parameters():
    """Muestra parámetros BASE actuales"""
    print("\n" + "="*80)
    print("📋 PARÁMETROS BASE ACTUALES")
    print("="*80 + "\n")
    
    try:
        from config.config_loader import load_config_from_yaml
        config = load_config_from_yaml()
        
        if not hasattr(config.backtesting, 'base_parameters'):
            print("❌ base_parameters no encontrado")
            return None
        
        params = config.backtesting.base_parameters
        print(f"{'Parámetro':<35} {'Valor Actual':<20}")
        print("-" * 80)
        for key in sorted(params.keys()):
            print(f"{key:<35} {str(params[key]):<20}")
        
        return params
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def update_parameters():
    """Permite al usuario actualizar parámetros"""
    print("\n" + "="*80)
    print("✏️  ACTUALIZAR PARÁMETROS BASE")
    print("="*80 + "\n")
    
    current = show_current_parameters()
    if current is None:
        return False
    
    print("\n💡 Opción 1: Actualizar valores específicos (ingresa parámetro)")
    print("   Ejemplo: ml_threshold")
    print("   O presiona ENTER para usar valores actuales\n")
    
    # Para este ejemplo, voy a permitir actualizar alguns parámetros clave
    key_params = [
        'ml_threshold',
        'cci_threshold', 
        'atr_period',
        'kelly_fraction',
        'max_drawdown',
        'risk_per_trade'
    ]
    
    new_params = dict(current)  # Copiar actuales
    
    print("📝 Valores a actualizar (deja en blanco para mantener actual):\n")
    
    for param in key_params:
        current_val = current.get(param, "")
        user_input = input(f"  {param} [{current_val}]: ").strip()
        
        if user_input:
            try:
                # Intentar convertir a número
                if '.' in user_input:
                    new_params[param] = float(user_input)
                else:
                    new_params[param] = int(user_input) if user_input.isdigit() else user_input
                print(f"    ✅ {param} = {new_params[param]}")
            except:
                print(f"    ❌ Valor inválido, mantiene {current_val}")
                new_params[param] = current_val
    
    # Actualizar config.yaml
    try:
        import yaml
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Actualizar base_parameters
        config_data['backtesting']['base_parameters'] = new_params
        
        # Guardar
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        print("\n✅ config.yaml actualizado correctamente")
        return True
    except Exception as e:
        print(f"\n❌ Error actualizando config.yaml: {e}")
        return False

def main():
    """Función principal"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    print("\n" + "="*80)
    print("🔧 CONFIGURADOR DE PARÁMETROS BASE + ENTRENAR + BACKTEST")
    print("="*80)
    print("\n¿Qué deseas hacer?\n")
    print("  1. Ver parámetros BASE actuales")
    print("  2. Actualizar parámetros BASE")
    print("  3. Entrenar modelo ML + Ejecutar backtest")
    print("  4. Salir\n")
    
    choice = input("Selecciona opción (1-4): ").strip()
    
    if choice == "1":
        show_current_parameters()
    elif choice == "2":
        if update_parameters():
            print("\n💡 Próximo paso: Ejecutar opción 3 para entrenar y hacer backtest")
    elif choice == "3":
        print("\n⏳ Esto tomará ~15-20 minutos...")
        import asyncio
        from main import train_ml_models, run_backtest
        
        async def train_and_backtest():
            print("\n[1/2] 🧠 Entrenando modelo ML...")
            success = await train_ml_models()
            if success:
                print("\n[2/2] 🏃 Ejecutando backtest...")
                await run_backtest()
                print("\n✅ Completo. Revisa resultados en:")
                print("   descarga_datos/data/dashboard_results/")
        
        try:
            asyncio.run(train_and_backtest())
        except KeyboardInterrupt:
            print("\n\n⚠️ Cancelado por usuario")
    elif choice == "4":
        print("\nSaliendo...\n")
    else:
        print("\n❌ Opción inválida\n")

if __name__ == "__main__":
    main()
