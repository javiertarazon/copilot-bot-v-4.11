"""
Tests para FASE 5: Task 14 - ThresholdAdjuster
Valida aplicación de ajustes y medición de convergencia.
"""

import pytest
import json
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from descarga_datos.utils.threshold_adjuster import (
    ThresholdAdjuster,
    ParameterAdjustment,
    ConvergenceMetrics,
    AdjustmentReport,
    get_threshold_adjuster
)


@pytest.fixture
def temp_config_dir():
    """Crea directorio temporal para configs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_config_dir):
    """Crea config.yaml de ejemplo."""
    config = {
        'strategies': {
            'UltraDetailedHeikinAshiML': {
                'ml_confidence_minimum': 0.75,
                'rsi_range_lower': 30.0,
                'rsi_range_upper': 70.0,
                'atr_multiplier': 1.5,
            }
        }
    }
    
    config_file = temp_config_dir / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file, config


@pytest.fixture
def adjuster(sample_config):
    """Crea instancia del ajustador."""
    config_file, _ = sample_config
    return ThresholdAdjuster(config_path=config_file)


@pytest.fixture
def sample_divergence_report_before():
    """Reporte de divergencias antes del ajuste."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_signals_analyzed": 100,
        "total_divergences": 20,
        "divergence_rate": 0.20,
        "patterns": [
            {
                "pattern_type": "missing_in_backtest",
                "frequency": 12,
                "symbols_affected": ["BTC_USDT"]
            },
            {
                "pattern_type": "extra_in_backtest",
                "frequency": 8,
                "symbols_affected": ["ETH_USDT"]
            }
        ]
    }


