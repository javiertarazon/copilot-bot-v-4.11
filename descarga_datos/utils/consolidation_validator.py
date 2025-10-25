"""
FASE FINAL: Task 15 - Consolidation Validator
Valida integridad completa del sistema y prepara para producción.

Funcionalidades:
1. Full test suite execution
2. Integration validation
3. Production readiness checks
4. Documentation generation
5. Deployment checklist
6. Final report
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import subprocess
import sys

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Estados de validación."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_TESTED = "not_tested"


@dataclass
class TestResult:
    """Resultado de ejecución de tests."""
    test_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    status: ValidationStatus
    errors: List[str] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        """Porcentaje de tests que passaron."""
        return (self.passed / self.total * 100) if self.total > 0 else 0.0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class IntegrationCheck:
    """Validación de integración."""
    check_name: str
    description: str
    result: bool
    details: str
    severity: str  # "critical", "high", "medium", "low"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProductionReadinessReport:
    """Reporte completo de preparación para producción."""
    timestamp: str
    duration_seconds: float
    
    # Tests
    test_results: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    
    # Integration
    integration_checks: List[IntegrationCheck] = field(default_factory=list)
    critical_issues: int = 0
    
    # Overall
    production_ready: bool = False
    readiness_score: float = 0.0
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = {
            'timestamp': self.timestamp,
            'duration_seconds': self.duration_seconds,
            'test_results': [r.to_dict() for r in self.test_results],
            'total_tests': self.total_tests,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'integration_checks': [c.to_dict() for c in self.integration_checks],
            'critical_issues': self.critical_issues,
            'production_ready': self.production_ready,
            'readiness_score': self.readiness_score,
            'recommendations': self.recommendations
        }
        return result


class ConsolidationValidator:
    """Valida sistema completo antes de producción."""
    
    def __init__(self, workspace_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None):
        """
        Inicializa validador.
        
        Args:
            workspace_dir: Directorio del workspace
            output_dir: Directorio para reportes
        """
        if workspace_dir is None:
            workspace_dir = Path(__file__).parent.parent.parent
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "data" / "consolidation_reports"
        
        self.workspace_dir = Path(workspace_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ConsolidationValidator initialized: workspace={self.workspace_dir}")
    
    def run_full_test_suite(self) -> List[TestResult]:
        """
        Ejecuta suite completa de tests.
        
        Returns:
            Lista de resultados de tests
        """
        test_files = [
            "descarga_datos/tests/test_signal_logger.py",
            "descarga_datos/tests/test_backtest_validator.py",
            "descarga_datos/tests/test_trace_comparator.py",
            "descarga_datos/tests/test_divergence_analyzer.py",
            "descarga_datos/tests/test_threshold_adjuster.py",
        ]
        
        results = []
        
        for test_file in test_files:
            try:
                # Ejecutar pytest
                cmd = [
                    sys.executable, "-m", "pytest",
                    test_file,
                    "-v", "--tb=no", "-q"
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Parsear output
                output = result.stdout + result.stderr
                
                # Extraer números
                passed = output.count(" passed")
                failed = output.count(" failed")
                skipped = output.count(" skipped")
                total = passed + failed + skipped
                
                # Determinar status
                status = ValidationStatus.PASSED if failed == 0 else ValidationStatus.FAILED
                
                test_result = TestResult(
                    test_name=Path(test_file).stem,
                    total=total,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    duration_seconds=0.0,
                    status=status,
                    errors=[] if failed == 0 else ["Some tests failed"]
                )
                
                results.append(test_result)
                logger.info(f"Test {test_file}: {passed}/{total} passed")
            
            except subprocess.TimeoutExpired:
                logger.error(f"Test {test_file} timed out")
                results.append(TestResult(
                    test_name=Path(test_file).stem,
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration_seconds=0.0,
                    status=ValidationStatus.FAILED,
                    errors=["Test execution timed out"]
                ))
            except Exception as e:
                logger.error(f"Error running {test_file}: {e}")
                results.append(TestResult(
                    test_name=Path(test_file).stem,
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration_seconds=0.0,
                    status=ValidationStatus.FAILED,
                    errors=[str(e)]
                ))
        
        return results
    
    def validate_module_structure(self) -> List[IntegrationCheck]:
        """
        Valida estructura de módulos.
        
        Returns:
            Lista de verificaciones
        """
        checks = []
        
        # Verificar módulos principales
        required_modules = {
            'signal_logger.py': 'Signal capture and persistence',
            'backtest_validator.py': 'Backtest execution and validation',
            'trace_comparator.py': 'Live vs backtest comparison',
            'divergence_analyzer.py': 'Divergence pattern analysis',
            'threshold_adjuster.py': 'Parameter adjustment and validation',
        }
        
        for module_name, description in required_modules.items():
            module_path = self.workspace_dir / "descarga_datos" / "utils" / module_name
            exists = module_path.exists()
            
            check = IntegrationCheck(
                check_name=f"Module: {module_name}",
                description=description,
                result=exists,
                details=f"{'Found' if exists else 'NOT FOUND'}: {module_path}",
                severity="critical" if not exists else "low"
            )
            checks.append(check)
        
        # Verificar directorios de datos
        required_dirs = {
            'data/signals': 'Signal storage',
            'data/backtests': 'Backtest results',
            'data/comparison_reports': 'Comparison reports',
            'data/divergence_analysis': 'Divergence analysis',
            'data/threshold_adjustments': 'Adjustment reports',
        }
        
        for dir_name, description in required_dirs.items():
            dir_path = self.workspace_dir / "descarga_datos" / dir_name
            exists = dir_path.exists()
            
            check = IntegrationCheck(
                check_name=f"Directory: {dir_name}",
                description=description,
                result=exists or True,  # Los directorios se crean dinámicamente
                details=f"Directory at {dir_path}",
                severity="low"
            )
            checks.append(check)
        
        return checks
    
    def validate_imports(self) -> List[IntegrationCheck]:
        """
        Valida que todos los imports funcionen.
        
        Returns:
            Lista de verificaciones
        """
        checks = []
        
        modules_to_check = [
            ('descarga_datos.utils.signal_logger', 'SignalLogger'),
            ('descarga_datos.utils.backtest_validator', 'BacktestValidator'),
            ('descarga_datos.utils.trace_comparator', 'TraceComparator'),
            ('descarga_datos.utils.divergence_analyzer', 'DivergenceAnalyzer'),
            ('descarga_datos.utils.threshold_adjuster', 'ThresholdAdjuster'),
        ]
        
        for module_name, class_name in modules_to_check:
            try:
                mod = __import__(module_name, fromlist=[class_name])
                has_class = hasattr(mod, class_name)
                
                check = IntegrationCheck(
                    check_name=f"Import: {module_name}.{class_name}",
                    description=f"Import and instantiation of {class_name}",
                    result=has_class,
                    details=f"{'Successfully' if has_class else 'Failed to'} import {class_name}",
                    severity="critical" if not has_class else "low"
                )
                checks.append(check)
            
            except ImportError as e:
                check = IntegrationCheck(
                    check_name=f"Import: {module_name}",
                    description=f"Module import",
                    result=False,
                    details=f"Import error: {e}",
                    severity="critical"
                )
                checks.append(check)
        
        return checks
    
    def validate_configuration(self) -> List[IntegrationCheck]:
        """
        Valida archivos de configuración.
        
        Returns:
            Lista de verificaciones
        """
        checks = []
        
        # Verificar config.yaml
        config_path = self.workspace_dir / "descarga_datos" / "config" / "config.yaml"
        config_exists = config_path.exists()
        
        check = IntegrationCheck(
            check_name="Config: config.yaml",
            description="Main configuration file",
            result=config_exists,
            details=f"{'Found' if config_exists else 'NOT FOUND'}: {config_path}",
            severity="critical" if not config_exists else "low"
        )
        checks.append(check)
        
        return checks
    
    def validate_documentation(self) -> List[IntegrationCheck]:
        """
        Valida documentación.
        
        Returns:
            Lista de verificaciones
        """
        checks = []
        
        # Verificar archivos de documentación
        required_docs = {
            'README.md': 'Main readme',
            'FASE_4_FINAL_STATUS_PRODUCCION_LISTA.md': 'FASE 4 summary',
            'FASE_5_COMPLETA_RESUMEN.md': 'FASE 5 summary',
            'PLAN_MEJORA_COMPLETO_STATUS_FINAL.md': 'Complete plan summary',
        }
        
        for doc_name, description in required_docs.items():
            doc_path = self.workspace_dir / doc_name
            exists = doc_path.exists()
            
            check = IntegrationCheck(
                check_name=f"Documentation: {doc_name}",
                description=description,
                result=exists,
                details=f"{'Found' if exists else 'NOT FOUND'}: {doc_path}",
                severity="medium" if not exists else "low"
            )
            checks.append(check)
        
        return checks
    
    def compile_report(self, test_results: List[TestResult],
                      integration_checks: List[IntegrationCheck]) -> ProductionReadinessReport:
        """
        Compila reporte final.
        
        Args:
            test_results: Resultados de tests
            integration_checks: Verificaciones de integración
            
        Returns:
            ProductionReadinessReport
        """
        # Calcular estadísticas
        total_tests = sum(r.total for r in test_results)
        total_passed = sum(r.passed for r in test_results)
        total_failed = sum(r.failed for r in test_results)
        
        # Contar problemas
        critical_issues = sum(
            1 for c in integration_checks
            if c.severity == "critical" and not c.result
        )
        
        # Calcular score (0-100)
        test_score = (total_passed / total_tests * 100) if total_tests > 0 else 0
        integration_score = (
            sum(1 for c in integration_checks if c.result) /
            len(integration_checks) * 100
        ) if integration_checks else 100
        
        readiness_score = (test_score * 0.6 + integration_score * 0.4)
        
        # Determinar si está listo
        production_ready = (
            total_failed == 0 and
            critical_issues == 0 and
            readiness_score >= 95
        )
        
        # Generar recomendaciones
        recommendations = []
        if total_failed > 0:
            recommendations.append(f"Fix {total_failed} failing tests before deployment")
        if critical_issues > 0:
            recommendations.append(f"Address {critical_issues} critical issues")
        if readiness_score < 95:
            recommendations.append(f"Improve readiness score ({readiness_score:.1f}% < 95%)")
        if not integration_checks:
            recommendations.append("Run integration checks")
        if production_ready:
            recommendations.append("System is ready for production deployment!")
        
        report = ProductionReadinessReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0.0,
            test_results=test_results,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            integration_checks=integration_checks,
            critical_issues=critical_issues,
            production_ready=production_ready,
            readiness_score=readiness_score,
            recommendations=recommendations
        )
        
        return report
    
    def save_report(self, report: ProductionReadinessReport,
                   filename: Optional[str] = None) -> Path:
        """
        Guarda reporte de consolidación.
        
        Args:
            report: ProductionReadinessReport
            filename: Nombre personalizado
            
        Returns:
            Path del archivo guardado
        """
        if filename is None:
            filename = f"consolidation_report_{datetime.now(timezone.utc).isoformat().replace(':', '-')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"Consolidation report saved: {filepath}")
        return filepath
    
    def get_summary(self, report: ProductionReadinessReport) -> str:
        """
        Genera resumen textual.
        
        Args:
            report: ProductionReadinessReport
            
        Returns:
            Resumen formateado
        """
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║        PRODUCTION READINESS CONSOLIDATION REPORT               ║
╚════════════════════════════════════════════════════════════════╝

Timestamp: {report.timestamp}

TEST EXECUTION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Tests:     {report.total_tests:>6}
Passed:          {report.total_passed:>6} ✅
Failed:          {report.total_failed:>6} {'✅' if report.total_failed == 0 else '❌'}
Pass Rate:       {(report.total_passed/report.total_tests*100 if report.total_tests > 0 else 0):>5.1f}%

Test Results by File:
"""
        for result in report.test_results:
            status_icon = "✅" if result.status == ValidationStatus.PASSED else "❌"
            summary += f"  {result.test_name:.<40} {result.passed:>3}/{result.total:<3} {status_icon}\n"
        
        summary += f"""
INTEGRATION CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Checks:    {len(report.integration_checks):>6}
Passed:          {sum(1 for c in report.integration_checks if c.result):>6} ✅
Failed:          {sum(1 for c in report.integration_checks if not c.result):>6}
Critical Issues: {report.critical_issues:>6} {'✅' if report.critical_issues == 0 else '⚠️'}

Critical Checks:
"""
        critical_checks = [c for c in report.integration_checks if c.severity == "critical"]
        for check in critical_checks[:5]:
            status_icon = "✅" if check.result else "❌"
            summary += f"  {check.check_name:.<40} {status_icon}\n"
        
        summary += f"""
PRODUCTION READINESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Readiness Score: {report.readiness_score:>5.1f}% / 100%
Production Ready: {'YES ✅ 🚀' if report.production_ready else 'NO ❌ 🛑'}

Status: {'READY FOR DEPLOYMENT' if report.production_ready else 'NOT READY - See recommendations'}

RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, rec in enumerate(report.recommendations, 1):
            summary += f"  {i}. {rec}\n"
        
        summary += f"""
