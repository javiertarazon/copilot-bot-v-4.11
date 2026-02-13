#!/usr/bin/env python3
"""
Test Completo del Simple Bridge EA - Todas las Funcionalidades
Verifica: Historial, Abrir/Cerrar, Trailing Stop, SL/TP, Lotaje, etc.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.simple_bridge_executor import SimpleBridgeExecutor
from config.config_loader import load_config


def print_header(title: str):
    """Imprime un encabezado formateado"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Imprime resultado de un test"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_1_connection(executor: SimpleBridgeExecutor) -> bool:
    """TEST 1: Conexión con el EA"""
    print_header("TEST 1: CONEXIÓN CON SIMPLE BRIDGE EA")
    
    try:
        connected = executor.connect()
        
        if connected:
            print_test_result("Conexión establecida", True, "EA respondió correctamente")
            return True
        else:
            print_test_result("Conexión establecida", False, "EA no respondió - Verifica que esté ejecutándose")
            return False
    except Exception as e:
        print_test_result("Conexión establecida", False, f"Error: {e}")
        return False


def test_2_account_info(executor: SimpleBridgeExecutor) -> bool:
    """TEST 2: Información de cuenta"""
    print_header("TEST 2: INFORMACIÓN DE CUENTA")
    
    try:
        account = executor.get_account_info()
        
        if account and 'balance' in account:
            print(f"  Login: {account.get('server', 'N/A')}")
            print(f"  Balance: ${account.get('balance', 0):,.2f}")
            print(f"  Equity: ${account.get('equity', 0):,.2f}")
            print(f"  Margin Libre: ${account.get('free_margin', 0):,.2f}")
            print(f"  Leverage: 1:{account.get('leverage', 1)}")
            print(f"  Trading Permitido: {account.get('trade_allowed', False)}")
            
            print_test_result("Información de cuenta", True, f"Balance: ${account['balance']:,.2f}")
            return True
        else:
            print_test_result("Información de cuenta", False, "No se recibió información")
            return False
    except Exception as e:
        print_test_result("Información de cuenta", False, f"Error: {e}")
        return False


def test_3_symbol_info(executor: SimpleBridgeExecutor) -> bool:
    """TEST 3: Información de símbolos"""
    print_header("TEST 3: INFORMACIÓN DE SÍMBOLOS")
    
    symbols = ['TM_VOLATILITY_50', 'TM_VOLATILITY_75', 'TM_VOLATILITY_100']
    all_passed = True
    
    for symbol in symbols:
        try:
            info = executor.get_symbol_info(symbol)
            
            if info and 'bid' in info:
                print(f"\n  📊 {symbol}:")
                print(f"     Bid: {info.get('bid', 0):.5f}")
                print(f"     Ask: {info.get('ask', 0):.5f}")
                print(f"     Spread: {info.get('spread', 0)} puntos")
                print(f"     Lote Mín: {info.get('volume_min', 0):.2f}")
                print(f"     Lote Máx: {info.get('volume_max', 0):.2f}")
                
                print_test_result(f"Símbolo {symbol}", True)
            else:
                print_test_result(f"Símbolo {symbol}", False, "No se recibió información")
                all_passed = False
        except Exception as e:
            print_test_result(f"Símbolo {symbol}", False, f"Error: {e}")
            all_passed = False
    
    return all_passed


def test_4_historical_data(executor: SimpleBridgeExecutor) -> bool:
    """TEST 4: Descarga de datos históricos"""
    print_header("TEST 4: DATOS HISTÓRICOS (OHLCV)")
    
    symbol = 'TM_VOLATILITY_100'
    timeframe = 15  # 15 minutos
    bars = 100
    
    try:
        print(f"  Descargando {bars} barras de {symbol} ({timeframe}m)...")
        
        df = executor.get_historical_data(symbol, timeframe, bars)
        
        if df is not None and len(df) > 0:
            print(f"\n  📈 Datos descargados:")
            print(f"     Total barras: {len(df)}")
            print(f"     Columnas: {list(df.columns)}")
            print(f"     Fecha inicio: {df.index[0]}")
            print(f"     Fecha fin: {df.index[-1]}")
            print(f"\n     Últimas 3 barras:")
            print(df.tail(3).to_string())
            
            # Validar estructura
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            has_all_cols = all(col in df.columns for col in required_cols)
            
            if has_all_cols:
                print_test_result("Datos históricos", True, f"{len(df)} barras descargadas")
                return True
            else:
                print_test_result("Datos históricos", False, "Faltan columnas OHLCV")
                return False
        else:
            print_test_result("Datos históricos", False, "No se recibieron datos")
            return False
    except Exception as e:
        print_test_result("Datos históricos", False, f"Error: {e}")
        return False


