"""
MÓDULO DE CÁLCULO DE P&L CON COMISIONES
========================================

Calcula P&L (Profit & Loss) incluyendo comisiones reales.
Patrón de Freqtrade - Precisión completa en reportes de ganancias/pérdidas.

Características:
1. Comisiones dinámicas por exchange
2. Comisiones de entrada Y salida
3. Validación de precisión numérica
4. Conversión automática de tipos
5. Logging detallado de cálculos

Author: Freqtrade Pattern Adaptation
Date: 28 Octubre 2025
"""

import logging
import math
from typing import Dict, Optional, Tuple, List, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FeeType(Enum):
    """Tipos de comisión"""
    TAKER = "taker"           # Orden que toma liquidez
    MAKER = "maker"           # Orden que agrega liquidez
    SPREAD = "spread"         # Diferencial (forex, etc)


@dataclass
class FeeStructure:
    """Estructura de comisiones de un exchange"""
    exchange: str
    taker_fee: float          # Comisión taker (ej: 0.0002 = 0.02%)
    maker_fee: float          # Comisión maker (ej: 0.0001 = 0.01%)
    spread_pips: float = 0.0  # Spreads en pips (forex)
    
    def get_fee(self, fee_type: FeeType = FeeType.TAKER) -> float:
        """Obtiene comisión según tipo"""
        if fee_type == FeeType.TAKER:
            return self.taker_fee
        elif fee_type == FeeType.MAKER:
            return self.maker_fee
        else:
            return self.spread_pips


# Alias para compatibilidad con tests
ExchangeConfig = FeeStructure


@dataclass
class TradeData:
    """Datos de un trade para P&L calculation"""
    trade_id: str
    symbol: str
    side: str  # 'buy' o 'sell'
    entry_price: float
    exit_price: float
    amount: float
    entry_time: datetime
    exit_time: datetime
    entry_fee_rate: float = 0.0002
    exit_fee_rate: float = 0.0002
    leverage: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'amount': self.amount,
            'entry_time': self.entry_time.isoformat() if isinstance(self.entry_time, datetime) else self.entry_time,
            'exit_time': self.exit_time.isoformat() if isinstance(self.exit_time, datetime) else self.exit_time,
            'entry_fee_rate': self.entry_fee_rate,
            'exit_fee_rate': self.exit_fee_rate,
            'leverage': self.leverage,
        }


@dataclass
class Trade:
    """Representa un trade completado"""
    trade_id: str
    symbol: str
    side: str  # 'buy' o 'sell' (long/short)
    
    # Entry
    entry_price: float
    entry_time: datetime
    entry_amount: float
    
    # Exit
    exit_price: float
    exit_time: datetime
    exit_amount: float  # Puede diferir por fills parciales
    
    # Fee structure
    exchange: str
    entry_fee_rate: float = 0.0002  # Bybit default
    exit_fee_rate: float = 0.0002
    
    # Additional metadata
    leverage: float = 1.0
    realized_pnl: Optional[float] = None
    realized_pnl_percent: Optional[float] = None
    fees_paid: Optional[float] = None


