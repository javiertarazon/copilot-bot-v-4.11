# 📦 GUÍA DE DEPLOYMENT: Sistema Live MT5 FASE 3

**Versión**: 1.0  
**Fecha**: 3 de noviembre de 2025  
**Status**: ✅ LISTO PARA PRODUCCIÓN

---

## 🎯 Pre-Deployment Checklist

### Validaciones Completadas ✅

- [x] MT5 Connection Test - PASSED
- [x] Position Size Pipeline - PASSED  
- [x] Data Staleness Validation - PASSED
- [x] Capital Synchronization - PASSED
- [x] SL/TP Validation - PASSED
- [x] Indicator Consistency - PASSED
- [x] Pipeline Logging - PASSED
- [x] 30-sec Integration Test - PASSED
- [x] 60-sec Integration Test - PASSED
- [x] 10-sec Real Execution - PASSED

### Requisitos de Sistema ✅

```
✅ Python 3.13.7
✅ Virtual Environment: .venv/
✅ MT5 Account: Deriv-Demo (5899273)
✅ Balance: 9997.05 USD
✅ CCXT: Disponible
✅ TALIB: Wrapper disponible
✅ Todas las dependencias instaladas
```

---

## 🚀 Deployment Steps

### Paso 1: Verificación Final de Código

```bash
# Navegar al directorio
cd c:\Users\javie\copilot\botcopilot-sar

# Verificar que todos los archivos modificados están en su lugar
dir descarga_datos\core\live_trading_orchestrator.py
dir descarga_datos\core\mt5_live_data.py
dir descarga_datos\core\mt5_order_executor.py
dir descarga_datos\utils\pipeline_logger.py

# Verificar tests
dir descarga_datos\tests\test_phase*.py
dir descarga_datos\tests\test_indicator_consistency.py
dir descarga_datos\tests\test_pipeline_logging.py
```

### Paso 2: Ejecutar Test Final Pre-Deployment

```bash
# Cambiar a directorio del proyecto
cd c:\Users\javie\copilot\botcopilot-sar

# Ejecutar quick backtest smoke test
python -m pytest descarga_datos/tests/test_quick_backtest.py -v

# Resultado esperado:
# ✅ test_quick_backtest.py::test_quick_backtest PASSED
```

### Paso 3: Iniciar Sistema en Modo Verificación

```bash
# Modo 1: Ejecutar orquestador por 5 minutos en background
python descarga_datos/main.py --live --duration 5

# Esperado:
# ✅ MT5 conectado
# ✅ Estrategia cargada
# ✅ Ciclos ejecutándose
# ✅ Logging visible en tiempo real
```

### Paso 4: Monitoreo de Logs

```bash
# En otra terminal, monitorear logs en tiempo real
Get-Content -Path "descarga_datos/logs/*.log" -Wait | Select-String "PIPELINE|ERROR|CRITICAL"

# Esperado:
# [PIPELINE 1/5 DATA] ...
# [PIPELINE 2/5 INDICATORS] ...
# [PIPELINE 3/5 SIGNAL] ...
# [PIPELINE 4/5 RISK] ...
# [PIPELINE 5/5 EXECUTE] ...
```

### Paso 5: Iniciar Sistema en Producción

```bash
# Opción A: Ejecución directa (foreground)
python descarga_datos/main.py --live

# Opción B: En background (usando start_live_ccxt.bat)
.\start_live_ccxt.bat

# Sistema se ejecutará indefinidamente hasta que se presione Ctrl+C
```

---

## 🔍 Validación Post-Deployment

### Verificación de Conectividad

```bash
# 1. Verificar que MT5 está conectado
# Buscar en logs: "MT5 conectado: javier tarazon @ Deriv-Demo"

# 2. Verificar balance
# Buscar en logs: "Balance: 9997.05, Equity: 9997.05"

# 3. Verificar que estrategia está cargada
# Buscar en logs: "UltraDetailedHeikinAshiML cargada"
```

### Verificación de Operación

```bash
# En logs, verificar presencia de:

# 1. Data Pipeline
[PIPELINE 1/5 DATA] Volatility 75 Index 15m: 200 barras

# 2. Indicators Pipeline
[PIPELINE 2/5 INDICATORS] 25 indicadores calculados

# 3. Signal Pipeline
[PIPELINE 3/5 SIGNAL] UltraDetailedHeikinAshiML

# 4. Risk Pipeline
[PIPELINE 4/5 RISK] APPROVED | PosSize: X.XXXX

# 5. Execute Pipeline
[PIPELINE 5/5 EXECUTE] BUY/SELL X.XXXX
```

### Verificación de Ciclos

```bash
# Cada 5 segundos debe aparecer en logs:
[CYCLE #N] Procesadas: 1 | Señales: 0 | Órdenes: 0 | Activas: 0 | Duration: XXXms

# Si falta por más de 10 segundos → ERROR
```

