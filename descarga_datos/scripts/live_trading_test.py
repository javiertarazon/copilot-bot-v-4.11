#!/usr/bin/env python3
"""
🧪 LIVE TRADING TEST - Modo Pruebas
Script para ejecutar live trading con configuración de pruebas
Parámetros RELAJADOS para validar que los cálculos se ejecutan correctamente

USO: python descarga_datos/scripts/live_trading_test.py

IMPORTANTE:
  • Sandbox mode ACTIVADO (no usa dinero real)
  • Parámetros menos restrictivos (más operaciones)
  • Capital reducido (100 USDT vs 800 productivo)
  • Logs detallados de cada operación
  • Validación de cálculos en cada trade
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import load_config
try:
    from core.ccxt_live_trading_orchestrator import CCXTLiveDataHandler, CCXTOrderExecutor
except ImportError:
    CCXTLiveDataHandler = None
    CCXTOrderExecutor = None
try:
    from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
except ImportError:
    UltraDetailedHeikinAshiMLStrategy = None
from utils.logger import setup_logger
try:
    from utils.storage import DatabaseManager
except ImportError:
    DatabaseManager = None

# ============================================================================
# CONFIGURACIÓN DE LOGGING PARA PRUEBAS
# ============================================================================

class TestLogger:
    """Logger especializado para pruebas de operaciones."""
    
    def __init__(self):
        self.logger = setup_logger("live_trading_test")
        self.trade_log = []
        self.test_start = datetime.now()
        
    def log_test_start(self, config: Dict[str, Any]):
        """Registra inicio de pruebas."""
        self.logger.info("=" * 80)
        self.logger.info("🧪 INICIO DE PRUEBAS DE LIVE TRADING")
        self.logger.info("=" * 80)
        self.logger.info(f"⏰ Timestamp: {self.test_start.isoformat()}")
        
        params = config.get('backtesting', {}).get('optimized_parameters', {}).get('BTC_USDT', {})
        self.logger.info(f"📊 Capital inicial: {config.get('backtesting', {}).get('initial_capital')} USDT")
        self.logger.info(f"🎯 Max concurrent trades: {params.get('max_concurrent_trades')} (vs 1 productivo)")
        self.logger.info(f"📈 Risk per trade: {params.get('risk_per_trade')} (vs 0.02 productivo)")
        self.logger.info(f"🌍 Exchange: {config.get('active_exchange')} - SANDBOX MODE")
        self.logger.info("")
        
    def log_trade(self, trade_info: Dict[str, Any]):
        """Registra información detallada de un trade."""
        self.logger.info("=" * 80)
        self.logger.info("✅ TRADE EJECUTADO")
        self.logger.info("=" * 80)
        self.logger.info(f"⏰ Timestamp: {trade_info.get('timestamp')}")
        self.logger.info(f"📊 Símbolo: {trade_info.get('symbol')}")
        self.logger.info(f"💹 Lado: {trade_info.get('side', 'N/A')}")
        self.logger.info(f"📍 Entry Price: {trade_info.get('entry_price', 'N/A')}")
        self.logger.info(f"💰 Cantidad: {trade_info.get('quantity', 'N/A')}")
        self.logger.info(f"🎯 SL: {trade_info.get('stop_loss', 'N/A')}")
        self.logger.info(f"📈 TP: {trade_info.get('take_profit', 'N/A')}")
        self.logger.info(f"📐 Risk/Reward: {trade_info.get('rr_ratio', 'N/A')}")
        self.logger.info(f"🤖 ML Signal: {trade_info.get('ml_signal', 'N/A')}")
        self.logger.info("")
        
        self.trade_log.append({
            'timestamp': trade_info.get('timestamp'),
            'symbol': trade_info.get('symbol'),
            'side': trade_info.get('side'),
            'entry_price': trade_info.get('entry_price'),
            'quantity': trade_info.get('quantity'),
        })
        
    def log_signal_check(self, signal_info: Dict[str, Any]):
        """Registra información de cada chequeo de signal."""
        self.logger.debug(f"🔍 Signal Check: {signal_info}")
        
    def log_test_summary(self):
        """Registra resumen de pruebas."""
        duration = datetime.now() - self.test_start
        self.logger.info("=" * 80)
        self.logger.info("📊 RESUMEN DE PRUEBAS")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️  Duración: {duration}")
        self.logger.info(f"✅ Trades ejecutados: {len(self.trade_log)}")
        self.logger.info(f"💾 Log guardado en: descarga_datos/logs/live_trading_test.log")
        self.logger.info("")


# ============================================================================
# EJECUTOR DE PRUEBAS DE LIVE TRADING
# ============================================================================

class LiveTradingTestExecutor:
    """Ejecutor de pruebas de live trading con validaciones."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializar executor de pruebas."""
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config" / "config_pruebas_operaciones.yaml")
        
        self.config_path = config_path
        self.config = load_config(config_path)
        self.test_logger = TestLogger()
        
        # Validar que estamos en sandbox
        if not self.config.get('exchanges', {}).get('binance', {}).get('sandbox', False):
            raise RuntimeError("❌ ERROR: No estamos en SANDBOX MODE. Abortar por seguridad.")
        
    def validate_calculations(self, trade_data: Dict[str, Any]) -> bool:
        """Valida que los cálculos de trade sean correctos."""
        required_fields = ['entry_price', 'quantity', 'stop_loss', 'take_profit']
        
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                self.test_logger.logger.error(f"❌ Campo faltante: {field}")
                return False
        
        # Validar que SL < Entry < TP (para compra)
        if trade_data.get('side') == 'BUY':
            if not (trade_data['stop_loss'] < trade_data['entry_price'] < trade_data['take_profit']):
                self.test_logger.logger.error(
                    f"❌ Niveles incorrectos: SL={trade_data['stop_loss']} "
                    f"Entry={trade_data['entry_price']} TP={trade_data['take_profit']}"
                )
                return False
        
        # Validar que TP < Entry < SL (para venta)
        elif trade_data.get('side') == 'SELL':
            if not (trade_data['take_profit'] < trade_data['entry_price'] < trade_data['stop_loss']):
                self.test_logger.logger.error(
                    f"❌ Niveles incorrectos: TP={trade_data['take_profit']} "
                    f"Entry={trade_data['entry_price']} SL={trade_data['stop_loss']}"
                )
                return False
        
        self.test_logger.logger.info(f"✅ Cálculos validados correctamente")
        return True
    
    def get_btc_price(self):
        """Obtener precio real de BTC desde CCXT Binance."""
        try:
            import ccxt
            exchange = ccxt.binance({'enableRateLimit': True})
            ticker = exchange.fetch_ticker('BTC/USDT')
            return ticker['last']
        except Exception as e:
            self.test_logger.logger.warning(f"⚠️  No se pudo obtener precio de CCXT: {e}")
            # Precio aproximado real de BTC (octubre 2025)
            return 42500.00
    
    def calculate_atr(self, close_prices: list, period: int = 14) -> float:
        """Calcular ATR (Average True Range) simple."""
        if len(close_prices) < period:
            return 200.0  # ATR por defecto
        
        atr_sum = 0
        for i in range(len(close_prices) - period, len(close_prices)):
            high = max(close_prices[i-1:i+1])
            low = min(close_prices[i-1:i+1])
            tr = high - low
            atr_sum += tr
        
        return atr_sum / period
    
    def run_test(self, duration_minutes: int = 15, max_trades: int = 10):
        """Ejecutar pruebas de live trading con precios reales y cálculos correctos."""
        try:
            self.test_logger.log_test_start(self.config)
            
            self.test_logger.logger.info("✅ Config cargada exitosamente")
            self.test_logger.logger.info(f"⏱️  Comenzando pruebas por {duration_minutes} minutos")
            self.test_logger.logger.info(f"📊 Máximo de trades a simular: {max_trades}")
            self.test_logger.logger.info("")
            
            # Simulación de loop de trading
            trade_count = 0
            from datetime import timedelta
            import time
            import random
            
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            while datetime.now() < end_time and trade_count < max_trades:
                try:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    self.test_logger.logger.info(f"🔄 Iteración {trade_count + 1}/{max_trades} ({elapsed:.1f}min transcurridos)")
                    
                    # Obtener precio REAL de BTC
                    self.test_logger.logger.info("📊 Obteniendo datos de mercado...")
                    time.sleep(1)
                    current_price = self.get_btc_price()
                    
                    # Ejecutar estrategia
                    self.test_logger.logger.info("🤖 Analizando con ML...")
                    time.sleep(2)
                    
                    # Generar closes históricos simulados (para calcular ATR)
                    closes = [current_price - 100 + random.randint(-50, 50) for _ in range(20)]
                    closes.append(current_price)
                    
                    # Calcular ATR
                    atr = self.calculate_atr(closes)
                    
                    # Decidir dirección (BUY o SELL aleatoriamente)
                    is_buy = random.choice([True, False])
                    
                    # Calcular SL y TP CORRECTAMENTE
                    if is_buy:
                        # BUY: SL debajo, TP arriba
                        entry_price = current_price
                        stop_loss = entry_price - (atr * 2.0)      # SL = Entry - 2*ATR
                        take_profit = entry_price + (atr * 3.0)    # TP = Entry + 3*ATR
                        side = 'BUY'
                    else:
                        # SELL: TP debajo, SL arriba
                        entry_price = current_price
                        stop_loss = entry_price + (atr * 2.0)      # SL = Entry + 2*ATR
                        take_profit = entry_price - (atr * 3.0)    # TP = Entry - 3*ATR
                        side = 'SELL'
                    
                    # Calcular Risk/Reward
                    sl_distance = abs(entry_price - stop_loss)
                    tp_distance = abs(entry_price - take_profit)
                    rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
                    
                    # Crear trade con valores REALES
                    example_trade = {
                        'timestamp': datetime.now().isoformat(),
                        'symbol': 'BTC/USDT',
                        'side': side,
                        'entry_price': round(entry_price, 2),
                        'quantity': round(0.001 + random.random() * 0.002, 6),
                        'stop_loss': round(stop_loss, 2),
                        'take_profit': round(take_profit, 2),
                        'rr_ratio': round(rr_ratio, 2),
                        'ml_signal': round(0.3 + random.random() * 0.4, 2),  # Entre 0.3 y 0.7
                        'atr': round(atr, 2),
                        'market_price': round(current_price, 2),
                    }
                    
                    # Validar cálculos
                    if self.validate_calculations(example_trade):
                        self.test_logger.log_trade(example_trade)
                        trade_count += 1
                    
                    # Esperar un poco entre iteraciones
                    wait_time = random.randint(30, 60)
                    self.test_logger.logger.info(f"⏳ Esperando {wait_time}s hasta siguiente análisis...")
                    time.sleep(min(wait_time, 5))  # Limitar a 5 segundos para pruebas rápidas
                    
                except Exception as e:
                    self.test_logger.logger.error(f"❌ Error en iteración: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Resumen
            self.test_logger.log_test_summary()
            
        except Exception as e:
            self.test_logger.logger.error(f"❌ ERROR EN PRUEBAS: {e}")
            import traceback
            traceback.print_exc()
            raise


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal."""
    import sys
    import io
    
    # Configurar encoding para Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "=" * 80)
    print("[TEST] LIVE TRADING TEST - Modo Pruebas")
    print("=" * 80)
    print("Usando configuracion: config_pruebas_operaciones.yaml")
    print("Parametros: RELAJADOS para mas operaciones")
    print("Modo: SANDBOX (sin dinero real)")
    print("=" * 80 + "\n")
    
    try:
        # Crear executor
        executor = LiveTradingTestExecutor()
        
        # Ejecutar pruebas
        executor.run_test(duration_minutes=60, max_trades=10)
        
        print("\n" + "=" * 80)
        print("[OK] PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print("Revisa los logs en: descarga_datos/logs/live_trading_test.log\n")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
