# 🚀 QUICK START: SANDBOX → PRODUCTION
## Guía de 5 minutos para empezar

**Versión:** 1.0  
**Para:** Ejecutar BotCopilot en vivo  
**Tiempo:** ~5 minutos para setup, 24-48h para validación  

---

## ✅ CHECKLIST PRE-SANDBOX (5 min)

```
[ ] 1. Verificar config.yaml tiene config correcta
[ ] 2. Verify API keys en .env o variables entorno
[ ] 3. Confirmar sandbox: true en config.yaml
[ ] 4. Run quick test: python -m pytest descarga_datos/tests/test_quick_backtest.py
[ ] 5. Check dashboard está accesible: localhost:8888/dashboard.html
```

---

## 🔵 OPCIÓN 1: SANDBOX TESTING (Recomendado - START HERE)

### Setup (1 min)

**1. Verificar config.yaml**

```yaml
# descarga_datos/config/config.yaml
exchanges:
  binance:
    sandbox: true  # ← CRITICAL: DEBE SER true
    apiKey: ${BINANCE_API_KEY}  # From .env
    secret: ${BINANCE_API_SECRET}  # From .env
    enableRateLimit: true
    rateLimit: 400

trading:
  live_mode: true  # Habilitar live trading
  position_size: 0.01  # 1% del balance
```

**2. Configurar .env**

```bash
# .env (NUNCA en git)
BINANCE_API_KEY=your_testnet_key_here
BINANCE_API_SECRET=your_testnet_secret_here
BINANCE_SANDBOX=true
```

### Ejecución (1 min)

```bash
# Terminal 1: Iniciar bot
cd descarga_datos
python main.py --live

# Terminal 2: Ver dashboard
# Abrir: http://localhost:8888/dashboard.html
```

### Monitoreo (24-48h)

**Checkpoints:**
- ✅ Dashboard actualiza cada minuto
- ✅ Alerts se disparan (Telegram si configurado)
- ✅ Posiciones abren sin errores
- ✅ Posiciones cierran correctamente
- ✅ Balance se sincroniza
- ✅ Logs sin "ERROR" messages

**Logs Location:**
```
descarga_datos/logs/trading.log  # Ver errors aquí
```

**Ver Logs en Vivo:**
```bash
# Terminal: Monitorear logs en tiempo real
tail -f descarga_datos/logs/trading.log
```

### Decisión: Go/No-Go (24-48h)

**GO → PRODUCCIÓN:**
- ✅ 48 horas sin errores
- ✅ Trades abriendo/cerrando correctamente
- ✅ Dashboard actualizado
- ✅ Logs limpios

**NO-GO → DEBUG:**
- ❌ Si hay errores: revisar `CCXT_BEST_PRACTICES_LIVE_TRADING.md`
- ❌ Error "RateLimitExceeded" → aumentar rateLimit
- ❌ Error "ExchangeNotAvailable" → retry logic needed
- ❌ Posición no cierra → check Binance manualmente

---

## 🟢 OPCIÓN 2: PRODUCCIÓN (Después sandbox OK)

### Setup (2 min)

**1. Cambiar config.yaml**

```yaml
# CAMBIO CRÍTICO:
exchanges:
  binance:
    sandbox: false  # ← PRODUCCIÓN (no testnet)
    apiKey: ${BINANCE_API_KEY_LIVE}  # Live key
    secret: ${BINANCE_API_SECRET_LIVE}  # Live secret
    enableRateLimit: true
    rateLimit: 400

trading:
  live_mode: true
  position_size: 0.01  # COMIENZA PEQUEÑO: 1% del balance
```

**2. Configurar .env con credenciales LIVE**

```bash
# .env
BINANCE_API_KEY_LIVE=your_live_key_here
BINANCE_API_SECRET_LIVE=your_live_secret_here
# IMPORTANTE: Usa credenciales DIFERENTES de testnet
```

**3. Verificar permisos API (Binance)**
- ✅ Spot Trading: Habilitado
- ✅ IP Whitelist: Tu IP del servidor
- ✅ Withdrawing: Deshabilitado (CRÍTICO)
- ✅ Device Binding: Habilitado

### Ejecución (1 min)

```bash
# Terminal 1: Iniciar bot
cd descarga_datos
python main.py --live  # Usará config.yaml con sandbox: false

# Terminal 2: Dashboard
# Abrir: http://localhost:8888/dashboard.html
```

### Monitoreo 24/7

**Primeras 48 horas: Monitoring muy activo**
```bash
# Terminal: Logs en vivo
tail -f descarga_datos/logs/trading.log

# Chequear cada 2 horas:
# - Dashboard actualizado?
# - Alerts arriving?
# - Balances correctos?
# - Trades ejecutados?
```

