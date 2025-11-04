"""
Script para cerrar la posición abierta y resincronizar con MT5
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from pathlib import Path
import time

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")

print("=" * 70)
print("CERRAR POSICIÓN ABIERTA Y RESINCRONIZAR")
print("=" * 70)

# Conectar
if not mt5.initialize(login=login, password=password, server=server):
    print(f"❌ Error al inicializar: {mt5.last_error()}")
    exit(1)

print("\n✅ Conectado a MT5")

# Obtener posiciones
print("\n[1] Buscando posiciones abiertas...")
positions = mt5.positions_get()

if not positions:
    print("   ✅ No hay posiciones abiertas")
    mt5.shutdown()
    exit(0)

print(f"   ⚠️  Encontradas {len(positions)} posición(es)")

# Listar posiciones
for i, pos in enumerate(positions, 1):
    print(f"\n   Posición #{i}:")
    print(f"      Símbolo: {pos.symbol}")
    print(f"      Tipo: {'LONG (BUY)' if pos.type == 0 else 'SHORT (SELL)'}")
    print(f"      Volumen: {pos.volume} lotes")
    print(f"      Entrada: {pos.price_open:.2f}")
    print(f"      Actual: {pos.price_current:.2f}")
    print(f"      P&L: {pos.profit:.2f} USD")
    print(f"      SL: {pos.sl:.2f}")
    print(f"      TP: {pos.tp:.2f}")
    print(f"      Ticket: {pos.ticket}")

# Cerrar posiciones
print("\n[2] Cerrando posiciones...")
for pos in positions:
    symbol = pos.symbol
    volume = pos.volume
    
    # Obtener precio actual
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"   ❌ No se pudo obtener info de {symbol}")
        continue
    
    # Determinar tipo de orden contrario
    if pos.type == 0:  # BUY - cerrar con SELL
        order_type = mt5.ORDER_TYPE_SELL
        price = symbol_info.bid
        tipo_str = "SELL"
    else:  # SELL - cerrar con BUY
        order_type = mt5.ORDER_TYPE_BUY
        price = symbol_info.ask
        tipo_str = "BUY"
    
    # Crear request de cierre
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "position": pos.ticket,  # Cerrar esta posición específica
        "price": price,
        "deviation": 10,
        "magic": 227362,
        "comment": f"Cierre manual - {tipo_str}",
        "type_filling": mt5.ORDER_FILLING_FOK,
        "type_time": mt5.ORDER_TIME_GTC,
    }
    
    # Enviar orden
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"   ✅ Posición cerrada: {symbol} ({volume} lotes)")
        print(f"      Orden: {tipo_str} @ {price:.2f}")
        print(f"      Deal: {result.deal}")
    else:
        print(f"   ❌ Error al cerrar {symbol}: {result.comment}")

# Verificar cierre
print("\n[3] Verificando...")
time.sleep(2)

positions_after = mt5.positions_get()
if not positions_after:
    print("   ✅ Todas las posiciones cerradas correctamente")
else:
    print(f"   ⚠️  Aún hay {len(positions_after)} posición(es) abiertas")
    for pos in positions_after:
        print(f"      - {pos.symbol}: {pos.volume} lotes")

# Obtener info de cuenta
print("\n[4] Estado de cuenta:")
account = mt5.account_info()
print(f"   Saldo: ${account.balance:.2f}")
print(f"   Equity: ${account.equity:.2f}")
print(f"   Margen libre: ${account.margin_free:.2f}")

print("\n" + "=" * 70)
print("✅ CIERRE COMPLETADO")
print("=" * 70)
print("\nAhora puedes ejecutar:")
print("   python descarga_datos/main.py --live-mt5")

mt5.shutdown()
