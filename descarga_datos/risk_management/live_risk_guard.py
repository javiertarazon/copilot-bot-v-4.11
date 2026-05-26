"""
Controles globales de riesgo para trading live.

Evalúa límites diarios/semanales, correlación entre posiciones, spread,
volatilidad intrabar y kill-switch por drawdown global.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _sum_closed_profit(position_history: Any, period: str, now: datetime) -> float:
    total = 0.0
    for position in position_history or []:
        close_time = _parse_datetime(position.get("close_time"))
        if close_time is None:
            continue

        same_period = False
        if period == "day":
            same_period = close_time.date() == now.date()
        elif period == "week":
            close_year, close_week, _ = close_time.isocalendar()
            now_year, now_week, _ = now.isocalendar()
            same_period = (close_year, close_week) == (now_year, now_week)

        if same_period:
            total += float(position.get("profit", 0.0) or 0.0)

    return total


def _resolve_baseline_balance(account_info: Dict[str, Any], baseline_balance: Optional[float]) -> float:
    for candidate in (
        baseline_balance,
        account_info.get("baseline_balance"),
        account_info.get("balance"),
        account_info.get("equity"),
    ):
        try:
            if candidate is not None:
                return float(candidate)
        except (TypeError, ValueError):
            continue
    return 0.0


def _find_correlation_group(symbol: str, groups: Dict[str, Any]) -> Optional[str]:
    for group_name, group_symbols in (groups or {}).items():
        if symbol in (group_symbols or []):
            return group_name
    return None


def _count_correlated_positions(symbol: str, active_positions: Dict[str, Any], groups: Dict[str, Any]) -> int:
    target_group = _find_correlation_group(symbol, groups)
    if not target_group:
        return 0

    total = 0
    for position in (active_positions or {}).values():
        position_symbol = position.get("symbol")
        if position_symbol and _find_correlation_group(position_symbol, groups) == target_group:
            total += 1
    return total


def _get_spread_limit(symbol: str, spread_filter: Dict[str, Any]) -> Optional[float]:
    spread_limits = spread_filter.get("max_spread_points")
    if isinstance(spread_limits, dict):
        return spread_limits.get(symbol, spread_limits.get("default"))
    if spread_limits is None:
        return None
    return float(spread_limits)


def _calculate_candle_range_pct(market_context: Dict[str, Any], fallback_price: Optional[float]) -> Optional[float]:
    high = market_context.get("high")
    low = market_context.get("low")
    close = market_context.get("close", fallback_price)

    try:
        high_value = float(high)
        low_value = float(low)
        close_value = float(close)
    except (TypeError, ValueError):
        return None

    if close_value <= 0:
        return None

    return abs(high_value - low_value) / close_value * 100


def evaluate_live_risk(
    signal: Dict[str, Any],
    active_positions: Dict[str, Any],
    position_history: Any,
    account_info: Dict[str, Any],
    live_config: Dict[str, Any],
    market_state: Optional[Dict[str, Any]] = None,
    baseline_balance: Optional[float] = None,
    kill_switch_active: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    controls = (live_config or {}).get("risk_controls", {}) or {}
    result: Dict[str, Any] = {
        "approved": True,
        "rejected": False,
        "rejection_reason": "",
        "kill_switch_triggered": False,
        "checks": {},
    }

    if not controls:
        return result

    now = now or datetime.now()
    symbol = signal.get("symbol", "")
    baseline = _resolve_baseline_balance(account_info or {}, baseline_balance)
    balance = float(account_info.get("balance", baseline) or baseline or 0.0)
    equity = float(account_info.get("equity", balance) or balance or 0.0)
    reference_balance = baseline or balance or equity

    def reject(reason: str, check_name: str, trigger_kill_switch: bool = False) -> Dict[str, Any]:
        result["approved"] = False
        result["rejected"] = True
        result["rejection_reason"] = reason
        result["failed_check"] = check_name
        result["kill_switch_triggered"] = trigger_kill_switch
        return result

    manual_kill_switch = bool(controls.get("manual_kill_switch", False))
    if kill_switch_active or manual_kill_switch:
        return reject("Kill-switch activo", "kill_switch", True)

    max_account_drawdown_pct = float(
        controls.get(
            "max_account_drawdown_pct",
            float(live_config.get("max_account_drawdown", 0.05) or 0.05) * 100,
        )
    )
    current_drawdown_pct = 0.0
    if reference_balance > 0:
        current_drawdown_pct = max((reference_balance - equity) / reference_balance * 100, 0.0)
    result["checks"]["current_drawdown_pct"] = current_drawdown_pct

    if bool(controls.get("kill_switch_enabled", True)) and current_drawdown_pct >= max_account_drawdown_pct:
        return reject(
            f"Drawdown global excedido ({current_drawdown_pct:.2f}% >= {max_account_drawdown_pct:.2f}%)",
            "max_account_drawdown_pct",
            True,
        )

    daily_pnl = _sum_closed_profit(position_history, "day", now)
    weekly_pnl = _sum_closed_profit(position_history, "week", now)
    result["checks"]["daily_realized_pnl"] = daily_pnl
    result["checks"]["weekly_realized_pnl"] = weekly_pnl

    max_daily_loss_pct = float(controls.get("max_daily_loss_pct", 0.0) or 0.0)
    max_weekly_loss_pct = float(controls.get("max_weekly_loss_pct", 0.0) or 0.0)
    if reference_balance > 0 and max_daily_loss_pct > 0:
        max_daily_loss = reference_balance * max_daily_loss_pct / 100
        result["checks"]["max_daily_loss"] = max_daily_loss
        if daily_pnl <= -max_daily_loss:
            return reject(
                f"Límite diario excedido ({daily_pnl:.2f} <= {-max_daily_loss:.2f})",
                "max_daily_loss_pct",
                True,
            )

    if reference_balance > 0 and max_weekly_loss_pct > 0:
        max_weekly_loss = reference_balance * max_weekly_loss_pct / 100
        result["checks"]["max_weekly_loss"] = max_weekly_loss
        if weekly_pnl <= -max_weekly_loss:
            return reject(
                f"Límite semanal excedido ({weekly_pnl:.2f} <= {-max_weekly_loss:.2f})",
                "max_weekly_loss_pct",
                True,
            )

    correlation_groups = controls.get("correlation_groups", {}) or {}
    correlated_positions = _count_correlated_positions(symbol, active_positions, correlation_groups)
    max_correlated_positions = int(controls.get("max_positions_per_correlation_group", 0) or 0)
    result["checks"]["correlated_positions"] = correlated_positions
    if max_correlated_positions > 0 and correlated_positions >= max_correlated_positions:
        return reject(
            f"Exposición correlacionada excedida ({correlated_positions} >= {max_correlated_positions})",
            "max_positions_per_correlation_group",
        )

    spread_filter = controls.get("spread_filter", {}) or {}
    if spread_filter.get("enabled", False):
        spread_limit = _get_spread_limit(symbol, spread_filter)
        spread_value = None if market_state is None else market_state.get("spread")
        result["checks"]["spread"] = spread_value
        result["checks"]["spread_limit"] = spread_limit
        if spread_limit is not None and spread_value is not None and float(spread_value) > float(spread_limit):
            return reject(
                f"Spread excesivo ({float(spread_value):.2f} > {float(spread_limit):.2f})",
                "spread_filter",
            )

    volatility_filter = controls.get("volatility_filter", {}) or {}
    market_context = signal.get("market_context", {}) or {}
    candle_range_pct = _calculate_candle_range_pct(market_context, signal.get("price"))
    result["checks"]["candle_range_pct"] = candle_range_pct
    if volatility_filter.get("enabled", False):
        max_candle_range_pct = float(volatility_filter.get("max_candle_range_pct", 0.0) or 0.0)
        result["checks"]["max_candle_range_pct"] = max_candle_range_pct
        if candle_range_pct is not None and max_candle_range_pct > 0 and candle_range_pct > max_candle_range_pct:
            return reject(
                f"Volatilidad intrabar excesiva ({candle_range_pct:.2f}% > {max_candle_range_pct:.2f}%)",
                "volatility_filter",
            )

    return result
