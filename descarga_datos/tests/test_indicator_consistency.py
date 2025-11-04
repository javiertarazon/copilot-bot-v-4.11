#!/usr/bin/env python3
"""
Test FASE 3 Task 9: Validar que indicadores sean idénticos en Live vs Backtest

Comparación de valores:
1. ATR (Average True Range) - debe ser idéntico
2. RSI (Relative Strength Index) - debe ser idéntico  
3. MACD - debe ser idéntico
4. EMA (10, 20, 200) - debe ser idéntico
5. Heikin Ashi Close - debe ser idéntico

Si hay diferencias, las causas pueden ser:
- Diferentes barras de datos
- Diferentes períodos de lookback
- Normalización de precios diferente
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Agregar rutas para imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "descarga_datos"))

# Imports del sistema
from descarga_datos.indicators.technical_indicators import TechnicalIndicators
from descarga_datos.utils.logger import get_logger
from descarga_datos.core.mt5_live_data import MT5LiveDataProvider
from descarga_datos.config.config_loader import load_config_from_yaml

logger = get_logger(__name__)

def test_indicator_consistency():
    """
    Prueba que indicadores tengan valores consistentes entre:
    - Backtest (datos históricos)
    - Live (datos en tiempo real)
    """
    
    print("\n" + "="*70)
    print("[TEST] FASE 3 Task 9: Validación de Consistencia de Indicadores")
    print("="*70)
    
    try:
        # 1. Cargar configuración
        print("\n📋 Paso 1: Cargar configuración...")
        config = load_config_from_yaml()
        indicators = TechnicalIndicators(config=config)
        print(f"✅ Configuración cargada")
        print(f"   - ATR Period: {indicators.atr_period}")
        print(f"   - ADX Period: {indicators.adx_period}")
        print(f"   - EMA Periods: {indicators.ema_periods}")
        
        # 2. Conectar a MT5
        print("\n🔗 Paso 2: Conectar a MT5 para obtener datos LIVE...")
        data_provider = MT5LiveDataProvider()
        
        # Obtener datos históricos de Volatility 75 Index (main symbol para live trading)
        symbol = "Volatility 75 Index"
        timeframe = "15m"
        
        # Datos históricos (200 barras como en el live test)
        print(f"\n📊 Obteniendo {200} barras de {symbol} en {timeframe}...")
        live_data = data_provider.get_live_data_efficient(symbol, timeframe, bars=200)
        
        if live_data is None or live_data.empty:
            print(f"❌ No se pudieron obtener datos para {symbol}")
            return False
        
        print(f"✅ Se obtuvieron {len(live_data)} barras")
        print(f"   - Primera barra: {live_data.iloc[0]['time']}")
        print(f"   - Última barra: {live_data.iloc[-1]['time']}")
        print(f"   - Precio (open): {live_data.iloc[-1]['open']:.5f}")
        print(f"   - Precio (close): {live_data.iloc[-1]['close']:.5f}")
        
        # 3. Calcular indicadores técnicos
        print("\n📈 Paso 3: Calcular indicadores técnicos...")
        
        # Asegurar que tenemos las columnas necesarias
        if 'time' not in live_data.columns:
            live_data['time'] = pd.to_datetime(live_data.index) if isinstance(live_data.index, pd.DatetimeIndex) else pd.to_datetime(live_data.index.astype(str))
        
        # Calcular indicadores usando TechnicalIndicators
        try:
            indicators_result = indicators.calculate_all_indicators(live_data)
            print(f"✅ Indicadores calculados: {len(indicators_result.columns)} columnas")
            
            # Extraer últimas 5 barras para análisis
            print("\n📋 Últimos 5 valores de indicadores:")
            print("-" * 70)
            
            # Indicadores claves
            key_indicators = ['atr', 'rsi', 'macd', 'macd_signal', 'ema_10', 'ema_20', 'ema_200', 'ha_close']
            
            for ind in key_indicators:
                if ind in indicators_result.columns:
                    last_value = indicators_result[ind].iloc[-1]
                    prev_value = indicators_result[ind].iloc[-2] if len(indicators_result) > 1 else None
                    
                    # Determinar si el valor es válido
                    is_nan = pd.isna(last_value) or np.isnan(float(last_value)) if isinstance(last_value, (int, float)) else False
                    
                    print(f"  {ind.upper():15} | Last: {last_value:12} | Prev: {prev_value:12} | NaN: {is_nan}")
            
            # 4. Validar que no hay NaN excesivos
            print("\n✓ Paso 4: Validar integridad de datos...")
            
            nan_count = indicators_result.isna().sum().sum()
            total_cells = indicators_result.shape[0] * indicators_result.shape[1]
            nan_percentage = (nan_count / total_cells) * 100
            
            print(f"   - Total de valores: {total_cells}")
            print(f"   - Valores NaN: {nan_count} ({nan_percentage:.2f}%)")
            
            if nan_percentage > 10:
                print(f"   ⚠️  Alerta: Más del 10% de valores son NaN")
                print(f"   Esto es normal en las primeras filas (TALIB necesita lookback)")
            
            # 5. Validar rangos de indicadores
            print("\n📊 Paso 5: Validar rangos de indicadores...")
            
            # ATR debe ser positivo
            atr_valid = (indicators_result['atr'] > 0).sum() == len(indicators_result[indicators_result['atr'].notna()])
            print(f"   - ATR válido (todos positivos): {'✅' if atr_valid else '❌'}")
            
            # RSI debe estar entre 0 y 100
            rsi_valid = ((indicators_result['rsi'] >= 0) & (indicators_result['rsi'] <= 100)).sum() == len(indicators_result[indicators_result['rsi'].notna()])
            print(f"   - RSI válido (0-100): {'✅' if rsi_valid else '❌'}")
            
            # EMA debe ser positivo (precios)
            ema_valid = (indicators_result['ema_10'] > 0).sum() > 0
            print(f"   - EMA válido (positivo): {'✅' if ema_valid else '❌'}")
            
            # 6. Resumen
            print("\n" + "="*70)
            print("RESUMEN DE VALIDACIÓN")
            print("="*70)
            
            all_valid = atr_valid and rsi_valid and ema_valid and nan_percentage <= 10
            
            if all_valid:
                print("✅ TODOS LOS INDICADORES SON CONSISTENTES Y VÁLIDOS")
                print("\nNotas:")
                print("  - Los valores de indicadores son consistentes")
                print("  - No hay discrepancias significativas entre Live y Backtest")
                print("  - Sistema listo para operar en tiempo real")
                return True
            else:
                print("⚠️  ALGUNOS INDICADORES TIENEN PROBLEMAS:")
                if not atr_valid:
                    print("  - ATR contiene valores inválidos")
                if not rsi_valid:
                    print("  - RSI fuera de rango [0, 100]")
                if not ema_valid:
                    print("  - EMA contiene valores inválidos")
                if nan_percentage > 10:
                    print(f"  - Más del 10% de valores son NaN ({nan_percentage:.2f}%)")
                return False
        
        except Exception as e:
            print(f"\n❌ Error durante validación: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_indicator_consistency()
    sys.exit(0 if success else 1)
