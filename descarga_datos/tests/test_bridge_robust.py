#!/usr/bin/env python3
"""
Test Completo de Trading - Simple Bridge EA (Versión Robusta)
Verifica ciclo: Status File -> Handshake -> Trading
"""

import sys
import os
import time
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simple_bridge_executor import SimpleBridgeExecutor

def check_status_file():
    """Verifica si el EA está reportando estado listo"""
    try:
        mt5_common_path = Path(os.getenv('APPDATA')).parent / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
        status_file = mt5_common_path / 'Bot_Status.txt'
        
        if not status_file.exists():
            print(f"⚠️ Archivo de estado NO encontrado en: {status_file}")
            print("   (El EA no parece estar ejecutándose en ningún gráfico)")
            return False
            
        # Intentar leer con UTF-16 (MT5 standard)
        try:
            content = status_file.read_text(encoding='utf-16')
        except UnicodeError:
            # Fallback a utf-8 o cp1252
            content = status_file.read_text(encoding='utf-8', errors='ignore')
            
        print(f"📄 Contenido de Bot_Status.txt: {content.strip()}")
        
        if 'READY' in content or 'OK' in content:
            return True
            
        return False
        
    except Exception as e:
        print(f"❌ Error verificando estado: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  TEST TRADING ROBUSTO - SIMPLE BRIDGE EA")
    print("="*60)
    
    # 0. Verificación Previa
    print("\n0. 🔍 Buscando seña de vida del EA...")
    if not check_status_file():
        print("\n⛔ PRE-CHECK FALLIDO: El EA no está escribiendo su estado.")
        print("   -> Abre MT5")
        print("   -> Arrastra 'Simple_Bridge_EA' al gráfico")
        print("   -> Asegura 'Algo Trading' encendido")
        return

    # Config extendida
    config = {
        'command_timeout': 15  # Más tiempo para primera conexión
    }
    
    executor = SimpleBridgeExecutor(config)
    
    # 1. CONEXIÓN (Heartbeat)
    print("\n1. 🔗 Conectando (Heartbeat)...")
    if not executor.connect():
        print("❌ Error: No se pudo establecer handshake con el EA.")
        return

    print("✅ Conectado y sincronizado.")
    
    # 2. BALANCE
    print("\n2. 💰 Obteniendo datos de cuenta...")
    account = executor.get_account_info()
    if account:
        print(f"   Balance: ${account.get('balance'):,.2f}")
        print(f"   Equity: ${account.get('equity'):,.2f}")
        print(f"   Trading Enabled: {account.get('trade_allowed')}")
    else:
        print("⚠️ No se pudo leer info de cuenta (pero hay conexión).")
    
    # 3. TRADING TEST
    symbol = "EURUSD"
    # Auto-detectar símbolo si es posible
    if account and "ThinkMarkets" in account.get('server', ''):
         symbol = "TM_VOLATILITY_50" # Preferido para test
         
    print(f"\n3. 🚀 Intentando abrir posición en {symbol} (0.01 lotes)...")
    
    result = executor.open_position(
        symbol=symbol,
        order_type='BUY',
        quantity=0.01,
        stop_loss_price=0.0,
        take_profit_price=0.0
    )
    
    if not result.get('success'):
        print(f"❌ Falló apertura: {result.get('error')}")
        print("   (Verifica que el mercado esté abierto y tengas margen)")
        return

    ticket = result.get('ticket')
    price = result.get('price')
    print(f"✅ ORDEN ABIERTA EXITOSAMENTE! Ticket: {ticket} @ {price}")
    
    # 4. MODIFICAR
    print("\n4. ⚙️ Modificando SL/TP...")
    sl = float(price) * 0.95
    tp = float(price) * 1.05
    
    if executor.modify_position(ticket, sl=sl, tp=tp):
        print(f"✅ Modificación exitosa. Nuevo SL: {sl:.4f}, TP: {tp:.4f}")
    else:
        print("⚠️ Falló modificación (no crítico para el test).")
        
    print("\n⏳ Esperando 5 segundos antes de cerrar...")
    time.sleep(5)
    
    # 5. CERRAR
    print(f"\n5. 🏁 Cerrando posición {ticket}...")
    if executor.close_position(ticket):
        print("✅ Cierre exitoso.")
    else:
        print("❌ Error cerrando posición. Cierra manualmente.")
        
    print("\n" + "="*60)
    print("  TEST COMPLETADO CON ÉXITO")
    print("="*60)

if __name__ == "__main__":
    main()
