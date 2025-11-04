# 📊 COMPARACIÓN ARQUITECTÓNICA: LIVE MT5 vs BACKTEST

## ESTRUCTURA DE SISTEMAS

### BACKTEST ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                        BACKTEST SYSTEM                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. DATA SOURCE                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ SQLite / CSV                                                 │ │
│  │ ├─ Rango: 2025-09-01 a 2025-11-03                          │ │
│  │ ├─ Barras: ~1000+ completas                                 │ │
│  │ ├─ Validación: Gaps verificados                             │ │
│  │ └─ Status: Datos LISTOS para usar ✓                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Datos históricos validados)                           │
│                                                                    │
│  2. STRATEGY EXECUTION                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ UltraDetailedHeikinAshiML                                    │ │
│  │ ├─ Indicadores: ATR, RSI, MACD (pre-calculados)            │ │
│  │ ├─ Normalización: APLICADA (escala estándar)               │ │
│  │ ├─ Señales: 1 por vela (determinísticas)                   │ │
│  │ └─ Output: {signal, price, SL, TP, size} ✓                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Señal generada)                                       │
│                                                                    │
│  3. RISK MANAGEMENT                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ AdvancedRiskManager                                          │ │
│  │ ├─ Balance: Inicial $10,000                                 │ │
│  │ ├─ Risk per trade: 0.5%                                     │ │
│  │ ├─ Position Size: 0.001 (calculado)                         │ │
│  │ ├─ Updated cada trade: ✓ (balance actualizado)            │ │
│  │ └─ Output: position_size = 0.001 ✓                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Position size conocido)                               │
│                                                                    │
│  4. EXECUTION ENGINE                                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ AdvancedBacktester                                           │ │
│  │ ├─ Recibe: Signal + position_size ✓                        │ │
│  │ ├─ Valida: SL < entrada < TP (BUY) ✓                      │ │
│  │ ├─ Simula: Ejecución inmediata                             │ │
│  │ ├─ Comisiones: 0.05% aplicadas                             │ │
│  │ ├─ Resultado: Trade objeto con P&L                         │ │
│  │ └─ Output: P&L = +/- XXX ✓                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Trade ejecutado)                                      │
│                                                                    │
│  5. METRICS CALCULATION                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Backtester Metrics                                           │ │
│  │ ├─ Total Trades: N                                          │ │
│  │ ├─ Win Rate: XX%                                            │ │
│  │ ├─ Profit Factor: X.XX                                      │ │
│  │ ├─ Drawdown: XX%                                            │ │
│  │ └─ Output: Results dashboard ✓                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓                                                         │
│  6. DASHBOARD OUTPUT                                              │
│  ✅ COMPLETE SUCCESS - Metrics válidas, reproducibles              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

