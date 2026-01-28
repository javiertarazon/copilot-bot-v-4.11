"""
MÓDULO DE TRAILING STOP CORRECTO
=================================

Implementa trailing stops dinámicos con doble tracking.
Patrón de Freqtrade: Local tracking + órdenes reales en exchange.

Características:
1. Tracking local del máximo precio
2. Actualización dinámica de stops cada vela
3. Sincronización con órdenes reales en exchange
4. Manejo de gaps y volatilidad
5. Logging exhaustivo de cambios

Author: Freqtrade Pattern Adaptation
Date: 28 Octubre 2025
"""

import logging
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

logger = logging.getLogger(__name__)


class StopType(Enum):
    """Tipos de stop"""
    FIXED = "fixed"           # Stop fijo (SL inicial)
    TRAILING = "trailing"     # Stop móvil (sigue el precio)
    ATR_BASED = "atr_based"   # Basado en volatilidad (ATR)


class PositionType(Enum):
    """Tipos de posición"""
    LONG = "long"
    SHORT = "short"


@dataclass
class TrailingStopState:
    """Estado de un trailing stop"""
    position_id: str
    symbol: str
    side: str  # 'long' o 'short'
    entry_price: float
    entry_time: datetime
    stop_type: StopType
    
    # Stop prices
    current_stop: float
    initial_stop_price: float = 0.0 # Stop inicial para cálculo de breakeven
    highest_price: float = 0.0  # Long: máximo alcanzado
    lowest_price: float = float('inf')  # Short: mínimo alcanzado
    
    # Configuration
    atr_period: int = 14
    atr_multiplier: float = 2.25
    stop_distance_percent: float = 0.80  # 80% trailing (ajustado por petición usuario)
    
    # State
    last_update: datetime = field(default_factory=datetime.now)
    updates_count: int = 0
    updates_history: List[Dict] = field(default_factory=list)
    synced_with_exchange: bool = False
    exchange_order_id: Optional[str] = None


