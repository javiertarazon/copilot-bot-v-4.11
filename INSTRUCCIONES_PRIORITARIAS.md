# 🚨 INSTRUCCIONES PRIORITARIAS - BOT TRADER COPILOT v4.11

## 📋 REGLAS FUNDAMENTALES DE OPERACIÓN

### 🔴 REGLA #1: IDIOMA ESPAÑOL OBLIGATORIO
- **TODAS las respuestas, pensamientos y comunicaciones DEBEN ser en ESPAÑOL**
- **TODOS los comentarios de código DEBEN ser en ESPAÑOL**
- **TODA la documentación nueva DEBE ser en ESPAÑOL**
- **EXCEPCIÓN**: Solo nombres de variables, funciones y clases en inglés (estándar de programación)

### 🔴 REGLA #2: ENTORNO VIRTUAL PYTHON 3.11 EXCLUSIVO
- **ÚNICO entorno permitido**: Python 3.11.x en entorno virtual
- **NUNCA usar Python del sistema** (puede causar conflictos de dependencias)
- **SIEMPRE activar entorno virtual antes de ejecutar scripts**:
  ```bash
  # Windows
  .venv\Scripts\activate
  
  # Linux/Mac
  source .venv/bin/activate
  ```
- **Verificar versión antes de ejecutar**:
  ```bash
  python --version  # Debe mostrar Python 3.11.x
  ```

### 🔴 REGLA #3: PUNTO DE ENTRADA ÚNICO
- **ÚNICO script autorizado**: `descarga_datos/main.py`
- **NUNCA ejecutar scripts individuales** sin autorización explícita
- **SIEMPRE usar argumentos del main.py**:
  ```bash
  python descarga_datos/main.py --backtest    # Backtesting
  python descarga_datos/main.py --live-mt5    # Trading en vivo MT5
  python descarga_datos/main.py --optimize    # Optimización ML
  ```

---

## ⚠️ ERRORES CRÍTICOS DOCUMENTADOS - NO REPETIR

### 🚫 ERROR #1: AutoTrading Deshabilitado (Error 10027)
**SÍNTOMA**: `Error 10027: Total de posiciones abiertas excedido`
**CAUSA REAL**: AutoTrading deshabilitado en MetaTrader 5
**SOLUCIÓN OBLIGATORIA**:
1. Abrir MT5 → Tools → Options → Expert Advisors
2. ✅ Marcar "Allow automated trading"
3. ✅ Marcar "Allow DLL imports"
4. Reiniciar MT5 completamente
5. Verificar: `python descarga_datos/tests/diagnose_simple.py`

**DOCUMENTACIÓN**: `SOLUCION_ERROR_10027.md`

### 🚫 ERROR #2: Inconsistencia de Timeframes
**PROBLEMA**: Backtest usa 4h, Live MT5 usa 15m → Señales diferentes
**SOLUCIÓN**: Alinear timeframes en `config/config.yaml`
```yaml
backtesting:
  timeframe: 15m  # Cambiar de 4h a 15m

# O cambiar live a 4h si es preferible
```

### 🚫 ERROR #3: Parámetros Duplicados
**PROBLEMA**: `base_parameters` y `optimized_parameters` duplicados en config.yaml
**SOLUCIÓN**: Usar solo `optimized_parameters` por símbolo
**ACCIÓN**: Eliminar duplicación y consolidar parámetros

### 🚫 ERROR #4: RSI Signal Filter Bloqueado
**PROBLEMA**: `rsi_ok_sell = rsi > 30` bloqueaba señales SELL
**SOLUCIÓN APLICADA**: Cambiado a `rsi_ok_sell = rsi < 60`
**UBICACIÓN**: `strategies/ultra_detailed_heikin_ashi_ml_strategy.py:1060`

### 🚫 ERROR #5: Position Size No Recibido
**PROBLEMA**: Position size no se pasaba del risk management al executor
**SOLUCIÓN APLICADA**: Agregado `signal_data['position_size'] = position_size`
**UBICACIÓN**: `core/live_trading_orchestrator.py`

---

## 📁 ESTRUCTURA DE ARCHIVOS PROTEGIDOS

### 🔒 ARCHIVOS CRÍTICOS - NO MODIFICAR SIN AUTORIZACIÓN
```
descarga_datos/
├── main.py                           # 🚨 PUNTO DE ENTRADA ÚNICO
├── config/config.yaml                # 🚨 CONFIGURACIÓN CENTRALIZADA
├── core/
│   ├── live_trading_orchestrator.py  # 🚨 ORQUESTADOR PRINCIPAL
│   └── mt5_order_executor.py         # 🚨 EJECUTOR DE ÓRDENES
├── strategies/
│   └── ultra_detailed_heikin_ashi_ml_strategy.py  # 🚨 ESTRATEGIA PRINCIPAL
└── ACCION_INMEDIATA.txt              # 🚨 PROBLEMAS CRÍTICOS
```

