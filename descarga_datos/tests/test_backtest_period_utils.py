from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

from descarga_datos.backtesting.period_utils import (
    build_multi_period_summary,
    build_period_summary,
    get_combined_period_range,
    normalize_backtest_periods,
)
from descarga_datos.config.config_loader import BacktestingConfig, Config


def test_normalize_backtest_periods_uses_configured_ranges():
    backtesting = BacktestingConfig(
        timeframe="15m",
        start_date="2019-01-01",
        end_date="2019-12-31",
        periods=[
            {"name": "in_sample", "start_date": "2020-01-01", "end_date": "2020-06-30"},
            {"name": "out_sample", "start_date": "2020-07-01", "end_date": "2020-12-31"},
        ],
    )

    periods = normalize_backtest_periods(backtesting)

    assert periods == [
        {"name": "in_sample", "start_date": "2020-01-01", "end_date": "2020-06-30"},
        {"name": "out_sample", "start_date": "2020-07-01", "end_date": "2020-12-31"},
    ]
    assert get_combined_period_range(backtesting) == ("2020-01-01", "2020-12-31")


def test_normalize_backtest_periods_falls_back_to_single_range():
    backtesting = BacktestingConfig(
        timeframe="15m",
        start_date="2019-01-01",
        end_date="2019-12-31",
    )

    assert normalize_backtest_periods(backtesting) == [
        {"name": "default", "start_date": "2019-01-01", "end_date": "2019-12-31"}
    ]


def test_build_multi_period_summary_reports_consistency():
    config = Config()
    config.backtesting.start_date = "2020-01-01"
    config.backtesting.end_date = "2020-06-30"
    config.backtesting.timeframe = "15m"
    config.backtesting.active_period_name = "period_a"

    period_a = build_period_summary(
        config=config,
        total_symbols=1,
        total_pnl=120.0,
        total_trades=8,
        avg_win_rate=62.5,
        timestamp="2026-01-01T00:00:00+00:00",
    )

    config.backtesting.start_date = "2020-07-01"
    config.backtesting.end_date = "2020-12-31"
    config.backtesting.active_period_name = "period_b"
    period_b = build_period_summary(
        config=config,
        total_symbols=1,
        total_pnl=80.0,
        total_trades=6,
        avg_win_rate=58.0,
        timestamp="2026-01-02T00:00:00+00:00",
    )

    combined = build_multi_period_summary([period_a, period_b], timestamp="2026-01-03T00:00:00+00:00")

    assert combined["multi_period"] is True
    assert combined["consistency"]["periods_tested"] == 2
    assert combined["consistency"]["profitable_periods"] == 2
    assert combined["consistency"]["consistently_profitable"] is True
    assert combined["consistency"]["pnl_range"] == {"min": 80.0, "max": 120.0}
    assert combined["periods"][0]["period_label"] == "period_a"
    assert combined["periods"][1]["period_label"] == "period_b"
