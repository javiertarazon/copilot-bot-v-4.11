"""Verificar configuración de estrategia"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.config_loader import load_config

config = load_config()
live_config = config.get('live_trading', {})
mapping = live_config.get('strategy_mapping', {})

print(f"\n{'='*60}")
print(f"VERIFICACIÓN DE CONFIGURACIÓN DE ESTRATEGIA")
print(f"{'='*60}\n")

print(f"Total estrategias configuradas: {len(mapping)}")
for name, cfg in mapping.items():
    print(f"\n  📋 Estrategia: {name}")
    print(f"     - Active: {cfg.get('active', False)}")
    print(f"     - Symbols: {cfg.get('symbols', [])}")
    print(f"     - Timeframe: {cfg.get('timeframe', 'N/A')}")

if 'UltraDetailedHeikinAshiMLStrategy' in mapping:
    ultra_cfg = mapping['UltraDetailedHeikinAshiMLStrategy']
    print(f"\n{'='*60}")
    print(f"✅ CONFIGURACIÓN COMPLETA PARA UltraDetailedHeikinAshiMLStrategy")
    print(f"{'='*60}")
    print(f"Active: {ultra_cfg.get('active')}")
    print(f"Symbols: {ultra_cfg.get('symbols')}")
    print(f"Timeframe: {ultra_cfg.get('timeframe')}")
    print(f"Risk per trade: ${ultra_cfg.get('risk_per_trade_usd')}")
    print(f"Indicators configurados: {len(ultra_cfg.get('indicators', {}))}")
    print(f"ML thresholds: {ultra_cfg.get('ml_thresholds', {})}")
else:
    print(f"\n⚠️ NO SE ENCONTRÓ CONFIGURACIÓN PARA UltraDetailedHeikinAshiMLStrategy")

print(f"\n{'='*60}\n")
