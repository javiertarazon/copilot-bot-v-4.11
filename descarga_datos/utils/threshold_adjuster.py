"""
FASE 5: Task 14 - Threshold Adjuster
Aplica recomendaciones del DivergenceAnalyzer (Task 13) a través del config.yaml
y valida convergencia de señales live vs backtest.

Funcionalidades:
1. Parsea recomendaciones del análisis
2. Valida nuevos parámetros contra constraint rules
3. Actualiza config.yaml de forma segura (respaldo)
4. Ejecuta backtest con parámetros ajustados
5. Compara señales antes/después
6. Reporta ganancia/pérdida de convergencia
"""

import json
import logging
import yaml
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from copy import deepcopy
import shutil

logger = logging.getLogger(__name__)


@dataclass
class ParameterAdjustment:
    """Un ajuste de parámetro individual."""
    parameter_name: str
    old_value: float
    new_value: float
    reason: str
    confidence: float
    applied: bool = False
    validation_passed: bool = True
    validation_notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConvergenceMetrics:
    """Métricas de convergencia antes/después del ajuste."""
    timestamp: str
    period: str
    
    # Antes del ajuste
    divergence_rate_before: float
    total_divergences_before: int
    missing_in_backtest_before: int
    extra_in_backtest_before: int
    
    # Después del ajuste
    divergence_rate_after: Optional[float] = None
    total_divergences_after: Optional[int] = None
    missing_in_backtest_after: Optional[int] = None
    extra_in_backtest_after: Optional[int] = None
    
    # Cambio
    divergence_rate_improvement: Optional[float] = None
    divergences_reduction: Optional[int] = None
    convergence_achieved: bool = False
    
    def calculate_improvements(self):
        """Calcula mejoras automáticamente."""
        if self.divergence_rate_after is not None:
            self.divergence_rate_improvement = (
                self.divergence_rate_before - self.divergence_rate_after
            )
        if self.total_divergences_after is not None:
            self.divergences_reduction = (
                self.total_divergences_before - self.total_divergences_after
            )
            # Convergencia si divergencias_after < divergencias_before
            self.convergence_achieved = self.total_divergences_after < self.total_divergences_before
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AdjustmentReport:
    """Reporte consolidado de ajustes aplicados."""
    timestamp: str
    analysis_period: str
    adjustments: List[ParameterAdjustment] = field(default_factory=list)
    convergence_metrics: Optional[ConvergenceMetrics] = None
    validation_summary: Dict[str, Any] = field(default_factory=dict)
    config_backup_path: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['adjustments'] = [a.to_dict() for a in self.adjustments]
        if self.convergence_metrics:
            result['convergence_metrics'] = self.convergence_metrics.to_dict()
        return result