---

## ⚠️ Troubleshooting

### Problema: MT5 no conecta

```
Error: "No se pudo establecer conexión con MetaTrader 5"

Soluciones:
1. Verificar que MT5 está abierto y la cuenta está conectada
2. Verificar que sandbox=true en config.yaml
3. Revisar credenciales de usuario
4. Intentar reconectar manualmente en MT5
```

### Problema: Position Size = 0

```
Error: "Position size cálculado es 0"

Soluciones:
1. Verificar que equity > 0
2. Verificar que risk_per_trade está configurado (default 2%)
3. Revisar cálculos de ATR (debe ser > 0)
4. Aumentar account balance si es muy bajo
```

### Problema: Señales duplicadas

```
Error: "Mismas señales múltiples veces"

Soluciones:
1. Verificar que cache staleness validation está activa
2. Revisar logs: debe aparecer "Cache invalidated after X seconds"
3. Si no aparece → cache no se invalida, aumentar debug logging
```

### Problema: Órdenes rechazadas por MT5

```
Error: "MT5 rechazó la orden: error code -X"

Soluciones:
1. Verificar logs de SL/TP validation
2. Confirmar que SL < Price < TP para BUY
3. Confirmar que SL > Price > TP para SELL
4. Verificar que hay suficiente balance
5. Revisar que symbol existe en MT5
```

### Problema: Sistema se congela

```
Error: "Sistema no responde"

Soluciones:
1. Verificar logs para ver dónde se detiene
2. Aumentar timeout de MT5 connection
3. Revisar que no hay loops infinitos en indicadores
4. Monitorear uso de memoria (memoria insuficiente)
5. Revisar conexión a internet
```

---

## 📊 Monitoreo en Vivo

### Métricas a Verificar

1. **Connectivity**
   ```
   ✅ MT5 conectado
   ✅ Balance sincronizado
   ✅ Equity actualizado
   ```

2. **Data Quality**
   ```
   ✅ 200 barras obtenidas
   ✅ Cache TTL < 5 seg
   ✅ NaN < 5% (normal)
   ```

3. **Signals**
   ```
   ✅ Indicadores calculados
   ✅ ML confidence entre 0-1
   ✅ Entry price válido
   ```

4. **Risk Management**
   ```
   ✅ Position size > 0
   ✅ Risk < max_drawdown
   ✅ SL/TP validado
   ```

5. **Execution**
   ```
   ✅ Órdenes enviadas a MT5
   ✅ Posiciones abiertas rastreadas
   ✅ Stops activos
   ```

6. **Performance**
   ```
   ✅ Cycle duration < 5 sec
   ✅ No errores en logs
   ✅ Memory stable
   ```

### Logs Críticos a Monitorear

```bash
# Buscar ERRORS
Get-Content descarga_datos/logs/*.log | Select-String "ERROR|CRITICAL|FAILED"

# Buscar WARNINGS
Get-Content descarga_datos/logs/*.log | Select-String "WARNING"

# Contar ciclos completados
Get-Content descarga_datos/logs/*.log | Select-String "CYCLE #" | Measure-Object
```

---

## 🔄 Escalabilidad y Mantenimiento

### Agregar Nuevos Símbolos

1. Editar `config/config.yaml`
2. Agregar símbolo a `live.symbols`
3. Agregar timeframe a `live.timeframes`
4. Reiniciar sistema

### Cambiar Parámetros de Estrategia

1. Editar configuración en `config/config.yaml`
2. Cambiar valores de `stop_loss_atr_multiplier`, `take_profit_atr_multiplier`
3. Cambiar `atr_period` si es necesario
4. Reiniciar sistema

### Ajustar Límites de Riesgo

1. Cambiar `risk_per_trade` (%)
2. Cambiar `max_drawdown_limit` (%)
3. Cambiar `max_consecutive_losses`
4. Reiniciar sistema

---

## 📞 Soporte

### En Caso de Problemas

1. Revisar logs en `descarga_datos/logs/`
2. Ejecutar test correspondiente (FASE 1, 2, o 3)
3. Documentar error con logs completos
4. Reiniciar sistema

### Archivos Importantes

```
Configuration: descarga_datos/config/config.yaml
Logs: descarga_datos/logs/trading.log
Tests: descarga_datos/tests/test_*.py
Utilities: descarga_datos/utils/pipeline_logger.py
```

---

## ✅ Deployment Completado

Sistema está listo para:
- ✅ Operación en tiempo real
- ✅ Monitoreo 24/7
- ✅ Escalado a múltiples símbolos
- ✅ Optimización continua

**Estado**: PRODUCTION READY 🚀

---

*Documento actualizado: 3 de noviembre de 2025*
