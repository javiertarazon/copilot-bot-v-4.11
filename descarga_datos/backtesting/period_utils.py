from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _get_attr(config: Any, key: str, default: Any = None) -> Any:
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def _parse_date(value: str) -> datetime:
    return datetime.strptime(str(value), "%Y-%m-%d")


def normalize_backtest_periods(backtesting_config: Any) -> List[Dict[str, str]]:
    raw_periods = _get_attr(backtesting_config, "periods", []) or []

    if not raw_periods:
        return [
            {
                "name": _get_attr(backtesting_config, "active_period_name", "") or "default",
                "start_date": str(_get_attr(backtesting_config, "start_date")),
                "end_date": str(_get_attr(backtesting_config, "end_date")),
            }
        ]

    normalized: List[Dict[str, str]] = []
    for index, raw_period in enumerate(raw_periods, start=1):
        if not isinstance(raw_period, dict):
            raise ValueError(f"Periodo de backtest inválido en posición {index}: debe ser un objeto")

        start_date = raw_period.get("start_date") or raw_period.get("start")
        end_date = raw_period.get("end_date") or raw_period.get("end")
        if not start_date or not end_date:
            raise ValueError(
                f"Periodo de backtest inválido en posición {index}: requiere start_date y end_date"
            )

        parsed_start = _parse_date(start_date)
        parsed_end = _parse_date(end_date)
        if parsed_end < parsed_start:
            raise ValueError(
                f"Periodo de backtest inválido en posición {index}: "
                f"end_date ({parsed_end.strftime('%Y-%m-%d')}) no puede ser menor que "
                f"start_date ({parsed_start.strftime('%Y-%m-%d')})"
            )

        normalized.append(
            {
                "name": str(raw_period.get("name") or raw_period.get("label") or f"period_{index}"),
                "start_date": parsed_start.strftime("%Y-%m-%d"),
                "end_date": parsed_end.strftime("%Y-%m-%d"),
            }
        )

    return normalized


def get_combined_period_range(backtesting_config: Any) -> Tuple[str, str]:
    periods = normalize_backtest_periods(backtesting_config)
    starts = [_parse_date(period["start_date"]) for period in periods]
    ends = [_parse_date(period["end_date"]) for period in periods]
    return min(starts).strftime("%Y-%m-%d"), max(ends).strftime("%Y-%m-%d")


def calculate_period_consistency(period_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not period_summaries:
        return {
            "periods_tested": 0,
            "profitable_periods": 0,
            "consistently_profitable": False,
            "pnl_range": {"min": 0.0, "max": 0.0},
            "win_rate_range": {"min": 0.0, "max": 0.0},
            "trade_count_range": {"min": 0, "max": 0},
        }

    metrics = [summary.get("metrics", {}) for summary in period_summaries]
    pnl_values = [float(metric.get("total_pnl", 0.0)) for metric in metrics]
    win_rates = [float(metric.get("avg_win_rate", 0.0)) for metric in metrics]
    trades = [int(metric.get("total_trades", 0)) for metric in metrics]
    profitable_periods = sum(1 for pnl in pnl_values if pnl > 0)

    return {
        "periods_tested": len(period_summaries),
        "profitable_periods": profitable_periods,
        "consistently_profitable": profitable_periods == len(period_summaries),
        "pnl_range": {"min": min(pnl_values), "max": max(pnl_values)},
        "win_rate_range": {"min": min(win_rates), "max": max(win_rates)},
        "trade_count_range": {"min": min(trades), "max": max(trades)},
    }


def build_period_summary(
    *,
    config: Any,
    total_symbols: int,
    total_pnl: float,
    total_trades: int,
    avg_win_rate: float,
    timestamp: str | None = None,
) -> Dict[str, Any]:
    backtesting_config = config.get("backtesting", {}) if isinstance(config, dict) else config.backtesting
    period_label = _get_attr(backtesting_config, "active_period_name", "") or (
        f"{_get_attr(backtesting_config, 'start_date')}→{_get_attr(backtesting_config, 'end_date')}"
    )

    return {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "period_label": period_label,
        "total_symbols": total_symbols,
        "period": {
            "start_date": str(_get_attr(backtesting_config, "start_date")),
            "end_date": str(_get_attr(backtesting_config, "end_date")),
            "timeframe": str(_get_attr(backtesting_config, "timeframe")),
        },
        "metrics": {
            "total_pnl": float(total_pnl),
            "total_trades": int(total_trades),
            "avg_win_rate": float(avg_win_rate),
        },
    }


def build_multi_period_summary(
    period_summaries: List[Dict[str, Any]], timestamp: str | None = None
) -> Dict[str, Any]:
    if not period_summaries:
        return {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "multi_period": True,
            "periods": [],
            "consistency": calculate_period_consistency([]),
        }

    latest_summary = dict(period_summaries[-1])
    latest_summary["timestamp"] = timestamp or datetime.now(timezone.utc).isoformat()
    latest_summary["multi_period"] = len(period_summaries) > 1
    latest_summary["periods"] = period_summaries
    latest_summary["consistency"] = calculate_period_consistency(period_summaries)
    return latest_summary
