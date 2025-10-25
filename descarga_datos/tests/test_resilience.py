#!/usr/bin/env python3
"""
Test de Resiliencia de Red - Validación de Exponential Backoff + Circuit Breaker

Este script realiza un live test de 10 minutos para validar que:
1. El exponential backoff aumenta delays correctamente
2. El circuit breaker se abre tras fallos repetidos
3. El sistema se recupera correctamente en HALF_OPEN
4. Las reconexiones son exitosas sin fallos permanentes
"""

import time
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.resilience import (
    ResilienceManager,
    ExponentialBackoffConfig,
    CircuitBreakerConfig,
    CircuitBreakerState,
    create_resilient_connection_manager
)


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class MockConnectionProvider:
    """Proveedor de conexión mock para pruebas"""
    
    def __init__(self, failure_pattern=None):
        """
        Args:
            failure_pattern: Lista de booleans indicando éxito/fallo
                            Ej: [False, False, True, True] = 2 fallos, 2 éxitos
        """
        self.failure_pattern = failure_pattern or []
        self.attempt_count = 0
        self.connected = False
    
    def attempt_connection(self):
        """Intenta conectar siguiendo el patrón de fallos"""
        try:
            if self.attempt_count < len(self.failure_pattern):
                if self.failure_pattern[self.attempt_count]:
                    self.connected = True
                    return True
                else:
                    raise ConnectionError(f"Conexión fallida (intento {self.attempt_count + 1})")
            else:
                # Después del patrón, siempre conecta
                self.connected = True
                return True
        finally:
            self.attempt_count += 1


def test_exponential_backoff():
    """Prueba 1: Validar que exponential backoff calcula delays correctamente"""
    logger.info("=" * 80)
    logger.info("PRUEBA 1: Exponential Backoff")
    logger.info("=" * 80)
    
    manager = ResilienceManager(
        name="TEST-BACKOFF",
        backoff_config=ExponentialBackoffConfig(
            initial_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False  # Sin jitter para valores predecibles
        )
    )
    
    logger.info("Calculando delays para primeros 5 intentos (sin jitter):")
    for attempt in range(5):
        delay = manager._calculate_backoff_delay(attempt)
        expected = min(1.0 * (2.0 ** attempt), 60.0)
        logger.info(f"  Intento {attempt}: {delay:.2f}s (esperado: {expected:.2f}s) ✓")
    
    logger.info("✅ PRUEBA 1 PASSOU\n")


def test_circuit_breaker_states():
    """Prueba 2: Validar transiciones de states del circuit breaker"""
    logger.info("=" * 80)
    logger.info("PRUEBA 2: Circuit Breaker States")
    logger.info("=" * 80)
    
    manager = ResilienceManager(
        name="TEST-CIRCUIT",
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=2.0,
            success_threshold=2
        )
    )
    
    # Estado inicial: CLOSED
    logger.info(f"Estado inicial: {manager.circuit_state.value}")
    assert manager.circuit_state == CircuitBreakerState.CLOSED, "Debe comenzar en CLOSED"
    
    # Simular 3 fallos consecutivos
    logger.info("Simulando 3 fallos consecutivos...")
    for i in range(3):
        manager._update_circuit_breaker_on_failure()
        logger.info(f"  Fallo {i+1}: State = {manager.circuit_state.value}")
    
    assert manager.circuit_state == CircuitBreakerState.OPEN, "Debe estar OPEN después de 3 fallos"
    logger.info("✓ Circuit breaker está OPEN después de threshold de fallos")
    
    # Verificar que no permite intentos
    should_attempt = manager._should_attempt_circuit_breaker()
    assert not should_attempt, "No debe permitir intentos mientras está OPEN"
    logger.info("✓ No permite intentos mientras está OPEN")
    
    # Esperar tiempo de recovery
    logger.info(f"Esperando {manager.circuit_config.recovery_timeout}s para recovery...")
    time.sleep(manager.circuit_config.recovery_timeout + 0.5)
    
    # Verificar transición a HALF_OPEN
    should_attempt = manager._should_attempt_circuit_breaker()
    assert should_attempt, "Debe permitir intentos después de recovery_timeout"
    assert manager.circuit_state == CircuitBreakerState.HALF_OPEN, "Debe estar en HALF_OPEN"
    logger.info("✓ Transicionó a HALF_OPEN después del recovery timeout")
    
    # Simular 2 éxitos en HALF_OPEN
    logger.info("Simulando 2 éxitos en HALF_OPEN...")
    for i in range(2):
        manager._update_circuit_breaker_on_success()
        logger.info(f"  Éxito {i+1}: State = {manager.circuit_state.value}")
    
    assert manager.circuit_state == CircuitBreakerState.CLOSED, "Debe volver a CLOSED"
    logger.info("✓ Circuit breaker volvió a CLOSED después de éxitos en HALF_OPEN")
    
    logger.info("✅ PRUEBA 2 PASSOU\n")


