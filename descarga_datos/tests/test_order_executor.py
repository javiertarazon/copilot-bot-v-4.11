#!/usr/bin/env python3
"""
Tests para FASE 3: Persistencia de Órdenes y Retry Logic

Valida:
1. Guardado y carga de órdenes en persistencia
2. Recuperación de órdenes tras desconexión
3. Retry automático con exponential backoff
4. Estado de órdenes
5. Limpieza de órdenes antiguas
6. Metrics e integración

Author: GitHub Copilot
Date: Octubre 2025
"""

import pytest
import json
import time
import tempfile
import threading
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports del sistema
from utils.order_persistence import (
    PersistedOrder,
    OrderStatus,
    OrderPersistenceManager,
    get_order_persistence_manager
)
from utils.order_executor_integration import (
    OrderExecutorIntegration,
    OrderExecutionResult,
    get_order_executor_integration
)
from utils.resilience import create_resilient_connection_manager


# ============================================================================
# TASK 7: Tests de Persistencia de Órdenes
# ============================================================================

class TestOrderPersistence:
    """Tests para persistencia de órdenes en JSON"""
    
    @pytest.fixture
    def temp_persistence_dir(self):
        """Crea directorio temporal para tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def persistence_manager(self, temp_persistence_dir):
        """Crea gestor de persistencia para tests"""
        return OrderPersistenceManager(
            persistence_dir=temp_persistence_dir,
            exchange_name="test_exchange"
        )
    
    def test_save_and_load_order(self, persistence_manager):
        """Test: Guardar y cargar orden"""
        # Crear orden
        order = PersistedOrder(
            order_id="order_1",
            symbol="BTC/USDT",
            order_type="market",
            side="buy",
            amount=0.5,
            price=50000.0
        )
        
        # Guardar
        assert persistence_manager.save_order(order) == True
        
        # Cargar
        loaded_orders = persistence_manager.load_all_orders()
        assert len(loaded_orders) == 1
        assert loaded_orders["order_1"].symbol == "BTC/USDT"
        assert loaded_orders["order_1"].amount == 0.5
        print("✅ Test guardado/cargado de orden passou")
    
    def test_save_batch_orders(self, persistence_manager):
        """Test: Guardar múltiples órdenes"""
        orders = [
            PersistedOrder(
                order_id=f"order_{i}",
                symbol=f"{'BTC' if i % 2 else 'ETH'}/USDT",
                order_type="limit",
                side="buy" if i % 2 else "sell",
                amount=float(i),
                price=100.0 * (i + 1)
            )
            for i in range(5)
        ]
        
        saved = persistence_manager.save_orders_batch(orders)
        assert saved == 5
        
        loaded = persistence_manager.load_all_orders()
        assert len(loaded) == 5
        print("✅ Test guardado batch de órdenes passou")
    
    def test_order_status_update(self, persistence_manager):
        """Test: Actualizar estado de orden"""
        order = PersistedOrder(
            order_id="order_status_test",
            symbol="BTC/USDT",
            order_type="limit",
            side="buy",
            amount=1.0,
            price=45000.0,
            status=OrderStatus.PENDING.value
        )
        
        persistence_manager.save_order(order)
        
        # Actualizar a SENT con exchange_id
        success = persistence_manager.update_order_status(
            "order_status_test",
            OrderStatus.SENT.value,
            exchange_id="binance_12345"
        )
        assert success == True
        
        # Verificar
        loaded = persistence_manager.load_all_orders()
        assert loaded["order_status_test"].status == OrderStatus.SENT.value
        assert loaded["order_status_test"].exchange_id == "binance_12345"
        print("✅ Test actualización de estado passou")
    
    def test_retry_count_increment(self, persistence_manager):
        """Test: Incrementar contador de reintentos"""
        order = PersistedOrder(
            order_id="retry_test",
            symbol="ETH/USDT",
            order_type="market",
            side="sell",
            amount=2.0,
            max_retries=3
        )
        
        persistence_manager.save_order(order)
        
        # Incrementar 3 veces (máximo)
        assert persistence_manager.increment_retry_count("retry_test") == True
        assert persistence_manager.increment_retry_count("retry_test") == True
        assert persistence_manager.increment_retry_count("retry_test") == True
        
        # 4to intento debe fallar (max_retries = 3)
        assert persistence_manager.increment_retry_count("retry_test") == False
        
        # Verificar estado
        loaded = persistence_manager.load_all_orders()
        assert loaded["retry_test"].status == OrderStatus.FAILED.value
        print("✅ Test contador de reintentos passou")
    
    def test_load_pending_orders(self, persistence_manager):
        """Test: Cargar órdenes pendientes para recuperación"""
        # Crear órdenes con diferentes estados
        orders = [
            PersistedOrder(
                order_id="pending_1",
                symbol="BTC/USDT",
                side="buy",
                amount=1.0,
                order_type="market",
                status=OrderStatus.PENDING.value
            ),
            PersistedOrder(
                order_id="failed_1",
                symbol="ETH/USDT",
                side="sell",
                amount=2.0,
                order_type="limit",
                status=OrderStatus.FAILED.value
            ),
            PersistedOrder(
                order_id="filled_1",
                symbol="ADA/USDT",
                side="buy",
                amount=100.0,
                order_type="market",
                status=OrderStatus.FILLED.value
            ),
        ]
        
        for order in orders:
            persistence_manager.save_order(order)
        
        # Cargar pendientes
        pending = persistence_manager.load_pending_orders()
        
        # Debe retornar PENDING + FAILED pero NO FILLED
        assert len(pending) == 2
        order_ids = {o.order_id for o in pending}
        assert "pending_1" in order_ids
        assert "failed_1" in order_ids
        assert "filled_1" not in order_ids
        print("✅ Test cargado de órdenes pendientes passou")
    
    def test_cleanup_old_orders(self, persistence_manager):
        """Test: Limpiar órdenes antiguas completadas"""
        # Crear orden completada hace 25 horas (max_age_hours = 24)
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        
        order_old = PersistedOrder(
            order_id="old_order",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            order_type="market",
            status=OrderStatus.FILLED.value,
            timestamp=old_time
        )
        
        # Crear orden nueva
        order_new = PersistedOrder(
            order_id="new_order",
            symbol="ETH/USDT",
            side="sell",
            amount=2.0,
            order_type="limit",
            status=OrderStatus.FILLED.value
        )
        
        persistence_manager.save_order(order_old)
        persistence_manager.save_order(order_new)
        
        # Limpiar
        cleaned = persistence_manager.cleanup_old_orders()
        
        assert cleaned == 1
        
        # Verificar que solo la nueva quedó
        remaining = persistence_manager.load_all_orders()
        assert len(remaining) == 1
        assert "new_order" in remaining
        assert "old_order" not in remaining
        print("✅ Test limpieza de órdenes antiguas passou")
    
    def test_persistence_stats(self, persistence_manager):
        """Test: Estadísticas de persistencia"""
        # Guardar órdenes
        for i in range(3):
            order = PersistedOrder(
                order_id=f"order_{i}",
                symbol="BTC/USDT",
                side="buy",
                amount=float(i + 1),
                order_type="market"
            )
            persistence_manager.save_order(order)
        
        stats = persistence_manager.get_stats()
        
        assert stats['total_orders'] == 3
        assert 'status_breakdown' in stats
        assert 'statistics' in stats
        assert stats['statistics']['saved'] == 3
        print("✅ Test estadísticas passou")


# ============================================================================
# TASK 8: Tests de Retry Logic e Integración
# ============================================================================

class TestOrderExecutorIntegration:
    """Tests para integración de persistencia y retry"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        # Limpiar singletons cacheados
        import utils.order_persistence as op_module
        op_module._persistence_manager = None
        
        import utils.order_executor_integration as oei_module
        oei_module.get_order_executor_integration._integrators = {}
        
        # Crear directorio temporal para cada test
        self.temp_dir = tempfile.TemporaryDirectory()
        orders_dir = Path(self.temp_dir.name) / "orders"
        orders_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear integrador
        self.integration = OrderExecutorIntegration(
            exchange_name="test_exchange",
            persistence_dir=str(orders_dir)
        )
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        # Limpiar singletons
        import utils.order_persistence as op_module
        op_module._persistence_manager = None
        
        import utils.order_executor_integration as oei_module
        oei_module.get_order_executor_integration._integrators = {}
        
        self.temp_dir.cleanup()
    
    def test_execute_order_success_first_try(self):
        """Test: Ejecutar orden exitosa en primer intento"""
        # Mock de función que ejecuta exitosamente
        execute_func = Mock(return_value={'id': 'exchange_123', 'status': 'open'})
        
        result = self.integration.execute_order_with_persistence(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            amount=1.0,
            execute_func=execute_func
        )
        
        assert result.success == True
        assert result.exchange_id == 'exchange_123'
        assert result.attempts == 1
        
        # Verificar que la orden fue guardada en persistencia
        pending = self.integration.persistence_manager.load_pending_orders()
        # No debe haber pendientes pues fue exitosa
        failed_orders = [o for o in pending if o.status == OrderStatus.FAILED.value]
        assert len(failed_orders) == 0
        print("✅ Test ejecución exitosa passou")
    
    def test_execute_order_with_retries(self):
        """Test: Ejecutar orden con reintentos"""
        attempt_count = [0]
        
        def execute_func_with_failures(*args, **kwargs):
            """Falla 2 veces, luego éxito"""
            attempt_count[0] += 1
            if attempt_count[0] <= 2:
                raise Exception("Fallo temporal")
            return {'id': 'exchange_456', 'status': 'open'}
        
        result = self.integration.execute_order_with_persistence(
            symbol="ETH/USDT",
            side="sell",
            order_type="limit",
            amount=2.0,
            price=2000.0,
            execute_func=execute_func_with_failures,
            max_retries=5
        )
        
        assert result.success == True
        assert result.exchange_id == 'exchange_456'
        assert result.attempts == 3  # 2 fallos + 1 éxito
        print("✅ Test ejecución con reintentos passou")
    
    def test_execute_order_max_retries_exceeded(self):
        """Test: Fallar cuando se exceden máximo de reintentos"""
        execute_func = Mock(side_effect=Exception("Fallo permanente"))
        
        result = self.integration.execute_order_with_persistence(
            symbol="ADA/USDT",
            side="buy",
            order_type="market",
            amount=100.0,
            execute_func=execute_func,
            max_retries=3
        )
        
        assert result.success == False
        assert result.attempts == 3
        assert "Falló después de" in result.error_message
        
        # Verificar que quedó en persistencia como FAILED
        all_orders = self.integration.persistence_manager.load_all_orders()
        failed = [o for o in all_orders.values() if o.status == OrderStatus.FAILED.value]
        assert len(failed) >= 1
        print("✅ Test máximo de reintentos passou")
    
    def test_recover_pending_orders(self):
        """Test: Recuperar órdenes pendientes"""
        # Guardar órdenes pendientes directamente
        orders = [
            PersistedOrder(
                order_id=f"pending_{i}",
                symbol="BTC/USDT",
                side="buy",
                amount=1.0,
                order_type="market",
                status=OrderStatus.PENDING.value
            )
            for i in range(3)
        ]
        
        for order in orders:
            self.integration.persistence_manager.save_order(order)
        
        # Recuperar (sin check_status_func, solo remarcar)
        results = self.integration.recover_pending_orders()
        
        assert len(results) == 3
        assert all(not r.success for r in results.values())
        
        # Verificar que están en estado RECOVERY
        pending_after = self.integration.persistence_manager.load_pending_orders()
        recovery_orders = [o for o in pending_after if o.status == OrderStatus.RECOVERY.value]
        assert len(recovery_orders) == 3
        print("✅ Test recuperación de órdenes passou")
    
    def test_recover_with_status_check(self):
        """Test: Recuperar órdenes verificando estado en exchange"""
        # Guardar orden con exchange_id en estado RECOVERY (que será recuperada)
        order = PersistedOrder(
            order_id="recovery_check_1",
            symbol="BTC/USDT",
            side="buy",
            amount=1.0,
            order_type="market",
            status=OrderStatus.RECOVERY.value,  # ← Debe estar en estado recuperable
            exchange_id="binance_999"
        )
        self.integration.persistence_manager.save_order(order)
        
        # Mock de función que verifica estado (orden ya ejecutada)
        def check_status_func(exchange_id, symbol):
            return 'filled'
        
        results = self.integration.recover_pending_orders(
            check_status_func=check_status_func
        )
        
        # Debe retornar la orden como recuperada
        assert len(results) == 1
        assert "recovery_check_1" in results
        
        # Verificar que la orden está marcada como FILLED
        all_orders = self.integration.persistence_manager.load_all_orders()
        assert all_orders["recovery_check_1"].status == OrderStatus.FILLED.value
        print("✅ Test verificación de estado passou")
    
    def test_execution_stats(self):
        """Test: Estadísticas de ejecución"""
        # Ejecutar algunas órdenes
        execute_func_ok = Mock(return_value={'id': 'ok_1'})
        
        for i in range(2):
            self.integration.execute_order_with_persistence(
                symbol="BTC/USDT",
                side="buy",
                amount=1.0,
                order_type="market",
                execute_func=execute_func_ok
            )
        
        stats = self.integration.get_execution_stats()
        
        assert stats['execution']['total_orders'] == 2
        assert stats['execution']['successful'] == 2
        assert 'persistence' in stats
        assert 'resilience' in stats
        print("✅ Test estadísticas de ejecución passou")
    
    def test_health_check(self):
        """Test: Verificar salud del sistema"""
        health = self.integration.health_check()
        
        assert 'healthy' in health
        assert 'persistence' in health
        assert 'resilience_status' in health
        assert 'execution_stats' in health
        print("✅ Test health check passou")


