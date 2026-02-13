"""Lista todos los simbolos disponibles en MT5"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

load_dotenv()

mt5.initialize()
mt5.login(
    int(os.getenv('MT5_LOGIN')), 
    password=os.getenv('MT5_PASSWORD','').replace('"',''), 
    server=os.getenv('MT5_SERVER')
)

print("="*60)
print("SIMBOLOS DISPONIBLES EN MT5")
print("="*60)

symbols = mt5.symbols_get()
print(f"\nTotal simbolos: {len(symbols)}")

# Buscar volatility
print("\n[SIMBOLOS CON 'VOLAT' O 'INDEX']")
volat = [s.name for s in symbols if 'volat' in s.name.lower() or 'index' in s.name.lower()]
for s in volat[:20]:
    print(f"  {s}")

# Mostrar categorias
print("\n[FOREX]")
forex = [s.name for s in symbols if s.path and 'forex' in s.path.lower()][:10]
for s in forex:
    print(f"  {s}")

print("\n[INDICES/OTROS]")
otros = [s.name for s in symbols if s.path and ('ind' in s.path.lower() or 'crypt' in s.path.lower())][:10]
for s in otros:
    print(f"  {s}")

print("\n[TODOS LOS SIMBOLOS]")
for s in symbols[:30]:
    info = mt5.symbol_info(s.name)
    print(f"  {s.name} | trade_mode={info.trade_mode if info else 'N/A'}")

mt5.shutdown()