### 📋 ARCHIVOS DE REFERENCIA OBLIGATORIA
```
ARCHIVOS MD/
├── SOLUCION_ERROR_10027.md           # Error AutoTrading
├── CHANGELOG_v4.9.md                 # Cambios v4.9
├── EXECUTIVE_SUMMARY_V411_FINAL.md   # Resumen v4.11
├── GUIA_IMPLEMENTACION_V411.md       # Guía implementación
└── PLAN_V411_OPTIMIZACIONES.md       # Plan optimizaciones
```

---

## 🔧 CONFIGURACIÓN OBLIGATORIA

### 📋 Variables de Entorno (.env)
```bash
# MT5 Configuration (OBLIGATORIO)
MT5_LOGIN=5899273
MT5_PASSWORD=Jatr280371$
MT5_SERVER=Deriv-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# CCXT Configuration (OPCIONAL - Deshabilitado por defecto)
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
```

### ⚙️ Configuración Principal (config.yaml)
```yaml
# CONFIGURACIÓN VALIDADA - NO CAMBIAR SIN AUTORIZACIÓN
backtesting:
  timeframe: 4h                    # ⚠️ INCONSISTENCIA: Live usa 15m
  symbols: [EURUSD]
  initial_capital: 1000

live_trading:
  account_type: 'DEMO'
  max_positions: 5
  risk_per_trade: 0.02

mt5:
  enabled: true                    # ✅ PROVEEDOR PRINCIPAL
  login: 5899273
  server: 'Deriv-Demo'

exchanges:
  binance:
    enabled: false                 # ❌ DESACTIVADO - Usando MT5
```

---

## 🚀 PROCEDIMIENTOS DE EJECUCIÓN

### 📊 Backtesting (VALIDADO)
```bash
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Verificar Python 3.11
python --version

# 3. Ejecutar backtest
python descarga_datos/main.py --backtest

# 4. Verificar resultados en dashboard
# http://localhost:8501
```

### 📈 Live Trading MT5 (OPERATIVO)
```bash
# 1. Verificar MT5 abierto y conectado
python descarga_datos/tests/diagnose_simple.py
# Debe mostrar: "Trading permitido: True ✅"

# 2. Si False, habilitar AutoTrading en MT5
# Tools → Options → Expert Advisors → Allow automated trading

# 3. Ejecutar live trading
python descarga_datos/main.py --live-mt5

# 4. Monitorear logs
Get-Content descarga_datos/logs/live_trading.log -Wait
```

### 🧠 Optimización ML
```bash
# 1. Entrenar modelos (OPCIONAL - Ya entrenados)
python descarga_datos/main.py --optimize

# 2. Verificar modelos en models/
ls descarga_datos/models/
```

---

## 📊 MÉTRICAS DE VALIDACIÓN

### ✅ Backtest Validado (Base de Comparación)
```
Capital Inicial: $1,000
Capital Final: $6,272.97
ROI: 627.3%
Trades Totales: 7,896
Win Rate: 79.9%
Max Drawdown: -12.34%
Profit Factor: 2.45x
Risk/Reward: 1:2.50
```

### ✅ Live Trading Operativo (Estado Actual)
```
Cuenta: 5899273 (Deriv Demo)
Saldo: $9,997.02
Símbolo: Volatility 75 Index
Timeframe: 15m (⚠️ Diferente a backtest 4h)
Position Size: 0.001 lotes
Stop Loss: ATR × 3.25 = 430.28 pts
Take Profit: ATR × 5.5 = 1075.70 pts
ML Confidence: 0.59-0.63 (>0.50 threshold)
```

---

## 🔍 DIAGNÓSTICOS OBLIGATORIOS

### 🩺 Verificación de Sistema
```bash
# 1. Estado MT5
python descarga_datos/tests/diagnose_simple.py

# 2. Conexión y datos
python descarga_datos/tests/test_deriv_complete.py

# 3. Indicadores técnicos
python descarga_datos/tests/test_indicator_consistency.py

# 4. Validación completa
python descarga_datos/tests/test_full_system.py
```

### 📋 Checklist Pre-Ejecución
- [ ] Python 3.11 activado en entorno virtual
- [ ] MT5 abierto y conectado a Deriv-Demo
- [ ] AutoTrading habilitado (diagnose_simple.py = True)
- [ ] Archivo .env con credenciales correctas
- [ ] config.yaml sin modificaciones no autorizadas
- [ ] Logs directory existe y es escribible

---

## 🚨 ESCALACIÓN DE PROBLEMAS

### 🔴 Problemas Críticos (Detener Sistema)
1. **Error 10027**: AutoTrading deshabilitado → Seguir SOLUCION_ERROR_10027.md
2. **Error -10004**: MT5 no conectado → Reiniciar MT5
3. **Error -6**: Credenciales incorrectas → Verificar .env
4. **Memory Leak**: Uso de memoria >90% → Reiniciar sistema