class PnLCalculator:
    """
    Calcula P&L con comisiones reales.
    
    Implementa patrón de Freqtrade:
    - Comisiones por exchange (taker/maker/spread)
    - Cálculo P&L bruto vs neto
    - Validación de precisión
    - Estadísticas agregadas
    """
    
    # Base de datos de comisiones por exchange
    EXCHANGES_STRUCTURE = {
        'bybit': FeeStructure(
            exchange='bybit',
            taker_fee=0.0002,      # 0.02% taker
            maker_fee=0.0001,      # 0.01% maker
        ),
        'binance': FeeStructure(
            exchange='binance',
            taker_fee=0.001,       # 0.1% taker
            maker_fee=0.001,       # 0.1% maker
        ),
        'kucoin': FeeStructure(
            exchange='kucoin',
            taker_fee=0.001,       # 0.1% taker
            maker_fee=0.001,       # 0.1% maker
        ),
        'mt5_forex': FeeStructure(
            exchange='mt5_forex',
            taker_fee=0.0,         # Sin comisión, hay spread
            maker_fee=0.0,
            spread_pips=1.0,       # ~1-2 pips típico
        ),
        'default': FeeStructure(
            exchange='default',
            taker_fee=0.001,       # Default fallback
            maker_fee=0.001,
        ),
    }
    
    def __init__(self, logger=None, logger_instance=None):
        """
        Inicializa calculador de P&L
        
        Args:
            logger: Logger personalizado
            logger_instance: Logger personalizado (alias para logger)
        """
        self.logger = logger or logger_instance or logger
        self.trades_history: List[Trade] = []
        self.total_fees_paid = 0.0
        
        if self.logger:
            self.logger.info("PnLCalculator inicializado")
    
    @staticmethod
    def get_fee_structure(exchange: str) -> FeeStructure:
        """
        Obtiene estructura de comisiones de un exchange.
        
        Args:
            exchange: Nombre del exchange
            
        Returns:
            FeeStructure con comisiones
        """
        return PnLCalculator.EXCHANGES_STRUCTURE.get(
            exchange.lower(),
            PnLCalculator.EXCHANGES_STRUCTURE['default']
        )
    
    @staticmethod
    def validate_numeric(value: Any, name: str = "value") -> float:
        """
        Valida y convierte a float, con manejo de errores.
        
        Args:
            value: Valor a validar
            name: Nombre del parámetro (para logs)
            
        Returns:
            Float validado
            
        Raises:
            ValueError: Si no se puede convertir
        """
        try:
            if value is None:
                raise ValueError(f"{name} es None")
            
            float_val = float(value)
            
            # Verificar NaN e infinito
            if math.isnan(float_val) or math.isinf(float_val):
                raise ValueError(f"{name} es NaN o infinito")
            
            return float_val
        
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error validando {name}: {str(e)}")
    
    def calculate_pnl_with_fees(
        self,
        entry_price: float,
        exit_price: float,
        amount: float,
        exchange: str = 'bybit',
        fee_type: FeeType = FeeType.TAKER,
        leverage: float = 1.0
    ) -> Dict[str, float]:
        """
        Calcula P&L incluyendo comisiones.
        
        Fórmula Freqtrade:
        P&L_bruto = (exit_price - entry_price) * amount * leverage
        comisión_entrada = entry_price * amount * fee_rate
        comisión_salida = exit_price * amount * fee_rate
        P&L_neto = P&L_bruto - comisión_entrada - comisión_salida
        
        Args:
            entry_price: Precio de entrada
            exit_price: Precio de salida
            amount: Cantidad de la posición
            exchange: Nombre del exchange
            fee_type: Tipo de comisión (taker/maker)
            leverage: Apalancamiento
            
        Returns:
            Diccionario con breakdown de P&L:
            {
                'pnl_gross': bruto sin comisiones,
                'fee_entry': comisión entrada,
                'fee_exit': comisión salida,
                'total_fees': comisión total,
                'pnl_net': neto después de comisiones,
                'pnl_percent': porcentaje de ganancia/pérdida,
                'roi': ROI en %,
            }
        """
        # Validar inputs
        entry_price = self.validate_numeric(entry_price, "entry_price")
        exit_price = self.validate_numeric(exit_price, "exit_price")
        amount = self.validate_numeric(amount, "amount")
        leverage = self.validate_numeric(leverage, "leverage")
        
        if entry_price <= 0 or exit_price <= 0 or amount <= 0:
            raise ValueError("Precios y amount deben ser positivos")
        
        # Obtener estructura de comisiones
        fee_struct = self.get_fee_structure(exchange)
        fee_rate = fee_struct.get_fee(fee_type)
        
        try:
            # ==================================================================================
            # CÁLCULO P&L BRUTO (sin comisiones)
            # ==================================================================================
            price_difference = exit_price - entry_price
            pnl_gross = price_difference * amount * leverage
            
            # ==================================================================================
            # CÁLCULO DE COMISIONES
            # ==================================================================================
            
            # Comisión entrada: basada en valor de entrada
            entry_value = entry_price * amount
            fee_entry = entry_value * fee_rate
            
            # Comisión salida: basada en valor de salida
            exit_value = exit_price * amount
            fee_exit = exit_value * fee_rate
            
            # Total comisiones
            total_fees = fee_entry + fee_exit
            
            # ==================================================================================
            # CÁLCULO P&L NETO (después de comisiones)
            # ==================================================================================
            pnl_net = pnl_gross - total_fees
            
            # ==================================================================================
            # PORCENTAJES Y MÉTRICAS
            # ==================================================================================
            
            # Porcentaje basado en valor inicial
            pnl_percent = (pnl_net / entry_value) * 100 if entry_value > 0 else 0
            
            # ROI (Return on Investment)
            roi = (pnl_net / entry_value) * 100 if entry_value > 0 else 0
            
            result = {
                # Precios
                'entry_price': entry_price,
                'exit_price': exit_price,
                'price_change': price_difference,
                'price_change_percent': (price_difference / entry_price) * 100,
                
                # Valores de posición
                'amount': amount,
                'entry_value': entry_value,
                'exit_value': exit_value,
                'leverage': leverage,
                
                # P&L
                'pnl_gross': round(pnl_gross, 8),
                'pnl_net': round(pnl_net, 8),
                'pnl_percent': round(pnl_percent, 4),
                'roi': round(roi, 4),
                
                # Comisiones
                'fee_rate': fee_rate,
                'fee_entry': round(fee_entry, 8),
                'fee_exit': round(fee_exit, 8),
                'total_fees': round(total_fees, 8),
                'fees_percent': round((total_fees / entry_value) * 100, 4),
                
                # Metadata
                'exchange': exchange,
                'fee_type': fee_type.value,
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ Error calculando P&L: {str(e)}")
            raise
    
    def calculate_trade_pnl(self, trade: Trade) -> Trade:
        """
        Calcula P&L para un trade completado.
        
        Args:
            trade: Objeto Trade
            
        Returns:
            Trade con P&L calculado
        """
        try:
            # Obtener estructura de comisiones
            fee_struct = self.get_fee_structure(trade.exchange)
            
            # Usar comisiones del trade o defaults
            entry_fee = trade.entry_fee_rate or fee_struct.taker_fee
            exit_fee = trade.exit_fee_rate or fee_struct.taker_fee
            
            # Calcular P&L
            pnl_result = self.calculate_pnl_with_fees(
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                amount=trade.exit_amount or trade.entry_amount,
                exchange=trade.exchange,
                leverage=trade.leverage
            )
            
            # Asignar resultados al trade
            trade.realized_pnl = pnl_result['pnl_net']
            trade.realized_pnl_percent = pnl_result['pnl_percent']
            trade.fees_paid = pnl_result['total_fees']
            
            # Registrar en historial
            self.trades_history.append(trade)
            self.total_fees_paid += pnl_result['total_fees']
            
            self.logger.info(
                f"✅ Trade {trade.trade_id} calculado: "
                f"P&L=${trade.realized_pnl:.2f} ({trade.realized_pnl_percent:.2f}%), "
                f"Comisiones=${trade.fees_paid:.4f}"
            )
            
            return trade
        
        except Exception as e:
            self.logger.error(f"❌ Error calculando P&L de trade: {str(e)}")
            raise
    
    def calculate_total_pnl_with_fees(
        self,
        trades: List[Any],
        exchange: str = 'bybit',
        include_slippage: bool = False
    ) -> float:
        """
        Calcula P&L total para un conjunto de trades incluyendo comisiones.
        
        ✅ IMPORTANTE: La estrategia reporta P&L como:
        pnl = (exit_price - entry_price) * position_size
        
        Donde position_size = risk_amount_usd / stop_distance_en_dollares
        
        Esto es correcto: position_size es un "MULTIPLICADOR DE RIESGO", no cantidad de monedas.
        pnl = price_change_en_dollares * position_size = P&L en USD ✓
        
        Las comisiones se calculan como porcentaje del VALOR de la posición en USD:
        valor_posicion_usd = entry_price * position_size
        commission = valor_posicion_usd * fee_rate * 2  (entrada + salida)
            
        Returns:
            P&L total neto en USD (después de comisiones)
        """
        try:
            total_pnl = 0.0
            total_fees = 0.0
            
            # Obtener estructura de comisiones
            fee_struct = self.get_fee_structure(exchange)
            commission_rate = fee_struct.taker_fee  # 0.0002 para Bybit (0.02%)
            
            for trade in trades:
                try:
                    pnl_gross = trade.get('pnl', 0)  # YA en USD desde la estrategia
                    entry_price = trade.get('entry_price', 0)
                    position_size = trade.get('position_size', 0)  # EN UNIDADES DE RIESGO (USD/punto)
                    trade_id = trade.get('entry_time', 'unknown')
                    
                    # Calcular valor EFECTIVO de posición en USD
                    # position_size * entry_price = cuántos USD se exponen en el mercado
                    position_value_usd = entry_price * position_size
                    
                    # Comisiones: 0.02% entrada + 0.02% salida (total 0.04%)
                    # commission = position_value_usd * 0.0002 * 2
                    total_commission = position_value_usd * commission_rate * 2
                    
                    # P&L neto = P&L bruto - comisiones
                    pnl_net = pnl_gross - total_commission
                    
                    total_pnl += pnl_net
                    total_fees += total_commission
                    
                except Exception as e:
                    self.logger.warning(f"Error calculando P&L para trade {trade_id}: {e}")
                    continue
            
            self.logger.info(f"✅ P&L Total: ${total_pnl:.2f} ({len(trades)} trades)")
            self.logger.info(f"✅ Total Comisiones: ${total_fees:.2f}")
            return total_pnl
        
        except Exception as e:
            self.logger.error(f"❌ Error calculando P&L total: {str(e)}")
            raise
    
    def get_aggregated_statistics(self) -> Dict:
        """Obtiene estadísticas agregadas de todos los trades"""
        if not self.trades_history:
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'total_fees': 0.0,
                'win_rate': 0.0,
            }
        
        winning_trades = [t for t in self.trades_history if t.realized_pnl and t.realized_pnl > 0]
        losing_trades = [t for t in self.trades_history if t.realized_pnl and t.realized_pnl < 0]
        
        total_pnl = sum(t.realized_pnl or 0 for t in self.trades_history)
        
        return {
            'total_trades': len(self.trades_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.trades_history) * 100) if self.trades_history else 0,
            'total_pnl': round(total_pnl, 2),
            'total_fees': round(self.total_fees_paid, 4),
            'avg_pnl_per_trade': round(total_pnl / len(self.trades_history), 2) if self.trades_history else 0,
            'avg_fees_per_trade': round(self.total_fees_paid / len(self.trades_history), 4) if self.trades_history else 0,
        }
    
    def format_pnl_report(self, pnl_data: Dict) -> str:
        """Formatea P&L como string legible"""
        return (
            f"P&L REPORT\n"
            f"{'='*50}\n"
            f"Entry Price:       ${pnl_data['entry_price']:>10.2f}\n"
            f"Exit Price:        ${pnl_data['exit_price']:>10.2f}\n"
            f"Price Change:      {pnl_data['price_change_percent']:>9.2f}%\n"
            f"\n"
            f"P&L Bruto:         ${pnl_data['pnl_gross']:>10.2f}\n"
            f"Comisiones:        ${pnl_data['total_fees']:>10.4f} ({pnl_data['fees_percent']:.2f}%)\n"
            f"  - Entrada:       ${pnl_data['fee_entry']:>10.4f}\n"
            f"  - Salida:        ${pnl_data['fee_exit']:>10.4f}\n"
            f"\n"
            f"P&L Neto:          ${pnl_data['pnl_net']:>10.2f}\n"
            f"ROI:               {pnl_data['roi']:>9.2f}%\n"
            f"Exchange:          {pnl_data['exchange']:>10}\n"
        )


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def create_pnl_calculator() -> PnLCalculator:
    """Factory para crear calculador de P&L"""
    return PnLCalculator()


def quick_calculate_pnl(
    entry_price: float,
    exit_price: float,
    amount: float,
    exchange: str = 'bybit'
) -> Dict[str, float]:
    """
    Cálculo rápido de P&L sin crear instancia.
    
    Args:
        entry_price: Precio de entrada
        exit_price: Precio de salida
        amount: Cantidad
        exchange: Nombre del exchange
        
    Returns:
        Diccionario con P&L
    """
    calculator = PnLCalculator()
    return calculator.calculate_pnl_with_fees(
        entry_price=entry_price,
        exit_price=exit_price,
        amount=amount,
        exchange=exchange
    )