### LIVE MT5 ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                      LIVE TRADING SYSTEM                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. DATA SOURCE                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ MT5 API (Streaming)                                          │ │
│  │ ├─ Rango: Últimas 100-200 barras                            │ │
│  │ ├─ Barras: Parciales, pueden estar incompletas              │ │
│  │ ├─ Caché: Guardado indefinidamente (NO se actualiza)        │ │
│  │ ├─ Validation: NINGUNA (se asume que MT5 es correcto)       │ │
│  │ └─ Status: ❌ PROBLEMA - Datos obsoletos                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  │ Problema: Si el caché tiene 10 minutos de antigüedad,       │
│  │ seguirá usando esos datos hasta que se limpie manualmente   │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Datos potencialmente obsoletos)                       │
│                                                                    │
│  2. STRATEGY EXECUTION                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ UltraDetailedHeikinAshiML (MISMO QUE BACKTEST)             │ │
│  │ ├─ Indicadores: ATR, RSI, MACD (calculados en vivo)        │ │
│  │ ├─ Normalización: ❌ NO APLICADA (escala bruta)            │ │
│  │ ├─ Señales: Múltiples por ciclo (mismo timestamp)          │ │
│  │ └─ Output: {signal?, price?, SL?, TP?, size?} ❌          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  │ Problemas:                                                   │ │
│  │ - ATR en escala diferente (1.4523 vs 145.23)               │ │
│  │ - Thresholds de backtest NO aplican                         │ │
│  │ - Señales duplicadas (mismo timestamp N veces)             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Señal potencialmente incorrecta/duplicada)             │
│                                                                    │
│  3. RISK MANAGEMENT                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ AdvancedRiskManager (SIN ACTUALIZACIÓN DINÁMICA)           │ │
│  │ ├─ Balance: Inicial $10,000 (CACHEADO)                     │ │
│  │ ├─ Risk per trade: 0.5%                                     │ │
│  │ ├─ Position Size: 0.001 (calculado)                         │ │
│  │ ├─ Updated cada ciclo: ❌ NO (balance viejo)              │ │
│  │ └─ Output: position_size = 0.001 (pero basado en $$ viejo)│ │
│  └──────────────────────────────────────────────────────────────┘ │
│  │ Problema: Si el balance actual es $9,950 (por trades):     │ │
│  │ - Debería usar $9,950 para calcular riesgo                 │ │
│  │ - PERO usa $10,000 cacheado del inicio                     │ │
│  │ - Resultado: Riesgo calculado incorrectamente              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Position size calculado pero NO USADO)                │
│                                                                    │
│  4. ORCHESTRATOR (DESCONEXIÓN)                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ LiveTradingOrchestrator                                      │ │
│  │ ├─ Recibe: Signal + position_size ✓                        │ │
│  │ ├─ Extrae: position_size del signal_details ✓              │ │
│  │ ├─ PERO LUEGO: ❌ NO PASA A EXECUTOR (quantity=None)      │ │
│  │ ├─ Envía: {signal, price, SL, TP, quantity=None} ❌       │ │
│  │ └─ Output: Signal incompleto                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  │ Problema CRÍTICO:                                            │ │
│  │ - Risk management calcula position_size = 0.001             │ │
│  │ - Orchestrator extrae position_size = 0.001                │ │
│  │ - PERO IGNORA y envía quantity=None al executor            │ │
│  │ - Executor debe recalcular (y lo hace INCORRECTAMENTE)     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Position size perdido en pipeline)                    │
│                                                                    │
│  5. ORDER EXECUTOR (REDONDEO INCORRECTO)                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ MT5OrderExecutor                                             │ │
│  │ ├─ Recibe: quantity=None (NO position_size)                │ │
│  │ ├─ Recalcula: risk_amount = 50.00 (basado en risk_percent) │ │
│  │ ├─ Calcula: lot_size = 0.001111                            │ │
│  │ ├─ Redondea: round(1.111) * 0.001 = 1 * 0.001 = 0.001 ✓ │ │
│  │ │           (En algunos casos)                             │ │
│  │ ├─ Redondea: round(0.1) * 0.001 = 0 * 0.001 = 0.00 ❌    │ │
│  │ │           (En otros casos - cuando risk es bajo)        │ │
│  │ ├─ Envía orden: quantity=0.00 o 0.001 (inconsistente)     │ │
│  │ └─ Output: ❌ MT5 RECHAZA si quantity=0.00                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  │ Problema CRÍTICO:                                            │ │
│  │ - round(0.0001 / 0.001) * 0.001 = 0.00 ❌                 │ │
│  │ - Solution: math.ceil() en lugar de round()                │ │
│  │ - math.ceil(0.1) * 0.001 = 1 * 0.001 = 0.001 ✓           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓ (Orden con volume 0.00)                                │
│                                                                    │
│  6. MT5 ORDER SEND (RECHAZO)                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ MetaTrader 5 API                                             │ │
│  │ ├─ Recibe orden: BUY/SELL, quantity=0.00                   │ │
│  │ ├─ Valida: Volume 0.00 < min_volume 0.001                  │ │
│  │ ├─ Rechaza: "No hay operaciones pendientes"                 │ │
│  │ └─ Output: ❌ ERROR - Position NO se abre                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ↓                                                         │
│  ❌ COMPLETE FAILURE - Sistema bloqueado                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## FLUJO DETALLADO: DÓNDE FALLAMOS

