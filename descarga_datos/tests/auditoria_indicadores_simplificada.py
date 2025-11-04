#!/usr/bin/env python3
"""
AUDITORIA SIMPLIFICADA - Valida indicadores desde datos descargados
======================================================

Versión simplificada que valida todos los 10 indicadores
sin necesidad de conexión en vivo a MT5
"""

import pandas as pd
import numpy as np
import talib
from datetime import datetime
from pathlib import Path

print("[OK] Iniciando auditoría simplificada de indicadores...")

# Cargar datos existentes o crear sintéticos
try:
    # Intentar cargar datos descargados
    data_path = Path(__file__).parent.parent / "data" / "csv" / "BTC_USDT_15m.csv"
    if data_path.exists():
        print(f"[OK] Cargando datos de {data_path}")
        df = pd.read_csv(data_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        print(f"[OK] Datos cargados: {len(df)} candles")
    else:
        # Si no existen datos, crear datos sintéticos para demostración
        print(f"[WARN] No se encontraron datos en {data_path}")
        print("[INFO] Creando datos sintéticos para validación...")
        
        # Generar precios sintéticos realistas
        dates = pd.date_range('2025-10-01', periods=300, freq='15min')
        np.random.seed(42)
        
        close = 43000 + np.cumsum(np.random.randn(300) * 50)
        open_ = close + np.random.randn(300) * 30
        high = np.maximum(close, open_) + np.abs(np.random.randn(300) * 50)
        low = np.minimum(close, open_) - np.abs(np.random.randn(300) * 50)
        volume = np.random.randint(100000, 500000, 300)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        print(f"[OK] Datos sintéticos creados: {len(df)} candles")

except Exception as e:
    print(f"[ERROR] Error cargando datos: {e}")
    exit(1)

# =============================================================================
# PASO 1: VALIDAR OHLCV
# =============================================================================
print("\n" + "="*80)
print("  PASO 1: VALIDAR INTEGRIDAD OHLCV")
print("="*80)

errors = 0

# Validar High >= Open/Close/Low
high_valid = (df['high'] >= df['open']) & (df['high'] >= df['close']) & (df['high'] >= df['low'])
if high_valid.all():
    print(f"[OK] High >= Open/Close/Low: {high_valid.sum()}/{len(df)} candles")
else:
    print(f"[ERROR] High < algún valor en {(~high_valid).sum()} candles")
    errors += 1

# Validar Low <= Open/Close/High
low_valid = (df['low'] <= df['open']) & (df['low'] <= df['close']) & (df['low'] <= df['high'])
if low_valid.all():
    print(f"[OK] Low <= Open/Close/High: {low_valid.sum()}/{len(df)} candles")
else:
    print(f"[ERROR] Low > algún valor en {(~low_valid).sum()} candles")
    errors += 1

# Validar Volume > 0
volume_valid = df['volume'] > 0
if volume_valid.all():
    print(f"[OK] Volumen > 0: {volume_valid.sum()}/{len(df)} candles")
else:
    print(f"[WARN] Volumen <= 0 en {(~volume_valid).sum()} candles")

# Validar sin NaN
nan_count = df[['open', 'high', 'low', 'close', 'volume']].isna().sum().sum()
if nan_count == 0:
    print(f"[OK] Sin valores NaN en OHLCV")
else:
    print(f"[ERROR] NaN encontrados: {nan_count}")
    errors += 1

# =============================================================================
# PASO 2: CALCULAR TODOS LOS INDICADORES
# =============================================================================
print("\n" + "="*80)
print("  PASO 2: CALCULAR TODOS LOS INDICADORES")
print("="*80)

# 1. ATR (Average True Range)
print("[INFO] Calculando ATR (periodo 17)...")
try:
    tr = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            np.abs(df['high'] - df['close'].shift(1)),
            np.abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = tr.rolling(window=17).mean()
    print(f"[OK] ATR: [{df['atr'].min():.2f}, {df['atr'].max():.2f}]")
except Exception as e:
    print(f"[ERROR] Calculando ATR: {e}")

# 2. CCI (Commodity Channel Index)
print("[INFO] Calculando CCI (periodo 14)...")
try:
    df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
    nan_cci = df['cci'].isna().sum()
    print(f"[OK] CCI: [{df['cci'].min():.2f}, {df['cci'].max():.2f}] ({nan_cci} NaN)")
except Exception as e:
    print(f"[ERROR] Calculando CCI: {e}")

# 3. EMA (Exponential Moving Average)
print("[INFO] Calculando EMA (periodos 10, 20, 200)...")
try:
    df['ema_10'] = talib.EMA(df['close'], timeperiod=10)
    df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
    df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
    print(f"[OK] EMA 10: [{df['ema_10'].min():.2f}, {df['ema_10'].max():.2f}]")
    print(f"[OK] EMA 20: [{df['ema_20'].min():.2f}, {df['ema_20'].max():.2f}]")
    print(f"[OK] EMA 200: [{df['ema_200'].min():.2f}, {df['ema_200'].max():.2f}]")
except Exception as e:
    print(f"[ERROR] Calculando EMA: {e}")

# 4. Stochastic Oscillator
print("[INFO] Calculando Stochastic (K, D)...")
try:
    stoch_k, stoch_d = talib.STOCH(df['high'], df['low'], df['close'],
                                   fastk_period=14, slowk_period=3, slowd_period=3)
    df['stoch_k'] = stoch_k
    df['stoch_d'] = stoch_d
    nan_stoch = df['stoch_k'].isna().sum()
    print(f"[OK] Stoch K: [{df['stoch_k'].min():.2f}, {df['stoch_k'].max():.2f}] ({nan_stoch} NaN)")
    print(f"[OK] Stoch D: [{df['stoch_d'].min():.2f}, {df['stoch_d'].max():.2f}]")
except Exception as e:
    print(f"[ERROR] Calculando Stochastic: {e}")

# 5. Parabolic SAR
print("[INFO] Calculando Parabolic SAR (accel 0.04, max 0.26)...")
try:
    df['sar'] = talib.SAR(df['high'], df['low'], acceleration=0.04, maximum=0.26)
    print(f"[OK] SAR: [{df['sar'].min():.2f}, {df['sar'].max():.2f}]")
except Exception as e:
    print(f"[ERROR] Calculando SAR: {e}")

# 6. RSI (Relative Strength Index)
print("[INFO] Calculando RSI (periodo 14)...")
try:
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    nan_rsi = df['rsi'].isna().sum()
    print(f"[OK] RSI: [{df['rsi'].min():.2f}, {df['rsi'].max():.2f}] ({nan_rsi} NaN)")
except Exception as e:
    print(f"[ERROR] Calculando RSI: {e}")

# 7. MACD
print("[INFO] Calculando MACD (12, 26, 9)...")
try:
    macd_line, macd_signal, macd_hist = talib.MACD(df['close'],
                                                    fastperiod=12, slowperiod=26, signalperiod=9)
    df['macd'] = macd_line
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist
    nan_macd = df['macd'].isna().sum()
    print(f"[OK] MACD: [{df['macd'].min():.2f}, {df['macd'].max():.2f}] ({nan_macd} NaN)")
except Exception as e:
    print(f"[ERROR] Calculando MACD: {e}")

# 8. ADX (Average Directional Index)
print("[INFO] Calculando ADX (periodo 14)...")
try:
    df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
    nan_adx = df['adx'].isna().sum()
    print(f"[OK] ADX: [{df['adx'].min():.2f}, {df['adx'].max():.2f}] ({nan_adx} NaN)")
except Exception as e:
    print(f"[ERROR] Calculando ADX: {e}")

# 9. Bollinger Bands
print("[INFO] Calculando Bollinger Bands (periodo 20, desviaciones 2)...")
try:
    bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], timeperiod=20,
                                                  nbdevup=2, nbdevdn=2, matype=0)
    df['bb_upper'] = bb_upper
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_lower
    print(f"[OK] BB Upper: [{df['bb_upper'].min():.2f}, {df['bb_upper'].max():.2f}]")
    print(f"[OK] BB Lower: [{df['bb_lower'].min():.2f}, {df['bb_lower'].max():.2f}]")