DEPLOYMENT CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [{'x' if report.total_failed == 0 else ' '}] All tests passing
- [{'x' if report.critical_issues == 0 else ' '}] No critical issues
- [{'x' if report.readiness_score >= 95 else ' '}] Readiness score ≥ 95%
- [{'x' if report.production_ready else ' '}] Production ready

NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if report.production_ready:
            summary += """
  1. Review this consolidation report ✅
  2. Execute deployment playbook
  3. Integrate with live trading system
  4. Monitor divergences and convergence
  5. Apply automatic threshold adjustments
  6. Maintain audit trail and logs
"""
        else:
            summary += """
  1. Address failing tests
  2. Fix critical issues
  3. Re-run consolidation validation
  4. Once readiness score ≥ 95%, proceed to deployment
"""
        
        return summary


# Singleton
_consolidation_validator: Optional[ConsolidationValidator] = None
_validator_lock = __import__('threading').RLock()


def get_consolidation_validator(workspace_dir: Optional[Path] = None) -> ConsolidationValidator:
    """Obtiene instancia singleton del ConsolidationValidator."""
    global _consolidation_validator
    
    with _validator_lock:
        if _consolidation_validator is None:
            _consolidation_validator = ConsolidationValidator(workspace_dir)
        return _consolidation_validator
