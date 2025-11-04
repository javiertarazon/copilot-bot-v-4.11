# 🎬 Visualización Paso a Paso: Transformación del DataFrame

## 📺 ETAPA 1: ANTES - DataFrame Crudo de MT5

```
get_live_data() → mt5.copy_rates_from_pos()

Retorna: Array de estructuras C
┌─────────────────────────────────────────────────────────┐
│ Array de 200 tuplas:                                     │
├─────────────────────────────────────────────────────────┤
│ (time=1730688600, open=42100.5, high=42150.0, ...       │ ← Tupla #1
│ (time=1730688900, open=42120.0, high=42200.0, ...       │ ← Tupla #2
│ (time=1730689200, open=42180.0, high=42250.0, ...       │ ← Tupla #3
│ ...
│ (time=1730696400, open=42180.0, high=42250.0, ...       │ ← Tupla #200
└─────────────────────────────────────────────────────────┘

Luego: pd.DataFrame(rates)

┌────────────────────────────────────────────────────────────────────────┐
│ Resultado después de pd.DataFrame(rates):                              │
├────────────────────────────────────────────────────────────────────────┤
│     time      open    high     low   close  tick_volume  spread  ...   │
│ 0   1730688600   42100.5  42150.0  42050.0  42120.0    0       0      │
│ 1   1730688900   42120.0  42200.0  42100.0  42180.0    0       0      │
│ 2   1730689200   42180.0  42250.0  42170.0  42200.0    0       0      │
│ 3   1730689500   42200.0  42350.0  42180.0  42250.0    0       0      │
│ ...                                                                     │
│ 199 1730696400   42180.0  42400.0  42200.0  42350.0    0       0      │
│                                                                         │
│ Shape: (200, 8)                                                         │
│ Columnas: [time, open, high, low, close, tick_volume, spread, real... │
│ Memory: ~12.8 KB                                                        │
└────────────────────────────────────────────────────────────────────────┘

PROBLEMAS EN ESTA ETAPA:
├─ 'time' es Unix timestamp (segundos desde 1970)
├─ Columna se llama 'tick_volume' (no 'volume')
├─ Hay columnas extras (spread, real_volume)
├─ Timestamps no son datetime objects
└─ Necesita limpieza
```

---

## 🔄 TRANSFORMACIÓN 1: Normalizar Timestamps

```python
# Paso 1: Convertir Unix timestamp a datetime
df['timestamp'] = pd.to_datetime(df['time'], unit='s')

ANTES:
┌────────────┬────────────────────┐
│ time       │ timestamp (nuevo)   │
├────────────┼────────────────────┤
│ 1730688600 │ NaT (aún no existe) │
│ 1730688900 │ NaT (aún no existe) │
│ 1730689200 │ NaT (aún no existe) │
└────────────┴────────────────────┘

DESPUÉS:
┌────────────┬──────────────────────────────────┐
│ time       │ timestamp                        │
├────────────┼──────────────────────────────────┤
│ 1730688600 │ 2025-11-04 10:30:00              │
│ 1730688900 │ 2025-11-04 10:45:00              │
│ 1730689200 │ 2025-11-04 11:00:00              │
│ ...        │ ...                              │
└────────────┴──────────────────────────────────┘

DataFrame ahora tiene:
├─ Columna 'timestamp' con datetime objects
├─ Columna 'time' aún presente (se elimina después)
├─ Shape: (200, 9)
└─ Memory: +1.6 KB (bytes adicionales para datetime)
```

---

## 🔄 TRANSFORMACIÓN 2: Renombrar Columnas OHLCV

```python
# Paso 2: Renombrar 'tick_volume' a 'volume'
df = df.rename(columns={'tick_volume': 'volume'})

ANTES:
┌───────────────────────┐
│ tick_volume (nombre)  │
├───────────────────────┤
│ 0                     │
│ 0                     │
│ 0                     │
│ ...                   │
└───────────────────────┘

DESPUÉS:
┌───────────────────────┐
│ volume (nombre nuevo) │
├───────────────────────┤
│ 0                     │
│ 0                     │
│ 0                     │
│ ...                   │
└───────────────────────┘

Cambio: Solo el nombre de la columna
├─ Los valores permanecen iguales (todos 0 para Volatility Index)
├─ DataFrame shape sin cambios: (200, 9)
└─ Memory: Sin cambios
```