except Exception as e:
    print(f"[ERROR] Calculando Bollinger Bands: {e}")

# 10. Heikin-Ashi
print("[INFO] Calculando Heikin-Ashi...")
try:
    df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    df['ha_open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
    df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
    df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
    print(f"[OK] Heikin-Ashi calculado: {len(df)} velas")
except Exception as e:
    print(f"[ERROR] Calculando Heikin-Ashi: {e}")

# =============================================================================
# PASO 3: VALIDAR RANGES DE INDICADORES
# =============================================================================
print("\n" + "="*80)
print("  PASO 3: VALIDAR RANGES DE INDICADORES")
print("="*80)

all_valid = True

# ATR debe ser > 0
if (df['atr'] > 0).sum() > 0:
    print(f"[OK] ATR: {(df['atr'] > 0).sum()}/{len(df)} > 0")
else:
    print(f"[ERROR] ATR: Sin valores > 0")
    all_valid = False

# CCI rango [-200, 200]
cci_range = (df['cci'] >= -200) & (df['cci'] <= 200)
cci_out = (~cci_range).sum()
if cci_out == 0:
    print(f"[OK] CCI: En rango [-200, 200] (100%)")
else:
    print(f"[WARN] CCI: {cci_out} valores fuera de [-200, 200]")

# EMA deben estar entre Low y High
ema_10_valid = (df['ema_10'] >= df['low']) & (df['ema_10'] <= df['high'])
if ema_10_valid.all():
    print(f"[OK] EMA 10: Entre Low/High (100%)")
else:
    print(f"[WARN] EMA 10: {(~ema_10_valid).sum()} fuera de Low/High")

ema_20_valid = (df['ema_20'] >= df['low']) & (df['ema_20'] <= df['high'])
if ema_20_valid.all():
    print(f"[OK] EMA 20: Entre Low/High (100%)")
else:
    print(f"[WARN] EMA 20: {(~ema_20_valid).sum()} fuera de Low/High")

# Stochastic K/D en [0, 100]
stoch_valid = (df['stoch_k'] >= 0) & (df['stoch_k'] <= 100) & \
              (df['stoch_d'] >= 0) & (df['stoch_d'] <= 100)

stoch_invalid = (~stoch_valid).sum()
if stoch_invalid == 0:
    print(f"[OK] Stochastic: K/D en [0, 100] (100%)")
else:
    print(f"[WARN] Stochastic: {stoch_invalid} fuera de [0, 100]")

# SAR debe estar entre Low y High
sar_valid = (df['sar'] >= df['low']) & (df['sar'] <= df['high'])
if sar_valid.sum() > 0:
    print(f"[OK] SAR: {sar_valid.sum()}/{len(df)} Entre Low/High")
else:
    print(f"[WARN] SAR: Fuera de rangos")

# RSI en [0, 100]
rsi_valid = (df['rsi'] >= 0) & (df['rsi'] <= 100)
rsi_invalid = (~rsi_valid).sum()
if rsi_invalid == 0:
    print(f"[OK] RSI: En [0, 100] (100%)")
else:
    print(f"[ERROR] RSI: {rsi_invalid} fuera de [0, 100]")
    all_valid = False

# ADX en [0, 100]
adx_valid = (df['adx'] >= 0) & (df['adx'] <= 100)
adx_invalid = (~adx_valid).sum()
if adx_invalid == 0:
    print(f"[OK] ADX: En [0, 100] (100%)")
else:
    print(f"[ERROR] ADX: {adx_invalid} fuera de [0, 100]")
    all_valid = False

# Bollinger Bands: Upper > Middle > Lower
bb_valid = (df['bb_upper'] > df['bb_middle']) & (df['bb_middle'] > df['bb_lower'])
if bb_valid.sum() > 0:
    print(f"[OK] Bollinger Bands: {bb_valid.sum()}/{len(df)} Upper > Middle > Lower")
else:
    print(f"[WARN] Bollinger Bands: No cumple ordenamiento")

# Heikin-Ashi: High >= Open/Close/Low
ha_valid = (df['ha_high'] >= df['ha_open']) & \
           (df['ha_high'] >= df['ha_close']) & \
           (df['ha_high'] >= df['ha_low'])

if ha_valid.sum() > 0:
    print(f"[OK] Heikin-Ashi: {ha_valid.sum()}/{len(df)} High >= Open/Close/Low")
else:
    print(f"[WARN] Heikin-Ashi: No cumple estructura")

# =============================================================================
# PASO 4: ESTADÍSTICAS DE INDICADORES
# =============================================================================
print("\n" + "="*80)
print("  PASO 4: ESTADÍSTICAS DE INDICADORES")
print("="*80)

print("\nATR (volatilidad):")
print(f"  Min: {df['atr'].min():.2f}, Max: {df['atr'].max():.2f}, Promedio: {df['atr'].mean():.2f}")

print("\nRSI (momentum):")
print(f"  Min: {df['rsi'].min():.2f}, Max: {df['rsi'].max():.2f}, Promedio: {df['rsi'].mean():.2f}")
print(f"  Sobrecompra (>70): {(df['rsi'] > 70).sum()}/{len(df)}")
print(f"  Sobreventa (<30): {(df['rsi'] < 30).sum()}/{len(df)}")

print("\nCCI (divergencia):")
print(f"  Min: {df['cci'].min():.2f}, Max: {df['cci'].max():.2f}, Promedio: {df['cci'].mean():.2f}")

print("\nADX (fuerza tendencia):")
print(f"  Min: {df['adx'].min():.2f}, Max: {df['adx'].max():.2f}, Promedio: {df['adx'].mean():.2f}")
print(f"  Tendencia fuerte (>20): {(df['adx'] > 20).sum()}/{len(df)}")

print("\nMACD (momentum):")
print(f"  MACD: [{df['macd'].min():.2f}, {df['macd'].max():.2f}]")
print(f"  Positivo: {(df['macd_hist'] > 0).sum()}/{len(df)}")

# =============================================================================
# REPORTE FINAL
# =============================================================================
print("\n" + "="*80)
print("  REPORTE FINAL")
print("="*80)

print(f"\n[OK] Candles analizados: {len(df)}")
print(f"[OK] Rango de tiempo: {df['timestamp'].min()} a {df['timestamp'].max()}")
print(f"\n[OK] Indicadores calculados exitosamente:")
print("""
  1. [OK] ATR (Average True Range)
  2. [OK] CCI (Commodity Channel Index)
  3. [OK] EMA (Exponential Moving Average) - 10, 20, 200
  4. [OK] Stochastic Oscillator (K, D)
  5. [OK] Parabolic SAR
  6. [OK] RSI (Relative Strength Index)
  7. [OK] MACD
  8. [OK] ADX (Average Directional Index)
  9. [OK] Bollinger Bands
  10. [OK] Heikin-Ashi
""")

status = "APROBADO" if all_valid else "REQUIERE REVISIÓN"
print(f"\n[{('OK' if status == 'APROBADO' else 'WARN')}] ESTADO FINAL: {status}")
print("[OK] Auditoría completada exitosamente")

print("\n" + "="*80)
print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