### ⚠️ Problemas Importantes (Investigar)
1. **Win Rate <70%**: Revisar parámetros de estrategia
2. **Señales <10/día**: Verificar filtros de indicadores
3. **Timeframe inconsistency**: Alinear backtest y live
4. **Position Size incorrecto**: Verificar risk management

### 📝 Problemas Menores (Monitorear)
1. **Logs grandes**: Implementar rotación
2. **Dashboard lento**: Optimizar queries
3. **Warnings deprecation**: Actualizar dependencias

---

## 📚 DOCUMENTACIÓN OBLIGATORIA DE CONSULTA

### 🔍 Antes de Modificar Código
1. **CHANGELOG_v4.9.md** - Cambios recientes y fixes aplicados
2. **EXECUTIVE_SUMMARY_V411_FINAL.md** - Estado actual del sistema
3. **Archivos en ARCHIVOS MD/06_Fixes/** - Fixes aplicados

### 🔧 Antes de Implementar Cambios
1. **PLAN_V411_OPTIMIZACIONES.md** - Plan de optimizaciones
2. **GUIA_IMPLEMENTACION_V411.md** - Guía de implementación
3. **Archivos FASE*_STARTER.md** - Guías rápidas por fase

### 🚨 En Caso de Errores
1. **SOLUCION_ERROR_10027.md** - Error AutoTrading
2. **DIAGNOSTICO_ERROR_10027.md** - Análisis detallado
3. **ACCION_INMEDIATA.txt** - Acciones inmediatas

---

## 🎯 OBJETIVOS DE RENDIMIENTO v4.11

### 📈 Performance Targets (En Desarrollo)
```
Objetivo: 10x speedup (5000ms → 500ms por ciclo)

Optimizaciones Planificadas:
- Caching: 8.3x speedup (50ms → 6ms)
- Numba JIT: 3.3x speedup (100ms → 30ms)  
- ONNX ML: 20x speedup (20ms → 1ms)
- Indexing: 6.25x speedup (50ms → 8ms)

Estado: ✅ Diseñado, ⏳ Implementación pendiente
```

### 🔒 Restricciones de Modificación
- **NO modificar** lógica de estrategia sin validación completa
- **NO cambiar** parámetros optimizados sin backtesting
- **NO desactivar** validaciones de seguridad
- **NO ejecutar** en cuenta real sin autorización

---

## ✅ CHECKLIST DE CUMPLIMIENTO

### 📋 Antes de Cada Sesión
- [ ] Respuestas y pensamientos en ESPAÑOL
- [ ] Entorno virtual Python 3.11 activado
- [ ] MT5 abierto con AutoTrading habilitado
- [ ] Documentación de errores conocidos revisada
- [ ] Configuración validada sin cambios no autorizados

### 📋 Durante Desarrollo
- [ ] Solo usar main.py como punto de entrada
- [ ] Consultar ARCHIVOS MD antes de modificaciones
- [ ] Validar cambios con tests existentes
- [ ] Documentar nuevos cambios en español
- [ ] Mantener compatibilidad con v4.10

### 📋 Antes de Producción
- [ ] Backtest regression test (100% match requerido)
- [ ] Live trading validation (24h mínimo)
- [ ] Todos los tests pasando (26/26)
- [ ] Documentación actualizada
- [ ] Plan de rollback preparado

---

## 📞 CONTACTOS Y RECURSOS

### 📚 Documentación Principal
- **Repositorio**: copilot-bot-v-4.11/
- **Documentación**: descarga_datos/ARCHIVOS MD/
- **Configuración**: descarga_datos/config/config.yaml
- **Logs**: descarga_datos/logs/

### 🛠️ Herramientas de Diagnóstico
- **diagnose_simple.py** - Estado MT5
- **test_full_system.py** - Validación completa
- **v411_checklist.py** - Progress tracking (v4.11)

### 📋 Escalación
- **Errores Críticos**: Consultar ACCION_INMEDIATA.txt
- **Problemas Técnicos**: Revisar ARCHIVOS MD/06_Fixes/
- **Dudas de Implementación**: GUIA_IMPLEMENTACION_V411.md

---

## 🏁 RESUMEN EJECUTIVO

**SISTEMA ACTUAL**: Bot Trader Copilot v4.11 operativo en MT5 Deriv Demo
**ESTADO**: ✅ Live Trading funcional, 79.9% win rate, 7,896 trades validados
**PROBLEMA PRINCIPAL**: Error 10027 (AutoTrading) - Solución documentada
**PRÓXIMOS PASOS**: Implementar optimizaciones v4.11 (10x speedup)
**RESTRICCIÓN CRÍTICA**: Solo Python 3.11 en entorno virtual, solo español

---

**FECHA**: 31 de enero de 2026
**VERSIÓN**: v4.11 (con optimizaciones en desarrollo)
**ESTADO**: ✅ OPERATIVO - Seguir estas instrucciones estrictamente