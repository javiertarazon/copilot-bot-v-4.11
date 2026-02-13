#!/usr/bin/env python3
"""
Test Rápido - Simple Bridge EA
Verifica solo conexión básica
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simple_bridge_executor import SimpleBridgeExecutor


def main():
    print("\n" + "="*60)
    print("  TEST RÁPIDO - SIMPLE BRIDGE EA")
    print("="*60)
    
    # Verificar directorios
    mt5_common = Path(os.getenv('APPDATA')).parent / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
    
    print(f"\n📁 Directorio MT5 Common: {mt5_common}")
    print(f"   Existe: {mt5_common.exists()}")
    
    command_dir = mt5_common / 'Bot_Commands'
    response_dir = mt5_common / 'Bot_Responses'
    
    print(f"\n📂 Directorios de comunicación:")
    print(f"   Comandos: {command_dir} - Existe: {command_dir.exists()}")
    print(f"   Respuestas: {response_dir} - Existe: {response_dir.exists()}")
    
    # Crear executor
    print("\n🔌 Creando Simple Bridge Executor...")
    executor = SimpleBridgeExecutor({})
    
    # Intentar conectar
    print("\n🔗 Intentando conectar con EA...")
    print("   (Asegúrate de que Simple_Bridge_EA.ex5 esté ejecutándose en MT5)")
    
    connected = executor.connect()
    
    if connected:
        print("\n✅ CONEXIÓN EXITOSA!")
        print("   El EA está respondiendo correctamente")
        
        # Test básico de account info
        print("\n📊 Probando obtener información de cuenta...")
        account = executor.get_account_info()
        
        if account:
            print(f"   Balance: ${account.get('balance', 0):,.2f}")
            print(f"   Equity: ${account.get('equity', 0):,.2f}")
            print(f"   Servidor: {account.get('server', 'N/A')}")
            print("\n✅ TODAS LAS PRUEBAS BÁSICAS PASARON")
        else:
            print("   ⚠️ No se pudo obtener información de cuenta")
        
        executor.disconnect()
    else:
        print("\n❌ NO SE PUDO CONECTAR")
        print("\n📝 PASOS PARA SOLUCIONAR:")
        print("   1. Abre MetaTrader 5")
        print("   2. Abre MetaEditor (F4 o menú Herramientas)")
        print("   3. Busca Simple_Bridge_EA.mq5 en Experts")
        print("   4. Presiona F7 para compilar")
        print("   5. Arrastra Simple_Bridge_EA.ex5 a un gráfico")
        print("   6. Acepta AutoTrading cuando pregunte")
        print("   7. Ejecuta este test nuevamente")
        
        # Verificar si hay status file
        status_file = mt5_common / 'Bot_Status.txt'
        if status_file.exists():
            print(f"\n   ℹ️ Archivo de estado encontrado: {status_file}")
            with open(status_file, 'r') as f:
                print(f"   Contenido:")
                for line in f:
                    print(f"      {line.strip()}")
        else:
            print(f"\n   ⚠️ No se encontró archivo de estado - EA probablemente no está ejecutándose")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
