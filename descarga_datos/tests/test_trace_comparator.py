"""
Test Suite for TraceComparator - FASE 4 Task 12
==============================================

Validación completa del módulo trace_comparator.py:
- Carga de signals live y backtest
- Identificación de divergencias
- Cálculo de estadísticas
- Exportación de reportes
- Health checks

Tests: 8 total
- TestInitialization: 2 tests
- TestSignalLoading: 2 tests
- TestDivergenceDetection: 2 tests
- TestReporting: 1 test
- TestStatistics: 1 test
"""

import json
import pytest
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.trace_comparator import (
    TraceComparator, SignalDivergence, ComparisonStats,
    get_trace_comparator, reset_trace_comparator
)
from utils.signal_logger import get_signal_logger, reset_signal_logger, SignalType


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
    test_logger = logging.getLogger("test_trace_comparator")
    test_logger.setLevel(logging.DEBUG)
    return test_logger


@pytest.fixture
def trace_comparator(temp_data_dir, logger):
    """Instancia del TraceComparator para cada test"""
    reset_trace_comparator()
    reset_signal_logger()
    
    comparator = TraceComparator(data_dir=temp_data_dir, logger=logger)
    yield comparator
    
    reset_trace_comparator()
    reset_signal_logger()


@pytest.fixture
def sample_live_signals():
    """Genera signals de trading en vivo de prueba"""
    return [
        {
            'signal_id': 'live_001',
            'timestamp': '2024-10-30T10:00:00Z',
            'unix_timestamp': 1730300400,
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'signal_type': 'BUY',
            'price': 45000.00,
            'ml_confidence': 0.85,
            'indicators': {'rsi': 45, 'trend': 'bullish'},
            'status': 'executed'
        },
        {
            'signal_id': 'live_002',
            'timestamp': '2024-10-30T14:00:00Z',
            'unix_timestamp': 1730314800,
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'signal_type': 'SELL',
            'price': 45500.00,
            'ml_confidence': 0.72,
            'indicators': {'rsi': 72, 'trend': 'bearish'},
            'status': 'executed'
        },
        {
            'signal_id': 'live_003',
            'timestamp': '2024-10-30T18:00:00Z',
            'unix_timestamp': 1730329200,
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'signal_type': 'BUY',
            'price': 45100.00,
            'ml_confidence': 0.80,
            'indicators': {'rsi': 50, 'trend': 'bullish'},
            'status': 'rejected'
        }
    ]


@pytest.fixture
def sample_backtest_signals():
    """Genera signals de backtest de prueba"""
    return [
        {
            'index': 50,
            'timestamp': '2024-10-30T10:00:30Z',
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'price': 45005.00,
            'signal_type': 'BUY',
            'ml_confidence': 0.84,
            'indicators': {'rsi': 45, 'trend': 'bullish'},
            'trade_result': {'pnl': 500.0, 'exit_index': 60}
        },
        {
            'index': 60,
            'timestamp': '2024-10-30T14:00:15Z',
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'price': 45510.00,
            'signal_type': 'SELL',
            'ml_confidence': 0.73,
            'indicators': {'rsi': 72, 'trend': 'bearish'},
            'trade_result': {'pnl': -200.0, 'exit_index': 70}
        }
    ]


# ============================================================================
# TESTS: INICIALIZACIÓN
# ============================================================================

class TestInitialization:
    """Validar inicialización del comparador"""

    def test_trace_comparator_init(self, trace_comparator):
        """Test: Inicializar comparador"""
        assert trace_comparator is not None
        assert trace_comparator.data_dir.exists()
        assert trace_comparator.reports_dir.exists()
        assert trace_comparator.comparisons_run == 0
        assert trace_comparator.divergences_found == 0
        print("✅ TraceComparator initialized successfully")

    def test_health_check(self, trace_comparator):
        """Test: Health check"""
        health = trace_comparator.get_health_check()
        
        assert health['status'] == 'healthy'
        assert health['comparisons_run'] == 0
        assert 'reports_dir' in health
        print(f"✅ Health check: {health}")


# ============================================================================
# TESTS: CARGA DE SIGNALS
# ============================================================================

class TestSignalLoading:
    """Validar carga de signals"""

    def test_load_live_signals(self, trace_comparator, sample_live_signals):
        """Test: Cargar signals en vivo"""
        # Crear signals usando signal logger
        signal_logger = get_signal_logger(data_dir=trace_comparator.data_dir)
        
        for sig in sample_live_signals[:2]:  # Usar primeros 2
            signal_logger.log_signal(
                symbol=sig['symbol'],
                timeframe=sig['timeframe'],
                strategy='TestStrategy',
                signal_type=SignalType[sig['signal_type']],
                price=sig['price'],
                ml_confidence=sig['ml_confidence']
            )
        
        # Cargar usando comparador
        loaded = trace_comparator._load_live_signals('BTC/USDT')
        
        assert len(loaded) >= 2
        assert all(s['symbol'] == 'BTC/USDT' for s in loaded)
        print(f"✅ Loaded {len(loaded)} live signals")

    def test_load_backtest_signals(self, trace_comparator, sample_backtest_signals):
        """Test: Cargar signals de backtest"""
        # Crear archivo de backtest
        backtest_dir = trace_comparator.data_dir / "backtests"
        backtest_dir.mkdir(exist_ok=True)
        
        filepath = backtest_dir / "backtest_signals_BTC_USDT_test001.json"
        with open(filepath, 'w') as f:
            json.dump(sample_backtest_signals, f)
        
        # Cargar
        loaded = trace_comparator._load_backtest_signals('BTC/USDT', run_id='test001')
        
        assert len(loaded) == 2
        assert all(s['symbol'] == 'BTC/USDT' for s in loaded)
        print(f"✅ Loaded {len(loaded)} backtest signals")


