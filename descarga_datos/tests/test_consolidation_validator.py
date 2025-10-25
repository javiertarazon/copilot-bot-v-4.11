"""
Tests para FASE FINAL: Task 15 - ConsolidationValidator
Valida integridad del sistema completo.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from descarga_datos.utils.consolidation_validator import (
    ConsolidationValidator,
    ValidationStatus,
    TestResult,
    IntegrationCheck,
    ProductionReadinessReport,
    get_consolidation_validator
)


@pytest.fixture
def temp_workspace():
    """Crea workspace temporal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def validator(temp_workspace):
    """Crea instancia del validador."""
    return ConsolidationValidator(workspace_dir=temp_workspace)


@pytest.fixture
def sample_test_results():
    """Resultados de tests de ejemplo."""
    return [
        TestResult(
            test_name="test_signal_logger",
            total=14,
            passed=14,
            failed=0,
            skipped=0,
            duration_seconds=1.2,
            status=ValidationStatus.PASSED
        ),
        TestResult(
            test_name="test_backtest_validator",
            total=9,
            passed=9,
            failed=0,
            skipped=0,
            duration_seconds=0.8,
            status=ValidationStatus.PASSED
        ),
        TestResult(
            test_name="test_trace_comparator",
            total=10,
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=1.0,
            status=ValidationStatus.PASSED
        ),
    ]


@pytest.fixture
def sample_integration_checks():
    """Verificaciones de integración de ejemplo."""
    return [
        IntegrationCheck(
            check_name="Module: signal_logger.py",
            description="Signal capture module",
            result=True,
            details="Found",
            severity="critical"
        ),
        IntegrationCheck(
            check_name="Directory: data/signals",
            description="Signal storage",
            result=True,
            details="Directory accessible",
            severity="high"
        ),
        IntegrationCheck(
            check_name="Import: SignalLogger",
            description="Module import",
            result=True,
            details="Successfully imported",
            severity="critical"
        ),
    ]


class TestValidationStatus:
    """Tests para ValidationStatus enum."""
    
    def test_validation_status_values(self):
        """Verifica valores del enum."""
        assert ValidationStatus.PASSED.value == "passed"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.WARNING.value == "warning"
        assert ValidationStatus.NOT_TESTED.value == "not_tested"


class TestTestResult:
    """Tests para TestResult dataclass."""
    
    def test_test_result_creation(self):
        """Crea resultado de test."""
        result = TestResult(
            test_name="test_sample",
            total=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_seconds=2.5,
            status=ValidationStatus.FAILED
        )
        
        assert result.test_name == "test_sample"
        assert result.total == 100
        assert result.passed == 95
        assert result.pass_rate == 95.0
    
    def test_pass_rate_calculation(self):
        """Calcula tasa de paso."""
        result = TestResult(
            test_name="test",
            total=10,
            passed=8,
            failed=2,
            skipped=0,
            duration_seconds=1.0,
            status=ValidationStatus.PASSED
        )
        
        assert result.pass_rate == 80.0
    
    def test_pass_rate_zero_total(self):
        """Maneja total zero."""
        result = TestResult(
            test_name="test",
            total=0,
            passed=0,
            failed=0,
            skipped=0,
            duration_seconds=0.0,
            status=ValidationStatus.NOT_TESTED
        )
        
        assert result.pass_rate == 0.0
    
    def test_test_result_to_dict(self):
        """Serializa a dict."""
        result = TestResult(
            test_name="test",
            total=10,
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=1.0,
            status=ValidationStatus.PASSED
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['test_name'] == "test"
        assert result_dict['status'] == "passed"


class TestIntegrationCheck:
    """Tests para IntegrationCheck dataclass."""
    
    def test_integration_check_creation(self):
        """Crea verificación."""
        check = IntegrationCheck(
            check_name="Module check",
            description="Test module existence",
            result=True,
            details="Found",
            severity="critical"
        )
        
        assert check.check_name == "Module check"
        assert check.result is True
    
    def test_integration_check_to_dict(self):
        """Serializa a dict."""
        check = IntegrationCheck(
            check_name="Test",
            description="Desc",
            result=True,
            details="OK",
            severity="high"
        )
        
        check_dict = check.to_dict()
        
        assert check_dict['check_name'] == "Test"
        assert check_dict['severity'] == "high"


class TestProductionReadinessReport:
    """Tests para ProductionReadinessReport."""
    
    def test_report_creation(self, sample_test_results, sample_integration_checks):
        """Crea reporte."""
        report = ProductionReadinessReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=5.0,
            test_results=sample_test_results,
            total_tests=33,
            total_passed=33,
            total_failed=0,
            integration_checks=sample_integration_checks,
            critical_issues=0,
            production_ready=True,
            readiness_score=99.0
        )
        
        assert report.total_tests == 33
        assert report.total_passed == 33
        assert report.production_ready is True
    
    def test_report_to_dict(self, sample_test_results, sample_integration_checks):
        """Serializa reporte."""
        report = ProductionReadinessReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=5.0,
            test_results=sample_test_results,
            total_tests=33,
            total_passed=33,
            total_failed=0,
            integration_checks=sample_integration_checks,
            critical_issues=0,
            production_ready=True,
            readiness_score=99.0
        )
        
        report_dict = report.to_dict()
        
        assert report_dict['total_tests'] == 33
        assert report_dict['production_ready'] is True
        assert len(report_dict['test_results']) == 3


