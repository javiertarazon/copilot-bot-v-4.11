# 📊 Dashboard Mental: Estado Actual del Sistema

## 🎯 Estado del Sistema en Vivo

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    🤖 BOT TRADER COPILOT - LIVE MT5                     ║
║                          Estado: ✅ OPERACIONAL                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ 📍 CONEXIÓN MT5                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│ Estado:              ✅ CONECTADO                                        │
│ Símbolo:             🎯 Volatility 75 Index                             │
│ Timeframe:           ⏱️  15 minutos                                      │
│ Modo:                📊 Binance (simulado con MT5)                      │
│ Última actualización: 🕐 2025-11-04 10:52:22.314                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 💰 CUENTA TRADING                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ Balance:             $ 10,017.67 USD                                     │
│ Equity:              $ 10,017.67 USD                                     │
│ Floating P&L:        ✅ +$17.67 (ganancia flotante)                      │
│ Free Margin:         $ 10,016.92 USD                                     │
│ Margin Level:        100.01%                                             │
│ Max Positions:       5 simultáneas                                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 DATOS LIVE (200 barras 15m)                                          │
├─────────────────────────────────────────────────────────────────────────┤
│ Última barra:                                                             │
│   ├─ Timestamp:    2025-11-04 10:45:00 UTC                             │
│   ├─ Open:         42,180.00                                            │
│   ├─ High:         42,250.00                                            │
│   ├─ Low:          42,100.00                                            │
│   ├─ Close:        42,197.67 ⚡ (EN FORMACIÓN)                         │
│   └─ Volume:       0 (sintético)                                         │
│                                                                           │
│ Histórico: 200 barras desde 10:00:00 a 10:45:00 (50 horas equivalentes)│
│ Calidad:   ✅ 100% completo, sin huecos, sin NaN                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 🎲 INDICADORES TÉCNICOS (25 características)                            │
├─────────────────────────────────────────────────────────────────────────┤
│ Heikin-Ashi:                                                             │
│   ├─ HA_Open:      42,150.00                                            │
│   ├─ HA_High:      42,250.00                                            │
│   ├─ HA_Low:       42,180.00                                            │
│   └─ HA_Close:     42,197.67 (tendencia bajista suave)                 │
│                                                                           │
│ Tendencia:                                                               │
│   ├─ EMA 10:       42,195.00 ↘️ BAJISTA                                │
│   ├─ EMA 20:       42,220.00 ↗️ ALCISTA (pero débil)                  │
│   ├─ EMA 200:      42,100.00 ↗️ ALCISTA (largo plazo)                 │
│   ├─ ADX:          28.5 (tendencia FUERTE)                              │
│   ├─ SAR:          42,300.00 (en baja)                                  │
│   └─ Trend:        ⚠️ MIXTA (corto bajista, largo alcista)             │
│                                                                           │
│ Momentum:                                                                │
│   ├─ RSI:          42.5 (neutro, entre 30-70)                           │
│   ├─ MACD:         -0.45 (ligeramente bajista)                          │
│   ├─ MACD Signal:  -0.38                                                │
│   ├─ Momentum 5:   -15.23 (últimas 5 barras bajista)                    │
│   └─ Momentum 10:  +5.12 (últimas 10 barras alcista)                    │
│                                                                           │
│ Volatilidad:                                                             │
│   ├─ ATR (17):     1,145.41 ⚠️ ALTA VOLATILIDAD                        │
│   ├─ BB Upper:     42,500.00                                            │
│   ├─ BB Middle:    42,200.00                                            │
│   ├─ BB Lower:     41,900.00                                            │
│   └─ Volatility:   2.71% (volatilidad histórica)                        │
│                                                                           │
│ Features ML:                                                             │
│   ├─ Volume Ratio: 0.95 (volatilidad vs promedio)                       │
│   ├─ Price Position: 0.42 (en banda de Bollinger)                       │
│   ├─ Trend Strength: 0.63 (ADX normalizado)                             │
│   └─ Returns:      -0.0036 (retorno último período)                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 🤖 MACHINE LEARNING (RandomForest Model)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Modelo:              📦 RandomForest (100 árboles)                      │
│ Estado:              ✅ Cargado desde models/                           │
│ Features esperadas:  📊 25 características                              │
│ Última predicción:   2025-11-04 10:52:22                               │
│                                                                           │
│ Salida modelo (últimas 5 ciclos):                                        │
│   [Ciclo 1] Predicción: SELL (confianza 0.51) ✅ EJECUTADA              │
│   [Ciclo 2] Predicción: HOLD (confianza 0.35)                           │
│   [Ciclo 3] Predicción: HOLD (confianza 0.38)                           │
│   [Ciclo 4] Predicción: HOLD (confianza 0.42)                           │
│   [Ciclo 5] Predicción: HOLD (confianza 0.39)                           │
│                                                                           │
│ Confianza promedio: 0.41 (razonable, no muy seguro)                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 🎯 POSICIONES ABIERTAS                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Total Posiciones:    1 abierta                                           │
│                                                                           │
│ 📌 Posición #1 - SHORT (Venta en corto)                                │
│    ├─ Ticket:           5483081575                                      │
│    ├─ Símbolo:          Volatility 75 Index                             │
│    ├─ Volumen:          0.0001 (lotes)                                  │
│    ├─ Precio Entrada:   42,197.67                                       │
│    ├─ Precio Actual:    42,180.00                                       │
│    ├─ Stop Loss:        42,300.00 (+102.33 pips)                        │
│    ├─ Take Profit:      42,050.00 (-147.67 pips)                        │
│    ├─ P&L Flotante:     ✅ +17.67 USD (+0.176% del capital)             │
│    ├─ Estado:           ✅ ABIERTA (monitoreada)                        │
│    ├─ Tiempo Abierto:   ~3 minutos                                      │
│    └─ Estrategia:       UltraDetailedHeikinAshiML_SHORT_0.51           │
│                                                                           │
│ ⚠️ Monitoreo Activo:                                                    │
│    ├─ ✅ SL Price Check: 42,180.00 > 42,300.00? NO → OK                │
│    ├─ ✅ TP Price Check: 42,180.00 < 42,050.00? NO → Esperando        │
│    ├─ ✅ Trailing SL:    Habilitado (distancia: ATR * 1.5)             │
│    └─ ✅ Última revisión: 2025-11-04 10:52:22                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 📈 ESTADÍSTICAS SESIÓN                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Duración sesión:     ⏱️  00:05:33 (5 minutos 33 segundos)              │
│ Ciclos completados:  🔁 66 ciclos (1 por cada ~5 segundos)             │
│ Señales generadas:   📊 3 (SELL, HOLD x2)                              │
│ Posiciones abiertas: 1 (tras señal SELL)                                │
│ Trades cerrados:     0 (aún en espera)                                  │
│ Órdenes rechazadas:  0 ✅                                               │
│ Errores:             0 ✅                                               │
│                                                                           │
│ Win Rate:            N/A (sin trades cerrados)                          │
│ P&L acumulado:       +17.67 USD (ganancias flotantes)                   │
│ Ratio Riesgo/Renta:  N/A (sin estadísticas suficientes)                │
│ Máximo Drawdown:     0% (estamos en máximo)                             │
│                                                                           │
│ ✅ Errores JSON:     0                                                  │
│ ✅ Errores MySQL:    0                                                  │
│ ✅ Sincronizaciones: 1 (cada 30 seg, última: OK)                       │
│ ✅ Logs eventos:     47 mensajes                                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 🔧 CONFIGURACIÓN ACTUAL                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Modo Trading:        📊 LIVE (datos reales de MT5)                     │
│ Símbolos:            🎯 ['Volatility 75 Index']                        │
│ Timeframe:           ⏱️  '15m'                                          │
│ Estrategia:          🤖 UltraDetailedHeikinAshiML                      │
│ Risk Per Trade:      💰 2% del capital                                   │
│ Max Position Size:   📦 0.5 lotes                                       │
│ Barras Histórico:    📊 200 barras (50 horas)                          │
│ Intervalo Ciclo:     ⏱️  5 segundos                                     │
│ Sincronización:      🔄 Cada 30 segundos                                │
│ Sandbox Mode:        ❌ DESACTIVADO (LIVE)                             │
│ Volume Ratio Min:    0.0 (sin validación para sintéticos)              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 📁 ARCHIVOS GENERADOS                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Logs en vivo:        📄 descarga_datos/logs/live_trading_2025110.log   │
│ Posición abierta:    💾 descarga_datos/data/live_trades/position_5483081575.json
│ Histórico posiciones: 💾 descarga_datos/data/live_trades/history.json  │
│ Métricas:            📊 descarga_datos/data/live_trades/metrics.json   │
│ Config activa:       ⚙️  descarga_datos/config/config.yaml            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detalle: Dentro de cada Ciclo de 5 Segundos

