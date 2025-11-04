"""
Herramienta de Diagnóstico y Recuperación - MT5 Live Trading
===========================================================
Intenta conectar a MT5 y reporta el estado
"""

import sys
from pathlib import Path
import time
import os

# Agregar rutas
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

def check_mt5_status():
    """Verificar estado de MT5"""
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE CONEXIÓN MT5")
    print("="*80 + "\n")
    
    try:
        import MetaTrader5 as mt5
        print("✅ Librería MetaTrader5 disponible")
    except ImportError:
        print("❌ Librería MetaTrader5 NO disponible")
        return False
    
    # Intentar inicializar
    print("\n🔄 Intentando inicializar MT5...")
    if mt5.initialize():
        print("✅ MT5 inicializado correctamente")
        
        # Obtener información de cuenta
        account_info = mt5.account_info()
        if account_info:
            print(f"\n📊 Información de Cuenta:")
            print(f"   Login:        {account_info.login}")
            print(f"   Servidor:     {account_info.server}")
            print(f"   Balance:      ${account_info.balance:,.2f}")
            print(f"   Equity:       ${account_info.equity:,.2f}")
            print(f"   Status:       ✅ CONECTADO")
            return True
        else:
            print("⚠️  No se pudo obtener información de cuenta")
            print(f"   Error: {mt5.last_error()}")
            return False
    else:
        error = mt5.last_error()
        print(f"❌ Error al inicializar MT5: {error}")
        
        # Si hay error de autorización, intentar login manual
        if "Authorization failed" in str(error) or error[0] == -6:
            print("\n🔑 Intentando login manual con credenciales de .env...")
            
            # Cargar credenciales
            from dotenv import load_dotenv
            load_dotenv()
            
            login = int(os.getenv('MT5_LOGIN', '5899273'))
            password = os.getenv('MT5_PASSWORD', 'Jatr280371$')
            server = os.getenv('MT5_SERVER', 'Deriv-Demo')
            
            print(f"   Login:    {login}")
            print(f"   Server:   {server}")
            print(f"   Password: {'*' * len(password)}")
            
            # Intentar login
            print("\n🔄 Intentando login...")
            if mt5.login(login, password=password, server=server):
                print("✅ Login exitoso")
                
                account_info = mt5.account_info()
                if account_info:
                    print(f"\n📊 Información de Cuenta:")
                    print(f"   Login:        {account_info.login}")
                    print(f"   Servidor:     {account_info.server}")
                    print(f"   Balance:      ${account_info.balance:,.2f}")
                    print(f"   Equity:       ${account_info.equity:,.2f}")
                    print(f"   Status:       ✅ CONECTADO")
                    return True
            else:
                print(f"❌ Error en login: {mt5.last_error()}")
                return False
        
        return False

def main():
    success = check_mt5_status()
    
    if success:
        print("\n" + "="*80)
        print("✅ SISTEMA LISTO PARA TRADING LIVE")
        print("="*80)
        print("\nEjecutar: python descarga_datos/main.py --live-mt5\n")
    else:
        print("\n" + "="*80)
        print("❌ ERROR: No se puede conectar a MT5")
        print("="*80)
        print("\n⚠️  POSIBLES SOLUCIONES:")
        print("   1. Asegúrate que MT5 está abierto en tu computadora")
        print("   2. Verifica que las credenciales en .env sean correctas")
        print("   3. Si MT5 está en otra máquina, conecta manualmente primero")
        print("   4. Reinicia MetaTrader 5 y vuelve a intentar\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
