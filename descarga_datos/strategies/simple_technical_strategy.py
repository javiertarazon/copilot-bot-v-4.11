#!/usr/bin/env python3
"""
SimpleTechnicalStrategy
=======================

Estrategia técnica interpretable para usar como benchmark canónico frente a la
estrategia ML. Comparte el mismo flujo de datos OHLCV y la misma estructura de
señales entre backtest y live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy
from utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class TradeSignal:
    direction: str
    confidence: float
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    atr: float
    timestamp: object


class SimpleTechnicalStrategy(BaseStrategy):
    """Estrategia técnica simple y auditable basada en tendencia + momentum."""

    strategy_name = "SimpleTechnical"

    def __init__(self, config=None, initial_balance=None):
        resolved_config = self._resolve_strategy_config(config)
        super().__init__(resolved_config)
        self.logger = get_logger("simple_technical_strategy")
        self.config = resolved_config

        self.symbol = resolved_config.get("symbol", "EURUSD")
        self.timeframe = resolved_config.get("timeframe", "4h")
        self.initial_balance = float(initial_balance or resolved_config.get("initial_capital", 10000.0))

        self.fast_ema = int(resolved_config.get("simple_fast_ema", 10))
        self.slow_ema = int(resolved_config.get("simple_slow_ema", 20))
        self.trend_ema = int(resolved_config.get("simple_trend_ema", 50))
        self.adx_threshold = float(resolved_config.get("simple_adx_threshold", 20.0))
        self.rsi_buy_min = float(resolved_config.get("simple_rsi_buy_min", 55.0))
        self.rsi_sell_max = float(resolved_config.get("simple_rsi_sell_max", 45.0))
        self.stop_loss_atr_multiplier = float(resolved_config.get("simple_stop_loss_atr_multiplier", 1.6))
        self.take_profit_atr_multiplier = float(resolved_config.get("simple_take_profit_atr_multiplier", 2.6))
        self.max_bars_in_trade = int(resolved_config.get("simple_max_bars_in_trade", 12))
        self.min_bars = max(self.trend_ema + 5, 60)
        self.commission_rate = self._normalize_rate(resolved_config.get("commission", 0.0))
        self.slippage_rate = self._normalize_rate(resolved_config.get("slippage", 0.0))

    def _resolve_strategy_config(self, config) -> Dict:
        if config is None:
            return {}

        if isinstance(config, dict):
            backtesting = config.get("backtesting", {})
            symbol = (backtesting.get("symbols") or ["EURUSD"])[0]
            return {
                "symbol": symbol,
                "timeframe": backtesting.get("timeframe", "4h"),
                "initial_capital": backtesting.get("initial_capital", 10000.0),
                "commission": backtesting.get("commission", 0.0),
                "slippage": backtesting.get("slippage", 0.0),
                **backtesting.get("base_parameters", {}),
                **backtesting.get("optimized_parameters", {}).get(symbol, {}),
            }

        if hasattr(config, "backtesting"):
            symbol = config.backtesting.symbols[0] if getattr(config.backtesting, "symbols", None) else "EURUSD"
            resolved = {
                "symbol": symbol,
                "timeframe": getattr(config.backtesting, "timeframe", "4h"),
                "initial_capital": getattr(config.backtesting, "initial_capital", 10000.0),
                "commission": getattr(config.backtesting, "commission", 0.0),
                "slippage": getattr(config.backtesting, "slippage", 0.0),
            }
            base_parameters = getattr(config.backtesting, "base_parameters", {}) or {}
            optimized_parameters = getattr(config.backtesting, "optimized_parameters", {}) or {}
            symbol_parameters = optimized_parameters.get(symbol, {}) if isinstance(optimized_parameters, dict) else {}
            resolved.update(base_parameters)
            if isinstance(symbol_parameters, dict):
                resolved.update(symbol_parameters)
            return resolved

        return dict(config)

    @staticmethod
    def _normalize_rate(raw_value: Optional[float]) -> float:
        value = float(raw_value or 0.0)
        if value > 0.01:
            return value / 100.0
        return value

    def _prepare_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None or data.empty:
            return pd.DataFrame()

        prepared = data.copy()

        if "timestamp" in prepared.columns:
            prepared["timestamp"] = pd.to_datetime(prepared["timestamp"])
            prepared = prepared.set_index("timestamp")

        prepared.index = pd.to_datetime(prepared.index)
        prepared = prepared.sort_index()

        if "volume" not in prepared.columns:
            prepared["volume"] = 0.0

        prepared = self.calculate_indicators(prepared)
        if "adx" not in prepared.columns:
            prepared["adx"] = self.indicators.calculate_adx(prepared)
        if "atr" not in prepared.columns:
            prepared["atr"] = self.indicators.calculate_atr(prepared)
        if "sar" not in prepared.columns:
            prepared["sar"] = self.indicators.calculate_sar(prepared)
        prepared = prepared.replace([np.inf, -np.inf], np.nan)
        prepared["volume_ratio"] = prepared.get("volume_ratio", 1.0)
        prepared["volume_ratio"] = prepared["volume_ratio"].replace([np.inf, -np.inf], np.nan).fillna(1.0)

        required_columns = [
            "open",
            "high",
            "low",
            "close",
            "atr",
            f"ema_{self.fast_ema}",
            f"ema_{self.slow_ema}",
            f"ema_{self.trend_ema}",
            "rsi",
            "adx",
            "macd",
            "macd_signal",
            "sar",
        ]
        prepared = prepared.dropna(subset=[column for column in required_columns if column in prepared.columns])
        return prepared

    def _calculate_confidence(self, row: pd.Series, direction: str) -> float:
        adx_score = min(max((float(row["adx"]) - self.adx_threshold) / 25.0, 0.0), 1.0)
        rsi = float(row["rsi"])
        if direction == "BUY":
            rsi_score = min(max((rsi - 50.0) / 30.0, 0.0), 1.0)
        else:
            rsi_score = min(max((50.0 - rsi) / 30.0, 0.0), 1.0)
        return round(min(0.99, 0.45 + (adx_score * 0.3) + (rsi_score * 0.25)), 4)

    def _build_signal_for_index(self, data: pd.DataFrame, index: int) -> Optional[TradeSignal]:
        if index <= 0 or index >= len(data):
            return None

        row = data.iloc[index]
        previous_row = data.iloc[index - 1]

        atr_value = float(row["atr"])
        if not np.isfinite(atr_value) or atr_value <= 0:
            return None

        ema_fast = f"ema_{self.fast_ema}"
        ema_slow = f"ema_{self.slow_ema}"
        ema_trend = f"ema_{self.trend_ema}"

        crossed_up = row[ema_fast] > row[ema_slow] and previous_row[ema_fast] <= previous_row[ema_slow]
        crossed_down = row[ema_fast] < row[ema_slow] and previous_row[ema_fast] >= previous_row[ema_slow]

        long_conditions = (
            crossed_up
            and row[ema_slow] > row[ema_trend]
            and row["close"] > row["sar"]
            and row["macd"] >= row["macd_signal"]
            and row["rsi"] >= self.rsi_buy_min
            and row["adx"] >= self.adx_threshold
        )
        short_conditions = (
            crossed_down
            and row[ema_slow] < row[ema_trend]
            and row["close"] < row["sar"]
            and row["macd"] <= row["macd_signal"]
            and row["rsi"] <= self.rsi_sell_max
            and row["adx"] >= self.adx_threshold
        )

        if not long_conditions and not short_conditions:
            return None

        direction = "BUY" if long_conditions else "SELL"
        entry_price = float(row["close"])
        stop_distance = max(atr_value * self.stop_loss_atr_multiplier, entry_price * 0.001)
        take_profit_distance = max(atr_value * self.take_profit_atr_multiplier, stop_distance * 1.4)

        if direction == "BUY":
            stop_loss_price = entry_price - stop_distance
            take_profit_price = entry_price + take_profit_distance
        else:
            stop_loss_price = entry_price + stop_distance
            take_profit_price = entry_price - take_profit_distance

        return TradeSignal(
            direction=direction,
            confidence=self._calculate_confidence(row, direction),
            entry_price=entry_price,
            stop_loss_price=float(stop_loss_price),
            take_profit_price=float(take_profit_price),
            atr=atr_value,
            timestamp=data.index[index],
        )

    def _format_live_signal(self, signal: Optional[TradeSignal], account_balance: float, symbol: str) -> Dict:
        if signal is None:
            return {
                "signal": "NO_SIGNAL",
                "signal_data": {},
                "symbol": symbol,
                "strategy_name": "SimpleTechnicalStrategy",
                "ml_confidence": 0.0,
                "reason": "no_signal",
            }

        direction = signal.direction.lower()
        position_size = self.calculate_position_size(
            signal.entry_price,
            signal.stop_loss_price,
            account_balance,
            direction,
        )
        if position_size <= 0:
            return {
                "signal": "NO_SIGNAL",
                "signal_data": {},
                "symbol": symbol,
                "strategy_name": "SimpleTechnicalStrategy",
                "ml_confidence": 0.0,
                "reason": "invalid_position_size",
            }

        return {
            "signal": signal.direction,
            "signal_data": {
                "entry_price": signal.entry_price,
                "stop_loss_price": signal.stop_loss_price,
                "take_profit_price": signal.take_profit_price,
                "atr": signal.atr,
                "risk_per_trade": self.max_risk_per_trade,
                "position_size": position_size,
                "timestamp": signal.timestamp,
            },
            "symbol": symbol,
            "strategy_name": "SimpleTechnicalStrategy",
            "ml_confidence": signal.confidence,
        }

    def get_live_signal(self, data: pd.DataFrame, symbol: str, timeframe: str = "4h") -> Dict:
        prepared = self._prepare_market_data(data)
        if len(prepared) < self.min_bars:
            return {
                "signal": "NO_SIGNAL",
                "signal_data": {},
                "symbol": symbol,
                "strategy_name": "SimpleTechnicalStrategy",
                "ml_confidence": 0.0,
                "reason": "insufficient_data",
            }

        signal = self._build_signal_for_index(prepared, len(prepared) - 1)
        return self._format_live_signal(signal, self.initial_balance, symbol)

    def _calculate_trade_pnl(self, position: Dict, exit_price: float) -> Dict[str, float]:
        direction_multiplier = 1 if position["direction"] == "BUY" else -1
        gross_pnl = (exit_price - position["entry_price"]) * position["position_size"] * direction_multiplier
        commission = (
            (position["entry_price"] * position["position_size"] * self.commission_rate)
            + (exit_price * position["position_size"] * self.commission_rate)
        )
        slippage = (
            (position["entry_price"] * position["position_size"] * self.slippage_rate)
            + (exit_price * position["position_size"] * self.slippage_rate)
        )
        return {
            "pnl": gross_pnl - commission - slippage,
            "commission": commission,
            "slippage": slippage,
        }

    def run(self, data: pd.DataFrame, symbol: str, timeframe: str = "4h") -> Dict:
        prepared = self._prepare_market_data(data)
        if len(prepared) < self.min_bars:
            return {"trades": [], "equity_curve": pd.Series(dtype=float)}

        trades = []
        balance = self.initial_balance
        peak_balance = balance
        equity_curve = [balance]
        open_position = None

        for index in range(self.min_bars, len(prepared)):
            row = prepared.iloc[index]
            signal = self._build_signal_for_index(prepared, index)

            if open_position:
                bars_held = index - open_position["entry_index"]
                exit_reason = None
                exit_price = None

                if open_position["direction"] == "BUY":
                    if row["low"] <= open_position["stop_loss"]:
                        exit_reason = "stop_loss"
                        exit_price = open_position["stop_loss"]
                    elif row["high"] >= open_position["take_profit"]:
                        exit_reason = "take_profit"
                        exit_price = open_position["take_profit"]
                    elif signal and signal.direction == "SELL":
                        exit_reason = "signal_reversal"
                        exit_price = float(row["close"])
                else:
                    if row["high"] >= open_position["stop_loss"]:
                        exit_reason = "stop_loss"
                        exit_price = open_position["stop_loss"]
                    elif row["low"] <= open_position["take_profit"]:
                        exit_reason = "take_profit"
                        exit_price = open_position["take_profit"]
                    elif signal and signal.direction == "BUY":
                        exit_reason = "signal_reversal"
                        exit_price = float(row["close"])

                if exit_reason is None and bars_held >= self.max_bars_in_trade:
                    exit_reason = "time_exit"
                    exit_price = float(row["close"])

                if exit_reason is not None and exit_price is not None:
                    pnl_info = self._calculate_trade_pnl(open_position, float(exit_price))
                    balance += pnl_info["pnl"]
                    peak_balance = max(peak_balance, balance)
                    trades.append(
                        {
                            "entry_time": open_position["entry_time"],
                            "exit_time": prepared.index[index],
                            "entry_price": open_position["entry_price"],
                            "exit_price": float(exit_price),
                            "position_size": open_position["position_size"],
                            "pnl": pnl_info["pnl"],
                            "type": "long" if open_position["direction"] == "BUY" else "short",
                            "symbol": symbol,
                            "exit_reason": exit_reason,
                            "commission": pnl_info["commission"],
                            "slippage": pnl_info["slippage"],
                            "stop_loss": open_position["stop_loss"],
                            "take_profit": open_position["take_profit"],
                            "signal_confidence": open_position["signal_confidence"],
                        }
                    )
                    equity_curve.append(balance)
                    open_position = None

            if open_position is not None or signal is None:
                continue

            current_drawdown = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0.0
            if not self.validate_risk_conditions(balance, current_drawdown):
                continue

            position_payload = self._format_live_signal(signal, balance, symbol)
            if position_payload["signal"] == "NO_SIGNAL":
                continue

            open_position = {
                "entry_index": index,
                "entry_time": prepared.index[index],
                "entry_price": signal.entry_price,
                "direction": signal.direction,
                "position_size": position_payload["signal_data"]["position_size"],
                "stop_loss": signal.stop_loss_price,
                "take_profit": signal.take_profit_price,
                "signal_confidence": signal.confidence,
            }

        if open_position:
            final_row = prepared.iloc[-1]
            pnl_info = self._calculate_trade_pnl(open_position, float(final_row["close"]))
            balance += pnl_info["pnl"]
            trades.append(
                {
                    "entry_time": open_position["entry_time"],
                    "exit_time": prepared.index[-1],
                    "entry_price": open_position["entry_price"],
                    "exit_price": float(final_row["close"]),
                    "position_size": open_position["position_size"],
                    "pnl": pnl_info["pnl"],
                    "type": "long" if open_position["direction"] == "BUY" else "short",
                    "symbol": symbol,
                    "exit_reason": "end_of_data",
                    "commission": pnl_info["commission"],
                    "slippage": pnl_info["slippage"],
                    "stop_loss": open_position["stop_loss"],
                    "take_profit": open_position["take_profit"],
                    "signal_confidence": open_position["signal_confidence"],
                }
            )
            equity_curve.append(balance)

        return {
            "trades": trades,
            "equity_curve": pd.Series(equity_curve, dtype=float),
        }