---

## 🔄 TRANSFORMACIÓN 3: Seleccionar Solo Columnas OHLCV

```python
# Paso 3: Seleccionar solo las 6 columnas que necesitamos
df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

ANTES (9 columnas):
┌─────────────┬──────────┬──────────┬──────────┬──────────┬────────┬──────┬──────┬────┐
│ timestamp   │ open     │ high     │ low      │ close    │ volume │ time │ ...  │    │
├─────────────┼──────────┼──────────┼──────────┼──────────┼────────┼──────┼──────┼────┤
│ 2025-11-04  │ 42100.5  │ 42150.0  │ 42050.0  │ 42120.0  │ 0      │ 1730 │ ...  │    │
│ 10:30:00    │          │          │          │          │        │ 688  │      │    │
└─────────────┴──────────┴──────────┴──────────┴──────────┴────────┴──────┴──────┴────┘
                                    ELIMINAR ←─────────────────────────────────

DESPUÉS (6 columnas - COLUMNAS OHLCV):
┌─────────────────────┬──────────┬──────────┬──────────┬──────────┬────────┐
│ timestamp           │ open     │ high     │ low      │ close    │ volume │
├─────────────────────┼──────────┼──────────┼──────────┼──────────┼────────┤
│ 2025-11-04 10:30:00 │ 42100.5  │ 42150.0  │ 42050.0  │ 42120.0  │ 0      │
│ 2025-11-04 10:45:00 │ 42120.0  │ 42200.0  │ 42100.0  │ 42180.0  │ 0      │
│ 2025-11-04 11:00:00 │ 42180.0  │ 42250.0  │ 42170.0  │ 42200.0  │ 0      │
│ ...                 │ ...      │ ...      │ ...      │ ...      │ ...    │
│ 2025-11-04 16:45:00 │ 42180.0  │ 42400.0  │ 42200.0  │ 42350.0  │ 0      │
└─────────────────────┴──────────┴──────────┴──────────┴──────────┴────────┘

Cambio:
├─ Elimina columnas: time, spread, real_volume, ...
├─ Mantiene solo: timestamp, open, high, low, close, volume
├─ DataFrame shape ahora: (200, 6) ✅ CORRECTO
├─ Memory: ~6.4 KB (descartadas columnas innecesarias)
└─ ¡AQUÍ TERMINA LA LIMPIEZA BÁSICA!
```

---

## ✨ RESULTADO: DataFrame Limpio OHLCV (Etapa 1 Completa)

```
DataFrame listo para indicadores:

      timestamp            open      high       low      close  volume
0    2025-11-04 10:30:00  42100.50  42150.00  42050.00  42120.00    0
1    2025-11-04 10:45:00  42120.00  42200.00  42100.00  42180.00    0
2    2025-11-04 11:00:00  42180.00  42250.00  42170.00  42200.00    0
3    2025-11-04 11:15:00  42200.00  42350.00  42180.00  42250.00    0
4    2025-11-04 11:30:00  42250.00  42400.00  42200.00  42300.00    0
...
195  2025-11-04 16:00:00  42100.00  42280.00  42050.00  42150.00    0
196  2025-11-04 16:15:00  42150.00  42300.00  42100.00  42200.00    0
197  2025-11-04 16:30:00  42200.00  42350.00  42150.00  42250.00    0
198  2025-11-04 16:45:00  42250.00  42400.00  42200.00  42300.00    0
199  2025-11-04 17:00:00  42180.00  42250.00  42100.00  42197.67    0

Shape: (200, 6) ✅
Columnas: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
Memory: ~6.4 KB

✅ ETAPA 1 COMPLETADA: Datos listos para cálculo de indicadores
```

---

## 🎲 ETAPA 2: Agregación de Indicadores Técnicos

