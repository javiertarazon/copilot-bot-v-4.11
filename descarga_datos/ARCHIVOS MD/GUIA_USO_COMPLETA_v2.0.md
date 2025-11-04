# 🚀 GUÍA DE USO COMPLETA - SISTEMA DE TRADING v2.0

**Versión**: 2.0 (Post PHASES 1-3.1)  
**Fecha**: Octubre 2025  
**Status**: ✅ Producción Ready  

---

## 📋 TABLA DE CONTENIDOS

1. [Setup Inicial](#setup-inicial)
2. [Backtesting](#backtesting)
3. [Live Trading Sandbox](#live-trading-sandbox)
4. [Live Trading Real](#live-trading-real)
5. [Monitoreo y Alertas](#monitoreo-y-alertas)
6. [Dashboard](#dashboard)
7. [Troubleshooting](#troubleshooting)

---

## ⚙️ Setup Inicial

### 1. Verificar Dependencias

```bash
cd c:\Users\javie\copilot\botcopilot-sar

# Verificar Python
python --version  # Debe ser 3.11.9+

# Verificar paquetes principales
pip list | grep -E "ccxt|pandas|numpy|ta-lib"
```

### 2. Compilar Módulos Nuevos

```bash
# Verificar sintaxis
python -m py_compile descarga_datos/core/ccxt_live_trading_orchestrator.py
python -m py_compile descarga_datos/core/ccxt_order_executor.py
python -m py_compile descarga_datos/core/orchestrator_alert_integration.py
python -m py_compile descarga_datos/utils/alert_manager.py
python -m py_compile descarga_datos/dashboard.py

# Si todo OK, continuar
```

### 3. Instalar Streamlit (para dashboard)

```bash
pip install streamlit
pip install plotly
pip install requests  # Para Discord webhook
```

### 4. Crear Directorios si no Existen

```bash
mkdir -p descarga_datos/logs
mkdir -p descarga_datos/data
```

---

## 🔬 Backtesting

### Quick Test (Smoke Test)

```bash
# Ejecutar test rápido
cd c:\Users\javie\copilot\botcopilot-sar
python -m pytest descarga_datos/tests/test_quick_backtest.py -v

# Salida esperada:
# PASSED ✅
# Time taken: ~5 segundos
```

### Backtesting Completo

```bash
# Opción 1: Configuración por defecto
python descarga_datos/main.py --backtest

# Opción 2: Con parámetros específicos
python descarga_datos/main.py --backtest --symbol BTC/USDT --timeframe 4h

# Opción 3: Últimas 30 días
python descarga_datos/main.py --backtest --days 30
```

### Validar Resultados

```bash
# Revisar archivo de resultados
cat descarga_datos/data/trading_results.json | python -m json.tool

# Buscar en logs
grep "PnL con comisiones" descarga_datos/logs/trading.log
grep "sync_positions" descarga_datos/logs/trading.log
```

### Métricas Esperadas

| Métrica | Valor Esperado | Nota |
|---------|---|---|
| Total Operaciones | >10 | Depende período |
| Win Rate | 30-50% | Realista |
| P&L Neto | Variable | Con comisiones |
| Comisiones % | ~0.2% | Binance SPOT |
| Discrepancias | 0 | Clave validación |

---

## 🏪 Live Trading Sandbox

### Habilitar Sandbox

```bash
# Editar config
nano descarga_datos/config/config.yaml

# Buscar sección exchange:
exchange:
  name: binance
  sandbox: true  # ← IMPORTANTE: true para sandbox
  apiKey: xxx
  secret: xxx
```

### Ejecutar en Sandbox (1 hora)

```bash
# Lanzar sistema
python descarga_datos/main.py --live

# En otra terminal, monitorear alertas
tail -f descarga_datos/logs/alerts.log

# En otra terminal, dashboard
streamlit run descarga_datos/dashboard.py
```

### Dashboard en Localhost

```
URL: http://localhost:8501
Abrir en navegador → Verás:
- Métricas principales
- Alertas activas
- Posiciones abiertas
- Gráficos P&L
```

### Validaciones Críticas (1 hora)

- ✅ Posiciones se abren correctamente
- ✅ Trailing stop se ajusta cada ~60s
- ✅ Sincronización cada ~60s (ver logs)
- ✅ Balance exacto vs Binance
- ✅ 0 posiciones fantasma nuevas
- ✅ P&L incluye comisiones
- ✅ Alertas funcionan (si Discord webhook configurado)

### Shutdown Graceful

```bash
# Presionar Ctrl+C para graceful shutdown
# El sistema:
# - Cierra todas las posiciones abiertas ✅
# - Guarda estado ✅
# - Cierra conexiones ✅
# - Log final ✅
```

---

## 💰 Live Trading Real

### ⚠️ REQUISITOS PREVIOS

Antes de ejecutar en real:

1. ✅ PHASE 1 validado (backtesting OK)
2. ✅ PHASE 2 validado (24h sandbox sin errores)
3. ✅ Documentar riesgo máximo por operación
4. ✅ Configurar alertas Discord
5. ✅ Revisar comisiones en config
6. ✅ Validar balance USDT en Binance

### Cambiar a Real

```bash
# config.yaml
exchange:
  sandbox: false  # ← Cambiar a false
```

### Lanzar en Real

```bash
# Terminal 1: Trading engine
python descarga_datos/main.py --live

# Terminal 2: Monitoreo de alertas (IMPORTANTE!)
tail -f descarga_datos/logs/alerts.log

# Terminal 3: Dashboard
streamlit run descarga_datos/dashboard.py

# Terminal 4: Verificación periódica (cada 5 min)
watch -n 300 'python descarga_datos/tests/sync_positions_auditor.py'
```

### Monitoreo Activo (Primeras 24h)

Revisar cada 1-2 horas:
- ✅ Posiciones abiertas
- ✅ Balance actualizado
- ✅ Alertas (especialmente CRITICAL)
- ✅ P&L realizando bien
- ✅ Logs sin errores

---

## 📊 Monitoreo y Alertas

### Alertas Automáticas

El sistema genera alertas automáticas para:

| Alerta | Severidad | Acción |
|---|---|---|
| SYNC_FAILED | 🔴 CRITICAL | Revisar conexión Binance |
| PHANTOM_POSITION | 🔴 CRITICAL | Investigar posición |
| BALANCE_MISMATCH | 🟡 WARNING | Verificar sync |
| TRAILING_STOP_ERROR | 🟡 WARNING | Revisar lógica |
| PNL_ANOMALY | 🟡 WARNING | Revisar operaciones |
| CONNECTION_ERROR | 🔴 CRITICAL | Revisar API keys |

### Configurar Discord Webhook

```bash
# 1. Crear servidor Discord (si no tienes)
# 2. Crear canal #trading-alerts
# 3. Crear webhook:
#    - Right-click canal → Edit Channel
#    - Webhooks → New Webhook
#    - Copiar URL

# 4. Actualizar config
nano descarga_datos/utils/alert_manager.py

# Buscar:
enable_discord = False
discord_webhook_url = None

# Cambiar a:
enable_discord = True
discord_webhook_url = "https://discord.com/api/webhooks/xxx/yyy"
```

### Leer Alertas

```bash
# Ver alertas activas
python -c "
import json
with open('descarga_datos/data/alert_history.json') as f:
    alerts = json.load(f)
    for a in alerts:
        if not a.get('resolved'):
            print(f'{a[\"severity\"]}: {a[\"title\"]}')"

# Ver últimas alertas
tail -50 descarga_datos/logs/alerts.log
```

---

## 🎯 Dashboard Web

### Lanzar Dashboard

```bash
cd descarga_datos
streamlit run dashboard.py
```

### URL y Puerto

```
http://localhost:8501
```

### Pantalla Principal

1. **Métricas Principales** (top)
   - 💰 P&L Total
   - 🎯 Win Rate
   - ⚠️ Alertas Activas
   - 🔄 Sincronización

2. **Alertas Activas** (section 2)
   - Críticas (🔴)
   - Advertencias (🟡)
   - Información (ℹ️)

3. **Posiciones Abiertas** (section 3)
   - Tabla con todas las posiciones
   - Precio entrada, unrealized P&L

4. **Gráficos** (section 4)
   - Ganancia acumulada
   - Distribución de operaciones

5. **Historial** (section 5)
   - Últimas 10 operaciones cerradas

6. **Configuración** (sidebar)
   - Refresh rate
   - Filtros
   - Estadísticas
   - Botón descargar reporte

### Descargar Reporte

```
1. Sidebar → "Descargar Reporte"
2. Botón "Descargar JSON"
3. Archivo: report_20251026_142030.json
```

---

## 🔧 Troubleshooting

### Problema 1: "sync_positions_with_exchange() falla"

**Síntomas**: Alerta SYNC_FAILED constantemente

**Causas posibles**:
- API key expirada
- Rate limit de Binance
- Conexión internet lenta
- IP bloqueada

**Solución**:
```bash
# Verificar API keys
python -c "import ccxt; ex = ccxt.binance({'apiKey': 'xxx', 'secret': 'yyy'}); print(ex.fetch_balance())"

# Esperar y reintentar (rate limit)
sleep 60
python descarga_datos/main.py --live

# Verificar IP en Binance
# https://www.binance.com/en/my/security
```

### Problema 2: "Balance mismatch > 0.1%"

**Síntomas**: Alerta BALANCE_MISMATCH

**Causas posibles**:
- Operación ejecutada externamente
- Comisiones no contabilizadas
- Staking/earning en Binance
- Bug en cálculo

**Solución**:
```bash
# Ejecutar auditoría
python descarga_datos/tests/sync_positions_auditor.py

# Revisar si hay operaciones en Binance
# https://www.binance.com/en/my/orders/spot

# Si es por comisiones:
# check_balance_consistency() en logs
# Revisar si comisión está incluida en P&L
```

### Problema 3: "Posición fantasma detectada"

**Síntomas**: Alerta PHANTOM_POSITION

**Causas posibles**:
- Orden cancelada en Binance pero no en sistema
- Bug en close_position_safe()
- Sync no ejecutó a tiempo

**Solución**:
```bash
# Ejecutar sync manual
await orchestrator.sync_positions_with_exchange()

# Revisar logs
grep "PHANTOM" descarga_datos/logs/alerts.log

# Si persiste, reiniciar orchestrator
```

### Problema 4: "Dashboard no carga datos"

**Síntomas**: Dashboard en blanco o error

**Causas posibles**:
- Archivos JSON no existen
- Streamlit cache corrupted
- Python path incorrect

**Solución**:
```bash
# Crear archivos vacíos
touch descarga_datos/data/alert_history.json
touch descarga_datos/data/position_history.json
echo "[]" > descarga_datos/data/alert_history.json

# Limpiar cache Streamlit
rm -rf ~/.streamlit/cache

# Reiniciar
streamlit run descarga_datos/dashboard.py
```

### Problema 5: "Trailing stop no se actualiza"

**Síntomas**: Alerta TRAILING_STOP_ERROR

**Causas posibles**:
- _update_trailing_stop() no se ejecuta
- Posición no tiene highest_price
- Fórmula incorrecta

**Solución**:
```bash
# Verificar logs
grep "_update_trailing_stop" descarga_datos/logs/trading.log

# Revisar código (línea 734-830)
grep -A5 "highest_price = " descarga_datos/core/ccxt_live_trading_orchestrator.py

# Forzar recalculación (restart trading engine)
```

---

## 📞 Comandos Útiles

### Monitoreo

```bash
# Ver últimas operaciones
tail -20 descarga_datos/logs/trading.log

# Ver últimas alertas
tail -20 descarga_datos/logs/alerts.log

# Contar alertas activas
grep '"resolved": false' descarga_datos/data/alert_history.json | wc -l

# Ver balance actual
python -c "from descarga_datos.utils.storage import *; print(get_account_balance())"

# Auditoría completa
python descarga_datos/tests/sync_positions_auditor.py
```

### Mantenimiento

```bash
# Backup de datos
cp -r descarga_datos/data descarga_datos/data.backup.$(date +%Y%m%d)

# Limpiar logs antiguos (>30 días)
find descarga_datos/logs -name "*.log" -mtime +30 -delete

# Verificar integridad DB
sqlite3 descarga_datos/data/trading_data.db ".integrity_check"

# Optimizar DB
sqlite3 descarga_datos/data/trading_data.db "VACUUM;"
```

### Debug

```bash
# Modo verbose
LOGLEVEL=DEBUG python descarga_datos/main.py --live

# Verificar sync manual
python -c "
import asyncio
from descarga_datos.core.orchestrator_alert_integration import *
# ... setup code
await orchestrator.sync_positions_with_exchange()
print('Sync completado')
"

# Test de comisiones
python -c "
from descarga_datos.core.ccxt_order_executor import *
pos = {'entry_price': 100, 'exit_price': 110, 'quantity': 1, 'type': 'buy'}
pnl = executor._calculate_pnl_with_fees(pos)
print(f'P&L con comisiones: {pnl}')
"
```

---

## 🎓 Flujo Típico de Operación

### Mañana
```
08:00 - Iniciar sistema
08:05 - Revisar dashboard
08:10 - Verificar alertas
08:15 - Revisar posiciones abiertas
```

### Mediodía
```
12:00 - Check rápido
12:05 - Revisar si hay alertas críticas
12:10 - Si OK, continuar
```

### Tarde
```
17:00 - Check detallado
17:05 - Revisar balance vs Binance
17:10 - Revisar P&L del día
17:15 - Si todo OK, monitor pasivo
```

### Noche
```
22:00 - Check final
22:05 - Revisar logs de alertas
22:10 - Preparar cierre
23:00 - Decidir si reiniciar o mantener overnight
```

---

## ✅ CHECKLIST PRE-PRODUCCIÓN

- [ ] Backtesting OK (>10 operaciones)
- [ ] Sandbox 24h sin errores
- [ ] Dashboard funciona
- [ ] Alertas Discord configuradas
- [ ] Sincronización cada 60s verificada
- [ ] P&L con comisiones verificado
- [ ] Balance exacto vs Binance
- [ ] 0 posiciones fantasma
- [ ] API keys rotadas recientemente
- [ ] Documentación revisada
- [ ] Equipo familiarizado con sistema
- [ ] Plan de rollback documentado

---

## 🆘 SOPORTE

### Recursos
- 📄 `PHASE_1_COMPLETADA_RESUMEN.md` - Detalle fixes
- 📄 `PROXIMOS_PASOS_PHASE_2.md` - Checklist
- 📄 `PHASE_3_INVESTIGACION_FREQTRADE.md` - Upgrade path
- 💻 Logs: `descarga_datos/logs/`
- 📊 Data: `descarga_datos/data/`

### Contacto
Para issues técnicos:
1. Revisar logs
2. Buscar en documentación
3. Ejecutar auditoría
4. Reiniciar sistema

---

**Última actualización**: Octubre 2025  
**Version**: 2.0  
**Status**: ✅ Production Ready

---

*¡Sistema listo para operar!*
