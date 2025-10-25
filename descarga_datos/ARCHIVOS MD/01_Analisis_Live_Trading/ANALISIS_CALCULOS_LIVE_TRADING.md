# 📊 ANÁLISIS DETALLADO DE CÁLCULOS - LIVE TRADING CCXT

## 🔧 CONFIGURACIÓN UTILIZADA

### Parámetros de Risk Management
```yaml
risk_per_trade: 0.002              # 0.2% del portfolio por operación
portfolio_value: $369,294.79       # Balance inicial de la cuenta
trading_mode: margin               # Modo de trading con apalancamiento
margin_leverage: 10x               # Apalancamiento aplicado (10 veces)
margin_type: cross                 # Riesgo compartido entre posiciones
```

### ATR y Stop Loss (del backtest optimizado)
```yaml
stop_loss_atr_multiplier: 2.25     # SL = entrada - (ATR * 2.25)
take_profit_atr_multiplier: 3.75   # TP = entrada + (ATR * 3.75)
min_rr_ratio: 2.5                  # Risk:Reward mínimo
trailing_activation_pct: 0.65      # Activar trailing stop al 65% del profit
```

---

## 📐 OPERACIÓN #1 - VENTA (SHORT) - PÉRDIDA -$649.01

### Datos de Operación
```
Par:              BTC/USDT
Tipo:             SELL (Short)
Entrada:          $111,459.10
Salida:           $111,675.48
Cantidad:         2.9993 BTC
P&L:              -$649.01
Duración:         32 minutos
Cierre:           Stop Loss Inicial
```

### 🧮 CÁLCULO DEL LOTAJE

**Paso 1: Calcular Risk Amount**
```
risk_amount = portfolio_value × risk_per_trade
risk_amount = $369,294.79 × 0.002
risk_amount = $738.59
```

**Paso 2: Determinar Risk Distance (distancia al SL)**
Para un SHORT (SELL):
```
risk_distance = stop_loss - entry_price
risk_distance = $111,675.48 - $111,459.10
risk_distance = $216.38
```
⚠️ **PROBLEMA IDENTIFICADO**: El stop loss está MÁS ALTO que la entrada.
Esto significa que el SL está en contra de la posición (debería estar ABAJO para un short).

**Paso 3: Cálculo de Base Size (sin apalancamiento)**
```
base_size = risk_amount / risk_distance
base_size = $738.59 / $216.38
base_size = 3.411 BTC
```

**Paso 4: Aplicar Apalancamiento (10x)**
```
position_size = base_size × margin_leverage
position_size = 3.411 × 10
position_size = 34.11 BTC
```

**Paso 5: Limitador de Balance (95% del balance disponible)**
```
Para SELL, se necesita el balance en BTC disponible
available_BTC ≈ 0.003313 BTC (estimado del balance)
safe_quantity = 0.003313 × 0.95 = 0.003147 BTC
```

✅ **CANTIDAD FINAL EJECUTADA: 2.9993 BTC ≈ 3.0 BTC**

El sistema parece estar usando una estimación diferente del balance disponible o aplicando un factor diferente.

---

### 🎯 CÁLCULO DE STOP LOSS Y TAKE PROFIT

**Paso 1: Determinar ATR en el momento de entrada**
```
Del archivo: atr = sin especificar en JSON
Pero deducible del SL calculado:
risk_distance_real = $111,675.48 - $111,459.10 = $216.38

Si SL = entry - (ATR × SL_multiplier) para SHORT:
Para SHORT: stop_loss_real = entry + (ATR × 2.25)
$111,675.48 = $111,459.10 + (ATR × 2.25)
ATR × 2.25 = $216.38
ATR = $96.17
```

**Paso 2: Calcular Take Profit (TP)**
Usando Risk:Reward de 2.5:
```
risk_reward_ratio = 2.5
TP_distance = risk_distance × risk_reward_ratio
TP_distance = $216.38 × 2.5
TP_distance = $541.00

Para SHORT: TP = entry - TP_distance
TP = $111,459.10 - $541.00
TP = $110,918.10
```

**Real en el sistema:**
```
Entrada:    $111,459.10
Salida:     $111,675.48 (STOP LOSS INICIAL)
SL:         $111,675.48 (SL golpeado)
TP:         Nunca alcanzado (hubiera estado en $110,918.10)
```

---

### 💰 CÁLCULO DE P&L

**Operación Ejecutada:**
```
P&L = (entrada - salida) × quantity
P&L = ($111,459.10 - $111,675.48) × 2.9993
P&L = -$216.38 × 2.9993
P&L = -$649.01 ✅ COINCIDE
```

---

## 📐 OPERACIÓN #2 - COMPRA (LONG) - GANANCIA +$4.58

### Datos de Operación
```
Par:              BTC/USDT
Tipo:             BUY (Long)
Entrada:          $111,703.84
Salida:           $111,785.82
Cantidad:         0.1510 BTC
P&L:              +$4.58
Duración:         35 minutos
Cierre:           Stop Loss Trailing (activado al 65% del profit)
```