```
╔═══════════════════════════════════════════════════════════════════╗
║           BACKTEST FLOW (Funciona Perfectamente)               ║
╚═══════════════════════════════════════════════════════════════════╝

PASO 1: DATOS LISTOS
├─ Fuente: CSV/SQLite con 1000+ barras
├─ Validación: Gaps verificados
├─ Status: ✅ Datos completos y confiables
└─ Siguiente: Estrategia

PASO 2: ESTRATEGIA GENERA SIGNAL
├─ Entrada: Datos históricos validados
├─ Procesamiento: Indicadores pre-normalizados
├─ Output: Signal {type, price, SL, TP}
├─ Status: ✅ Signal correcta
└─ Siguiente: Risk Management

PASO 3: RISK MANAGEMENT CALCULA POSITION SIZE
├─ Entrada: Balance actual = $10,000
├─ Cálculo: risk_amount = $50, position_size = 0.001
├─ Output: signal_details {position_size: 0.001}
├─ Status: ✅ Position size calculado correctamente
└─ Siguiente: Backtest Engine

PASO 4: BACKTEST ENGINE EJECUTA TRADE
├─ Entrada: Signal + position_size ✅
├─ Validación: SL < entrada < TP
├─ Simulación: Trade con quantity=0.001
├─ Comisiones: Aplicadas
├─ Output: Trade ejecutado con P&L
├─ Status: ✅ Trade simulado correctamente
└─ Siguiente: Metrics

PASO 5: METRICS CALCULADAS
├─ Balance actualizado
├─ Win rate, profit factor, drawdown
├─ Status: ✅ Métricas válidas
└─ RESULTADO FINAL: ✅✅✅ ÉXITO

╔═══════════════════════════════════════════════════════════════════╗
║          LIVE MT5 FLOW (Falla en 3 puntos críticos)            ║
╚═══════════════════════════════════════════════════════════════════╝

PASO 1: DATOS DE MT5 (❌ PROBLEMA 1: DATOS OBSOLETOS)
├─ Fuente: MT5 API streaming
├─ Caché: Guardado indefinidamente
├─ Actualización: NO se actualiza automáticamente
├─ Status: ❌ Datos potencialmente obsoletos
│  └─ Ciclo 1: timestamp 12:45:00 ✓
│  └─ Ciclo 2: timestamp 12:45:00 (MISMA DATA)
│  └─ Ciclo 3: timestamp 12:45:00 (MISMA DATA)
│  └─ ... repite 18 veces
└─ Siguiente: Estrategia (procesa datos duplicados)

PASO 2: ESTRATEGIA GENERA SIGNAL (❌ PROBLEMA 2: SEÑALES DUPLICADAS)
├─ Entrada: Datos duplicados del caché viejo
├─ Procesamiento: Indicadores SIN normalizar
├─ Output: Signal {type, price, SL, TP}
├─ Status: ❌ Señal duplicada (mismo timestamp)
│  └─ Signal 1: SELL a 12:45:00 con precio X
│  └─ Signal 2: SELL a 12:45:00 con precio X (IGUAL)
│  └─ Signal 3: SELL a 12:45:00 con precio X (IGUAL)
└─ Siguiente: Risk Management (recalcula 3 veces innecesariamente)

PASO 3: RISK MANAGEMENT CALCULA POSITION SIZE
├─ Entrada: Balance CACHEADO = $10,000 (viejo)
├─ Cálculo: risk_amount = $50, position_size = 0.001
├─ Output: signal_details {position_size: 0.001}
├─ Status: ✓ Position size calculado
│  └─ PERO: Basado en balance viejo (no equity actual)
│  └─ Si equity real = $9,950, debería ser $49.75 riesgo
└─ Siguiente: Orchestrator (PERO AQUÍ OCURRE EL DESASTRE)

PASO 4A: ORCHESTRATOR RECIBE POSITION SIZE (❌ PROBLEMA 3: NO LO PASA)
├─ Entrada: signal_details {position_size: 0.001}
├─ Acción: Extrae position_size = 0.001
├─ PROBLEMA: ❌ NO PASA AL EXECUTOR
├─ Envía: result = executor.open_position(
│           symbol='Volatility 75',
│           quantity=None,  ❌❌❌ INCORRECTO
│           ...
│          )
├─ Status: ❌ Position size perdido en pipeline
└─ Siguiente: Executor (sin position_size)

PASO 4B: EXECUTOR RECIBE quantity=None (❌ PROBLEMA 4: REDONDEO A 0.00)
├─ Entrada: quantity=None (no sabe qué tamaño usar)
├─ Acción: Recalcula lot_size
│  └─ risk_amount = 50.00 (de risk_percent)
│  └─ effective_stop = 45 puntos
│  └─ lot_size = 50 / (45 * 1.0) = 0.0011111
│  └─ Redondeo VIEJO: round(0.0011111 / 0.001) * 0.001
│     └─ = round(1.111) * 0.001
│     └─ = 1 * 0.001
│     └─ = 0.001 ✓ (Este funciona)
│  └─ PERO CUANDO RISK ES MÁS BAJO:
│     └─ risk_amount = 5.00 (si risk_percent es 0.05%)
│     └─ lot_size = 5 / (45 * 1.0) = 0.0001111
│     └─ Redondeo VIEJO: round(0.0001111 / 0.001) * 0.001
│        └─ = round(0.1111) * 0.001
│        └─ = round(0.1111) = 0
│        └─ = 0 * 0.001
│        └─ = 0.00 ❌❌❌ CERO!
├─ Output: lot_size = 0.00
├─ Status: ❌ Lote inválido
└─ Siguiente: MT5 API (envía orden con 0.00)

PASO 5: MT5 RECHAZA ORDEN
├─ Recibe: BUY/SELL con quantity=0.00
├─ Validación: 0.00 < min_volume 0.001
├─ Resultado: RECHAZADA
├─ Error: "No hay operaciones pendientes"
├─ Status: ❌ Orden NO se ejecuta
└─ RESULTADO FINAL: ❌❌❌ FALLA TOTAL

DÓNDE FALLAMOS (3 PUNTOS):
1. ❌ Datos obsoletos → Señales duplicadas
2. ❌ Position size ignorado → Recalculado incorrectamente
3. ❌ Redondeo incorrecto → Lote = 0.00
```

