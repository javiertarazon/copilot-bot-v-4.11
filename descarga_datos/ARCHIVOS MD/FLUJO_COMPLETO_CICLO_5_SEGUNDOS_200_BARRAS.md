# 🔄 Flujo Completo: Ciclo de 5 Segundos en Live MT5 con 200 Barras 15m

## 📍 Timeline: ¿Qué ocurre cada 5 segundos?

```
CICLO #1 (10:52:17)
├─ 10:52:17.00 - Inicio ciclo
│  ├─ get_live_data() → MT5.copy_rates_from_pos() → 200 barras
│  │  └─ Returns DataFrame (200, 6)
│  │     ├─ timestamp: 2025-11-04 10:00:00 a 10:47:00 (últimas 47 barras + histórico)
│  │     ├─ open:     42100.5, 42120.0, ..., 42197.67 (actual)
│  │     ├─ high:     42150.0, 42200.0, ..., 42250.0
│  │     ├─ low:      42050.0, 42100.0, ..., 42100.0
│  │     ├─ close:    42120.0, 42180.0, ..., 42197.67 (cierre barra actual)
│  │     └─ volume:   0, 0, ..., 0 (sintético)
│  │
│  ├─ _prepare_data(df) → Agregar 25 indicadores técnicos
│  │  └─ Returns DataFrame (200, 31) con:
│  │     ├─ Heikin-Ashi: ha_open, ha_high, ha_low, ha_close
│  │     ├─ Tendencia: ema_10, ema_20, ema_200, adx, sar
│  │     ├─ Momentum: macd, macd_signal, rsi, momentum_5, momentum_10
│  │     ├─ Volatilidad: atr, bb_upper, bb_middle, bb_lower, volatility
│  │     └─ Features ML: volume_ratio, price_position, trend_strength, returns
│  │
│  ├─ strategy.get_live_signal(df_prepared) → ML prediction
│  │  ├─ Extraer últimas 25 features de la fila 200
│  │  ├─ Normalizar con StandardScaler
│  │  ├─ RandomForest.predict() → confianza 0.2-0.8
│  │  ├─ Evaluar condiciones:
│  │  │  ├─ ¿trend_bearish = True? ✅
│  │  │  ├─ ¿rsi_ok_sell = True? ✅
│  │  │  ├─ ¿ml_confidence >= threshold? ✅
│  │  │  └─ → SELL signal ✅
│  │  └─ Returns:
│  │     {
│  │       'signal': 'SELL',
│  │       'signal_data': {
│  │         'direction': 'short',
│  │         'entry_price': 42197.67,
│  │         'stop_loss_price': 42300.0,
│  │         'take_profit_price': 42050.0,
│  │         'position_size': 0.0001,
│  │         'ml_confidence': 0.51
│  │       }
│  │     }
│  │
│  ├─ AdvancedRiskManager.calculate_position_size()
│  │  ├─ balance = 10000 USD
│  │  ├─ risk_per_trade = 0.02 (2%)
│  │  ├─ atr_value = 1145.41 (del indicador ATR17)
│  │  ├─ Fórmula: position_size = 10000 * 0.02 / 1145.41
│  │  └─ position_size = 0.0001747 (redondeado a 0.0001)
│  │
│  ├─ MT5OrderExecutor.open_short_position()
│  │  ├─ Crear orden:
│  │  │  ├─ type = mt5.ORDER_TYPE_SELL
│  │  │  ├─ symbol = 'Volatility 75 Index'
│  │  │  ├─ volume = 0.0001
│  │  │  ├─ price = 42197.67 (precio actual)
│  │  │  ├─ sl = 42300.0 (42197.67 + ATR*2.25)
│  │  │  ├─ tp = 42050.0 (42197.67 - ATR*3.75)
│  │  │  └─ comment = "UltraDetailedHeikinAshiML_SHORT_0.51"
│  │  │
│  │  ├─ mt5.order_send(request) → Enviada a MT5
│  │  │  └─ MT5 ejecuta inmediatamente
│  │  │
│  │  └─ Returns: {'order': 5483081575, 'price': 42197.67}
│  │
│  ├─ _record_trade_opened()
│  │  ├─ Guardar en PositionTracker local:
│  │  │  ticket: 5483081575
│  │  │  symbol: 'Volatility 75 Index'
│  │  │  entry_price: 42197.67
│  │  │  direction: 'short'
│  │  │  volume: 0.0001
│  │  │  sl: 42300.0
│  │  │  tp: 42050.0
│  │  │  entry_time: 2025-11-04 10:52:17
│  │  │  status: 'OPEN'
│  │  │
│  │  └─ Guardar en JSON: descarga_datos/data/live_trades/position_5483081575.json
│  │
│  └─ 10:52:17.50 - Fin del procesamiento
│
├─ (esperar 5 segundos)
│
CICLO #2 (10:52:22)
├─ 10:52:22.00 - Inicio ciclo
│  ├─ get_live_data() → MT5.copy_rates_from_pos()
│  │  └─ Returns DataFrame ACTUALIZADO:
│  │     ├─ timestamp: 10:05:00 a 10:52:00 (NUEVAS barras)
│  │     ├─ close: [..., 42190.0, 42185.0] (nuevas velas 15m)
│  │     └─ NOTA: Barra que fue cierre en ciclo #1 ahora en middle
│  │
│  ├─ _prepare_data(df) → Recalcular 25 indicadores con datos nuevos
│  ├─ strategy.get_live_signal(df_prepared) → Evaluar
│  │  └─ RESULTADO: No hay señal (no cumple condiciones)
│  │
│  ├─ _monitor_active_positions()
│  │  ├─ Para ticket 5483081575 SHORT @ 42197.67:
│  │  │  ├─ Obtener tick actual: bid=42185.0, ask=42187.0
│  │  │  ├─ tp_price = 42050.0
│  │  │  ├─ sl_price = 42300.0
│  │  │  ├─ Checks:
│  │  │  │  ├─ current_price (42185.0) >= tp_price (42050.0)? ✅ NO ALCANZADO TODAVÍA
│  │  │  │  ├─ current_price (42185.0) <= sl_price (42300.0)? ✅ DENTRO
│  │  │  │  └─ → Posición sigue ABIERTA
│  │  │  │
│  │  │  └─ Trailing Stop (si habilitado):
│  │  │     ├─ Si es SHORT y price bajo new low:
│  │  │     │  └─ Ajustar SL hacia nuevo nivel
│  │  │     └─ Asegurar ganancias progresivamente
│  │  │
│  │  └─ Resultado: Posición sigue en monitoreo
│  │
│  ├─ _sync_positions_with_mt5() [CADA 30 seg, aquí NO]
│  │  └─ (Se ejecuta en ciclo #6 → 10:52:47)
│  │
│  └─ 10:52:22.30 - Fin
│
├─ (esperar 5 segundos)
│
... (ciclos #3-#6 similares: lectura datos → evaluación → monitoreo)

CICLO #7 (10:52:47) ← SINCRONIZACIÓN
├─ 10:52:47.00 - Inicio
│  ├─ get_live_data() → 200 barras
│  ├─ get_live_signal() → Evaluar
│  ├─ _monitor_active_positions() → Verificar
│  │
│  ├─ _sync_positions_with_mt5() [Ejecución en este ciclo]
│  │  ├─ PositionTracker local: 1 posición (5483081575)
│  │  │  └─ SHORT @ 42197.67, SL 42300, TP 42050
│  │  │
│  │  ├─ mt5.positions_get(symbol='Volatility 75 Index')
│  │  │  └─ MT5 retorna: [posición 5483081575]
│  │  │     ├─ ticket: 5483081575
│  │  │     ├─ entry_price: 42197.67
│  │  │     ├─ current_price: 42180.0
│  │  │     ├─ type: SELL
│  │  │     ├─ volume: 0.0001
│  │  │     └─ pnl: +17.67 (ganancia flotante)
│  │  │
│  │  ├─ COMPARAR:
│  │  │  ├─ Local: 1 posición
│  │  │  ├─ MT5: 1 posición
│  │  │  └─ Coincidencias: 1 ✅
│  │  │     Desajustes: 0 ✅
│  │  │
│  │  └─ LOG: "Sincronización MT5: 1 coincidencias, 0 desajustes, 0 cierres externos"
│  │
│  └─ 10:52:47.50 - Fin
│
└─ (continuar ciclos...) 

CICLO #12 (10:53:13) ← MÉTRICAS
├─ 10:53:13.00 - Inicio
│  ├─ get_live_data() → 200 barras
│  ├─ get_live_signal() → Evaluar
│  ├─ _monitor_active_positions() → Verificar
│  ├─ _sync_positions_with_mt5() [cada 30s, no ejecuta aquí]
│  │
│  ├─ _log_metrics() [CADA 60 ciclos ÷ 5 seg = cada ~10 ciclos]
│  │  ├─ Calcular métricas actuales:
│  │  │  ├─ Total trades: 0 (abiertos, no cerrados)
│  │  │  ├─ Win rate: 0% (no hay trades cerrados aún)
│  │  │  ├─ P&L actual: +17.67 USD (ganancias flotantes)
│  │  │  ├─ Posiciones abiertas: 1 (SHORT 5483081575)
│  │  │  └─ Account balance: 10017.67 USD (10000 + flotante)
│  │  │
│  │  └─ LOG: "Métricas actuales - P&L: +17.67, Trades: 0, Win Rate: 0.00"
│  │
│  └─ 10:53:13.30 - Fin
│
└─ (continuar ciclos indefinidamente hasta Ctrl+C)
```

