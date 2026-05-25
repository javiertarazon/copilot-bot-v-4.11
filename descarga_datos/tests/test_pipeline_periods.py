import sys
import types
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

from descarga_datos.config.config_loader import load_config_from_yaml


CONFIG_PATH = repo_root / "descarga_datos" / "config" / "config.yaml"


def test_config_usa_periodos_anuales_separados():
    config = load_config_from_yaml(CONFIG_PATH)

    assert config.ml_training.training["train_start"] == "2017-01-01"
    assert config.ml_training.training["train_end"] == "2017-12-31"
    assert config.ml_training.training["val_start"] == "2018-01-01"
    assert config.ml_training.training["val_end"] == "2018-12-31"
    assert config.backtesting.start_date == "2019-01-01"
    assert config.backtesting.end_date == "2019-12-31"


def test_pipeline_backtest_final_usa_rango_dedicado(monkeypatch):
    fake_strategy_module = types.ModuleType("strategies.ultra_detailed_heikin_ashi_ml_strategy")
    captured = {}

    class PlaceholderStrategy:
        def __init__(self, config=None):
            self.config = config

        def run(self, data, symbol, timeframe):
            captured["data_start"] = data.index.min()
            captured["data_end"] = data.index.max()
            return {"total_pnl": 123.0, "symbol": symbol, "timeframe": timeframe}

    fake_strategy_module.UltraDetailedHeikinAshiMLStrategy = PlaceholderStrategy
    monkeypatch.setitem(sys.modules, "strategies.ultra_detailed_heikin_ashi_ml_strategy", fake_strategy_module)

    from descarga_datos.optimizacion import run_optimization_pipeline2 as pipeline_module

    class FakeDataStorage:
        def query_data(self, table_name, start_ts=None, end_ts=None):
            captured["table_name"] = table_name
            captured["start_ts"] = start_ts
            captured["end_ts"] = end_ts
            index = pd.date_range("2019-01-01", periods=3, freq="D")
            return pd.DataFrame(
                {
                    "open": [1.0, 2.0, 3.0],
                    "high": [2.0, 3.0, 4.0],
                    "low": [0.5, 1.5, 2.5],
                    "close": [1.5, 2.5, 3.5],
                    "volume": [100, 110, 120],
                },
                index=index,
            )

    fake_storage_module = types.ModuleType("utils.storage")
    fake_storage_module.DataStorage = FakeDataStorage
    monkeypatch.setitem(sys.modules, "utils.storage", fake_storage_module)
    monkeypatch.setattr(pipeline_module, "load_config_from_yaml", lambda: {"active_exchange": "mt5"})

    pipeline = pipeline_module.OptimizationPipeline(
        symbols=["XAUUSD"],
        timeframe="15m",
        train_start="2017-01-01",
        train_end="2017-12-31",
        val_start="2018-01-01",
        val_end="2018-12-31",
        opt_start="2018-01-01",
        opt_end="2018-12-31",
        backtest_start="2019-01-01",
        backtest_end="2019-12-31",
        n_trials=1,
    )

    result = pipeline._run_backtest_with_params("XAUUSD", {}, "prueba")

    assert captured["table_name"] == "XAUUSD_15m"
    assert captured["start_ts"] == int(pd.Timestamp("2019-01-01").timestamp())
    assert captured["end_ts"] == int(pd.Timestamp("2019-12-31").timestamp())
    assert captured["data_start"] == pd.Timestamp("2019-01-01")
    assert captured["data_end"] == pd.Timestamp("2019-01-03")
    assert result["total_pnl"] == 123.0