```python
# Función: _prepare_data(df_ohlcv) agrega 25 indicadores

ENTRADA (6 columnas):
     timestamp            open      high       low      close  volume
0    2025-11-04 10:30:00  42100.50  42150.00  42050.00  42120.00    0

↓↓↓ ADD_INDICATORS ↓↓↓

PROCESO: Cálculo de 25 indicadores en paralelo

1. HEIKIN-ASHI (4 columnas)
   ├─ ha_open    = (ha_open[t-1] + ha_close[t-1]) / 2 = 42110.25
   ├─ ha_high    = max(open[t], high[t], ha_close[t-1]) = 42150.00
   ├─ ha_low     = min(open[t], low[t], ha_close[t-1]) = 42050.00
   └─ ha_close   = (open[t] + high[t] + low[t] + close[t]) / 4 = 42105.00

2. TENDENCIA (5 columnas)
   ├─ ema_10     = EMA(close, período=10) = 42104.23
   ├─ ema_20     = EMA(close, período=20) = 42112.45
   ├─ ema_200    = EMA(close, período=200) = 42098.67
   ├─ adx        = ADX(high, low, close, período=14) = 28.56
   └─ sar        = SAR(high, low) = 42200.00 (en tendencia baja)

3. MOMENTUM (4 columnas)
   ├─ rsi        = RSI(close, período=14) = 42.50
   ├─ macd       = MACD(close) = -0.45
   ├─ macd_signal= MACD Signal = -0.38
   └─ momentum_5 = close[t] - close[t-5] = -15.23

4. VOLATILIDAD (4 columnas)
   ├─ atr        = ATR(high, low, close, período=17) = 1145.41
   ├─ bb_upper   = SMA + (2 * STD) = 42500.00
   ├─ bb_middle  = SMA(close, período=20) = 42200.00
   └─ bb_lower   = SMA - (2 * STD) = 41900.00

5. FEATURES ML (4 columnas)
   ├─ volume_ratio   = volatility / avg_volatility = 0.95
   ├─ price_position = (close - bb_lower) / (bb_upper - bb_lower) = 0.42
   ├─ trend_strength = adx / 100 = 0.2856
   └─ returns        = log(close[t] / close[t-1]) = -0.0036

TOTAL: 6 + 25 = 31 columnas

SALIDA (31 columnas):
     timestamp  open  high   low  close  volume  ha_open  ha_high  ha_low  ha_close  ema_10  ema_20  ema_200  ...  returns
0    2025-11-04 42100.50  42150.00  42050.00  42120.00    0      42110.25  42150.00  42050.00  42105.00  42104.23  42112.45  42098.67  ...  -0.0036
```

---

## 📊 Visualización: Ejemplo de 5 Barras Completo

```
ENTRADA: 5 barras OHLCV sin indicadores

     timestamp            open      high       low      close  volume
0    2025-11-04 10:30:00  42100.50  42150.00  42050.00  42120.00    0
1    2025-11-04 10:45:00  42120.00  42200.00  42100.00  42180.00    0
2    2025-11-04 11:00:00  42180.00  42250.00  42170.00  42200.00    0
3    2025-11-04 11:15:00  42200.00  42350.00  42180.00  42250.00    0
4    2025-11-04 11:30:00  42250.00  42400.00  42200.00  42300.00    0

Shape: (5, 6)

↓↓↓ ADD_INDICATORS ↓↓↓

SALIDA: 5 barras con 31 columnas

     timestamp       open    high      low    close  volume   ha_open   ha_high ...  returns
0    2025-11-04   42100.50  42150.00  42050.00  42120.00    0    42110.25  42150.00  ...  0.0000
1    2025-11-04   42120.00  42200.00  42100.00  42180.00    0    42115.13  42200.00  ...  0.0014
2    2025-11-04   42180.00  42250.00  42170.00  42200.00    0    42157.57  42250.00  ...  0.0005
3    2025-11-04   42200.00  42350.00  42180.00  42250.00    0    42203.93  42350.00  ...  0.0012
4    2025-11-04   42250.00  42400.00  42200.00  42300.00    0    42251.48  42400.00  ...  0.0015

Shape: (5, 31) ✅
Memory: ~1.3 KB

✅ ETAPA 2 COMPLETADA: Indicadores listos para ML
```

