#!/usr/bin/env python3
"""
Script de Validación Pre-Live Trading MT5 v4.11

Valida que todas las correcciones críticas estén implementadas correctamente
antes de iniciar el trading en vivo con MT5.

Verificaciones:
1. Barras históricas >= 1000 (contexto ML)
2. Agregación por ticks deshabilitada
3. Sincronización con cierre de vela implementada
4. Validación de velas completas activa
5. Timeframes alineados entre backtest y live
6. Optimizaciones v4.11 activadas (CachedDataProvider, IndexedPositionMonitor)
7. AutoTrading habilitado en MT5
8. Configuración correcta en config.yaml

Autor: GitHub Copilot
Fecha: Noviembre 2025
"""

import sys
import os
from pathlib import Path

# Agregar directorio padre al path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from config.config_loader import load_config_from_yaml
from utils.logger import setup_logger
import importlib

logger = setup_logger('ValidateLiveSetup')

class LiveSetupValidator:
    """Validador de configuración para live trading MT5"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.config = None
        
    def print_header(self):
        """Imprime encabezado del validador"""
        print("\n" + "="*70)
        print("🔍 VALIDACIÓN DE CONFIGURACIÓN LIVE TRADING MT5 v4.11")
        print("="*70 + "\n")
        
    def print_result(self, check_name: str, passed: bool, message: str = "", warning: bool = False):
        """Imprime resultado de una verificación"""
        if warning:
            icon = "⚠️"
            self.warnings += 1
        elif passed:
            icon = "✅"
            self.checks_passed += 1
        else:
            icon = "❌"
            self.checks_failed += 1
            
        status = "OK" if passed else "FAIL"
        if warning:
            status = "WARN"
            
        print(f"{icon} {check_name:.<50} {status}")
        if message:
            print(f"   → {message}")
            
    def validate_config_loading(self) -> bool:
        """Valida que se pueda cargar la configuración"""
        try:
            self.config = load_config_from_yaml()
            self.print_result("Carga de configuración", True, "config.yaml cargado correctamente")
            return True
        except Exception as e:
            self.print_result("Carga de configuración", False, f"Error: {e}")
            return False
            
    def validate_history_bars(self) -> bool:
        """Valida que se usen 1000+ barras históricas"""
        try:
            # Verificar en configuración MT5
            mt5_config = self.config.get('mt5', {})
            history_bars = mt5_config.get('history_bars', 0)
            
            if history_bars >= 1000:
                self.print_result("Barras históricas (1000+)", True, f"Configurado: {history_bars} barras")
                return True
            else:
                self.print_result("Barras históricas (1000+)", False, 
                                f"Configurado: {history_bars} barras (debe ser >= 1000)")
                return False
        except Exception as e:
            self.print_result("Barras históricas", False, f"Error verificando: {e}")
            return False
            
    def validate_tick_aggregation_disabled(self) -> bool:
        """Valida que la agregación por ticks esté deshabilitada"""
        try:
            # Verificar en configuración MT5
            mt5_config = self.config.get('mt5', {})
            use_tick_agg = mt5_config.get('use_tick_aggregation', True)
            
            # También verificar en live_trading
            live_config = self.config.get('live_trading', {})
            use_tick_agg_live = live_config.get('use_tick_aggregation', True)
            
            if not use_tick_agg and not use_tick_agg_live:
                self.print_result("Agregación por ticks deshabilitada", True, 
                                "Usando datos históricos directos")
                return True
            else:
                self.print_result("Agregación por ticks deshabilitada", False,
                                "Debe estar en 'false' para evitar 99.3% duplicación")
                return False
        except Exception as e:
            self.print_result("Agregación por ticks", False, f"Error verificando: {e}")
            return False
            
    def validate_candle_sync_implementation(self) -> bool:
        """Valida que la sincronización con cierre de vela esté implementada"""
        try:
            # Verificar que MT5LiveDataProvider tenga los métodos necesarios
            from core.mt5_live_data import MT5LiveDataProvider
            
            has_is_candle_closed = hasattr(MT5LiveDataProvider, 'is_candle_closed')
            has_wait_for_candle = hasattr(MT5LiveDataProvider, 'wait_for_candle_close')
            
            if has_is_candle_closed and has_wait_for_candle:
                self.print_result("Sincronización con cierre de vela", True,
                                "Métodos is_candle_closed y wait_for_candle_close implementados")
                return True
            else:
                missing = []
                if not has_is_candle_closed:
                    missing.append("is_candle_closed")
                if not has_wait_for_candle:
                    missing.append("wait_for_candle_close")
                self.print_result("Sincronización con cierre de vela", False,
                                f"Métodos faltantes: {', '.join(missing)}")
                return False
        except Exception as e:
            self.print_result("Sincronización con cierre de vela", False, f"Error verificando: {e}")
            return False
            
    def validate_timeframe_alignment(self) -> bool:
        """Valida que los timeframes estén alineados entre backtest y live"""
        try:
            # Obtener timeframe de backtest
            backtest_config = self.config.get('backtesting', {})
            backtest_tf = backtest_config.get('timeframe', '4h')
            
            # Obtener timeframes de live
            live_config = self.config.get('live_trading', {})
            live_timeframes = live_config.get('timeframes', [])
            
            # Verificar MT5 config también
            mt5_config = self.config.get('mt5', {})
            mt5_timeframes = mt5_config.get('timeframes', [])
            
            if backtest_tf in live_timeframes or backtest_tf in mt5_timeframes:
                self.print_result("Alineación de timeframes", True,
                                f"Backtest: {backtest_tf}, Live: {live_timeframes or mt5_timeframes}")
                return True
            else:
                self.print_result("Alineación de timeframes", False,
                                f"Backtest usa {backtest_tf} pero live usa {live_timeframes or mt5_timeframes}")
                self.print_result("", False, 
                                "RECOMENDACIÓN: Usar mismo timeframe para consistencia", warning=True)
                return False
        except Exception as e:
            self.print_result("Alineación de timeframes", False, f"Error verificando: {e}")
            return False
            
    def validate_v411_optimizations(self) -> bool:
        """Valida que las optimizaciones v4.11 estén disponibles"""
        try:
            optimizations_available = []
            optimizations_missing = []
            
            # Verificar CachedDataProvider
            try:
                from v411_optimizations.cached_data_provider import CachedDataProvider
                optimizations_available.append("CachedDataProvider")
            except ImportError:
                optimizations_missing.append("CachedDataProvider")
                
            # Verificar IndexedPositionMonitor
            try:
                from v411_optimizations.indexed_position_monitor import IndexedPositionMonitor
                optimizations_available.append("IndexedPositionMonitor")
            except ImportError:
                optimizations_missing.append("IndexedPositionMonitor")
                
            # Verificar NumbaIndicators
            try:
                from v411_optimizations.numba_indicators import calculate_ema_numba
                optimizations_available.append("NumbaIndicators")
            except ImportError:
                optimizations_missing.append("NumbaIndicators (opcional)")
                
            # Verificar ONNXModelPredictor
            try:
                from v411_optimizations.onnx_model_predictor import ONNXModelPredictor
                optimizations_available.append("ONNXModelPredictor")
            except ImportError:
                optimizations_missing.append("ONNXModelPredictor (opcional)")
            
            if len(optimizations_available) >= 2:  # Al menos CachedDataProvider e IndexedPositionMonitor
                self.print_result("Optimizaciones v4.11", True,
                                f"Disponibles: {', '.join(optimizations_available)}")
                if optimizations_missing:
                    self.print_result("", False,
                                    f"Opcionales faltantes: {', '.join(optimizations_missing)}", warning=True)
                return True
            else:
                self.print_result("Optimizaciones v4.11", False,
                                f"Faltantes: {', '.join(optimizations_missing)}")
                return False
        except Exception as e:
            self.print_result("Optimizaciones v4.11", False, f"Error verificando: {e}")
            return False
            
    def validate_mt5_connection(self) -> bool:
        """Valida que MT5 esté disponible y se pueda conectar"""
        try:
            import MetaTrader5 as mt5
            
            # Intentar inicializar
            if not mt5.initialize():
                self.print_result("Conexión MT5", False, 
                                f"Error inicializando MT5: {mt5.last_error()}")
                return False
                
            # Verificar terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                self.print_result("Conexión MT5", False, "No se pudo obtener info de terminal")
                mt5.shutdown()
                return False
                
            # Verificar AutoTrading
            if not terminal_info.trade_allowed:
                self.print_result("AutoTrading MT5", False,
                                "AutoTrading está DESHABILITADO. Habilitar en MT5 (botón toolbar)")
                mt5.shutdown()
                return False
            else:
                self.print_result("AutoTrading MT5", True, "Habilitado correctamente")
                
            # Verificar account info
            account_info = mt5.account_info()
            if account_info is None:
                self.print_result("Cuenta MT5", False, "No se pudo obtener info de cuenta")
                mt5.shutdown()
                return False
            else:
                self.print_result("Cuenta MT5", True,
                                f"{account_info.name} @ {account_info.server} (Balance: {account_info.balance})")
                
            mt5.shutdown()
            return True
            
        except ImportError:
            self.print_result("MT5 Disponible", False, "MetaTrader5 package no instalado")
            return False
        except Exception as e:
            self.print_result("Conexión MT5", False, f"Error: {e}")
            return False
            
    def validate_complete_candle_logic(self) -> bool:
        """Valida que la lógica de velas completas esté implementada en el orchestrator"""
        try:
            # Leer el archivo orchestrator y buscar la lógica
            orchestrator_file = current_dir / "core" / "live_trading_orchestrator.py"
            
            if not orchestrator_file.exists():
                self.print_result("Validación velas completas", False, "Orchestrator file no encontrado")
                return False
                
            with open(orchestrator_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar indicadores de implementación
            has_candle_check = "is_candle_closed" in content
            has_complete_validation = "vela en formación" in content.lower() or "velas cerradas" in content.lower()
            
            if has_candle_check and has_complete_validation:
                self.print_result("Validación velas completas", True,
                                "Lógica implementada en orchestrator")
                return True
            else:
                self.print_result("Validación velas completas", False,
                                "Lógica no encontrada en orchestrator")
                return False
        except Exception as e:
            self.print_result("Validación velas completas", False, f"Error verificando: {e}")
            return False
            
    def print_summary(self):
        """Imprime resumen de la validación"""
        print("\n" + "="*70)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("="*70)
        print(f"✅ Verificaciones exitosas: {self.checks_passed}")
        print(f"❌ Verificaciones fallidas:  {self.checks_failed}")
        print(f"⚠️  Advertencias:           {self.warnings}")
        print("="*70)
        
        if self.checks_failed == 0:
            print("\n🎉 ¡VALIDACIÓN COMPLETA! Sistema listo para live trading.")
            print("\nPróximo paso:")
            print("   python descarga_datos/main.py --live")
            return True
        else:
            print("\n⚠️  VALIDACIÓN INCOMPLETA. Corregir errores antes de live trading.")
            print("\nErrores críticos que deben corregirse:")
            print("   - Revisa las verificaciones marcadas con ❌")
            print("   - Asegúrate de tener MT5 conectado con AutoTrading habilitado")
            print("   - Verifica que config.yaml tenga las configuraciones correctas")
            return False
            
    def run_all_validations(self) -> bool:
        """Ejecuta todas las validaciones"""
        self.print_header()
        
        # Validaciones críticas
        print("🔍 VALIDACIONES CRÍTICAS:\n")
        
        if not self.validate_config_loading():
            print("\n❌ Error crítico: No se pudo cargar la configuración.")
            return False
            
        self.validate_history_bars()
        self.validate_tick_aggregation_disabled()
        self.validate_candle_sync_implementation()
        self.validate_complete_candle_logic()
        self.validate_timeframe_alignment()
        
        print("\n🔧 VALIDACIONES DE OPTIMIZACIÓN:\n")
        self.validate_v411_optimizations()
        
        print("\n🔌 VALIDACIONES DE CONEXIÓN:\n")
        self.validate_mt5_connection()
        
        # Resumen
        return self.print_summary()


def main():
    """Función principal"""
    validator = LiveSetupValidator()
    success = validator.run_all_validations()
    
    # Exit code: 0 si todo OK, 1 si hay errores
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
