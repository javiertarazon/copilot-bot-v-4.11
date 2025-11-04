# 📋 PLAN DE IMPLEMENTACIÓN - 4 FIXES CRÍTICOS

**Fecha:** 28 de Octubre 2025  
**Estado:** ❓ ACLARACIONES REQUERIDAS ANTES DE EJECUTAR

---

## 🎯 PREGUNTAS CRÍTICAS (RESPONDE ANTES DE CONTINUAR)

### 1️⃣ SINCRONIZACIÓN DE POSICIONES

**Pregunta:** ¿Dónde está el código actual de live trading?

- ¿Está en `descarga_datos/core/live_trading_orchestrator.py`?
- ¿O en otro archivo como `main.py --live-ccxt`?
- ¿Necesito actualizar ambos?

**Impacto:** Determina qué archivos modificar

**Opciones:**
```
A) Solo live_trading_orchestrator.py (recomendado para modularidad)
B) Solo main.py (si todo está centralizado)
C) Ambos (cobertura completa)
```

---

### 2️⃣ TRAILING STOP CORRECTO

**Pregunta:** ¿Cómo está implementado actualmente el trailing stop?

- ¿Está en `strategies/ultra_detailed_heikin_ashi_ml_strategy.py`?
- ¿O en `risk_management/` (archivo específico)?
- ¿Es un trailing stop dinámico o fijo?

**Impacto:** Determina si reemplazar completamente o mejorar existente

**Opciones:**
```
A) Reemplazar completamente con patrón Freqtrade (más robusto)
B) Mejorar el actual (menos invasivo)
C) Crear nuevo módulo paralelo (menos riesgo)
```

---

### 3️⃣ P&L CON COMISIONES

**Pregunta:** ¿Dónde se calcula actualmente el P&L?

- ¿En `backtesting/backtester.py`?
- ¿En `core/` (módulo específico)?
- ¿Se reporta en logs o en dashboard?

**Impacto:** Determina dónde inyectar el cálculo de comisiones

**Opciones:**
```
A) En el backtester (afecta todos los backtests)
B) En live trading (afecta solo operaciones reales)
C) En ambos (máxima precisión)
```

---

### 4️⃣ CIERRE SEGURO (GRACEFUL SHUTDOWN)

**Pregunta:** ¿Cómo se detiene actualmente el bot en live trading?

- ¿Hay implementado un manejador de `KeyboardInterrupt`?
- ¿Se cierran conexiones con exchange (Bybit)?
- ¿Se guardan posiciones abiertas antes de cerrar?
- ¿Hay dashboard Streamlit que mostrar resultados?

**Impacto:** Determina qué recursos gestionar en shutdown

**Opciones:**
```
A) Implementar en main.py (entry point)
B) Implementar en live_trading_orchestrator.py
C) Ambos con coordinación
```

---

## 📍 CONTEXTO ACTUAL DEL PROYECTO

### Estructura de Archivos Relevantes
```
descarga_datos/
├── main.py                           ← Entry point (--live-ccxt, --backtest)
├── core/
│   ├── live_trading_orchestrator.py  ← Orquestación live
│   ├── order_executor.py             ← Ejecución de órdenes
│   └── data_downloader.py            ← Descarga CCXT
├── strategies/
│   └── ultra_detailed_heikin_ashi_ml_strategy.py  ← Lógica de trading
├── risk_management/
│   ├── position_manager.py
│   ├── risk_calculator.py
│   └── trailing_stop_manager.py     ← ¿Trailing stop aquí?
├── backtesting/
│   └── backtester.py                ← Cálculo de P&L
└── utils/
    └── logger.py                     ← Logging
```

---

## ❓ PREGUNTAS SECUNDARIAS

### 5. EXCHANGE Y COMISIONES
- **¿Qué exchange usas principalmente?**
  - Bybit (crypto, 0.02% comisión)
  - Binance (0.1% comisión)
  - Otro?

**Esto afecta:** Valores de comisión a usar en cálculos

### 6. MODO DE EJECUCIÓN PRINCIPAL
- **¿Dónde pasarás más tiempo?**
  - Backtesting (parámetros nuevos)
  - Live trading (sandbox)
  - Live trading (real)

**Esto afecta:** Prioridad de fixes (todos son importantes, pero orden varía)

### 7. RESTRICCIONES CONOCIDAS
- **¿Hay código que NO debo tocar?**
  - Según instrucciones: strategy.py estructura bloqueada
  - main.py estructura bloqueada
  - ¿Hay más limitaciones?

**Esto afecta:** Cómo inyectar los fixes sin romper restricciones

### 8. TESTING
- **¿Quieres que pruebe cada fix?**
  - ¿Con backtest (`main.py --backtest-only`)?
  - ¿Con sandbox live (`sandbox: true`)?
  - ¿Ambos?

**Esto afecta:** Tiempo total y validación de cambios

---

## 📊 RESUMEN DE CAMBIOS PROPUESTOS

| Fix | Prioridad | Complejidad | Archivo Principal | Testing Requerido |
|-----|-----------|-------------|-------------------|-------------------|
| **Sincronización** | 🔴 Crítica | Media | `live_trading_orchestrator.py` | ✅ Live sandbox |
| **Trailing Stop** | 🔴 Crítica | Alta | `risk_management/` o `strategies/` | ✅ Backtest + Live |
| **P&L Comisiones** | 🟡 Alta | Baja | `backtesting/backtester.py` | ✅ Backtest |
| **Cierre Seguro** | 🟡 Alta | Media | `main.py` o `orchestrator` | ✅ Manual |

---

## 🚀 PRÓXIMOS PASOS (UNA VEZ RESPONDAS)

1. **Responder las 8 preguntas arriba**
2. **Yo crearé plan detallado** con:
   - Archivos exactos a modificar
   - Código a copiar de Freqtrade
   - Puntos de integración precisos
   - Tests a ejecutar
3. **Ejecutar implementación** en fases:
   - Fase 1: P&L Comisiones (más simple)
   - Fase 2: Sincronización (media complejidad)
   - Fase 3: Trailing Stop (más complejo)
   - Fase 4: Cierre Seguro (validación)
4. **Validar cada fase** antes de siguiente

---

## 📋 CHECKLIST PRE-IMPLEMENTACIÓN

- [ ] Respondiste todas 8 preguntas
- [ ] Confirmaste estructura actual del proyecto
- [ ] Identificaste restricciones (código bloqueado)
- [ ] Definiste prioridad de fixes
- [ ] Acordaste estrategia de testing

---

**⏸️ EN PAUSA:** Esperando tus respuestas para continuar.
