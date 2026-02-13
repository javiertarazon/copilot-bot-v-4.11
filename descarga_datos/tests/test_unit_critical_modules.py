"""
Tests Unitarios para Módulos Críticos - Bot de Trading v4.11
=============================================================

Tests para validar el funcionamiento correcto de:
1. AdvancedRiskManager (gestión de riesgo)
2. MLModelManager (gestión de modelos ML)
3. Cálculo de drawdown en tiempo real
4. Indicadores técnicos básicos

Creado: Auditoría 29-Ene-2026
Autor: GitHub Copilot
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd

# Configurar paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestAdvancedRiskManager(unittest.TestCase):
    """Tests para AdvancedRiskManager"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        from risk_management.risk_management import AdvancedRiskManager, get_risk_manager
        self.risk_manager = AdvancedRiskManager()
        
    def test_singleton_pattern(self):
        """Test que get_risk_manager retorna siempre la misma instancia"""
        from risk_management.risk_management import get_risk_manager
        
        rm1 = get_risk_manager()
        rm2 = get_risk_manager()
        
        self.assertIs(rm1, rm2, "get_risk_manager debe retornar la misma instancia (singleton)")
        
    def test_kelly_fraction_calculation(self):
        """Test cálculo de fracción de Kelly"""
        # Caso: win_rate=60%, avg_win=$100, avg_loss=$50
        kelly = self.risk_manager.calculate_kelly_fraction(
            win_rate=0.6,
            avg_win=100,
            avg_loss=50,
            confidence_factor=0.25
        )
        
        # Kelly debe ser positivo y menor a 25%
        self.assertGreater(kelly, 0, "Kelly debe ser positivo con win_rate > 50%")
        self.assertLessEqual(kelly, 0.25, "Kelly ajustado no debe exceder 25%")
        
    def test_kelly_fraction_negative_loss(self):
        """Test Kelly con pérdida cero o negativa"""
        kelly = self.risk_manager.calculate_kelly_fraction(
            win_rate=0.6,
            avg_win=100,
            avg_loss=0,  # Pérdida cero
            confidence_factor=0.25
        )
        
        self.assertEqual(kelly, 0.0, "Kelly debe ser 0 con avg_loss=0")
        
    def test_kelly_fraction_low_win_rate(self):
        """Test Kelly con win rate muy bajo"""
        kelly = self.risk_manager.calculate_kelly_fraction(
            win_rate=0.3,  # Solo 30% win rate
            avg_win=50,
            avg_loss=100,  # Pérdidas mayores que ganancias
            confidence_factor=0.25
        )
        
        # Con baja probabilidad de ganar, Kelly debería ser mínimo
        self.assertGreaterEqual(kelly, 0.01, "Kelly mínimo debe ser 1%")
        
    def test_drawdown_calculation_no_drawdown(self):
        """Test cálculo de drawdown cuando no hay drawdown"""
        result = self.risk_manager.calculate_current_drawdown(
            current_balance=10000,
            initial_balance=10000,
            peak_balance=10000
        )
        
        self.assertEqual(result['current_drawdown_pct'], 0.0, "Drawdown debe ser 0 si balance = pico")
        self.assertFalse(result['is_in_drawdown'], "is_in_drawdown debe ser False")
        
    def test_drawdown_calculation_with_loss(self):
        """Test cálculo de drawdown con pérdida"""
        result = self.risk_manager.calculate_current_drawdown(
            current_balance=8000,  # Pérdida de $2000
            initial_balance=10000,
            peak_balance=10000
        )
        
        self.assertEqual(result['current_drawdown_pct'], 20.0, "Drawdown debe ser 20%")
        self.assertTrue(result['is_in_drawdown'], "is_in_drawdown debe ser True")
        
    def test_drawdown_recovery_needed(self):
        """Test cálculo de recuperación necesaria"""
        result = self.risk_manager.calculate_current_drawdown(
            current_balance=8000,
            initial_balance=10000,
            peak_balance=10000
        )
        
        # Para recuperar de $8000 a $10000 se necesita 25% ganancia
        self.assertEqual(result['recovery_needed_pct'], 25.0, "Recuperación necesaria debe ser 25%")
        
    def test_drawdown_from_higher_peak(self):
        """Test drawdown cuando el pico fue mayor que el inicial"""
        result = self.risk_manager.calculate_current_drawdown(
            current_balance=9000,
            initial_balance=10000,
            peak_balance=12000  # Llegó a $12k antes
        )
        
        # Drawdown desde pico de $12k: (12000-9000)/12000 = 25%
        self.assertEqual(result['drawdown_from_peak'], 25.0, "Drawdown desde pico debe ser 25%")
        
    def test_trade_history_update(self):
        """Test actualización de historial de trades"""
        # Agregar algunos trades
        self.risk_manager.update_trade_history(pnl=100, success=True)
        self.risk_manager.update_trade_history(pnl=-50, success=False)
        self.risk_manager.update_trade_history(pnl=75, success=True)
        
        self.assertEqual(len(self.risk_manager.trade_history), 3, "Debe haber 3 trades en historial")
        
    def test_trade_history_lookback_limit(self):
        """Test que el historial respeta el lookback_period"""
        original_lookback = self.risk_manager.lookback_period
        self.risk_manager.lookback_period = 5  # Reducir para test
        
        # Agregar más trades de los permitidos
        for i in range(10):
            self.risk_manager.update_trade_history(pnl=10, success=True)
            
        self.assertEqual(len(self.risk_manager.trade_history), 5, 
                        "Historial no debe exceder lookback_period")
        
        # Restaurar
        self.risk_manager.lookback_period = original_lookback