---

## COMPARATIVA DE MÓDULOS

### 1. DATA ACQUISITION

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Fuente: SQLite/CSV          │ Fuente: MT5 API             │
│ ✅ Datos históricos         │ ❌ Datos parciales          │
│ ✅ Rango completo           │ ❌ Últimas N barras         │
│ ✅ Validación de gaps       │ ❌ Sin validación           │
│ ✅ Sin latencia de red      │ ❌ Latencia N segundos      │
│ ✅ Determinístico           │ ❌ No determinístico        │
│ ✅ Reproducible             │ ❌ No reproducible          │
│ ✅ Datos conocidos de inicio│ ❌ Datos streaming continuo │
└─────────────────────────────┴─────────────────────────────┘
```

### 2. INDICATOR CALCULATION

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Normalización: ✅ APLICADA  │ Normalización: ❌ NO        │
│ ATR escala: Real (145.23)   │ ATR escala: Bruta (1.4523)  │
│ RSI escala: 0-100 ✅        │ RSI escala: 0-100 ✅        │
│ Consistencia: ✅ Con config │ Consistencia: ❌ Diferente  │
│ Thresholds: ✅ Aplican      │ Thresholds: ❌ No aplican   │
└─────────────────────────────┴─────────────────────────────┘
```

### 3. SIGNAL GENERATION

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Frecuencia: 1 por vela      │ Frecuencia: Múltiples       │
│ Determinismo: ✅ 100%       │ Determinismo: ❌ 0%         │
│ Reproducibilidad: ✅ 100%   │ Reproducibilidad: ❌ 0%     │
│ Duplicadas: ✅ No           │ Duplicadas: ❌ Sí (18+)     │
│ Timestamp: ✅ Únicos        │ Timestamp: ❌ Repetidos     │
│ Validación: ✅ Previa       │ Validación: ❌ Ninguna      │
└─────────────────────────────┴─────────────────────────────┘
```

### 4. RISK MANAGEMENT

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Capital base: $10,000       │ Capital base: $10,000       │
│ Actualización: ✅ Cada cycle│ Actualización: ❌ Una sola  │
│ Balance usado: ✅ Actual    │ Balance usado: ❌ Cacheado  │
│ Risk adaptativo: ✅ Sí      │ Risk adaptativo: ❌ No      │
│ Position sizing: ✅ Correcto│ Position sizing: ❌ Incómodo│
│ Ejemplo:                    │ Ejemplo:                    │
│ └─ Cycle 1: $10,000         │ └─ Cycle 1: $10,000 (OK)    │
│ └─ Cycle 2: $10,050 (upd)   │ └─ Cycle 2: Usa $10,000     │
│ └─ Risk calc: Correcto ✅   │ └─ Risk calc: Incorrecta ❌ │
└─────────────────────────────┴─────────────────────────────┘
```

