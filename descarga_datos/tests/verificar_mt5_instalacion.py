"""
Script para verificar la instalación de MetaTrader 5
"""
import os
import sys
from pathlib import Path

# Agregar el directorio utils al path para importar el manager
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from mt5_account_manager import MT5AccountManager

print("🔍 VERIFICANDO INSTALACIÓN DE METATRADER 5")
print("=" * 50)

manager = MT5AccountManager()
ruta_mt5 = manager.verify_installation()

if ruta_mt5:
    print(f"\n✅ MT5 INSTALADO CORRECTAMENTE")
    print(f"📁 Ruta: {ruta_mt5}")
    
    # Mostrar cuenta activa
    active_account = manager.get_active_account()
    print(f"\n🏦 CUENTA ACTIVA: {active_account['name']}")
    print(f"   Login: {active_account['login']}")
    print(f"   Servidor: {active_account['server']}")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Abrir MT5 desde la ruta encontrada")
    print(f"2. Conectar con servidor: {active_account['server']}")
    print(f"3. Usar login: {active_account['login']}")
    print(f"4. Password: {active_account['password']}")
    print("5. Habilitar AutoTrading: Tools → Options → Expert Advisors → Allow automated trading")
    print("6. Ejecutar: python tests/diagnose_simple.py")
    
    print(f"\n💡 Para cambiar cuenta: python utils/mt5_account_manager.py [icmarkets|thinkmarkets]")

print("\n" + "=" * 50)