@pytest.fixture
def sample_divergence_report_after():
    """Reporte de divergencias después del ajuste (mejorado)."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_signals_analyzed": 100,
        "total_divergences": 10,
        "divergence_rate": 0.10,
        "patterns": [
            {
                "pattern_type": "missing_in_backtest",
                "frequency": 6,
                "symbols_affected": ["BTC_USDT"]
            },
            {
                "pattern_type": "extra_in_backtest",
                "frequency": 4,
                "symbols_affected": ["ETH_USDT"]
            }
        ]
    }


class TestThresholdAdjusterInitialization:
    """Tests para inicialización."""
    
    def test_initialization_with_valid_config(self, sample_config):
        """Inicializa con config válido."""
        config_file, config = sample_config
        adjuster = ThresholdAdjuster(config_path=config_file)
        
        assert adjuster.config_path == config_file
        assert adjuster.config is not None
        assert 'strategies' in adjuster.config
    
    def test_initialization_creates_output_dir(self, adjuster):
        """Crea directorio de salida."""
        assert adjuster.output_dir.exists()


class TestParameterValidation:
    """Tests para validación de parámetros."""
    
    def test_validate_ml_confidence_minimum(self, adjuster):
        """Valida rango de ml_confidence_minimum."""
        # Válido
        is_valid, msg = adjuster.validate_parameter('ml_confidence_minimum', 0.75)
        assert is_valid
        
        # Demasiado bajo
        is_valid, msg = adjuster.validate_parameter('ml_confidence_minimum', 0.4)
        assert not is_valid
        
        # Demasiado alto
        is_valid, msg = adjuster.validate_parameter('ml_confidence_minimum', 1.0)
        assert not is_valid
    
    def test_validate_rsi_range(self, adjuster):
        """Valida rango RSI."""
        # Válido
        is_valid, msg = adjuster.validate_parameter('rsi_range_lower', 35.0)
        assert is_valid
        
        is_valid, msg = adjuster.validate_parameter('rsi_range_upper', 65.0)
        assert is_valid
        
        # Inválido
        is_valid, msg = adjuster.validate_parameter('rsi_range_lower', 5.0)
        assert not is_valid
    
    def test_validate_atr_multiplier(self, adjuster):
        """Valida ATR multiplier."""
        is_valid, msg = adjuster.validate_parameter('atr_multiplier', 1.8)
        assert is_valid
        
        is_valid, msg = adjuster.validate_parameter('atr_multiplier', 5.0)
        assert not is_valid
    
    def test_unconstrained_parameter(self, adjuster):
        """Parámetro sin constraints se acepta."""
        is_valid, msg = adjuster.validate_parameter('custom_param', 999.0)
        assert is_valid


class TestAdjustmentCreation:
    """Tests para crear ajustes desde recomendaciones."""
    
    def test_create_adjustments_from_recommendations(self, adjuster):
        """Convierte recomendaciones a ajustes."""
        recommendations = [
            {
                'filter_name': 'ml_confidence_minimum',
                'current_value': 0.75,
                'recommended_value': 0.65,
                'reason': 'Capturar señales perdidas',
                'confidence': 0.85
            },
            {
                'filter_name': 'atr_multiplier',
                'current_value': 1.5,
                'recommended_value': 1.8,
                'reason': 'Reducir falsos positivos',
                'confidence': 0.80
            }
        ]
        
        adjustments = adjuster.create_adjustments_from_recommendations(recommendations)
        
        assert len(adjustments) == 2
        assert adjustments[0].parameter_name == 'ml_confidence_minimum'
        assert adjustments[0].old_value == 0.75
        assert adjustments[0].new_value == 0.65
        assert adjustments[0].validation_passed
    
    def test_create_adjustments_validates(self, adjuster):
        """Valida recomendaciones durante creación."""
        recommendations = [
            {
                'filter_name': 'ml_confidence_minimum',
                'current_value': 0.75,
                'recommended_value': 0.3,  # Inválido (< 0.5)
                'reason': 'Test',
                'confidence': 0.5
            }
        ]
        
        adjustments = adjuster.create_adjustments_from_recommendations(recommendations)
        
        assert len(adjustments) == 1
        assert not adjustments[0].validation_passed
        assert "outside valid range" in adjustments[0].validation_notes


class TestAdjustmentApplication:
    """Tests para aplicar ajustes."""
    
    def test_apply_adjustments_dry_run(self, adjuster):
        """Aplica ajustes en dry_run (sin guardar)."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85
            )
        ]
        
        success, msg = adjuster.apply_adjustments(adjustments, dry_run=True)
        
        assert success
        assert "applied" in msg.lower() or "dry" in msg.lower()
    
    def test_apply_adjustments_saves_config(self, adjuster, sample_config):
        """Aplica ajustes y guarda config."""
        config_file, _ = sample_config
        adjuster = ThresholdAdjuster(config_path=config_file)
        
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85,
                validation_passed=True
            )
        ]
        
        success, msg = adjuster.apply_adjustments(adjustments, dry_run=False)
        
        assert success
        
        # Verificar que config fue actualizado
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config['strategies']['UltraDetailedHeikinAshiML']['ml_confidence_minimum'] == 0.65
    
    def test_apply_adjustments_fails_validation(self, adjuster):
        """Rechaza ajustes que fallan validación."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.2,  # Inválido
                reason='Test',
                confidence=0.5,
                validation_passed=False
            )
        ]
        
        success, msg = adjuster.apply_adjustments(adjustments)
        
        assert not success
        assert "Validation failed" in msg
    
    def test_create_backup_on_apply(self, adjuster):
        """Crea respaldo al aplicar ajustes."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85,
                validation_passed=True
            )
        ]
        
        success, msg = adjuster.apply_adjustments(adjustments, dry_run=False)
        
        assert success
        
        # Verificar que existe respaldo
        backups = list(adjuster.output_dir.glob("config_backup_*.yaml"))
        assert len(backups) > 0


class TestConvergenceMetrics:
    """Tests para métricas de convergencia."""
    
    def test_create_convergence_metrics(self, adjuster, sample_divergence_report_before):
        """Crea métricas de convergencia."""
        metrics = adjuster.create_convergence_report(sample_divergence_report_before)
        
        assert metrics.divergence_rate_before == 0.20
        assert metrics.total_divergences_before == 20
        assert metrics.missing_in_backtest_before == 12
        assert metrics.extra_in_backtest_before == 8
    
    def test_convergence_metrics_after_adjustment(
        self, 
        adjuster,
        sample_divergence_report_before,
        sample_divergence_report_after
    ):
        """Calcula mejora después de ajuste."""
        metrics = adjuster.create_convergence_report(
            sample_divergence_report_before,
            sample_divergence_report_after
        )
        
        assert metrics.divergence_rate_after == 0.10
        assert metrics.total_divergences_after == 10
        
        # Mejoras
        assert metrics.divergence_rate_improvement == 0.10
        assert metrics.divergences_reduction == 10
        assert metrics.convergence_achieved is True
    
    def test_convergence_metrics_no_improvement(self, adjuster):
        """Detecta cuando no hay mejora."""
        report_bad = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_signals_analyzed": 100,
            "total_divergences": 30,
            "divergence_rate": 0.30,
            "patterns": []
        }
        
        report_worse = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_signals_analyzed": 100,
            "total_divergences": 40,
            "divergence_rate": 0.40,
            "patterns": []
        }
        
        metrics = adjuster.create_convergence_report(report_bad, report_worse)
        
        assert abs(metrics.divergence_rate_improvement - (-0.10)) < 0.001
        assert metrics.divergences_reduction == -10
        assert metrics.convergence_achieved is False


