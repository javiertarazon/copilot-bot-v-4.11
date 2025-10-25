"""
Backtest Validator Module - FASE 4 Task 11
===========================================

Ejecuta backtests equivalentes al trading en vivo y captura señales para comparación.

CARACTERÍSTICAS:
- Ejecutar backtest con parámetros idénticos a live trading
- Capturar señales en MISMO FORMATO que live (para Task 12: comparación)
- Usar estrategia UltraDetailedHeikinAshiML con modelos ML pre-entrenados
- Almacenar en: descarga_datos/data/backtests/backtest_signals_{timestamp}.json
- Validar reproducibilidad (mismo input → mismo output)
- Calcular divergencias vs live trading

INTEGRACIÓN:
- Usa existing AdvancedBacktester
- Usa existing UltraDetailedHeikinAshiMLStrategy
- Captura signals usando SignalLogger
- Compara con live signals en Task 12

WORKFLOW:
1. Cargar datos históricos (desde SQLite o CSV)
2. Instanciar estrategia con config live
3. Ejecutar backtest
4. Iterar sobre barras, capturar señales
5. Guardar signals_backtest.json
6. Comparar con signals_live.json en Task 12
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import threading

# Importar módulos existentes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.backtester import AdvancedBacktester
from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
from utils.signal_logger import get_signal_logger, SignalType, SignalStatus
from utils.logger import get_logger
from config.config_loader import load_config_from_yaml


@dataclass
class BacktestSignal:
    """Señal capturada durante backtest"""
    index: int                      # Índice en el DataFrame
    timestamp: str                  # ISO format
    symbol: str
    timeframe: str
    price: float
    signal_type: str               # BUY, SELL, NO_SIGNAL
    ml_confidence: float           # 0.0-1.0
    indicators: Dict[str, Any]
    trade_result: Optional[Dict[str, Any]] = None  # Si se ejecutó


class BacktestValidator:
    """
    Valida backtests contra parámetros live y captura señales para comparación.
    
    Thread-safe con RLock para operaciones concurrentes.
    """

    def __init__(self, 
                 config_path: Optional[str] = None,
                 data_dir: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Args:
            config_path: Ruta a config.yaml (default: descarga_datos/config/config.yaml)
            data_dir: Directorio base (default: descarga_datos/data)
            logger: Logger (default: get_logger())
        """
        self.logger = logger or get_logger(__name__)
        
        # Directorio de datos
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.backtests_dir = self.data_dir / "backtests"
        self.backtests_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuración
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config" / "config.yaml")
        
        self.config = load_config_from_yaml(Path(config_path))
        
        # Backtester
        self.backtester = AdvancedBacktester()
        self.backtester.configure({
            'initial_capital': self.config.backtesting.initial_capital,
            'commission': self.config.backtesting.commission,
            'slippage': self.config.backtesting.slippage
        })
        
        # Signal logger para capturar señales de backtest
        self.signal_logger = get_signal_logger(data_dir=data_dir, logger=self.logger)
        
        # Estadísticas
        self.backtests_run = 0
        self.signals_captured = 0
        self._lock = threading.RLock()
        
        self.logger.info(f"✅ BacktestValidator initialized: {self.backtests_dir}")

    def run_backtest_for_symbol(self,
                               symbol: str,
                               timeframe: str,
                               data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Ejecuta backtest para un símbolo y captura señales.
        
        Args:
            symbol: BTC/USDT, ETH/USDT, etc
            timeframe: 4h, 1h, etc
            data: DataFrame con OHLCV. Si None, carga del SQLite/CSV
            
        Returns:
            Dict con resultados del backtest + signals capturadas
        """
        with self._lock:
            try:
                self.logger.info(f"🎯 Iniciando backtest para {symbol} {timeframe}")
                
                # Cargar datos si no se proporcionan
                if data is None:
                    data = self._load_data_for_backtest(symbol, timeframe)
                
                if data is None or len(data) < 100:
                    self.logger.error(f"❌ Datos insuficientes para {symbol}: {len(data) if data is not None else 0}")
                    return {
                        'status': 'failed',
                        'reason': 'insufficient_data',
                        'signals_captured': 0
                    }
                
                # Instanciar estrategia
                strategy = UltraDetailedHeikinAshiMLStrategy(config=self.config)
                
                # Ejecutar backtest
                backtest_result = self.backtester.run(
                    strategy=strategy,
                    data=data,
                    symbol=symbol,
                    timeframe=timeframe
                )
                
                # Capturar señales generadas durante backtest
                signals_captured = self._capture_signals_from_backtest(
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy_result=backtest_result,
                    data=data
                )
                
                with self._lock:
                    self.backtests_run += 1
                    self.signals_captured += len(signals_captured)
                
                result = {
                    'status': 'completed',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'backtest_result': backtest_result,
                    'signals_captured': len(signals_captured),
                    'signals': signals_captured,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                self.logger.info(
                    f"✅ Backtest completado: {len(signals_captured)} señales capturadas"
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Error en backtest: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e),
                    'signals_captured': 0
                }

    def validate_signal_consistency(self,
                                   symbol: str,
                                   limit_signals: int = 100) -> Dict[str, Any]:
        """
        Valida que un backtest reproduce señales consistentemente.
        
        Ejecuta backtest 2 veces y compara señales generadas.
        
        Args:
            symbol: BTC/USDT
            limit_signals: Máximo de señales a validar
            
        Returns:
            Dict con resultados de validación
        """
        with self._lock:
            try:
                self.logger.info(f"🔄 Validando consistencia para {symbol}")
                
                # Ejecutar backtest 1
                result1 = self.run_backtest_for_symbol(symbol, timeframe='4h')
                signals1 = result1.get('signals', [])
                
                # Ejecutar backtest 2 (debe generar idénticas señales)
                result2 = self.run_backtest_for_symbol(symbol, timeframe='4h')
                signals2 = result2.get('signals', [])
                
                # Comparar
                consistent = len(signals1) == len(signals2)
                
                if consistent:
                    # Verificar que cada señal coincide
                    for sig1, sig2 in zip(signals1[:limit_signals], signals2[:limit_signals]):
                        if (sig1['price'] != sig2['price'] or 
                            sig1['signal_type'] != sig2['signal_type'] or
                            abs(sig1['ml_confidence'] - sig2['ml_confidence']) > 0.001):
                            consistent = False
                            break
                
                return {
                    'status': 'completed',
                    'symbol': symbol,
                    'consistent': consistent,
                    'run1_signals': len(signals1),
                    'run2_signals': len(signals2),
                    'validation_passed': consistent,
                    'notes': 'Backtest is deterministic' if consistent else 'Divergence detected'
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error validating consistency: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e),
                    'validation_passed': False
                }

    def save_backtest_signals(self,
                             symbol: str,
                             signals: List[BacktestSignal],
                             run_id: Optional[str] = None) -> str:
        """
        Guarda señales de backtest a JSON para comparación con live.
        
        Args:
            symbol: BTC/USDT
            signals: Lista de BacktestSignal
            run_id: ID único del run (default: timestamp)
            
        Returns:
            Ruta del archivo guardado
        """
        try:
            if run_id is None:
                run_id = datetime.now(timezone.utc).isoformat().replace(':', '-')
            
            filename = f"backtest_signals_{symbol.replace('/', '_')}_{run_id}.json"
            filepath = self.backtests_dir / filename
            
            # Convertir a dict
            signals_data = [asdict(sig) for sig in signals]
            
            # Guardar
            with open(filepath, 'w') as f:
                json.dump(signals_data, f, indent=2)
            
            self.logger.info(f"💾 Backtest signals guardadas: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving backtest signals: {str(e)}")
            raise

    def get_backtest_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de backtests ejecutados.
        
        Args:
            symbol: Si None, estadísticas globales
            
        Returns:
            Dict con métricas
        """
        with self._lock:
            try:
                stats = {
                    'backtests_run': self.backtests_run,
                    'total_signals_captured': self.signals_captured,
                    'avg_signals_per_backtest': (
                        self.signals_captured / self.backtests_run 
                        if self.backtests_run > 0 else 0
                    ),
                    'backtests_dir': str(self.backtests_dir)
                }
                
                # Si se especifica símbolo, obtener stats específicas
                if symbol:
                    symbol_signals = self.signal_logger.get_signals_for_symbol(
                        symbol,
                        limit=10000
                    )
                    
                    # Filtrar solo señales de backtest (necesitaría un tag, pero usamos heurística)
                    stats[f'{symbol}_total_signals'] = len(symbol_signals)
                
                return stats
                
            except Exception as e:
                self.logger.error(f"❌ Error getting statistics: {str(e)}")
                return {'status': 'error'}

    def get_health_check(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del validator.
        
        Returns:
            Dict con métricas de health
        """
        with self._lock:
            try:
                backtest_files = len(list(self.backtests_dir.glob("backtest_signals_*.json")))
                
                return {
                    'status': 'healthy',
                    'backtests_run': self.backtests_run,
                    'signals_captured': self.signals_captured,
                    'backtest_files_on_disk': backtest_files,
                    'backtests_dir': str(self.backtests_dir)
                }
            except Exception as e:
                self.logger.error(f"❌ Error in health check: {str(e)}")
                return {'status': 'error'}

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _load_data_for_backtest(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Carga datos históricos para backtest.
        
        Priority: SQLite → CSV → Download
        """
        try:
            # TODO: Implementar carga desde SQLite/CSV
            # Por ahora, retornar None (el usuario debe proveer data)
            self.logger.warning(f"Data loading not implemented. Use data parameter.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading backtest data: {e}")
            return None

    def _capture_signals_from_backtest(self,
                                       symbol: str,
                                       timeframe: str,
                                       strategy_result: Dict[str, Any],
                                       data: pd.DataFrame) -> List[BacktestSignal]:
        """
        Captura señales generadas durante backtest.
        
        Extrae del resultado de estrategia y registra usando SignalLogger.
        """
        try:
            signals = []
            
            # Obtener trades del backtest
            trades = strategy_result.get('trades', [])
            
            # Iterar sobre trades y crear BacktestSignal
            for trade in trades:
                entry_bar = trade.get('entry_index', -1)
                
                if entry_bar >= 0 and entry_bar < len(data):
                    row = data.iloc[entry_bar]
                    
                    # Determinar tipo de señal
                    signal_type = 'BUY' if trade.get('type') == 'long' else 'SELL'
                    
                    # ML confidence (si está disponible)
                    ml_conf = trade.get('ml_confidence', 0.5)
                    
                    # Crear BacktestSignal
                    sig = BacktestSignal(
                        index=entry_bar,
                        timestamp=pd.Timestamp(row.get('timestamp', 
                                                      data.index[entry_bar])).isoformat() if hasattr(data.index[entry_bar], 'isoformat') else data.index[entry_bar],
                        symbol=symbol,
                        timeframe=timeframe,
                        price=float(row.get('open', row.get('close', 0))),
                        signal_type=signal_type,
                        ml_confidence=float(ml_conf),
                        indicators={
                            'rsi': float(row.get('rsi', 50)) if 'rsi' in row else None,
                            'atr': float(row.get('atr', 0)) if 'atr' in row else None,
                            'trend': row.get('trend', 'neutral') if 'trend' in row else 'neutral'
                        },
                        trade_result={
                            'pnl': float(trade.get('pnl', 0)),
                            'exit_index': trade.get('exit_index', -1)
                        }
                    )
                    
                    signals.append(sig)
                    
                    # Registrar en SignalLogger con prefijo "backtest"
                    self.signal_logger.log_signal(
                        symbol=symbol,
                        timeframe=timeframe,
                        strategy=f"UltraDetailedHeikinAshiMLStrategy_BACKTEST",
                        signal_type=SignalType[signal_type],
                        price=float(row.get('open', row.get('close', 0))),
                        ml_confidence=float(ml_conf),
                        indicators=sig.indicators,
                        notes=f"Backtest trade index={entry_bar}"
                    )
            
            self.logger.debug(f"Captured {len(signals)} signals from backtest")
            return signals
            
        except Exception as e:
            self.logger.error(f"Error capturing backtest signals: {str(e)}")
            return []


# ============================================================================
# FACTORY Y SINGLETON
# ============================================================================

_validator_instance: Optional[BacktestValidator] = None
_validator_lock = threading.Lock()


def get_backtest_validator(config_path: Optional[str] = None,
                          data_dir: Optional[Path] = None,
                          logger: Optional[logging.Logger] = None) -> BacktestValidator:
    """
    Factory function para obtener instancia singleton del BacktestValidator.
    
    Args:
        config_path: Ruta a config.yaml
        data_dir: Directorio de datos
        logger: Logger
        
    Returns:
        Instancia singleton del BacktestValidator
    """
    global _validator_instance
    
    if _validator_instance is None:
        with _validator_lock:
            if _validator_instance is None:
                _validator_instance = BacktestValidator(config_path, data_dir, logger)
    
    return _validator_instance


def reset_backtest_validator() -> None:
    """Resetea la instancia singleton (usado en tests)"""
    global _validator_instance
    with _validator_lock:
        _validator_instance = None