---

## 🔍 Zoom: Inside get_live_data() - Llamada a MT5

```python
# Línea exacta donde ocurre la "magia":
rates = mt5.copy_rates_from_pos(
    'Volatility 75 Index',  # Símbolo
    mt5.TIMEFRAME_M15,      # 15 minutos
    0,                      # pos=0 → desde la barra más reciente
    200                     # Últimas 200 barras
)

# ¿Qué retorna?
# Es un array de tuplas C (estructuras):
# [
#   (time=1730688600, open=42100.5, high=42150.0, low=42050.0, close=42120.0, tick_volume=0, spread=0, real_volume=0),
#   (time=1730688900, open=42120.0, high=42200.0, low=42100.0, close=42180.0, tick_volume=0, spread=0, real_volume=0),
#   ...
#   (time=1730696400, open=42180.0, high=42250.0, low=42170.0, close=42197.67, tick_volume=0, spread=0, real_volume=0),
# ]
#
# TOTAL: 200 tuplas (barras)
```

---

## 📊 Ejemplo: DataFrame en cada ciclo

### Ciclo #1 (10:52:17)
```
Llamada: get_live_data('Volatility 75 Index', '15m', 200)

Resultado DataFrame:
    timestamp            open       high        low      close  volume
0   2025-11-04 10:00:00  42100.50   42150.00   42050.00  42120.00     0
1   2025-11-04 10:15:00  42120.00   42200.00   42100.00  42180.00     0
2   2025-11-04 10:30:00  42180.00   42250.00   42170.00  42200.00     0
...
197 2025-11-04 10:35:00  42150.00   42300.00   42100.00  42250.00     0
198 2025-11-04 10:40:00  42200.00   42350.00   42150.00  42300.00     0
199 2025-11-04 10:45:00  42250.00   42400.00   42200.00  42350.00     0  ← ÚLTIMA BARRA (casi completa)

Shape: (200, 6)

Nota: La barra #199 es la que se está formando en este momento
      Se actualiza cada 5 segundos
```

