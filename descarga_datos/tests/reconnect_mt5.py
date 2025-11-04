"""
Script para reconectar MT5 y validar conexión
"""
import MetaTrader5 as mt5
import os
import time
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")

print("=" * 70)
print("RECONECTAR A MT5 - DERIV")
print("=" * 70)

# Intentar reconectar
print(f"\n[1] Cerrando conexión anterior...")
mt5.shutdown()
time.sleep(2)

print(f"[2] Reconectando a MT5...")
print(f"    Login: {login}")
print(f"    Server: {server}")

if not mt5.initialize(login=login, password=password, server=server):
    print(f"❌ Error: {mt5.last_error()}")
    exit(1)

print("✅ Inicializado")

# Verificar estado
print(f"\n[3] Verificando estado de conexión...")
terminal = mt5.terminal_info()
print(f"    Terminal conectada: {terminal.connected}")
print(f"    Trading permitido: {terminal.trade_allowed}")

account = mt5.account_info()
print(f"\n[4] Información de cuenta:")
print(f"    Nombre: {account.name}")
print(f"    Saldo: ${account.balance:.2f}")
print(f"    Margen libre: ${account.margin_free:.2f}")

if not terminal.trade_allowed:
    print(f"\n🔴 ADVERTENCIA: Trading NO PERMITIDO")
    print(f"   En MT5, ve a Tools > Options > Expert Advisors")
    print(f"   Marca: 'Allow automated trading'")
    print(f"   Luego reinicia MT5 completamente")
else:
    print(f"\n✅ Trading está PERMITIDO - Sistema listo para ejecutar")

# Verificar símbolo
print(f"\n[5] Verificando símbolo 'Volatility 75 Index'...")
symbol = "Volatility 75 Index"
if not mt5.symbol_select(symbol, True):
    print(f"❌ No se pudo seleccionar símbolo: {mt5.last_error()}")
else:
    sym_info = mt5.symbol_info(symbol)
    if sym_info:
        print(f"✅ Símbolo disponible")
        print(f"   Bid: {sym_info.bid:.2f}")
        print(f"   Ask: {sym_info.ask:.2f}")
        print(f"   Volumen min: {sym_info.volume_min}")
        print(f"   Volumen max: {sym_info.volume_max}")

print("\n" + "=" * 70)
print("✅ RECONEXIÓN COMPLETADA")
print("=" * 70)

mt5.shutdown()
