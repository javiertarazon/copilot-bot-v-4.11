"""
Puerta de promoción para el flujo canónico XAUUSD.
"""

from typing import Any, Dict, Iterable
from config.canonical_defaults import CANONICAL_STRATEGY, CANONICAL_SYMBOL


DEFAULT_REQUIRED_STAGES = ("training", "validation", "final_test", "sandbox_demo")


def _get_live_validation_config(config: Any) -> Dict[str, Any]:
    live_trading = getattr(config, "live_trading", None)
    if live_trading is None:
        return {}
    validation = getattr(live_trading, "validation", {})
    return validation if isinstance(validation, dict) else {}


def _normalize_stage_map(stage_names: Iterable[str], completed: Dict[str, Any]) -> Dict[str, bool]:
    return {stage: bool(completed.get(stage, False)) for stage in stage_names}


def build_validation_report(config: Any) -> Dict[str, Any]:
    validation = _get_live_validation_config(config)

    required_stages = validation.get("required_stages")
    if required_stages is None:
        required_stages = list(DEFAULT_REQUIRED_STAGES)

    completed_raw = validation.get("completed_stages")
    if completed_raw is None:
        completed_raw = {}
    completed_stages = _normalize_stage_map(required_stages, completed_raw)

    promotion_rules = validation.get("promotion_rules")
    if promotion_rules is None:
        promotion_rules = {}

    demo_requires = promotion_rules.get("demo_requires")
    if demo_requires is None:
        demo_requires = ["training", "validation", "final_test"]

    real_requires = promotion_rules.get("real_requires")
    if real_requires is None:
        real_requires = list(DEFAULT_REQUIRED_STAGES)

    allow_real_trading = validation.get("allow_real_trading", False)
    current_stage = validation.get("current_stage", "training")

    missing_demo = [stage for stage in demo_requires if not completed_stages.get(stage, False)]
    missing_real = [stage for stage in real_requires if not completed_stages.get(stage, False)]

    return {
        "symbol": getattr(getattr(config, "live_trading", None), "active_symbol", CANONICAL_SYMBOL),
        "strategy": getattr(getattr(config, "live_trading", None), "active_strategy", CANONICAL_STRATEGY),
        "current_stage": current_stage,
        "required_stages": required_stages,
        "completed_stages": completed_stages,
        "demo_requires": demo_requires,
        "real_requires": real_requires,
        "missing_demo": missing_demo,
        "missing_real": missing_real,
        "allow_real_trading": allow_real_trading,
        "demo_ready": not missing_demo,
        "real_ready": allow_real_trading and not missing_real,
        "config_is_consistent": set(demo_requires).issubset(required_stages)
        and set(real_requires).issubset(required_stages),
    }


def format_validation_report(report: Dict[str, Any]) -> str:
    stage_lines = [
        f"  - {stage}: {'OK' if done else 'PENDIENTE'}"
        for stage, done in report["completed_stages"].items()
    ]
    missing_demo = ", ".join(report["missing_demo"]) if report["missing_demo"] else "ninguna"
    missing_real = ", ".join(report["missing_real"]) if report["missing_real"] else "ninguna"

    return "\n".join(
        [
            "",
            "[VALIDATION] REPORTE DE PROMOCIÓN XAUUSD",
            "=" * 50,
            f"Símbolo: {report['symbol']}",
            f"Estrategia: {report['strategy']}",
            f"Etapa actual: {report['current_stage']}",
            "Etapas completadas:",
            *stage_lines,
            f"Listo para demo: {'SI' if report['demo_ready'] else 'NO'}",
            f"Faltantes para demo: {missing_demo}",
            f"Listo para real: {'SI' if report['real_ready'] else 'NO'}",
            f"Faltantes para real: {missing_real}",
            f"Permiso explícito para real: {'SI' if report['allow_real_trading'] else 'NO'}",
            "=" * 50,
        ]
    )
