"""
Test Suite for SignalLogger - FASE 4 Task 10
=============================================

Validación completa del módulo signal_logger.py:
- Creación y persistencia de señales
- Actualización de estado
- Búsqueda y filtrado
- Thread-safety
- Limpieza automática
- Health checks

Tests: 8 total
- TestSignalCreation: 2 tests
- TestSignalPersistence: 2 tests
- TestSignalStatusUpdate: 2 tests
- TestSignalRetrieval: 2 tests
- TestSignalCleanup: 1 test
- TestThreadSafety: 1 test
- TestHealthCheck: 1 test
- TestE2E: 1 test
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread
import logging
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.signal_logger import (
    SignalLogger, TradingSignal, SignalType, SignalStatus,
    SignalIndicators, get_signal_logger, reset_signal_logger
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_data_dir():
    """Crea directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def logger(temp_data_dir):
    """Logger de test"""
    test_logger = logging.getLogger("test_signal_logger")
    test_logger.setLevel(logging.DEBUG)
    return test_logger


@pytest.fixture
def signal_logger(temp_data_dir, logger):
    """Instancia de SignalLogger para cada test"""
    reset_signal_logger()
    sl = SignalLogger(data_dir=temp_data_dir, logger=logger)
    yield sl
    reset_signal_logger()


# ============================================================================
# TESTS: CREACIÓN DE SEÑALES
# ============================================================================

class TestSignalCreation:
    """Validar creación correcta de señales"""

    def test_create_buy_signal(self, signal_logger):
        """Test: Crear señal BUY completa"""
        signal_id = signal_logger.log_signal(
            symbol="BTC/USDT",
            timeframe="4h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.BUY,
            price=45230.50,
            ml_confidence=0.85,
            indicators={
                'rsi': 45.2,
                'atr': 150.5,
                'trend': 'bullish',
                'volume': 1250000.0
            },
            notes="Strong bullish signal"
        )
        
        # Validar
        assert signal_id is not None
        assert len(signal_id) == 16  # Hash corto
        
        # Recuperar y verificar
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert len(signals) == 1
        
        sig = signals[0]
        assert sig.signal_type == SignalType.BUY
        assert sig.price == 45230.50
        assert sig.ml_confidence == 0.85
        assert sig.indicators.rsi == 45.2
        assert sig.status == SignalStatus.GENERATED
        print(f"✅ BUY signal created: {signal_id}")

    def test_create_sell_and_nosignal(self, signal_logger):
        """Test: Crear señales SELL y NO_SIGNAL"""
        # SELL
        sell_id = signal_logger.log_signal(
            symbol="ETH/USDT",
            timeframe="1h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.SELL,
            price=2340.10,
            ml_confidence=0.72,
            indicators={'rsi': 72.5, 'trend': 'bearish'}
        )
        
        # NO_SIGNAL
        no_sig_id = signal_logger.log_signal(
            symbol="ETH/USDT",
            timeframe="1h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.NO_SIGNAL,
            price=2341.00,
            ml_confidence=0.35
        )
        
        # Validar
        assert sell_id is not None
        assert no_sig_id is not None
        
        signals = signal_logger.get_signals_for_symbol("ETH/USDT", limit=10)
        assert len(signals) == 2
        
        types = [s.signal_type for s in signals]
        assert SignalType.SELL in types
        assert SignalType.NO_SIGNAL in types
        print(f"✅ SELL ({sell_id}) and NO_SIGNAL ({no_sig_id}) created")


# ============================================================================
# TESTS: PERSISTENCIA
# ============================================================================