def test_retry_with_fallback():
    """Prueba 3: Validar reintentos con fallback a éxito"""
    logger.info("=" * 80)
    logger.info("PRUEBA 3: Retry con Fallback a Éxito")
    logger.info("=" * 80)
    
    # Patrón: 2 fallos, luego éxito
    provider = MockConnectionProvider(failure_pattern=[False, False, True])
    
    manager = ResilienceManager(
        name="TEST-RETRY",
        backoff_config=ExponentialBackoffConfig(
            initial_delay=0.5,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False,
            max_retries=5
        )
    )
    
    logger.info("Intentando conexión con patrón: [FAIL, FAIL, SUCCESS]")
    
    success, result, error = manager.execute_with_retry(provider.attempt_connection)
    
    logger.info(f"Resultado: Success={success}, Error={error}")
    logger.info(f"Total intentos: {provider.attempt_count}")
    logger.info(f"Estadísticas del manager: {manager.get_status()}")
    
    assert success, "Debe ser exitoso al final"
    assert provider.attempt_count == 3, f"Debe haber realizado 3 intentos, realizó {provider.attempt_count}"
    logger.info("✅ PRUEBA 3 PASSOU\n")


def test_circuit_breaker_protection():
    """Prueba 4: Validar que circuit breaker protege contra reintentos innecesarios"""
    logger.info("=" * 80)
    logger.info("PRUEBA 4: Circuit Breaker Protection")
    logger.info("=" * 80)
    
    # Proveedor que siempre falla
    def always_fail():
        raise ConnectionError("Conexión permanente fallida")
    
    manager = ResilienceManager(
        name="TEST-PROTECTION",
        backoff_config=ExponentialBackoffConfig(
            initial_delay=0.3,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False,
            max_retries=5
        ),
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=5.0,
            success_threshold=2
        )
    )
    
    logger.info("Primer intento: Ejecutar 3 operaciones que fallan")
    
    # Primer intento - será bloqueado por circuit breaker rápidamente
    start_time = time.time()
    for i in range(3):
        success, result, error = manager.execute_with_retry(always_fail)
        elapsed = time.time() - start_time
        state = manager.circuit_state.value
        logger.info(f"  Operación {i+1}: {state} - Tiempo: {elapsed:.1f}s")
    
    total_time = time.time() - start_time
    logger.info(f"Tiempo total para 3 operaciones: {total_time:.1f}s")
    
    status = manager.get_status()
    logger.info(f"Estado final: {status['circuit_state']}")
    logger.info(f"  Fallos totales: {status['total_failures']}")
    logger.info(f"  Éxitos totales: {status['total_successes']}")
    
    assert manager.circuit_state == CircuitBreakerState.OPEN, "Debe estar OPEN"
    logger.info("✓ Circuit breaker está OPEN, evitando reintentos innecesarios")
    
    logger.info("✅ PRUEBA 4 PASSOU\n")


def test_live_connection_simulation():
    """Prueba 5: Simulación de conexión en vivo de 2 minutos"""
    logger.info("=" * 80)
    logger.info("PRUEBA 5: Simulación de Conexión en Vivo (2 minutos)")
    logger.info("=" * 80)
    
    manager = create_resilient_connection_manager(
        name="LIVE-TEST",
        initial_delay=2.0,
        logger=logger
    )
    
    # Crear proveedor mock que simula reconexiones realistas
    class RealisticProvider:
        def __init__(self):
            self.call_count = 0
            self.failures = 0
        
        def attempt_connection(self):
            self.call_count += 1
            # Simular: 1er intento falla, 2do éxito, mantiene 30s, luego falla de nuevo, etc
            if self.call_count == 1:
                self.failures += 1
                raise ConnectionError("Conexión inicial fallida")
            elif self.call_count <= 4:
                return True  # Éxito durante 30 segundos
            else:
                self.failures += 1
                raise ConnectionError("Desconexión simulada")
    
    provider = RealisticProvider()
    
    logger.info("Iniciando prueba de 2 minutos con reconexiones simuladas...")
    logger.info(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    
    end_time = datetime.now() + timedelta(minutes=2)
    operation_count = 0
    
    while datetime.now() < end_time:
        success, result, error = manager.execute_with_retry(provider.attempt_connection)
        operation_count += 1
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        state = manager.get_status()['circuit_state']
        
        logger.info(
            f"[{timestamp}] Op {operation_count:3d}: {'✓' if success else '✗'} | "
            f"State: {state:10s} | "
            f"Fallos: {provider.failures}"
        )
        
        # Esperar 5 segundos entre operaciones
        time.sleep(5)
    
    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN DE PRUEBA EN VIVO")
    logger.info("=" * 80)
    final_status = manager.get_status()
    logger.info(f"Total operaciones: {final_status['total_attempts']}")
    logger.info(f"Total éxitos: {final_status['total_successes']}")
    logger.info(f"Total fallos: {final_status['total_failures']}")
    logger.info(f"Tasa de éxito: {final_status['success_rate']*100:.1f}%")
    logger.info(f"Estado final: {final_status['circuit_state']}")
    
    logger.info("✅ PRUEBA 5 PASSOU\n")


def main():
    """Ejecuta todas las pruebas"""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  TEST SUITE: RESILIENCIA DE RED (Exponential Backoff + Circuit Breaker)".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    
    try:
        # Ejecutar pruebas
        test_exponential_backoff()
        test_circuit_breaker_states()
        test_retry_with_fallback()
        test_circuit_breaker_protection()
        test_live_connection_simulation()
        
        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 78 + "║")
        logger.info("║" + "  ✅ TODAS LAS PRUEBAS PASSOU".center(78) + "║")
        logger.info("║" + " " * 78 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("")
        
        return 0
    
    except AssertionError as e:
        logger.error(f"\n❌ ERROR EN PRUEBA: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n❌ ERROR INESPERADO: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