### 5. EXECUTION

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Validation: ✅ Integral     │ Validation: ❌ Parcial      │
│ │ └─ SL/TP OK              │ │ └─ SL/TP not checked     │
│ │ └─ Position size OK      │ │ └─ Position size unknown │
│ │ └─ Capital OK            │ │ └─ Capital desync        │
│ Orden execution: ✅ Segura  │ Orden execution: ❌ Frágil  │
│ Pipeline: ✅ Conectado      │ Pipeline: ❌ Desconectado   │
│ │ └─ Risk mgmt → Exec      │ │ └─ Risk mgmt → Orch (OK) │
│ │ └─ Signal → Exec         │ │ └─ Orch → Exec (BREAK)   │
│ │ └─ Exec → Result         │ │ └─ Exec → MT5 (FAIL)     │
│ Comisiones: ✅ Aplicadas    │ Comisiones: ✅ Reales       │
│ Slippage: ✅ Simulado       │ Slippage: ✅ Real           │
└─────────────────────────────┴─────────────────────────────┘
```

### 6. ERROR HANDLING

```
┌─────────────────────────────┬─────────────────────────────┐
│      BACKTEST               │      LIVE MT5               │
├─────────────────────────────┼─────────────────────────────┤
│ Rechazos: ❌ Teóricos       │ Rechazos: ✅ Reales         │
│ Razón: Validación previa    │ Razón: Sin validación previa│
│ Recuperación: N/A           │ Recuperación: Manual        │
│ Logging: ✅ Integral        │ Logging: ❌ Parcial         │
│ Debugging: ✅ Fácil         │ Debugging: ❌ Difícil       │
│ Reproducibilidad: ✅ 100%   │ Reproducibilidad: ❌ 0%     │
└─────────────────────────────┴─────────────────────────────┘
```

---

## TIMELINE: DÓNDE OCURREN LAS FALLAS

### Backtest Timeline (Todo Correcto)

```
T=0:00   ┌─ Cargar datos históricos (CSV/SQLite)
         ├─ Validar: 1000+ barras, gaps OK
         └─ ✅ Datos listos

