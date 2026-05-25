from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

from descarga_datos.config.config_loader import load_config_from_yaml
from descarga_datos.validation.promotion_gate import build_validation_report


CONFIG_PATH = repo_root / "descarga_datos" / "config" / "config.yaml"


def test_config_canonicamente_apunta_a_xauusd():
    config = load_config_from_yaml(CONFIG_PATH)

    assert config.backtesting.symbols == ["XAUUSD"]
    assert config.backtesting.timeframe == "15m"
    assert config.live_trading.active_symbol == "XAUUSD"
    assert config.live_trading.mt5_symbols == ["XAUUSD"]
    assert config.live_trading.mt5_timeframes == ["15m"]
    assert config.backtesting.strategies == {"UltraDetailedHeikinAshiML": True}


def test_reporte_inicial_bloquea_demo_y_real():
    config = load_config_from_yaml(CONFIG_PATH)
    report = build_validation_report(config)

    assert report["demo_ready"] is False
    assert report["real_ready"] is False
    assert report["missing_demo"] == ["training", "validation", "final_test"]
    assert report["missing_real"] == ["training", "validation", "final_test", "sandbox_demo"]


def test_reporte_permita_demo_y_real_segun_etapas():
    config = load_config_from_yaml(CONFIG_PATH)
    validation = config.live_trading.validation

    validation["completed_stages"] = {
        "training": True,
        "validation": True,
        "final_test": True,
        "sandbox_demo": False,
    }

    report = build_validation_report(config)
    assert report["demo_ready"] is True
    assert report["real_ready"] is False

    validation["completed_stages"]["sandbox_demo"] = True
    validation["allow_real_trading"] = True

    report = build_validation_report(config)
    assert report["demo_ready"] is True
    assert report["real_ready"] is True
