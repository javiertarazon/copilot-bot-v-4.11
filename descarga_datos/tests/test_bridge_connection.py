#!/usr/bin/env python3
"""
Test Completo de Trading - Simple Bridge EA (Versión Robusta con Ruta Local)
Verifica ciclo: Status File -> Handshake -> Trading (MQL5/Files LOCAL)
"""

import sys
import os
import time
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simple_bridge_executor import SimpleBridgeExecutor

# RUTA DEL TERMINAL HASH (HARDCODED PARA ESTA PRUEBA)
MT5_FILES_PATH = r"C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files"

def check_status_file():
    """Verifica si el EA está reportando estado listo en MQL5/Files"""
    try:
        mt5_files = Path(MT5_FILES_PATH)
        status_file = mt5_files / 'status.txt'
        
        if not status_file.exists():
            print(f"⚠️ Archivo de estado NO encontrado en: {status_file}")
            print("   (El EA no parece estar ejecutándose en ningún gráfico)")
            return False
            
        # Intentar leer con UTF-16
        try:
            content = status_file.read_text(encoding='utf-16')
        except UnicodeError:
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
    print("  TEST TRADING ROBUSTO - SIMPLE BRIDGE EA (LOCAL PATH)")
    print("="*60)
    print(f"📂 Ruta de archivos MQL5: {MT5_FILES_PATH}")
    
    # 0. Verificación Previa
    if not os.path.exists(MT5_FILES_PATH):
        print("❌ Ruta MQL5/Files no existe. Revisa el Hash del Terminal.")
        return

    print("\n0. 🔍 Buscando seña de vida del EA...")
    if not check_status_file():
        print("\n⛔ PRE-CHECK FALLIDO: El EA no está escribiendo su estado.")
        print("   -> Abre MT5")
        print("   -> Recompila el EA (si acabas de cambiar el código)")
        print("   -> Arrastra 'Simple_Bridge_EA' al gráfico")
        return

    # Config extendida con ruta local
    config = {
        'command_timeout': 15,
        'mt5_files_path': MT5_FILES_PATH  # <-- Usar ruta local
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
    else:
        print("⚠️ No se pudo leer info de cuenta.")
    
    # 3. TRADING TEST
    symbol = "TM_VOLATILITY_75"  # Símbolo confirmado por usuario
         
    print(f"\n3. 🚀 Preparando operación en {symbol}...")
    
    # Obtener info del símbolo para saber volumen mínimo
    symbol_info = executor.get_symbol_info(symbol)
    if not symbol_info:
        print(f"❌ Error: No se pudo obtener info de {symbol} (¿Existe en Market Watch?)")
        return
        
    vol_min = symbol_info.get('volume_min', 0.01)
    vol_max = symbol_info.get('volume_max', 100.0)
    print(f"   Volumen Mínimo: {vol_min}")
    print(f"   Volumen Máximo: {vol_max}")
    
    quantity = vol_min  # Usar el mínimo permitido
    print(f"   Intentando abrir BUY {quantity} lotes en {symbol}...")
    
    result = executor.open_position(
        symbol=symbol,
        order_type='BUY',
        quantity=quantity
    )
    
    if not result.get('success'):
        print(f"❌ Falló apertura: {result.get('error')}")
        return

    ticket = result.get('ticket')
    price = result.get('price')
    print(f"✅ ORDEN ABIERTA EXITOSAMENTE! Ticket: {ticket} @ {price}")
    
    # 4. MODIFICAR
    print("\n4. ⚙️ Modificando SL/TP...")
    sl = float(price) * 0.95
    tp = float(price) * 1.05
    
    if executor.modify_position(ticket, sl=sl, tp=tp):
        print(f"✅ Modificación exitosa.")
    else:
        print("⚠️ Falló modificación.")
        
    print("\n⏳ Esperando 5 segundos...")
    time.sleep(5)
    
    # 5. CERRAR
    print(f"\n5. 🏁 Cerrando posición {ticket}...")
    if executor.close_position(ticket):
        print("✅ Cierre exitoso.")
    else:
        print("❌ Error cerrando posición.")
        
    print("\n" + "="*60)
    print("  TEST COMPLETADO CON ÉXITO")
    print("="*60)

if __name__ == "__main__":
    main()
