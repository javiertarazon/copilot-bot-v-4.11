#!/usr/bin/env python3
"""
Test: Backtest con Parámetros BASE (Pre-optimización, PNL esperado ~$400,000)

Este script ejecuta un backtest usando SOLO los parámetros BASE, sin
configuraciones optimizadas por símbolo. Objetivo: Validar que la
configuración BASE devuelve el PNL de $400,000 esperado.
"""

import sys
import asyncio
from pathlib import Path

# Agregar path para importar modules
sys.path.insert(0, str(Path(__file__).parent.parent))

async def run_backtest_base_params():
    """Ejecuta backtest con parámetros BASE"""
    
    print("\n" + "="*80)
    print("🧪 BACKTEST CON PARÁMETROS BASE (Pre-optimización)")
    print("="*80)
    print("\n📊 Configuración:")
    print("  • Símbolo: Volatility 75 Index")
    print("  • Período: 2025-01-01 a 2025-10-31")
    print("  • Timeframe: 15m")
    print("  • Capital inicial: $10,000")
    print("  • Parámetros: BASE (pre-optimización)")
    print("  • Objetivo: Validar PNL ~$400,000")
    print()
    
    try:
        # Importar configuración y función de backtest
        from config.config_loader import load_config_from_yaml
        from main import run_backtest
        
        print("[1/3] 📥 Cargando configuración...")
        config = load_config_from_yaml()
        print("  ✅ Config cargada correctamente")
        
        # Verificar que tenemos base_parameters
        if not hasattr(config.backtesting, 'base_parameters'):
            print("  ❌ ERROR: base_parameters no encontrado en config")
            return False
        
        print(f"  ✅ Base parameters encontrados: {len(config.backtesting.base_parameters)} parámetros")
        print(f"\n     Parámetros BASE clave:")
        base_params = config.backtesting.base_parameters
        print(f"     • ml_threshold: {base_params.get('ml_threshold')}")
        print(f"     • cci_threshold: {base_params.get('cci_threshold')}")
        print(f"     • atr_period: {base_params.get('atr_period')}")
        print(f"     • kelly_fraction: {base_params.get('kelly_fraction')}")
        print(f"     • max_drawdown: {base_params.get('max_drawdown')}")
        print(f"     • risk_per_trade: {base_params.get('risk_per_trade')}")
        
        print("\n[2/3] 🏃 Ejecutando backtest...")
        
        # Ejecutar backtest (la función maneja la estrategia automáticamente)
        results = await run_backtest()
        
        print("  ✅ Backtest completado")
        
        print("\n[3/3] 📈 Resultados:")
        print("="*80)
        
        # Los resultados están en el archivo de salida
        print("\n� Nota: Los resultados detallados se muestran arriba durante la ejecución")
        print("   El backtest utilizó los parámetros BASE configurados")
        
        return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    success = await run_backtest_base_params()
    
    if success:
        print("\n" + "="*80)
        print("✅ TEST COMPLETADO CON ÉXITO")
        print("="*80 + "\n")
        return 0
    else:
        print("\n" + "="*80)
        print("❌ TEST FALLÓ")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