# ============================================================================
# TESTS: DETECCIÓN DE DIVERGENCIAS
# ============================================================================

class TestDivergenceDetection:
    """Validar detección de divergencias"""

    def test_find_matching_signals(self, trace_comparator, sample_live_signals, sample_backtest_signals):
        """Test: Identificar signals que coinciden"""
        divergences = trace_comparator._find_divergences(
            sample_live_signals,
            sample_backtest_signals
        )
        
        # Debe encontrar divergencias (signals sin match)
        assert len(divergences) > 0
        
        # Verificar tipos de divergencia
        types = set(d.divergence_type for d in divergences)
        print(f"✅ Found {len(divergences)} divergences: {types}")

    def test_divergence_types(self, trace_comparator):
        """Test: Diferentes tipos de divergencias"""
        live = [
            {
                'symbol': 'BTC/USDT',
                'timeframe': '4h',
                'signal_type': 'BUY',
                'price': 45000.00,
                'ml_confidence': 0.85,
                'timestamp': '2024-10-30T10:00:00Z'
            }
        ]
        
        backtest = []  # Sin signals correspondientes
        
        divergences = trace_comparator._find_divergences(live, backtest)
        
        assert len(divergences) == 1
        assert divergences[0].divergence_type == 'missing_in_backtest'
        print(f"✅ Divergence type detected: {divergences[0].divergence_type}")


# ============================================================================
# TESTS: ESTADÍSTICAS
# ============================================================================

class TestStatistics:
    """Validar cálculo de estadísticas"""

    def test_calculate_comparison_stats(self, trace_comparator, sample_live_signals, sample_backtest_signals):
        """Test: Calcular estadísticas de comparación"""
        divergences = trace_comparator._find_divergences(
            sample_live_signals,
            sample_backtest_signals
        )
        
        stats = trace_comparator._calculate_statistics(
            sample_live_signals,
            sample_backtest_signals,
            divergences
        )
        
        assert stats.total_live_signals == 3
        assert stats.total_backtest_signals == 2
        assert stats.divergences > 0
        assert 0.0 <= stats.match_rate <= 1.0
        
        print(f"✅ Statistics calculated:")
        print(f"   - Total live: {stats.total_live_signals}")
        print(f"   - Total backtest: {stats.total_backtest_signals}")
        print(f"   - Match rate: {stats.match_rate*100:.1f}%")


# ============================================================================
# TESTS: REPORTES
# ============================================================================

class TestReporting:
    """Validar generación de reportes"""

    def test_save_comparison_report(self, trace_comparator):
        """Test: Guardar reporte de comparación"""
        report = {
            'status': 'completed',
            'symbol': 'BTC/USDT',
            'statistics': {
                'total_live_signals': 10,
                'total_backtest_signals': 8,
                'match_rate': 0.8
            },
            'divergences': []
        }
        
        filepath = trace_comparator.save_comparison_report(
            report,
            report_id='test_report_001'
        )
        
        assert Path(filepath).exists()
        
        # Verificar contenido
        with open(filepath, 'r') as f:
            saved = json.load(f)
        
        assert saved['symbol'] == 'BTC/USDT'
        print(f"✅ Report saved to {filepath}")


# ============================================================================
# TESTS: ESTADÍSTICAS DEL COMPARADOR
# ============================================================================

class TestComparatorStats:
    """Validar estadísticas del comparador"""

    def test_get_comparison_statistics(self, trace_comparator):
        """Test: Obtener estadísticas del comparador"""
        stats = trace_comparator.get_comparison_statistics()
        
        assert 'comparisons_run' in stats
        assert 'divergences_found' in stats
        assert stats['comparisons_run'] == 0
        assert stats['divergences_found'] == 0
        
        print(f"✅ Comparator statistics: {stats}")


# ============================================================================
# TESTS: END-TO-END
# ============================================================================

class TestE2E:
    """Test completo end-to-end"""

    def test_full_comparison_flow(self, trace_comparator, sample_live_signals, sample_backtest_signals):
        """Test: Flujo completo de comparación"""
        # 1. Guardar signals de backtest
        backtest_dir = trace_comparator.data_dir / "backtests"
        backtest_dir.mkdir(exist_ok=True)
        
        filepath = backtest_dir / "backtest_signals_BTC_USDT_e2e.json"
        with open(filepath, 'w') as f:
            json.dump(sample_backtest_signals, f)
        
        # 2. Generar signals en vivo usando signal logger
        signal_logger = get_signal_logger(data_dir=trace_comparator.data_dir)
        
        for sig in sample_live_signals:
            signal_logger.log_signal(
                symbol=sig['symbol'],
                timeframe=sig['timeframe'],
                strategy='TestStrategy',
                signal_type=SignalType[sig['signal_type']],
                price=sig['price'],
                ml_confidence=sig['ml_confidence']
            )
        
        # 3. Comparar
        result = trace_comparator.compare_symbol('BTC/USDT', backtest_run_id='e2e')
        
        assert result['status'] == 'completed'
        assert 'statistics' in result
        assert 'divergences' in result
        
        # 4. Guardar reporte
        report_path = trace_comparator.save_comparison_report(result, report_id='e2e')
        assert Path(report_path).exists()
        
        # 5. Verificar health
        health = trace_comparator.get_health_check()
        assert health['status'] == 'healthy'
        assert health['report_files_on_disk'] > 0
        
        print(f"✅ E2E flow completed")
        print(f"   - Report saved: {report_path}")
        print(f"   - Divergences found: {len(result.get('divergences', []))}")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
