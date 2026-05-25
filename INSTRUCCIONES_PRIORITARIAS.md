# Instrucciones prioritarias del repositorio canónico

## Reglas fundamentales

### 1. Idioma

- Documentación y mensajes operativos en español.
- Nombres de variables, funciones y clases en inglés.

### 2. Punto de entrada

- El único punto de entrada operativo es:
  - `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py`

### 3. Alcance

- Un único bot
- Un único símbolo: `XAUUSD`
- Un único timeframe: `15m`
- Una única estrategia inicial: `UltraDetailedHeikinAshiML`
- Un único flujo live: `MT5 demo`

### 4. Promoción obligatoria

Ninguna versión se ejecuta en demo o real sin pasar este orden:

1. entrenamiento
2. validación
3. prueba final
4. sandbox/demo

### 5. Credenciales

- No guardar credenciales en documentación ni en YAML.
- Usar variables de entorno o `.env`.
- Plantilla oficial:
  - `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/.env.example`

### 6. Archivos canónicos

- Configuración: `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/config/config.yaml`
- Validación: `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/docs/VALIDACION_XAUUSD.md`
- Estrategia principal: `/tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/strategies/ultra_detailed_heikin_ashi_ml_strategy.py`

## Comandos oficiales

```bash
python /tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py --train-ml
python /tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py --backtest-only
python /tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py --validation-report
python /tmp/workspace/javiertarazon/copilot-bot-v-4.11/descarga_datos/main.py --live-mt5
```

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