### Ciclo #2 (10:52:22 - 5 segundos después)
```
Llamada: get_live_data('Volatility 75 Index', '15m', 200)

Resultado DataFrame ACTUALIZADO:
    timestamp            open       high        low      close  volume
0   2025-11-04 10:05:00  42100.00   42180.00   42050.00  42160.00     0  ← NUEVO
1   2025-11-04 10:20:00  42160.00   42250.00   42140.00  42200.00     0
2   2025-11-04 10:35:00  42200.00   42300.00   42180.00  42250.00     0
...
198 2025-11-04 10:40:00  42250.00   42350.00   42200.00  42300.00     0  ← AHORA EN POSICIÓN 198
199 2025-11-04 10:45:00  42300.00   42400.00   42250.00  42350.00     0  ← ÚLTIMA (BARRA QUE ERA #199 CERRÓ)

Shape: (200, 6)

¡IMPORTANTE!: 
- Barra #199 del ciclo #1 cerró oficialmente
- Nueva barra #199 iniciada (posición #199 en ciclo #2)
```

---

## 🎯 ¿Por qué necesitamos TODAS las 200 barras cada ciclo?

```
Razón 1: INDICADORES DEPENDIENTES
├─ EMA 200 necesita 200 datos históricos
├─ ADX necesita 14+ datos
├─ MACD necesita 26 datos
├─ Heikin-Ashi necesita continuidad
└─ Sin histórico: indicadores imprecisos

Razón 2: HEIKIN-ASHI REQUIERE CONTINUIDAD
├─ HA_Close[t] depende de OHLC[t]
├─ HA_Open[t] depende de HA_Open[t-1] + HA_Close[t-1]
├─ HA_High[t] depende de max(HA_Open[t], HA_Close[t], HA_High[t-1])
└─ Sin barras previas: HA incorrecta

Razón 3: MACHINE LEARNING
├─ RandomForest entrena con 25 features
├─ Cada feature requiere histórico para normalización
├─ StandardScaler calcula media/std sobre datos
└─ Más datos históricos = normalización más precisa

Razón 4: DETECCIÓN DE TENDENCIA
├─ RSI necesita 14 barras
├─ EMA 200 necesita 200 barras para sentimiento largo plazo
├─ SAR necesita continuidad
└─ Tendencia confiable requiere histórico

Razón 5: ATR PARA RIESGO
├─ ATR 17 necesita 17 barras
├─ Position sizing depende de ATR
├─ Sin ATR confiable: posición mal dimensionada
└─ Histórico asegura ATR estable
```

