# 🧪 CONFIGURACIÓN DE PRUEBAS - LIVE TRADING TEST

## 📋 RESUMEN

Configuración **RELAJADA** para ejecutar más operaciones y validar que los cálculos se ejecutan correctamente.

- **Archivo**: `descarga_datos/config/config_pruebas_operaciones.yaml`
- **Script**: `descarga_datos/scripts/live_trading_test.py`
- **Modo**: SANDBOX (sin dinero real)
- **Objetivo**: Validar cálculos y ejecución de trades

---

## 🔧 CAMBIOS PRINCIPALES

### 1️⃣ Capital Reducido

```yaml
initial_capital: 100 USDT  # vs 800 USDT productivo
```

**Razón**: Usar menos dinero en pruebas

---

### 2️⃣ Más Operaciones Concurrentes

```yaml
max_concurrent_trades: 2  # ↑ De 1 a 2
```

**Razón**: Permite ejecutar múltiples trades simultáneamente para validar sincronización

---

### 3️⃣ Parámetros Menos Restrictivos

| Parámetro | Productivo | Pruebas | Cambio |
|-----------|-----------|---------|--------|
| `cci_threshold` | 90 | 85 | ↓ -5 (menos restrictivo) |
| `ml_threshold` | 0.2 | 0.15 | ↓ -0.05 (más sensible) |
| `liquidity_score_min` | 5 | 3 | ↓ -2 (menos restrictivo) |
| `stoch_oversold` | 35 | 30 | ↓ -5 (más oportunidades) |
| `volume_ratio_min` | 0.3 | 0.2 | ↓ -0.1 (menos restrictivo) |
| `ema_trend_period` | 50 | 30 | ↓ -20 (más sensible) |

**Razón**: Generar más signals para validar cálculos

---

### 4️⃣ Mayor Riesgo Permitido

| Parámetro | Productivo | Pruebas | Cambio |
|-----------|-----------|---------|--------|
| `risk_per_trade` | 0.02 (2%) | 0.03 (3%) | ↑ +1% |
| `max_portfolio_heat` | 0.05 (5%) | 0.08 (8%) | ↑ +3% |
| `max_drawdown` | 0.03 (3%) | 0.05 (5%) | ↑ +2% |

**Razón**: Permitir pruebas más agresivas sin afectar límites de seguridad

---

### 5️⃣ Stops y Targets Más Cercanos

| Parámetro | Productivo | Pruebas | Cambio |
|-----------|-----------|---------|--------|
| `stop_loss_atr_multiplier` | 2.25 | 2.0 | ↓ -0.25 |
| `take_profit_atr_multiplier` | 3.75 | 3.0 | ↓ -0.75 |

**Razón**: Activaciones más rápidas para validar cálculos

---

## 🚀 CÓMO USAR

### Opción 1: Ejecutar Script de Pruebas

```bash
# Desde la raíz del repositorio
python descarga_datos/scripts/live_trading_test.py
```

**Salida esperada**:
```
================================================================================
🧪 LIVE TRADING TEST - Modo Pruebas
================================================================================
Usando configuración: config_pruebas_operaciones.yaml
Parámetros: RELAJADOS para más operaciones
Modo: SANDBOX (sin dinero real)
================================================================================

[INFO] 🧪 INICIO DE PRUEBAS DE LIVE TRADING
[INFO] ⏰ Timestamp: 2025-10-25T11:30:00
[INFO] 📊 Capital inicial: 100 USDT
[INFO] 🎯 Max concurrent trades: 2 (vs 1 productivo)
[INFO] 📈 Risk per trade: 0.03 (vs 0.02 productivo)
[INFO] 🌍 Exchange: binance - SANDBOX MODE

[INFO] ✅ TRADE EJECUTADO
[INFO] ⏰ Timestamp: 2025-10-25T11:30:05
[INFO] 📊 Símbolo: BTC/USDT
[INFO] 💹 Lado: BUY
[INFO] 📍 Entry Price: 43000.00
[INFO] 💰 Cantidad: 0.001
[INFO] 🎯 SL: 42500.00
[INFO] 📈 TP: 44000.00
[INFO] 📐 Risk/Reward: 2.0
[INFO] 🤖 ML Signal: 0.75
```

### Opción 2: Usar Configuración Directamente

```bash
# Con main.py
python descarga_datos/main.py --live-ccxt --config config_pruebas_operaciones.yaml
```

---