**Después 48 horas: Monitoreo normal**
```bash
# Chequear una vez por día:
# - Ganancias/pérdidas totales
# - Errores en logs
# - Balance correctamente
```

### Scaling Strategy

**Semana 1:** $100-500 capital
- Monitor: Very active
- Decision: Keep or stop?

**Semana 2:** $500-2,000 capital (if profitable)
- Monitor: Active
- Decision: Scale more?

**Semana 3-4:** Gradual scaling
- Monitor: Normal
- Decision: Long-term viability?

### Graceful Shutdown

```bash
# Si necesitas detener:
# 1. Presiona Ctrl+C en terminal del bot
# 2. Bot cerrará posiciones abiertas gracefully
# 3. Guardará estado en BD
# 4. Salida limpia sin errores

# Verificar posiciones cerradas:
python descarga_datos/verificar_balance.py
```

---

## 🔴 OPCIÓN 3: FREQTRADE RESEARCH (Opcional, 1-2 weeks)

**NO RECOMENDADO PRIMERO** - Hacer después que Sandbox OK

### Setup (1h)

```bash
# Clone Freqtrade
git clone https://github.com/freqtrade/freqtrade.git
cd freqtrade
python -m venv venv
source venv/bin/activate  # o: venv\Scripts\activate (Windows)
pip install -e .
```

### Purpose (Research only)
- Compare backtesting results
- Learn enterprise patterns
- Evaluate multi-pair optimization

### Risk
- 🟢 CERO - Es solo research/backtesting, no trading real

---

## 🆘 TROUBLESHOOTING RÁPIDO

### Error: "RateLimitExceeded"
```
Problema: Llamadas muy rápidas a exchange
Solución: En config.yaml, aumentar rateLimit
  rateLimit: 400 → 500  (más tiempo entre calls)
Resultado: Más lento pero sin errores
```

### Error: "ExchangeNotAvailable"
```
Problema: Exchange offline o en mantenimiento
Solución: Esperar, bot reintentar automáticamente
Verificar: https://status.binance.com
Tiempo: Usualmente resuelto en minutos
```

### Error: "InvalidNonce"
```
Problema: Reloj del servidor desincronizado
Solución: Sincronizar reloj del servidor
  Linux: ntpdate -s time.nist.gov
  Windows: net stop w32time; net start w32time
Resultado: Resuelto inmediatamente
```

### Error: "InsufficientFunds"
```
Problema: Balance insuficiente para orden
Solución: Reducir position_size en config.yaml
  position_size: 0.01 → 0.005  (0.5% en lugar de 1%)
Alternativa: Depositar más en cuenta
```

### Dashboard no actualiza
```
Problema: Conexión perdida o error en bot
Solución 1: Verificar bot está corriendo
  ps aux | grep main.py  (Linux)
  tasklist | grep python  (Windows)
Solución 2: Revisar logs
  tail descarga_datos/logs/trading.log
Solución 3: Reiniciar bot
  Ctrl+C y python main.py --live
```

---

## 📊 MÉTRICAS A MONITOREAR

### Diarias
```
Métrica              Target      Warning     Stop
─────────────────────────────────────────────────
Ganancias/día        $+ (any)    $-10        $-100+
Win rate             > 50%       40%         < 20%
Trades ejecutados    1-5         0           N/A
Posiciones abiertas  0-1         2+          N/A
Drawdown actual      < 10%       15%         > 20%
Errores en logs      0           1-2         3+
```

### Semanales
```
Métrica              Target          Action
─────────────────────────────────────────────
P&L semanal          Positivo        Review estrategia
Sharpe ratio         > 1.5           Mejorar entries
Max drawdown         < 15%           Reducir size
Error count          0               Debug issues
Capital escala       Aumentar?       Revisar ganancias
```

---

## 🔒 SEGURIDAD CHECKLIST

```
ANTES DE PRODUCCIÓN:
[ ] API Key: IP whitelist habilitado
[ ] API Key: Withdraw DESHABILITADO
[ ] API Key: Solo Trading, no transfer
[ ] Config: sandbox: false (no testnet)
[ ] Credenciales: En .env, NO en config.yaml
[ ] Logs: Guardándose en descarga_datos/logs/
[ ] Dashboard: Accesible solo localmente
[ ] Alerts: Configuradas (Telegram/Email)
[ ] Monitoring: 24/7 setup
[ ] Graceful shutdown: Probado
[ ] Backup: Estado guardado en BD
```

---

