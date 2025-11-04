"""
Logger mejorado para pipeline de trading - Visibilidad completa de cada paso.

Proporciona funciones para logging detallado en:
1. Obtención de datos
2. Cálculo de indicadores
3. Generación de señales
4. Aplicación de riesgo
5. Ejecución de órdenes
"""

from utils.logger import get_logger
from typing import Any, Dict, Optional
from datetime import datetime

logger = get_logger(__name__)

class PipelineLogger:
    """Logger estructurado para el pipeline de trading."""
    
    @staticmethod
    def log_data_fetch(symbol: str, timeframe: str, bars: int, timestamp: datetime = None, **kwargs):
        """
        Log: Obtención de datos
        
        Args:
            symbol: Símbolo (ej: "Volatility 75 Index")
            timeframe: Timeframe (ej: "15m")
            bars: Cantidad de barras obtenidas
            timestamp: Timestamp del último dato
            **kwargs: Parámetros adicionales (precio, volumen, etc)
        """
        ts = timestamp.isoformat() if timestamp else "N/A"
        logger.info(f"[PIPELINE 1/5 DATA] {symbol} {timeframe}: {bars} barras | Last: {ts}")
        if kwargs:
            for key, value in kwargs.items():
                logger.debug(f"  - {key}: {value}")
    
    @staticmethod
    def log_indicator_calculation(symbol: str, indicator_count: int, nan_count: int = 0, **indicators):
        """
        Log: Cálculo de indicadores
        
        Args:
            symbol: Símbolo procesado
            indicator_count: Total de indicadores calculados
            nan_count: Cantidad de valores NaN (si aplica)
            **indicators: Últimos valores de indicadores clave
        """
        nan_info = f" | NaN: {nan_count}" if nan_count > 0 else ""
        logger.info(f"[PIPELINE 2/5 INDICATORS] {symbol}: {indicator_count} indicadores calculados{nan_info}")
        for ind_name, ind_value in indicators.items():
            logger.debug(f"  - {ind_name}: {ind_value:.5f}" if isinstance(ind_value, (int, float)) else f"  - {ind_name}: {ind_value}")
    
    @staticmethod
    def log_strategy_signal(strategy_name: str, symbol: str, signal: str, confidence: float = None, 
                           entry_price: float = None, sl: float = None, tp: float = None):
        """
        Log: Generación de señal de la estrategia
        
        Args:
            strategy_name: Nombre de la estrategia
            symbol: Símbolo
            signal: Tipo de señal (BUY, SELL, NO_SIGNAL)
            confidence: Confianza de la señal (0-1)
            entry_price: Precio de entrada
            sl: Stop Loss
            tp: Take Profit
        """
        conf_str = f" | Confidence: {confidence:.3f}" if confidence is not None else ""
        entry_str = f" | Entry: {entry_price:.2f}" if entry_price is not None else ""
        sl_tp_str = f" | SL/TP: {sl:.2f}/{tp:.2f}" if sl is not None and tp is not None else ""
        
        logger.info(f"[PIPELINE 3/5 SIGNAL] {strategy_name} → {symbol}: {signal}{conf_str}{entry_str}{sl_tp_str}")
    
    @staticmethod
    def log_risk_management(symbol: str, action: str, position_size: float = None, risk_amount: float = None,
                           max_loss: float = None, **details):
        """
        Log: Aplicación de gestión de riesgo
        
        Args:
            symbol: Símbolo
            action: Acción tomada (APPROVED, REJECTED, MODIFIED)
            position_size: Tamaño de la posición
            risk_amount: Cantidad en riesgo
            max_loss: Pérdida máxima permitida
            **details: Detalles adicionales (razón de rechazo, etc)
        """
        ps_str = f" | PosSize: {position_size:.4f}" if position_size is not None else ""
        risk_str = f" | Risk: {risk_amount:.2f}" if risk_amount is not None else ""
        max_str = f" | MaxLoss: {max_loss:.2f}" if max_loss is not None else ""
        
        logger.info(f"[PIPELINE 4/5 RISK] {symbol}: {action}{ps_str}{risk_str}{max_str}")
        for key, value in details.items():
            logger.debug(f"  - {key}: {value}")
    
    @staticmethod
    def log_order_execution(symbol: str, order_type: str, quantity: float, price: float = None, 
                           sl: float = None, tp: float = None, status: str = "SENT", **details):
        """
        Log: Ejecución de orden
        
        Args:
            symbol: Símbolo
            order_type: Tipo de orden (BUY, SELL, CLOSE)
            quantity: Cantidad a operar
            price: Precio de entrada
            sl: Stop Loss
            tp: Take Profit
            status: Estado de la orden (SENT, CONFIRMED, FAILED)
            **details: Detalles adicionales (ID de orden, etc)
        """
        price_str = f" | Price: {price:.5f}" if price is not None else ""
        sl_str = f" | SL: {sl:.5f}" if sl is not None else ""
        tp_str = f" | TP: {tp:.5f}" if tp is not None else ""
        
        logger.info(f"[PIPELINE 5/5 EXECUTE] {order_type} {quantity:.4f} {symbol} @ {price_str}{sl_str}{tp_str} | {status}")
        for key, value in details.items():
            logger.debug(f"  - {key}: {value}")
    
    @staticmethod
    def log_cycle_summary(cycle_num: int, strategies_processed: int, signals_generated: int = 0,
                         orders_sent: int = 0, active_positions: int = 0, duration_ms: float = None):
        """
        Log: Resumen de ciclo
        
        Args:
            cycle_num: Número del ciclo
            strategies_processed: Estrategias procesadas
            signals_generated: Señales generadas
            orders_sent: Órdenes enviadas
            active_positions: Posiciones activas
            duration_ms: Duración del ciclo en ms
        """
        duration_str = f" | Duration: {duration_ms:.0f}ms" if duration_ms is not None else ""
        logger.info(f"[CYCLE #{cycle_num}] Procesadas: {strategies_processed} | Señales: {signals_generated} | "
                   f"Órdenes: {orders_sent} | Activas: {active_positions}{duration_str}")
    
    @staticmethod
    def log_error_in_pipeline(step: str, error: str, symbol: str = None, recovery_action: str = None):
        """
        Log: Error en el pipeline
        
        Args:
            step: Paso del pipeline donde ocurrió el error
            error: Descripción del error
            symbol: Símbolo involucrado (si aplica)
            recovery_action: Acción de recuperación ejecutada
        """
        symbol_str = f" [{symbol}]" if symbol else ""
        recovery_str = f" | Acción: {recovery_action}" if recovery_action else ""
        logger.error(f"[PIPELINE ERROR {step}]{symbol_str}: {error}{recovery_str}")