## 📊 QUÉ VALIDAR

### 1. Cálculos de Entry

Verifica que:
- Entry Price sea el precio actual del mercado
- Cantidad se calcule correctamente: `position_size = capital * risk_per_trade / (entry - stop_loss)`

### 2. Cálculos de Stop Loss

Verifica que:
- SL = Entry - (ATR * stop_loss_atr_multiplier)
- SL < Entry (para BUY)
- SL > Entry (para SELL)

### 3. Cálculos de Take Profit

Verifica que:
- TP = Entry + (ATR * take_profit_atr_multiplier)
- TP > Entry (para BUY)
- TP < Entry (para SELL)

### 4. Risk/Reward Ratio

Verifica que:
- RR = TP_Distance / SL_Distance
- RR >= min_rr_ratio (2.0 en pruebas)

### 5. ML Signals

Verifica que:
- ML Signal está entre ml_threshold_min y ml_threshold_max
- Signal válido dispara entry solo si cumple threshold

### 6. Concurrencia

Verifica que:
- Se ejecutan máximo 2 trades simultáneamente (max_concurrent_trades)
- No se excede max_portfolio_heat

---

## 🔒 SEGURIDAD

✅ **SANDBOX MODE SIEMPRE ACTIVADO**
```yaml
exchanges:
  binance:
    sandbox: true  # CRÍTICO
  bybit:
    sandbox: true  # CRÍTICO
```

⚠️ **Capital bajo**
- Productivo: 800 USDT
- Pruebas: 100 USDT

🚨 **Validaciones automáticas**
- Verifica cálculos en cada trade
- Logs detallados de cada operación
- Alertas de anomalías

---

## 📝 LOGS

Los logs se guardan en: `descarga_datos/logs/live_trading_test.log`

Ejemplo de log:
```
2025-10-25 11:30:00,000 [INFO] 🧪 INICIO DE PRUEBAS DE LIVE TRADING
2025-10-25 11:30:00,005 [INFO] 📡 Inicializando componentes...
2025-10-25 11:30:00,050 [INFO] ✅ Componentes inicializados
2025-10-25 11:30:00,100 [INFO] 🔄 Iteración 1/10
2025-10-25 11:30:00,150 [INFO] 📊 Obteniendo datos de mercado...
2025-10-25 11:30:00,200 [INFO] 🤖 Analizando con ML...
2025-10-25 11:30:00,250 [INFO] ✅ TRADE EJECUTADO
2025-10-25 11:30:00,300 [INFO] ✅ Cálculos validados correctamente
```

---

## ⚡ DIFERENCIAS RESPECTO A PRODUCTIVO

### Productivo (config.yaml)
```yaml
initial_capital: 800
max_concurrent_trades: 1
cci_threshold: 90
ml_threshold: 0.2
risk_per_trade: 0.02
```

### Pruebas (config_pruebas_operaciones.yaml)
```yaml
initial_capital: 100
max_concurrent_trades: 2
cci_threshold: 85
ml_threshold: 0.15
risk_per_trade: 0.03
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Ejecutar pruebas con config relajada
2. ✅ Validar que se ejecutan trades correctamente
3. ✅ Verificar cálculos en logs
4. ✅ Confirmar que signals son correctos
5. ✅ Revisar sincronización con múltiples trades
6. ✅ Si todo OK → Usar config.yaml productivo

---

## ❓ TROUBLESHOOTING

### "No trades ejecutados"
- Revisar logs en `descarga_datos/logs/live_trading_test.log`
- Verificar que SANDBOX mode esté activo
- Aumentar `cci_threshold` y `ml_threshold` en config_pruebas

### "Cálculos incorrectos"
- Verificar Entry Price vs Market Price
- Revisar ATR values
- Validar SL < Entry < TP (para BUY)

### "Error en conexión CCXT"
- Verificar credenciales en config
- Asegurar internet activo
- Reintentar con `max_retries: 3`

---

## 📞 SOPORTE

Para más información sobre parámetros específicos, revisa:
- `descarga_datos/config/config.yaml` - Config productivo
- `descarga_datos/strategies/ultra_detailed_heikin_ashi_ml_strategy.py` - Lógica de estrategia
- `descarga_datos/ARCHIVOS MD/GUIA_DRAWDOWN_v4.7.md` - Documentación general

---

**Última actualización**: 25 de Octubre de 2025
**Estado**: ✅ LISTO PARA USAR
