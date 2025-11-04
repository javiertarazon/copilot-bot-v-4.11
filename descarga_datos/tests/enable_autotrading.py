"""
Script para intentar habilitar AutoTrading en MT5
"""
import MetaTrader5 as mt5
import os
import subprocess
import time
import ctypes
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")
mt5_path = os.getenv("MT5_PATH", "C:\\Program Files\\MetaTrader 5\\terminal64.exe")

print("=" * 70)
print("HABILITAR AUTOTRADING EN MT5")
print("=" * 70)

# 1. Verificar si MT5 está abierto
print("\n[1] Verificando si MT5 está abierto...")
try:
    # Intentar inicializar sin login
    if mt5.initialize():
        mt5.shutdown()
        print("✅ MT5 está abierto")
    else:
        print("❌ MT5 no está abierto")
        print("   Abriendo MT5...")
        subprocess.Popen([mt5_path])
        print("   Espera 30 segundos para que MT5 se abra...")
        time.sleep(30)
except:
    print("❌ Error al verificar MT5")

# 2. Conectar a la cuenta
print("\n[2] Conectando a cuenta MT5...")
if not mt5.initialize(login=login, password=password, server=server):
    print(f"❌ Error: {mt5.last_error()}")
    exit(1)

print("✅ Cuenta conectada")

# 3. Verificar estado de AutoTrading
terminal = mt5.terminal_info()
print(f"\n[3] Estado actual:")
print(f"    Trading permitido: {terminal.trade_allowed}")

if terminal.trade_allowed:
    print("✅ AutoTrading ya está habilitado!")
    mt5.shutdown()
    exit(0)

# 4. Intentar habilitar vía API (algunas versiones de MT5 lo permiten)
print("\n[4] Intentando habilitar AutoTrading...")
print("    ⚠️  Esta acción requiere acción manual en MT5")

print("\n" + "=" * 70)
print("📋 INSTRUCCIONES MANUALES RÁPIDAS:")
print("=" * 70)
print("""
En la ventana de MetaTrader 5:
1. Click en: Tools (Herramientas)
2. Click en: Options (Opciones)
3. Tab: Expert Advisors (Asesores Expertos)
4. Marca: ✅ Allow automated trading
5. Marca: ✅ Allow DLL imports (si existe)
6. Click: OK
7. Reinicia MT5 (cierra y abre nuevamente)

Luego ejecuta:
   python descarga_datos/tests/diagnose_simple.py

Si muestra "Trading permitido: True", entonces ejecuta:
   python descarga_datos/main.py --live-mt5
""")

print("\n" + "=" * 70)

# 5. Intentar abrir configuración automáticamente (solo funciona en algunas versiones)
try:
    # Algunos scripts MT5 pueden ejecutar esto:
    # Pero generalmente requiere la interfaz gráfica
    print("💡 Nota: La configuración debe hacerse en la interfaz gráfica de MT5")
    print("        No es automatizable por seguridad")
except:
    pass

mt5.shutdown()