# Funciones de conveniencia para logging de componentes específicos
def log_mt5_data_sync(symbol: str, bars_synced: int, cache_hit: bool, age_ms: float = None):
    """Log de sincronización de datos MT5."""
    cache_str = "CACHE HIT" if cache_hit else "FRESH"
    age_str = f" | Age: {age_ms:.0f}ms" if age_ms is not None else ""
    logger.info(f"[MT5 DATA] {symbol}: {bars_synced} barras | {cache_str}{age_str}")


def log_indicator_clean(symbol: str, rows_before: int, rows_after: int, nan_removed: int):
    """Log de limpieza de datos con NaN."""
    pct = (nan_removed / rows_before * 100) if rows_before > 0 else 0
    logger.info(f"[INDICATOR CLEAN] {symbol}: {rows_before} → {rows_after} filas | NaN removido: {nan_removed} ({pct:.1f}%)")


def log_capital_check(balance: float, equity: float, drawdown_pct: float = None, max_drawdown_limit: float = None):
    """Log de revisión de capital."""
    dd_str = f" | Drawdown: {drawdown_pct:.2f}%" if drawdown_pct is not None else ""
    limit_str = f" | Limit: {max_drawdown_limit:.2f}%" if max_drawdown_limit is not None else ""
    logger.info(f"[CAPITAL] Balance: {balance:.2f} USD | Equity: {equity:.2f} USD{dd_str}{limit_str}")


def log_position_update(symbol: str, quantity: float, entry_price: float, unrealized_pnl: float = None,
                       status: str = "OPEN"):
    """Log de actualización de posición."""
    pnl_str = f" | PnL: {unrealized_pnl:+.2f}" if unrealized_pnl is not None else ""
    logger.info(f"[POSITION {status}] {symbol}: {quantity:.4f} @ {entry_price:.5f}{pnl_str}")


def log_sl_tp_validation(symbol: str, order_type: str, price: float, sl: float, tp: float,
                        is_valid: bool, reason: str = None):
    """Log de validación de SL/TP."""
    valid_str = "✅ PASSED" if is_valid else "❌ FAILED"
    reason_str = f" | {reason}" if reason else ""
    logger.info(f"[SL/TP VALIDATION] {order_type} {symbol}: {valid_str}{reason_str} | Price:{price:.5f} SL:{sl:.5f} TP:{tp:.5f}")