---

## 🤖 ETAPA 3: Extracción de Features para ML

```python
# Función: strategy.get_live_signal(df_prepared)
# Extrae últimas 25 features de la última fila

ENTRADA: DataFrame (200, 31)
         └─ Fila 199 (última): Contiene todas las 25 features

EXTRACCIÓN:
features_last_row = df_prepared[feature_names].iloc[-1].values

┌─────────────────────────────────────────────────────────────────┐
│ Fila 199 (última) - Extracción de 25 features                  │
├─────────────────────────────────────────────────────────────────┤
│ [0]  ha_open          = 42251.48                                │
│ [1]  ha_high          = 42400.00                                │
│ [2]  ha_low           = 42200.00                                │
│ [3]  ha_close         = 42300.00                                │
│ [4]  ema_10           = 42247.23                                │
│ [5]  ema_20           = 42198.45                                │
│ [6]  ema_200          = 42150.67                                │
│ [7]  adx              = 28.56                                   │
│ [8]  sar              = 42200.00                                │
│ [9]  rsi              = 42.50                                   │
│ [10] macd             = -0.45                                   │
│ [11] macd_signal      = -0.38                                   │
│ [12] momentum_5       = -15.23                                  │
│ [13] momentum_10      = +5.12                                   │
│ [14] atr              = 1145.41                                 │
│ [15] bb_upper         = 42500.00                                │
│ [16] bb_middle        = 42200.00                                │
│ [17] bb_lower         = 41900.00                                │
│ [18] volatility       = 2.71                                    │
│ [19] volume_ratio     = 0.95                                    │
│ [20] price_position   = 0.42                                    │
│ [21] trend_strength   = 0.2856                                  │
│ [22] returns          = -0.0036                                 │
│ [23] close_normalized = 0.5234  (normalizado con historia)      │
│ [24] volume_ratio_lag = 0.94    (período anterior)             │
└─────────────────────────────────────────────────────────────────┘

Vector resultante: Array NumPy (1, 25)
shape: (1, 25)
dtype: float64

```

---

## 🧠 ETAPA 4: Normalización StandardScaler

```python
# Proceso: scaler.transform(features_array)

ENTRADA (valores crudos):
features_raw = [42251.48, 42400.00, 42200.00, 42300.00, 42247.23, ...]

↓↓↓ StandardScaler.transform() ↓↓↓

NORMALIZACIÓN (z-score):
normalized = (x - mean) / std

Para cada feature:
├─ ha_open: (42251.48 - 42175.25) / 85.32 = +0.891
├─ ha_high: (42400.00 - 42250.15) / 120.45 = +1.245
├─ ha_low: (42200.00 - 42150.33) / 95.12 = +0.523
├─ ha_close: (42300.00 - 42220.50) / 78.45 = +1.011
├─ ema_10: (42247.23 - 42150.67) / 95.23 = +1.014
└─ ... (20 features más)

SALIDA (valores normalizados):
features_normalized = [+0.891, +1.245, +0.523, +1.011, +1.014, ..., -0.234]

shape: (1, 25)
rango: aproximadamente [-3, +3] (distribución normal)
```

---

## 🎯 ETAPA 5: Predicción del Modelo ML

```python
# Proceso: model.predict(features_normalized)

ENTRADA (25 features normalizados):
[+0.891, +1.245, +0.523, +1.011, +1.014, ..., -0.234]
  ↓
RandomForest(100 árboles, profundidad=10, min_samples_leaf=5)
  ↓

ÁRBOL 1 (de 100):
┌─────────────────────┐
│ Nodo raíz: ADX > 0.5│
├─────────────────────┤
│ ├─ Rama SÍ: RSI > 0.3
│ │  ├─ Rama SÍ: EMA Positive
│ │ │  └─ Predicción: SELL ✅
│ │  └─ Rama NO
│ │     └─ Predicción: BUY
│ └─ Rama NO: Volume High
│    ├─ Rama SÍ: Momentum Positive
│    │  └─ Predicción: BUY
│    └─ Rama NO
│       └─ Predicción: HOLD
└─────────────────────┘

ÁRBOL 2 - 100 (procesados en paralelo):
... (otros árboles toman decisiones similares)

AGREGACIÓN (Majority Voting):
├─ Árboles que predicen BUY:   23
├─ Árboles que predicen SELL:  51 ✅ GANADOR
├─ Árboles que predicen HOLD:  26
│
└─ Predicción final: SELL (51 votos de 100)

CONFIANZA (Probabilidades):
probabilities = [BUY: 0.23, SELL: 0.51, HOLD: 0.26]
                           ↑ Máximo

max_confidence = 0.51 (51%)

```

