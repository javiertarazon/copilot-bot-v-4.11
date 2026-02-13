"""Diagnóstico completo del modo live MT5"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

mt5.initialize()
mt5.login(
    int(os.getenv('MT5_LOGIN')), 
    password=os.getenv('MT5_PASSWORD','').replace('"',''), 
    server=os.getenv('MT5_SERVER')
)

print("="*60)
print("DIAGNOSTICO TRADING LIVE MT5")
print("="*60)

# 1. Cuenta
acc = mt5.account_info()
print("\n[CUENTA]")
print(f"  Balance: ${acc.balance:.2f}")
print(f"  Equity: ${acc.equity:.2f}")
print(f"  Trade Allowed: {acc.trade_allowed}")
print(f"  Expert Allowed: {acc.trade_expert}")

# 2. Posiciones
pos = mt5.positions_get()
print(f"\n[POSICIONES ABIERTAS]: {len(pos) if pos else 0}")

# 3. Simbolos
print("\n[SIMBOLOS VOLATILITY]")
syms = ['Volatility 50 Index', 'Volatility 75 Index', 'Volatility 100 Index']
for s in syms:
    info = mt5.symbol_info(s)
    if info:
        tick = mt5.symbol_info_tick(s)
        print(f"  {s}: trade_mode={info.trade_mode} bid={tick.bid:.2f}")
    else:
        print(f"  {s}: NO DISPONIBLE")

# 4. Deals recientes
print("\n[DEALS ULTIMOS 7 DIAS]")
deals = mt5.history_deals_get(datetime.now() - timedelta(days=7), datetime.now())
print(f"  Total: {len(deals) if deals else 0}")

mt5.shutdown()
print("\n" + "="*60)
