"""
MÓDULO DE SINCRONIZACIÓN DE POSICIONES
========================================

Sincroniza posiciones locales con estado real en exchange.
Patrón copiado de Freqtrade - Validación robusta de órdenes.

Este módulo verifica:
1. Órdenes abiertas en exchange vs tracking local
2. Fills parciales no registrados
3. Órdenes cerradas no sincronizadas
4. Discrepancias en volumen/precio

Author: Freqtrade Pattern Adaptation
Date: 28 Octubre 2025
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Estados de órdenes según CCXT"""
    OPEN = 'open'
    CLOSED = 'closed'
    CANCELED = 'canceled'
    EXPIRED = 'expired'


class SyncStatus(Enum):
    """Estados de sincronización"""
    SYNCED = 'synced'
    OUT_OF_SYNC = 'out_of_sync'
    PARTIAL_SYNC = 'partial_sync'
    ERROR = 'error'


class OrderType(Enum):
    """Tipos de órdenes"""
    MARKET = 'market'
    LIMIT = 'limit'
    STOP_LOSS = 'stop_loss'
    TAKE_PROFIT = 'take_profit'
    BRACKET = 'bracket'


@dataclass
class ExchangeOrderData:
    """Datos de orden del exchange"""
    order_id: str
    pair: str
    side: str
    amount: float
    price: float
    status: str
    filled: float
    timestamp: datetime
    fee: Optional[float] = None
    fee_currency: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'pair': self.pair,
            'side': self.side,
            'amount': self.amount,
            'price': self.price,
            'status': self.status,
            'filled': self.filled,
            'timestamp': self.timestamp.isoformat(),
            'fee': self.fee,
            'fee_currency': self.fee_currency,
        }


class ExchangeError(Exception):
    """Error genérico de exchange"""
    pass


class OrderNotFound(ExchangeError):
    """Orden no encontrada en exchange"""
    pass


class PartialFillError(ExchangeError):
    """Fill parcial detectado"""
    pass


@dataclass
class LocalOrder:
    """Orden en tracking local"""
    order_id: str
    pair: str
    side: str  # 'buy' o 'sell'
    amount: float
    price: float
    status: str
    timestamp: datetime
    filled: float = 0.0
    fee: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'pair': self.pair,
            'side': self.side,
            'amount': self.amount,
            'price': self.price,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'filled': self.filled,
            'fee': self.fee,
        }


@dataclass
class SyncResult:
    """Resultado de sincronización"""
    is_synced: bool
    local_orders: List[LocalOrder]
    exchange_orders: List[Dict]
    mismatches: List[Dict]
    timestamp: datetime


