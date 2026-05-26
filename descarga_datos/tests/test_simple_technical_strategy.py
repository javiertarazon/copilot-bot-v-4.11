#!/usr/bin/env python3
"""
Tests focalizados para la estrategia técnica simple.
"""

from types import SimpleNamespace
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backtesting.backtesting_orchestrator import load_strategies_from_config
from core.downloader import AdvancedDataDownloader
from strategies.simple_technical_strategy import SimpleTechnicalStrategy


def _build_test_config():
    return SimpleNamespace(
        backtesting=SimpleNamespace(
            symbols=["EURUSD"],
            timeframe="4h",
            initial_capital=1000.0,
            commission=0.1,
            slippage=0.05,
            strategies={"SimpleTechnical": True},
            base_parameters={
                "risk_per_trade": 0.02,
                "max_drawdown_limit": 0.2,
                "simple_fast_ema": 10,
                "simple_slow_ema": 20,
                "simple_trend_ema": 50,
                "simple_adx_threshold": 10,
                "simple_rsi_buy_min": 52,
                "simple_rsi_sell_max": 48,
                "simple_stop_loss_atr_multiplier": 1.4,
                "simple_take_profit_atr_multiplier": 2.4,
                "simple_max_bars_in_trade": 8,
            },
            optimized_parameters={},
        )
    )


def _build_market_data(rows=220):
    index = pd.date_range("2025-01-01", periods=rows, freq="4h")
    base = np.linspace(1.05, 1.25, rows)
    cycle = 0.015 * np.sin(np.linspace(0, 10 * np.pi, rows))
    close = base + cycle
    close[90:140] += np.linspace(-0.03, 0.05, 50)
    close[140:190] += np.linspace(0.04, -0.03, 50)
    open_ = np.roll(close, 1)
    open_[0] = close[0] - 0.001
    high = np.maximum(open_, close) + 0.004
    low = np.minimum(open_, close) - 0.004
    volume = np.linspace(100, 200, rows)
    volume[110:150] *= 1.5
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def test_strategy_loader_recovers_simple_technical():
    config = _build_test_config()
    strategies = load_strategies_from_config(config)

    assert "SimpleTechnical" in strategies
    assert isinstance(strategies["SimpleTechnical"], SimpleTechnicalStrategy)


def test_simple_technical_live_signal_uses_canonical_format():
    strategy = SimpleTechnicalStrategy(config=_build_test_config(), initial_balance=1000.0)
    signal = strategy.get_live_signal(_build_market_data(), "EURUSD", "4h")

    assert set(signal.keys()) >= {"signal", "signal_data", "symbol", "strategy_name", "ml_confidence"}
    assert signal["strategy_name"] == "SimpleTechnicalStrategy"
    assert signal["symbol"] == "EURUSD"


def test_simple_technical_backtest_returns_trades_and_equity_curve():
    strategy = SimpleTechnicalStrategy(config=_build_test_config(), initial_balance=1000.0)
    result = strategy.run(_build_market_data(), "EURUSD", "4h")

    assert "trades" in result
    assert "equity_curve" in result
    assert isinstance(result["equity_curve"], pd.Series)
    assert isinstance(result["trades"], list)


def test_advanced_downloader_honors_mt5_only_mode():
    config = SimpleNamespace(
        mt5=SimpleNamespace(enabled=True),
        data=SimpleNamespace(use_ccxt_for_crypto=False),
        storage=SimpleNamespace(path=str(REPO_ROOT / "data")),
        backtesting=SimpleNamespace(data_quality=None),
        active_exchange=None,
        max_retries=1,
        retry_delay=0,
    )

    downloader = AdvancedDataDownloader(config)

    assert downloader._mt5_only_mode_enabled() is True
