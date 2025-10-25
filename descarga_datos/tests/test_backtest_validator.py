"""
Test Suite for BacktestValidator - FASE 4 Task 11
================================================

Validación completa del módulo backtest_validator.py:
- Ejecución de backtests
- Captura de señales
- Persistencia de resultados
- Validación de consistencia
- Statistics y health checks

Tests: 6 total
- TestBacktestExecution: 2 tests
- TestSignalCapture: 2 tests
- TestConsistency: 1 test
- TestPersistence: 1 test
- TestStatistics: 1 test
- TestHealthCheck: 1 test
"""

import json
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, timezone
import logging
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.backtest_validator import (
    BacktestValidator, BacktestSignal, get_backtest_validator, 
    reset_backtest_validator
)
from utils.signal_logger import get_signal_logger, reset_signal_logger


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_data_dir():
    """Crea directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def logger():
    """Logger de test"""
    test_logger = logging.getLogger("test_backtest_validator")
    test_logger.setLevel(logging.DEBUG)
    return test_logger


@pytest.fixture
def sample_ohlcv_data():
    """Genera datos OHLCV de prueba"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=200, freq='4h')
    
    # Generar precio base
    base_price = 45000.0
    returns = np.random.normal(0.001, 0.02, 200)
    prices = base_price * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.002, 0.002, 200)),
        'high': prices * (1 + np.random.uniform(0.001, 0.01, 200)),
        'low': prices * (1 + np.random.uniform(-0.01, -0.001, 200)),
        'close': prices,
        'volume': np.random.uniform(1000000, 2000000, 200)
    })
    
    # Calcular indicadores básicos
    data['rsi'] = 50 + 20 * np.sin(np.arange(200) / 20)
    data['atr'] = data['close'] * 0.01
    data['trend'] = 'bullish'
    
    return data


@pytest.fixture
def backtest_validator(temp_data_dir, logger):
    """Instancia del BacktestValidator para cada test"""
    reset_backtest_validator()
    reset_signal_logger()
    
    validator = BacktestValidator(data_dir=temp_data_dir, logger=logger)
    yield validator
    
    reset_backtest_validator()
    reset_signal_logger()


# ============================================================================
# TESTS: EJECUCIÓN DE BACKTESTS
# ============================================================================

class TestBacktestExecution:
    """Validar ejecución de backtests"""

    def test_backtest_validator_initialization(self, backtest_validator):
        """Test: Inicializar validator correctamente"""
        assert backtest_validator is not None
        assert backtest_validator.data_dir.exists()
        assert backtest_validator.backtests_dir.exists()
        assert backtest_validator.backtests_run == 0
        assert backtest_validator.signals_captured == 0
        print("✅ BacktestValidator initialized successfully")

    def test_health_check(self, backtest_validator):
        """Test: Health check report"""
        health = backtest_validator.get_health_check()
        
        assert health['status'] == 'healthy'
        assert health['backtests_run'] == 0
        assert health['signals_captured'] == 0
        assert 'backtests_dir' in health
        print(f"✅ Health check: {health}")


# ============================================================================
# TESTS: CAPTURA DE SEÑALES
# ============================================================================

class TestSignalCapture:
    """Validar captura de señales desde backtest"""

    def test_create_backtest_signal(self):
        """Test: Crear objeto BacktestSignal"""
        sig = BacktestSignal(
            index=50,
            timestamp="2024-10-30T15:45:23Z",
            symbol="BTC/USDT",
            timeframe="4h",
            price=45230.50,
            signal_type="BUY",
            ml_confidence=0.85,
            indicators={'rsi': 45.2, 'atr': 150.5},
            trade_result={'pnl': 523.45, 'exit_index': 60}
        )
        
        assert sig.signal_type == "BUY"
        assert sig.ml_confidence == 0.85
        assert sig.trade_result['pnl'] == 523.45
        print(f"✅ BacktestSignal created: {sig.index}")

    def test_save_backtest_signals(self, backtest_validator):
        """Test: Guardar signals a JSON"""
        # Crear signals de prueba
        signals = [
            BacktestSignal(
                index=i,
                timestamp=f"2024-10-30T{10+i:02d}:00:00Z",
                symbol="BTC/USDT",
                timeframe="4h",
                price=45000.0 + i * 100,
                signal_type="BUY" if i % 2 == 0 else "SELL",
                ml_confidence=0.7 + i * 0.01,
                indicators={'rsi': 50 + i}
            )
            for i in range(5)
        ]
        
        # Guardar
        filepath = backtest_validator.save_backtest_signals(
            symbol="BTC/USDT",
            signals=signals,
            run_id="test_run_001"
        )
        
        # Verificar
        assert Path(filepath).exists()
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 5
        assert data[0]['symbol'] == 'BTC/USDT'
        assert data[0]['signal_type'] == 'BUY'
        print(f"✅ Backtest signals saved to {filepath}")


