# 🧪 Guía de Tests - Bot Trader Copilot

## 📋 Descripción General

Esta carpeta contiene los tests esenciales para validar funcionalidad crítica del sistema de trading:
- **Backtesting**: Pruebas de estrategia con datos históricos
- **Conexión MT5**: Validación de conectividad y órdenes live
- **Equivalencia**: Verificación de que backtest y live trading usan el mismo pipeline de datos

## ✅ Tests Disponibles

### 1. **test_deriv_complete.py** - Live Trading MT5
**Propósito**: Prueba exhaustiva de conexión y operaciones live en MT5

**Funcionalidad**:
- ✅ Conexión a MetaTrader 5 (Deriv Demo)
- ✅ Descarga de datos de mercado
- ✅ Stream de ticks en tiempo real
- ✅ Apertura de órdenes BUY/SELL
- ✅ Modificación de SL/TP con validación de broker
- ✅ Trailing stops
- ✅ Cierre de posiciones
- ✅ Verificación de balance

**Ejecución**:
```bash
python descarga_datos/tests/test_deriv_complete.py
```

**Requisitos**:
- Configuración en `descarga_datos/.env` con credenciales MT5
- Conexión a internet
- Cuenta Deriv con modo demo habilitado

**Tiempo**: ~120 segundos

---

### 2. **verify_equivalence_simple.py** - Backtest vs Live
**Propósito**: Verificar que backtest y trading live usan el mismo pipeline de datos y procesamiento

**Validaciones**:
- ✅ Estructura de datos: CSV vs live coinciden
- ✅ Indicadores: Mismo cálculo en ambos modos
- ✅ Normalización: Escalado idéntico
- ✅ Signals: Generación coherente
- ✅ Flow: Pipeline completo validado

**Ejecución**:
```bash
python descarga_datos/tests/verify_equivalence_simple.py
```

**Requisitos**:
- Datos CSV disponibles en `descarga_datos/data/csv/`
- Base de datos SQLite en `descarga_datos/data/data.db`

**Tiempo**: ~30 segundos

**Output**:
- JSON report: `descarga_datos/data/backtests/equivalence_verification_simple.json`

---

### 3. **backtest_clean_combined.py** - Backtest de Estrategia
**Propósito**: Ejecutar backtest limpio de la estrategia UltraDetailedHeikinAshiML

**Funcionalidad**:
- ✅ Carga de datos históricos
- ✅ Ejecución de estrategia
- ✅ Cálculo de métricas (win rate, Sharpe, etc)
- ✅ Generación de resultados

**Ejecución**:
```bash
python descarga_datos/tests/backtest_clean_combined.py
```

**Requisitos**:
- Datos en `descarga_datos/data/csv/` o descargar automáticamente
- Modelo ML entrenado (si aplica)

**Tiempo**: ~60 segundos

**Output**:
- Dashboard: http://localhost:8519
- JSON results: `descarga_datos/data/dashboard_results/backtest_results.json`

---

### 4. **migrate_csv_to_sqlite.py** - Migración de Datos
**Propósito**: Migrar datos CSV históricos a base de datos SQLite

**Funcionalidad**:
- ✅ Lee archivos CSV de datos
- ✅ Valida integridad
- ✅ Inserta en SQLite
- ✅ Verifica integridad post-migración

**Ejecución**:
```bash
python descarga_datos/tests/migrate_csv_to_sqlite.py
```

**Requisitos**:
- Archivos CSV en `descarga_datos/data/csv/`

**Output**:
- Base de datos actualizada: `descarga_datos/data/data.db`

---

### 5. **check_data_paths_consolidated.py** - Validación de Estructura
**Propósito**: Verificar que la estructura de datos sea correcta y no haya duplicados

**Validaciones**:
- ✅ Carpeta única de datos en `descarga_datos/data/`
- ✅ Sin carpetas anidadas duplicadas
- ✅ Referencias de rutas correctas en código
- ✅ Integridad de datos
- ✅ Módulos importan correctamente

**Ejecución**:
```bash
python descarga_datos/tests/check_data_paths_consolidated.py
```

**Resultado**: Exit code 0 = ✅ válido

---

## 🚀 Ejecución de Tests