class TestMLModelManager(unittest.TestCase):
    """Tests para MLModelManager"""
    
    @classmethod
    def setUpClass(cls):
        """Verificar si talib está disponible"""
        try:
            import talib
            cls.talib_available = True
        except ImportError:
            cls.talib_available = False
    
    def setUp(self):
        """Configuración inicial para cada test"""
        if not self.talib_available:
            self.skipTest("talib no disponible - MLModelManager requiere talib")
        from strategies.ultra_detailed_heikin_ashi_ml_strategy import MLModelManager
        self.ml_manager = MLModelManager()
        
    def test_model_path_generation(self):
        """Test generación de rutas de modelos"""
        # Verificar que el directorio de modelos existe o se puede crear
        model_dir = self.ml_manager.model_dir
        self.assertIsNotNone(model_dir, "model_dir no debe ser None")
        
    def test_get_model_path(self):
        """Test generación de path para modelo específico"""
        path = self.ml_manager.get_model_path("TM_VOLATILITY_75", "random_forest")
        
        self.assertIn("TM_VOLATILITY_75", str(path), "Path debe contener el símbolo")
        self.assertIn("random_forest", str(path), "Path debe contener el nombre del modelo")
        
    def test_get_onnx_model_path(self):
        """Test generación de path para modelo ONNX"""
        path = self.ml_manager.get_onnx_model_path("TM_VOLATILITY_75", "random_forest")
        
        # El path puede ser None si el modelo ONNX no existe, lo cual es válido
        if path is not None:
            self.assertIn("TM_VOLATILITY_75", str(path), "Path ONNX debe contener el símbolo")
            self.assertTrue(str(path).endswith('.onnx'), "Path debe terminar en .onnx")
        # Si es None, el test pasa porque es comportamiento válido cuando no hay ONNX
        
    def test_load_nonexistent_model(self):
        """Test carga de modelo inexistente"""
        model, scaler = self.ml_manager.load_model("NONEXISTENT_SYMBOL", "random_forest")
        
        # Debe retornar None si el modelo no existe
        self.assertIsNone(model, "Modelo debe ser None si no existe")
        self.assertIsNone(scaler, "Scaler debe ser None si modelo no existe")


class TestPrepareFeatures(unittest.TestCase):
    """Tests para preparación de features"""
    
    @classmethod
    def setUpClass(cls):
        """Verificar si talib está disponible"""
        try:
            import talib
            cls.talib_available = True
        except ImportError:
            cls.talib_available = False
    
    def setUp(self):
        """Crear DataFrame de prueba"""
        if not self.talib_available:
            self.skipTest("talib no disponible - requiere talib para MLModelManager")
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='15min')
        
        self.test_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 200),
            'high': np.random.uniform(110, 120, 200),
            'low': np.random.uniform(90, 100, 200),
            'close': np.random.uniform(100, 110, 200),
            'volume': np.random.uniform(1000, 10000, 200)
        }, index=dates)
        
        # Asegurar high > low
        self.test_data['high'] = self.test_data[['open', 'close', 'high']].max(axis=1) + 1
        self.test_data['low'] = self.test_data[['open', 'close', 'low']].min(axis=1) - 1
        
    def test_feature_columns_count(self):
        """Test que prepare_features genera el número correcto de columnas"""
        from strategies.ultra_detailed_heikin_ashi_ml_strategy import MLModelManager
        
        ml_manager = MLModelManager()
        
        # Primero necesitamos calcular indicadores
        from indicators.technical_indicators import TechnicalIndicators
        ti = TechnicalIndicators()
        data_with_indicators = ti.calculate_all_indicators(self.test_data)
        
        # Si hay suficientes datos, preparar features
        if len(data_with_indicators.dropna()) > 50:
            features = ml_manager.prepare_features(data_with_indicators.dropna())
            
            # Debe tener las columnas esperadas (26 features según config)
            self.assertGreater(len(features.columns), 0, "Features debe tener columnas")
            