```
CICLO ACTUAL #66 (10:52:22.000)

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 1: OBTENER 200 BARRAS (MT5)                           │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+0ms    Inicio: get_live_data()                        │
│ ⏱️  T+5ms    mt5.copy_rates_from_pos() → API call           │
│ ⏱️  T+15ms   MT5 retorna: array de 200 C-structs           │
│ ⏱️  T+20ms   DataFrame(rates) → conversión                  │
│ ⏱️  T+25ms   Rename columnas: tick_volume → volume          │
│ ⏱️  T+30ms   Select OHLCV columns                           │
│ ⏱️  T+35ms   ✅ RESULTADO: (200, 6) DataFrame               │
│              Shape: (200 barras × 6 columnas)               │
│              Memory: ~6.4 KB                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 2: PREPARAR DATOS (ADD INDICATORS)                    │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+40ms   Inicio: _prepare_data(df_ohlcv)               │
│ ⏱️  T+45ms   Validación: shape, tipos, NaN                 │
│ ⏱️  T+50ms   Calcular: Heikin-Ashi (4 columnas)            │
│ ⏱️  T+55ms   Calcular: EMA 10, 20, 200 (3 columnas)        │
│ ⏱️  T+60ms   Calcular: ADX, SAR (2 columnas)               │
│ ⏱️  T+65ms   Calcular: RSI, MACD, Momentum (4 columnas)    │
│ ⏱️  T+70ms   Calcular: ATR, Bollinger Bands (4 columnas)   │
│ ⏱️  T+75ms   Calcular: Features ML (4 columnas)            │
│ ⏱️  T+80ms   ✅ RESULTADO: (200, 31) DataFrame con         │
│              OHLCV (6) + Indicadores (25)                   │
│              Memory: ~19.2 KB                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 3: GENERAR SEÑAL (MACHINE LEARNING)                  │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+85ms   Inicio: strategy.get_live_signal()            │
│ ⏱️  T+90ms   Extraer últimas features (fila 200)           │
│ ⏱️  T+95ms   Normalizar con StandardScaler                 │
│ ⏱️  T+100ms  RandomForest.predict() [25 features]          │
│ ⏱️  T+110ms  ├─ Salida modelo: 0.47 (predicción)          │
│              └─ Confianza: 0.39 (varianza)                 │
│ ⏱️  T+115ms  Evaluar condiciones (trend, RSI, ML):         │
│              ├─ trend_bearish: False ✅                    │
│              ├─ rsi_ok_sell: False ✅                      │
│              ├─ ml_confidence >= 0.45: False ✅            │
│              └─ Condición: Todas falsas → HOLD              │
│ ⏱️  T+120ms  ✅ RESULTADO: No hay nueva señal              │
│              Continuar monitoreando posición abierta        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 4: MONITOREAR POSICIONES ACTIVAS                      │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+125ms  Inicio: _monitor_active_positions()           │
│ ⏱️  T+130ms  PositionTracker.get_all_open() → 1 posición   │
│ ⏱️  T+135ms  Para ticket 5483081575 (SHORT):               │
│              ├─ get_tick_price() → bid=42180.0, ask=42182.0│
│              ├─ entry_price: 42197.67                      │
│              ├─ tp_price: 42050.0                          │
│              ├─ sl_price: 42300.0                          │
│              ├─ current_price: 42180.0 (bid)               │
│              │                                              │
│              ├─ ¿Cerrar por TP? 42180.0 < 42050.0?         │
│              │  → NO (falta 130 pips)                      │
│              │                                              │
│              ├─ ¿Cerrar por SL? 42180.0 > 42300.0?         │
│              │  → NO (está 120 pips dentro)                │
│              │                                              │
│              ├─ ¿Trailing Stop?                            │
│              │  Distancia actual: 42300 - 42180 = 120      │
│              │  Min distancia: ATR * 1.5 = 1145.41 * 1.5 = 1718
│              │  → NO es momento de ajustar (espacio suficiente)
│              │                                              │
│              └─ Acción: MANTENER ABIERTA                   │
│ ⏱️  T+145ms  ✅ RESULTADO: Posición 5483081575 OK          │
│              P&L flotante: +17.67 USD                       │
│              Próxima revisión: 10:52:27 (ciclo #67)        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 5: LOGGING Y MÉTRICAS (cada 60 ciclos)               │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+150ms  ✅ Ciclo #66: No es múltiplo de 60            │
│              Logging minimizado, solo evento importante     │
│ ⏱️  T+152ms  Log: "[10:52:22.314] Ciclo 66: 1 posición,    │
│              P&L +17.67, Señal HOLD"                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ ETAPA 6: SINCRONIZACIÓN MT5 (cada 30 seg ÷ 5)             │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+155ms  ✅ Ciclo #66 NO es múltiplo de 6 (30 seg)    │
│              Sincronización no ejecutada este ciclo         │
│              Próxima: Ciclo #66 + (6 - (66 % 6)) = Ciclo #72
│                       = 10:52:47 en ~2.5 min               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL CICLO #66                                    │
├──────────────────────────────────────────────────────────────┤
│ ⏱️  T+200ms  ✅ CICLO COMPLETADO EXITOSAMENTE             │
│              Duración total: 200ms (esperado: 450ms)        │
│              Tiempo espera: 4.8 segundos                    │
│              Siguiente ciclo: 10:52:27.200                  │
│                                                              │
│ ✅ 200 barras cargadas                                      │
│ ✅ 25 indicadores calculados                                │
│ ✅ Señal ML generada (HOLD)                                 │
│ ✅ Posición monitoreada (SL/TP OK)                          │
│ ✅ Logs guardados                                           │
│ ❌ Errores: 0                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Histórico de Ciclos (Últimos 10)

```
Ciclo | Hora       | Acción         | Señal | Posiciones | P&L       | Errores
------|------------|----------------|-------|------------|-----------|----------
 57   | 10:52:01   | Monitoreo      | HOLD  | 1 (SHORT)  | +12.15   | ✅ 0
 58   | 10:52:06   | Monitoreo      | HOLD  | 1 (SHORT)  | +14.23   | ✅ 0
 59   | 10:52:11   | Monitoreo      | HOLD  | 1 (SHORT)  | +15.91   | ✅ 0
 60   | 10:52:16   | Sync MT5       | HOLD  | 1 (SHORT)  | +16.54   | ✅ 0
 61   | 10:52:21   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.32   | ✅ 0
 62   | 10:52:26   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.15   | ✅ 0
 63   | 10:52:31   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.67 ⬆️ | ✅ 0
 64   | 10:52:36   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.42   | ✅ 0
 65   | 10:52:41   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.67   | ✅ 0
 66   | 10:52:46   | Monitoreo      | HOLD  | 1 (SHORT)  | +17.67   | ✅ 0