class TestParameterAdjustment:
    """Tests para dataclass ParameterAdjustment."""
    
    def test_parameter_adjustment_creation(self):
        """Crea ajuste de parámetro."""
        adj = ParameterAdjustment(
            parameter_name='ml_confidence_minimum',
            old_value=0.75,
            new_value=0.65,
            reason='Reduce false negatives',
            confidence=0.85
        )
        
        assert adj.parameter_name == 'ml_confidence_minimum'
        assert adj.applied is False
        assert adj.validation_passed is True
    
    def test_parameter_adjustment_to_dict(self):
        """Serializa ajuste a dict."""
        adj = ParameterAdjustment(
            parameter_name='ml_confidence_minimum',
            old_value=0.75,
            new_value=0.65,
            reason='Test',
            confidence=0.85
        )
        
        adj_dict = adj.to_dict()
        
        assert adj_dict['parameter_name'] == 'ml_confidence_minimum'
        assert adj_dict['old_value'] == 0.75
        assert adj_dict['new_value'] == 0.65


class TestAdjustmentReport:
    """Tests para reporte de ajustes."""
    
    def test_create_adjustment_report(self, adjuster):
        """Crea reporte de ajustes."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85,
                applied=True
            )
        ]
        
        report = AdjustmentReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period="2024-10-24",
            adjustments=adjustments
        )
        
        assert len(report.adjustments) == 1
        assert report.adjustments[0].applied is True
    
    def test_save_adjustment_report(self, adjuster):
        """Guarda reporte de ajustes."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85
            )
        ]
        
        report = AdjustmentReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period="2024-10-24",
            adjustments=adjustments
        )
        
        filepath = adjuster.save_adjustment_report(report)
        
        assert filepath.exists()
        
        # Verificar contenido
        with open(filepath, 'r') as f:
            saved = json.load(f)
        
        assert len(saved['adjustments']) == 1


class TestSummaryGeneration:
    """Tests para generación de resúmenes."""
    
    def test_get_summary_basic(self, adjuster):
        """Genera resumen básico."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85,
                applied=True
            )
        ]
        
        report = AdjustmentReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period="2024-10-24",
            adjustments=adjustments
        )
        
        summary = adjuster.get_summary(report)
        
        assert "REPORTE DE AJUSTE" in summary
        assert "ml_confidence_minimum" in summary
        assert "0.65" in summary
    
    def test_get_summary_with_convergence(self, adjuster, sample_divergence_report_before):
        """Genera resumen con métricas de convergencia."""
        adjustments = [
            ParameterAdjustment(
                parameter_name='ml_confidence_minimum',
                old_value=0.75,
                new_value=0.65,
                reason='Test',
                confidence=0.85
            )
        ]
        
        metrics = adjuster.create_convergence_report(sample_divergence_report_before)
        
        report = AdjustmentReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period="2024-10-24",
            adjustments=adjustments,
            convergence_metrics=metrics
        )
        
        summary = adjuster.get_summary(report)
        
        assert "MÉTRICAS DE CONVERGENCIA" in summary
        assert "Divergencias totales" in summary


class TestSingleton:
    """Tests para patrón singleton."""
    
    def test_singleton_instance(self):
        """Verifica singleton."""
        adjuster1 = get_threshold_adjuster()
        adjuster2 = get_threshold_adjuster()
        
        assert adjuster1 is adjuster2


class TestIntegration:
    """Tests de integración end-to-end."""
    
    def test_full_adjustment_workflow(self, adjuster):
        """Flujo completo: recommendations → adjustments → save → report."""
        # 1. Recomendaciones
        recommendations = [
            {
                'filter_name': 'ml_confidence_minimum',
                'current_value': 0.75,
                'recommended_value': 0.65,
                'reason': 'Capture missed signals',
                'confidence': 0.85
            }
        ]
        
        # 2. Crear ajustes
        adjustments = adjuster.create_adjustments_from_recommendations(recommendations)
        assert len(adjustments) == 1
        assert adjustments[0].validation_passed
        
        # 3. Aplicar (dry_run)
        success, msg = adjuster.apply_adjustments(adjustments, dry_run=True)
        assert success
        
        # 4. Crear reporte
        report = AdjustmentReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_period="2024-10-24",
            adjustments=adjustments
        )
        
        # 5. Guardar
        filepath = adjuster.save_adjustment_report(report)
        assert filepath.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
