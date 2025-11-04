"""
Script que espera a que AutoTrading esté habilitado y luego inicia live trading
"""
import MetaTrader5 as mt5
import os
import time
import sys
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")

print("=" * 70)
print("MONITOR DE AUTOTRADING - ESPERA A QUE SE HABILITE")
print("=" * 70)
print(f"\nEsta ventana verificará cada 5 segundos si AutoTrading está habilitado.")
print(f"Una vez habilitado, iniciará automáticamente el sistema live trading.\n")

# Conectar inicialmente
if not mt5.initialize(login=login, password=password, server=server):
    print(f"❌ Error al conectar: {mt5.last_error()}")
    exit(1)

print("✅ Conectado a MT5")
print("=" * 70)

# Loop de espera
attempt = 0
max_attempts = 300  # 25 minutos (300 * 5 segundos)

while attempt < max_attempts:
    try:
        # Reconectar cada intento
        mt5.shutdown()
        time.sleep(1)
        
        if not mt5.initialize(login=login, password=password, server=server):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ No se pudo conectar")
            attempt += 1
            time.sleep(5)
            continue
        
        terminal = mt5.terminal_info()
        
        if terminal.trade_allowed:
            print(f"\n{'=' * 70}")
            print(f"✅ ¡AUTOTRADING HABILITADO EN MT5!")
            print(f"{'=' * 70}")
            print(f"Tiempo: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Cuenta: {mt5.account_info().name}")
            print(f"\n🚀 Iniciando sistema live trading en 3 segundos...\n")
            
            mt5.shutdown()
            time.sleep(3)
            
            # Iniciar el sistema
            import subprocess
            main_py = Path(__file__).parent.parent / "main.py"
            result = subprocess.run(
                [sys.executable, str(main_py), "--live-mt5"],
                cwd=Path(__file__).parent.parent.parent
            )
            exit(result.returncode)
        else:
            status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ AutoTrading aún deshabilitado (intento {attempt+1}/{max_attempts})"
            print(status_msg)
            attempt += 1
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n\n❌ Cancelado por usuario")
        mt5.shutdown()
        exit(0)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Error: {e}")
        attempt += 1
        time.sleep(5)

print(f"\n❌ Timeout: AutoTrading no fue habilitado en {max_attempts * 5} segundos")
print(f"Verifica que hayas completado todos los pasos en MT5:")
print(f"  1. Tools > Options > Expert Advisors")
print(f"  2. Marca 'Allow automated trading'")
print(f"  3. Reinicia MT5")
mt5.shutdown()
exit(1)
