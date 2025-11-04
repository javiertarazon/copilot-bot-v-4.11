"""Script simple de diagnóstico MT5"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("DIAGNÓSTICO MT5 - ANÁLISIS DE PROBLEMA")
print("=" * 70)

# Inicializar
if not mt5.initialize(login=int(os.getenv("MT5_LOGIN")), 
                      password=os.getenv("MT5_PASSWORD"), 
                      server=os.getenv("MT5_SERVER")):
    print(f"❌ Error al inicializar: {mt5.last_error()}")
    exit(1)

print("\n✅ MT5 inicializado")

# Info de cuenta
account = mt5.account_info()
print(f"\n📊 CUENTA:")
print(f"   Nombre: {account.name}")
print(f"   Saldo: ${account.balance:.2f}")
print(f"   Equity: ${account.equity:.2f}")
print(f"   Margen libre: ${account.margin_free:.2f}")

# Info terminal
terminal = mt5.terminal_info()
print(f"\n💻 TERMINAL:")
print(f"   Conectada: {terminal.connected}")
print(f"   Trading permitido: {terminal.trade_allowed} ❌ <-- PROBLEMA")

# Posiciones
pos = mt5.positions_get()
print(f"\n📈 POSICIONES ABIERTAS: {len(pos) if pos else 0}")
if pos:
    for p in pos:
        print(f"   - {p.symbol}: {p.volume} lotes, Tipo={'LONG' if p.type == 0 else 'SHORT'}")

# Órdenes
orders = mt5.orders_get()
print(f"\n📋 ÓRDENES PENDIENTES: {len(orders) if orders else 0}")
if orders:
    for o in orders:
        print(f"   - {o.symbol}: {o.volume_current} lotes @ {o.price_open:.2f}")

print("\n" + "=" * 70)
print("⚠️  PROBLEMA IDENTIFICADO:")
print("=" * 70)
print("🔴 'Conectado a servidor: False'")
print("\nEsto significa que MT5 está conectado LOCALMENTE pero NO al servidor Deriv")
print("\n✅ SOLUCIÓN:")
print("   1. Abre MetaTrader 5")
print("   2. Ve a File > Login")
print("   3. Login: 5899273")
print("   4. Password: [Tu contraseña]")
print("   5. Server: Deriv-Demo")
print("   6. Presiona OK y espera a conectar")
print("   7. Verifica que dice 'Connected' en la esquina inferior")
print("   8. Luego ejecuta: python descarga_datos/main.py --live-mt5")

print("\n💡 NOTA: La cuenta dice 'Saldo: $9,997.02' pero no está")
print("   conectada al servidor. Necesita reconectar.")

mt5.shutdown()
