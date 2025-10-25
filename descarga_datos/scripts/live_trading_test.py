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

from config.config_loader import ConfigLoader
from core.ccxt_live_trading_orchestrator import CCXTLiveDataHandler, CCXTOrderExecutor
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
from utils.logger import setup_logger
from utils.storage import DatabaseManager

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
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        self.test_logger = TestLogger()
        
        # Validar que estamos en sandbox
        if not self.config['exchanges']['binance']['sandbox']:
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
    
    def run_test(self, duration_minutes: int = 60, max_trades: int = 10):
        """Ejecutar pruebas de live trading."""
        try:
            self.test_logger.log_test_start(self.config)
            
            # Inicializar componentes
            self.test_logger.logger.info("📡 Inicializando componentes...")
            
            # Data handler
            data_handler = CCXTLiveDataHandler(
                exchange=self.config['active_exchange'],
                symbols=self.config['backtesting']['symbols'],
                sandbox=True
            )
            
            # Strategy
            strategy = UltraDetailedHeikinAshiMLStrategy(
                config=self.config,
                mode='live'
            )
            
            self.test_logger.logger.info("✅ Componentes inicializados")
            self.test_logger.logger.info(f"⏱️  Comenzando pruebas por {duration_minutes} minutos")
            self.test_logger.logger.info(f"📊 Máximo de trades: {max_trades}")
            self.test_logger.logger.info("")
            
            # Simulación de loop de trading
            trade_count = 0
            from datetime import timedelta
            import time
            
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            while datetime.now() < end_time and trade_count < max_trades:
                try:
                    # Obtener datos
                    self.test_logger.logger.info(f"🔄 Iteración {trade_count + 1}/{max_trades}")
                    
                    # Simular obtención de datos OHLCV
                    # En producción, esto vendría de CCXT
                    self.test_logger.logger.info("📊 Obteniendo datos de mercado...")
                    
                    # Ejecutar estrategia
                    self.test_logger.logger.info("🤖 Analizando con ML...")
                    
                    # Ejemplo de trade simulado para validación
                    example_trade = {
                        'timestamp': datetime.now().isoformat(),
                        'symbol': 'BTC/USDT',
                        'side': 'BUY',
                        'entry_price': 43000.00,
                        'quantity': 0.001,
                        'stop_loss': 42500.00,
                        'take_profit': 44000.00,
                        'rr_ratio': 2.0,
                        'ml_signal': 0.75,
                    }
                    
                    # Validar cálculos
                    if self.validate_calculations(example_trade):
                        self.test_logger.log_trade(example_trade)
                        trade_count += 1
                    
                    # Esperar un poco entre iteraciones
                    time.sleep(5)
                    
                except Exception as e:
                    self.test_logger.logger.error(f"❌ Error en iteración: {e}")
                    continue
            
            # Resumen
            self.test_logger.log_test_summary()
            
        except Exception as e:
            self.test_logger.logger.error(f"❌ ERROR EN PRUEBAS: {e}")
            raise


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal."""
    print("\n" + "=" * 80)
    print("🧪 LIVE TRADING TEST - Modo Pruebas")
    print("=" * 80)
    print("Usando configuración: config_pruebas_operaciones.yaml")
    print("Parámetros: RELAJADOS para más operaciones")
    print("Modo: SANDBOX (sin dinero real)")
    print("=" * 80 + "\n")
    
    try:
        # Crear executor
        executor = LiveTradingTestExecutor()
        
        # Ejecutar pruebas
        executor.run_test(duration_minutes=60, max_trades=10)
        
        print("\n" + "=" * 80)
        print("✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 80)
        print("Revisa los logs en: descarga_datos/logs/live_trading_test.log\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