---

## 🔄 Ciclo Detallado: Línea Temporal

```
CICLO #1
├─ 10:52:17.00s: Inicio
│  ├─ 10:52:17.05s: mt5.copy_rates_from_pos()
│  │  └─ MT5 retorna 200 barras instantáneamente
│  │
│  ├─ 10:52:17.10s: pd.DataFrame(rates) → Conversión
│  │
│  ├─ 10:52:17.15s: _prepare_data() → Cálc indicadores
│  │  └─ Recalcular 25 indicadores en 200 filas
│  │
│  ├─ 10:52:17.20s: strategy.get_live_signal()
│  │  ├─ Extraer features últimas fila
│  │  ├─ StandardScaler.transform()
│  │  ├─ RandomForest.predict()
│  │  └─ Evaluar condiciones: SELL ✅
│  │
│  ├─ 10:52:17.25s: AdvancedRiskManager
│  │  └─ Calcular position_size = 0.0001
│  │
│  ├─ 10:52:17.30s: MT5OrderExecutor.open_short_position()
│  │  ├─ Crear orden
│  │  ├─ mt5.order_send() → MT5 ejecuta
│  │  └─ Retorna ticket 5483081575
│  │
│  ├─ 10:52:17.35s: _record_trade_opened()
│  │  └─ Guardar en PositionTracker + JSON
│  │
│  ├─ 10:52:17.40s: _monitor_active_positions()
│  │  └─ Verificar SL/TP (posición nueva, check básico)
│  │
│  └─ 10:52:17.50s: Fin ciclo (450ms total)
│
└─ 10:52:17.50s - 10:52:22.00s: ESPERAR 4.5 segundos

CICLO #2
├─ 10:52:22.00s: Inicio
│  ├─ 10:52:22.05s: mt5.copy_rates_from_pos()
│  │  └─ MT5 retorna 200 barras NUEVAS (barra anterior cerró)
│  │
│  ├─ 10:52:22.40s: strategy.get_live_signal()
│  │  └─ Sin señal (condiciones no se cumplen)
│  │
│  ├─ 10:52:22.45s: _monitor_active_positions()
│  │  ├─ Ticket 5483081575 SHORT
│  │  ├─ current_price = 42185.0
│  │  ├─ tp = 42050.0 (NO ALCANZADO)
│  │  ├─ sl = 42300.0 (OK)
│  │  └─ Posición sigue abierta
│  │
│  └─ 10:52:22.50s: Fin ciclo
│
└─ 10:52:22.50s - 10:52:27.00s: ESPERAR 4.5 segundos

... (ciclos similares)

CICLO #7 (10:52:47)
├─ ... (get_live_data, get_signal, monitor)
│
├─ 10:52:47.45s: _sync_positions_with_mt5()
│  ├─ Local tracker: 1 posición
│  ├─ mt5.positions_get(): 1 posición
│  ├─ Coincidencias: 1 ✅
│  ├─ Desajustes: 0 ✅
│  └─ LOG: "Sincronización MT5: 1 coincidencias, 0 desajustes"
│
└─ 10:52:47.50s: Fin ciclo
```