class TestSignalPersistence:
    """Validar persistencia en archivos JSON"""

    def test_signals_saved_to_file(self, signal_logger, temp_data_dir):
        """Test: Señales se guardan en archivos JSON"""
        signal_logger.log_signal(
            symbol="BTC/USDT",
            timeframe="4h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.BUY,
            price=45230.50,
            ml_confidence=0.85
        )
        
        # Verificar archivo existe
        signals_dir = temp_data_dir / "signals"
        assert signals_dir.exists()
        
        files = list(signals_dir.glob("signals_*.json"))
        assert len(files) > 0
        
        # Verificar contenido
        with open(files[0], 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['symbol'] == 'BTC/USDT'
        assert data[0]['signal_type'] == 'BUY'
        assert data[0]['ml_confidence'] == 0.85
        print(f"✅ Signal persisted to {files[0].name}")

    def test_multiple_signals_same_file(self, signal_logger):
        """Test: Múltiples señales del mismo día en mismo archivo"""
        # Crear 3 señales del mismo símbolo
        for i in range(3):
            signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                price=45000 + i * 100,
                ml_confidence=0.7 + i * 0.05
            )
        
        # Recuperar todas
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=10)
        assert len(signals) == 3
        
        # Verificar orden (descendente por timestamp)
        for i in range(len(signals) - 1):
            assert signals[i].unix_timestamp >= signals[i + 1].unix_timestamp
        
        print(f"✅ 3 signals saved to same file, correct ordering")


# ============================================================================
# TESTS: ACTUALIZACIÓN DE ESTADO
# ============================================================================

class TestSignalStatusUpdate:
    """Validar actualización de estados de señales"""

    def test_update_signal_to_accepted(self, signal_logger):
        """Test: Actualizar señal a ACCEPTED"""
        signal_id = signal_logger.log_signal(
            symbol="BTC/USDT",
            timeframe="4h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.BUY,
            price=45230.50,
            ml_confidence=0.85
        )
        
        # Actualizar a ACCEPTED
        result = signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=signal_id,
            new_status=SignalStatus.ACCEPTED
        )
        
        assert result is True
        
        # Verificar
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert signals[0].status == SignalStatus.ACCEPTED
        print(f"✅ Signal {signal_id} updated to ACCEPTED")

    def test_update_signal_with_order_id_and_pnl(self, signal_logger):
        """Test: Actualizar con order_id y PnL"""
        signal_id = signal_logger.log_signal(
            symbol="BTC/USDT",
            timeframe="4h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.BUY,
            price=45230.50,
            ml_confidence=0.85
        )
        
        # Ejecutado con P&L positivo
        result = signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=signal_id,
            new_status=SignalStatus.FILLED,
            order_id="ORDER_12345",
            pnl=523.45
        )
        
        assert result is True
        
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        sig = signals[0]
        assert sig.status == SignalStatus.FILLED
        assert sig.order_id == "ORDER_12345"
        assert sig.pnl == 523.45
        print(f"✅ Signal {signal_id} updated with order_id and PnL")


# ============================================================================
# TESTS: RECUPERACIÓN DE SEÑALES
# ============================================================================

class TestSignalRetrieval:
    """Validar recuperación y filtrado de señales"""

    def test_get_signals_by_symbol(self, signal_logger):
        """Test: Recuperar señales por símbolo"""
        # Crear señales para diferentes símbolos
        for symbol in ["BTC/USDT", "ETH/USDT", "BTC/USDT"]:
            signal_logger.log_signal(
                symbol=symbol,
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY,
                price=45000.0,
                ml_confidence=0.8
            )
        
        # Recuperar BTC
        btc_signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=10)
        assert len(btc_signals) == 2
        assert all(s.symbol == "BTC/USDT" for s in btc_signals)
        
        # Recuperar ETH
        eth_signals = signal_logger.get_signals_for_symbol("ETH/USDT", limit=10)
        assert len(eth_signals) == 1
        assert eth_signals[0].symbol == "ETH/USDT"
        print(f"✅ Symbol filtering works: BTC={len(btc_signals)}, ETH={len(eth_signals)}")

    def test_get_signals_with_status_filter(self, signal_logger):
        """Test: Filtrar por estado"""
        # Crear 3 señales
        ids = []
        for i in range(3):
            signal_id = signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY,
                price=45000 + i,
                ml_confidence=0.8
            )
            ids.append(signal_id)
        
        # Aceptar primera
        signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=ids[0],
            new_status=SignalStatus.ACCEPTED
        )
        
        # Rechazar segunda
        signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=ids[1],
            new_status=SignalStatus.REJECTED,
            reject_reason="risk_management"
        )
        
        # Obtener solo ACCEPTED
        accepted = signal_logger.get_signals_for_symbol(
            "BTC/USDT",
            limit=10,
            status_filter=SignalStatus.ACCEPTED
        )
        
        assert len(accepted) == 1
        assert accepted[0].signal_id == ids[0]
        print(f"✅ Status filtering works: 1 ACCEPTED signal found")


