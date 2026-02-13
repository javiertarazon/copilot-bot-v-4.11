#!/usr/bin/env python3
"""
Script de Verificación Post-Compilación
Ejecuta este script DESPUÉS de recompilar el EA
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("\n" + "="*70)
    print("  VERIFICACIÓN POST-COMPILACIÓN")
    print("="*70)
    
    # Verificar archivo .ex5
    ex5_path = Path(r"C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Simple_Bridge_EA.ex5")
    
    print(f"\n📝 Verificando archivo compilado...")
    print(f"   Ruta: {ex5_path}")
    
    if ex5_path.exists():
        mtime = datetime.fromtimestamp(ex5_path.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        print(f"   ✅ Archivo existe")
        print(f"   📅 Compilado: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ⏱️  Hace: {age:.0f} segundos")
        
        if age < 60:
            print(f"   ✅ Archivo recién compilado")
        elif age < 300:
            print(f"   ⚠️  Archivo tiene {age/60:.1f} minutos")
        else:
            print(f"   ❌ Archivo muy antiguo - Recompila nuevamente")
            return False
    else:
        print(f"   ❌ Archivo NO existe - Recompila el EA")
        return False
    
    # Verificar archivo de estado
    import os
    status_file = Path(os.getenv('APPDATA')).parent / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files' / 'Bot_Status.txt'
    
    print(f"\n📄 Verificando estado del EA...")
    print(f"   Ruta: {status_file}")
    
    if status_file.exists():
        mtime = datetime.fromtimestamp(status_file.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        print(f"   ✅ Archivo existe")
        print(f"   📅 Actualizado: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ⏱️  Hace: {age:.0f} segundos")
        
        if age < 10:
            print(f"   ✅ EA está ejecutándose activamente")
        elif age < 60:
            print(f"   ⚠️  EA podría estar inactivo")
        else:
            print(f"   ❌ EA no está ejecutándose - Agrégalo al gráfico")
            return False
    else:
        print(f"   ❌ EA nunca se ha ejecutado")
        return False
    
    # Test de conexión rápido
    print(f"\n🔌 Intentando conexión con EA...")
    
    from core.simple_bridge_executor import SimpleBridgeExecutor
    
    executor = SimpleBridgeExecutor({})
    
    connected = executor.connect()
    
    if connected:
        print(f"   ✅ CONEXIÓN EXITOSA!")
        
        # Test de account info
        account = executor.get_account_info()
        if account:
            print(f"\n📊 Datos de cuenta:")
            print(f"   Balance: ${account.get('balance', 0):,.2f}")
            print(f"   Servidor: {account.get('server', 'N/A')}")
            print(f"\n{'='*70}")
            print(f"  ✅ EA FUNCIONANDO CORRECTAMENTE")
            print(f"  Puedes ejecutar: ..\.venv\Scripts\python.exe tests\\test_simple_bridge_complete.py")
            print(f"{'='*70}\n")
            return True
        else:
            print(f"   ⚠️  Conectado pero no se obtuvo info de cuenta")
            return False
    else:
        print(f"   ❌ NO SE PUDO CONECTAR")
        print(f"\n❌ SOLUCIONES:")
        print(f"   1. Verifica que MT5 esté abierto")
        print(f"   2. Verifica que el EA esté en el gráfico (icono en esquina)")
        print(f"   3. Verifica que AutoTrading esté habilitado (botón verde)")
        print(f"   4. Revisa logs en pestaña 'Experts' de MT5")
        print(f"   5. Intenta quitar y volver a agregar el EA")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