class ThresholdAdjuster:
    """Aplica y valida ajustes de parámetros."""
    
    # Restricciones de parámetros
    CONSTRAINTS = {
        'ml_confidence_minimum': (0.5, 0.95),      # Rango válido
        'ml_confidence_strong': (0.6, 0.99),
        'rsi_range_lower': (10.0, 50.0),
        'rsi_range_upper': (50.0, 90.0),
        'atr_multiplier': (0.5, 3.0),
        'volume_multiplier': (0.1, 5.0),
    }
    
    def __init__(self, config_path: Optional[Path] = None, 
                 output_dir: Optional[Path] = None):
        """
        Inicializa el ajustador de thresholds.
        
        Args:
            config_path: Path al config.yaml
            output_dir: Directorio para reportes y respaldos
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "data" / "threshold_adjustments"
        
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
        logger.info(f"ThresholdAdjuster initialized: config={self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga config.yaml."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def validate_parameter(self, param_name: str, value: float) -> Tuple[bool, str]:
        """
        Valida un parámetro contra constraints.
        
        Args:
            param_name: Nombre del parámetro
            value: Nuevo valor
            
        Returns:
            (is_valid, message)
        """
        if param_name not in self.CONSTRAINTS:
            return True, "Parameter not in constraints (unconstrained)"
        
        min_val, max_val = self.CONSTRAINTS[param_name]
        
        if value < min_val or value > max_val:
            msg = f"Value {value} outside valid range [{min_val}, {max_val}]"
            return False, msg
        
        return True, "Valid"
    
    def create_adjustments_from_recommendations(
        self, 
        recommendations: List[Dict]
    ) -> List[ParameterAdjustment]:
        """
        Convierte recomendaciones del DivergenceAnalyzer a ajustes.
        
        Args:
            recommendations: Lista de recomendaciones (dicts)
            
        Returns:
            Lista de ParameterAdjustment
        """
        adjustments = []
        
        for rec in recommendations:
            # Obtener valor actual del config
            param_name = rec.get('filter_name', '')
            current_value = self._get_current_parameter_value(param_name)
            
            adjustment = ParameterAdjustment(
                parameter_name=param_name,
                old_value=current_value or rec.get('current_value', 0.0),
                new_value=rec.get('recommended_value', 0.0),
                reason=rec.get('reason', ''),
                confidence=rec.get('confidence', 0.0)
            )
            
            # Validar
            is_valid, msg = self.validate_parameter(param_name, adjustment.new_value)
            adjustment.validation_passed = is_valid
            adjustment.validation_notes = msg
            
            adjustments.append(adjustment)
            logger.debug(f"Adjustment created: {adjustment.parameter_name} "
                        f"{adjustment.old_value} → {adjustment.new_value}")
        
        return adjustments
    
    def _get_current_parameter_value(self, param_name: str) -> Optional[float]:
        """Obtiene valor actual de un parámetro del config."""
        # Buscar en estrategia
        if 'strategies' in self.config:
            for strategy in self.config['strategies'].values():
                if param_name in strategy:
                    return float(strategy[param_name])
        
        # Buscar en nivel top
        if param_name in self.config:
            return float(self.config[param_name])
        
        return None
    
    def _set_parameter_in_config(self, param_name: str, value: float):
        """Establece valor de parámetro en config."""
        # Buscar en estrategia (como primera opción)
        if 'strategies' in self.config:
            for strategy in self.config['strategies'].values():
                if param_name in strategy:
                    strategy[param_name] = value
                    return
        
        # Establecer en nivel top
        self.config[param_name] = value
    
    def apply_adjustments(self, 
                         adjustments: List[ParameterAdjustment],
                         dry_run: bool = True) -> Tuple[bool, str]:
        """
        Aplica ajustes al config.yaml.
        
        Args:
            adjustments: Lista de ajustes a aplicar
            dry_run: Si True, solo simula sin guardar
            
        Returns:
            (success, message)
        """
        # Validar todos primero
        failed_validations = [a for a in adjustments if not a.validation_passed]
        if failed_validations:
            msg = f"Validation failed for {len(failed_validations)} parameters"
            logger.error(msg)
            return False, msg
        
        # Crear respaldo
        backup_path = self._create_backup()
        
        try:
            # Aplicar cambios
            for adjustment in adjustments:
                if adjustment.validation_passed:
                    self._set_parameter_in_config(
                        adjustment.parameter_name,
                        adjustment.new_value
                    )
                    adjustment.applied = True
            
            if not dry_run:
                # Guardar config
                with open(self.config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                logger.info(f"Config saved with {len(adjustments)} adjustments")
            else:
                logger.info(f"DRY RUN: Would apply {len(adjustments)} adjustments")
            
            return True, "Adjustments applied successfully"
        
        except Exception as e:
            logger.error(f"Error applying adjustments: {e}")
            # Restaurar respaldo
            if backup_path and not dry_run:
                self._restore_backup(backup_path)
            return False, str(e)
    
    def _create_backup(self) -> Optional[str]:
        """Crea respaldo del config actual."""
        try:
            timestamp = datetime.now(timezone.utc).isoformat().replace(':', '-')
            backup_path = self.output_dir / f"config_backup_{timestamp}.yaml"
            
            shutil.copy(self.config_path, backup_path)
            logger.info(f"Config backup created: {backup_path}")
            
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def _restore_backup(self, backup_path: str):
        """Restaura config desde respaldo."""
        try:
            shutil.copy(backup_path, self.config_path)
            logger.info(f"Config restored from backup: {backup_path}")
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
    
    def create_convergence_report(
        self,
        divergence_report_before: Dict,
        divergence_report_after: Optional[Dict] = None
    ) -> ConvergenceMetrics:
        """
        Crea reporte de convergencia.
        
        Args:
            divergence_report_before: Reporte antes del ajuste
            divergence_report_after: Reporte después (opcional)
            
        Returns:
            ConvergenceMetrics
        """
        # Extraer stats del reporte 'antes'
        total_divs_before = divergence_report_before.get('total_divergences', 0)
        total_signals_before = divergence_report_before.get('total_signals_analyzed', 1)
        div_rate_before = divergence_report_before.get('divergence_rate', 0.0)
        
        # Contar divergencias por tipo
        missing_before = 0
        extra_before = 0
        
        for pattern in divergence_report_before.get('patterns', []):
            if pattern.get('pattern_type') == 'missing_in_backtest':
                missing_before = pattern.get('frequency', 0)
            elif pattern.get('pattern_type') == 'extra_in_backtest':
                extra_before = pattern.get('frequency', 0)
        
        metrics = ConvergenceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            period="After adjustment",
            divergence_rate_before=div_rate_before,
            total_divergences_before=total_divs_before,
            missing_in_backtest_before=missing_before,
            extra_in_backtest_before=extra_before
        )
        
        # Si tenemos reporte después, añadir
        if divergence_report_after:
            metrics.divergence_rate_after = divergence_report_after.get('divergence_rate', 0.0)
            metrics.total_divergences_after = divergence_report_after.get('total_divergences', 0)
            
            for pattern in divergence_report_after.get('patterns', []):
                if pattern.get('pattern_type') == 'missing_in_backtest':
                    metrics.missing_in_backtest_after = pattern.get('frequency', 0)
                elif pattern.get('pattern_type') == 'extra_in_backtest':
                    metrics.extra_in_backtest_after = pattern.get('frequency', 0)
            
            metrics.calculate_improvements()
        
        return metrics
    
    def save_adjustment_report(
        self,
        report: AdjustmentReport,
        filename: Optional[str] = None
    ) -> Path:
        """Guarda reporte de ajustes."""
        if filename is None:
            filename = f"adjustment_report_{datetime.now(timezone.utc).isoformat().replace(':', '-')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"Adjustment report saved: {filepath}")
        return filepath
    
    def get_summary(self, report: AdjustmentReport) -> str:
        """Genera resumen textual del reporte."""
        summary = f"""
