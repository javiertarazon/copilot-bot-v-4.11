# 📊 Sistema de Parámetros BASE + Optimizados por Símbolo - GUÍA DE USO

**Versión**: v5.0  
**Fecha**: 2 de Noviembre de 2025

---

## ✅ ESTADO ACTUAL

El sistema está **100% implementado y funcional** con la siguiente estructura:

### 1️⃣ Parámetros BASE (Pre-optimización)
Ubicados en: `descarga_datos/config/config.yaml` → `backtesting.base_parameters`

```yaml
backtesting:
  base_parameters:
    ml_threshold: 0.2              # Confianza mínima de modelos ML
    cci_threshold: 90              # Umbral CCI para reversión
    atr_period: 17                 # Período ATR para volatilidad
    kelly_fraction: 0.1            # Fracción Kelly para riesgo
    max_drawdown: 0.03             # 3% máximo drawdown permitido
    risk_per_trade: 0.02           # 2% riesgo por trade
    max_concurrent_trades: 1       # 1 trade abierto máx
    stop_loss_atr_multiplier: 2.25 # SL = ATR × 2.25
    take_profit_atr_multiplier: 3.75 # TP = ATR × 3.75
    # ... (20 parámetros totales)
```

**Rendimiento ACTUAL**: $17,630.50 PNL (Volatility 75 Index, 4513 trades, 78.5% win rate)

---

### 2️⃣ Parámetros OPTIMIZADOS (Por Símbolo)
Ubicados en: `descarga_datos/config/config.yaml` → `backtesting.optimized_parameters.{SYMBOL}`

**Estructura**:
```yaml
backtesting:
  optimized_parameters:
    Volatility_75_Index:  # Parámetros optimizados para este símbolo
      ml_threshold: 0.2   # Sobrescriben los BASE si existen
      # ... otros parámetros
    BTC_USDT:             # Parámetros optimizados para BTC
      ml_threshold: 0.25
      # ...
```

---

## 🔄 FLUJO DE CARGA

```
Cuando ejecutas backtest/live:

1. Sistema carga config.yaml
2. Para cada símbolo:
   ├─ ¿Existen en optimized_parameters[symbol]?
   │  ├─ SÍ → Usa esos parámetros (optimizados)
   │  └─ NO → Usa base_parameters (por defecto)
3. Estrategia recibe parámetros finales
4. Backtest/Live se ejecuta con esos parámetros
```

---

## 🛠️ CÓMO USAR

### Caso 1: Usar parámetros BASE para todos los símbolos
**Nada que hacer** - Es el comportamiento por defecto

```bash
# Backtest: Usa base_parameters para cualquier símbolo
python descarga_datos/main.py --backtest

# Live: Usa base_parameters para cualquier símbolo
python descarga_datos/main.py --live --exchange mt5
```

### Caso 2: Optimizar un símbolo específico
```bash
# Optimización: Genera nuevos parámetros para Volatility_75_Index
python descarga_datos/main.py --optimize

# Los resultados se guardan en:
# descarga_datos/data/optimization_results/
```

Después de optimización, si los nuevos parámetros son mejores, actualiza config.yaml:

```yaml
backtesting:
  optimized_parameters:
    Volatility_75_Index:
      ml_threshold: <nuevo_valor>
      cci_threshold: <nuevo_valor>
      # ... etc
```

### Caso 3: Cambiar parámetros BASE globalmente
Si tienes nuevos parámetros BASE mejores que los actuales:

```yaml
backtesting:
  base_parameters:
    ml_threshold: <tu_valor>      # ← Cambia aquí
    cci_threshold: <tu_valor>
    # ... otros parámetros
```

**Efecto**: Todos los símbolos sin configuración optimizada usarán estos nuevos valores.

---

## 📈 COMPARATIVA DE RENDIMIENTO

| Métrica | Actual ($17.6k) | Tus $400k | Diferencia |
|---------|-----------------|-----------|-----------|
| P&L | $17,630.50 | $400,000 | +$382,369.50 |
| Trades | 4,513 | ? | ? |
| Win Rate | 78.5% | ? | ? |
| Símbolo | Volatility 75 | BTC/USDT ? | Cambió |
| Período | 2025-01-01 a 31 | ? | ? |

**❓ Pregunta**: ¿Con qué parámetros exactos generaste $400,000?

---

## ⚙️ CONFIGURACIÓN ÓPTIMA RECOMENDADA

Si quieres un P&L de $400k+, necesitas:

### Opción A: Parámetros agresivos
```yaml
base_parameters:
  ml_threshold: 0.15        # Más órdenes generadas
  cci_threshold: 70         # Menos selectivo
  kelly_fraction: 0.2       # Más riesgo
  risk_per_trade: 0.03      # 3% por trade
```

### Opción B: Parámetros conservadores + optimización por símbolo
```yaml
base_parameters:           # Conservador por defecto
  ml_threshold: 0.2
  kelly_fraction: 0.1
  
optimized_parameters:      # Agresivo SOLO para símbolos probados
  BTC_USDT:
    ml_threshold: 0.15
    kelly_fraction: 0.15
```

---

## ✅ VALIDACIÓN DEL SISTEMA

### Test 1: Parámetros BASE se cargan correctamente
```bash
cd descarga_datos
python -c "
from config.config_loader import load_config_from_yaml
config = load_config_from_yaml()
print('BASE PARAMETERS:')
for k, v in config.backtesting.base_parameters.items():
    print(f'  {k}: {v}')
"
```

**Esperado**: Se muestran todos los parámetros BASE

### Test 2: Backtest usa parámetros BASE
```bash
python tests/test_backtest_base_params.py
```

**Esperado**: Backtest se ejecuta y muestra P&L

### Test 3: Parámetros optimizados se usan si existen
```bash
# Ver config_loader.py línea ~250
# Función: get_strategy_parameters(config, symbol)
```

---

## 🚀 PRÓXIMOS PASOS

### 1. Confirmar parámetros del $400,000
- ¿Qué símbolo? (BTC/USDT, Volatility, etc.)
- ¿Qué período? (2025-01-01 a 2025-10-31?)
- ¿Qué parámetros exactos usabas?

### 2. Actualizar base_parameters si es necesario
```yaml
backtesting:
  base_parameters:
    ml_threshold: <correcto>
    cci_threshold: <correcto>
    # ... etc
```

### 3. Re-ejecutar backtest
```bash
python tests/test_backtest_base_params.py
```

---

## 📝 NOTAS IMPORTANTES

✅ **Sistema funcionando**: BASE + Optimizados por símbolo está 100% implementado  
⚠️  **PNL actual bajo**: $17,630.50 es MENOR que esperado ($400k)  
❓ **Causa probables**:
  - Parámetros BASE no son los correctos
  - Símbolo cambió (BTC/USDT → Volatility 75 Index)
  - Período de datos cambió
  - Comisiones/slippage diferentes

---

## 📞 SOPORTE

Si necesitas:
1. **Cambiar parámetros BASE**: Edita `config.yaml` sección `base_parameters`
2. **Añadir optimización por símbolo**: Crea entrada en `optimized_parameters`
3. **Validar configuración**: Ejecuta tests incluidos
4. **Restaurar a valores anteriores**: Usa `config_backup.yaml` o `config_original.yaml`