---

## 📈 Gráfico: Evolución de Precio vs SL/TP

```
Precio (Volatility 75 Index)

42400 │                                          ═══════════════════
      │                                      ╱╲
42350 │                                    ╱  ╲╱─────────────────
      │                                  ╱
42300 │ ★ SL (Stop Loss)═════════════════════════════════════════
      │                │
42250 │                │         Precio actual
      │                │╲        (bajando)
42200 │                │ ╲╲╲╲
      │                │    ╲╲╲╲╲╲
42150 │                │         ╲╲
      │                │          ╲
42100 │ Entrada SHORT  │           ╲
      │      42197.67  │            ╲
42050 │ ★ TP (Take Profit)          ╲←─ GANANCIA
      │                              ╲
42000 │                               ╲
      │                                ╲
41950 │────────────────────────────────────────────────────────
      └─────────────────────────────────────────────────────────
        10:45  10:50  10:55  11:00  11:05  11:10  11:15

CICLO #1 (10:52:17): Entrada SHORT @ 42197.67
├─ SL = 42300.0 (si sube 102.33 → pérdida 2% * posición)
├─ TP = 42050.0 (si baja 147.67 → ganancia 3% * posición)
└─ P&L flotante: +17.67 (ganancia actual si precio 42180)

Monitoreo cada 5 segundos:
├─ 10:52:22: price 42180, floating +17.67 ✅
├─ 10:52:27: price 42150, floating +47.67 ✅
├─ 10:52:32: price 42080, floating +117.67 ✅
└─ 10:52:37: price 42050, hit TP, cierre +147.67 ✅ GANANCIA
```

---

## ✅ Validación: Correcta Recepción de 200 Barras

