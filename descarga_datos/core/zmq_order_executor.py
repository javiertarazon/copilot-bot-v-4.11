#!/usr/bin/env python3
"""
ZMQ Order Executor - Ejecutor de órdenes via ZeroMQ para comunicación con EA en MT5.

Este módulo implementa un ejecutor de órdenes que se comunica con un Expert Advisor (EA)
en MetaTrader 5 a través de ZeroMQ, proporcionando:
- Baja latencia (<10ms)
- Datos tick-by-tick
- Ejecución nativa de órdenes en MT5 via EA
- Heartbeats para detectar desconexiones

Author: GitHub Copilot
Date: Enero 2026
Version: 4.11
"""

import zmq
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field

from utils.logger import get_logger, setup_logger
from utils.retry_manager import retry_operation

# Logger del módulo
logger = setup_logger('ZMQOrderExecutor')


class ZMQOrderType(Enum):
    """Tipos de órdenes para ZMQ (mapean a MT5)"""
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5


@dataclass
class ZMQPosition:
    """Representa una posición abierta recibida del EA"""
    ticket: int
    symbol: str
    order_type: int  # 0=BUY, 1=SELL
    volume: float
    open_price: float
    sl: float
    tp: float
    profit: float
    open_time: datetime
    magic: int = 0
    comment: str = ""