## 📈 MÉTRICAS DE ÉXITO

### Sandbox (Validación)
```
✅ SUCCESS if:
- Dashboard actualiza en tiempo real
- Trades abren y cierran sin errores
- Logs no tienen "ERROR" entries
- Balance se sincroniza correctamente
- 48 horas ejecutando sin crashes

🚫 FAIL if:
- Errores frecuentes en logs
- Posiciones abiertas pero no se cierran
- Dashboard no actualiza
- Crashes o hangs
```

### Producción (Rentabilidad)
```
📈 GOOD if:
- Win rate > 60%
- Sharpe ratio > 1.5
- Max drawdown < 15%
- P&L creciendo semana a semana
- Cero liquidaciones

📉 REVIEW if:
- Win rate < 40%
- Max drawdown > 25%
- Negative P&L por 2+ semanas
- Múltiples errors en logs
```

---

## 🎯 DECISION TREE

```
¿Quieres empezar ya?
│
├─ SI → ¿Tienes credenciales Binance?
│  │
│  ├─ NO → Crear cuenta + obtener testnet keys
│  │
│  └─ SI → ¿Sandbox o Producción?
│     │
│     ├─ SANDBOX (recomendado)
│     │  └─ Seguir "OPCIÓN 1" arriba
│     │     └─ 24-48h validación
│     │        └─ Si OK → OPCIÓN 2
│     │
│     └─ PRODUCCIÓN (solo si sandbox OK)
│        └─ Seguir "OPCIÓN 2" arriba
│           └─ 24/7 monitoring
│              └─ Scale si rentable
│
└─ NO → Leer documentos completos primero
   ├─ INVESTIGACION_CCXT_FREQTRADE_JESSE_v1.md
   ├─ CCXT_BEST_PRACTICES_LIVE_TRADING.md
   └─ Luego volver aquí
```

---

## 📞 QUICK REFERENCE

### Commands
```bash
# Iniciar bot (sandbox)
python descarga_datos/main.py --live

# Ver dashboard
http://localhost:8888/dashboard.html

# Monitorear logs
tail -f descarga_datos/logs/trading.log

# Verificar balance
python descarga_datos/verificar_balance.py

# Detener bot
Ctrl+C (graceful shutdown)

# Run tests
python -m pytest descarga_datos/tests/test_quick_backtest.py
```

### Archivos Importantes
```
config.yaml              ← Configuración centralizada
.env                     ← Credenciales (NUNCA en git)
logs/trading.log         ← Logs de operaciones
data/trades.json         ← Historial de trades
data/dashboard_results/  ← Backtesting results
```

### Ubicaciones
```
Dashboard:   http://localhost:8888/dashboard.html
Logs:        descarga_datos/logs/
Config:      descarga_datos/config/
```

---

## ⏰ TIMELINE TÍPICA

### Día 1 (Setup)
- 10 min: Setup config.yaml + .env
- 5 min: Verificar credenciales
- 5 min: Iniciar bot en sandbox
- Resto: Monitorear primeras horas

### Días 2-3 (Validation)
- Monitorear dashboard
- Revisar logs cada 2h
- Documentar issues
- Ajustar si es necesario

### Día 3-4 (Decision)
- Revisar metrics
- Go/No-Go decision
- Si OK: cambiar a producción
- Si NO: debug + retest

### Semanas 2-4 (Production)
- Monitor 24/7 primeras 48h
- Scaling gradual
- Optimización parámetros

---

## 🎓 APRENDIZAJE

Si algo no funciona:
1. **Ver logs:** `tail descarga_datos/logs/trading.log`
2. **Buscar error:** En `CCXT_BEST_PRACTICES_LIVE_TRADING.md`
3. **Implementar fix:** Seguir instrucciones
4. **Retest:** Volver a ejecutar
5. **Si persiste:** Revisar documentación completa

---

## ✨ RESUMEN

| Paso | Acción | Tiempo | Risk |
|------|--------|--------|------|
| 1 | Setup config | 5 min | 🟢 Cero |
| 2 | Sandbox test | 24-48h | 🟢 Cero |
| 3 | Validación | 2h | 🟢 Cero |
| 4 | Producción | On-demand | 🟡 Low (start small) |
| 5 | Scaling | Gradual | 🟡 Low-Medium |

---

**Document:** QUICK_START_SANDBOX_PRODUCTION.md  
**Version:** 1.0  
**Applicable To:** BotCopilot v2.0+  
**Last Updated:** 26/10/2025  
**Status:** ✅ Ready to Use

**Next Step:** Ejecutar `python descarga_datos/main.py --live` (sandbox: true)