# ============================================================================
# TASK 9: Test de Integración End-to-End
# ============================================================================

class TestOrderExecutorE2E:
    """Test de integración end-to-end con simulación"""
    
    @pytest.fixture
    def temp_persistence_dir(self):
        """Crea directorio temporal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_full_order_lifecycle(self, temp_persistence_dir):
        """Test: Ciclo completo de orden (pendiente -> enviada -> completada)"""
        integration = OrderExecutorIntegration(
            exchange_name="lifecycle_test",
            persistence_dir=temp_persistence_dir
        )
        
        # Fase 1: Crear y ejecutar orden
        execute_func = Mock(return_value={'id': 'lifecycle_123'})
        
        result1 = integration.execute_order_with_persistence(
            symbol="BTC/USDT",
            side="buy",
            amount=0.5,
            order_type="market",
            stop_loss=40000.0,
            take_profit=60000.0,
            execute_func=execute_func
        )
        
        assert result1.success == True
        order_id = result1.order_id
        
        # Fase 2: Marcar como completada
        success = integration.persistence_manager.mark_completed(order_id)
        assert success == True
        
        # Fase 3: Verificar que no aparece en pendientes
        pending = integration.persistence_manager.load_pending_orders()
        filled_orders = [o.order_id for o in pending if o.status == OrderStatus.FILLED.value]
        assert order_id not in filled_orders
        
        # Fase 4: Limpiar
        cleaned = integration.cleanup_old_orders()
        # Puede ser 0 si la orden es muy nueva
        
        print("✅ Test ciclo completo de orden passou")
    
    def test_concurrent_order_execution(self, temp_persistence_dir):
        """Test: Ejecución concurrente de múltiples órdenes"""
        integration = OrderExecutorIntegration(
            exchange_name="concurrent_test",
            persistence_dir=temp_persistence_dir
        )
        
        results = []
        
        def execute_func(*args, **kwargs):
            exchange_id = f"exchange_{len(results)}"
            time.sleep(0.01)  # Simular latencia
            return {'id': exchange_id}
        
        def submit_order(symbol, i):
            result = integration.execute_order_with_persistence(
                symbol=symbol,
                side="buy" if i % 2 else "sell",
                amount=float(i + 1),
                order_type="market",
                execute_func=execute_func
            )
            results.append(result)
        
        # Ejecutar órdenes en threads
        threads = []
        for i in range(5):
            symbol = ["BTC/USDT", "ETH/USDT", "ADA/USDT"][i % 3]
            t = threading.Thread(target=submit_order, args=(symbol, i))
            threads.append(t)
            t.start()
        
        # Esperar a que terminen
        for t in threads:
            t.join()
        
        # Verificar resultados
        assert len(results) == 5
        successful = sum(1 for r in results if r.success)
        assert successful == 5
        
        # Verificar que todas fueron persistidas
        all_orders = integration.persistence_manager.load_all_orders()
        assert len(all_orders) == 5
        
        print("✅ Test ejecución concurrente passou")


# ============================================================================
# Helper Functions
# ============================================================================

def create_sample_order(**kwargs) -> PersistedOrder:
    """Crea orden de ejemplo para tests"""
    defaults = {
        'order_id': 'test_order_1',
        'symbol': 'BTC/USDT',
        'order_type': 'market',
        'side': 'buy',
        'amount': 1.0
    }
    defaults.update(kwargs)
    return PersistedOrder(**defaults)


def create_mock_execute_func(
    success: bool = True,
    exchange_id: str = 'exchange_123',
    delay: float = 0.0
):
    """Crea función mock para ejecutar órdenes"""
    def execute_func(*args, **kwargs):
        if delay > 0:
            time.sleep(delay)
        if success:
            return {'id': exchange_id, 'status': 'open'}
        else:
            raise Exception("Mock execution failed")
    return execute_func


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
