"""
FASE 5: Task 13 - Divergence Analyzer
Extrae patrones de divergencias y genera recomendaciones de ajuste de filtros.

Analiza reportes del Trace Comparator para identificar:
1. Señales faltantes en backtest (missed opportunities)
2. Señales extras en backtest (over-trading)
3. Diferencias de timing (slippage/latencia)
4. Mismatches de tipo de señal (estrategia divergence)

Genera recomendaciones automáticas para ajustar:
- ML confidence minimums
- RSI ranges
- ATR ratios
- Volume filters
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class DivergencePattern:
    """Patrón identificado en divergencias."""
    pattern_type: str  # missing_in_backtest, extra_in_backtest, timing_diff, type_mismatch
    frequency: int
    avg_impact_pnl: float
    symbols_affected: List[str] = field(default_factory=list)
    avg_price_diff: float = 0.0
    avg_timing_diff_ms: int = 0
    root_causes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FilterRecommendation:
    """Recomendación de ajuste de filtro."""
    filter_name: str
    current_value: float
    recommended_value: float
    reason: str
    impact_estimate: float  # Porcentaje esperado de mejora
    confidence: float  # 0.0 a 1.0
    test_results: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DivergenceReport:
    """Reporte consolidado de análisis de divergencias."""
    timestamp: str
    analysis_period: str  # "2024-10-24" or "2024-10-20 to 2024-10-24"
    total_signals_analyzed: int
    total_divergences: int
    divergence_rate: float  # 0.0 a 1.0
    patterns: List[DivergencePattern] = field(default_factory=list)
    recommendations: List[FilterRecommendation] = field(default_factory=list)
    symbol_analysis: Dict[str, Dict] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['patterns'] = [p.to_dict() for p in self.patterns]
        result['recommendations'] = [r.to_dict() for r in self.recommendations]
        return result


class DivergenceAnalyzer:
    """Analiza divergencias y genera recomendaciones de ajuste."""
    
    def __init__(self, reports_dir: Optional[Path] = None):
        """
        Inicializa el analizador.
        
        Args:
            reports_dir: Directorio donde están guardados los reportes de Trace Comparator
        """
        if reports_dir is None:
            reports_dir = Path(__file__).parent.parent / "data" / "comparison_reports"
        
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.output_dir = Path(__file__).parent.parent / "data" / "divergence_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DivergenceAnalyzer initialized: reports_dir={self.reports_dir}")
    
    def load_comparison_reports(self, days_old: int = 7) -> List[Dict]:
        """
        Carga reportes de comparación de los últimos N días.
        
        Args:
            days_old: Número de días hacia atrás a buscar
            
        Returns:
            Lista de reportes cargados
        """
        if not self.reports_dir.exists():
            logger.warning(f"Reports directory does not exist: {self.reports_dir}")
            return []
        
        reports = []
        cutoff_time = (datetime.now(timezone.utc) - timedelta(days=days_old)).timestamp()
        
        for report_file in self.reports_dir.glob("comparison_report_*.json"):
            try:
                file_mtime = report_file.stat().st_mtime
                if file_mtime >= cutoff_time:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                        reports.append(report_data)
                        logger.debug(f"Loaded report: {report_file.name}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading report {report_file}: {e}")
        
        logger.info(f"Loaded {len(reports)} reports from last {days_old} days")
        return reports
    
    def analyze_divergences(self, reports: List[Dict]) -> DivergenceReport:
        """
        Analiza reportes y genera patrones de divergencias.
        
        Args:
            reports: Lista de reportes del Trace Comparator
            
        Returns:
            DivergenceReport con análisis consolidado
        """
        divergence_count = defaultdict(int)
        symbol_divergences = defaultdict(lambda: defaultdict(list))
        pnl_impacts = defaultdict(list)
        price_diffs = defaultdict(list)
        timing_diffs = defaultdict(list)
        
        total_signals = 0
        total_divergences = 0
        
        # Procesar cada reporte
        for report in reports:
            if 'symbol_analysis' not in report:
                continue
            
            for symbol, sym_data in report['symbol_analysis'].items():
                # Extraer total de señales
                if 'total_signals' in sym_data:
                    total_signals += sym_data.get('total_signals', 0)
                
                # Extraer divergencias
                if 'divergences' in sym_data:
                    for div in sym_data['divergences']:
                        div_type = div.get('divergence_type', 'unknown')
                        divergence_count[div_type] += 1
                        total_divergences += 1
                        
                        symbol_divergences[symbol][div_type].append(div)
                        
                        # Extraer impacto PnL
                        if 'pnl_impact' in div:
                            pnl_impacts[div_type].append(div['pnl_impact'])
                        
                        # Extraer diferencia de precio
                        if 'price_difference' in div:
                            price_diffs[div_type].append(div['price_difference'])
                        
                        # Extraer diferencia de timing
                        if 'timing_diff_ms' in div:
                            timing_diffs[div_type].append(div['timing_diff_ms'])
        
        # Crear patrones
        patterns = []
        for div_type, count in divergence_count.items():
            avg_pnl = statistics.mean(pnl_impacts[div_type]) if pnl_impacts[div_type] else 0.0
            avg_price = statistics.mean(price_diffs[div_type]) if price_diffs[div_type] else 0.0
            avg_timing = int(statistics.mean(timing_diffs[div_type])) if timing_diffs[div_type] else 0
            
            symbols = list(set([s for s in symbol_divergences.keys() 
                              if div_type in symbol_divergences[s]]))
            
            pattern = DivergencePattern(
                pattern_type=div_type,
                frequency=count,
                avg_impact_pnl=avg_pnl,
                symbols_affected=symbols,
                avg_price_diff=avg_price,
                avg_timing_diff_ms=avg_timing,
                root_causes=self._identify_root_causes(div_type, avg_pnl, avg_price, avg_timing)
            )
            patterns.append(pattern)
        
        # Calcular tasa de divergencia
        divergence_rate = total_divergences / total_signals if total_signals > 0 else 0.0
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            patterns=patterns,
            divergence_rate=divergence_rate,
            symbol_analysis=dict(symbol_divergences)
        )
        
        # Análisis por símbolo
        symbol_analysis = self._analyze_by_symbol(symbol_divergences)
        
        report = DivergenceReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period=self._get_analysis_period(reports),
            total_signals_analyzed=total_signals,
            total_divergences=total_divergences,
            divergence_rate=divergence_rate,
            patterns=patterns,
            recommendations=recommendations,
            symbol_analysis=symbol_analysis
        )
        
        logger.info(f"Analysis complete: {total_divergences}/{total_signals} divergences "
                   f"({divergence_rate*100:.2f}%)")
        
        return report
    
    def _identify_root_causes(self, div_type: str, avg_pnl: float, 
                              avg_price: float, avg_timing: int) -> List[str]:
        """Identifica causas raíz potenciales de divergencias."""
        causes = []
        
        if div_type == "missing_in_backtest":
            if avg_price > 2.0:
                causes.append("ML confidence demasiado alta (señales fuertes perdidas)")
            if avg_timing > 1000:
                causes.append("Latencia live vs backtest (retraso en detección)")
            if avg_pnl > 100:
                causes.append("RSI range demasiado estricto (oportunidades perdidas)")
        
        elif div_type == "extra_in_backtest":
            if avg_price > 1.5:
                causes.append("ML confidence demasiado baja (falsos positivos en backtest)")
            if avg_pnl < -100:
                causes.append("Over-trading en backtest (filtros insuficientes)")
            causes.append("ATR ratio o volume filter más estricto needed")
        
        elif div_type == "timing_diff":
            if avg_timing > 2000:
                causes.append("Latencia de datos o procesamiento (>2s delay)")
            causes.append("Sincronización de timeframes entre live y backtest")
        
        elif div_type == "signal_type_mismatch":
            causes.append("Estrategia divergence (live vs backtest ejecutan diferente)")
            causes.append("Estado de indicadores inconsistente")
        
        return causes
    
    def _generate_recommendations(self, patterns: List[DivergencePattern],
                                  divergence_rate: float,
                                  symbol_analysis: Dict) -> List[FilterRecommendation]:
        """Genera recomendaciones de ajuste de filtros."""
        recommendations = []
        
        # Analizar cada patrón
        for pattern in patterns:
            if pattern.pattern_type == "missing_in_backtest":
                # Las señales se pierden en live → reducir ML confidence
                if pattern.frequency > 5:
                    rec = FilterRecommendation(
                        filter_name="ml_confidence_minimum",
                        current_value=0.75,
                        recommended_value=0.65,
                        reason=f"Reducir para capturar {pattern.frequency} señales perdidas",
                        impact_estimate=pattern.frequency / len(pattern.symbols_affected) if pattern.symbols_affected else 0,
                        confidence=0.85
                    )
                    recommendations.append(rec)
            
            elif pattern.pattern_type == "extra_in_backtest":
                # Hay más señales en backtest → aumentar filtros
                if pattern.frequency > 5:
                    rec = FilterRecommendation(
                        filter_name="atr_multiplier",
                        current_value=1.5,
                        recommended_value=1.8,
                        reason=f"Aumentar para filtrar {pattern.frequency} señales falsas",
                        impact_estimate=pattern.frequency / len(pattern.symbols_affected) if pattern.symbols_affected else 0,
                        confidence=0.80
                    )
                    recommendations.append(rec)
            
            elif pattern.pattern_type == "timing_diff":
                # Diferencias de timing → ajustar thresholds
                if pattern.avg_timing_diff_ms > 1000:
                    rec = FilterRecommendation(
                        filter_name="signal_delay_tolerance_ms",
                        current_value=500,
                        recommended_value=1500,
                        reason=f"Aumentar tolerancia por latencia ({pattern.avg_timing_diff_ms}ms promedio)",
                        impact_estimate=0.3,
                        confidence=0.75
                    )
                    recommendations.append(rec)
        
        # Ajustes globales basados en tasa de divergencia
        if divergence_rate > 0.20:
            rec = FilterRecommendation(
                filter_name="rsi_range_lower",
                current_value=30.0,
                recommended_value=35.0,
                reason=f"Tasa de divergencia alta ({divergence_rate*100:.1f}%) - endurecerer filtros",
                impact_estimate=0.15,
                confidence=0.70
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _analyze_by_symbol(self, symbol_divergences: Dict) -> Dict[str, Dict]:
        """Analiza divergencias por símbolo."""
        result = {}
        
        for symbol, div_dict in symbol_divergences.items():
            total = sum(len(v) for v in div_dict.values())
            result[symbol] = {
                'total_divergences': total,
                'by_type': {k: len(v) for k, v in div_dict.items()},
                'critical_issues': len([v for div_list in div_dict.values() 
                                       for v in div_list if abs(v.get('pnl_impact', 0)) > 200])
            }
        
        return result
    
    def _get_analysis_period(self, reports: List[Dict]) -> str:
        """Extrae período de análisis de los reportes."""
        if not reports:
            return "N/A"
        
        # Intentar extraer timestamps
        timestamps = []
        for report in reports:
            if 'timestamp' in report:
                try:
                    ts = datetime.fromisoformat(report['timestamp'])
                    timestamps.append(ts)
                except (ValueError, TypeError):
                    pass
        
        if len(timestamps) >= 2:
            timestamps.sort()
            start = timestamps[0].strftime("%Y-%m-%d")
            end = timestamps[-1].strftime("%Y-%m-%d")
            return f"{start} to {end}" if start != end else start
        elif timestamps:
            return timestamps[0].strftime("%Y-%m-%d")
        
        return "N/A"
    
    def save_report(self, report: DivergenceReport, filename: Optional[str] = None) -> Path:
        """
        Guarda reporte de análisis en JSON.
        
        Args:
            report: DivergenceReport a guardar
            filename: Nombre personalizado (opcional)
            
        Returns:
            Path del archivo guardado
        """
        if filename is None:
            filename = f"divergence_analysis_{datetime.now(timezone.utc).isoformat().replace(':', '-')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"Report saved: {filepath}")
        return filepath
    
    def export_recommendations_to_yaml(self, report: DivergenceReport, 
                                       filename: Optional[str] = None) -> Path:
        """
        Exporta recomendaciones en formato YAML para editar config.yaml.
        
        Args:
            report: DivergenceReport con recomendaciones
            filename: Nombre personalizado (opcional)
            
        Returns:
            Path del archivo generado
        """
        if filename is None:
            filename = f"recommended_filters_{datetime.now(timezone.utc).isoformat().replace(':', '-')}.yaml"
        
        filepath = self.output_dir / filename
        
        content = "# RECOMENDACIONES DE AJUSTE - FASE 5\n"
        content += f"# Generado: {datetime.now(timezone.utc).isoformat()}\n"
        content += "# Aplicar estos cambios a descarga_datos/config/config.yaml\n\n"
        
        content += "# Cambios recomendados:\n"
        for rec in report.recommendations:
            content += f"\n# {rec.filter_name}\n"
            content += f"#   Cambio: {rec.current_value} → {rec.recommended_value}\n"
            content += f"#   Razón: {rec.reason}\n"
            content += f"#   Confianza: {rec.confidence*100:.0f}%\n"
            content += f"#   {rec.filter_name}: {rec.recommended_value}\n"
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"Recommendations exported: {filepath}")
        return filepath
    
    def get_summary(self, report: DivergenceReport) -> str:
        """Genera resumen textual del análisis."""
        summary = f"""
