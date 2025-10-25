#!/usr/bin/env python3
"""
Sistema de Persistencia de Órdenes - FASE 3

Proporciona persistencia de órdenes en flight en archivos JSON para recuperación
ante desconexiones. Permite guardar estado de órdenes, recuperarlas ante crashes,
y marcar como procesadas.

Author: GitHub Copilot
Date: Octubre 2025
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import uuid


class OrderStatus(Enum):
    """Estados posibles de una orden"""
    PENDING = "pending"              # Esperando ser enviada
    SENT = "sent"                    # Enviada al exchange
    PARTIAL = "partial"              # Parcialmente ejecutada
    FILLED = "filled"                # Totalmente ejecutada
    FAILED = "failed"                # Falló en envío
    RECOVERY = "recovery"            # En proceso de recuperación
    CANCELLED = "cancelled"          # Cancelada


@dataclass
class PersistedOrder:
    """Estructura de orden persistida"""
    order_id: str
    symbol: str
    order_type: str                  # 'buy', 'sell', 'limit_buy', etc.
    side: str                        # 'buy' o 'sell'
    amount: float
    price: Optional[float] = None
    status: str = OrderStatus.PENDING.value
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    exchange_id: Optional[str] = None # ID del exchange si fue enviada
    retries: int = 0
    max_retries: int = 5
    error_message: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable"""
        data = asdict(self)
        data['timestamp'] = self.timestamp  # Asegurar string
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PersistedOrder':
        """Crea desde diccionario"""
        return PersistedOrder(**data)
    
    def is_json_serializable(self) -> bool:
        """Verifica si está listo para JSON"""
        try:
            json.dumps(self.to_dict())
            return True
        except (TypeError, ValueError):
            return False


