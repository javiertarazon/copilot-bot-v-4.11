#!/usr/bin/env python3
"""
Test completo de conexión MT5 Live
- Conexión MT5
- Descarga de datos en vivo
- Verificación de balance
- Simulación de operaciones
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_conexion_mt5():
    """Test 1: Conexión MT5"""
    print("="*70)
    print("TEST 1: CONEXIÓN MT5")
    print("="*70)
    
    # Inicializar MT5
    if not mt5.initialize():
        print("❌ Error: No se pudo inicializar MT5")
        return False
    
    print("✅ MT5 inicializado")
    
    # Login
    login = int(os.getenv('MT5_LOGIN'))
    password = os.getenv('MT5_PASSWORD', '').replace('"', '')
    server = os.getenv('MT5_SERVER')
    
    if not mt5.login(login, password=password, server=server):
        print(f"❌ Error: Login fallido - {mt5.last_error()}")
        return False
    
    print(f"✅ Login exitoso: {login}")
    print(f"   Servidor: {server}")
    
    return True


def test_info_cuenta():
    """Test 2: Información de cuenta"""
    print("\n" + "="*70)
    print("TEST 2: INFORMACIÓN DE CUENTA")
    print("="*70)
    
    account = mt5.account_info()
    if account is None:
        print("❌ Error obteniendo info de cuenta")
        return False
    
    print(f"✅ Información de cuenta:")
    print(f"   Login:          {account.login}")
    print(f"   Servidor:       {account.server}")
    print(f"   Balance:        ${account.balance:,.2f}")
    print(f"   Equity:         ${account.equity:,.2f}")
    print(f"   Margin:         ${account.margin:,.2f}")
    print(f"   Free Margin:    ${account.margin_free:,.2f}")
    print(f"   Margin Level:   {account.margin_level:.2f}%")
    print(f"   Profit:         ${account.profit:,.2f}")
    print(f"   Leverage:       1:{account.leverage}")
    print(f"   Moneda:         {account.currency}")
    print(f"   Trade Allowed:  {account.trade_allowed}")
    print(f"   Expert Allowed: {account.trade_expert}")
    
    return True


def test_simbolos_disponibles():
    """Test 3: Símbolos disponibles"""
    print("\n" + "="*70)
    print("TEST 3: SÍMBOLOS VOLATILITY INDEX")
    print("="*70)
    
    simbolos_buscar = ['TM_VOLATILITY_50', 'TM_VOLATILITY_75', 'TM_VOLATILITY_100']
    simbolos_encontrados = []
    
    for symbol in simbolos_buscar:
        info = mt5.symbol_info(symbol)
        if info:
            tick = mt5.symbol_info_tick(symbol)
            simbolos_encontrados.append(symbol)
            
            print(f"\n✅ {symbol}:")
            print(f"   Bid/Ask:     {tick.bid:.5f} / {tick.ask:.5f}")
            print(f"   Spread:      {info.spread} pts")
            print(f"   Trade Mode:  {info.trade_mode} (4=full)")
            print(f"   Vol min/max: {info.volume_min}/{info.volume_max}")
            print(f"   Tick Value:  ${info.trade_tick_value:.2f}")
            print(f"   Disponible:  {'Sí' if info.visible else 'No'}")
        else:
            print(f"\n❌ {symbol}: NO DISPONIBLE")
    
    if not simbolos_encontrados:
        print("\n❌ ERROR: Ningún símbolo Volatility disponible")
        return False
    
    return simbolos_encontrados


def test_descarga_datos_live(symbol, barras=100):
    """Test 4: Descarga de datos en vivo"""
    print("\n" + "="*70)
    print(f"TEST 4: DESCARGA DE DATOS LIVE - {symbol}")
    print("="*70)
    
    # Obtener últimas barras
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, barras)
    
    if rates is None or len(rates) == 0:
        print(f"❌ Error descargando datos de {symbol}")
        return False
    
    print(f"✅ Datos descargados: {len(rates)} barras de 15min")
    print(f"   Periodo: {datetime.fromtimestamp(rates[0]['time'])} → {datetime.fromtimestamp(rates[-1]['time'])}")
    print(f"\n   Última barra:")
    print(f"      Time:   {datetime.fromtimestamp(rates[-1]['time'])}")
    print(f"      Open:   {rates[-1]['open']:.5f}")
    print(f"      High:   {rates[-1]['high']:.5f}")
    print(f"      Low:    {rates[-1]['low']:.5f}")
    print(f"      Close:  {rates[-1]['close']:.5f}")
    print(f"      Volume: {rates[-1]['tick_volume']}")
    
    # Calcular estadísticas
    closes = [r['close'] for r in rates]
    print(f"\n   Estadísticas (últimas {barras} barras):")
    print(f"      Precio máximo:  {max(closes):.5f}")
    print(f"      Precio mínimo:  {min(closes):.5f}")
    print(f"      Precio actual:  {closes[-1]:.5f}")
    print(f"      Volatilidad:    {(max(closes) - min(closes)):.5f}")
    
    return True


def test_ticks_live(symbol, segundos=5):
    """Test 5: Ticks en tiempo real"""
    print("\n" + "="*70)
    print(f"TEST 5: TICKS EN TIEMPO REAL - {symbol} ({segundos}s)")
    print("="*70)
    
    print(f"\nObservando ticks por {segundos} segundos...")
    
    import time
    start_time = time.time()
    tick_count = 0
    last_bid = 0
    
    while time.time() - start_time < segundos:
        tick = mt5.symbol_info_tick(symbol)
        if tick and tick.bid != last_bid:
            tick_count += 1
            print(f"   Tick #{tick_count}: Bid={tick.bid:.5f} Ask={tick.ask:.5f} Spread={tick.ask-tick.bid:.5f}")
            last_bid = tick.bid
        time.sleep(0.1)
    
    print(f"\n✅ Total ticks recibidos: {tick_count} en {segundos}s")
    return True


def test_posiciones_abiertas():
    """Test 6: Posiciones abiertas"""
    print("\n" + "="*70)
    print("TEST 6: POSICIONES ABIERTAS")
    print("="*70)
    
    positions = mt5.positions_get()
    
    if positions is None:
        print("❌ Error obteniendo posiciones")
        return False
    
    print(f"✅ Total posiciones: {len(positions)}")
    
    if len(positions) > 0:
        for pos in positions:
            tipo = "BUY" if pos.type == 0 else "SELL"
            print(f"\n   Posición #{pos.ticket}:")
            print(f"      Símbolo:     {pos.symbol}")
            print(f"      Tipo:        {tipo}")
            print(f"      Volumen:     {pos.volume}")
            print(f"      Precio:      {pos.price_open:.5f}")
            print(f"      SL:          {pos.sl:.5f}")
            print(f"      TP:          {pos.tp:.5f}")
            print(f"      Profit:      ${pos.profit:.2f}")
            print(f"      Tiempo:      {datetime.fromtimestamp(pos.time)}")
    else:
        print("   (No hay posiciones abiertas)")
    
    return True


def test_historial_deals(dias=7):
    """Test 7: Historial de operaciones"""
    print("\n" + "="*70)
    print(f"TEST 7: HISTORIAL DE DEALS (últimos {dias} días)")
    print("="*70)
    
    desde = datetime.now() - timedelta(days=dias)
    hasta = datetime.now()
    
    deals = mt5.history_deals_get(desde, hasta)
    
    if deals is None:
        print("❌ Error obteniendo historial")
        return False
    
    print(f"✅ Total deals: {len(deals)}")
    
    if len(deals) > 0:
        # Mostrar últimos 5 deals
        print(f"\n   Últimos 5 deals:")
        for deal in list(deals)[-5:]:
            tipo_str = "BUY" if deal.type == 0 else "SELL" if deal.type == 1 else "OTHER"
            print(f"      {datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M')}: "
                  f"{deal.symbol} {tipo_str} vol={deal.volume:.2f} profit=${deal.profit:.2f}")
        
        # Calcular profit total
        profit_total = sum(d.profit for d in deals)
        print(f"\n   Profit total ({dias} días): ${profit_total:.2f}")
    else:
        print("   (No hay deals en el periodo)")
    
    return True


def test_capacidad_operacion(symbol):
    """Test 8: Capacidad para operar (simulación)"""
    print("\n" + "="*70)
    print(f"TEST 8: CAPACIDAD PARA OPERAR - {symbol}")
    print("="*70)
    
    # Obtener info del símbolo
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"❌ No se pudo obtener info de {symbol}")
        return False
    
    # Obtener tick actual
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"❌ No se pudo obtener tick de {symbol}")
        return False
    
    # Obtener info de cuenta
    account = mt5.account_info()
    
    print(f"✅ Análisis de capacidad para operar:")
    print(f"\n   Símbolo: {symbol}")
    print(f"      Trade Mode:      {symbol_info.trade_mode} (4=permitido)")
    print(f"      Bid/Ask:         {tick.bid:.5f} / {tick.ask:.5f}")
    print(f"      Vol mín/máx:     {symbol_info.volume_min} / {symbol_info.volume_max}")
    print(f"      Step:            {symbol_info.volume_step}")
    
    print(f"\n   Cuenta:")
    print(f"      Balance:         ${account.balance:,.2f}")
    print(f"      Free Margin:     ${account.margin_free:,.2f}")
    print(f"      Trade Allowed:   {account.trade_allowed}")
    print(f"      Expert Allowed:  {account.trade_expert}")
    
    # Calcular tamaño de lote con 1% riesgo
    riesgo_pct = 0.01
    riesgo_usd = account.balance * riesgo_pct
    
    # Simular SL de 2% del precio
    sl_distance = tick.bid * 0.02
    
    # Calcular lote (simplificado)
    tick_value = symbol_info.trade_tick_value
    lot_size = riesgo_usd / (sl_distance / symbol_info.point * tick_value)
    lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
    
    print(f"\n   Cálculo de operación (1% riesgo):")
    print(f"      Riesgo USD:      ${riesgo_usd:.2f}")
    print(f"      SL distance:     {sl_distance:.5f}")
    print(f"      Lote calculado:  {lot_size:.2f}")
    
    # Verificar si puede operar
    puede_operar = (
        symbol_info.trade_mode == 4 and
        account.trade_allowed and
        account.trade_expert and
        account.margin_free > 0
    )
    
    if puede_operar:
        print(f"\n   ✅ APTO PARA OPERAR")
        print(f"      Se pueden ejecutar operaciones automáticas")
    else:
        print(f"\n   ❌ NO APTO PARA OPERAR")
        if not account.trade_allowed:
            print(f"      - Trading no permitido en la cuenta")
        if not account.trade_expert:
            print(f"      - Expert Advisors no permitidos")
        if symbol_info.trade_mode != 4:
            print(f"      - Símbolo no disponible para trading")
    
    return puede_operar


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("  TEST COMPLETO DE CONEXIÓN MT5 LIVE")
    print("  Bot Trader Copilot v4.11")
    print("="*70)
    print()
    
    try:
        # Test 1: Conexión
        if not test_conexion_mt5():
            return False
        
        # Test 2: Info cuenta
        if not test_info_cuenta():
            return False
        
        # Test 3: Símbolos
        simbolos = test_simbolos_disponibles()
        if not simbolos:
            return False
        
        # Usar primer símbolo disponible
        symbol = simbolos[0]
        
        # Test 4: Descarga datos
        if not test_descarga_datos_live(symbol):
            return False
        
        # Test 5: Ticks live
        if not test_ticks_live(symbol):
            return False
        
        # Test 6: Posiciones
        if not test_posiciones_abiertas():
            return False
        
        # Test 7: Historial
        if not test_historial_deals():
            return False
        
        # Test 8: Capacidad operación
        if not test_capacidad_operacion(symbol):
            return False
        
        # Resumen final
        print("\n" + "="*70)
        print("  ✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("="*70)
        print()
        print("El sistema está listo para:")
        print("  ✅ Conectar con MT5")
        print("  ✅ Descargar datos en vivo")
        print("  ✅ Recibir ticks en tiempo real")
        print("  ✅ Ejecutar operaciones automáticas")
        print()
        print("Para iniciar trading live, ejecuta:")
        print("  cd descarga_datos")
        print("  ..\.venv\Scripts\python.exe main.py --live-mt5")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        mt5.shutdown()
        print("MT5 desconectado")


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