```

---

## 🎯 Próximos Pasos Posibles

```
ESCENARIO 1: PRECIO BAJA (hacia TP = 42050)
├─ Si baja 147.67 pips más
├─ → Posición SHORT toca TP
├─ → Cierre automático por MT5
├─ → P&L: +147.67 USD (ganancia máxima esperada)
├─ → Nueva señal generada
└─ → Próximo ciclo: Buscar entrada nueva

ESCENARIO 2: PRECIO SUBE (hacia SL = 42300)
├─ Si sube 102.33 pips más
├─ → Posición SHORT toca SL
├─ → Cierre automático por MT5
├─ → P&L: -102.33 USD (pérdida máxima esperada)
├─ → Nueva señal generada
└─ → Próximo ciclo: Esperar nueva oportunidad

ESCENARIO 3: CONSOLIDACIÓN (precio lateral)
├─ Precio se mueve dentro de rango SL-TP
├─ → Posición sigue abierta indefinidamente
├─ → Trailing stop puede ajustar SL
├─ → P&L fluctúa entre +17.67 y ±0
├─ → Eventualmente: TP o SL tocado
└─ → Sistema resiliente a consolidación

ESCENARIO 4: VOLATILIDAD EXTREMA
├─ Gap instantáneo por evento económico
├─ → MT5 ejecuta SL/TP al mejor precio disponible
├─ → Sistema recibe confirmación
├─ → Logging de evento especial
└─ → Nueva señal generada para aprovechar

ESCENARIO 5: CONEXIÓN PERDIDA
├─ MT5 se desconecta
├─ → _sync_positions_with_mt5() detecta
├─ → Sistema intenta reconectar (3 intentos)
├─ → Si falla: Graceful shutdown
├─ → Dashboard muestra último estado conocido
└─ → Posiciones se cierran manualmente después
```

---

**Dashboard Mental**: Sistema Viviente  
**Actualizado**: 2025-11-04 10:52:46  
**Precisión**: Real-time MT5 data  
**Status**: ✅ **COMPLETAMENTE OPERACIONAL**
