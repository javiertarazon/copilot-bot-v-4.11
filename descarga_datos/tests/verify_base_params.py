#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import load_config_from_yaml, get_strategy_parameters

config = load_config_from_yaml()
symbol = config.backtesting.symbols[0] if config.backtesting.symbols else "Volatility 75 Index"

print(f"Symbol: {symbol}")
print(f"\nBase parameters section exists: {hasattr(config.backtesting, 'base_parameters')}")

params = get_strategy_parameters(config, symbol)
print(f"\nParameters loaded:")
print(f"  ml_threshold: {params.get('ml_threshold')}")
print(f"  cci_threshold: {params.get('cci_threshold')}")
print(f"  atr_period: {params.get('atr_period')}")
print(f"  kelly_fraction: {params.get('kelly_fraction')}")
print(f"  max_drawdown: {params.get('max_drawdown')}")
print(f"\n✅ All {len(params)} base parameters loaded successfully!")
