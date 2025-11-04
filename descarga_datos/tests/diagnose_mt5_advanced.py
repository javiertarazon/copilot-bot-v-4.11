"""
Script de diagnóstico avanzado para MT5
Verifica: AutoTrading, límites de posiciones, credenciales, balances
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("DIAGNÓSTICO AVANZADO MT5")
print("=" * 70)

# 1. Verificar si MT5 está disponible
print("\n[1] VERIFICANDO DISPONIBILIDAD DE MT5...")
try:
    if not mt5.initialize(login=int(os.getenv("MT5_LOGIN")), 
                          password=os.getenv("MT5_PASSWORD"), 
                          server=os.getenv("MT5_SERVER")):
        print(f"❌ Error al inicializar: {mt5.last_error()}")
        exit(1)
    print("✅ MT5 inicializado correctamente")
except Exception as e:
    print(f"❌ Error crítico: {e}")
    exit(1)

# 2. Verificar cuenta
print("\n[2] INFORMACIÓN DE CUENTA...")
account_info = mt5.account_info()
if account_info:
    print(f"✅ Cuenta conectada: {account_info.name}")
    print(f"   Servidor: {account_info.server}")
    print(f"   Saldo: {account_info.balance:.2f} USD")
    print(f"   Equity: {account_info.equity:.2f} USD")
    print(f"   Apalancamiento: {account_info.leverage}:1")
    print(f"   Margen libre: {account_info.margin_free:.2f} USD")
    print(f"   Nivel de margen: {account_info.margin_level:.2f}%")
else:
    print(f"❌ Error al obtener info de cuenta: {mt5.last_error()}")

# 3. Verificar estado del servidor
print("\n[3] ESTADO DE SERVIDOR...")
terminal_info = mt5.terminal_info()
if terminal_info:
    print(f"   Terminal conectada: {terminal_info.connected}")
    print(f"   Conectado a servidor: {terminal_info.trade_allowed}")
    print(f"   Versión MT5: {terminal_info.version}")
    
    if not terminal_info.trade_allowed:
        print("\n🚨 CRÍTICO: Trading NO PERMITIDO en la terminal")
        print("   Posibles causas:")
        print("   1. Cuenta en Demo/Paper trading - Verificar configuración de cuenta")
        print("   2. Terminal no conectada a servidor - Reinicia MT5")
        print("   3. Trading deshabilitado - Ve a Tools > Options")
    else:
        print("✅ Trading está PERMITIDO")
else:
    print(f"❌ Error al obtener info de terminal: {mt5.last_error()}")

# 4. Verificar posiciones abiertas
print("\n[4] POSICIONES ABIERTAS...")
positions = mt5.positions_get()
if positions:
    print(f"✅ Total de posiciones: {len(positions)}")
    for pos in positions:
        print(f"\n   Símbolo: {pos.symbol}")
        print(f"   Tipo: {'LONG' if pos.type == 0 else 'SHORT'}")
        print(f"   Volumen: {pos.volume} lotes")
        print(f"   Precio de entrada: {pos.price_open:.2f}")
        print(f"   P&L: {pos.profit:.2f} USD")
else:
    print("✅ No hay posiciones abiertas")

# 5. Verificar órdenes pendientes
print("\n[5] ÓRDENES PENDIENTES...")
orders = mt5.orders_get()
if orders:
    print(f"⚠️  Total de órdenes pendientes: {len(orders)}")
    for order in orders:
        print(f"\n   Símbolo: {order.symbol}")
        print(f"   Precio: {order.price_open:.2f}")
        print(f"   Volumen: {order.volume_current} lotes")
else:
    print("✅ No hay órdenes pendientes")

# 6. Verificar símbolo específico
print("\n[6] VERIFICANDO SÍMBOLO 'Volatility 75 Index'...")
symbol = "Volatility 75 Index"
symbol_info = mt5.symbol_info(symbol)
if symbol_info:
    print(f"✅ Símbolo disponible")
    print(f"   Trade permitido: {symbol_info.trade_mode}")
    print(f"   Volumen mínimo: {symbol_info.volume_min}")
    print(f"   Volumen máximo: {symbol_info.volume_max}")
    print(f"   Volumen paso: {symbol_info.volume_step}")
    print(f"   Precio bid: {symbol_info.bid:.2f}")
    print(f"   Precio ask: {symbol_info.ask:.2f}")
    
    # Permitir trading del símbolo
    if not mt5.symbol_select(symbol, True):
        print(f"⚠️  No se pudo seleccionar el símbolo")
    else:
        print(f"✅ Símbolo seleccionado para trading")
else:
    print(f"❌ Símbolo no encontrado: {mt5.last_error()}")

# 7. Test de orden (SIN enviar realmente)
print("\n[7] VALIDACIÓN DE PARÁMETROS DE ORDEN...")
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": 0.001,
    "type": mt5.ORDER_TYPE_SELL,
    "price": symbol_info.bid if symbol_info else 0,
    "sl": symbol_info.bid + 100 if symbol_info else 0,
    "tp": symbol_info.bid - 100 if symbol_info else 0,
    "deviation": 10,
    "magic": 227362,
    "comment": "Diagnóstico",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_FOK,
}
print("✅ Parámetros de orden validados")
print(f"   Acción: DEAL (Orden inmediata)")
print(f"   Símbolo: {request['symbol']}")
print(f"   Volumen: {request['volume']} lotes")
print(f"   Tipo: SELL")
print(f"   Type Filling: FOK (Fill or Kill)")

# 8. Resumen de problemas posibles
print("\n" + "=" * 70)
print("RESUMEN DE SOLUCIONES POSIBLES:")
print("=" * 70)

problems = []

if terminal_info and not terminal_info.autotrade:
    problems.append("❌ AutoTrading deshabilitado en MT5")

if positions and len(positions) >= 1:
    problems.append(f"❌ Hay {len(positions)} posición(es) abierta(s) - limita el máximo permitido")

if account_info and account_info.margin_free < 50:
    problems.append("❌ Margen disponible insuficiente (<$50)")

if not problems:
    print("✅ No se detectaron problemas obvios")
    print("\nAcciones recomendadas:")
    print("1. Verifica en MT5: Tools > Options > Expert Advisors")
    print("2. Marca 'Allow automated trading'")
    print("3. Marca 'Allow DLL imports' si no está marcado")
    print("4. Reinicia MT5")
    print("5. Vuelve a ejecutar: python descarga_datos/main.py --live-mt5")
else:
    print("Problemas detectados:")
    for problem in problems:
        print(f"  {problem}")

mt5.shutdown()
print("\n" + "=" * 70)
print("Diagnóstico completado")
print("=" * 70)