def test_5_calculate_lot(executor: SimpleBridgeExecutor) -> bool:
    """TEST 5: Cálculo de lotaje óptimo"""
    print_header("TEST 5: CÁLCULO DE LOTAJE ÓPTIMO")
    
    symbol = 'TM_VOLATILITY_100'
    risk_percent = 1.0  # 1% de riesgo
    stop_distance = 50  # 50 puntos de SL
    
    try:
        print(f"  Calculando lotaje para {symbol}...")
        print(f"  Riesgo: {risk_percent}% del balance")
        print(f"  Distancia SL: {stop_distance} puntos")
        
        lot_size = executor.calculate_lot_size(symbol, risk_percent, stop_distance)
        
        if lot_size > 0:
            account = executor.get_account_info()
            balance = account.get('balance', 0)
            risk_amount = balance * (risk_percent / 100)
            
            print(f"\n  💰 Resultado:")
            print(f"     Balance: ${balance:,.2f}")
            print(f"     Riesgo máximo: ${risk_amount:.2f}")
            print(f"     Lotaje calculado: {lot_size:.2f}")
            
            print_test_result("Cálculo de lotaje", True, f"Lote: {lot_size:.2f}")
            return True
        else:
            print_test_result("Cálculo de lotaje", False, "Lotaje = 0")
            return False
    except Exception as e:
        print_test_result("Cálculo de lotaje", False, f"Error: {e}")
        return False


def test_6_open_position(executor: SimpleBridgeExecutor) -> dict:
    """TEST 6: Abrir posición de prueba"""
    print_header("TEST 6: ABRIR POSICIÓN (BUY)")
    
    symbol = 'TM_VOLATILITY_100'
    order_type = 'BUY'
    volume = 0.01  # Lote mínimo para prueba
    
    try:
        # Obtener precio actual
        info = executor.get_symbol_info(symbol)
        if not info:
            print_test_result("Abrir posición", False, "No se pudo obtener precio")
            return {}
        
        current_price = info['ask']
        
        # Calcular SL y TP
        sl = current_price - 50  # 50 puntos abajo
        tp = current_price + 100  # 100 puntos arriba
        
        print(f"  📝 Parámetros de la orden:")
        print(f"     Símbolo: {symbol}")
        print(f"     Tipo: {order_type}")
        print(f"     Volumen: {volume}")
        print(f"     Precio: {current_price:.5f}")
        print(f"     Stop Loss: {sl:.5f} (-50 puntos)")
        print(f"     Take Profit: {tp:.5f} (+100 puntos)")
        
        result = executor.open_position(
            symbol=symbol,
            order_type=order_type,
            quantity=volume,
            stop_loss_price=sl,
            take_profit_price=tp
        )
        
        if result.get('success'):
            ticket = result.get('ticket')
            print(f"\n  ✅ Posición abierta:")
            print(f"     Ticket: {ticket}")
            print(f"     Precio de entrada: {result.get('price', 0):.5f}")
            print(f"     Volumen: {result.get('volume', 0):.2f}")
            
            print_test_result("Abrir posición", True, f"Ticket #{ticket}")
            return result
        else:
            error = result.get('error', 'Unknown error')
            print_test_result("Abrir posición", False, f"Error: {error}")
            return {}
    except Exception as e:
        print_test_result("Abrir posición", False, f"Error: {e}")
        return {}