class TrailingStopManager:
    """
    Gestiona trailing stops con sincronización exchange.
    
    Implementa patrón de Freqtrade:
    - Tracking local del máximo/mínimo
    - Actualización dinámica por vela
    - Órdenes reales en exchange (stop-loss orders)
    - Validación de sincronización
    """
    
    def __init__(
        self,
        exchange_client=None,
        logger=None,
        logger_instance=None,
        default_atr_multiplier: float = 2.25
    ):
        """
        Inicializa gestor de trailing stops
        
        Args:
            exchange_client: Cliente CCXT para colocar órdenes
            logger: Logger (alias para logger_instance)
            logger_instance: Logger personalizado
            default_atr_multiplier: Multiplicador ATR por defecto (SL = price - atr*mult)
        """
        self.exchange = exchange_client
        # Aceptar tanto 'logger' como 'logger_instance' para compatibilidad
        self.logger = logger or logger_instance or logger
        self.default_atr_multiplier = default_atr_multiplier
        
        # Tracking de stops activos
        self.active_stops: Dict[str, TrailingStopState] = {}
        
        # Estadísticas
        self.total_stops_created = 0
        self.total_stops_triggered = 0
        self.total_stops_updated = 0
        
        self.logger.info(
            f"TrailingStopManager inicializado (ATR multiplier: {default_atr_multiplier}x)"
        )
    
    def create_trailing_stop(
        self,
        position_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        atr_value: Optional[float] = None,
        stop_type: StopType = StopType.ATR_BASED
    ) -> TrailingStopState:
        """
        Crea un trailing stop para una posición.
        
        Patrón Freqtrade: Inicializa stop basado en ATR
        
        Args:
            position_id: ID único de posición
            symbol: Par (ej: 'BTC/USDT')
            side: 'long' o 'short'
            entry_price: Precio de entrada
            atr_value: Valor ATR (si es None, se calcula después)
            stop_type: Tipo de stop a usar
            
        Returns:
            TrailingStopState con configuración inicial
        """
        # Calcular stop inicial
        if atr_value:
            if side == 'long':
                initial_stop = entry_price - (atr_value * self.default_atr_multiplier)
                highest_price = entry_price
                lowest_price = float('inf')
            else:  # short
                initial_stop = entry_price + (atr_value * self.default_atr_multiplier)
                highest_price = float('inf')
                lowest_price = entry_price
        else:
            # Sin ATR, usar distancia porcentual
            if side == 'long':
                initial_stop = entry_price * 0.98  # 2% por debajo
                highest_price = entry_price
                lowest_price = float('inf')
            else:
                initial_stop = entry_price * 1.02  # 2% por encima
                highest_price = float('inf')
                lowest_price = entry_price
        
        # Crear estado del stop
        stop_state = TrailingStopState(
            position_id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            entry_time=datetime.now(),
            stop_type=stop_type,
            current_stop=initial_stop,
            initial_stop_price=initial_stop,
            highest_price=highest_price,
            lowest_price=lowest_price,
            atr_multiplier=self.default_atr_multiplier,
        )
        
        # Registrar
        self.active_stops[position_id] = stop_state
        self.total_stops_created += 1
        
        # Log
        direction = "Long ⬆️" if side == 'long' else "Short ⬇️"
        self.logger.info(
            f"✅ Trailing stop creado para {position_id} ({direction}): "
            f"Entry=${entry_price:.2f}, Stop=${initial_stop:.2f}"
        )
        
        return stop_state
    
    def update_trailing_stop(
        self,
        position_id: str,
        current_price: float,
        atr_value: Optional[float] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Actualiza trailing stop con precio actual.
        
        Lógica:
        - Long: Si actual > máximo anterior → subirlo con ATR
        - Short: Si actual < mínimo anterior → bajarlo con ATR
        
        Patrón Freqtrade: update_trade_state + adjust_stoploss
        
        Args:
            position_id: ID de posición
            current_price: Precio actual
            atr_value: Valor ATR actual
            
        Returns:
            Tupla (fue_actualizado, cambio_dict)
        """
        if position_id not in self.active_stops:
            self.logger.warning(f"⚠️  Stop no encontrado para {position_id}")
            return False, None
        
        stop_state = self.active_stops[position_id]
        old_stop = stop_state.current_stop
        was_updated = False
        change_info = None
        
        try:
            if stop_state.side == 'long':
                # LONG: Stop sigue al máximo
                if current_price > stop_state.highest_price:
                    # Nuevo máximo, actualizar stop
                    stop_state.highest_price = current_price
                    
                    if atr_value:
                        new_stop = current_price - (atr_value * self.default_atr_multiplier)
                    else:
                        new_stop = current_price * 0.98

                    # BREAKEVEN LOGIC: Si ganancia > 25% del riesgo inicial, asegurar BreakEven
                    risk_amount = abs(stop_state.entry_price - stop_state.initial_stop_price)
                    current_profit = current_price - stop_state.entry_price
                    
                    if risk_amount > 0 and current_profit > (risk_amount * 0.25):
                        # Asegurar al menos el precio de entrada + pequeña ganancia (0.1%)
                        be_price = stop_state.entry_price * 1.001
                        new_stop = max(new_stop, be_price)
                        self.logger.debug(f"🛡️ Breakeven activado para {position_id} (Profit: {current_profit:.2f}, Risk: {risk_amount:.2f})")
                    
                    if new_stop > stop_state.current_stop:
                        stop_state.current_stop = new_stop
                        was_updated = True
                        
                        change_info = {
                            'type': 'trailing_stop_updated',
                            'position_id': position_id,
                            'symbol': stop_state.symbol,
                            'side': 'long',
                            'current_price': current_price,
                            'old_stop': old_stop,
                            'new_stop': new_stop,
                            'improvement': new_stop - old_stop,
                        }
                        
                        self.logger.info(
                            f"📈 {position_id} | Trailing stop actualizado: "
                            f"${old_stop:.2f} → ${new_stop:.2f} "
                            f"(precio=${current_price:.2f})"
                        )
            
            else:  # SHORT
                # SHORT: Stop sigue al mínimo
                if current_price < stop_state.lowest_price:
                    # Nuevo mínimo, actualizar stop
                    stop_state.lowest_price = current_price
                    
                    if atr_value:
                        new_stop = current_price + (atr_value * self.default_atr_multiplier)
                    else:
                        new_stop = current_price * 1.02

                    # BREAKEVEN LOGIC: Si ganancia > 25% del riesgo inicial, asegurar BreakEven
                    risk_amount = abs(stop_state.entry_price - stop_state.initial_stop_price)
                    current_profit = stop_state.entry_price - current_price # Short profit
                    
                    if risk_amount > 0 and current_profit > (risk_amount * 0.25):
                        # Asegurar al menos el precio de entrada - pequeña ganancia (0.1%)
                        be_price = stop_state.entry_price * 0.999
                        new_stop = min(new_stop, be_price)
                        self.logger.debug(f"🛡️ Breakeven activado para {position_id} (Profit: {current_profit:.2f}, Risk: {risk_amount:.2f})")
                    
                    if new_stop < stop_state.current_stop:
                        stop_state.current_stop = new_stop
                        was_updated = True
                        
                        change_info = {
                            'type': 'trailing_stop_updated',
                            'position_id': position_id,
                            'symbol': stop_state.symbol,
                            'side': 'short',
                            'current_price': current_price,
                            'old_stop': old_stop,
                            'new_stop': new_stop,
                            'improvement': old_stop - new_stop,
                        }
                        
                        self.logger.info(
                            f"📉 {position_id} | Trailing stop actualizado: "
                            f"${old_stop:.2f} → ${new_stop:.2f} "
                            f"(precio=${current_price:.2f})"
                        )
            
            # Actualizar metadata
            if was_updated:
                stop_state.updates_count += 1
                stop_state.last_update = datetime.now()
                stop_state.updates_history.append(change_info)
                self.total_stops_updated += 1
            
            return was_updated, change_info
        
        except Exception as e:
            self.logger.error(f"❌ Error actualizando stop {position_id}: {str(e)}")
            return False, None
    
    def sync_stop_with_exchange(
        self,
        position_id: str,
        pair: str,
        amount: float
    ) -> bool:
        """
        Sincroniza stop local con orden real en exchange.
        
        Patrón Freqtrade: place_stoploss_order
        
        Args:
            position_id: ID de posición
            pair: Par (ej: 'BTC/USDT')
            amount: Cantidad para la orden
            
        Returns:
            True si fue sincronizado correctamente
        """
        if position_id not in self.active_stops:
            self.logger.warning(f"⚠️  Stop no encontrado: {position_id}")
            return False
        
        if not self.exchange:
            self.logger.warning("⚠️  Exchange no configurado")
            return False
        
        stop_state = self.active_stops[position_id]
        
        try:
            self.logger.debug(
                f"🔄 Sincronizando stop con exchange: "
                f"{position_id} @ ${stop_state.current_stop:.2f}"
            )
            
            # Cancelar orden anterior si existe
            if stop_state.exchange_order_id:
                try:
                    self.exchange.cancel_order(stop_state.exchange_order_id, pair)
                    self.logger.debug(f"  Orden anterior cancelada: {stop_state.exchange_order_id}")
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error cancelando orden anterior: {e}")
            
            # Colocar nueva orden stop-loss
            order_type = 'market'  # Usar market orden para stop
            
            if stop_state.side == 'long':
                # Long: Cerrar con sell si toca stop
                order = self.exchange.create_order(
                    symbol=pair,
                    type=order_type,
                    side='sell',
                    amount=amount,
                    params={
                        'stopPrice': stop_state.current_stop,
                        'type': 'STOP_MARKET',  # Orden stop-market en Bybit
                    }
                )
            else:  # SHORT
                # Short: Cerrar con buy si toca stop
                order = self.exchange.create_order(
                    symbol=pair,
                    type=order_type,
                    side='buy',
                    amount=amount,
                    params={
                        'stopPrice': stop_state.current_stop,
                        'type': 'STOP_MARKET',
                    }
                )
            
            # Guardar ID de orden
            stop_state.exchange_order_id = order['id']
            stop_state.synced_with_exchange = True
            
            self.logger.info(
                f"✅ Stop sincronizado con exchange: "
                f"Orden {order['id']} @ ${stop_state.current_stop:.2f}"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error sincronizando con exchange: {str(e)}")
            return False
    
    def check_stop_triggered(
        self,
        position_id: str,
        current_price: float
    ) -> bool:
        """
        Verifica si un stop fue activado.
        
        Args:
            position_id: ID de posición
            current_price: Precio actual
            
        Returns:
            True si el stop fue activado
        """
        if position_id not in self.active_stops:
            return False
        
        stop_state = self.active_stops[position_id]
        
        triggered = False
        
        if stop_state.side == 'long':
            # Long: Triggered si precio cae por debajo del stop
            triggered = current_price <= stop_state.current_stop
        else:
            # Short: Triggered si precio sube por encima del stop
            triggered = current_price >= stop_state.current_stop
        
        if triggered:
            self.logger.warning(
                f"🛑 STOP ACTIVADO para {position_id}: "
                f"Precio=${current_price:.2f}, Stop=${stop_state.current_stop:.2f}"
            )
            self.total_stops_triggered += 1
            # Remover stop (ya está ejecutado)
            del self.active_stops[position_id]
        
        return triggered
    
    def close_stop(self, position_id: str) -> bool:
        """
        Cierra un trailing stop (posición cerrada manualmente).
        
        Args:
            position_id: ID de posición
            
        Returns:
            True si fue cerrado
        """
        if position_id not in self.active_stops:
            return False
        
        stop_state = self.active_stops[position_id]
        
        try:
            # Cancelar orden en exchange si existe
            if stop_state.exchange_order_id and self.exchange:
                try:
                    self.exchange.cancel_order(
                        stop_state.exchange_order_id,
                        stop_state.symbol
                    )
                except Exception as e:
                    self.logger.warning(
                        f"⚠️  Error cancelando orden en exchange: {e}"
                    )
            
            # Remover del tracking
            del self.active_stops[position_id]
            
            self.logger.info(f"✅ Trailing stop cerrado: {position_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error cerrando stop {position_id}: {e}")
            return False
    
    def get_stop_info(self, position_id: str) -> Optional[Dict]:
        """Obtiene información de un stop activo"""
        if position_id not in self.active_stops:
            return None
        
        stop_state = self.active_stops[position_id]
        
        return {
            'position_id': position_id,
            'symbol': stop_state.symbol,
            'side': stop_state.side,
            'entry_price': stop_state.entry_price,
            'current_stop': stop_state.current_stop,
            'type': stop_state.stop_type.value,
            'updates_count': stop_state.updates_count,
            'synced_with_exchange': stop_state.synced_with_exchange,
            'exchange_order_id': stop_state.exchange_order_id,
        }
    
    def get_all_stops(self) -> List[Dict]:
        """Obtiene información de todos los stops activos"""
        return [
            self.get_stop_info(pos_id)
            for pos_id in self.active_stops.keys()
        ]
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de trailing stops"""
        return {
            'active_stops': len(self.active_stops),
            'total_stops_created': self.total_stops_created,
            'total_stops_triggered': self.total_stops_triggered,
            'total_stops_updated': self.total_stops_updated,
            'trigger_rate': (
                self.total_stops_triggered / self.total_stops_created
                if self.total_stops_created > 0 else 0
            ),
        }


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def create_trailing_stop_manager(
    exchange_client=None,
    atr_multiplier: float = 2.25
) -> TrailingStopManager:
    """Factory para crear gestor de trailing stops"""
    return TrailingStopManager(
        exchange_client=exchange_client,
        default_atr_multiplier=atr_multiplier
    )
