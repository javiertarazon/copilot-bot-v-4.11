
"""
Simple Bridge Executor - Ejecutor de órdenes via EA Simple Bridge
Comunicación por archivos para máxima compatibilidad y seguridad
"""

import os
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
from utils.logger import setup_logger


@dataclass
class Position:
    """Representa una posición abierta"""
    ticket: int
    symbol: str
    type: str
    volume: float
    open_price: float
    sl: float
    tp: float
    profit: float


class SimpleBridgeExecutor:
    """
    Ejecutor de órdenes que se comunica con MT5 via archivos.
    Utiliza el Simple_Bridge_EA.ex5 compilado en MT5.
    
    Ventajas vs Python-MT5 directo:
    - Menor latencia (ejecución nativa en MT5)
    - Mayor seguridad (validación en MQL5)
    - Gestión de riesgo nativa
    - No depende de DLL externos
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el ejecutor.
        
        Args:
            config: Configuración desde config.yaml
        """
        self.logger = setup_logger("SimpleBridgeExecutor")
        self.config = config or {}
        
        # Directorios de comunicación (deben coincidir con MT5 Common Files)
        mt5_common_path = Path(os.getenv('APPDATA')).parent / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
        
        self.command_dir = mt5_common_path / 'Bot_Commands'
        self.response_dir = mt5_common_path / 'Bot_Responses'
        self.ticks_dir = mt5_common_path / 'Bot_Ticks'
        self.data_dir = mt5_common_path / 'Bot_Data'
        
        # Crear directorios si no existen
        for dir_path in [self.command_dir, self.response_dir, self.ticks_dir, self.data_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.timeout = config.get('command_timeout', 10)  # 10 segundos timeout
        self.connected = False
        
        self.logger.info("SimpleBridgeExecutor inicializado")
        self.logger.info(f"Directorio comandos: {self.command_dir}")
    
    def connect(self) -> bool:
        """
        Verifica conexión con el EA.
        
        Returns:
            True si el EA está activo
        """
        try:
            response = self._send_command({'ACTION': 'HEARTBEAT'})
            
            if response and response.get('STATUS') == 'OK':
                self.connected = True
                self.logger.info("✅ Conexión establecida con Simple Bridge EA")
                return True
            else:
                self.logger.error("❌ No se recibió respuesta del EA")
                return False
                
        except Exception as e:
            self.logger.error(f"Error conectando con EA: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión (limpia archivos pendientes)"""
        try:
            # Limpiar archivos pendientes
            for file in self.command_dir.glob('*.cmd'):
                file.unlink()
            for file in self.response_dir.glob('*.rsp'):
                file.unlink()
            
            self.connected = False
            self.logger.info("Desconectado de Simple Bridge EA")
        except Exception as e:
            self.logger.error(f"Error al desconectar: {e}")
    
    def open_position(
        self,
        symbol: str,
        order_type: str,
        quantity: float,
        stop_loss_price: float = None,
        take_profit_price: float = None,
        price: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Abre una posición.
        
        Args:
            symbol: Símbolo a operar
            order_type: 'BUY' o 'SELL'
            quantity: Volumen en lotes
            stop_loss_price: Precio de stop loss
            take_profit_price: Precio de take profit
            price: Precio límite (0 = market)
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            order_type_int = 0 if order_type.upper() == 'BUY' else 1
            
            command = {
                'ACTION': 'ORDER',
                'SYMBOL': symbol,
                'TYPE': order_type_int,
                'VOLUME': quantity,
                'PRICE': price,
                'SL': stop_loss_price or 0.0,
                'TP': take_profit_price or 0.0
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                return {
                    'success': True,
                    'ticket': int(response.get('TICKET', 0)),
                    'price': float(response.get('PRICE', 0.0)),
                    'volume': float(response.get('VOLUME', 0.0)),
                    'symbol': symbol,
                    'type': order_type
                }
            else:
                error = response.get('ERROR', 'Unknown error') if response else 'No response'
                self.logger.error(f"Error abriendo posición: {error}")
                return {'success': False, 'error': error}
                
        except Exception as e:
            self.logger.error(f"Excepción abriendo posición: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_position(
        self,
        ticket: int,
        volume: float = None,
        **kwargs
    ) -> bool:
        """
        Cierra una posición.
        
        Args:
            ticket: Ticket de la posición
            volume: Volumen a cerrar (None = cerrar todo)
            
        Returns:
            True si se cerró exitosamente
        """
        try:
            command = {
                'ACTION': 'CLOSE',
                'TICKET': ticket,
                'VOLUME': volume or 0.0
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                self.logger.info(f"✅ Posición {ticket} cerrada")
                return True
            else:
                error = response.get('ERROR', 'Unknown error') if response else 'No response'
                self.logger.error(f"Error cerrando posición: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción cerrando posición: {e}")
            return False
    
    def modify_position(
        self,
        ticket: int,
        sl: float = None,
        tp: float = None,
        **kwargs
    ) -> bool:
        """
        Modifica SL/TP de una posición.
        
        Args:
            ticket: Ticket de la posición
            sl: Nuevo stop loss (None = mantener actual)
            tp: Nuevo take profit (None = mantener actual)
            
        Returns:
            True si se modificó exitosamente
        """
        try:
            command = {
                'ACTION': 'MODIFY',
                'TICKET': ticket,
                'SL': sl or 0.0,
                'TP': tp or 0.0
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                self.logger.info(f"✅ Posición {ticket} modificada - SL: {sl}, TP: {tp}")
                return True
            else:
                error = response.get('ERROR', 'Unknown error') if response else 'No response'
                self.logger.error(f"Error modificando posición: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción modificando posición: {e}")
            return False
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """
        Obtiene posiciones abiertas.
        
        Args:
            symbol: Filtrar por símbolo (None = todas)
            
        Returns:
            Lista de posiciones
        """
        try:
            command = {
                'ACTION': 'GET_POSITIONS',
                'SYMBOL': symbol or ''
            }
            
            response = self._send_command(command)
            
            if not response or response.get('STATUS') != 'OK':
                return []
            
            positions = []
            count = int(response.get('COUNT', 0))
            
            for i in range(count):
                pos = Position(
                    ticket=int(response.get(f'POS{i}_TICKET', 0)),
                    symbol=response.get(f'POS{i}_SYMBOL', ''),
                    type='BUY' if int(response.get(f'POS{i}_TYPE', 0)) == 0 else 'SELL',
                    volume=float(response.get(f'POS{i}_VOLUME', 0.0)),
                    open_price=float(response.get(f'POS{i}_OPEN_PRICE', 0.0)),
                    sl=float(response.get(f'POS{i}_SL', 0.0)),
                    tp=float(response.get(f'POS{i}_TP', 0.0)),
                    profit=float(response.get(f'POS{i}_PROFIT', 0.0))
                )
                positions.append(pos)
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la cuenta.
        
        Returns:
            Diccionario con datos de la cuenta
        """
        try:
            command = {'ACTION': 'ACCOUNT_INFO'}
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                return {
                    'balance': float(response.get('BALANCE', 0.0)),
                    'equity': float(response.get('EQUITY', 0.0)),
                    'margin': float(response.get('MARGIN', 0.0)),
                    'free_margin': float(response.get('FREE_MARGIN', 0.0)),
                    'profit': float(response.get('PROFIT', 0.0)),
                    'leverage': int(response.get('LEVERAGE', 1)),
                    'currency': response.get('CURRENCY', 'USD'),
                    'server': response.get('SERVER', ''),
                    'trade_allowed': bool(int(response.get('TRADE_ALLOWED', 0)))
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de cuenta: {e}")
            return {}
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene información del símbolo.
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            Diccionario con datos del símbolo
        """
        try:
            command = {
                'ACTION': 'SYMBOL_INFO',
                'SYMBOL': symbol
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                return {
                    'symbol': symbol,
                    'bid': float(response.get('BID', 0.0)),
                    'ask': float(response.get('ASK', 0.0)),
                    'spread': int(response.get('SPREAD', 0)),
                    'point': float(response.get('POINT', 0.00001)),
                    'digits': int(response.get('DIGITS', 5)),
                    'volume_min': float(response.get('VOLUME_MIN', 0.01)),
                    'volume_max': float(response.get('VOLUME_MAX', 100.0))
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de símbolo: {e}")
            return {}
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: int = 15,
        bars: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene datos históricos.
        
        Args:
            symbol: Símbolo
            timeframe: Timeframe en minutos (1, 5, 15, 30, 60, 240, 1440)
            bars: Cantidad de barras
            
        Returns:
            DataFrame con OHLCV
        """
        try:
            command = {
                'ACTION': 'HISTORICAL_DATA',
                'SYMBOL': symbol,
                'TIMEFRAME': timeframe,
                'BARS': bars
            }
            
            response = self._send_command(command, timeout=30)  # Más tiempo para datos históricos
            
            if not response or response.get('STATUS') != 'OK':
                error = response.get('ERROR', 'Unknown error') if response else 'No response'
                self.logger.error(f"Error obteniendo datos históricos: {error}")
                return None
            
            # Leer archivo CSV generado por el EA
            csv_file = self.data_dir / response.get('CSV_FILE', '').replace('Bot_Data\\', '')
            
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                
                self.logger.info(f"✅ Descargadas {len(df)} barras de {symbol} ({timeframe}m)")
                return df
            else:
                self.logger.error(f"Archivo CSV no encontrado: {csv_file}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos: {e}")
            return None
    
    def calculate_lot_size(
        self,
        symbol: str,
        risk_percent: float,
        stop_distance_points: float
    ) -> float:
        """
        Calcula lotaje óptimo basado en riesgo.
        
        Args:
            symbol: Símbolo
            risk_percent: % de riesgo (1.0 = 1%)
            stop_distance_points: Distancia del SL en puntos
            
        Returns:
            Tamaño de lote calculado
        """
        try:
            command = {
                'ACTION': 'CALCULATE_LOT',
                'SYMBOL': symbol,
                'RISK_PERCENT': risk_percent,
                'STOP_DISTANCE': stop_distance_points
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                lot_size = float(response.get('LOT_SIZE', 0.01))
                self.logger.info(f"Lote calculado para {symbol}: {lot_size} (Riesgo: {risk_percent}%)")
                return lot_size
            
            return 0.01  # Mínimo por defecto
            
        except Exception as e:
            self.logger.error(f"Error calculando lotaje: {e}")
            return 0.01
    
    def update_trailing_stops(
        self,
        symbol: str = None,
        trailing_pct: float = 0.65
    ) -> Dict[str, int]:
        """
        Actualiza trailing stops de todas las posiciones.
        
        Args:
            symbol: Filtrar por símbolo (None = todas)
            trailing_pct: % de trailing (0.65 = 65%)
            
        Returns:
            Dict con 'total' y 'updated'
        """
        try:
            command = {
                'ACTION': 'UPDATE_TRAILING',
                'SYMBOL': symbol or '',
                'TRAILING_PCT': trailing_pct
            }
            
            response = self._send_command(command)
            
            if response and response.get('STATUS') == 'OK':
                total = int(response.get('TOTAL_POSITIONS', 0))
                updated = int(response.get('UPDATED', 0))
                
                if updated > 0:
                    self.logger.info(f"✅ Trailing stops actualizados: {updated}/{total} posiciones")
                
                return {'total': total, 'updated': updated}
            
            return {'total': 0, 'updated': 0}
            
        except Exception as e:
            self.logger.error(f"Error actualizando trailing stops: {e}")
            return {'total': 0, 'updated': 0}
    
    def _send_command(
        self,
        command: Dict[str, Any],
        timeout: int = None
    ) -> Optional[Dict[str, str]]:
        """
        Envía comando al EA y espera respuesta.
        NUEVA ESTRATEGIA: Archivo único ACTIVE_COMMAND.cmd
        
        Args:
            command: Diccionario con comando
            timeout: Timeout en segundos
            
        Returns:
            Diccionario con respuesta parseada
        """
        timeout = timeout or self.timeout
        
        #--- Usar archivos únicos en lugar de UUID
        command_file = self.command_dir / "ACTIVE_COMMAND.cmd"
        response_file = self.response_dir / "ACTIVE_COMMAND.rsp"
        
        try:
            # Limpiar archivos anteriores
            if command_file.exists():
                command_file.unlink()
            if response_file.exists():
                response_file.unlink()
            
            # Pequeña espera para asegurar que EA detecta el cambio
            time.sleep(0.05)
            
            # Escribir archivo de comando
            with open(command_file, 'w') as f:
                for key, value in command.items():
                    f.write(f"{key}={value}\n")
            
            self.logger.debug(f"📤 Comando enviado: {command.get('ACTION')}")
            
            # Esperar respuesta
            start_time = time.time()
            while time.time() - start_time < timeout:
                if response_file.exists():
                    time.sleep(0.05)  # Asegurar que el archivo esté completo
                    
                    # Leer respuesta
                    with open(response_file, 'r', encoding='utf-16') as f:
                        response = {}
                        for line in f:
                            line = line.strip()
                            if '=' in line:
                                key, value = line.split('=', 1)
                                response[key] = value
                    
                    self.logger.debug(f"📥 Respuesta recibida: {response.get('STATUS')}")
                    
                    # Limpiar archivos
                    response_file.unlink()
                    
                    return response
                
                time.sleep(0.1)
            
            # Timeout
            self.logger.warning(f"Timeout esperando respuesta para comando {command.get('ACTION')}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error enviando comando: {e}")
            return None
#!/usr/bin/env python3