@dataclass
class ZMQTick:
    """Representa un tick recibido del EA"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime
    flags: int = 0


class ZMQOrderExecutor:
    """
    Ejecutor de órdenes que se comunica con un EA en MT5 via ZeroMQ.
    
    Proporciona la misma interfaz que MT5OrderExecutor pero con comunicación
    a través de sockets ZMQ para:
    - Menor latencia
    - Datos tick-by-tick
    - Ejecución nativa en MT5
    
    Attributes:
        zmq_orders_url: URL para envío de órdenes (REQ/REP)
        zmq_ticks_url: URL para recepción de ticks (SUB)
        timeout_ms: Timeout en milisegundos para operaciones
        heartbeat_interval: Intervalo de heartbeat en segundos
    """
    
    # Magic number para identificar órdenes del bot
    MAGIC_NUMBER = 20260129
    
    def __init__(
        self,
        config: Dict = None,
        zmq_orders_url: str = 'tcp://localhost:5555',
        zmq_ticks_url: str = 'tcp://localhost:5556',
        timeout_ms: int = 5000,
        heartbeat_interval: int = 10,
        account_type: str = 'DEMO',
        risk_per_trade: float = 0.01,
        max_positions: int = 5
    ):
        """
        Inicializa el ejecutor ZMQ.
        
        Args:
            config: Configuración del live trading
            zmq_orders_url: URL del socket para órdenes (REQ/REP)
            zmq_ticks_url: URL del socket para ticks (SUB)
            timeout_ms: Timeout para operaciones ZMQ
            heartbeat_interval: Intervalo de heartbeat en segundos
            account_type: Tipo de cuenta (DEMO/REAL)
            risk_per_trade: Riesgo por operación (porcentaje)
            max_positions: Máximo de posiciones simultáneas
        """
        self.config = config or {}
        self.zmq_orders_url = zmq_orders_url
        self.zmq_ticks_url = zmq_ticks_url
        self.timeout_ms = timeout_ms
        self.heartbeat_interval = heartbeat_interval
        self.account_type = account_type
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        
        # Leer configuración ZMQ del config si está disponible
        zmq_config = self.config.get('zmq', {})
        if zmq_config:
            self.zmq_orders_url = zmq_config.get('orders_url', self.zmq_orders_url)
            self.zmq_ticks_url = zmq_config.get('ticks_url', self.zmq_ticks_url)
            self.timeout_ms = zmq_config.get('timeout_ms', self.timeout_ms)
            self.heartbeat_interval = zmq_config.get('heartbeat_interval', self.heartbeat_interval)
        
        # Contexto y sockets ZMQ
        self.context: zmq.Context = None
        self.orders_socket: zmq.Socket = None
        self.ticks_socket: zmq.Socket = None
        
        # Estado de conexión
        self._connected = False
        self._last_heartbeat = None
        self._heartbeat_thread: threading.Thread = None
        self._stop_heartbeat = threading.Event()
        
        # Cache de posiciones
        self._positions_cache: Dict[int, ZMQPosition] = {}
        self._positions_lock = threading.Lock()
        
        # Ticks en tiempo real
        self._ticks_buffer: Dict[str, List[ZMQTick]] = {}
        self._ticks_thread: threading.Thread = None
        self._stop_ticks = threading.Event()
        
        # Logger
        self.logger = logger
        
        # Estadísticas
        self.stats = {
            'orders_sent': 0,
            'orders_success': 0,
            'orders_failed': 0,
            'avg_latency_ms': 0.0,
            'ticks_received': 0
        }
    
    def initialize(self) -> bool:
        """
        Inicializa la conexión ZMQ con el EA.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            self.logger.info("="*60)
            self.logger.info("🔌 Inicializando ZMQ Order Executor...")
            self.logger.info(f"   Orders URL: {self.zmq_orders_url}")
            self.logger.info(f"   Ticks URL: {self.zmq_ticks_url}")
            
            # Crear contexto ZMQ
            self.context = zmq.Context()
            
            # Socket para órdenes (REQ/REP pattern)
            self.orders_socket = self.context.socket(zmq.REQ)
            self.orders_socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
            self.orders_socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
            self.orders_socket.setsockopt(zmq.LINGER, 0)
            self.orders_socket.connect(self.zmq_orders_url)
            
            # Socket para ticks (SUB pattern)
            self.ticks_socket = self.context.socket(zmq.SUB)
            self.ticks_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 segundo timeout para ticks
            self.ticks_socket.connect(self.zmq_ticks_url)
            self.ticks_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribirse a todo
            
            # Verificar conexión con heartbeat
            if self._send_heartbeat():
                self._connected = True
                self._last_heartbeat = datetime.now()
                
                # Iniciar thread de heartbeat
                self._start_heartbeat_thread()
                
                # Iniciar thread de recepción de ticks
                self._start_ticks_thread()
                
                self.logger.info("✅ ZMQ conectado exitosamente al EA")
                return True
            else:
                self.logger.error("❌ No se pudo establecer conexión con el EA")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando ZMQ: {e}")
            return False
    
    def shutdown(self) -> None:
        """Cierra la conexión ZMQ de forma segura."""
        self.logger.info("🔌 Cerrando conexión ZMQ...")
        
        # Detener threads
        self._stop_heartbeat.set()
        self._stop_ticks.set()
        
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)
        
        if self._ticks_thread and self._ticks_thread.is_alive():
            self._ticks_thread.join(timeout=2)
        
        # Cerrar sockets
        if self.orders_socket:
            self.orders_socket.close()
        if self.ticks_socket:
            self.ticks_socket.close()
        if self.context:
            self.context.term()
        
        self._connected = False
        self.logger.info("✅ ZMQ desconectado")
    
    def is_connected(self) -> bool:
        """Verifica si hay conexión activa con el EA."""
        return self._connected and self._last_heartbeat is not None
    
    def _send_heartbeat(self) -> bool:
        """Envía heartbeat al EA y verifica respuesta."""
        try:
            request = {'action': 'heartbeat', 'timestamp': time.time()}
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            return response.get('status') == 'ok'
        except zmq.Again:
            self.logger.warning("⚠️ Timeout en heartbeat")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error en heartbeat: {e}")
            return False
    
    def _start_heartbeat_thread(self) -> None:
        """Inicia el thread de heartbeat."""
        def heartbeat_loop():
            while not self._stop_heartbeat.is_set():
                if self._send_heartbeat():
                    self._last_heartbeat = datetime.now()
                    self._connected = True
                else:
                    self._connected = False
                    self.logger.warning("⚠️ Conexión con EA perdida")
                
                self._stop_heartbeat.wait(self.heartbeat_interval)
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def _start_ticks_thread(self) -> None:
        """Inicia el thread de recepción de ticks."""
        def ticks_loop():
            while not self._stop_ticks.is_set():
                try:
                    tick_data = self.ticks_socket.recv_json(flags=zmq.NOBLOCK)
                    tick = ZMQTick(
                        symbol=tick_data['symbol'],
                        bid=tick_data['bid'],
                        ask=tick_data['ask'],
                        last=tick_data.get('last', 0),
                        volume=tick_data.get('volume', 0),
                        time=datetime.fromtimestamp(tick_data['time']),
                        flags=tick_data.get('flags', 0)
                    )
                    
                    # Agregar al buffer
                    symbol = tick.symbol
                    if symbol not in self._ticks_buffer:
                        self._ticks_buffer[symbol] = []
                    self._ticks_buffer[symbol].append(tick)
                    
                    # Limitar buffer a últimos 1000 ticks por símbolo
                    if len(self._ticks_buffer[symbol]) > 1000:
                        self._ticks_buffer[symbol] = self._ticks_buffer[symbol][-1000:]
                    
                    self.stats['ticks_received'] += 1
                    
                except zmq.Again:
                    pass  # No hay datos disponibles
                except Exception as e:
                    self.logger.debug(f"Error recibiendo tick: {e}")
                
                time.sleep(0.001)  # 1ms para no saturar CPU
        
        self._ticks_thread = threading.Thread(target=ticks_loop, daemon=True)
        self._ticks_thread.start()
    
    @retry_operation(retries=3, delay=1)
    def send_order(
        self,
        symbol: str,
        order_type: ZMQOrderType,
        volume: float,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = ""
    ) -> Optional[int]:
        """
        Envía una orden al EA para ejecución.
        
        Args:
            symbol: Símbolo a operar
            order_type: Tipo de orden (BUY, SELL, etc.)
            volume: Volumen en lotes
            price: Precio (0 para mercado)
            sl: Stop Loss
            tp: Take Profit
            comment: Comentario de la orden
            
        Returns:
            Ticket de la orden si fue exitosa, None si falló
        """
        if not self.is_connected():
            self.logger.error("❌ No hay conexión con el EA")
            return None
        
        try:
            start_time = time.time()
            
            order_data = {
                'action': 'order',
                'symbol': symbol,
                'type': order_type.value if isinstance(order_type, ZMQOrderType) else order_type,
                'volume': volume,
                'price': price,
                'sl': sl,
                'tp': tp,
                'magic': self.MAGIC_NUMBER,
                'comment': comment or f"BOT_{datetime.now().strftime('%H%M%S')}"
            }
            
            self.logger.info(f"📤 Enviando orden: {symbol} {order_type.name if isinstance(order_type, ZMQOrderType) else order_type} {volume} lots")
            self.orders_socket.send_json(order_data)
            
            response = self.orders_socket.recv_json()
            latency_ms = (time.time() - start_time) * 1000
            
            self.stats['orders_sent'] += 1
            
            # Actualizar latencia promedio
            n = self.stats['orders_sent']
            self.stats['avg_latency_ms'] = (self.stats['avg_latency_ms'] * (n-1) + latency_ms) / n
            
            if response.get('status') == 'ok':
                ticket = response.get('ticket')
                self.stats['orders_success'] += 1
                self.logger.info(f"✅ Orden ejecutada: ticket={ticket}, latencia={latency_ms:.1f}ms")
                return ticket
            else:
                error = response.get('error', 'Unknown error')
                self.stats['orders_failed'] += 1
                self.logger.error(f"❌ Orden rechazada: {error}")
                return None
                
        except zmq.Again:
            self.logger.error("❌ Timeout esperando respuesta del EA")
            self.stats['orders_failed'] += 1
            raise  # Re-raise para retry
        except Exception as e:
            self.logger.error(f"❌ Error enviando orden: {e}")
            self.stats['orders_failed'] += 1
            raise
    
    def open_position(
        self,
        symbol: str,
        direction: str,  # 'BUY' o 'SELL'
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = ""
    ) -> Optional[int]:
        """
        Abre una posición de mercado.
        
        Args:
            symbol: Símbolo a operar
            direction: 'BUY' o 'SELL'
            volume: Volumen en lotes
            sl: Stop Loss (precio)
            tp: Take Profit (precio)
            comment: Comentario
            
        Returns:
            Ticket de la posición si fue exitosa
        """
        order_type = ZMQOrderType.BUY if direction.upper() == 'BUY' else ZMQOrderType.SELL
        return self.send_order(symbol, order_type, volume, 0.0, sl, tp, comment)
    
    def close_position(self, ticket: int, volume: float = None) -> bool:
        """
        Cierra una posición existente.
        
        Args:
            ticket: Ticket de la posición a cerrar
            volume: Volumen a cerrar (None = todo)
            
        Returns:
            True si se cerró exitosamente
        """
        if not self.is_connected():
            return False
        
        try:
            request = {
                'action': 'close',
                'ticket': ticket,
                'volume': volume
            }
            
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            
            if response.get('status') == 'ok':
                self.logger.info(f"✅ Posición {ticket} cerrada")
                return True
            else:
                self.logger.error(f"❌ Error cerrando posición: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error cerrando posición: {e}")
            return False
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> bool:
        """
        Modifica SL/TP de una posición existente.
        
        Args:
            ticket: Ticket de la posición
            sl: Nuevo Stop Loss (None = no cambiar)
            tp: Nuevo Take Profit (None = no cambiar)
            
        Returns:
            True si se modificó exitosamente
        """
        if not self.is_connected():
            return False
        
        try:
            request = {
                'action': 'modify',
                'ticket': ticket,
                'sl': sl,
                'tp': tp
            }
            
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            
            if response.get('status') == 'ok':
                self.logger.info(f"✅ Posición {ticket} modificada: SL={sl}, TP={tp}")
                return True
            else:
                self.logger.error(f"❌ Error modificando posición: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error modificando posición: {e}")
            return False
    
    def get_positions(self, symbol: str = None) -> List[ZMQPosition]:
        """
        Obtiene posiciones abiertas del EA.
        
        Args:
            symbol: Filtrar por símbolo (None = todas)
            
        Returns:
            Lista de posiciones abiertas
        """
        if not self.is_connected():
            return []
        
        try:
            request = {
                'action': 'get_positions',
                'symbol': symbol,
                'magic': self.MAGIC_NUMBER
            }
            
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            
            if response.get('status') == 'ok':
                positions = []
                for pos_data in response.get('positions', []):
                    pos = ZMQPosition(
                        ticket=pos_data['ticket'],
                        symbol=pos_data['symbol'],
                        order_type=pos_data['type'],
                        volume=pos_data['volume'],
                        open_price=pos_data['open_price'],
                        sl=pos_data['sl'],
                        tp=pos_data['tp'],
                        profit=pos_data['profit'],
                        open_time=datetime.fromtimestamp(pos_data['open_time']),
                        magic=pos_data.get('magic', 0),
                        comment=pos_data.get('comment', '')
                    )
                    positions.append(pos)
                
                # Actualizar cache
                with self._positions_lock:
                    self._positions_cache = {p.ticket: p for p in positions}
                
                return positions
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo posiciones: {e}")
            return []
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de la cuenta desde el EA.
        
        Returns:
            Diccionario con info de cuenta o None
        """
        if not self.is_connected():
            return None
        
        try:
            request = {'action': 'account_info'}
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            
            if response.get('status') == 'ok':
                return response.get('account')
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo info de cuenta: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un símbolo desde el EA.
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            Diccionario con info del símbolo o None
        """
        if not self.is_connected():
            return None
        
        try:
            request = {'action': 'symbol_info', 'symbol': symbol}
            self.orders_socket.send_json(request)
            response = self.orders_socket.recv_json()
            
            if response.get('status') == 'ok':
                return response.get('symbol_info')
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo info de símbolo: {e}")
            return None
    
    def get_ticks(self, symbol: str, count: int = 100) -> List[ZMQTick]:
        """
        Obtiene los últimos ticks recibidos para un símbolo.
        
        Args:
            symbol: Símbolo
            count: Número máximo de ticks a retornar
            
        Returns:
            Lista de ticks (más recientes primero)
        """
        if symbol in self._ticks_buffer:
            return list(reversed(self._ticks_buffer[symbol][-count:]))
        return []
    
    def get_current_tick(self, symbol: str) -> Optional[ZMQTick]:
        """
        Obtiene el tick más reciente para un símbolo.
        
        Args:
            symbol: Símbolo
            
        Returns:
            Último tick o None
        """
        if symbol in self._ticks_buffer and self._ticks_buffer[symbol]:
            return self._ticks_buffer[symbol][-1]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del ejecutor."""
        return {
            **self.stats,
            'connected': self.is_connected(),
            'last_heartbeat': self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            'symbols_with_ticks': list(self._ticks_buffer.keys())
        }
    
    # =========================================================================
    # MÉTODOS DE COMPATIBILIDAD CON MT5OrderExecutor
    # =========================================================================
    
    def execute_signal(
        self,
        signal: Dict[str, Any],
        symbol: str,
        current_price: float = None
    ) -> Optional[int]:
        """
        Ejecuta una señal de trading (compatible con MT5OrderExecutor).
        
        Args:
            signal: Diccionario con la señal {'direction': 'BUY'/'SELL', 'sl': ..., 'tp': ...}
            symbol: Símbolo a operar
            current_price: Precio actual (opcional)
            
        Returns:
            Ticket de la posición o None
        """
        direction = signal.get('direction', signal.get('action', 'HOLD'))
        if direction == 'HOLD':
            return None
        
        sl = signal.get('sl', signal.get('stop_loss', 0.0))
        tp = signal.get('tp', signal.get('take_profit', 0.0))
        volume = signal.get('volume', signal.get('quantity', 0.01))
        comment = signal.get('comment', 'BOT_SIGNAL')
        
        return self.open_position(symbol, direction, volume, sl, tp, comment)
    
    def has_open_position(self, symbol: str = None) -> bool:
        """Verifica si hay posiciones abiertas."""
        positions = self.get_positions(symbol)
        return len(positions) > 0
    
    def get_open_positions_count(self) -> int:
        """Retorna el número de posiciones abiertas."""
        return len(self.get_positions())


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_zmq_executor(config: Dict = None) -> ZMQOrderExecutor:
    """
    Crea una instancia de ZMQOrderExecutor con la configuración proporcionada.
    
    Args:
        config: Configuración del sistema
        
    Returns:
        Instancia configurada de ZMQOrderExecutor
    """
    zmq_config = config.get('zmq', {}) if config else {}
    live_config = config.get('live_trading', {}) if config else {}
    
    return ZMQOrderExecutor(
        config=live_config,
        zmq_orders_url=zmq_config.get('orders_url', 'tcp://localhost:5555'),
        zmq_ticks_url=zmq_config.get('ticks_url', 'tcp://localhost:5556'),
        timeout_ms=zmq_config.get('timeout_ms', 5000),
        heartbeat_interval=zmq_config.get('heartbeat_interval', 10),
        account_type=live_config.get('account_type', 'DEMO'),
        risk_per_trade=live_config.get('risk_per_trade', 0.01),
        max_positions=live_config.get('max_positions', 5)
    )