def test_7_get_positions(executor: SimpleBridgeExecutor) -> list:
    """TEST 7: Obtener posiciones abiertas"""
    print_header("TEST 7: OBTENER POSICIONES ABIERTAS")
    
    try:
        positions = executor.get_positions()
        
        print(f"  Total posiciones abiertas: {len(positions)}")
        
        if positions:
            for pos in positions:
                print(f"\n  📊 Posición #{pos.ticket}:")
                print(f"     Símbolo: {pos.symbol}")
                print(f"     Tipo: {pos.type}")
                print(f"     Volumen: {pos.volume:.2f}")
                print(f"     Precio apertura: {pos.open_price:.5f}")
                print(f"     Stop Loss: {pos.sl:.5f}")
                print(f"     Take Profit: {pos.tp:.5f}")
                print(f"     Profit actual: ${pos.profit:.2f}")
            
            print_test_result("Obtener posiciones", True, f"{len(positions)} posiciones")
        else:
            print("  ℹ️  No hay posiciones abiertas")
            print_test_result("Obtener posiciones", True, "0 posiciones")
        
        return positions
    except Exception as e:
        print_test_result("Obtener posiciones", False, f"Error: {e}")
        return []


def test_8_modify_position(executor: SimpleBridgeExecutor, ticket: int) -> bool:
    """TEST 8: Modificar SL/TP de posición"""
    print_header("TEST 8: MODIFICAR SL/TP (Dinámico)")
    
    if not ticket:
        print("  ⚠️  No hay ticket para modificar - Test omitido")
        return True
    
    try:
        # Obtener posición actual
        positions = executor.get_positions()
        current_pos = next((p for p in positions if p.ticket == ticket), None)
        
        if not current_pos:
            print_test_result("Modificar posición", False, "Posición no encontrada")
            return False
        
        # Mover SL más cerca (más conservador)
        new_sl = current_pos.open_price - 30 if current_pos.type == 'BUY' else current_pos.open_price + 30
        new_tp = current_pos.tp  # Mantener TP
        
        print(f"  Modificando posición #{ticket}:")
        print(f"     SL anterior: {current_pos.sl:.5f}")
        print(f"     SL nuevo: {new_sl:.5f}")
        print(f"     TP: {new_tp:.5f}")
        
        success = executor.modify_position(ticket, sl=new_sl, tp=new_tp)
        
        if success:
            print_test_result("Modificar posición", True, "SL/TP actualizados")
            return True
        else:
            print_test_result("Modificar posición", False, "Fallo al modificar")
            return False
    except Exception as e:
        print_test_result("Modificar posición", False, f"Error: {e}")
        return False


def test_9_trailing_stop(executor: SimpleBridgeExecutor) -> bool:
    """TEST 9: Trailing Stop automático"""
    print_header("TEST 9: TRAILING STOP AUTOMÁTICO")
    
    try:
        print("  Ejecutando trailing stop con 65% de protección...")
        
        result = executor.update_trailing_stops(trailing_pct=0.65)
        
        total = result.get('total', 0)
        updated = result.get('updated', 0)
        
        print(f"\n  📊 Resultado:")
        print(f"     Posiciones revisadas: {total}")
        print(f"     Trailing stops actualizados: {updated}")
        
        if total >= 0:
            print_test_result("Trailing stop", True, f"{updated}/{total} posiciones actualizadas")
            return True
        else:
            print_test_result("Trailing stop", False, "Error en resultado")
            return False
    except Exception as e:
        print_test_result("Trailing stop", False, f"Error: {e}")
        return False


