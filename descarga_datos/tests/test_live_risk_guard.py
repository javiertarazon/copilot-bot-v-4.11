#!/usr/bin/env python3
"""
Tests unitarios para controles globales de riesgo live.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_management.live_risk_guard import evaluate_live_risk


def _live_config():
    return {
        "max_account_drawdown": 0.05,
        "risk_controls": {
            "kill_switch_enabled": True,
            "manual_kill_switch": False,
            "max_daily_loss_pct": 2.0,
            "max_weekly_loss_pct": 4.0,
            "max_account_drawdown_pct": 5.0,
            "max_positions_per_correlation_group": 2,
            "correlation_groups": {
                "majors": ["EURUSD", "GBPUSD", "AUDUSD"],
            },
            "spread_filter": {
                "enabled": True,
                "max_spread_points": {"default": 35, "EURUSD": 25},
            },
            "volatility_filter": {
                "enabled": True,
                "max_candle_range_pct": 1.5,
            },
        },
    }


def test_live_risk_guard_rejects_daily_loss_limit():
    result = evaluate_live_risk(
        signal={"symbol": "EURUSD", "price": 1.10, "market_context": {"high": 1.11, "low": 1.09, "close": 1.10}},
        active_positions={},
        position_history=[
            {"profit": -250.0, "close_time": datetime(2026, 5, 26, 10, 0, 0)},
        ],
        account_info={"balance": 10_000.0, "equity": 9_800.0},
        live_config=_live_config(),
        market_state={"spread": 10},
        baseline_balance=10_000.0,
        now=datetime(2026, 5, 26, 12, 0, 0),
    )

    assert result["rejected"] is True
    assert result["kill_switch_triggered"] is True
    assert result["failed_check"] == "max_daily_loss_pct"


def test_live_risk_guard_rejects_correlation_spread_and_volatility():
    result = evaluate_live_risk(
        signal={"symbol": "AUDUSD", "price": 0.67, "market_context": {"high": 0.69, "low": 0.66, "close": 0.67}},
        active_positions={
            "1": {"symbol": "EURUSD"},
            "2": {"symbol": "GBPUSD"},
        },
        position_history=[],
        account_info={"balance": 10_000.0, "equity": 9_950.0},
        live_config=_live_config(),
        market_state={"spread": 40},
        baseline_balance=10_000.0,
        now=datetime(2026, 5, 26, 12, 0, 0),
    )

    assert result["rejected"] is True
    assert result["failed_check"] == "max_positions_per_correlation_group"


def test_live_risk_guard_accepts_signal_inside_limits():
    result = evaluate_live_risk(
        signal={"symbol": "EURUSD", "price": 1.10, "market_context": {"high": 1.105, "low": 1.095, "close": 1.10}},
        active_positions={"1": {"symbol": "USDJPY"}},
        position_history=[],
        account_info={"balance": 10_000.0, "equity": 9_950.0},
        live_config=_live_config(),
        market_state={"spread": 12},
        baseline_balance=10_000.0,
        now=datetime(2026, 5, 26, 12, 0, 0),
    )

    assert result["approved"] is True
    assert result["rejected"] is False