class TestConsolidationValidatorInitialization:
    """Tests para inicialización."""
    
    def test_initialization(self, temp_workspace):
        """Inicializa validador."""
        validator = ConsolidationValidator(workspace_dir=temp_workspace)
        
        assert validator.workspace_dir == temp_workspace
        assert validator.output_dir.exists()
    
    def test_output_dir_creation(self, validator):
        """Crea directorio de output."""
        assert validator.output_dir.exists()


class TestModuleStructureValidation:
    """Tests para validación de estructura."""
    
    def test_validate_module_structure(self, validator):
        """Valida estructura de módulos."""
        checks = validator.validate_module_structure()
        
        assert isinstance(checks, list)
        assert len(checks) > 0
        
        # Debería tener verificaciones de módulos
        module_checks = [c for c in checks if "Module:" in c.check_name]
        assert len(module_checks) > 0
    
    def test_module_check_properties(self, validator):
        """Verifica propiedades de checks."""
        checks = validator.validate_module_structure()
        
        for check in checks:
            assert hasattr(check, 'check_name')
            assert hasattr(check, 'result')
            assert hasattr(check, 'severity')
    
    def test_critical_severity_detection(self, validator):
        """Detecta problemas críticos."""
        checks = validator.validate_module_structure()
        
        critical_checks = [c for c in checks if c.severity == "critical"]
        assert len(critical_checks) > 0


class TestImportValidation:
    """Tests para validación de imports."""
    
    def test_validate_imports(self, validator):
        """Valida imports."""
        checks = validator.validate_imports()
        
        assert isinstance(checks, list)
        assert len(checks) > 0
    
    def test_import_check_structure(self, validator):
        """Estructura de import checks."""
        checks = validator.validate_imports()
        
        for check in checks:
            assert "Import:" in check.check_name
            assert check.severity in ["critical", "high", "medium", "low"]


class TestConfigurationValidation:
    """Tests para validación de configuración."""
    
    def test_validate_configuration(self, validator):
        """Valida configuración."""
        checks = validator.validate_configuration()
        
        assert isinstance(checks, list)
        assert len(checks) > 0
    
    def test_config_file_check(self, validator):
        """Verifica config.yaml."""
        checks = validator.validate_configuration()
        
        config_checks = [c for c in checks if "config.yaml" in c.check_name]
        assert len(config_checks) > 0


class TestDocumentationValidation:
    """Tests para validación de documentación."""
    
    def test_validate_documentation(self, validator):
        """Valida documentación."""
        checks = validator.validate_documentation()
        
        assert isinstance(checks, list)
        assert len(checks) > 0
    
    def test_documentation_check_structure(self, validator):
        """Estructura de doc checks."""
        checks = validator.validate_documentation()
        
        for check in checks:
            assert "Documentation:" in check.check_name


