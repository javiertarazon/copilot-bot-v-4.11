"""
Verificación completa del sistema Live MT5
- Conexión MT5
- Símbolos disponibles
- Obtención de datos
- Capacidad de trading
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

load_dotenv()

print("="*70)
print("VERIFICACIÓN COMPLETA - LIVE TRADING MT5")
print("="*70)

# 1. CONEXIÓN MT5
print("\n[1] CONEXIÓN MT5")
if not mt5.initialize():
    print(f"  ❌ Error: {mt5.last_error()}")
    sys.exit(1)
print("  ✅ MT5 Inicializado")

login = int(os.getenv('MT5_LOGIN'))
password = os.getenv('MT5_PASSWORD', '').replace('"', '')
server = os.getenv('MT5_SERVER')

if not mt5.login(login, password=password, server=server):
    print(f"  ❌ Login fallido: {mt5.last_error()}")
    sys.exit(1)
print(f"  ✅ Conectado: Login {login} en {server}")

# 2. CUENTA
print("\n[2] INFORMACIÓN DE CUENTA")
acc = mt5.account_info()
print(f"  Balance: ${acc.balance:.2f}")
print(f"  Equity: ${acc.equity:.2f}")
print(f"  Trade Allowed: {acc.trade_allowed}")
print(f"  Expert Allowed: {acc.trade_expert}")

# 3. SÍMBOLOS VOLATILITY
print("\n[3] SÍMBOLOS VOLATILITY (TM_VOLATILITY)")
symbols_config = ['TM_VOLATILITY_50', 'TM_VOLATILITY_75', 'TM_VOLATILITY_100']
symbols_ok = []

for sym in symbols_config:
    info = mt5.symbol_info(sym)
    if info:
        # Habilitar símbolo si no está visible
        if not info.visible:
            mt5.symbol_select(sym, True)
            info = mt5.symbol_info(sym)
        
        tick = mt5.symbol_info_tick(sym)
        if tick:
            trade_modes = {0: 'DISABLED', 4: 'FULL'}
            mode_str = trade_modes.get(info.trade_mode, f'MODE_{info.trade_mode}')
            print(f"  ✅ {sym}")
            print(f"     Bid/Ask: {tick.bid:.2f} / {tick.ask:.2f}")
            print(f"     Spread: {(tick.ask - tick.bid):.2f} pts")
            print(f"     Trade Mode: {mode_str}")
            print(f"     Volume min/max: {info.volume_min} / {info.volume_max}")
            symbols_ok.append(sym)
        else:
            print(f"  ⚠️ {sym}: Sin tick data")
    else:
        print(f"  ❌ {sym}: NO DISPONIBLE en este servidor")

# 4. OBTENER DATOS HISTÓRICOS
print("\n[4] DATOS HISTÓRICOS (últimas 10 barras 15m)")
if symbols_ok:
    for sym in symbols_ok[:1]:  # Solo el primero para demo
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 10)
        if rates is not None and len(rates) > 0:
            print(f"  ✅ {sym}: {len(rates)} barras obtenidas")
            print(f"     Última barra: {datetime.fromtimestamp(rates[-1]['time'])}")
            print(f"     OHLC: O={rates[-1]['open']:.2f} H={rates[-1]['high']:.2f} L={rates[-1]['low']:.2f} C={rates[-1]['close']:.2f}")
        else:
            print(f"  ❌ {sym}: No se pudieron obtener datos")
else:
    print("  ⚠️ No hay símbolos disponibles para test")

# 5. POSICIONES ABIERTAS
print("\n[5] POSICIONES ABIERTAS")
positions = mt5.positions_get()
if positions:
    print(f"  Total: {len(positions)}")
    for pos in positions:
        tipo = "BUY" if pos.type == 0 else "SELL"
        print(f"  - {pos.symbol}: {tipo} {pos.volume} @ {pos.price_open:.2f} (P&L: ${pos.profit:.2f})")
else:
    print("  No hay posiciones abiertas")

# 6. ÓRDENES PENDIENTES
print("\n[6] ÓRDENES PENDIENTES")
orders = mt5.orders_get()
if orders:
    print(f"  Total: {len(orders)}")
else:
    print("  No hay órdenes pendientes")

# 7. TEST DE ENVÍO DE ORDEN (SIN EJECUTAR)
print("\n[7] CAPACIDAD DE TRADING")
if symbols_ok and acc.trade_allowed and acc.trade_expert:
    sym = symbols_ok[0]
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    
    # Crear request de prueba (ORDER_CHECK, no ORDER_SEND)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym,
        "volume": info.volume_min,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "sl": tick.ask - 100,  # SL a 100 puntos
        "tp": tick.ask + 100,  # TP a 100 puntos
        "deviation": 20,
        "magic": 234000,
        "comment": "TEST_CHECK",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Solo verificar, no ejecutar
    check = mt5.order_check(request)
    if check and check.retcode == 0:
        print(f"  ✅ SISTEMA LISTO: Puede ejecutar órdenes en {sym}")
        print(f"     Volume min: {info.volume_min}")
        print(f"     Margin required: ${check.margin:.2f}")
    else:
        retcode_msgs = {
            10014: "Invalid volume",
            10015: "Invalid price",
            10016: "Invalid stops",
            10019: "Not enough money",
            10030: "Invalid filling type"
        }
        msg = retcode_msgs.get(check.retcode, f"Code {check.retcode}") if check else "Check failed"
        print(f"  ⚠️ Verificación de orden: {msg}")
        if check:
            print(f"     Comment: {check.comment}")
else:
    if not symbols_ok:
        print("  ❌ No hay símbolos disponibles")
    elif not acc.trade_allowed:
        print("  ❌ Trading no permitido en esta cuenta")
    elif not acc.trade_expert:
        print("  ❌ Expert Advisors no permitidos")

# 8. RESUMEN
print("\n" + "="*70)
print("RESUMEN")
print("="*70)
if symbols_ok and acc.trade_allowed:
    print(f"✅ SISTEMA OPERATIVO")
    print(f"   Símbolos disponibles: {', '.join(symbols_ok)}")
    print(f"   Cuenta: ${acc.balance:.2f}")
    print(f"   Trading: HABILITADO")
else:
    print("❌ SISTEMA NO OPERATIVO")
    if not symbols_ok:
        print("   Problema: Símbolos de Volatility Index no disponibles")
    if not acc.trade_allowed:
        print("   Problema: Trading no permitido")

mt5.shutdown()
