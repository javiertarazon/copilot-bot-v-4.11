
#!/usr/bin/env python3
"""
Módulo de Resiliencia de Red - Exponential Backoff + Circuit Breaker

Proporciona mecanismos para manejar reconexiones con estrategias de backoff
exponencial y circuit breaker para evitar intentos innecesarios tras fallos repetidos.
"""

import time
import logging
import random
from typing import Callable, Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum


class CircuitBreakerState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "CLOSED"          # Funcionando normalmente
    OPEN = "OPEN"              # Falló, bloqueando nuevos intentos
    HALF_OPEN = "HALF_OPEN"    # Probando reconexión tras espera


class ExponentialBackoffConfig:
    """Configuración para exponential backoff"""
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        max_retries: int = 5
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.max_retries = max_retries


class CircuitBreakerConfig:
    """Configuración para circuit breaker"""
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold      # Fallos antes de abrir
        self.recovery_timeout = recovery_timeout        # Tiempo antes de HALF_OPEN
        self.success_threshold = success_threshold      # Éxitos en HALF_OPEN para cerrar


class ResilienceManager:
    """
    Gestor de resiliencia con exponential backoff y circuit breaker.
    
    Proporciona una interfaz unificada para reintentos con backoff exponencial
    y protección via circuit breaker contra fallos repetidos.
    """
    
    def __init__(
        self,
        name: str,
        backoff_config: Optional[ExponentialBackoffConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuraciones
        self.backoff_config = backoff_config or ExponentialBackoffConfig()
        self.circuit_config = circuit_breaker_config or CircuitBreakerConfig()
        
        # Estado del circuit breaker
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
        
        # Métricas
        self.total_attempts = 0
        self.total_failures = 0
        self.total_successes = 0
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calcula el delay exponencial para un intento.
        
        Args:
            attempt: Número de intento (0-indexed)
            
        Returns:
            float: Delay en segundos
        """
        delay = self.backoff_config.initial_delay * (
            self.backoff_config.exponential_base ** attempt
        )
        
        # Limitar al máximo
        delay = min(delay, self.backoff_config.max_delay)
        
        # Agregar jitter (±20%)
        if self.backoff_config.jitter:
            jitter_amount = delay * 0.2
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.1, delay)  # Asegurar que sea positivo
        
        return delay
    
    def _should_attempt_circuit_breaker(self) -> bool:
        """
        Determina si se debe permitir un intento basado en el estado del circuit breaker.
        
        Returns:
            bool: True si se debe permitir el intento
        """
        now = datetime.now()
        
        if self.circuit_state == CircuitBreakerState.CLOSED:
            # Funcionando normalmente
            return True
        
        elif self.circuit_state == CircuitBreakerState.OPEN:
            # Verificar si es tiempo de intentar recuperación
            if self.last_failure_time and (
                now - self.last_failure_time
            ).total_seconds() >= self.circuit_config.recovery_timeout:
                self.logger.warning(
                    f"[{self.name}] Circuit breaker pasando a HALF_OPEN "
                    f"(intento de recuperación tras {self.circuit_config.recovery_timeout}s)"
                )
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            else:
                # Aún en período de bloqueo
                remaining = self.circuit_config.recovery_timeout - (
                    now - self.last_failure_time
                ).total_seconds()
                self.logger.debug(
                    f"[{self.name}] Circuit breaker OPEN - "
                    f"reabierto en {remaining:.1f}s"
                )
                return False
        
        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Intentando recuperación
            return True
        
        return False
    
    def _update_circuit_breaker_on_failure(self):
        """Actualiza el estado del circuit breaker tras un fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.circuit_state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.circuit_config.failure_threshold:
                self.logger.error(
                    f"[{self.name}] Circuit breaker ABIERTO "
                    f"({self.failure_count} fallos consecutivos)"
                )
                self.circuit_state = CircuitBreakerState.OPEN
                self.last_state_change = datetime.now()
        
        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Fallo durante recuperación, volver a OPEN
            self.logger.warning(
                f"[{self.name}] Circuit breaker retornando a OPEN "
                f"(fallo durante HALF_OPEN)"
            )
            self.circuit_state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now()
    
    def _update_circuit_breaker_on_success(self):
        """Actualiza el estado del circuit breaker tras un éxito"""
        self.failure_count = 0
        self.success_count += 1
        
        if self.circuit_state == CircuitBreakerState.CLOSED:
            # Continuar normalmente
            pass
        
        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.circuit_config.success_threshold:
                self.logger.info(
                    f"[{self.name}] Circuit breaker CERRADO "
                    f"({self.success_count} éxitos en HALF_OPEN)"
                )
                self.circuit_state = CircuitBreakerState.CLOSED
                self.success_count = 0
                self.last_state_change = datetime.now()
    
    def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[Exception]]:
        """
        Ejecuta una función con reintentos usando exponential backoff.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            Tuple[success, result, error]:
                - success: True si se ejecutó sin errores
                - result: Resultado de la función (None si error)
                - error: Excepción si hubo error (None si éxito)
        """
        self.total_attempts += 1
        
        # Verificar circuit breaker primero
        if not self._should_attempt_circuit_breaker():
            error = Exception(f"Circuit breaker OPEN para {self.name}")
            self.logger.warning(f"[{self.name}] {error}")
            return False, None, error
        
        last_error = None
        
        for attempt in range(self.backoff_config.max_retries):
            try:
                self.logger.debug(
                    f"[{self.name}] Intento {attempt + 1}/{self.backoff_config.max_retries}"
                )
                
                result = func(*args, **kwargs)
                
                # Éxito
                self._update_circuit_breaker_on_success()
                self.total_successes += 1
                self.logger.debug(f"[{self.name}] Intento exitoso en intento {attempt + 1}")
                return True, result, None
            
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"[{self.name}] Intento {attempt + 1} falló: {type(e).__name__}: {e}"
                )
                
                # Actualizar circuit breaker
                self._update_circuit_breaker_on_failure()
                self.total_failures += 1
                
                # Si no es el último intento, esperar antes de reintentar
                if attempt < self.backoff_config.max_retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.info(
                        f"[{self.name}] Esperando {delay:.2f}s antes de reintento..."
                    )
                    time.sleep(delay)
                else:
                    # Último intento falló
                    self.logger.error(
                        f"[{self.name}] Todos los {self.backoff_config.max_retries} "
                        f"intentos fallaron"
                    )
        
        return False, None, last_error
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna el estado actual del gestor de resiliencia.
        
        Returns:
            Dict con información del estado
        """
        return {
            "name": self.name,
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_attempts": self.total_attempts,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "success_rate": (
                self.total_successes / self.total_attempts 
                if self.total_attempts > 0 
                else 0.0
            ),
            "last_state_change": self.last_state_change.isoformat(),
            "uptime_seconds": (
                datetime.now() - self.last_state_change
            ).total_seconds()
        }
    
    def reset(self):
        """Resetea el estado del circuit breaker y contadores"""
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
        self.logger.info(f"[{self.name}] Estado reseteado")


def create_resilient_connection_manager(
    name: str,
    initial_delay: float = 2.0,
    logger: Optional[logging.Logger] = None
) -> ResilienceManager:
    """
    Factory para crear un gestor de resiliencia optimizado para conexiones.
    
    Args:
        name: Nombre del conexión
        initial_delay: Delay inicial en segundos
        logger: Logger personalizado (opcional)
        
    Returns:
        ResilienceManager configurado para conexiones
    """
    backoff = ExponentialBackoffConfig(
        initial_delay=initial_delay,
        max_delay=120.0,  # Máx 2 minutos
        exponential_base=2.0,
        jitter=True,
        max_retries=6  # Hasta 2 + 4 + 8 + 16 + 32 + 64 = 126s
    )
    
    circuit = CircuitBreakerConfig(
        failure_threshold=3,      # 3 fallos abren el circuito
        recovery_timeout=30.0,    # Intenta recuperación cada 30s
        success_threshold=2       # 2 éxitos en HALF_OPEN para cerrar
    )
    
    return ResilienceManager(
        name=name,
        backoff_config=backoff,
        circuit_breaker_config=circuit,
        logger=logger
    )