class TestReportCompilation:
    """Tests para compilación de reportes."""
    
    def test_compile_report_perfect_score(self, validator, sample_test_results, sample_integration_checks):
        """Compila reporte con puntuación perfecta."""
        # Todos los tests passen, sin problemas críticos
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        
        assert report.total_tests == sum(r.total for r in sample_test_results)
        assert report.total_passed == sum(r.passed for r in sample_test_results)
        assert report.total_failed == 0
    
    def test_compile_report_with_failures(self, validator):
        """Compila reporte con fallos."""
        test_results = [
            TestResult(
                test_name="test",
                total=10,
                passed=8,
                failed=2,
                skipped=0,
                duration_seconds=1.0,
                status=ValidationStatus.FAILED
            )
        ]
        
        checks = [
            IntegrationCheck(
                check_name="Test",
                description="Test",
                result=False,
                details="Failed",
                severity="critical"
            )
        ]
        
        report = validator.compile_report(test_results, checks)
        
        assert report.total_failed == 2
        assert report.critical_issues == 1
        assert report.production_ready is False
    
    def test_readiness_score_calculation(self, validator, sample_test_results, sample_integration_checks):
        """Calcula score de readiness."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        
        assert 0 <= report.readiness_score <= 100
        assert report.readiness_score > 90  # Debería ser alto


class TestReportSaving:
    """Tests para guardado de reportes."""
    
    def test_save_report(self, validator, sample_test_results, sample_integration_checks):
        """Guarda reporte."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        filepath = validator.save_report(report)
        
        assert filepath.exists()
        assert filepath.suffix == ".json"
    
    def test_save_report_custom_filename(self, validator, sample_test_results, sample_integration_checks):
        """Guarda con nombre personalizado."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        filepath = validator.save_report(report, filename="custom_report.json")
        
        assert filepath.name == "custom_report.json"
        assert filepath.exists()


class TestSummaryGeneration:
    """Tests para generación de resúmenes."""
    
    def test_get_summary_format(self, validator, sample_test_results, sample_integration_checks):
        """Genera resumen."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        summary = validator.get_summary(report)
        
        assert isinstance(summary, str)
        assert "PRODUCTION READINESS" in summary
        assert "CONSOLIDATION REPORT" in summary
    
    def test_summary_contains_key_metrics(self, validator, sample_test_results, sample_integration_checks):
        """Resumen contiene métricas clave."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        summary = validator.get_summary(report)
        
        assert str(report.total_tests) in summary
        assert str(report.total_passed) in summary
    
    def test_summary_ready_message(self, validator, sample_test_results, sample_integration_checks):
        """Muestra mensaje de listo."""
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        summary = validator.get_summary(report)
        
        if report.production_ready:
            assert "READY FOR DEPLOYMENT" in summary or "✅" in summary


class TestSingleton:
    """Tests para patrón singleton."""
    
    def test_singleton_instance(self):
        """Verifica singleton."""
        validator1 = get_consolidation_validator()
        validator2 = get_consolidation_validator()
        
        assert validator1 is validator2


class TestIntegration:
    """Tests de integración end-to-end."""
    
    def test_full_validation_workflow(self, validator):
        """Flujo completo de validación."""
        # 1. Validar estructura
        structure_checks = validator.validate_module_structure()
        assert len(structure_checks) > 0
        
        # 2. Validar imports
        import_checks = validator.validate_imports()
        assert len(import_checks) > 0
        
        # 3. Validar configuración
        config_checks = validator.validate_configuration()
        assert len(config_checks) > 0
        
        # 4. Validar documentación
        doc_checks = validator.validate_documentation()
        assert len(doc_checks) > 0
        
        # 5. Compilar reporte
        all_checks = structure_checks + import_checks + config_checks + doc_checks
        
        test_results = [
            TestResult(
                test_name="consolidated",
                total=100,
                passed=100,
                failed=0,
                skipped=0,
                duration_seconds=5.0,
                status=ValidationStatus.PASSED
            )
        ]
        
        report = validator.compile_report(test_results, all_checks)
        
        assert report is not None
        assert report.total_tests == 100
    
    def test_report_generation_and_save(self, validator, sample_test_results, sample_integration_checks):
        """Genera y guarda reporte."""
        # Compilar
        report = validator.compile_report(sample_test_results, sample_integration_checks)
        
        # Guardar
        filepath = validator.save_report(report)
        
        # Verificar
        assert filepath.exists()
        
        # Leer y validar
        with open(filepath, 'r') as f:
            saved = json.load(f)
        
        assert saved['total_tests'] > 0
        assert 'production_ready' in saved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
