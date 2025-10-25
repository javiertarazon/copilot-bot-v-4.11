#!/usr/bin/env python3
"""Test de carga de configuración con credenciales"""

from descarga_datos.config.config_loader import load_config_from_yaml

cfg = load_config_from_yaml()
print('✅ Config cargada correctamente')

binance_cfg = cfg.exchanges.get('binance')
if binance_cfg:
    api_key = binance_cfg.api_key
    api_secret = binance_cfg.api_secret
    
    print(f'\n📊 CREDENCIALES BINANCE:')
    print(f'  API Key: {"✅ CARGADA" if api_key else "❌ VACÍA"}')
    if api_key:
        print(f'    Primeros 10 chars: {api_key[:10]}...')
    print(f'  API Secret: {"✅ CARGADA" if api_secret else "❌ VACÍA"}')
    if api_secret:
        print(f'    Primeros 10 chars: {api_secret[:10]}...')
    print(f'  Sandbox: {binance_cfg.sandbox}')
    print(f'  Habilitado: {binance_cfg.enabled}')
else:
    print('❌ Binance no configurado')

bybit_cfg = cfg.exchanges.get('bybit')
if bybit_cfg:
    print(f'\n📊 CREDENCIALES BYBIT:')
    print(f'  API Key: {"✅ CARGADA" if bybit_cfg.api_key else "❌ VACÍA"}')
    print(f'  Habilitado: {bybit_cfg.enabled}')