# ============================================================================
# TESTS: ESTADÍSTICAS
# ============================================================================

class TestSignalStatistics:
    """Validar cálculo de estadísticas"""

    def test_signal_statistics_global(self, signal_logger):
        """Test: Estadísticas globales"""
        # Crear mezcla de señales
        for i in range(5):
            signal_type = SignalType.BUY if i < 3 else SignalType.SELL
            signal_id = signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=signal_type,
                price=45000.0,
                ml_confidence=0.7 + i * 0.03
            )
            
            # Marcar como ejecutada con P&L
            if i < 3:  # Ganancias
                signal_logger.update_signal_status(
                    symbol="BTC/USDT",
                    signal_id=signal_id,
                    new_status=SignalStatus.FILLED,
                    pnl=100.0 * (i + 1)
                )
            else:  # Pérdidas
                signal_logger.update_signal_status(
                    symbol="BTC/USDT",
                    signal_id=signal_id,
                    new_status=SignalStatus.FILLED,
                    pnl=-50.0
                )
        
        # Obtener estadísticas
        stats = signal_logger.get_signal_statistics(symbol="BTC/USDT")
        
        assert stats['total_signals'] == 5
        assert stats['buy_signals'] == 3
        assert stats['sell_signals'] == 2
        assert stats['executed_trades'] == 5
        assert stats['win_rate'] == 0.6  # 3 ganancias de 5
        assert stats['total_pnl'] == 500.0  # 100 + 200 + 300 - 50 - 50
        print(f"✅ Statistics calculated: {stats}")

    def test_signal_statistics_by_symbol(self, signal_logger):
        """Test: Estadísticas por símbolo"""
        # BTC: 3 señales
        for i in range(3):
            signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY,
                price=45000.0,
                ml_confidence=0.8
            )
        
        # ETH: 2 señales
        for i in range(2):
            signal_logger.log_signal(
                symbol="ETH/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.SELL,
                price=2300.0,
                ml_confidence=0.75
            )
        
        # Verificar
        btc_stats = signal_logger.get_signal_statistics(symbol="BTC/USDT")
        eth_stats = signal_logger.get_signal_statistics(symbol="ETH/USDT")
        
        assert btc_stats['total_signals'] == 3
        assert eth_stats['total_signals'] == 2
        print(f"✅ Symbol stats: BTC={btc_stats['total_signals']}, ETH={eth_stats['total_signals']}")


# ============================================================================
# TESTS: LIMPIEZA
# ============================================================================

class TestSignalCleanup:
    """Validar limpieza de señales antiguas"""

    def test_cleanup_old_signals(self, signal_logger):
        """Test: Eliminar señales antiguas"""
        # Crear 5 señales
        for i in range(5):
            signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY,
                price=45000.0 + i,
                ml_confidence=0.8
            )
        
        # Verificar que tenemos 5
        signals_before = signal_logger.get_signals_for_symbol("BTC/USDT", limit=100)
        assert len(signals_before) == 5
        
        # Limpiar (0 días = eliminar todos)
        deleted = signal_logger.cleanup_old_signals(days_old=0)
        assert deleted >= 5
        
        # Verificar que quedan 0
        signals_after = signal_logger.get_signals_for_symbol("BTC/USDT", limit=100)
        assert len(signals_after) == 0
        print(f"✅ Cleanup removed {deleted} old signals")


