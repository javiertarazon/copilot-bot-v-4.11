"""
Gate de validación para promover resultados de backtest a trading live.

Usa los artefactos ya generados en ``data/dashboard_results`` para producir un
reporte homogéneo y decidir si el sistema puede operar en demo/real.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent.parent / "data" / "dashboard_results"


@dataclass
class ValidationThresholds:
    enabled: bool = True
    require_results: bool = True
    min_total_trades: int = 30
    min_win_rate: float = 0.45
    min_profit_factor: float = 1.05
    max_drawdown_pct: float = 15.0
    min_total_pnl: float = 0.0


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _safe_symbol_filename(symbol: str) -> str:
    return symbol.replace("/", "_").replace(":", "_")


def _normalize_percentage(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= numeric_value <= 1:
        return numeric_value * 100
    return numeric_value


def _normalize_win_rate(value: Any) -> Optional[float]:
    return _normalize_percentage(value)


def _pick_metric(source: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return None


def _extract_strategy_metrics(strategy_payload: Dict[str, Any]) -> Dict[str, Optional[float]]:
    metrics = strategy_payload.get("metrics", {}) if isinstance(strategy_payload.get("metrics"), dict) else {}
    merged = {**metrics, **strategy_payload}

    return {
        "total_trades": _pick_metric(merged, "total_trades", "trade_count", "trades_count") or 0,
        "win_rate_pct": _normalize_win_rate(_pick_metric(merged, "win_rate", "winrate")),
        "profit_factor": _pick_metric(merged, "profit_factor", "pf"),
        "max_drawdown_pct": _normalize_percentage(_pick_metric(merged, "max_drawdown", "drawdown", "max_dd")),
        "total_pnl": _pick_metric(merged, "total_pnl", "pnl", "net_profit", "profit") or 0.0,
    }


def _evaluate_strategy(metrics: Dict[str, Optional[float]], thresholds: ValidationThresholds) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    total_trades = int(metrics.get("total_trades") or 0)
    win_rate_pct = metrics.get("win_rate_pct")
    profit_factor = metrics.get("profit_factor")
    max_drawdown_pct = metrics.get("max_drawdown_pct")
    total_pnl = float(metrics.get("total_pnl") or 0.0)

    if total_trades < thresholds.min_total_trades:
        reasons.append(f"trades insuficientes ({total_trades} < {thresholds.min_total_trades})")
    if win_rate_pct is None or win_rate_pct < thresholds.min_win_rate * 100:
        reasons.append(
            f"win rate insuficiente ({0.0 if win_rate_pct is None else win_rate_pct:.2f}% < {thresholds.min_win_rate * 100:.2f}%)"
        )
    if profit_factor is None or float(profit_factor) < thresholds.min_profit_factor:
        reasons.append(
            f"profit factor insuficiente ({0.0 if profit_factor is None else float(profit_factor):.2f} < {thresholds.min_profit_factor:.2f})"
        )
    if max_drawdown_pct is None or max_drawdown_pct > thresholds.max_drawdown_pct:
        reasons.append(
            f"drawdown excesivo ({0.0 if max_drawdown_pct is None else max_drawdown_pct:.2f}% > {thresholds.max_drawdown_pct:.2f}%)"
        )
    if total_pnl < thresholds.min_total_pnl:
        reasons.append(f"PnL insuficiente ({total_pnl:.2f} < {thresholds.min_total_pnl:.2f})")

    return len(reasons) == 0, reasons


def _resolve_thresholds(config: Optional[Dict[str, Any]]) -> ValidationThresholds:
    raw_validation = ((config or {}).get("live_trading", {}) or {}).get("validation", {}) or {}
    supported_keys = {field for field in ValidationThresholds.__dataclass_fields__}
    filtered = {key: value for key, value in raw_validation.items() if key in supported_keys}
    return ValidationThresholds(**filtered)


def build_validation_report(
    config: Optional[Dict[str, Any]] = None,
    results_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    thresholds = _resolve_thresholds(config)
    resolved_results_dir = Path(results_dir) if results_dir else DEFAULT_RESULTS_DIR

    report: Dict[str, Any] = {
        "status": "passed",
        "enabled": thresholds.enabled,
        "results_dir": str(resolved_results_dir),
        "thresholds": asdict(thresholds),
        "global": {},
        "symbols": {},
        "errors": [],
    }

    if not thresholds.enabled:
        report["status"] = "disabled"
        return report

    if not resolved_results_dir.exists():
        report["status"] = "failed"
        report["errors"].append(f"No existe el directorio de resultados: {resolved_results_dir}")
        return report

    summary_path = resolved_results_dir / "global_summary.json"
    if summary_path.exists():
        try:
            summary = _load_json(summary_path)
            global_metrics = summary.get("metrics", {}) if isinstance(summary.get("metrics"), dict) else {}
            report["global"] = {
                "total_pnl": global_metrics.get("total_pnl"),
                "total_trades": global_metrics.get("total_trades"),
                "avg_win_rate_pct": _normalize_win_rate(global_metrics.get("avg_win_rate")),
                "period": summary.get("period", {}),
            }
        except Exception as exc:
            report["errors"].append(f"No se pudo leer global_summary.json: {exc}")

    symbol_files = list(resolved_results_dir.glob("*_results.json"))
    if thresholds.require_results and not symbol_files:
        report["status"] = "failed"
        report["errors"].append("No se encontraron archivos *_results.json para validar")
        return report

    config_backtesting = (config or {}).get("backtesting", {}) or {}
    configured_symbols = config_backtesting.get("symbols", []) or []
    active_strategies = [
        name
        for name, enabled in ((config_backtesting.get("strategies", {}) or {}).items())
        if enabled
    ]

    overall_passed = True
    for symbol in configured_symbols:
        symbol_path = resolved_results_dir / f"{_safe_symbol_filename(symbol)}_results.json"
        if not symbol_path.exists():
            overall_passed = False
            report["symbols"][symbol] = {
                "status": "failed",
                "reason": "archivo de resultados no encontrado",
            }
            continue

        try:
            symbol_payload = _load_json(symbol_path)
        except Exception as exc:
            overall_passed = False
            report["symbols"][symbol] = {
                "status": "failed",
                "reason": f"archivo inválido: {exc}",
            }
            continue

        strategies_payload = symbol_payload.get("strategies", {}) if isinstance(symbol_payload.get("strategies"), dict) else {}
        candidate_items = list(strategies_payload.items())
        if active_strategies:
            filtered_candidates = [item for item in candidate_items if item[0] in active_strategies]
            if filtered_candidates:
                candidate_items = filtered_candidates

        evaluated_candidates = []
        for strategy_name, strategy_payload in candidate_items:
            metrics = _extract_strategy_metrics(strategy_payload if isinstance(strategy_payload, dict) else {})
            passed, reasons = _evaluate_strategy(metrics, thresholds)
            evaluated_candidates.append(
                {
                    "strategy": strategy_name,
                    "passed": passed,
                    "reasons": reasons,
                    "metrics": metrics,
                }
            )

        if not evaluated_candidates:
            overall_passed = False
            report["symbols"][symbol] = {
                "status": "failed",
                "reason": "sin estrategias evaluables",
            }
            continue

        sorted_candidates = sorted(
            evaluated_candidates,
            key=lambda item: (
                item["passed"],
                float(item["metrics"].get("profit_factor") or 0.0),
                float(item["metrics"].get("total_pnl") or 0.0),
            ),
            reverse=True,
        )
        selected = sorted_candidates[0]

        report["symbols"][symbol] = {
            "status": "passed" if selected["passed"] else "failed",
            "selected_strategy": selected["strategy"],
            "selected_metrics": selected["metrics"],
            "reasons": selected["reasons"],
            "candidates": sorted_candidates,
        }

        if not selected["passed"]:
            overall_passed = False

    if configured_symbols and not overall_passed:
        report["errors"].append("Uno o más símbolos no cumplen el gate de validación")

    report["status"] = "passed" if overall_passed and not report["errors"] else "failed"
    return report


def validate_backtest_readiness(
    config: Optional[Dict[str, Any]] = None,
    results_dir: Optional[Path] = None,
) -> Tuple[bool, Dict[str, Any]]:
    report = build_validation_report(config=config, results_dir=results_dir)
    return report.get("status") in {"passed", "disabled"}, report