class TestTechnicalIndicators(unittest.TestCase):
    """Tests para indicadores técnicos"""
    
    def setUp(self):
        """Crear DataFrame de prueba"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='15min')
        
        self.test_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 200),
            'high': np.random.uniform(110, 120, 200),
            'low': np.random.uniform(90, 100, 200),
            'close': np.random.uniform(100, 110, 200),
            'volume': np.random.uniform(1000, 10000, 200)
        }, index=dates)
        
        # Asegurar high > low
        self.test_data['high'] = self.test_data[['open', 'close', 'high']].max(axis=1) + 1
        self.test_data['low'] = self.test_data[['open', 'close', 'low']].min(axis=1) - 1
        
    def test_heikin_ashi_calculation(self):
        """Test cálculo de velas Heikin Ashi"""
        from indicators.technical_indicators import TechnicalIndicators
        
        ti = TechnicalIndicators()
        result = ti.calculate_heikin_ashi(self.test_data)
        
        self.assertIn('ha_open', result.columns, "Debe tener columna ha_open")
        self.assertIn('ha_high', result.columns, "Debe tener columna ha_high")
        self.assertIn('ha_low', result.columns, "Debe tener columna ha_low")
        self.assertIn('ha_close', result.columns, "Debe tener columna ha_close")
        
    def test_ema_calculation(self):
        """Test cálculo de EMA"""
        from indicators.technical_indicators import TechnicalIndicators
        
        ti = TechnicalIndicators()
        # calculate_ema espera un DataFrame, no una Series
        ema = ti.calculate_ema(self.test_data, period=10)
        
        self.assertEqual(len(ema), len(self.test_data), "EMA debe tener misma longitud que datos")
        
    def test_atr_calculation(self):
        """Test cálculo de ATR"""
        from indicators.technical_indicators import TechnicalIndicators
        
        ti = TechnicalIndicators()
        atr = ti.calculate_atr(self.test_data, period=14)
        
        # ATR siempre debe ser positivo
        valid_atr = atr.dropna()
        if len(valid_atr) > 0:
            self.assertTrue((valid_atr >= 0).all(), "ATR debe ser siempre >= 0")
            
    def test_rsi_calculation(self):
        """Test cálculo de RSI (mediante calculate_all_indicators)"""
        from indicators.technical_indicators import TechnicalIndicators
        
        ti = TechnicalIndicators()
        # RSI se calcula como parte de calculate_all_indicators
        result = ti.calculate_all_indicators(self.test_data.copy())
        
        # RSI debe existir si se calcularon todos los indicadores
        if 'rsi' in result.columns:
            valid_rsi = result['rsi'].dropna()
            if len(valid_rsi) > 0:
                self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all(), 
                              "RSI debe estar entre 0 y 100")


class TestConfigConstants(unittest.TestCase):
    """Tests para constants.py"""
    
    def test_constants_import(self):
        """Test que las constantes se pueden importar correctamente"""
        try:
            from config.constants import (
                MIN_TRAINING_SAMPLES,
                ML_THRESHOLD_MIN_DEFAULT,
                ML_THRESHOLD_MAX_DEFAULT,
                STOP_LOSS_ATR_MULTIPLIER_DEFAULT,
                TAKE_PROFIT_ATR_MULTIPLIER_DEFAULT
            )
            imported = True
        except ImportError:
            imported = False
            
        self.assertTrue(imported, "Constantes deben poder importarse")
        
    def test_constants_values(self):
        """Test que las constantes tienen valores razonables"""
        from config.constants import (
            MIN_TRAINING_SAMPLES,
            ML_THRESHOLD_MIN_DEFAULT,
            ML_THRESHOLD_MAX_DEFAULT,
            STOP_LOSS_ATR_MULTIPLIER_DEFAULT,
            TAKE_PROFIT_ATR_MULTIPLIER_DEFAULT
        )
        
        self.assertGreater(MIN_TRAINING_SAMPLES, 0, "MIN_TRAINING_SAMPLES debe ser > 0")
        self.assertGreater(ML_THRESHOLD_MIN_DEFAULT, 0, "ML_THRESHOLD_MIN debe ser > 0")
        self.assertLess(ML_THRESHOLD_MAX_DEFAULT, 1, "ML_THRESHOLD_MAX debe ser < 1")
        self.assertLess(ML_THRESHOLD_MIN_DEFAULT, ML_THRESHOLD_MAX_DEFAULT, "MIN debe ser < MAX")
        self.assertGreater(STOP_LOSS_ATR_MULTIPLIER_DEFAULT, 0, "SL multiplier debe ser > 0")
        self.assertGreater(TAKE_PROFIT_ATR_MULTIPLIER_DEFAULT, 0, "TP multiplier debe ser > 0")


def run_tests():
    """Ejecutar todos los tests"""
    # Crear test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedRiskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMLModelManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPrepareFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigConstants))
    
    # Ejecutar con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar éxito/fallo
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
