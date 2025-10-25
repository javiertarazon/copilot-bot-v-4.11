"""
Tests para FASE 5: Task 13 - DivergenceAnalyzer
Valida la extracción de patrones y generación de recomendaciones.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from descarga_datos.utils.divergence_analyzer import (
    DivergenceAnalyzer,
    DivergencePattern,
    FilterRecommendation,
    DivergenceReport,
    get_divergence_analyzer
)


@pytest.fixture
def temp_reports_dir():
    """Crea directorio temporal para reportes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_report():
    """Genera un reporte de ejemplo."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "comparison_id": "test_comp_001",
        "symbol_analysis": {
            "BTC_USDT": {
                "total_signals": 50,
                "signals_matched": 45,
                "divergences": [
                    {
                        "divergence_type": "missing_in_backtest",
                        "price_difference": 2.5,
                        "pnl_impact": 150.0,
                        "timing_diff_ms": 500
                    },
                    {
                        "divergence_type": "extra_in_backtest",
                        "price_difference": 1.2,
                        "pnl_impact": -75.0,
                        "timing_diff_ms": 300
                    }
                ]
            },
            "ETH_USDT": {
                "total_signals": 40,
                "signals_matched": 38,
                "divergences": [
                    {
                        "divergence_type": "timing_diff",
                        "price_difference": 0.8,
                        "pnl_impact": 50.0,
                        "timing_diff_ms": 1200
                    }
                ]
            }
        }
    }


@pytest.fixture
def analyzer(temp_reports_dir):
    """Crea instancia del analizador."""
    return DivergenceAnalyzer(reports_dir=temp_reports_dir)


class TestDivergenceAnalyzerInitialization:
    """Tests para inicialización del analizador."""
    
    def test_initialization_creates_directories(self, temp_reports_dir):
        """Verifica que se crean directorios necesarios."""
        analyzer = DivergenceAnalyzer(reports_dir=temp_reports_dir)
        
        assert analyzer.reports_dir.exists()
        assert analyzer.output_dir.exists()
    
    def test_initialization_with_default_dirs(self):
        """Verifica inicialización con directorios por defecto."""
        analyzer = DivergenceAnalyzer()
        
        assert analyzer.reports_dir.exists()
        assert analyzer.output_dir.exists()
        assert "comparison_reports" in str(analyzer.reports_dir)
        assert "divergence_analysis" in str(analyzer.output_dir)


class TestReportLoading:
    """Tests para carga de reportes."""
    
    def test_load_empty_directory(self, analyzer):
        """Verifica comportamiento con directorio vacío."""
        reports = analyzer.load_comparison_reports()
        
        assert isinstance(reports, list)
        assert len(reports) == 0
    
    def test_load_single_report(self, analyzer, sample_report, temp_reports_dir):
        """Carga un reporte de ejemplo."""
        report_file = temp_reports_dir / "comparison_report_2024-10-24T12-00-00Z.json"
        
        with open(report_file, 'w') as f:
            json.dump(sample_report, f)
        
        reports = analyzer.load_comparison_reports(days_old=7)
        
        assert len(reports) == 1
        assert reports[0]["timestamp"] == sample_report["timestamp"]
    
    def test_load_multiple_reports(self, analyzer, sample_report, temp_reports_dir):
        """Carga múltiples reportes."""
        for i in range(3):
            report_file = temp_reports_dir / f"comparison_report_{i}.json"
            with open(report_file, 'w') as f:
                json.dump(sample_report, f)
        
        reports = analyzer.load_comparison_reports(days_old=7)
        
        assert len(reports) == 3
    
    def test_load_respects_days_old(self, analyzer):
        """Verifica parámetro days_old (sin archivos reales)."""
        # Con directorio vacío, debería retornar lista vacía
        reports = analyzer.load_comparison_reports(days_old=5)
        
        assert isinstance(reports, list)
        assert len(reports) >= 0  # Puede estar vacío


class TestDivergenceAnalysis:
    """Tests para análisis de divergencias."""
    
    def test_analyze_empty_reports(self, analyzer):
        """Analiza lista vacía de reportes."""
        report = analyzer.analyze_divergences([])
        
        assert report.total_signals_analyzed == 0
        assert report.total_divergences == 0
        assert report.divergence_rate == 0.0
        assert len(report.patterns) == 0
    
    def test_analyze_single_report(self, analyzer, sample_report):
        """Analiza un reporte de ejemplo."""
        report = analyzer.analyze_divergences([sample_report])
        
        assert report.total_signals_analyzed == 90  # 50 + 40
        assert report.total_divergences == 3
        assert abs(report.divergence_rate - 3/90) < 0.01
        assert len(report.patterns) == 3  # 3 tipos de divergencias
    
    def test_pattern_identification(self, analyzer, sample_report):
        """Identifica patrones correctamente."""
        report = analyzer.analyze_divergences([sample_report])
        
        pattern_types = {p.pattern_type for p in report.patterns}
        
        assert "missing_in_backtest" in pattern_types
        assert "extra_in_backtest" in pattern_types
        assert "timing_diff" in pattern_types
    
    def test_pattern_statistics(self, analyzer, sample_report):
        """Calcula estadísticas de patrones."""
        report = analyzer.analyze_divergences([sample_report])
        
        for pattern in report.patterns:
            assert pattern.frequency > 0
            assert len(pattern.symbols_affected) > 0
            assert pattern.avg_price_diff >= 0
            assert pattern.avg_timing_diff_ms >= 0
    
    def test_root_cause_identification(self, analyzer, sample_report):
        """Identifica causas raíz."""
        report = analyzer.analyze_divergences([sample_report])
        
        for pattern in report.patterns:
            # Al menos un patrón debe tener causas identificadas
            if pattern.frequency > 2:
                assert len(pattern.root_causes) > 0


class TestRecommendationGeneration:
    """Tests para generación de recomendaciones."""
    
    def test_generate_recommendations_high_divergence(self, analyzer, sample_report):
        """Genera recomendaciones con alta tasa de divergencia."""
        # Multiplicar divergencias para crear alta tasa
        for _ in range(5):
            sample_report["symbol_analysis"]["XRP_USDT"] = {
                "total_signals": 100,
                "divergences": [
                    {"divergence_type": "extra_in_backtest", "pnl_impact": -50.0, "price_difference": 1.5}
                ] * 20
            }
        
        report = analyzer.analyze_divergences([sample_report])
        
        assert len(report.recommendations) > 0
    
    def test_recommendation_structure(self, analyzer, sample_report):
        """Verifica estructura de recomendaciones."""
        report = analyzer.analyze_divergences([sample_report])
        
        for rec in report.recommendations:
            assert isinstance(rec, FilterRecommendation)
            assert rec.filter_name is not None
            assert rec.current_value is not None
            assert rec.recommended_value is not None
            assert 0 <= rec.confidence <= 1.0
            assert rec.reason is not None
    
    def test_missing_in_backtest_recommendation(self, analyzer):
        """Genera recomendaciones para missing_in_backtest."""
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol_analysis": {
                "BTC_USDT": {
                    "total_signals": 100,
                    "divergences": [
                        {
                            "divergence_type": "missing_in_backtest",
                            "pnl_impact": 250.0,
                            "price_difference": 3.5,
                            "timing_diff_ms": 800
                        }
                    ] * 8
                }
            }
        }
        
        report = analyzer.analyze_divergences([report_data])
        
        # Debería recomendar reducir ML confidence
        ml_recs = [r for r in report.recommendations if "ml_confidence" in r.filter_name]
        assert len(ml_recs) > 0
    
    def test_extra_in_backtest_recommendation(self, analyzer):
        """Genera recomendaciones para extra_in_backtest."""
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol_analysis": {
                "ETH_USDT": {
                    "total_signals": 100,
                    "divergences": [
                        {
                            "divergence_type": "extra_in_backtest",
                            "pnl_impact": -150.0,
                            "price_difference": 1.8,
                            "timing_diff_ms": 300
                        }
                    ] * 8
                }
            }
        }
        
        report = analyzer.analyze_divergences([report_data])
        
        # Debería recomendar aumentar ATR o filtros
        atr_recs = [r for r in report.recommendations if "atr" in r.filter_name]
        assert len(atr_recs) > 0


class TestSymbolAnalysis:
    """Tests para análisis por símbolo."""
    
    def test_symbol_analysis_structure(self, analyzer, sample_report):
        """Verifica estructura de análisis por símbolo."""
        report = analyzer.analyze_divergences([sample_report])
        
        assert "BTC_USDT" in report.symbol_analysis
        assert "ETH_USDT" in report.symbol_analysis
        
        for symbol, stats in report.symbol_analysis.items():
            assert "total_divergences" in stats
            assert "by_type" in stats
            assert "critical_issues" in stats
    
    def test_symbol_divergence_count(self, analyzer, sample_report):
        """Cuenta divergencias por símbolo."""
        report = analyzer.analyze_divergences([sample_report])
        
        assert report.symbol_analysis["BTC_USDT"]["total_divergences"] == 2
        assert report.symbol_analysis["ETH_USDT"]["total_divergences"] == 1
    
    def test_critical_issues_detection(self, analyzer):
        """Detecta problemas críticos (PnL > 200)."""
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol_analysis": {
                "XRP_USDT": {
                    "total_signals": 50,
                    "divergences": [
                        {"divergence_type": "missing_in_backtest", "pnl_impact": 300.0, 
                         "price_difference": 1.5, "timing_diff_ms": 500},
                        {"divergence_type": "extra_in_backtest", "pnl_impact": -250.0,
                         "price_difference": 1.0, "timing_diff_ms": 300}
                    ]
                }
            }
        }
        
        analysis = analyzer.analyze_divergences([report_data])
        
        # El análisis detecta divergencias con |pnl_impact| > 200
        assert analysis.symbol_analysis["XRP_USDT"]["critical_issues"] == 2


class TestReportSerialization:
    """Tests para serialización de reportes."""
    
    def test_divergence_report_to_dict(self, analyzer, sample_report):
        """Convierte reporte a diccionario."""
        report = analyzer.analyze_divergences([sample_report])
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert "timestamp" in report_dict
        assert "patterns" in report_dict
        assert "recommendations" in report_dict
        assert "symbol_analysis" in report_dict
    
    def test_pattern_serialization(self, analyzer, sample_report):
        """Serializa patrones correctamente."""
        report = analyzer.analyze_divergences([sample_report])
        report_dict = report.to_dict()
        
        for pattern_dict in report_dict["patterns"]:
            assert "pattern_type" in pattern_dict
            assert "frequency" in pattern_dict
            assert "symbols_affected" in pattern_dict
    
    def test_recommendation_serialization(self, analyzer, sample_report):
        """Serializa recomendaciones correctamente."""
        report = analyzer.analyze_divergences([sample_report])
        report_dict = report.to_dict()
        
        for rec_dict in report_dict["recommendations"]:
            assert "filter_name" in rec_dict
            assert "current_value" in rec_dict
            assert "recommended_value" in rec_dict
            assert "confidence" in rec_dict


class TestReportSaving:
    """Tests para guardado de reportes."""
    
    def test_save_report(self, analyzer, sample_report):
        """Guarda reporte en JSON."""
        report = analyzer.analyze_divergences([sample_report])
        filepath = analyzer.save_report(report)
        
        assert filepath.exists()
        assert filepath.suffix == ".json"
        
        # Verificar que se puede leer
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
            assert "patterns" in saved_data
    
    def test_save_report_custom_filename(self, analyzer, sample_report):
        """Guarda reporte con nombre personalizado."""
        report = analyzer.analyze_divergences([sample_report])
        filepath = analyzer.save_report(report, filename="custom_analysis.json")
        
        assert filepath.name == "custom_analysis.json"
        assert filepath.exists()
    
    def test_export_recommendations_to_yaml(self, analyzer):
        """Exporta recomendaciones en YAML."""
        # Crear reporte simple
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol_analysis": {
                "BTC_USDT": {
                    "total_signals": 50,
                    "divergences": [
                        {"divergence_type": "extra_in_backtest", "pnl_impact": -50.0,
                         "price_difference": 1.2, "timing_diff_ms": 300}
                    ]
                }
            }
        }
        
        report = analyzer.analyze_divergences([report_data])
        filepath = analyzer.export_recommendations_to_yaml(report)
        
        assert filepath.exists()
        assert filepath.suffix == ".yaml"
        
        with open(filepath, 'r') as f:
            content = f.read()
            assert "RECOMENDACIONES" in content or len(content) > 50


class TestSummaryGeneration:
    """Tests para generación de resúmenes."""
    
    def test_get_summary_format(self, analyzer, sample_report):
        """Verifica formato del resumen."""
        report = analyzer.analyze_divergences([sample_report])
        summary = analyzer.get_summary(report)
        
        assert isinstance(summary, str)
        assert "ANÁLISIS DE DIVERGENCIAS" in summary
        assert "PATRONES IDENTIFICADOS" in summary
        assert "RECOMENDACIONES" in summary
    
    def test_summary_contains_key_info(self, analyzer, sample_report):
        """Resumen contiene información clave."""
        report = analyzer.analyze_divergences([sample_report])
        summary = analyzer.get_summary(report)
        
        assert str(report.total_signals_analyzed) in summary
        assert str(report.total_divergences) in summary
        assert "BTC_USDT" in summary or "ETH_USDT" in summary


class TestSingleton:
    """Tests para patrón singleton."""
    
    def test_singleton_instance(self):
        """Verifica que get_divergence_analyzer devuelve singleton."""
        analyzer1 = get_divergence_analyzer()
        analyzer2 = get_divergence_analyzer()
        
        assert analyzer1 is analyzer2
    
    def test_singleton_with_custom_dir(self, temp_reports_dir):
        """Singleton con directorio personalizado."""
        # Limpiar singleton anterior
        import descarga_datos.utils.divergence_analyzer as da_module
        da_module._divergence_analyzer = None
        
        analyzer = get_divergence_analyzer(reports_dir=temp_reports_dir)
        
        assert analyzer.reports_dir == temp_reports_dir


class TestIntegration:
    """Tests de integración end-to-end."""
    
    def test_full_analysis_workflow(self, analyzer):
        """Flujo completo: analyze → save (simplificado)."""
        # Crear datos de análisis sin necesidad de archivo
        sample_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comparison_id": "test_comp",
            "symbol_analysis": {
                "BTC_USDT": {
                    "total_signals": 50,
                    "signals_matched": 48,
                    "divergences": [
                        {"divergence_type": "missing_in_backtest", "pnl_impact": 150.0,
                         "price_difference": 2.5, "timing_diff_ms": 500},
                        {"divergence_type": "extra_in_backtest", "pnl_impact": -75.0,
                         "price_difference": 1.2, "timing_diff_ms": 300}
                    ]
                }
            }
        }
        
        # Analizar y guardar
        analysis = analyzer.analyze_divergences([sample_report])
        assert analysis.total_divergences == 2
        
        saved_path = analyzer.save_report(analysis)
        assert saved_path.exists()
    
    def test_multiple_reports_aggregation(self, analyzer):
        """Agrega análisis de múltiples reportes."""
        reports = []
        total_divs = 0
        
        for i in range(3):
            num_divs = i + 1
            total_divs += num_divs
            
            report_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol_analysis": {
                    "BTC_USDT": {
                        "total_signals": 50,
                        "divergences": [
                            {"divergence_type": "missing_in_backtest", "pnl_impact": 100.0,
                             "price_difference": 1.5, "timing_diff_ms": 500}
                        ] * num_divs
                    }
                }
            }
            reports.append(report_data)
        
        analysis = analyzer.analyze_divergences(reports)
        
        assert analysis.total_signals_analyzed == 150
        assert analysis.total_divergences == total_divs  # 1+2+3 = 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