---

## ✅ RESULTADO FINAL: Señal de Trading

```
SALIDA DE LA ESTRATEGIA:

{
    'signal': 'SELL',
    'signal_data': {
        'direction': 'short',
        'entry_price': 42300.00,
        'stop_loss_price': 42420.00,
        'take_profit_price': 42100.00,
        'position_size': 0.0001747,
        'ml_confidence': 0.51,
        'ema_trend': 'bearish',
        'rsi_value': 42.50,
        'atr_value': 1145.41
    }
}

INTERPRETACIÓN:
├─ Signal: SELL (vender en corto)
├─ Confianza: 51% (moderadamente confiable)
├─ Entrada: 42300.00
├─ SL (Stop Loss): 42420.00 (a 120 pips si se equivoca)
├─ TP (Take Profit): 42100.00 (a 200 pips si acierta)
├─ Tamaño posición: 0.0001747 lotes
│  └─ Calculado: (balance * risk_per_trade) / ATR
│     └─ (10000 * 0.02) / 1145.41 = 0.0001747
└─ Otros datos: EMA bajista, RSI neutro, ATR alto

✅ SEÑAL LISTA PARA EJECUCIÓN EN MT5
```

---

## 🔄 Ciclo Completo en Visión General

```
CICLO TRADING (5 segundos):

MT5 RAW DATA (200 C-structs)
        ↓
[ETAPA 1] LIMPIEZA
   ├─ pd.DataFrame()
   ├─ Timestamp conversion
   ├─ Column rename
   └─ Select OHLCV
        ↓
OHLCV DataFrame (200, 6)
        ↓
[ETAPA 2] INDICADORES
   ├─ Heikin-Ashi
   ├─ Tendencia (EMA, ADX, SAR)
   ├─ Momentum (RSI, MACD)
   ├─ Volatilidad (ATR, BB)
   └─ ML Features
        ↓
PREPARADO DataFrame (200, 31)
        ↓
[ETAPA 3] FEATURE EXTRACTION
   └─ Extract last row [25 features]
        ↓
FEATURES Vector (1, 25)
        ↓
[ETAPA 4] NORMALIZACIÓN
   └─ StandardScaler.transform()
        ↓
NORMALIZED Vector (1, 25) [-3 a +3]
        ↓
[ETAPA 5] ML PREDICCIÓN
   ├─ RandomForest.predict()
   ├─ RandomForest.predict_proba()
   └─ Determine winner class
        ↓
PREDICCIÓN + CONFIANZA
        ↓
[ETAPA 6] VALIDACIÓN
   ├─ Evaluar condiciones técnicas
   ├─ Aplicar reglas de negocio
   └─ Generar señal final
        ↓
SEÑAL DE TRADING
   ├─ BUY / SELL / HOLD
   ├─ Parámetros: entry, SL, TP
   └─ Confianza
        ↓
[EJECUCIÓN]
   ├─ SI SEÑAL → MT5.order_send()
   ├─ MONITOREO SL/TP
   └─ LOGGING RESULTADO

⏱️  TIEMPO TOTAL: ~450ms por ciclo
🔁 FRECUENCIA: Cada 5 segundos (indefinidamente)
📊 DATOS: 200 barras nuevas cada ciclo
✅ VALIDACIÓN: Datos completos, sin NaN, sin infinitos

```

---

**Documento**: Transformaciones de DataFrame paso a paso  
**Versión**: v4.10  
**Status**: ✅ Explicación Visual Completa  
**Comprensión**: 100% de transformaciones documentadas
