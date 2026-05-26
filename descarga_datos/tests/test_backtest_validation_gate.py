#!/usr/bin/env python3
"""
Tests unitarios para el gate de validación backtest/live.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_management.backtest_validation_gate import build_validation_report, validate_backtest_readiness


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_validation_gate_passes_with_valid_metrics(tmp_path):
    results_dir = tmp_path / "dashboard_results"
    _write_json(
        results_dir / "global_summary.json",
        {
            "metrics": {
                "total_pnl": 1250.0,
                "total_trades": 80,
                "avg_win_rate": 0.61,
            }
        },
    )
    _write_json(
        results_dir / "EURUSD_results.json",
        {
            "symbol": "EURUSD",
            "strategies": {
                "UltraDetailedHeikinAshiML": {
                    "total_trades": 80,
                    "win_rate": 0.61,
                    "profit_factor": 1.48,
                    "max_drawdown": 0.09,
                    "total_pnl": 1250.0,
                }
            },
        },
    )

    config = {
        "backtesting": {
            "symbols": ["EURUSD"],
            "strategies": {"UltraDetailedHeikinAshiML": True},
        },
        "live_trading": {
            "validation": {
                "enabled": True,
                "min_total_trades": 30,
                "min_win_rate": 0.45,
                "min_profit_factor": 1.05,
                "max_drawdown_pct": 15.0,
                "min_total_pnl": 0.0,
            }
        },
    }

    is_ready, report = validate_backtest_readiness(config=config, results_dir=results_dir)

    assert is_ready is True
    assert report["status"] == "passed"
    assert report["symbols"]["EURUSD"]["selected_strategy"] == "UltraDetailedHeikinAshiML"


def test_validation_gate_fails_when_symbol_metrics_do_not_meet_thresholds(tmp_path):
    results_dir = tmp_path / "dashboard_results"
    _write_json(
        results_dir / "EURUSD_results.json",
        {
            "symbol": "EURUSD",
            "strategies": {
                "UltraDetailedHeikinAshiML": {
                    "total_trades": 5,
                    "win_rate": 0.30,
                    "profit_factor": 0.9,
                    "max_drawdown": 0.22,
                    "total_pnl": -50.0,
                }
            },
        },
    )

    report = build_validation_report(
        config={
            "backtesting": {
                "symbols": ["EURUSD"],
                "strategies": {"UltraDetailedHeikinAshiML": True},
            },
            "live_trading": {"validation": {"enabled": True}},
        },
        results_dir=results_dir,
    )

    assert report["status"] == "failed"
    assert report["symbols"]["EURUSD"]["status"] == "failed"
    assert report["errors"]
