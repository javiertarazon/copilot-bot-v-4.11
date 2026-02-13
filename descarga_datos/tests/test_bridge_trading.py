#!/usr/bin/env python3
"""
Test Completo de Trading - Simple Bridge EA
Verifica ciclo: Conexión -> Balance -> Abrir -> Modificar -> Cerrar
"""

import sys
import os
import time
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simple_bridge_executor import SimpleBridgeExecutor

def main():
    print("\n" + "="*60)
    print("  TEST TRADING COMPLETO - SIMPLE BRIDGE EA")
    print("="*60)
    
    # Config básica
    config = {
        'command_timeout': 10
    }
    
    executor = SimpleBridgeExecutor(config)
    
    # 1. CONEXIÓN
    print("\n1. 🔗 Conectando...")
    if not executor.connect():
        print("❌ Error: No se pudo conectar con el EA.")
        return

    print("✅ Conectado.")
    
    # 2. BALANCE
    print("\n2. 💰 Verificando cuenta...")
    account = executor.get_account_info()
    if not account:
        print("❌ Error obteniendo info de cuenta")
        return
        
    print(f"   Balance: ${account.get('balance'):,.2f}")
    print(f"   Equity: ${account.get('equity'):,.2f}")
    print(f"   Trading permitido: {account.get('trade_allowed')}")
    
    if not account.get('trade_allowed'):
        print("⚠️ Trading NO permitido en la cuenta/terminal. Habilita AutoTrading.")
        # Continuamos por si acaso es un falso negativo del flag
    
    # 3. ABRIR POSICIÓN
    symbol = "EURUSD" # Intentar par común primero
    # Si estamos en ThinkMarkets Volatility
    if "ThinkMarkets" in account.get('server', ''):
        symbol = "TM_VOLATILITY_50" 
        
    print(f"\n3. 🚀 Abriendo posición de prueba en {symbol}...")
    
    # Intentar abrir BUY 0.01
    result = executor.open_position(
        symbol=symbol,
        order_type='BUY',
        quantity=0.01,
        stop_loss_price=0.0,
        take_profit_price=0.0
    )
    
    if not result.get('success'):
        print(f"❌ Falló apertura: {result.get('error')}")
        # Intentar con EURUSD si falló volatility
        if symbol != "EURUSD":
            print("   Intentando con EURUSD...")
            symbol = "EURUSD"
            result = executor.open_position(symbol, 'BUY', 0.01)
            
        if not result.get('success'):
            print("❌ No se pudo abrir posición. Abortando.")
            return

    ticket = result.get('ticket')
    print(f"✅ Posición abierta! Ticket: {ticket}")
    print(f"   Precio: {result.get('price')}")
    
    # 4. MODIFICAR POSICIÓN
    print("\n4. ⚙️ Modificando SL/TP...")
    open_price = float(result.get('price'))
    
    # SL 100 puntos abajo, TP 200 puntos arriba (aprox)
    # Para volatility/forex varía, pero pondremos valores absolutos pequeños
    # Si precio es 1000, sl 990.
    
    # Calcular SL/TP dummy basados en precio
    sl = open_price * 0.99
    tp = open_price * 1.02
    
    mod_result = executor.modify_position(ticket, sl=sl, tp=tp)
    
    if mod_result:
        print(f"✅ Posición modificada. SL: {sl:.5f}, TP: {tp:.5f}")
    else:
        print("⚠️ Advertencia: No se pudo modificar SL/TP")
        
    print("\n⏳ Esperando 5 segundos...")
    time.sleep(5)
    
    # 5. CERRAR POSICIÓN
    print(f"\n5. 🏁 Cerrando posición {ticket}...")
    close_result = executor.close_position(ticket)
    
    if close_result:
        print("✅ Posición cerrada exitosamente.")
    else:
        print("❌ Error cerrando posición. Cierra manualmente en MT5.")
        
    print("\n" + "="*60)
    print("  TEST FINALIZADO")
    print("="*60)

if __name__ == "__main__":
    main()
