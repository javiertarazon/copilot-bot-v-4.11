import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def diagnose():
    print("=== DIAGNÓSTICO MT5 ===")
    
    if not mt5.initialize():
        print(f"❌ Error inicializando MT5: {mt5.last_error()}")
        return

    # 1. Info de Cuenta
    account_info = mt5.account_info()
    if account_info:
        print(f"✅ Conectado a: {account_info.login} ({account_info.server})")
        print(f"   Balance: {account_info.balance}, Equity: {account_info.equity}")
    else:
        print("❌ No se pudo obtener info de cuenta")

    # 2. Buscar Símbolos
    print("\n=== SÍMBOLOS DISPONIBLES (Buscando 'Vol' o '75') ===")
    symbols = mt5.symbols_get()
    found_symbols = []
    if symbols:
        for s in symbols:
            if "vol" in s.name.lower() or "75" in s.name:
                print(f"   Symbol: {s.name}, Path: {s.path}, Visible: {s.visible}")
                found_symbols.append(s.name)
    else:
        print("❌ No se pudieron obtener símbolos")

    # 3. Intentar obtener datos de "Volatility 75 Index"
    target = "Volatility 75 Index"
    print(f"\n=== PRUEBA DE DATOS: {target} ===")
    rates = mt5.copy_rates_from_pos(target, mt5.TIMEFRAME_M15, 0, 10)
    if rates is None:
        print(f"❌ Fallo al obtener datos para '{target}'. Error: {mt5.last_error()}")
        # Intentar con el primero encontrado si hay
        if found_symbols:
            alt = found_symbols[0]
            print(f"   Intentando con alternativa: '{alt}'")
            rates_alt = mt5.copy_rates_from_pos(alt, mt5.TIMEFRAME_M15, 0, 10)
            if rates_alt is None:
                print(f"❌ Fallo también con '{alt}'. Error: {mt5.last_error()}")
            else:
                print(f"✅ Éxito con '{alt}': {len(rates_alt)} barras")
    else:
        print(f"✅ Datos obtenidos correctamente para '{target}': {len(rates)} barras")

    # 4. Analizar Posiciones Abiertas
    print("\n=== POSICIONES ABIERTAS ===")
    positions = mt5.positions_get()
    if positions:
        for p in positions:
            print(f"Ticket: {p.ticket}")
            print(f"  Symbol: {p.symbol}")
            print(f"  Type: {'BUY' if p.type == 0 else 'SELL'}")
            print(f"  Vol: {p.volume}")
            print(f"  Open Price: {p.price_open}")
            print(f"  Current Price: {p.price_current}")
            print(f"  SL: {p.sl}")
            print(f"  TP: {p.tp}")
            print(f"  Profit: {p.profit}")
            
            # Verificar error 10016
            # Si intentamos modificar a los valores que fallaban
            # SL:387.679 TP:392.73 (del log)
            # Verificamos si tienen sentido con el precio actual
            print("  -- Análisis de Stops --")
            symbol_info = mt5.symbol_info(p.symbol)
            if symbol_info:
                print(f"  Min Stop Level: {symbol_info.trade_stops_level}")
                print(f"  Freeze Level: {symbol_info.trade_freeze_level}")
                print(f"  Ask: {symbol_info.ask}, Bid: {symbol_info.bid}")
    else:
        print("ℹ️ No hay posiciones abiertas")

    mt5.shutdown()

if __name__ == "__main__":
    diagnose()
