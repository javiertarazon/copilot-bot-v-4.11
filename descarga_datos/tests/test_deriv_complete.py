#!/usr/bin/env python3
"""
🧪 TEST COMPLETO DE CONECTIVIDAD Y OPERACIONES DERIV MT5

Pruebas exhaustivas para operar con Volatility Indices de Deriv:
1. ✅ Conectividad a MT5
2. ✅ Descarga de datos históricos
3. ✅ Streaming de datos en vivo
4. ✅ Apertura de operaciones (BUY/SELL)
5. ✅ Asignación de TP/SL
6. ✅ Trailing Stop
7. ✅ Cierre de posiciones
8. ✅ Verificación de balance

Author: GitHub Copilot
Date: 1 Noviembre 2025
Version: 1.0
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Utilities para comparación backtest vs live
from utils.backtest_validator import get_backtest_validator
from utils.trace_comparator import get_trace_comparator
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
from utils.stop_loss_calculator import StopLossTakeProfitCalculator

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("❌ ERROR: MetaTrader5 no está instalado")
    print("   Instala con: pip install MetaTrader5")
    sys.exit(1)

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Variables de entorno cargadas desde: {env_file}")
except ImportError:
    pass  # python-dotenv no instalado, usar variables de entorno del sistema


# ==================== CONFIGURACIÓN ====================

# Símbolos de Volatility Indices a probar
TEST_SYMBOLS = [
    "Volatility 75 Index",   # Recomendado principal
    "Volatility 100 Index",  # Alternativa alta volatilidad
    "Volatility 50 Index",   # Alternativa conservadora
]

# Configuración de pruebas
TEST_CONFIG = {
    "timeframe": "15m",           # Timeframe para datos históricos
    "days_back": 30,              # Días de historia a descargar
    "test_volume": 0.001,         # Volumen mínimo para pruebas (0.001 lotes = 10 centavos)
    "test_sl_points": 10000,      # Stop Loss en puntos para prueba (100 en precio real)
    "test_tp_points": 20000,      # Take Profit en puntos para prueba (200 en precio real)
    "trailing_stop_points": 5000, # Trailing stop en puntos (50 en precio real)
    "max_test_duration": 60,      # Duración máxima de prueba en vivo (segundos)
}


# ==================== CLASE PRINCIPAL ====================

class DerivTester:
    """Tester completo para operaciones con Deriv MT5."""
    
    def __init__(self, login: int, password: str, server: str = "Deriv-Demo"):
        """
        Inicializa el tester.
        
        Args:
            login: Número de cuenta demo Deriv
            password: Password de la cuenta
            server: Servidor MT5 (default: Deriv-Demo)
        """
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        self.test_results = {}
        
        # Directorio de salida para logs
        self.output_dir = Path(__file__).parent.parent / "data" / "deriv_tests"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de log
        self.log_file = self.output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        # Últimos ticks capturados durante streaming (DataFrame)
        self.last_live_ticks_df = None
    
    def log(self, message: str, level: str = "INFO"):
        """Registra mensaje en consola y archivo."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    
    # ==================== TEST 1: CONECTIVIDAD ====================
    
    def test_connectivity(self) -> bool:
        """
        Test 1: Verifica conectividad a Deriv MT5.
        
        Returns:
            True si la conexión es exitosa
        """
        self.log("\n" + "="*70)
        self.log("TEST 1: CONECTIVIDAD A DERIV MT5")
        self.log("="*70)
        
        try:
            # Inicializar MT5
            if not mt5.initialize():
                self.log(f"❌ Error al inicializar MT5: {mt5.last_error()}", "ERROR")
                return False
            
            # Conectar con credenciales
            if not mt5.login(login=self.login, password=self.password, server=self.server):
                self.log(f"❌ Error al conectar: {mt5.last_error()}", "ERROR")
                return False
            
            # Verificar información de cuenta
            account_info = mt5.account_info()
            if account_info is None:
                self.log("❌ No se pudo obtener información de cuenta", "ERROR")
                return False
            
            self.log(f"\n✅ CONECTADO EXITOSAMENTE")
            self.log(f"   Cuenta: {account_info.login}")
            self.log(f"   Nombre: {account_info.name}")
            self.log(f"   Servidor: {account_info.server}")
            self.log(f"   Balance: ${account_info.balance:,.2f}")
            self.log(f"   Equity: ${account_info.equity:,.2f}")
            self.log(f"   Margen: ${account_info.margin:,.2f}")
            self.log(f"   Margen Libre: ${account_info.margin_free:,.2f}")
            self.log(f"   Nivel Margen: {account_info.margin_level:.2f}%")
            self.log(f"   Moneda: {account_info.currency}")
            self.log(f"   Apalancamiento: 1:{account_info.leverage}")
            
            self.connected = True
            self.test_results["connectivity"] = {
                "status": "PASSED",
                "account": account_info.login,
                "server": account_info.server,
                "balance": float(account_info.balance),
                "equity": float(account_info.equity),
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error en test de conectividad: {e}", "ERROR")
            self.test_results["connectivity"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 2: VERIFICAR SÍMBOLOS ====================
    
    def test_symbol_availability(self) -> bool:
        """
        Test 2: Verifica disponibilidad de símbolos Volatility Indices.
        
        Returns:
            True si al menos un símbolo está disponible
        """
        self.log("\n" + "="*70)
        self.log("TEST 2: DISPONIBILIDAD DE SÍMBOLOS")
        self.log("="*70)
        
        try:
            available_symbols = {}
            
            for symbol in TEST_SYMBOLS:
                self.log(f"\n🔍 Verificando {symbol}...")
                
                # Verificar si existe
                symbol_info = mt5.symbol_info(symbol)
                
                if symbol_info is None:
                    self.log(f"   ❌ No disponible", "WARNING")
                    available_symbols[symbol] = False
                else:
                    # Verificar si se puede seleccionar
                    if not mt5.symbol_select(symbol, True):
                        self.log(f"   ⚠️  Disponible pero no se puede seleccionar", "WARNING")
                        available_symbols[symbol] = False
                    else:
                        self.log(f"   ✅ Disponible y seleccionado")
                        self.log(f"      Descripción: {symbol_info.description}")
                        self.log(f"      Spread: {symbol_info.spread} puntos")
                        self.log(f"      Digits: {symbol_info.digits}")
                        self.log(f"      Tick Size: {symbol_info.point}")
                        self.log(f"      Min Volume: {symbol_info.volume_min}")
                        self.log(f"      Max Volume: {symbol_info.volume_max}")
                        self.log(f"      Volume Step: {symbol_info.volume_step}")
                        available_symbols[symbol] = True
            
            # Resumen
            available_count = sum(available_symbols.values())
            self.log(f"\n📊 RESUMEN: {available_count}/{len(TEST_SYMBOLS)} símbolos disponibles")
            
            self.test_results["symbol_availability"] = {
                "status": "PASSED" if available_count > 0 else "FAILED",
                "available_symbols": available_symbols,
                "count": available_count
            }
            
            return available_count > 0
            
        except Exception as e:
            self.log(f"❌ Error en verificación de símbolos: {e}", "ERROR")
            self.test_results["symbol_availability"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 3: DESCARGA DE DATOS HISTÓRICOS ====================
    
    def test_historical_data_download(self, symbol: str) -> bool:
        """
        Test 3: Descarga datos históricos.
        
        Args:
            symbol: Símbolo a descargar
            
        Returns:
            True si la descarga es exitosa
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 3: DESCARGA DE DATOS HISTÓRICOS - {symbol}")
        self.log("="*70)
        
        try:
            # Mapeo de timeframes
            timeframe_map = {
                "1m": mt5.TIMEFRAME_M1,
                "5m": mt5.TIMEFRAME_M5,
                "15m": mt5.TIMEFRAME_M15,
                "30m": mt5.TIMEFRAME_M30,
                "1h": mt5.TIMEFRAME_H1,
                "4h": mt5.TIMEFRAME_H4,
                "1d": mt5.TIMEFRAME_D1,
            }
            
            timeframe_mt5 = timeframe_map.get(TEST_CONFIG["timeframe"], mt5.TIMEFRAME_M15)
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=TEST_CONFIG["days_back"])
            
            self.log(f"\n📥 Descargando datos...")
            self.log(f"   Símbolo: {symbol}")
            self.log(f"   Timeframe: {TEST_CONFIG['timeframe']}")
            self.log(f"   Desde: {start_date.strftime('%Y-%m-%d')}")
            self.log(f"   Hasta: {end_date.strftime('%Y-%m-%d')}")
            
            # Descargar datos
            rates = mt5.copy_rates_range(symbol, timeframe_mt5, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                self.log(f"   ❌ No se pudieron descargar datos", "ERROR")
                return False
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            self.log(f"\n✅ DATOS DESCARGADOS EXITOSAMENTE")
            self.log(f"   Registros: {len(df):,}")
            self.log(f"   Primer registro: {df.iloc[0]['time']}")
            self.log(f"   Último registro: {df.iloc[-1]['time']}")
            self.log(f"   Precio actual: {df.iloc[-1]['close']:.5f}")
            self.log(f"   Rango: {df['low'].min():.5f} - {df['high'].max():.5f}")
            
            # Guardar CSV
            csv_file = self.output_dir / f"{symbol.replace(' ', '_')}_{TEST_CONFIG['timeframe']}.csv"
            df.to_csv(csv_file, index=False)
            self.log(f"   Guardado en: {csv_file}")
            
            # Verificar calidad de datos
            self.log(f"\n📊 CALIDAD DE DATOS:")
            self.log(f"   Datos faltantes: {df.isnull().sum().sum()}")
            self.log(f"   Duplicados: {df.duplicated().sum()}")
            
            self.test_results[f"historical_data_{symbol}"] = {
                "status": "PASSED",
                "records": len(df),
                "first_date": str(df.iloc[0]['time']),
                "last_date": str(df.iloc[-1]['time']),
                "current_price": float(df.iloc[-1]['close']),
                "csv_file": str(csv_file)
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error en descarga de datos históricos: {e}", "ERROR")
            self.test_results[f"historical_data_{symbol}"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 4: DATOS EN VIVO ====================
    
    def test_live_data_stream(self, symbol: str, duration: int = 30) -> bool:
        """
        Test 4: Streaming de datos en vivo.
        
        Args:
            symbol: Símbolo a monitorear
            duration: Duración del test en segundos
            
        Returns:
            True si el streaming funciona correctamente
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 4: STREAMING DE DATOS EN VIVO - {symbol}")
        self.log("="*70)
        
        try:
            self.log(f"\n📡 Monitoreando datos en vivo durante {duration} segundos...")
            
            ticks_received = []
            start_time = time.time()
            
            while (time.time() - start_time) < duration:
                # Obtener último tick
                tick = mt5.symbol_info_tick(symbol)
                
                if tick is None:
                    self.log(f"   ⚠️  No se pudo obtener tick", "WARNING")
                    time.sleep(1)
                    continue
                
                tick_data = {
                    "time": datetime.fromtimestamp(tick.time),
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last,
                    "volume": tick.volume,
                    "spread": tick.ask - tick.bid
                }
                
                ticks_received.append(tick_data)
                
                # Mostrar cada 5 segundos
                if len(ticks_received) % 5 == 0:
                    self.log(f"   Tick #{len(ticks_received)}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}, Spread={tick_data['spread']:.5f}")
                
                time.sleep(1)
            
            if len(ticks_received) == 0:
                self.log(f"   ❌ No se recibieron ticks", "ERROR")
                return False
            
            # Análisis de ticks
            df_ticks = pd.DataFrame(ticks_received)
            # Guardar en la instancia para comparaciones posteriores
            self.last_live_ticks_df = df_ticks.copy()
            
            self.log(f"\n✅ STREAMING COMPLETADO")
            self.log(f"   Ticks recibidos: {len(ticks_received)}")
            self.log(f"   Bid promedio: {df_ticks['bid'].mean():.5f}")
            self.log(f"   Ask promedio: {df_ticks['ask'].mean():.5f}")
            self.log(f"   Spread promedio: {df_ticks['spread'].mean():.5f}")
            self.log(f"   Spread mínimo: {df_ticks['spread'].min():.5f}")
            self.log(f"   Spread máximo: {df_ticks['spread'].max():.5f}")
            
            self.test_results[f"live_data_{symbol}"] = {
                "status": "PASSED",
                "ticks_received": len(ticks_received),
                "avg_bid": float(df_ticks['bid'].mean()),
                "avg_ask": float(df_ticks['ask'].mean()),
                "avg_spread": float(df_ticks['spread'].mean())
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error en streaming de datos: {e}", "ERROR")
            self.test_results[f"live_data_{symbol}"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 5: APERTURA DE OPERACIÓN BUY ====================
    
    def test_open_buy_position(self, symbol: str) -> Optional[int]:
        """
        Test 5: Abre una posición de compra (BUY).
        
        Args:
            symbol: Símbolo a operar
            
        Returns:
            Ticket de la orden si es exitosa, None si falla
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 5: APERTURA DE POSICIÓN BUY - {symbol}")
        self.log("="*70)
        
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.log(f"   ❌ No se pudo obtener información del símbolo", "ERROR")
                return None
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.log(f"   ❌ No se pudo obtener precio actual", "ERROR")
                return None
            
            price = tick.ask
            
            # Calcular SL y TP
            point = symbol_info.point
            sl_price = price - (TEST_CONFIG["test_sl_points"] * point)
            tp_price = price + (TEST_CONFIG["test_tp_points"] * point)
            
            self.log(f"\n📊 PREPARANDO ORDEN BUY:")
            self.log(f"   Símbolo: {symbol}")
            self.log(f"   Volumen: {TEST_CONFIG['test_volume']} lotes")
            self.log(f"   Precio: {price:.5f}")
            self.log(f"   Stop Loss planificado: {sl_price:.5f} ({TEST_CONFIG['test_sl_points']} puntos)")
            self.log(f"   Take Profit planificado: {tp_price:.5f} ({TEST_CONFIG['test_tp_points']} puntos)")
            self.log(f"   Nota: Abriremos SIN SL/TP y los agregaremos después")
            
            # Crear request de orden SIN SL/TP inicialmente
            # (Deriv tiene restricciones específicas sobre niveles de SL/TP)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(TEST_CONFIG["test_volume"]),
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": 20,
                "magic": 123456,
                "comment": "TEST_BUY_DERIV",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill para Deriv
            }
            
            # Enviar orden
            self.log(f"\n📤 Enviando orden BUY...")
            result = mt5.order_send(request)
            
            if result is None:
                self.log(f"   ❌ Error al enviar orden: {mt5.last_error()}", "ERROR")
                return None
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.log(f"   ❌ Orden rechazada: {result.comment} (código: {result.retcode})", "ERROR")
                return None
            
            self.log(f"\n✅ ORDEN BUY EJECUTADA EXITOSAMENTE")
            self.log(f"   Ticket: {result.order}")
            self.log(f"   Volumen: {result.volume}")
            self.log(f"   Precio: {result.price:.5f}")
            self.log(f"   SL/TP: Se agregarán en el siguiente test")
            self.log(f"   Comentario: {result.comment}")
            
            # Agregar SL/TP inmediatamente después de la apertura
            time.sleep(1)  # Pequeña pausa para asegurar que la posición está registrada
            
            modify_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": result.order,
                "sl": sl_price,
                "tp": tp_price,
            }
            
            modify_result = mt5.order_send(modify_request)
            if modify_result and modify_result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log(f"   ✅ SL/TP agregados exitosamente")
                self.log(f"      SL: {sl_price:.5f}")
                self.log(f"      TP: {tp_price:.5f}")
            else:
                self.log(f"   ⚠️  No se pudieron agregar SL/TP (continuamos sin ellos)", "WARNING")
            
            self.test_results[f"open_buy_{symbol}"] = {
                "status": "PASSED",
                "ticket": result.order,
                "volume": float(result.volume),
                "price": float(result.price),
                "sl": float(sl_price),
                "tp": float(tp_price)
            }
            
            return result.order
            
        except Exception as e:
            self.log(f"❌ Error al abrir posición BUY: {e}", "ERROR")
            self.test_results[f"open_buy_{symbol}"] = {"status": "FAILED", "error": str(e)}
            return None
    
    # ==================== TEST 6: MODIFICAR SL/TP ====================
    
    def test_modify_sl_tp(self, symbol: str, ticket: int) -> bool:
        """
        Test 6: Modifica Stop Loss y Take Profit de una posición existente.
        
        Ahora con validación de restricciones del broker para evitar error 10016.
        
        Args:
            symbol: Símbolo de la posición
            ticket: Ticket de la posición
            
        Returns:
            True si la modificación es exitosa
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 6: MODIFICACIÓN DE SL/TP - Ticket {ticket}")
        self.log("="*70)
        
        try:
            # Obtener posición actual
            positions = mt5.positions_get(ticket=ticket)
            
            if positions is None or len(positions) == 0:
                self.log(f"   ❌ Posición no encontrada", "ERROR")
                return False
            
            position = positions[0]
            
            # Obtener restricciones del broker
            constraints = StopLossTakeProfitCalculator.get_broker_constraints(symbol)
            if constraints is None:
                self.log(f"   ❌ No se pudo obtener restricciones del broker", "ERROR")
                return False
            
            self.log(f"\n📋 Restricciones del broker:")
            self.log(f"   Distancia mínima de stop: {constraints.min_stop_distance_points} puntos ({constraints.min_distance_value:.5f})")
            
            # Calcular SL/TP válidos según restricciones del broker
            desired_sl_points = TEST_CONFIG["test_sl_points"] - 100
            desired_tp_points = TEST_CONFIG["test_tp_points"] + 200
            
            adjusted_sl, adjusted_tp, is_valid, adjust_msg = StopLossTakeProfitCalculator.calculate_valid_sl_tp(
                position.price_open,
                position.type,
                desired_sl_points,
                desired_tp_points,
                constraints
            )
            
            self.log(f"\n📊 PREPARANDO MODIFICACIÓN:")
            self.log(f"   Ticket: {ticket}")
            self.log(f"   Tipo: {'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'}")
            self.log(f"   Precio apertura: {position.price_open:.5f}")
            self.log(f"   SL actual: {position.sl:.5f}")
            self.log(f"   TP actual: {position.tp:.5f}")
            self.log(f"\n   SL deseado: {desired_sl_points} puntos")
            self.log(f"   TP deseado: {desired_tp_points} puntos")
            self.log(f"\n   SL ajustado (válido): {adjusted_sl:.5f} ({int(abs(position.price_open - adjusted_sl) / constraints.point)} puntos)")
            self.log(f"   TP ajustado (válido): {adjusted_tp:.5f} ({int(abs(position.price_open - adjusted_tp) / constraints.point)} puntos)")
            self.log(f"   Nota: {adjust_msg}")
            
            if not is_valid:
                self.log(f"   ⚠️ ADVERTENCIA: SL/TP ajustados pero pueden no ser óptimos", "WARNING")
            
            # Crear request de modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": adjusted_sl,
                "tp": adjusted_tp,
            }
            
            # Enviar modificación
            self.log(f"\n📤 Enviando modificación con valores válidos...")
            result = mt5.order_send(request)
            
            if result is None:
                self.log(f"   ❌ Error al modificar: {mt5.last_error()}", "ERROR")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.log(f"   ❌ Modificación rechazada: {result.comment} (código: {result.retcode})", "ERROR")
                return False
            
            self.log(f"\n✅ SL/TP MODIFICADOS EXITOSAMENTE")
            
            self.test_results[f"modify_sltp_{ticket}"] = {
                "status": "PASSED",
                "new_sl": float(adjusted_sl),
                "new_tp": float(adjusted_tp)
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error al modificar SL/TP: {e}", "ERROR")
            self.test_results[f"modify_sltp_{ticket}"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 7: TRAILING STOP ====================
    
    def test_trailing_stop(self, symbol: str, ticket: int, duration: int = 30) -> bool:
        """
        Test 7: Implementa trailing stop durante un período.
        
        Args:
            symbol: Símbolo de la posición
            ticket: Ticket de la posición
            duration: Duración del test en segundos
            
        Returns:
            True si el trailing stop funciona correctamente
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 7: TRAILING STOP - Ticket {ticket}")
        self.log("="*70)
        
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.log(f"   ❌ No se pudo obtener información del símbolo", "ERROR")
                return False
            
            point = symbol_info.point
            trailing_stop = TEST_CONFIG["trailing_stop_points"] * point
            
            self.log(f"\n📊 CONFIGURACIÓN TRAILING STOP:")
            self.log(f"   Distancia: {TEST_CONFIG['trailing_stop_points']} puntos ({trailing_stop:.5f})")
            self.log(f"   Duración: {duration} segundos")
            
            start_time = time.time()
            modifications_count = 0
            
            while (time.time() - start_time) < duration:
                # Obtener posición actual
                positions = mt5.positions_get(ticket=ticket)
                
                if positions is None or len(positions) == 0:
                    self.log(f"   ⚠️  Posición cerrada (SL/TP alcanzado)", "WARNING")
                    break
                
                position = positions[0]
                
                # Obtener precio actual
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    continue
                
                # Calcular nuevo SL según tipo de posición
                if position.type == mt5.ORDER_TYPE_BUY:
                    current_price = tick.bid
                    new_sl = current_price - trailing_stop
                    
                    # Solo modificar si el nuevo SL es mejor que el actual
                    if new_sl > position.sl:
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "symbol": symbol,
                            "position": ticket,
                            "sl": new_sl,
                            "tp": position.tp,
                        }
                        
                        result = mt5.order_send(request)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            modifications_count += 1
                            self.log(f"   ✅ SL ajustado: {position.sl:.5f} → {new_sl:.5f}")
                
                else:  # SELL
                    current_price = tick.ask
                    new_sl = current_price + trailing_stop
                    
                    # Solo modificar si el nuevo SL es mejor que el actual
                    if new_sl < position.sl or position.sl == 0:
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "symbol": symbol,
                            "position": ticket,
                            "sl": new_sl,
                            "tp": position.tp,
                        }
                        
                        result = mt5.order_send(request)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            modifications_count += 1
                            self.log(f"   ✅ SL ajustado: {position.sl:.5f} → {new_sl:.5f}")
                
                time.sleep(2)  # Check cada 2 segundos
            
            self.log(f"\n✅ TRAILING STOP COMPLETADO")
            self.log(f"   Ajustes realizados: {modifications_count}")
            
            self.test_results[f"trailing_stop_{ticket}"] = {
                "status": "PASSED",
                "modifications": modifications_count
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error en trailing stop: {e}", "ERROR")
            self.test_results[f"trailing_stop_{ticket}"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 8: CIERRE DE POSICIÓN ====================
    
    def test_close_position(self, symbol: str, ticket: int) -> bool:
        """
        Test 8: Cierra una posición existente.
        
        Args:
            symbol: Símbolo de la posición
            ticket: Ticket de la posición
            
        Returns:
            True si el cierre es exitoso
        """
        self.log("\n" + "="*70)
        self.log(f"TEST 8: CIERRE DE POSICIÓN - Ticket {ticket}")
        self.log("="*70)
        
        try:
            # Obtener posición actual
            positions = mt5.positions_get(ticket=ticket)
            
            if positions is None or len(positions) == 0:
                self.log(f"   ⚠️  Posición ya cerrada", "WARNING")
                return True
            
            position = positions[0]
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.log(f"   ❌ No se pudo obtener precio actual", "ERROR")
                return False
            
            # Precio de cierre según tipo de orden
            if position.type == mt5.ORDER_TYPE_BUY:
                close_price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL
            else:
                close_price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
            
            self.log(f"\n📊 CERRANDO POSICIÓN:")
            self.log(f"   Ticket: {ticket}")
            self.log(f"   Tipo: {'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'}")
            self.log(f"   Volumen: {position.volume}")
            self.log(f"   Precio apertura: {position.price_open:.5f}")
            self.log(f"   Precio cierre: {close_price:.5f}")
            self.log(f"   P&L: ${position.profit:.2f}")
            
            # Crear request de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(position.volume),
                "type": order_type,
                "position": ticket,
                "price": close_price,
                "deviation": 20,
                "magic": 123456,
                "comment": "TEST_CLOSE_DERIV",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill para Deriv
            }
            
            # Enviar cierre
            self.log(f"\n📤 Enviando orden de cierre...")
            result = mt5.order_send(request)
            
            if result is None:
                self.log(f"   ❌ Error al cerrar: {mt5.last_error()}", "ERROR")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.log(f"   ❌ Cierre rechazado: {result.comment} (código: {result.retcode})", "ERROR")
                return False
            
            self.log(f"\n✅ POSICIÓN CERRADA EXITOSAMENTE")
            self.log(f"   P&L Final: ${position.profit:.2f}")
            
            self.test_results[f"close_position_{ticket}"] = {
                "status": "PASSED",
                "profit": float(position.profit),
                "close_price": float(close_price)
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error al cerrar posición: {e}", "ERROR")
            self.test_results[f"close_position_{ticket}"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== TEST 9: VERIFICAR BALANCE ====================
    
    def test_verify_balance(self) -> bool:
        """
        Test 9: Verifica el balance final de la cuenta.
        
        Returns:
            True si se puede obtener el balance
        """
        self.log("\n" + "="*70)
        self.log("TEST 9: VERIFICACIÓN DE BALANCE FINAL")
        self.log("="*70)
        
        try:
            account_info = mt5.account_info()
            
            if account_info is None:
                self.log(f"   ❌ No se pudo obtener información de cuenta", "ERROR")
                return False
            
            self.log(f"\n💰 BALANCE FINAL:")
            self.log(f"   Balance: ${account_info.balance:,.2f}")
            self.log(f"   Equity: ${account_info.equity:,.2f}")
            self.log(f"   Margen: ${account_info.margin:,.2f}")
            self.log(f"   Margen Libre: ${account_info.margin_free:,.2f}")
            self.log(f"   Nivel Margen: {account_info.margin_level:.2f}%")
            self.log(f"   Profit: ${account_info.profit:,.2f}")
            
            # Comparar con balance inicial
            if "connectivity" in self.test_results:
                initial_balance = self.test_results["connectivity"].get("balance", 0)
                balance_change = account_info.balance - initial_balance
                self.log(f"\n📊 CAMBIO EN BALANCE:")
                self.log(f"   Balance inicial: ${initial_balance:,.2f}")
                self.log(f"   Balance final: ${account_info.balance:,.2f}")
                self.log(f"   Cambio: ${balance_change:,.2f} ({(balance_change/initial_balance)*100:.2f}%)")
            
            self.test_results["final_balance"] = {
                "status": "PASSED",
                "balance": float(account_info.balance),
                "equity": float(account_info.equity),
                "profit": float(account_info.profit)
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error al verificar balance: {e}", "ERROR")
            self.test_results["final_balance"] = {"status": "FAILED", "error": str(e)}
            return False
    
    # ==================== MÉTODO PRINCIPAL ====================
    
    def run_all_tests(self):
        """Ejecuta todos los tests en secuencia."""
        self.log("\n" + "="*70)
        self.log("🧪 INICIANDO BATERÍA COMPLETA DE TESTS DERIV MT5")
        self.log("="*70)
        self.log(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"   Cuenta: {self.login}")
        self.log(f"   Servidor: {self.server}")
        
        try:
            # Test 1: Conectividad
            if not self.test_connectivity():
                self.log("\n❌ Test de conectividad falló. Abortando tests.", "ERROR")
                return
            
            # Test 2: Verificar símbolos
            if not self.test_symbol_availability():
                self.log("\n❌ No hay símbolos disponibles. Abortando tests.", "ERROR")
                return
            
            # Obtener primer símbolo disponible
            available_symbols = self.test_results.get("symbol_availability", {}).get("available_symbols", {})
            test_symbol = None
            for symbol, available in available_symbols.items():
                if available:
                    test_symbol = symbol
                    break
            
            if test_symbol is None:
                self.log("\n❌ No se encontró símbolo para operar. Abortando tests.", "ERROR")
                return
            
            self.log(f"\n✅ Usando símbolo para tests: {test_symbol}")
            
            # Test 3: Descarga de datos históricos
            self.test_historical_data_download(test_symbol)
            
            # Test 4: Datos en vivo
            self.test_live_data_stream(test_symbol, duration=20)
            
            # Test 5: Abrir posición BUY
            ticket = self.test_open_buy_position(test_symbol)
            
            if ticket:
                # Test 6: Modificar SL/TP
                self.test_modify_sl_tp(test_symbol, ticket)
                
                # Test 7: Trailing stop
                self.test_trailing_stop(test_symbol, ticket, duration=30)
                
                # Test 8: Cerrar posición
                self.test_close_position(test_symbol, ticket)

            # Comparar flujo LIVE vs BACKTEST y manejo de datos
            try:
                self.compare_live_vs_backtest(test_symbol)
            except Exception as e:
                self.log(f"⚠️  Error al comparar live vs backtest: {e}", "WARNING")
            
            # Test 9: Verificar balance final
            self.test_verify_balance()
            
            # Resumen final
            self.print_summary()
            
        except KeyboardInterrupt:
            self.log("\n⚠️  Tests interrumpidos por usuario", "WARNING")
        except Exception as e:
            self.log(f"\n❌ Error en ejecución de tests: {e}", "ERROR")
        finally:
            # Desconectar
            mt5.shutdown()
            self.log("\n🔌 Desconectado de MT5")
    
    def print_summary(self):
        """Imprime resumen de todos los tests."""
        self.log("\n" + "="*70)
        self.log("📊 RESUMEN DE TESTS")
        self.log("="*70)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = result.get("status", "UNKNOWN")
            if status == "PASSED":
                passed += 1
                self.log(f"   ✅ {test_name}: PASSED")
            elif status == "FAILED":
                failed += 1
                self.log(f"   ❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            else:
                self.log(f"   ⚠️  {test_name}: {status}")
        
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"\n📈 RESULTADO FINAL:")
        self.log(f"   Total tests: {total}")
        self.log(f"   Exitosos: {passed}")
        self.log(f"   Fallidos: {failed}")
        self.log(f"   Tasa de éxito: {success_rate:.1f}%")
        
        if failed == 0:
            self.log(f"\n🎉 ¡TODOS LOS TESTS PASARON! Sistema listo para operar.")
        else:
            self.log(f"\n⚠️  Algunos tests fallaron. Revisar errores antes de operar.")
        
        self.log(f"\n📄 Log completo guardado en: {self.log_file}")

    # ==================== MÉTODO ADICIONAL: COMPARAR LIVE VS BACKTEST ====================

    def compare_live_vs_backtest(self, symbol: str) -> Dict[str, Any]:
        """
        Ejecuta un backtest con los mismos datos descargados y compara señales
        y el preprocesado entre los datos históricos (backtest) y los datos
        generados en vivo (construidos a partir de ticks).

        Steps:
        - Carga CSV histórico generado por test_historical_data_download
        - Ejecuta _prepare_data() de la estrategia para ambos conjuntos
        - Ejecuta BacktestValidator usando el DataFrame histórico
        - Guarda las señales de backtest y ejecuta TraceComparator
        - Almacena el resultado en self.test_results
        """
        self.log("\n" + "="*70)
        self.log(f"COMPARACIÓN LIVE vs BACKTEST - {symbol}")
        self.log("="*70)

        results: Dict[str, Any] = {"status": "unknown"}

        try:
            # Cargar CSV histórico guardado por el test
            csv_file = self.output_dir / f"{symbol.replace(' ', '_')}_{TEST_CONFIG['timeframe']}.csv"
            if not csv_file.exists():
                self.log(f"   ❌ CSV histórico no encontrado: {csv_file}", "ERROR")
                results['status'] = 'no_historical_csv'
                self.test_results[f"compare_{symbol}"] = results
                return results

            df_hist = pd.read_csv(csv_file)
            # Asegurar columnas y tipos
            if 'time' in df_hist.columns:
                df_hist['time'] = pd.to_datetime(df_hist['time'])

            # Garantizar que exista columna 'volume' (mapear alternativas comunes)
            if 'volume' not in df_hist.columns:
                if 'tick_volume' in df_hist.columns:
                    df_hist = df_hist.rename(columns={'tick_volume': 'volume'})
                    self.log("   Mapeado 'tick_volume' -> 'volume' en CSV histórico")
                elif 'vol' in df_hist.columns:
                    df_hist = df_hist.rename(columns={'vol': 'volume'})
                    self.log("   Mapeado 'vol' -> 'volume' en CSV histórico")
                else:
                    # Si no existe volumen, crear columna con 0 (no ideal pero evita errores)
                    df_hist['volume'] = 0
                    self.log("   Columna 'volume' ausente en CSV histórico: creada con ceros")

            # Instanciar estrategia y preparar datos tal como en backtest
            strat = UltraDetailedHeikinAshiMLStrategy(config=None)
            try:
                hist_processed = strat._prepare_data(df_hist.copy())
            except Exception:
                # Si la estrategia requiere config, intentar con versión sin config
                hist_processed = strat._prepare_data(df_hist.copy())

            self.log(f"   Datos históricos procesados: {len(hist_processed)} filas; columnas: {list(hist_processed.columns)[:8]}")

            # Construir velas desde ticks en vivo (si están disponibles)
            if self.last_live_ticks_df is None or self.last_live_ticks_df.empty:
                self.log("   ⚠️  No hay ticks en vivo disponibles para comparar", "WARNING")
                results['status'] = 'no_live_ticks'
                self.test_results[f"compare_{symbol}"] = results
                return results

            df_ticks = self.last_live_ticks_df.copy()
            df_ticks.set_index('time', inplace=True)

            # Resample a timeframe (ej. '15T' para 15 minutos)
            rule_map = {'1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T', '1h': '60T', '4h': '240T', '1d': '1D'}
            rule = rule_map.get(TEST_CONFIG['timeframe'], '15T')

            # Asegurar columna de volume en ticks
            if 'volume' not in df_ticks.columns:
                if 'vol' in df_ticks.columns:
                    df_ticks = df_ticks.rename(columns={'vol': 'volume'})
                else:
                    df_ticks['volume'] = 0

            # Usar columna 'last' como price para OHLC
            ohlc = df_ticks['last'].resample(rule).agg(['first', 'max', 'min', 'last'])
            vol = df_ticks['volume'].resample(rule).sum().rename('volume')
            ohlc = ohlc.rename(columns={'first': 'open', 'max': 'high', 'min': 'low', 'last': 'close'})
            candles = pd.concat([ohlc, vol], axis=1)
            # Rellenar volume faltante con 0 y no eliminar filas por NaN en otras columnas aún
            candles['volume'] = candles['volume'].fillna(0)
            candles = candles.dropna(subset=['open', 'high', 'low', 'close'])
            candles = candles.reset_index()

            live_processed = strat._prepare_data(candles.copy())
            self.log(f"   Datos live (desde ticks) procesados: {len(live_processed)} filas; columns: {list(live_processed.columns)[:8]}")

            # Comparar esquema básico
            same_columns = list(hist_processed.columns) == list(live_processed.columns)
            cols_hist = set(hist_processed.columns)
            cols_live = set(live_processed.columns)
            common_cols = cols_hist.intersection(cols_live)

            results['data_preprocessing'] = {
                'hist_rows': len(hist_processed),
                'live_rows': len(live_processed),
                'same_columns': same_columns,
                'common_columns_count': len(common_cols)
            }

            # Ejecutar backtest usando el DataFrame histórico
            validator = get_backtest_validator()
            backtest_result = validator.run_backtest_for_symbol(symbol=symbol, timeframe=TEST_CONFIG['timeframe'], data=df_hist)

            # Guardar señales de backtest a archivo para que TraceComparator las cargue
            signals = backtest_result.get('signals', [])
            run_id = datetime.now().isoformat().replace(':', '-')
            try:
                saved_path = validator.save_backtest_signals(symbol, signals, run_id=run_id)
            except Exception:
                saved_path = None

            # Comparar señales live vs backtest
            comparator = get_trace_comparator()
            comparison = comparator.compare_symbol(symbol, backtest_run_id=run_id)

            results['backtest_signals_captured'] = len(signals)
            results['backtest_saved_path'] = saved_path
            results['comparison'] = comparison
            results['status'] = 'completed'

            self.test_results[f"compare_{symbol}"] = results
            self.log(f"   ✅ Comparación LIVE vs BACKTEST completada. Divergencias: {len(comparison.get('divergences', []))}")
            return results

        except Exception as e:
            self.log(f"   ❌ Error comparando live vs backtest: {e}", "ERROR")
            results['status'] = 'error'
            results['error'] = str(e)
            self.test_results[f"compare_{symbol}"] = results
            return results


# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """Función principal."""
    print("="*70)
    print("🧪 TEST COMPLETO DE DERIV MT5 - VOLATILITY INDICES")
    print("="*70)
    print("\nEste script probará:")
    print("  1. Conectividad a Deriv MT5")
    print("  2. Disponibilidad de símbolos")
    print("  3. Descarga de datos históricos")
    print("  4. Streaming de datos en vivo")
    print("  5. Apertura de posición BUY")
    print("  6. Modificación de SL/TP")
    print("  7. Trailing stop")
    print("  8. Cierre de posición")
    print("  9. Verificación de balance")
    
    print("\n⚠️  IMPORTANTE: Usar cuenta DEMO para estos tests")
    print("   No se recomienda usar cuenta real.\n")
    
    # Intentar leer credenciales de variables de entorno
    login = None
    password = None
    server = "Deriv-Demo"
    
    # Intentar primero con DERIV_LOGIN
    if os.getenv("DERIV_LOGIN"):
        login = int(os.getenv("DERIV_LOGIN"))
        password = os.getenv("DERIV_PASSWORD")
        server = os.getenv("DERIV_SERVER", "Deriv-Demo")
        print(f"✅ Credenciales cargadas desde DERIV_* variables\n")
    # Si no existe, intentar con MT5_LOGIN (formato alternativo)
    elif os.getenv("MT5_LOGIN"):
        login = int(os.getenv("MT5_LOGIN"))
        password = os.getenv("MT5_PASSWORD")
        server = os.getenv("MT5_SERVER", "Deriv-Demo")
        print(f"✅ Credenciales cargadas desde MT5_* variables\n")
    
    # Si no hay credenciales en variables de entorno, solicitar interactivamente
    if not login:
        print("📝 No se encontraron credenciales en variables de entorno.")
        print("   Ingresa tus credenciales de Deriv MT5:\n")
        
        # Solicitar credenciales
        login = input("Login de Deriv (número de cuenta): ").strip()
        if not login:
            print("❌ Login requerido")
            return
        
        password = input("Password: ").strip()
        if not password:
            print("❌ Password requerido")
            return
        
        server = input("Servidor [Deriv-Demo]: ").strip() or "Deriv-Demo"
    
    print("\n⏳ Iniciando tests...\n")
    
    try:
        # Crear tester
        tester = DerivTester(
            login=int(login),
            password=password,
            server=server
        )
        
        # Ejecutar todos los tests
        tester.run_all_tests()
        
    except ValueError:
        print("❌ Login debe ser un número")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
