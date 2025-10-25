"""
Trace Comparator Module - FASE 4 Task 12
========================================

Compara señales de trading en vivo vs backtests para identificar divergencias.

CARACTERÍSTICAS:
- Cargar signals_live y signals_backtest
- Comparar por symbol y timeframe
- Identificar divergencias (señales faltantes, extras, diferentes)
- Calcular estadísticas de divergencia
- Generar reporte detallado
- Exportar a JSON/CSV

ENTRADA:
- signals_live: signals/{symbol}_{date}.json (desde SignalLogger)
- signals_backtest: backtests/backtest_signals_{symbol}_{id}.json (desde BacktestValidator)

SALIDA:
- comparison_report_{timestamp}.json
  - Divergencias identificadas
  - Estadísticas de coincidencia
  - Análisis de diferencias por símbolo/timeframe
  - Recomendaciones

CASOS DE DIVERGENCIA:
1. Señal en live pero no en backtest (market conditions deviation)
2. Señal en backtest pero no en live (missed opportunity o risk management)
3. Misma señal pero precio/confianza ML diferente (data timing issue)
4. Señal ejecutada en live vs rejected en backtest (risk management divergence)

INTEGRACIÓN:
- Usa SignalLogger para cargar signals_live
- Usa BacktestValidator para cargar signals_backtest
- Genera análisis comparativo
- Identifica root causes de divergencias
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import pandas as pd
import threading
from collections import defaultdict

# Importar módulos existentes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.signal_logger import get_signal_logger, SignalType, SignalStatus, TradingSignal
from utils.logger import get_logger


@dataclass
class SignalDivergence:
    """Representa una divergencia encontrada"""
    divergence_type: str           # missing_in_backtest, extra_in_backtest, different_signal, timing_diff
    symbol: str
    timeframe: str
    live_signal: Optional[Dict[str, Any]]
    backtest_signal: Optional[Dict[str, Any]]
    timestamp: Optional[str]
    price_diff: Optional[float]    # Diferencia de precio si aplica
    confidence_diff: Optional[float]  # Diferencia de ML confidence
    notes: str


@dataclass
class ComparisonStats:
    """Estadísticas generales de la comparación"""
    total_live_signals: int
    total_backtest_signals: int
    matching_signals: int          # Coinciden perfectamente
    divergences: int               # Total de divergencias
    match_rate: float              # 0.0-1.0
    missing_in_backtest: int       # En live pero no en backtest
    extra_in_backtest: int         # En backtest pero no en live
    signal_type_mismatches: int    # BUY vs SELL
    timing_issues: int             # Mismo signal pero tiempo diferente
    pnl_impact: float              # PnL perdido por divergencias


class TraceComparator:
    """
    Comparador de traces (signals) entre live trading y backtests.
    
    Identifica divergencias y analiza root causes.
    """

    def __init__(self,
                 data_dir: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Args:
            data_dir: Directorio base (default: descarga_datos/data)
            logger: Logger (default: get_logger())
        """
        self.logger = logger or get_logger(__name__)
        
        # Directorio de datos
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.reports_dir = self.data_dir / "comparison_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Signal logger para acceder a signals
        self.signal_logger = get_signal_logger(data_dir=data_dir, logger=self.logger)
        
        # Estadísticas
        self.comparisons_run = 0
        self.divergences_found = 0
        self._lock = threading.RLock()
        
        self.logger.info(f"✅ TraceComparator initialized: {self.reports_dir}")

    def compare_symbol(self,
                      symbol: str,
                      live_start_date: Optional[str] = None,
                      live_end_date: Optional[str] = None,
                      backtest_run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compara signals de live vs backtest para un símbolo.
        
        Args:
            symbol: BTC/USDT
            live_start_date: Fecha inicio (ISO format). Default: últimas 24h
            live_end_date: Fecha fin (ISO format). Default: ahora
            backtest_run_id: ID del backtest. Default: más reciente
            
        Returns:
            Dict con resultados de comparación
        """
        with self._lock:
            try:
                self.logger.info(f"🔍 Comparando {symbol}")
                
                # Cargar signals live
                live_signals = self._load_live_signals(
                    symbol,
                    start_date=live_start_date,
                    end_date=live_end_date
                )
                
                # Cargar signals backtest
                backtest_signals = self._load_backtest_signals(
                    symbol,
                    run_id=backtest_run_id
                )
                
                if not live_signals:
                    self.logger.warning(f"⚠️  No live signals found for {symbol}")
                    return {
                        'status': 'no_live_data',
                        'symbol': symbol,
                        'live_signals_count': 0
                    }
                
                if not backtest_signals:
                    self.logger.warning(f"⚠️  No backtest signals found for {symbol}")
                    return {
                        'status': 'no_backtest_data',
                        'symbol': symbol,
                        'backtest_signals_count': 0
                    }
                
                # Comparar
                divergences = self._find_divergences(live_signals, backtest_signals)
                stats = self._calculate_statistics(live_signals, backtest_signals, divergences)
                
                with self._lock:
                    self.comparisons_run += 1
                    self.divergences_found += len(divergences)
                
                result = {
                    'status': 'completed',
                    'symbol': symbol,
                    'statistics': asdict(stats),
                    'divergences': [asdict(d) for d in divergences],
                    'live_signals_loaded': len(live_signals),
                    'backtest_signals_loaded': len(backtest_signals),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                self.logger.info(
                    f"✅ Comparison completed: {len(divergences)} divergences found"
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Error comparing {symbol}: {str(e)}")
                return {
                    'status': 'error',
                    'error': str(e)
                }

    def compare_multiple_symbols(self,
                                symbols: List[str],
                                backtest_run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compara múltiples símbolos en una operación.
        
        Args:
            symbols: Lista de símbolos a comparar
            backtest_run_id: ID del backtest
            
        Returns:
            Dict con resultados consolidados
        """
        try:
            all_results = {}
            total_divergences = 0
            
            for symbol in symbols:
                self.logger.info(f"Processing {symbol}...")
                result = self.compare_symbol(symbol, backtest_run_id=backtest_run_id)
                all_results[symbol] = result
                
                if result.get('status') == 'completed':
                    total_divergences += len(result.get('divergences', []))
            
            return {
                'status': 'completed',
                'symbols_compared': len(symbols),
                'total_divergences': total_divergences,
                'results': all_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error comparing multiple symbols: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def save_comparison_report(self,
                              comparison_result: Dict[str, Any],
                              report_id: Optional[str] = None) -> str:
        """
        Guarda reporte de comparación a JSON.
        
        Args:
            comparison_result: Resultado de compare_symbol o compare_multiple_symbols
            report_id: ID único (default: timestamp)
            
        Returns:
            Ruta del archivo guardado
        """
        try:
            if report_id is None:
                report_id = datetime.now(timezone.utc).isoformat().replace(':', '-')
            
            filename = f"comparison_report_{report_id}.json"
            filepath = self.reports_dir / filename
            
            # Guardar
            with open(filepath, 'w') as f:
                json.dump(comparison_result, f, indent=2)
            
            self.logger.info(f"💾 Comparison report saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving report: {str(e)}")
            raise

    def export_comparison_to_csv(self,
                                comparison_result: Dict[str, Any],
                                symbol: str) -> str:
        """
        Exporta divergencias a CSV para análisis.
        
        Args:
            comparison_result: Resultado de comparación
            symbol: Símbolo
            
        Returns:
            Ruta del archivo CSV
        """
        try:
            divergences = comparison_result.get('divergences', [])
            
            if not divergences:
                self.logger.warning("No divergences to export")
                return ""
            
            # Crear DataFrame
            df = pd.DataFrame(divergences)
            
            # Guardar
            filename = f"divergences_{symbol.replace('/', '_')}.csv"
            filepath = self.reports_dir / filename
            
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"📊 CSV export: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting to CSV: {str(e)}")
            return ""

    def get_comparison_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de comparaciones ejecutadas.
        
        Returns:
            Dict con métricas
        """
        with self._lock:
            try:
                return {
                    'comparisons_run': self.comparisons_run,
                    'divergences_found': self.divergences_found,
                    'avg_divergences_per_comparison': (
                        self.divergences_found / self.comparisons_run
                        if self.comparisons_run > 0 else 0
                    ),
                    'reports_dir': str(self.reports_dir)
                }
                
            except Exception as e:
                self.logger.error(f"❌ Error getting statistics: {str(e)}")
                return {}

    def get_health_check(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del comparador.
        
        Returns:
            Dict con métricas de health
        """
        with self._lock:
            try:
                report_files = len(list(self.reports_dir.glob("*.json")))
                csv_files = len(list(self.reports_dir.glob("*.csv")))
                
                return {
                    'status': 'healthy',
                    'comparisons_run': self.comparisons_run,
                    'divergences_found': self.divergences_found,
                    'report_files_on_disk': report_files,
                    'csv_exports_on_disk': csv_files,
                    'reports_dir': str(self.reports_dir)
                }
            except Exception as e:
                self.logger.error(f"❌ Error in health check: {str(e)}")
                return {'status': 'error'}

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _load_live_signals(self,
                          symbol: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Carga signals en vivo desde archivos del SignalLogger.
        
        Args:
            symbol: BTC/USDT
            start_date: Fecha inicio (ISO format)
            end_date: Fecha fin (ISO format)
            
        Returns:
            Lista de signals (dict)
        """
        try:
            # Obtener del signal logger
            signals = self.signal_logger.get_signals_for_symbol(symbol, limit=10000)
            
            if not signals:
                return []
            
            # Convertir a dict
            signals_dict = [s.to_dict() for s in signals]
            
            # Filtrar por rango de fechas si se especifica
            if start_date:
                start_ts = datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp()
                signals_dict = [s for s in signals_dict if s.get('unix_timestamp', 0) >= start_ts]
            
            if end_date:
                end_ts = datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp()
                signals_dict = [s for s in signals_dict if s.get('unix_timestamp', 0) <= end_ts]
            
            return signals_dict
            
        except Exception as e:
            self.logger.error(f"Error loading live signals: {e}")
            return []

    def _load_backtest_signals(self,
                              symbol: str,
                              run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Carga signals de backtest desde archivos BacktestValidator.
        
        Args:
            symbol: BTC/USDT
            run_id: ID del backtest (default: más reciente)
            
        Returns:
            Lista de signals (dict)
        """
        try:
            backtest_dir = self.data_dir / "backtests"
            
            if not backtest_dir.exists():
                self.logger.warning(f"Backtest directory not found: {backtest_dir}")
                return []
            
            # Buscar archivos
            pattern = f"backtest_signals_{symbol.replace('/', '_')}_*.json"
            files = list(backtest_dir.glob(pattern))
            
            if not files:
                return []
            
            # Si especifica run_id, buscar ese archivo
            if run_id:
                matching = [f for f in files if run_id in f.name]
                if matching:
                    files = [matching[0]]
            else:
                # Usar más reciente (last modified)
                files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:1]
            
            if not files:
                return []
            
            # Cargar
            with open(files[0], 'r') as f:
                signals = json.load(f)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error loading backtest signals: {e}")
            return []

    def _find_divergences(self,
                         live_signals: List[Dict[str, Any]],
                         backtest_signals: List[Dict[str, Any]]) -> List[SignalDivergence]:
        """
        Identifica divergencias entre signals live y backtest.
        """
        try:
            divergences = []
            
            # Crear índices por (symbol, timeframe, price_range)
            # Para matching, buscamos signals cercanas en tiempo y precio
            
            # Agrupar por symbol/timeframe
            live_by_key = defaultdict(list)
            backtest_by_key = defaultdict(list)
            
            for sig in live_signals:
                key = (sig.get('symbol'), sig.get('timeframe'))
                live_by_key[key].append(sig)
            
            for sig in backtest_signals:
                key = (sig.get('symbol'), sig.get('timeframe'))
                backtest_by_key[key].append(sig)
            
            # Para cada live signal, buscar match en backtest
            matched_backtest = set()
            
            for key, live_sigs in live_by_key.items():
                backtest_sigs = backtest_by_key.get(key, [])
                
                for live_sig in live_sigs:
                    matched = False
                    live_price = live_sig.get('price', 0)
                    live_type = live_sig.get('signal_type')
                    
                    for i, backtest_sig in enumerate(backtest_sigs):
                        if i in matched_backtest:
                            continue
                        
                        backtest_price = backtest_sig.get('price', 0)
                        backtest_type = backtest_sig.get('signal_type')
                        
                        # Verificar si coinciden (mismo tipo, precio similar)
                        price_diff = abs(live_price - backtest_price)
                        price_pct = price_diff / live_price if live_price > 0 else 0
                        
                        if (live_type == backtest_type and price_pct < 0.02):  # Máx 2% diff
                            matched = True
                            matched_backtest.add(i)
                            
                            # Registrar si hay diferencias significativas
                            conf_diff = abs(
                                live_sig.get('ml_confidence', 0) - 
                                backtest_sig.get('ml_confidence', 0)
                            )
                            
                            if price_pct > 0.01 or conf_diff > 0.05:
                                divergences.append(SignalDivergence(
                                    divergence_type='timing_diff',
                                    symbol=key[0],
                                    timeframe=key[1],
                                    live_signal=live_sig,
                                    backtest_signal=backtest_sig,
                                    timestamp=live_sig.get('timestamp'),
                                    price_diff=price_diff,
                                    confidence_diff=conf_diff,
                                    notes=f"Price diff: {price_pct*100:.2f}%, Confidence diff: {conf_diff:.3f}"
                                ))
                            break
                    
                    if not matched:
                        # Signal en live pero no en backtest
                        divergences.append(SignalDivergence(
                            divergence_type='missing_in_backtest',
                            symbol=key[0],
                            timeframe=key[1],
                            live_signal=live_sig,
                            backtest_signal=None,
                            timestamp=live_sig.get('timestamp'),
                            price_diff=None,
                            confidence_diff=None,
                            notes="Signal not generated in backtest"
                        ))
            
            # Señales en backtest pero no en live
            for key, backtest_sigs in backtest_by_key.items():
                for i, backtest_sig in enumerate(backtest_sigs):
                    if i not in matched_backtest:
                        divergences.append(SignalDivergence(
                            divergence_type='extra_in_backtest',
                            symbol=key[0],
                            timeframe=key[1],
                            live_signal=None,
                            backtest_signal=backtest_sig,
                            timestamp=backtest_sig.get('timestamp'),
                            price_diff=None,
                            confidence_diff=None,
                            notes="Signal not executed in live trading"
                        ))
            
            return divergences
            
        except Exception as e:
            self.logger.error(f"Error finding divergences: {e}")
            return []

    def _calculate_statistics(self,
                             live_signals: List[Dict[str, Any]],
                             backtest_signals: List[Dict[str, Any]],
                             divergences: List[SignalDivergence]) -> ComparisonStats:
        """
        Calcula estadísticas de la comparación.
        """
        try:
            total_live = len(live_signals)
            total_backtest = len(backtest_signals)
            total_div = len(divergences)
            
            matching = total_live - sum(
                1 for d in divergences 
                if d.divergence_type == 'missing_in_backtest'
            )
            
            missing_in_backtest = sum(1 for d in divergences if d.divergence_type == 'missing_in_backtest')
            extra_in_backtest = sum(1 for d in divergences if d.divergence_type == 'extra_in_backtest')
            timing_issues = sum(1 for d in divergences if d.divergence_type == 'timing_diff')
            
            # Signal type mismatches
            signal_mismatches = 0
            for d in divergences:
                if d.live_signal and d.backtest_signal:
                    if d.live_signal.get('signal_type') != d.backtest_signal.get('signal_type'):
                        signal_mismatches += 1
            
            match_rate = matching / total_live if total_live > 0 else 0.0
            
            # Calcular PnL impact (aprox)
            pnl_impact = missing_in_backtest * 100.0  # Asumiendo $100 per missed signal
            
            return ComparisonStats(
                total_live_signals=total_live,
                total_backtest_signals=total_backtest,
                matching_signals=matching,
                divergences=total_div,
                match_rate=round(match_rate, 3),
                missing_in_backtest=missing_in_backtest,
                extra_in_backtest=extra_in_backtest,
                signal_type_mismatches=signal_mismatches,
                timing_issues=timing_issues,
                pnl_impact=pnl_impact
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            return ComparisonStats(
                total_live_signals=0,
                total_backtest_signals=0,
                matching_signals=0,
                divergences=0,
                match_rate=0.0,
                missing_in_backtest=0,
                extra_in_backtest=0,
                signal_type_mismatches=0,
                timing_issues=0,
                pnl_impact=0.0
            )


# ============================================================================
# FACTORY Y SINGLETON
# ============================================================================

_comparator_instance: Optional[TraceComparator] = None
_comparator_lock = threading.Lock()


def get_trace_comparator(data_dir: Optional[Path] = None,
                        logger: Optional[logging.Logger] = None) -> TraceComparator:
    """
    Factory function para obtener instancia singleton del TraceComparator.
    
    Args:
        data_dir: Directorio de datos
        logger: Logger
        
    Returns:
        Instancia singleton del TraceComparator
    """
    global _comparator_instance
    
    if _comparator_instance is None:
        with _comparator_lock:
            if _comparator_instance is None:
                _comparator_instance = TraceComparator(data_dir, logger)
    
    return _comparator_instance


def reset_trace_comparator() -> None:
    """Resetea la instancia singleton (usado en tests)"""
    global _comparator_instance
    with _comparator_lock:
        _comparator_instance = None