ANÁLISIS DE DIVERGENCIAS - RESUMEN
==================================

Período: {report.analysis_period}
Timestamp: {report.timestamp}

ESTADÍSTICAS GENERALES
---------------------
Total de señales analizadas: {report.total_signals_analyzed:,}
Total de divergencias: {report.total_divergences:,}
Tasa de divergencia: {report.divergence_rate*100:.2f}%

PATRONES IDENTIFICADOS
---------------------
"""
        for pattern in report.patterns:
            summary += f"""
{pattern.pattern_type.upper()}
  Frecuencia: {pattern.frequency}
  Símbolos afectados: {', '.join(pattern.symbols_affected[:3]) if pattern.symbols_affected else 'N/A'}
  Impacto PnL promedio: ${pattern.avg_impact_pnl:.2f}
  Diferencia precio promedio: {pattern.avg_price_diff:.4f}%
  Diferencia timing: {pattern.avg_timing_diff_ms}ms
  Causas raíz:
"""
            for cause in pattern.root_causes:
                summary += f"    - {cause}\n"
        
        summary += f"""
RECOMENDACIONES ({len(report.recommendations)})
------------------
"""
        for i, rec in enumerate(report.recommendations, 1):
            summary += f"""
{i}. {rec.filter_name}
   Cambio: {rec.current_value} → {rec.recommended_value}
   Razón: {rec.reason}
   Confianza: {rec.confidence*100:.0f}%
"""
        
        summary += f"""
ANÁLISIS POR SÍMBOLO
------------------
"""
        for symbol, stats in report.symbol_analysis.items():
            by_type_str = ', '.join(f"{k}:{v}" for k, v in stats['by_type'].items())
            summary += f"{symbol}: {stats['total_divergences']} divergencias ({by_type_str})\n"
        
        return summary


# Singleton para acceso global
_divergence_analyzer: Optional[DivergenceAnalyzer] = None
_analyzer_lock = __import__('threading').RLock()


def get_divergence_analyzer(reports_dir: Optional[Path] = None) -> DivergenceAnalyzer:
    """Obtiene instancia singleton del DivergenceAnalyzer."""
    global _divergence_analyzer
    
    with _analyzer_lock:
        if _divergence_analyzer is None:
            _divergence_analyzer = DivergenceAnalyzer(reports_dir)
        return _divergence_analyzer