class PositionSynchronizer:
    """
    Sincroniza posiciones entre tracking local y exchange real.
    
    Implementa patrón robusto de Freqtrade:
    - Retry automático con exponential backoff
    - Validación exhaustiva de órdenes
    - Logging detallado de discrepancias
    - Reconciliación segura
    """
    
    # Configuración de reintentos
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # segundos
    BACKOFF_FACTOR = 2
    
    # Comisiones por exchange (Taker fees)
    EXCHANGES_FEE = {
        'bybit': 0.0002,      # 0.02% Bybit taker
        'binance': 0.001,     # 0.1% Binance taker
        'kucoin': 0.001,      # 0.1% KuCoin taker
        'default': 0.001,     # Default fallback
    }
    
    def __init__(self, exchange_client=None, order_executor=None, logger=None, logger_instance=None):
        """
        Inicializa sincronizador
        
        Args:
            exchange_client: Cliente CCXT o similar (alias para order_executor)
            order_executor: Ejecutor de órdenes
            logger: Logger personalizado
            logger_instance: Logger personalizado (alias para logger)
        """
        # Aceptar ambos nombres para compatibilidad
        self.exchange = exchange_client or order_executor
        self.order_executor = order_executor or exchange_client
        self.logger = logger or logger_instance or logger
        self.local_orders: Dict[str, LocalOrder] = {}
        self.last_sync_time: Optional[datetime] = None
        self.sync_count = 0
        
        if self.logger:
            self.logger.info("PositionSynchronizer inicializado")
    
    def fetch_open_orders_with_retry(
        self, 
        pair: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> List[Dict]:
        """
        Obtiene órdenes abiertas del exchange con reintentos automáticos.
        
        Patrón de Freqtrade: fetch_open_orders con retry y validación
        
        Args:
            pair: Par a buscar (None = todos)
            max_retries: Número máximo de reintentos
            
        Returns:
            Lista de órdenes abiertas
            
        Raises:
            ExchangeError: Si falla después de reintentos
        """
        if max_retries is None:
            max_retries = self.MAX_RETRIES
        
        if not self.exchange:
            self.logger.warning("❌ Exchange client no configurado")
            return []
        
        retry_count = 0
        delay = self.RETRY_DELAY
        
        while retry_count < max_retries:
            try:
                self.logger.debug(
                    f"📡 Fetching open orders (intento {retry_count + 1}/{max_retries})"
                )
                
                # Obtener órdenes del exchange
                orders = self.exchange.fetch_open_orders(pair)
                
                # Validar órdenes
                self._validate_orders(orders)
                
                self.logger.debug(f"✅ Fetcheadas {len(orders)} órdenes abiertas")
                return orders
                
            except (ExchangeError, ConnectionError, TimeoutError) as e:
                retry_count += 1
                
                if retry_count >= max_retries:
                    self.logger.error(
                        f"❌ Fetch open orders falló después de {max_retries} reintentos: {str(e)}"
                    )
                    raise
                
                # Esperar antes de reintentar (exponential backoff)
                self.logger.warning(
                    f"⚠️  Reintentando en {delay}s... (intento {retry_count}/{max_retries})"
                )
                time.sleep(delay)
                delay *= self.BACKOFF_FACTOR
        
        return []
    
    def _validate_orders(self, orders: List[Dict]) -> bool:
        """
        Valida que órdenes tienen estructura correcta.
        
        Args:
            orders: Lista de órdenes a validar
            
        Returns:
            True si todas son válidas
            
        Raises:
            ValueError: Si orden falta campos requeridos
        """
        required_fields = ['id', 'symbol', 'side', 'amount', 'price', 'status']
        
        for order in orders:
            # Verificar campos requeridos
            missing = [f for f in required_fields if f not in order]
            if missing:
                self.logger.warning(
                    f"⚠️  Orden {order.get('id', 'UNKNOWN')} "
                    f"falta campos: {missing}"
                )
                continue
            
            # Validar tipos
            try:
                assert isinstance(order['amount'], (int, float)), "amount debe ser numérico"
                assert isinstance(order['price'], (int, float)), "price debe ser numérico"
                assert order['status'] in [
                    'open', 'closed', 'canceled', 'expired'
                ], f"status inválido: {order['status']}"
                
            except AssertionError as e:
                self.logger.warning(f"⚠️  Validación fallida para orden: {e}")
                continue
        
        return True
    
    def validate_order_against_exchange(
        self,
        order_id: str,
        local_order: LocalOrder
    ) -> Tuple[bool, Dict]:
        """
        Valida una orden local contra estado real en exchange.
        
        Patrón de Freqtrade: validate_order_time_in_force
        
        Args:
            order_id: ID de la orden
            local_order: Orden en tracking local
            
        Returns:
            Tupla (is_valid, exchange_order_data)
        """
        try:
            # Obtener orden del exchange
            real_order = self.exchange.fetch_order(order_id, local_order.pair)
            
            # Comparar estados
            if real_order['status'] != local_order.status:
                self.logger.warning(
                    f"⚠️  Status mismatch para {order_id}: "
                    f"local={local_order.status}, exchange={real_order['status']}"
                )
                
                # Si exchange dice closed pero local dice open → actualizar
                if real_order['status'] == 'closed' and local_order.status == 'open':
                    self.logger.info(f"🔄 Actualizando estado: {order_id} → closed")
                    local_order.status = 'closed'
                    local_order.filled = real_order.get('filled', 0.0)
            
            # Verificar filled parcial
            if real_order.get('filled', 0.0) < local_order.amount:
                if real_order['status'] == 'open':
                    self.logger.info(
                        f"ℹ️  Fill parcial en {order_id}: "
                        f"{real_order.get('filled', 0.0)}/{local_order.amount}"
                    )
            
            return True, real_order
            
        except Exception as e:
            self.logger.error(f"❌ Error validando orden {order_id}: {str(e)}")
            return False, {}
    
    def reconcile_local_vs_exchange(
        self,
        local_positions: Dict[str, LocalOrder],
        pair: Optional[str] = None
    ) -> SyncResult:
        """
        Reconcilia todas las posiciones locales con estado del exchange.
        
        Patrón de Freqtrade: position reconciliation
        
        Args:
            local_positions: Diccionario de órdenes locales
            pair: Par específico a reconciliar (None = todos)
            
        Returns:
            SyncResult con estado de sincronización
        """
        self.sync_count += 1
        timestamp = datetime.now()
        mismatches = []
        
        self.logger.info(
            f"🔄 Iniciando reconciliación #{self.sync_count} "
            f"(local: {len(local_positions)} órdenes)"
        )
        
        try:
            # Obtener órdenes del exchange
            exchange_orders = self.fetch_open_orders_with_retry(pair)
            exchange_ids = {order['id'] for order in exchange_orders}
            
            # Verificar cada orden local
            for order_id, local_order in local_positions.items():
                if pair and local_order.pair != pair:
                    continue
                
                # Verificar si existe en exchange
                if order_id not in exchange_ids:
                    if local_order.status == 'open':
                        mismatches.append({
                            'type': 'missing_in_exchange',
                            'order_id': order_id,
                            'local_status': local_order.status,
                            'action': 'Marcar como cerrada localmente'
                        })
                        self.logger.warning(
                            f"⚠️  Orden {order_id} no encontrada en exchange "
                            f"pero está abierta localmente"
                        )
                else:
                    # Validar orden encontrada
                    is_valid, exchange_order = self.validate_order_against_exchange(
                        order_id, local_order
                    )
                    
                    if not is_valid:
                        mismatches.append({
                            'type': 'validation_failed',
                            'order_id': order_id,
                            'reason': 'Error durante validación'
                        })
            
            # Verificar órdenes en exchange que no están localmente (inesperado)
            local_ids = set(local_positions.keys())
            for exchange_order in exchange_orders:
                if exchange_order['id'] not in local_ids:
                    mismatches.append({
                        'type': 'unknown_in_exchange',
                        'order_id': exchange_order['id'],
                        'pair': exchange_order['symbol'],
                        'action': 'Investigar origen de orden'
                    })
                    self.logger.warning(
                        f"⚠️  Orden desconocida en exchange: {exchange_order['id']}"
                    )
            
            # Generar resultado
            is_synced = len(mismatches) == 0
            self.last_sync_time = timestamp
            
            if is_synced:
                self.logger.info(f"✅ Sincronización exitosa #{self.sync_count}")
            else:
                self.logger.warning(
                    f"⚠️  Sincronización completada con {len(mismatches)} discrepancias"
                )
            
            return SyncResult(
                is_synced=is_synced,
                local_orders=list(local_positions.values()),
                exchange_orders=exchange_orders,
                mismatches=mismatches,
                timestamp=timestamp
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error en reconciliación: {str(e)}")
            return SyncResult(
                is_synced=False,
                local_orders=list(local_positions.values()),
                exchange_orders=[],
                mismatches=[{'type': 'sync_error', 'error': str(e)}],
                timestamp=timestamp
            )
    
    def get_fee_rate(self, exchange: str) -> float:
        """
        Obtiene comisión (taker fee) para un exchange.
        
        Args:
            exchange: Nombre del exchange
            
        Returns:
            Tasa de comisión (ej: 0.0002 para 0.02%)
        """
        rate = self.EXCHANGES_FEE.get(exchange, self.EXCHANGES_FEE['default'])
        self.logger.debug(f"Fee rate para {exchange}: {rate*100:.4f}%")
        return rate
    
    def handle_order_mismatch(self, mismatch: Dict) -> Dict:
        """
        Maneja una discrepancia entre local y exchange.
        
        Args:
            mismatch: Diccionario con detalles del mismatch
            
        Returns:
            Diccionario con acción recomendada
        """
        mismatch_type = mismatch.get('type', 'unknown')
        
        if mismatch_type == 'missing_in_exchange':
            self.logger.warning(
                f"🔧 Manejando: Orden {mismatch['order_id']} "
                f"desaparecida del exchange"
            )
            return {
                'action': 'close_locally',
                'reason': 'Order not found in exchange',
                'order_id': mismatch['order_id']
            }
        
        elif mismatch_type == 'unknown_in_exchange':
            self.logger.warning(
                f"🔧 Manejando: Orden {mismatch['order_id']} "
                f"desconocida en local"
            )
            return {
                'action': 'investigate',
                'reason': 'Unknown order in exchange',
                'order_id': mismatch['order_id']
            }
        
        else:
            return {
                'action': 'log_and_alert',
                'reason': f'Mismatch type: {mismatch_type}',
                'order_id': mismatch.get('order_id', 'unknown')
            }
    
    def sync_positions_with_exchange(
        self,
        local_positions: Dict[str, Any],
        strategy_configs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sincroniza posiciones locales con posiciones reales en MT5.
        Método específico para live trading MT5 - NO usa exchange CCXT.

        Args:
            local_positions: Diccionario de posiciones locales
            strategy_configs: Configuraciones de estrategias

        Returns:
            Dict con resultado de sincronización
        """
        try:
            self.logger.info("[SYNC MT5] Iniciando sincronización con broker MT5...")

            # Obtener posiciones abiertas desde MT5
            mt5_positions = self._fetch_mt5_positions()

            # Convertir posiciones locales a formato comparable
            local_positions_formatted = self._format_local_positions(local_positions)

            # Comparar posiciones
            sync_result = self._compare_positions(local_positions_formatted, mt5_positions)

            # Procesar discrepancias
            processed_result = self._process_mt5_sync_result(sync_result)

            self.logger.info(f"[SYNC MT5] Sincronización completada: {processed_result}")

            return processed_result

        except Exception as e:
            self.logger.error(f"[SYNC MT5] Error en sincronización: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'matched': 0,
                'mismatches': 0,
                'external_closes': [],
                'updated_positions': local_positions
            }

    def _fetch_mt5_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene posiciones abiertas desde MT5.

        Returns:
            Lista de posiciones MT5
        """
        try:
            # Usar el order_executor para obtener posiciones MT5
            if hasattr(self.order_executor, 'get_positions'):
                positions = self.order_executor.get_positions()
                self.logger.debug(f"[SYNC MT5] Obtenidas {len(positions)} posiciones de MT5")
                return positions
            else:
                self.logger.warning("[SYNC MT5] Order executor no tiene método get_positions")
                return []

        except Exception as e:
            self.logger.error(f"[SYNC MT5] Error obteniendo posiciones MT5: {str(e)}")
            return []

    def _format_local_positions(self, local_positions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formatea posiciones locales para comparación.

        Args:
            local_positions: Posiciones locales del orchestrator

        Returns:
            Lista formateada de posiciones locales
        """
        formatted = []

        for position_id, position_data in local_positions.items():
            formatted.append({
                'ticket': position_data.get('ticket', position_id),
                'symbol': position_data.get('symbol', ''),
                'type': position_data.get('type', position_data.get('direction', 'buy')),
                'volume': position_data.get('volume', position_data.get('amount', 0)),
                'price': position_data.get('price', position_data.get('entry_price', 0)),
                'sl': position_data.get('sl', position_data.get('stop_loss', 0)),
                'tp': position_data.get('tp', position_data.get('take_profit', 0)),
                'profit': position_data.get('profit', 0),
                'status': 'open'
            })

        self.logger.debug(f"[SYNC MT5] Formateadas {len(formatted)} posiciones locales")
        return formatted

    def _compare_positions(
        self,
        local_positions: List[Dict[str, Any]],
        mt5_positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compara posiciones locales vs MT5.

        Args:
            local_positions: Posiciones locales formateadas
            mt5_positions: Posiciones de MT5

        Returns:
            Dict con resultado de comparación
        """
        matched = []
        mismatches = []
        external_closes = []

        # Crear mapas por símbolo para comparación
        local_by_symbol = {}
        for pos in local_positions:
            symbol = pos.get('symbol', '')
            if symbol not in local_by_symbol:
                local_by_symbol[symbol] = []
            local_by_symbol[symbol].append(pos)

        mt5_by_symbol = {}
        for pos in mt5_positions:
            symbol = pos.get('symbol', '')
            if symbol not in mt5_by_symbol:
                mt5_by_symbol[symbol] = []
            mt5_by_symbol[symbol].append(pos)

        # Comparar por símbolo
        all_symbols = set(local_by_symbol.keys()) | set(mt5_by_symbol.keys())

        for symbol in all_symbols:
            local_symbol_positions = local_by_symbol.get(symbol, [])
            mt5_symbol_positions = mt5_by_symbol.get(symbol, [])

            # Si no hay posiciones locales pero sí en MT5 → posiciones externas
            if not local_symbol_positions and mt5_symbol_positions:
                for mt5_pos in mt5_symbol_positions:
                    mismatches.append({
                        'type': 'external_position',
                        'symbol': symbol,
                        'mt5_position': mt5_pos
                    })

            # Si hay posiciones locales pero no en MT5 → posibles cierres externos
            elif local_symbol_positions and not mt5_symbol_positions:
                for local_pos in local_symbol_positions:
                    external_closes.append({
                        'ticket': local_pos.get('ticket'),
                        'symbol': symbol,
                        'reason': 'closed_externally',
                        'local_position': local_pos
                    })

            # Si hay posiciones en ambos, comparar
            elif local_symbol_positions and mt5_symbol_positions:
                # Lógica simplificada: asumir que coinciden si hay al menos una posición por símbolo
                matched.extend(local_symbol_positions)

        return {
            'matched': matched,
            'mismatches': mismatches,
            'external_closes': external_closes,
            'total_local': len(local_positions),
            'total_mt5': len(mt5_positions)
        }

    def _process_mt5_sync_result(self, sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa resultado de sincronización MT5.

        Args:
            sync_result: Resultado de comparación

        Returns:
            Dict formateado para el orchestrator
        """
        matched_count = len(sync_result.get('matched', []))
        mismatches_count = len(sync_result.get('mismatches', []))
        external_closes = sync_result.get('external_closes', [])

        # Determinar estado
        if mismatches_count == 0 and len(external_closes) == 0:
            status = 'success'
        elif mismatches_count > 0:
            status = 'warning'
        else:
            status = 'partial'

        result = {
            'status': status,
            'matched': matched_count,
            'mismatches': mismatches_count,
            'external_closes': external_closes,
            'updated_positions': {},  # Por ahora no actualizamos posiciones
            'message': f"Sincronización MT5: {matched_count} coincidencias, {mismatches_count} desajustes, {len(external_closes)} cierres externos"
        }

        self.logger.info(f"[SYNC MT5] {result['message']}")
        return result


# ============================================================================
# FUNCIONES DE CONVENIENCIA (Para integración fácil)
# ============================================================================

def create_synchronizer(exchange_client=None) -> PositionSynchronizer:
    """Factory para crear sincronizador"""
    return PositionSynchronizer(exchange_client=exchange_client)


def validate_order_exists_on_exchange(
    synchronizer: PositionSynchronizer,
    order_id: str,
    pair: str,
    max_retries: int = 2
) -> bool:
    """
    Conveniencia: Validar que orden existe en exchange
    
    Args:
        synchronizer: Instancia de PositionSynchronizer
        order_id: ID de orden
        pair: Par (ej: 'BTC/USDT')
        max_retries: Reintentos
        
    Returns:
        True si orden existe y es válida
    """
    try:
        order = synchronizer.exchange.fetch_order(order_id, pair)
        return order is not None
    except Exception as e:
        logger.warning(f"❌ Orden {order_id} no encontrada: {str(e)}")
        return False