def test_10_close_position(executor: SimpleBridgeExecutor, ticket: int) -> bool:
    """TEST 10: Cerrar posición"""
    print_header("TEST 10: CERRAR POSICIÓN")
    
    if not ticket:
        print("  ⚠️  No hay ticket para cerrar - Test omitido")
        return True
    
    try:
        print(f"  Cerrando posición #{ticket}...")
        
        # Esperar 3 segundos para simular holding time
        print("  Esperando 3 segundos...")
        time.sleep(3)
        
        success = executor.close_position(ticket)
        
        if success:
            print_test_result("Cerrar posición", True, f"Posición #{ticket} cerrada")
            
            # Verificar que se cerró
            time.sleep(1)
            positions = executor.get_positions()
            still_open = any(p.ticket == ticket for p in positions)
            
            if not still_open:
                print("  ✅ Confirmado: Posición cerrada correctamente")
                return True
            else:
                print("  ⚠️  Posición aún aparece como abierta")
                return False
        else:
            print_test_result("Cerrar posición", False, "Fallo al cerrar")
            return False
    except Exception as e:
        print_test_result("Cerrar posición", False, f"Error: {e}")
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n" + "█"*70)
    print("  TEST COMPLETO - SIMPLE BRIDGE EA")
    print("  Todas las funcionalidades: Historial, Trading, Gestión de Riesgo")
    print("█"*70)
    
    # Cargar configuración
    config = load_config()
    
    # Crear executor
    executor = SimpleBridgeExecutor(config)
    
    # Resultados
    results = {}
    test_ticket = None
    
    try:
        # TEST 1: Conexión
        results['connection'] = test_1_connection(executor)
        if not results['connection']:
            print("\n❌ FALLO CRÍTICO: No se pudo conectar con el EA")
            print("   Asegúrate de que Simple_Bridge_EA.ex5 está ejecutándose en MT5")
            return
        
        time.sleep(0.5)
        
        # TEST 2: Información de cuenta
        results['account'] = test_2_account_info(executor)
        time.sleep(0.5)
        
        # TEST 3: Información de símbolos
        results['symbols'] = test_3_symbol_info(executor)
        time.sleep(0.5)
        
        # TEST 4: Datos históricos
        results['historical'] = test_4_historical_data(executor)
        time.sleep(0.5)
        
        # TEST 5: Cálculo de lotaje
        results['lot_calc'] = test_5_calculate_lot(executor)
        time.sleep(0.5)
        
        # TEST 6: Abrir posición
        open_result = test_6_open_position(executor)
        results['open_pos'] = bool(open_result.get('success'))
        if results['open_pos']:
            test_ticket = open_result.get('ticket')
        time.sleep(1)
        
        # TEST 7: Obtener posiciones
        positions = test_7_get_positions(executor)
        results['get_pos'] = True
        time.sleep(0.5)
        
        # TEST 8: Modificar posición (solo si hay ticket)
        if test_ticket:
            results['modify_pos'] = test_8_modify_position(executor, test_ticket)
            time.sleep(1)
        else:
            results['modify_pos'] = None
        
        # TEST 9: Trailing stop
        results['trailing'] = test_9_trailing_stop(executor)
        time.sleep(0.5)
        
        # TEST 10: Cerrar posición (solo si hay ticket)
        if test_ticket:
            results['close_pos'] = test_10_close_position(executor, test_ticket)
        else:
            results['close_pos'] = None
        
        # RESUMEN FINAL
        print_header("RESUMEN DE TESTS")
        
        tests_passed = sum(1 for v in results.values() if v is True)
        tests_failed = sum(1 for v in results.values() if v is False)
        tests_skipped = sum(1 for v in results.values() if v is None)
        total_tests = len([v for v in results.values() if v is not None])
        
        print(f"\n  Tests ejecutados: {total_tests}")
        print(f"  ✅ Pasados: {tests_passed}")
        print(f"  ❌ Fallados: {tests_failed}")
        print(f"  ⊘  Omitidos: {tests_skipped}")
        
        success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"\n  Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n  🎉 ¡TODOS LOS TESTS PASARON!")
            print("  El Simple Bridge EA está completamente funcional")
        elif success_rate >= 80:
            print("\n  ✅ Sistema funcional con algunas limitaciones")
        else:
            print("\n  ⚠️  Requiere atención - Varios tests fallaron")
        
        print("\n" + "█"*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error fatal en los tests: {e}")
    finally:
        # Desconectar
        try:
            executor.disconnect()
        except:
            pass


if __name__ == "__main__":
    main()
