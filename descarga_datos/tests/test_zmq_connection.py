#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión ZMQ con MT5.

Este script intenta conectar con el EA ZMQ_Bridge corriendo en MT5
y ejecuta pruebas básicas de comunicación.

Usage:
    python test_zmq_connection.py

Requisitos:
    1. MT5 abierto con el EA ZMQ_Bridge_EA corriendo
    2. pyzmq instalado
"""

import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import time

def test_zmq_connection():
    """Prueba la conexión ZMQ con el EA en MT5."""
    
    print("="*60)
    print("🔌 TEST DE CONEXIÓN ZMQ")
    print("="*60)
    print()
    
    # Verificar que pyzmq está instalado
    try:
        import zmq
        print(f"✅ pyzmq instalado: v{zmq.pyzmq_version()}")
    except ImportError:
        print("❌ pyzmq no está instalado")
        print("   Ejecutar: pip install pyzmq")
        return False
    
    # Importar ZMQOrderExecutor
    try:
        from core.zmq_order_executor import ZMQOrderExecutor, ZMQOrderType
        print("✅ ZMQOrderExecutor importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando ZMQOrderExecutor: {e}")
        return False
    
    print()
    print("-"*60)
    print("📡 Intentando conectar con el EA...")
    print("-"*60)
    
    # Crear executor con timeout corto para prueba
    executor = ZMQOrderExecutor(
        zmq_orders_url='tcp://localhost:5555',
        zmq_ticks_url='tcp://localhost:5556',
        timeout_ms=3000  # 3 segundos timeout
    )
    
    # Intentar inicializar
    if not executor.initialize():
        print()
        print("❌ No se pudo conectar con el EA")
        print()
        print("Verifica que:")
        print("  1. MT5 está abierto")
        print("  2. El EA ZMQ_Bridge_EA está corriendo en un gráfico")
        print("  3. Trading algorítmico está habilitado en MT5")
        print("  4. No hay firewall bloqueando puertos 5555/5556")
        return False
    
    print("✅ Conexión establecida!")
    print()
    
    # Test: Obtener info de cuenta
    print("-"*60)
    print("📊 Obteniendo información de cuenta...")
    print("-"*60)
    
    account_info = executor.get_account_info()
    if account_info:
        print(f"  Login:        {account_info.get('login')}")
        print(f"  Servidor:     {account_info.get('server')}")
        print(f"  Balance:      ${account_info.get('balance', 0):.2f}")
        print(f"  Equity:       ${account_info.get('equity', 0):.2f}")
        print(f"  Leverage:     1:{account_info.get('leverage')}")
        print(f"  Trade Allow:  {account_info.get('trade_allowed')}")
    else:
        print("  ⚠️ No se pudo obtener info de cuenta")
    
    print()
    
    # Test: Obtener info de símbolo
    print("-"*60)
    print("📈 Obteniendo información de símbolos...")
    print("-"*60)
    
    symbols = ['TM_VOLATILITY_75', 'TM_VOLATILITY_100', 'EURUSD']
    for symbol in symbols:
        symbol_info = executor.get_symbol_info(symbol)
        if symbol_info:
            print(f"  {symbol}:")
            print(f"    Bid/Ask: {symbol_info.get('bid', 0):.5f} / {symbol_info.get('ask', 0):.5f}")
            print(f"    Spread:  {symbol_info.get('spread', 0)} pts")
            print(f"    Vol min: {symbol_info.get('volume_min', 0)}")
        else:
            print(f"  {symbol}: No disponible")
    
    print()
    
    # Test: Obtener posiciones
    print("-"*60)
    print("📋 Obteniendo posiciones abiertas...")
    print("-"*60)
    
    positions = executor.get_positions()
    if positions:
        print(f"  Total posiciones: {len(positions)}")
        for pos in positions:
            print(f"    #{pos.ticket}: {pos.symbol} {'BUY' if pos.order_type == 0 else 'SELL'} {pos.volume} lots @ {pos.open_price:.5f}")
    else:
        print("  No hay posiciones abiertas")
    
    print()
    
    # Mostrar estadísticas
    print("-"*60)
    print("📉 Estadísticas del executor:")
    print("-"*60)
    stats = executor.get_stats()
    print(f"  Conectado:       {stats.get('connected')}")
    print(f"  Órdenes enviadas: {stats.get('orders_sent')}")
    print(f"  Latencia prom:    {stats.get('avg_latency_ms', 0):.1f}ms")
    print(f"  Ticks recibidos:  {stats.get('ticks_received')}")
    
    # Cerrar conexión
    executor.shutdown()
    
    print()
    print("="*60)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("="*60)
    print()
    print("Para usar ZMQ en el bot, edita config.yaml:")
    print()
    print("  zmq:")
    print("    enabled: true")
    print()
    print("  live_trading:")
    print("    executor_type: 'zmq'")
    print()
    
    return True


def test_order_simulation():
    """
    Simula envío de una orden (sin ejecutar realmente).
    Solo para verificar que el formato de mensaje es correcto.
    """
    print()
    print("="*60)
    print("🧪 TEST DE SIMULACIÓN DE ORDEN")
    print("="*60)
    print()
    
    from core.zmq_order_executor import ZMQOrderExecutor, ZMQOrderType
    
    # Mostrar formato de orden que se enviaría
    order_data = {
        'action': 'order',
        'symbol': 'TM_VOLATILITY_75',
        'type': ZMQOrderType.BUY.value,
        'volume': 0.01,
        'price': 0,  # 0 = mercado
        'sl': 40000.0,
        'tp': 45000.0,
        'magic': 20260129,
        'comment': 'BOT_TEST'
    }
    
    print("Formato de orden JSON que se enviaría:")
    import json
    print(json.dumps(order_data, indent=2))
    print()
    print("⚠️ Esta es solo una simulación, no se ejecutó ninguna orden")


if __name__ == '__main__':
    success = test_zmq_connection()
    
    if success:
        print()
        response = input("¿Desea ver simulación de orden? (s/n): ")
        if response.lower() == 's':
            test_order_simulation()
    
    sys.exit(0 if success else 1)
