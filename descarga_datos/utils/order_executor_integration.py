#!/usr/bin/env python3
"""
Integración de Persistencia y Retry para Order Executor - FASE 3

Proporciona funcionalidades para:
1. Persistir órdenes antes de enviarlas
2. Recuperar órdenes no completadas tras desconexión
3. Implementar retry con backoff exponencial
4. Mantener historial de intentos

Author: GitHub Copilot
Date: Octubre 2025
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from utils.order_persistence import (
    OrderPersistenceManager,
    PersistedOrder,
    OrderStatus,
    get_order_persistence_manager
)
from utils.resilience import (
    ResilienceManager,
    ExponentialBackoffConfig,
    CircuitBreakerConfig,
    create_resilient_connection_manager
)


@dataclass
class OrderExecutionResult:
    """Resultado de ejecución de orden"""
    success: bool
    order_id: Optional[str] = None
    exchange_id: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 0
    final_status: Optional[str] = None


class OrderExecutorIntegration:
    """
    Integrador de persistencia y retry para order executor.
    
    Responsabilidades:
    - Persistir órdenes antes de enviar
    - Ejecutar con retry automático
    - Recuperar órdenes fallidas
    - Mantener métricas de ejecución
    """
    
    def __init__(
        self,
        exchange_name: str = "bybit",
        persistence_dir: Optional[str] = None,
        resilience_manager: Optional[ResilienceManager] = None,
        logger: Optional[logging.Logger] = None,
        initial_backoff_delay: float = 1.0
    ):
        """
        Inicializa integrador.
        
        Args:
            exchange_name: Nombre del exchange
            persistence_dir: Directorio personalizado para persistencia
            resilience_manager: Gestor de resiliencia personalizado
            logger: Logger personalizado
            initial_backoff_delay: Delay inicial para backoff exponencial
        """
        self.exchange_name = exchange_name
        self.persistence_manager = get_order_persistence_manager(
            exchange_name=exchange_name,
            persistence_dir=persistence_dir
        )
        
        # Usar resilience manager proporcionado o crear uno
        if resilience_manager is None:
            self.resilience_manager = create_resilient_connection_manager(
                name=f"OrderExecutor-{exchange_name}",
                initial_delay=initial_backoff_delay
            )
        else:
            self.resilience_manager = resilience_manager
        
        self.logger = logger or logging.getLogger(__name__)
        
        # Estadísticas
        self._execution_stats = {
            'total_orders': 0,
            'successful': 0,
            'failed': 0,
            'recovered': 0,
            'total_retries': 0
        }
        
        # Lock para thread-safety
        self._lock = threading.RLock()
        
        self.logger.info(
            f"OrderExecutorIntegration inicializado para {exchange_name}"
        )
    
    def execute_order_with_persistence(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        execute_func: Optional[Callable] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        max_retries: int = 5
    ) -> OrderExecutionResult:
        """
        Ejecuta orden con persistencia y retry automático.
        
        Args:
            symbol: Par (BTC/USDT)
            side: 'buy' o 'sell'
            order_type: 'market', 'limit', etc.
            amount: Cantidad
            price: Precio (para limit)
            execute_func: Función que ejecuta la orden en el exchange
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            max_retries: Máximo de reintentos
            
        Returns:
            OrderExecutionResult con resultado de ejecución
        """
        # Generar ID de orden
        order_id = self.persistence_manager._generate_order_id()
        
        # 1. Crear y persistir orden pendiente
        persisted_order = PersistedOrder(
            order_id=order_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            status=OrderStatus.PENDING.value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_retries=max_retries
        )
        
        if not self.persistence_manager.save_order(persisted_order):
            self.logger.error(f"Error persistiendo orden {order_id}")
            return OrderExecutionResult(
                success=False,
                order_id=order_id,
                error_message="Error guardando orden en persistencia"
            )
        
        self.logger.info(f"Orden persistida: {order_id} ({symbol} {side})")
        
        # 2. Actualizar estado a RECOVERY si estamos recuperando
        self.persistence_manager.update_order_status(
            order_id,
            OrderStatus.RECOVERY.value
        )
        
        # 3. Ejecutar con retry usando resilience manager
        result = self._execute_with_retry(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            execute_func=execute_func,
            max_retries=max_retries
        )
        
        # 4. Actualizar persistencia con resultado
        if result.success:
            self.persistence_manager.update_order_status(
                order_id,
                OrderStatus.SENT.value,
                exchange_id=result.exchange_id
            )
            self._execution_stats['successful'] += 1
        else:
            self.persistence_manager.update_order_status(
                order_id,
                OrderStatus.FAILED.value,
                error_message=result.error_message
            )
            self._execution_stats['failed'] += 1
        
        self._execution_stats['total_orders'] += 1
        
        return result
    
    def _execute_with_retry(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float],
        execute_func: Optional[Callable],
        max_retries: int
    ) -> OrderExecutionResult:
        """
        Ejecuta orden con reintentos automáticos.
        
        Args:
            order_id: ID local de la orden
            symbol: Par
            side: Lado de la operación
            order_type: Tipo de orden
            amount: Cantidad
            price: Precio
            execute_func: Función que ejecuta
            max_retries: Máximo de reintentos
            
        Returns:
            OrderExecutionResult con intentos contados correctamente
        """
        if execute_func is None:
            return OrderExecutionResult(
                success=False,
                order_id=order_id,
                error_message="execute_func no proporcionado",
                attempts=0
            )
        
        last_error = None
        attempts = 0
        exchange_id = None
        
        # Usar resilience manager para cada intento (manejo manual del loop)
        for attempt in range(max_retries):
            attempts += 1
            try:
                self.logger.debug(f"Intento {attempts}/{max_retries} para orden {order_id}")
                
                # Ejecutar función
                result = execute_func(symbol=symbol, side=side, order_type=order_type,
                                    amount=amount, price=price)
                
                if result:
                    exchange_id = result.get('id') or result.get('order_id')
                    self.logger.info(
                        f"Orden ejecutada: {order_id} -> {exchange_id} "
                        f"(intentos: {attempts})"
                    )
                    self._execution_stats['total_retries'] += max(0, attempts - 1)
                    
                    return OrderExecutionResult(
                        success=True,
                        order_id=order_id,
                        exchange_id=exchange_id,
                        attempts=attempts,
                        final_status=OrderStatus.SENT.value
                    )
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Intento {attempts} falló: {last_error}")
                
                # Incrementar contador en persistencia
                if attempts < max_retries:
                    retry_ok = self.persistence_manager.increment_retry_count(order_id)
                    if not retry_ok:
                        self.logger.warning(f"Orden {order_id} alcanzó max_retries")
                        break
                    
                    # Esperar antes de reintentar
                    wait_time = min(2 ** (attempts - 1), 30)
                    self.logger.debug(f"Esperando {wait_time}s antes de reintento...")
                    time.sleep(wait_time)
        
        self._execution_stats['total_retries'] += max(0, attempts - 1)
        
        return OrderExecutionResult(
            success=False,
            order_id=order_id,
            error_message=f"Falló después de {attempts} intentos: {last_error}",
            attempts=attempts,
            final_status=OrderStatus.FAILED.value
        )
    
    def recover_pending_orders(
        self,
        check_status_func: Optional[Callable] = None
    ) -> Dict[str, OrderExecutionResult]:
        """
        Recupera órdenes pendientes tras desconexión.
        
        Args:
            check_status_func: Función para verificar estado en exchange
            
        Returns:
            Diccionario con resultados de recuperación
        """
        self.logger.info("Iniciando recuperación de órdenes pendientes...")
        
        # Cargar órdenes pendientes
        pending_orders = self.persistence_manager.load_pending_orders()
        
        if not pending_orders:
            self.logger.info("No hay órdenes pendientes para recuperar")
            return {}
        
        self.logger.info(f"Recuperando {len(pending_orders)} órdenes pendientes")
        
        recovery_results = {}
        
        for order in pending_orders:
            try:
                # Si tenemos exchange_id, verificar estado
                if order.exchange_id and check_status_func:
                    try:
                        status = check_status_func(order.exchange_id, order.symbol)
                        
                        if status in ['filled', 'closed', 'completed']:
                            self.logger.info(
                                f"Orden {order.order_id} ya fue ejecutada en exchange"
                            )
                            self.persistence_manager.mark_completed(order.order_id)
                            recovery_results[order.order_id] = OrderExecutionResult(
                                success=True,
                                order_id=order.order_id,
                                exchange_id=order.exchange_id,
                                final_status=OrderStatus.FILLED.value
                            )
                            self._execution_stats['recovered'] += 1
                            continue
                        
                    except Exception as e:
                        self.logger.debug(f"Error verificando estado: {e}")
                
                # Si no fue ejecutada o no tenemos exchange_id, remarcar para retry
                self.persistence_manager.update_order_status(
                    order.order_id,
                    OrderStatus.RECOVERY.value
                )
                
                recovery_results[order.order_id] = OrderExecutionResult(
                    success=False,
                    order_id=order.order_id,
                    error_message="Orden en estado de recuperación",
                    final_status=OrderStatus.RECOVERY.value
                )
                
            except Exception as e:
                self.logger.error(
                    f"Error recuperando orden {order.order_id}: {e}"
                )
                recovery_results[order.order_id] = OrderExecutionResult(
                    success=False,
                    order_id=order.order_id,
                    error_message=str(e)
                )
        
        self.logger.info(
            f"Recuperación completada: "
            f"{self._execution_stats['recovered']} órdenes ya ejecutadas"
        )
        
        return recovery_results
    
    def cleanup_old_orders(self) -> int:
        """
        Limpia órdenes completadas/fallidas antiguas.
        
        Returns:
            Número de órdenes eliminadas
        """
        cleaned = self.persistence_manager.cleanup_old_orders()
        self.logger.debug(f"Limpiadas {cleaned} órdenes antiguas")
        return cleaned
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de ejecución.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._lock:
            persistence_stats = self.persistence_manager.get_stats()
            
            return {
                'execution': self._execution_stats.copy(),
                'persistence': persistence_stats,
                'resilience': self.resilience_manager.get_status(),
                'timestamp': datetime.now().isoformat()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del sistema de ejecución.
        
        Returns:
            Diccionario con estado de salud
        """
        persistence_health = self.persistence_manager.health_check()
        
        return {
            'healthy': persistence_health['healthy'],
            'persistence': persistence_health,
            'resilience_status': self.resilience_manager.get_status(),
            'execution_stats': self._execution_stats.copy()
        }


def get_order_executor_integration(
    exchange_name: str = "bybit",
    persistence_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> OrderExecutorIntegration:
    """
    Factory para obtener integrador de order executor.
    
    Args:
        exchange_name: Nombre del exchange
        persistence_dir: Directorio personalizado
        logger: Logger personalizado
        
    Returns:
        OrderExecutorIntegration singleton por exchange
    """
    # Usar cache simple (puede mejorarse con singleton pattern)
    if not hasattr(get_order_executor_integration, '_integrators'):
        get_order_executor_integration._integrators = {}
    
    key = exchange_name
    
    if key not in get_order_executor_integration._integrators:
        get_order_executor_integration._integrators[key] = OrderExecutorIntegration(
            exchange_name=exchange_name,
            persistence_dir=persistence_dir,
            logger=logger
        )
    
    return get_order_executor_integration._integrators[key]