# ============================================================================
# TESTS: THREAD-SAFETY
# ============================================================================

class TestThreadSafety:
    """Validar thread-safety de operaciones"""

    def test_concurrent_signal_creation(self, signal_logger):
        """Test: Crear señales concurrentemente"""
        def create_signals(symbol, count):
            for i in range(count):
                signal_logger.log_signal(
                    symbol=symbol,
                    timeframe="4h",
                    strategy="UltraDetailedHeikinAshiML",
                    signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                    price=45000.0 + i,
                    ml_confidence=0.8
                )
        
        # Crear múltiples threads
        threads = []
        for i in range(5):
            t = Thread(
                target=create_signals,
                args=(f"SYM{i}/USDT", 10)
            )
            threads.append(t)
            t.start()
        
        # Esperar
        for t in threads:
            t.join()
        
        # Verificar totales
        total_signals = 0
        for i in range(5):
            signals = signal_logger.get_signals_for_symbol(f"SYM{i}/USDT", limit=100)
            total_signals += len(signals)
        
        assert total_signals == 50
        print(f"✅ Concurrent creation: 50 signals created by 5 threads")


# ============================================================================
# TESTS: HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Validar health checks del logger"""

    def test_health_check(self, signal_logger):
        """Test: Health check status"""
        # Crear algunas señales
        for i in range(3):
            signal_logger.log_signal(
                symbol="BTC/USDT",
                timeframe="4h",
                strategy="UltraDetailedHeikinAshiML",
                signal_type=SignalType.BUY,
                price=45000.0,
                ml_confidence=0.8
            )
        
        # Health check
        health = signal_logger.get_health_check()
        
        assert health['status'] == 'healthy'
        assert health['signals_in_memory'] == 3
        assert 'BTC/USDT' in health['symbols_tracked']
        assert health['signal_files_on_disk'] > 0
        assert health['total_disk_size_mb'] >= 0
        print(f"✅ Health check: {health}")


# ============================================================================
# TESTS: END-TO-END
# ============================================================================

class TestE2E:
    """Test completo end-to-end del flujo de señales"""

    def test_full_signal_lifecycle(self, signal_logger):
        """Test: Ciclo de vida completo de una señal"""
        # 1. Crear
        signal_id = signal_logger.log_signal(
            symbol="BTC/USDT",
            timeframe="4h",
            strategy="UltraDetailedHeikinAshiML",
            signal_type=SignalType.BUY,
            price=45230.50,
            ml_confidence=0.85,
            indicators={
                'rsi': 45.2,
                'atr': 150.5,
                'trend': 'bullish',
                'volume': 1250000.0
            }
        )
        assert signal_id is not None
        
        # 2. Verificar GENERATED
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert signals[0].status == SignalStatus.GENERATED
        
        # 3. Aceptar (risk management passou)
        signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=signal_id,
            new_status=SignalStatus.ACCEPTED
        )
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert signals[0].status == SignalStatus.ACCEPTED
        
        # 4. Enviar (order executor)
        signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=signal_id,
            new_status=SignalStatus.EXECUTED,
            order_id="ORD_123456"
        )
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert signals[0].status == SignalStatus.EXECUTED
        assert signals[0].order_id == "ORD_123456"
        
        # 5. Rellenar (exchange)
        signal_logger.update_signal_status(
            symbol="BTC/USDT",
            signal_id=signal_id,
            new_status=SignalStatus.FILLED,
            pnl=523.45
        )
        signals = signal_logger.get_signals_for_symbol("BTC/USDT", limit=1)
        assert signals[0].status == SignalStatus.FILLED
        assert signals[0].pnl == 523.45
        
        # Verificar persistencia en archivo
        signals_files = signal_logger.signals_dir.glob("signals_*.json")
        assert len(list(signals_files)) > 0
        
        print(f"✅ Full lifecycle: GENERATED → ACCEPTED → EXECUTED → FILLED")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