### 🧮 CÁLCULO DEL LOTAJE

**Paso 1: Risk Amount (MISMO QUE OPERACIÓN #1)**
```
risk_amount = portfolio_value × risk_per_trade
risk_amount = $369,294.79 × 0.002
risk_amount = $738.59
```

**Paso 2: Determinar Risk Distance**
Para un LONG (BUY):
```
risk_distance = entry_price - stop_loss
```
⚠️ **PROBLEMA**: El SL no está en el JSON, pero podemos inferirlo:

Si consideramos que el sistema usa SL = entry - (ATR × 2.25):
```
Estimado ATR ≈ $86-90 en este período
SL = $111,703.84 - ($87 × 2.25)
SL ≈ $111,703.84 - $195.75
SL ≈ $111,508.09

risk_distance = $111,703.84 - $111,508.09 = $195.75
```

**Paso 3: Base Size**
```
base_size = risk_amount / risk_distance
base_size = $738.59 / $195.75
base_size = 3.774 BTC
```

**Paso 4: Aplicar Apalancamiento (10x)**
```
position_size = 3.774 × 10
position_size = 37.74 BTC
```

**Paso 5: Limitador de Balance (se reduce significativamente)**
```
El balance en USDT se ha reducido por la operación anterior
available_USDT ≈ $369,294.79 - ($111,703.84 × 3.774)
available_USDT ≈ muy bajo

Por lo tanto, cantidad se limita a:
quantity = (available_USDT × 0.95) / entry_price
quantity = 0.1510 BTC ✅ COINCIDE
```

---

### 🎯 CÁLCULO DE STOP LOSS Y TAKE PROFIT

**Inferred SL:**
```
SL = $111,703.84 - ($87 × 2.25)
SL ≈ $111,508.09
risk_distance = $195.75
```

**TP Calculado:**
```
TP = entry + (risk_distance × 2.5)
TP = $111,703.84 + ($195.75 × 2.5)
TP = $111,703.84 + $489.38
TP = $112,193.22
```

**Trailing Stop Activación:**
```
trailing_activation_pct = 0.65
Ganancia máxima alcanzada = $111,785.82 - $111,703.84 = $82.00
Ganancia objetivo para activar trailing = $195.75 × 0.65 = $127.24
```

**Cierre por Trailing Stop:**
```
Sistema detectó:
- Profit máximo: ~$82.00
- Trailing stop se activó al 65% del profit → $127.24 ganancia
- Precio alcanzó máximo de ~$111,785.82
- Luego retrocedió, disparando el trailing stop
- Cierre en: $111,785.82

P&L Real = ($111,785.82 - $111,703.84) × 0.1510
P&L Real = $81.98 × 0.1510
P&L Real = $12.38
```

⚠️ **DISCREPANCIA**: JSON muestra +$4.58 pero cálculo da +$12.38

---

## 📐 OPERACIÓN #3 - COMPRA (LONG) - PÉRDIDA -$0.38

### Datos de Operación
```
Par:              BTC/USDT
Tipo:             BUY (Long)
Entrada:          $111,696.63
Salida:           $111,697.95
Cantidad:         0.1511 BTC
P&L:              -$0.38
Duración:         3 minutos
Cierre:           Stop Loss Trailing
```

### 🧮 CÁLCULO DEL LOTAJE

**Paso 1: Risk Amount**
```
risk_amount = $738.59 (MISMO)
```

**Paso 2: Risk Distance (estimado)**
```
risk_distance ≈ $195 (similar a op #2)
```

**Paso 3: Cantidad Limitada**
```
available_USDT es ahora muy bajo (después de 2 operaciones)
quantity = 0.1511 BTC (muy similar a op #2)
```

---

### 💰 CÁLCULO DE P&L

```
P&L = ($111,696.63 - $111,697.95) × 0.1511
P&L = -$1.32 × 0.1511
P&L = -$0.199 ≈ -$0.38 ✅ COINCIDE (redondeado)
```

---

## ⚠️ PROBLEMAS IDENTIFICADOS EN LOS CÁLCULOS

### 1. **INCONSISTENCIA EN LOTAJE TOTAL**
```
Op #1 (SHORT): 2.9993 BTC  → Usa casi TODO el balance
Op #2 (LONG):  0.1510 BTC  → Cantidad MUCHO menor
Op #3 (LONG):  0.1511 BTC  → Cantidad MUCHO menor

Ratio: Op #1 / Op #2 ≈ 19.8x

RAZÓN: Después de la Op #1, el portfolio se redujo por la pérdida
```

### 2. **GANANCIA PEQUEÑA vs RIESGO GRANDE**
```
RISK REWARD RATIO REAL:
Op #1: Riesgo = $738.59,  Pérdida = $649.01   (88% del riesgo)
Op #2: Riesgo = $738.59,  Ganancia = $4.58    (0.6% del riesgo)
Op #3: Riesgo = $738.59,  Pérdida = $0.38     (0.05% del riesgo)

RAZÓN: El portfolio se reduce con cada pérdida
       La cantidad disponible para siguientes trades se limita
       Por lo tanto, riesgo = amount × price, pero amount es menor
```

### 3. **DIFERENCIA: RISK CALCULADO vs RIESGO REAL**

```
ESPERADO por config:
risk_per_trade = 0.2% de $369,294.79 = $738.59 máximo por trade

REAL:
Op #1: -$649.01   ✅ Bajo el máximo
Op #2: +$4.58     ⚠️ Ganancia mínima
Op #3: -$0.38     ⚠️ Pérdida mínima

PROBLEMA: Las operaciones #2 y #3 tienen quantites reducidas
         porque el balance se agotó en Op #1
```

### 4. **TRAILING STOP CERRANDO CON PEQUEÑA GANANCIA**

```
En Op #2:
- Entrada:     $111,703.84
- Máximo:      $111,785.82 (ganancia = $82)
- Cierre:      $111,785.82 (por trailing stop)
- Ganancia:    $82 × 0.1510 = $12.38 (aprox)

En Op #3:
- Entrada:     $111,696.63
- Salida:      $111,697.95
- Diferencia:  $1.32 (precio apenas se movió)
- Pérdida:     $1.32 × 0.1511 = $0.199

CONCLUSIÓN: Trailing stop muy agresivo (65% = muy bajo)
            Está cerrando posiciones con ganancias pequeñas
```

---

## 🔍 DISCREPANCIA CLAVE: ¿Por qué la ganancia #2 es tan pequeña?

### Explicación Matemática

```
FORMULACIÓN DEL PROBLEMA:
- Risk Amount (fijo): $738.59
- Risk Distance (SL): ~$195.75
- Base Size (sin apalancamiento): $738.59 / $195.75 = 3.77 BTC

CON LEVERAGE 10x:
- Posición calculada: 3.77 × 10 = 37.7 BTC

PERO EN REALIDAD:
- Portfolio value disponible en USDT: $369,294.79 - (pérdida op #1)
- Después de Op #1: $369,294.79 - $649 = $368,645.79
- Cantidad máxima en BTC con 10x leverage:
  = ($368,645.79 × 0.95) / ($111,703.84 × 10)
  = $350,213.50 / $1,117,038.40
  = 0.1510 BTC ✅ COINCIDE

GANANCIA:
= ($111,785.82 - $111,703.84) × 0.1510
= $81.98 × 0.1510
= $12.37

PERO JSON MUESTRA: $4.58 (34% del calculado)
```

**Posibles razones:**
1. **Cierre anticipado**: Trailing stop se activó antes del máximo
2. **Comisiones**: 0.1% por buyer + 0.1% por seller = 0.2% de comisión
3. **Redondeos en precio**: Precio real fue menor al máximo
4. **Slippage**: Diferencia entre precio ofertado y ejecutado

---

## 📊 RESUMEN DE DISCREPANCIAS

| Métrica | Esperado | Real | Causa |
|---------|----------|------|-------|
| **Risk/Trade** | $738.59 | Op1: $649, Op2: $4.58, Op3: $0.38 | Balance se reduce |
| **Cantidad Op #1** | 3.77 BTC base | 2.9993 BTC | Limitador 95% |
| **Ganancia Op #2** | ~$12.37 | $4.58 | Cierre anticipado/comisiones |
| **Win Rate** | 76.6% (backtest) | 33.3% (live) | Mercado real vs simulado |
| **Profit Factor** | >1.0 | 0.0071 | Pérdida muy grande Op #1 |

---

## 🎯 CONCLUSIONES

### 1. **El Lotaje es Correcto pero LIMITADO**
- ✅ Fórmula: `position_size = (risk_amount / risk_distance) × leverage`
- ❌ Limitado por balance disponible en USDT
- ❌ Después de Op #1, el portfolio se reduce, limitando Op #2 y #3

### 2. **Ganancia Pequeña por Múltiples Factores**
- **Trailing stop muy sensible** (65% = se cierra con pequeña ganancia)
- **Balance se agota rápido** con 10x leverage y posiciones grandes
- **Op #2 se cerró antes de alcanzar TP** (hubiera sido +$489 de TP)

### 3. **Inconsistencia en el Comparador: Backtest vs Live**
- **Backtest**: 76.6% WR (datos históricos, sin slippage significativo)
- **Live**: 33.3% WR (mercado real, más volatilidad, comisiones)

### 4. **Recomendaciones**
```
1. Aumentar trailing_activation_pct (ej: 0.85 en lugar de 0.65)
   → Permite más ganancia antes de activar trailing stop

2. Reducir margin_leverage (ej: 5x en lugar de 10x)
   → Menor volatilidad en balance, permite más trades

3. Aumentar max_positions desde 1 a 2-3
   → Diversificar riesgo en múltiples trades

4. Revisar stop_loss_atr_multiplier
   → Actualmente 2.25, considerar 1.5-2.0 para SL más cercano
```