class OrderPersistenceManager:
    """
    Gestor de persistencia de órdenes en JSON.
    
    Responsabilidades:
    - Guardar órdenes en flight a JSON
    - Cargar órdenes no procesadas ante recuperación
    - Marcar órdenes como procesadas/completadas
    - Limpiar órdenes antiguas
    - Proporcionar estadísticas de recuperación
    """
    
    def __init__(
        self,
        persistence_dir: Optional[str] = None,
        exchange_name: str = "bybit",
        max_age_hours: int = 24,
        cleanup_interval_seconds: int = 3600
    ):
        """
        Inicializa el gestor de persistencia.
        
        Args:
            persistence_dir: Directorio para almacenar órdenes (default: descarga_datos/data/orders/)
            exchange_name: Nombre del exchange para namespacing
            max_age_hours: Horas máximas para mantener órdenes antiguas
            cleanup_interval_seconds: Intervalo de limpieza automática
        """
        # Configurar directorio
        if persistence_dir is None:
            persistence_dir = Path(__file__).parent.parent / "data" / "orders"
        else:
            persistence_dir = Path(persistence_dir)
        
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        self.exchange_name = exchange_name
        self.max_age_hours = max_age_hours
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Lock para thread-safety
        self._lock = threading.RLock()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas
        self._stats = {
            'saved': 0,
            'loaded': 0,
            'recovered': 0,
            'failed': 0,
            'cleaned': 0
        }
        
        self.logger.info(
            f"OrderPersistenceManager inicializado: "
            f"dir={self.persistence_dir}, exchange={exchange_name}"
        )
    
    def _get_orders_file(self) -> Path:
        """Obtiene ruta del archivo de órdenes del exchange actual"""
        return self.persistence_dir / f"orders_{self.exchange_name}.json"
    
    def _get_recovery_file(self) -> Path:
        """Obtiene ruta del archivo de recuperación"""
        return self.persistence_dir / f"recovery_{self.exchange_name}.json"
    
    def _generate_order_id(self) -> str:
        """Genera ID único para orden local"""
        return str(uuid.uuid4())[:12]
    
    def save_order(self, order: PersistedOrder) -> bool:
        """
        Guarda una orden en persistencia.
        
        Args:
            order: PersistedOrder a guardar
            
        Returns:
            True si fue exitoso, False si falló
        """
        try:
            with self._lock:
                # Validar que sea serializable
                if not order.is_json_serializable():
                    self.logger.error(f"Orden no serializable: {order}")
                    return False
                
                # Cargar órdenes existentes
                orders = self._load_all_orders()
                
                # Actualizar o agregar orden
                order_dict = order.to_dict()
                orders[order.order_id] = order_dict
                
                # Guardar a archivo
                orders_file = self._get_orders_file()
                with open(orders_file, 'w') as f:
                    json.dump(orders, f, indent=2)
                
                self._stats['saved'] += 1
                self.logger.debug(f"Orden guardada: {order.order_id} ({order.symbol})")
                return True
                
        except Exception as e:
            self.logger.error(f"Error guardando orden {order.order_id}: {e}")
            self._stats['failed'] += 1
            return False
    
    def save_orders_batch(self, orders: List[PersistedOrder]) -> int:
        """
        Guarda múltiples órdenes.
        
        Args:
            orders: Lista de PersistedOrder
            
        Returns:
            Número de órdenes guardadas exitosamente
        """
        saved = 0
        for order in orders:
            if self.save_order(order):
                saved += 1
        return saved
    
    def load_pending_orders(self) -> List[PersistedOrder]:
        """
        Carga órdenes pendientes para recuperación.
        
        Returns:
            Lista de PersistedOrder en estado PENDING o RECOVERY
        """
        try:
            with self._lock:
                orders_file = self._get_orders_file()
                if not orders_file.exists():
                    return []
                
                with open(orders_file, 'r') as f:
                    data = json.load(f)
                
                pending = []
                for order_id, order_data in data.items():
                    try:
                        order = PersistedOrder.from_dict(order_data)
                        # Recuperar pendientes y órdenes con fallos
                        if order.status in [
                            OrderStatus.PENDING.value,
                            OrderStatus.FAILED.value,
                            OrderStatus.RECOVERY.value
                        ]:
                            pending.append(order)
                    except Exception as e:
                        self.logger.warning(f"Error cargando orden {order_id}: {e}")
                
                self._stats['loaded'] += len(pending)
                self.logger.info(f"Cargadas {len(pending)} órdenes pendientes")
                return pending
                
        except Exception as e:
            self.logger.error(f"Error cargando órdenes pendientes: {e}")
            return []
    
    def load_all_orders(self) -> Dict[str, PersistedOrder]:
        """
        Carga todas las órdenes del archivo.
        
        Returns:
            Diccionario con order_id -> PersistedOrder
        """
        try:
            with self._lock:
                orders_file = self._get_orders_file()
                if not orders_file.exists():
                    return {}
                
                with open(orders_file, 'r') as f:
                    data = json.load(f)
                
                orders = {}
                for order_id, order_data in data.items():
                    try:
                        orders[order_id] = PersistedOrder.from_dict(order_data)
                    except Exception as e:
                        self.logger.warning(f"Error cargando orden {order_id}: {e}")
                
                return orders
                
        except Exception as e:
            self.logger.error(f"Error cargando todas las órdenes: {e}")
            return {}
    
    def _load_all_orders(self) -> Dict[str, Dict[str, Any]]:
        """Carga órdenes como diccionarios (sin lock)"""
        orders_file = self._get_orders_file()
        if not orders_file.exists():
            return {}
        
        with open(orders_file, 'r') as f:
            return json.load(f)
    
    def update_order_status(
        self,
        order_id: str,
        status: str,
        exchange_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Actualiza el estado de una orden.
        
        Args:
            order_id: ID de la orden
            status: Nuevo estado (usar OrderStatus enum)
            exchange_id: ID del exchange si fue asignado
            error_message: Mensaje de error si aplica
            
        Returns:
            True si fue exitoso
        """
        try:
            with self._lock:
                orders = self._load_all_orders()
                
                if order_id not in orders:
                    self.logger.warning(f"Orden no encontrada: {order_id}")
                    return False
                
                orders[order_id]['status'] = status
                if exchange_id:
                    orders[order_id]['exchange_id'] = exchange_id
                if error_message:
                    orders[order_id]['error_message'] = error_message
                
                # Guardar actualización
                orders_file = self._get_orders_file()
                with open(orders_file, 'w') as f:
                    json.dump(orders, f, indent=2)
                
                self.logger.debug(f"Orden actualizada: {order_id} -> {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error actualizando orden {order_id}: {e}")
            return False
    
    def increment_retry_count(self, order_id: str) -> bool:
        """
        Incrementa contador de reintentos.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            True si se incrementó, False si alcanzó max_retries
        """
        try:
            with self._lock:
                orders = self._load_all_orders()
                
                if order_id not in orders:
                    return False
                
                order_data = orders[order_id]
                current_retries = order_data.get('retries', 0)
                max_retries = order_data.get('max_retries', 5)
                
                if current_retries >= max_retries:
                    order_data['status'] = OrderStatus.FAILED.value
                    self.logger.warning(
                        f"Orden {order_id} alcanzó max retries ({max_retries})"
                    )
                    success = False
                else:
                    order_data['retries'] = current_retries + 1
                    success = True
                
                # Guardar
                orders_file = self._get_orders_file()
                with open(orders_file, 'w') as f:
                    json.dump(orders, f, indent=2)
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error incrementando retry para {order_id}: {e}")
            return False
    
    def mark_completed(self, order_id: str) -> bool:
        """
        Marca una orden como completada.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            True si fue exitoso
        """
        return self.update_order_status(order_id, OrderStatus.FILLED.value)
    
    def remove_order(self, order_id: str) -> bool:
        """
        Elimina una orden del archivo.
        
        Args:
            order_id: ID de la orden
            
        Returns:
            True si fue exitoso
        """
        try:
            with self._lock:
                orders = self._load_all_orders()
                
                if order_id in orders:
                    del orders[order_id]
                    
                    orders_file = self._get_orders_file()
                    with open(orders_file, 'w') as f:
                        json.dump(orders, f, indent=2)
                    
                    self.logger.debug(f"Orden eliminada: {order_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error eliminando orden {order_id}: {e}")
            return False
    
    def cleanup_old_orders(self) -> int:
        """
        Limpia órdenes completadas/fallidas antiguas.
        
        Returns:
            Número de órdenes eliminadas
        """
        try:
            with self._lock:
                orders = self._load_all_orders()
                cutoff_time = datetime.fromisoformat(
                    (datetime.now() - __import__('datetime').timedelta(
                        hours=self.max_age_hours
                    )).isoformat()
                )
                
                to_delete = []
                for order_id, order_data in orders.items():
                    try:
                        order_time = datetime.fromisoformat(order_data['timestamp'])
                        status = order_data.get('status', OrderStatus.PENDING.value)
                        
                        # Eliminar si es vieja y no está pendiente
                        if (order_time < cutoff_time and 
                            status in [OrderStatus.FILLED.value, OrderStatus.FAILED.value]):
                            to_delete.append(order_id)
                    except Exception as e:
                        self.logger.debug(f"Error parseando orden {order_id}: {e}")
                
                # Eliminar
                for order_id in to_delete:
                    del orders[order_id]
                
                if to_delete:
                    orders_file = self._get_orders_file()
                    with open(orders_file, 'w') as f:
                        json.dump(orders, f, indent=2)
                    
                    self._stats['cleaned'] += len(to_delete)
                    self.logger.info(f"Limpiadas {len(to_delete)} órdenes antiguas")
                
                return len(to_delete)
                
        except Exception as e:
            self.logger.error(f"Error limpiando órdenes antiguas: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de persistencia.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self._lock:
                orders = self._load_all_orders()
                
                status_counts = {}
                for order_id, order_data in orders.items():
                    status = order_data.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                return {
                    'total_orders': len(orders),
                    'status_breakdown': status_counts,
                    'statistics': self._stats.copy(),
                    'last_cleanup': getattr(self, '_last_cleanup', None),
                    'persistence_dir': str(self.persistence_dir)
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo stats: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del sistema de persistencia.
        
        Returns:
            Diccionario con estado de salud
        """
        try:
            with self._lock:
                orders_file = self._get_orders_file()
                
                health = {
                    'healthy': True,
                    'errors': [],
                    'warnings': []
                }
                
                # Verificar acceso a directorios
                if not self.persistence_dir.exists():
                    health['healthy'] = False
                    health['errors'].append(
                        f"Directorio de persistencia no existe: {self.persistence_dir}"
                    )
                
                # Verificar permisos de escritura
                try:
                    test_file = self.persistence_dir / ".healthcheck"
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    health['healthy'] = False
                    health['errors'].append(f"Sin permisos de escritura: {e}")
                
                # Cargar órdenes para validación
                try:
                    orders = self._load_all_orders()
                    pending = sum(
                        1 for order in orders.values()
                        if order.get('status') == OrderStatus.PENDING.value
                    )
                    if pending > 10:
                        health['warnings'].append(
                            f"Muchas órdenes pendientes ({pending})"
                        )
                except Exception as e:
                    health['warnings'].append(f"Error cargando órdenes: {e}")
                
                return health
                
        except Exception as e:
            return {
                'healthy': False,
                'errors': [str(e)],
                'warnings': []
            }


# Instancia global
_persistence_manager: Optional[OrderPersistenceManager] = None


def get_order_persistence_manager(
    exchange_name: str = "bybit",
    persistence_dir: Optional[str] = None
) -> OrderPersistenceManager:
    """
    Obtiene gestor de persistencia (singleton por exchange).
    
    Args:
        exchange_name: Nombre del exchange
        persistence_dir: Directorio personalizado (opcional)
        
    Returns:
        OrderPersistenceManager singleton
    """
    global _persistence_manager
    
    if _persistence_manager is None or _persistence_manager.exchange_name != exchange_name:
        _persistence_manager = OrderPersistenceManager(
            persistence_dir=persistence_dir,
            exchange_name=exchange_name
        )
    
    return _persistence_manager