T=0:01   ┌─ Para cada barra (iterativo):
         ├─ 1. Calcular indicadores
         ├─ 2. Generar signal
         ├─ 3. Calcular position_size
         ├─ 4. Ejecutar trade (simulado)
         ├─ 5. Actualizar balance
         └─ ✅ Ciclo completado

T=1:00   ┌─ Backtest terminado
         ├─ Todas las señales ejecutadas
         ├─ Métricas calculadas
         └─ ✅ Resultados completos
```

### Live MT5 Timeline (3 Puntos de Falla)

```
T=0:00   ┌─ Conectar a MT5
         ├─ Obtener datos (últimas 100 barras)
         ├─ Caché: timestamp 12:45:00
         └─ ✅ Conexión OK

T=0:05   ┌─ Ciclo 1: get_live_data()
         ├─ Retorna caché (12:45:00)
         ├─ Estrategia genera SELL
         ├─ Risk mgmt: position_size = 0.001
         ├─ Orch envía: quantity=None ❌
         ├─ Exec recalcula: lot_size = 0.00 ❌
         ├─ MT5 rechaza ❌
         └─ ❌ FALLA #1

T=0:10   ┌─ Ciclo 2: get_live_data()
         ├─ Retorna caché MISMO (12:45:00) ❌
         ├─ Estrategia genera SELL DUPLICADA
         ├─ Risk mgmt: position_size = 0.001
         ├─ Orch envía: quantity=None ❌
         ├─ Exec recalcula: lot_size = 0.00 ❌
         ├─ MT5 rechaza ❌
         └─ ❌ FALLA #2 (DUPLICADA)

T=0:15   ┌─ Ciclo 3: get_live_data()
         ├─ Retorna caché MISMO (12:45:00) ❌
         ├─ ... (REPITE 18+ VECES)
         └─ ❌ FALLA #18+ (MULTIPLICADA)

T=2:00   ┌─ Sistema sigue en bucle
         ├─ 18+ señales duplicadas procesadas
         ├─ 18+ órdenes rechazadas
         ├─ 0 trades ejecutados
         └─ ❌ SISTEMA COMPLETAMENTE BLOQUEADO
```

---

## CONCLUSIÓN ARQUITECTÓNICA

```
┌─────────────────────────────────────────────────────────────┐
│         WHY BACKTEST WORKS AND LIVE MT5 DOESN'T             │
└─────────────────────────────────────────────────────────────┘

BACKTEST:
✅ Datos histór completos → Análisis correcto
✅ Indicadores normalizados → Thresholds aplican
✅ Ejecución sincrónica → Determinístico
✅ Risk management actualizado → Position sizing correcto
✅ Pipeline conectado → Señal + Size → Ejecución
✅ Validación integral → Sin errores sorpresa
═════════════════════════════════════════════════════════════
RESULTADO: ✅ 100% FUNCIONAL

LIVE MT5:
❌ Datos obsoletos (caché viejo)
❌ Indicadores sin normalizar (escala bruta)
❌ Ejecución asincrónica (no determinístico)
❌ Risk management desincronizado (balance viejo)
❌ Pipeline desconectado (position_size ignorado)
❌ Validación parcial (position_size → 0.00)
═════════════════════════════════════════════════════════════
RESULTADO: ❌ 0% FUNCIONAL (3 puntos de bloqueo)

THE FIX:
15 minutos para implementar 3 fixes críticos:
1. ceil() en lugar de round()        (5 min)
2. Pasar position_size a executor    (10 min)
3. Validar freshness de datos        (20 min)
═════════════════════════════════════════════════════════════
RESULTADO ESPERADO: ✅ 80% FUNCIONAL (suficiente para trading)
```

---

**Documento Generado**: Noviembre 3, 2025  
**Clasificación**: Análisis Técnico Comparativo  
**Siguiente Paso**: Implementar los 3 fixes críticos