### Smoke Test (Rápido - 2 minutos)
```bash
# Verificar datos y estructura
python descarga_datos/tests/check_data_paths_consolidated.py

# Verificar equivalencia
python descarga_datos/tests/verify_equivalence_simple.py
```

### Full Test Suite (15 minutos)
```bash
# 1. Validar estructura
python descarga_datos/tests/check_data_paths_consolidated.py

# 2. Equivalencia
python descarga_datos/tests/verify_equivalence_simple.py

# 3. Backtest limpio
python descarga_datos/tests/backtest_clean_combined.py

# 4. Live trading (si tiene credenciales MT5)
python descarga_datos/tests/test_deriv_complete.py
```

### Validación de Datos
```bash
# Migrar CSV a SQLite si es necesario
python descarga_datos/tests/migrate_csv_to_sqlite.py

# Verificar integridad
python descarga_datos/tests/check_data_paths_consolidated.py
```

---

## 📊 Salidas Esperadas

### ✅ Exitoso
```
✅ VALIDACIÓN EXITOSA - Estructura de datos consolidada correctamente!
📋 Estructura verificada:
  ✅ Única carpeta de datos: descarga_datos/data/
  ✅ Sin carpetas duplicadas
  ✅ Referencias de rutas correctas en código
  ✅ Datos accesibles
  ✅ Módulos importan correctamente
```

### ✅ Backtest Exitoso
```
📊 BACKTEST RESULTS
├─ Total trades: 4,512
├─ Win rate: 78.5%
├─ P&L: $461,910.79
└─ Sharpe ratio: 2.45
```

### ✅ Live Trading Exitoso
```
🔌 MT5 CONNECTIVITY: ✅ Connected
📊 LIVE DATA STREAM: ✅ 20 ticks captured
💰 ORDER MANAGEMENT: ✅ BUY/SELL successful
⛔ SL/TP VALIDATION: ✅ Broker constraints met
📈 BALANCE: $9,999.93
```

---

## 🔍 Troubleshooting

### Error: "No module named 'utils'"
```bash
# Asegúrate de estar en el directorio correcto
cd C:\Users\javie\copilot\botcopilot-sar
python descarga_datos/tests/test_deriv_complete.py
```

### Error: "data.db not found"
```bash
# Migrar CSV a SQLite
python descarga_datos/tests/migrate_csv_to_sqlite.py
```

### Error: "MT5 connection failed"
```bash
# Verificar credenciales en descarga_datos/.env
# Verificar que MetaTrader 5 esté abierto
# Verificar que la cuenta sea válida
```

### Error: "CSV files not found"
```bash
# Los archivos deben estar en descarga_datos/data/csv/
# O se descargarán automáticamente al ejecutar backtest
```

---

## 📁 Archivos en Backup

Los siguientes tests fueron archivados como obsoletos o duplicados:
- Versiones antiguas de backtest (`backtest_live_data_v*.py`)
- Tests de brokers obsoletos (Binance, Bybit, Kraken)
- Debug y análisis scripts
- Versiones dryrun y experimentales

**Ubicación**: `descarga_datos/tests/BACKUP_OLD_TESTS_[timestamp]/`

Si necesitas recuperar un test antiguo, puedes encontrarlo allí.

---

## 📝 Convenciones

- **Nombres**: Descripción clara del propósito
- **Exit Code 0**: Exitoso
- **Exit Code 1**: Error (ver stdout/stderr)
- **Logs**: `descarga_datos/logs/`
- **Resultados**: `descarga_datos/data/`

---

## ✅ Verificación de Integridad

Para verificar que todo está funcionando correctamente:

```bash
# 1. Estructura
python descarga_datos/tests/check_data_paths_consolidated.py

# 2. Equivalencia
python descarga_datos/tests/verify_equivalence_simple.py

# 3. Integridad de datos
python descarga_datos/tests/migrate_csv_to_sqlite.py --validate

# 4. Test rápido si tienes MT5
# python descarga_datos/tests/test_deriv_complete.py
```

Si todos los tests pasan, el sistema está ✅ **LISTO PARA OPERACIÓN**.

---

**Última actualización**: 2 de noviembre de 2025  
**Status**: ✅ Estructura de tests optimizada