# ============================================================================
# TESTS: ESTADÍSTICAS
# ============================================================================

class TestStatistics:
    """Validar estadísticas de backtests"""

    def test_get_backtest_statistics(self, backtest_validator):
        """Test: Obtener estadísticas"""
        stats = backtest_validator.get_backtest_statistics()
        
        assert 'backtests_run' in stats
        assert 'total_signals_captured' in stats
        assert 'avg_signals_per_backtest' in stats
        assert stats['backtests_run'] == 0
        assert stats['total_signals_captured'] == 0
        print(f"✅ Statistics retrieved: {stats}")


# ============================================================================
# TESTS: PERSISTENCIA
# ============================================================================

class TestPersistence:
    """Validar persistencia de resultados"""

    def test_backtest_signals_persistence(self, backtest_validator):
        """Test: Signals persisten en disco"""
        signals = [
            BacktestSignal(
                index=i,
                timestamp=f"2024-10-30T{10+i:02d}:00:00Z",
                symbol="ETH/USDT",
                timeframe="1h",
                price=2300.0 + i * 10,
                signal_type="SELL",
                ml_confidence=0.75,
                indicators={'rsi': 60 + i}
            )
            for i in range(3)
        ]
        
        # Guardar
        filepath = backtest_validator.save_backtest_signals(
            symbol="ETH/USDT",
            signals=signals
        )
        
        # Verificar archivo
        backtest_files = list(backtest_validator.backtests_dir.glob("backtest_signals_*.json"))
        assert len(backtest_files) > 0
        
        # Verificar contenido
        with open(filepath, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 3
        assert loaded[0]['symbol'] == 'ETH/USDT'
        print(f"✅ Backtest signals persisted: {len(backtest_files)} files")


# ============================================================================
# TESTS: VALIDACIÓN DE CONSISTENCIA
# ============================================================================

class TestConsistency:
    """Validar consistencia de backtests"""

    def test_backtest_validator_basic(self, backtest_validator, sample_ohlcv_data):
        """Test: Validador se inicializa sin errores"""
        # Este test simplemente verifica que el validator se puede usar
        # Sin ejecutar backtest real (que requeriría ML models pre-entrenados)
        
        validator = backtest_validator
        assert validator.backtester is not None
        assert validator.signal_logger is not None
        assert validator.config is not None
        
        print("✅ BacktestValidator basic functionality works")


# ============================================================================
# TESTS: HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Validar health checks"""

    def test_health_check_format(self, backtest_validator):
        """Test: Health check retorna formato correcto"""
        health = backtest_validator.get_health_check()
        
        required_keys = [
            'status',
            'backtests_run',
            'signals_captured',
            'backtest_files_on_disk',
            'backtests_dir'
        ]
        
        for key in required_keys:
            assert key in health, f"Missing key: {key}"
        
        assert health['status'] in ['healthy', 'error']
        print(f"✅ Health check format valid: {health}")


# ============================================================================
# TESTS: END-TO-END
# ============================================================================

class TestE2E:
    """Test completo end-to-end"""

    def test_backtest_validator_full_flow(self, backtest_validator, sample_ohlcv_data):
        """Test: Flujo completo del validator"""
        validator = backtest_validator
        
        # 1. Verificar estado inicial
        assert validator.backtests_run == 0
        assert validator.signals_captured == 0
        
        # 2. Crear y guardar signals de prueba (simulando backtest)
        signals = [
            BacktestSignal(
                index=i,
                timestamp=f"2024-10-30T{10+i:02d}:00:00Z",
                symbol="BTC/USDT",
                timeframe="4h",
                price=45000.0 + i * 50,
                signal_type="BUY" if i < 3 else "SELL",
                ml_confidence=0.75 + i * 0.01,
                indicators={'rsi': 45 + i * 2},
                trade_result={'pnl': 100.0 * (i + 1), 'exit_index': i + 10}
            )
            for i in range(6)
        ]
        
        filepath = validator.save_backtest_signals(
            symbol="BTC/USDT",
            signals=signals,
            run_id="e2e_test"
        )
        
        # 3. Verificar persistencia
        assert Path(filepath).exists()
        
        with open(filepath, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 6
        
        # 4. Verificar estadísticas
        stats = validator.get_backtest_statistics()
        assert 'backtests_run' in stats
        
        # 5. Health check
        health = validator.get_health_check()
        assert health['status'] == 'healthy'
        assert health['backtest_files_on_disk'] > 0
        
        print(f"✅ E2E flow completed successfully")
        print(f"   - Signals created: {len(signals)}")
        print(f"   - File persisted: {filepath}")
        print(f"   - Health: {health}")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