REPORTE DE AJUSTE DE THRESHOLDS - RESUMEN
==========================================

Timestamp: {report.timestamp}
Período: {report.analysis_period}

AJUSTES APLICADOS ({len(report.adjustments)})
------------------------------------------
"""
        for i, adj in enumerate(report.adjustments, 1):
            status = "✓" if adj.applied else "✗"
            valid = "✓" if adj.validation_passed else "✗"
            summary += f"""
{i}. {adj.parameter_name} {status} {valid}
   Cambio: {adj.old_value} → {adj.new_value}
   Razón: {adj.reason}
   Confianza: {adj.confidence*100:.0f}%
   Validación: {adj.validation_notes}
"""
        
        if report.convergence_metrics:
            metrics = report.convergence_metrics
            summary += f"""
MÉTRICAS DE CONVERGENCIA
------------------------
Antes del ajuste:
  - Divergencias totales: {metrics.total_divergences_before}
  - Tasa de divergencia: {metrics.divergence_rate_before*100:.2f}%
  - Missing in backtest: {metrics.missing_in_backtest_before}
  - Extra in backtest: {metrics.extra_in_backtest_before}
"""
            if metrics.divergence_rate_after is not None:
                summary += f"""
Después del ajuste:
  - Divergencias totales: {metrics.total_divergences_after}
  - Tasa de divergencia: {metrics.divergence_rate_after*100:.2f}%
  - Missing in backtest: {metrics.missing_in_backtest_after}
  - Extra in backtest: {metrics.extra_in_backtest_after}

Mejora:
  - Reducción divergencia: {metrics.divergence_rate_improvement*100:.2f}%
  - Divergencias menos: {metrics.divergences_reduction}
  - Convergencia lograda: {"SÍ" if metrics.convergence_achieved else "NO"}
"""
        
        if report.config_backup_path:
            summary += f"\nRespaldo de config: {report.config_backup_path}\n"
        
        return summary


# Singleton
_threshold_adjuster: Optional[ThresholdAdjuster] = None
_adjuster_lock = __import__('threading').RLock()


def get_threshold_adjuster(config_path: Optional[Path] = None) -> ThresholdAdjuster:
    """Obtiene instancia singleton del ThresholdAdjuster."""
    global _threshold_adjuster
    
    with _adjuster_lock:
        if _threshold_adjuster is None:
            _threshold_adjuster = ThresholdAdjuster(config_path)
        return _threshold_adjuster