```python
# En _prepare_data():

def _prepare_data(self, df_ohlcv):
    """Preparar datos para estrategia"""
    
    # Validación #1: Tenemos datos?
    if df_ohlcv is None:
        logger.error("DataFrame es None")
        return None
    
    # Validación #2: Cantidad suficiente?
    if len(df_ohlcv) < 50:
        logger.warning(f"Solo {len(df_ohlcv)} barras, necesitamos 50+")
        return None
    
    # Validación #3: Columnas correctas?
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    if not all(col in df_ohlcv.columns for col in required_cols):
        logger.error("Faltan columnas OHLCV")
        return None
    
    # Validación #4: Datos numéricos?
    if not all(df_ohlcv[col].dtype in [float, int] for col in required_cols[1:]):
        logger.error("Datos OHLCV no son numéricos")
        return None
    
    # Validación #5: Sin NaN?
    if df_ohlcv[required_cols].isna().any().any():
        logger.error("Hay NaN en datos OHLCV")
        return None
    
    # Validación #6: Timestamps ordenados?
    if not df_ohlcv['timestamp'].is_monotonic_increasing:
        logger.warning("Timestamps no ordenados, reordenando...")
        df_ohlcv = df_ohlcv.sort_values('timestamp')
    
    # ✅ TODO CORRECTO, proceder
    logger.info(f"✅ Datos validados: {len(df_ohlcv)} barras, {df_ohlcv.shape[1]} columnas")
    
    # Agregar indicadores
    df_with_indicators = add_indicators(df_ohlcv)
    
    return df_with_indicators
```

---

## 🎓 Resumen: Ciclo de 5 Segundos Resumido

| Momento | Acción | Input | Output | Duración |
|---------|--------|-------|--------|----------|
| T+0ms | Inicio ciclo | - | - | - |
| T+50ms | get_live_data() | MT5 API | DataFrame (200,6) | 50ms |
| T+100ms | _prepare_data() | OHLCV | + 25 indicadores | 50ms |
| T+150ms | get_live_signal() | 31 features | SELL/BUY/HOLD | 50ms |
| T+200ms | Risk management | Signal | position_size | 50ms |
| T+250ms | MT5OrderExecutor | Position | Order ticket | 50ms |
| T+300ms | _record_trade() | Ticket | JSON guardado | 50ms |
| T+350ms | Monitor positions | Tickets | SL/TP check | 50ms |
| T+400ms | Logging | Métricas | LOG message | 50ms |
| T+450ms | Fin ciclo | - | - | 450ms |
| T+450-5000ms | ESPERAR | - | - | 4.55s |

**Total**: 5 segundos por ciclo (450ms procesamiento + 4.55s espera)

---

## 🚨 Manejo de Errores en Flujo

```python
try:
    # 1. OBTENER 200 BARRAS
    df = self.data_provider.get_live_data(symbol, '15m', 200)
    if df is None or len(df) < 50:
        logger.warning("Datos insuficientes en ciclo")
        # SKIP este ciclo, intentar siguiente
        continue
    
    # 2. PREPARAR
    df_prep = self._prepare_data(df)
    if df_prep is None:
        logger.warning("Error preparando datos")
        continue
    
    # 3. SEÑAL
    signal = self.strategy.get_live_signal(df_prep)
    if signal is None:
        logger.warning("Error en estrategia")
        continue
    
    # 4. RIESGO
    if signal['signal'] in ['BUY', 'SELL']:
        try:
            self._open_position_mt5(signal)
        except Exception as e:
            logger.error(f"Error abriendo posición: {e}")
            # Logging, NO crash
    
    # 5. MONITOREO
    try:
        self._monitor_active_positions()
    except Exception as e:
        logger.error(f"Error monitoreando: {e}")
        # Logging, NO crash
    
except KeyboardInterrupt:
    logger.info("Usuario interrumpió con Ctrl+C")
    self.shutdown()
    
except Exception as e:
    logger.error(f"Error inesperado en ciclo: {e}")
    # Continue en siguiente ciclo, NO crash
    continue
```

---

**Documento**: Flujo Completo de 5 Segundos  
**Versión**: v4.10  
**Status**: ✅ Implementado y Validado  
**Duración por ciclo**: 450ms procesamiento + 4.55s espera
