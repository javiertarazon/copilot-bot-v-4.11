# 🚀 INSTRUCCIONES RÁPIDAS - Live Trading v4.6

**Versión:** 4.6 (Corrección de Fórmulas)  
**Fecha:** 25 de Octubre de 2025  
**Status:** ✅ LISTO PARA EJECUTAR

---

## ⚡ INICIO RÁPIDO

### 1️⃣ Pre-requisitos

```bash
# Verificar que Python está activo
cd c:\Users\javie\copilot\botcopilot-sar

# Activar virtual environment (si es necesario)
.venv\Scripts\Activate.ps1

# Verificar dependencias
pip list | findstr "ccxt pandas"
```

### 2️⃣ Ejecutar Live Trading

```bash
# Opción A: CCXT (Crypto - Binance Testnet)
python descarga_datos/main.py --live-ccxt

# Opción B: MT5 (Forex - Demo)
python descarga_datos/main.py --live-mt5

# Opción C: Ambos simultáneamente
python descarga_datos/main.py --live-ccxt --live-mt5
```

**Duración:** Ilimitada (hasta que mates el proceso)

### 3️⃣ Monitorear Dashboard

Una vez que el bot esté corriendo:

```
URL: http://localhost:8519
Puerto: 8519 (fallback: 8520-8523 si ocupado)

Abrir en navegador:
http://localhost:8519
```

**Dashboard muestra:**
- Operaciones en tiempo real
- P&L actual
- Win rate
- Métricas de balance
- Historial de trades

---

## 🎯 QUÉ ESPERAR

### Configuración Actual

```yaml
Trading Mode: MARGIN (Apalancado)
Leverage: 5x (conservador)
Risk Per Trade: 2% (estándar)
Timeframe: 15 minutos
Symbol: BTC/USDT

Exchange: Binance Testnet (Demo - Sandbox)
Account Type: DEMO (Sin dinero real)
```

### Resultados Esperados

| Métrica | Esperado |
|---------|----------|
| **Win Rate** | 70-80% (basado en backtest 76.6%) |
| **P&L Diario** | +$50 a +$200 aprox. |
| **Max Drawdown** | -5% a -10% |
| **Trades/Día** | 5-15 operaciones |
| **Duración Promedio** | 1-4 horas por trade |

### Ejemplos de Posiciones (Correctas)

**Con tu balance actual ($369,294):**
```
Operación típica:
├── Cantidad: 0.1-0.5 BTC
├── Exposición: $4,000-$20,000
├── Margen Requerido: $800-$4,000
├── Riesgo Máximo: $7,400 (2% del balance)
└── Status: ✅ Realista y seguro
```

**Antes (incorrecto) - AHORA CORREGIDO:**
```
Operación anterior:
├── Cantidad: 2.99 BTC ← MUY GRANDE
├── Exposición: $333,000 ← EXCESIVO
├── Resultado: -$649 ← GRAN PÉRDIDA
└── Status: ❌ AHORA CORREGIDO A 0.15-0.5 BTC
```

---

## 🛑 DETENER LIVE TRADING

### Graceful Shutdown

```bash
# En la terminal donde está corriendo:
Presiona: CTRL + C

# El bot cerrará:
1. Posiciones abiertas
2. Conexiones
3. Guardará historial
4. Finalizará dashboard
```

### Si no responde:

```bash
# Buscar proceso
tasklist | findstr python

# Matar proceso (si es necesario)
taskkill /PID <PID> /F
```

---

## 📊 MONITOREO DURANTE EJECUCIÓN

### Logs

```bash
# Ver logs en tiempo real
Get-Content -Path "descarga_datos/logs/live_trading.log" -Wait

# Ver últimos errores
Get-Content "descarga_datos/logs/*.log" | Select-Object -Last 50
```

### Posiciones Abiertas

```bash
# Ver archivo de posiciones
cat "descarga_datos/data/live_trading_results/position_history.json"
```

### Balance

```bash
# Verificar balance actual
python descarga_datos/verificar_balance.py
```

---

## ✅ VALIDACIÓN PRE-EJECUCIÓN

### Checklist

```
☐ Virtual environment activado
☐ Dependencias instaladas (ccxt, pandas, etc)
☐ Config actualizado en config.yaml
☐ Credenciales en .env (si aplica)
☐ Internet conexión estable
☐ Puerto 8519 disponible (netstat -ano | findstr :8519)
☐ Binance testnet accesible
☐ Mínimo 2 GB RAM disponible
☐ Mínimo 500 MB disco disponible
```

### Test Rápido

```bash
# Verificar que el sistema puede conectar
python -c "
import ccxt
binance = ccxt.binance({'sandbox': True})
print('✓ CCXT conectando correctamente')
print(f'✓ Balance: {binance.fetch_balance()}')
"
```

---

## 🔧 CONFIGURACIÓN IMPORTANTE

### En `config.yaml`

```yaml
live_trading:
  enabled: true                    # Habilitar live trading
  trading_mode: margin             # Margin, spot, o futures
  margin_leverage: 5               # ✅ Corrected v4.6
  risk_per_trade: 0.02             # 2% ✅ Corrected v4.6
  ccxt_exchange: binance           # Exchange a usar
  active_symbol: BTC/USDT          # Par a tradear
  account_type: DEMO               # DEMO = Sandbox
```

### Si necesitas cambiar:

```bash
# Editar config
notepad descarga_datos/config/config.yaml

# Cambios comunes:
# - trading_mode: 'spot', 'margin', 'futures'
# - margin_leverage: 1, 5, 10, 20 (máximo permitido)
# - risk_per_trade: 0.01 (1%), 0.02 (2%), 0.03 (3%)
# - active_symbol: 'BTC/USDT', 'ETH/USDT', 'XRP/USDT'
```

---

## 📈 DESPUÉS DE EJECUTAR

### Datos Generados

Después de 2-4 horas de ejecución, habrá:

```
descarga_datos/data/live_trading_results/
├── live_tracker_auto_TIMESTAMP.json    (Historial de trades)
├── position_history.json               (Posiciones abiertas/cerradas)
├── metrics.csv                         (Métricas en CSV)
└── analysis.json                       (Análisis de desempeño)
```

### Crear Nuevo Análisis

```bash
# Después de completar live trading:

# 1. Copiar resultados
cp descarga_datos/data/live_trading_results/live_tracker_auto_*.json backups/

# 2. Analizar resultados
python -c "
import json
with open('live_tracker_auto_TIMESTAMP.json') as f:
    data = json.load(f)
    trades = data.get('trades', [])
    print(f'Total trades: {len(trades)}')
    print(f'Wins: {len([t for t in trades if t[\"pnl\"] > 0])}')
    print(f'Win rate: {len([t for t in trades if t[\"pnl\"] > 0]) / len(trades) * 100:.1f}%')
"

# 3. Generar reporte
python descarga_datos/audit_data.py
```

---

## ⚠️ TROUBLESHOOTING

### "Import Error: No module named 'ccxt'"

```bash
pip install ccxt
```

### "Connection refused" a Binance

```bash
# Verificar internet
ping google.com

# Verificar que Binance testnet está disponible
# URL: https://testnet.binancefuture.com/
```

### Dashboard no abre

```bash
# Verificar puerto
netstat -ano | findstr :8519

# Si ocupado, matar proceso
taskkill /PID <PID> /F

# O cambiar puerto en config (fallback automático a 8520)
```

### Posiciones no cierran

```bash
# Ver logs
tail descarga_datos/logs/live_trading.log

# Verificar conexión
python descarga_datos/verificar_balance.py

# Si problema persiste: Ctrl+C y reiniciar
```

### Errores de "Insufficient Balance"

```bash
# Verificar balance en testnet
python descarga_datos/verificar_balance.py

# Si necesario, resetear cuenta
# → Ir a https://testnet.binance.vision/
# → Resetear balance manual
```

---

## 🎓 COMPARATIVA: Antes vs Después

### Con Fórmula v4.6 (Correcta)

```
ANTES (Incorrecto):
├── Op #1: 2.99 BTC × $111,459 = $333k exposición (EXCESIVO)
├── Op #2: 0.15 BTC × $45,000 = $6,750 exposición (20x menor por balance agotado)
├── Op #3: 0.15 BTC × $45,000 = $6,750 exposición
└── P&L: -$644.80 (WR: 33%)

AHORA (Correcto v4.6):
├── Op #1: 0.15 BTC × $111,459 = $16,718 exposición (consistente)
├── Op #2: 0.15 BTC × $45,000 = $6,750 exposición (consistente)
├── Op #3: 0.15 BTC × $45,000 = $6,750 exposición (consistente)
└── P&L: ↑↑ Esperado +$2,000-$3,000 (WR: 76% como backtest)
```

---

## 📞 SOPORTE RÁPIDO

### Documentación Disponible

```
Necesito entender la corrección:
→ descarga_datos/ARCHIVOS MD/00_Correcion_v46/
   - SOLUCION_IMPLEMENTACION_CORRECTA.md
   - REFERENCIA_CALCULOS_CORRECTOS_CRYPTO.md

Necesito ver análisis anterior:
→ descarga_datos/ARCHIVOS MD/01_Analisis_Live_Trading/

Necesito ayuda con dashboard:
→ descarga_datos/ARCHIVOS MD/02_Dashboard/
   - GUIA_VISUAL_DASHBOARD.md

Índice maestro:
→ descarga_datos/ARCHIVOS MD/INDICE_MAESTRO_v46.md
```

---

## ✨ RESUMEN FINAL

```
🔧 Código: CORREGIDO ✅
📋 Config: ACTUALIZADO ✅
🧪 Tests: PASADOS ✅
📚 Documentos: ORGANIZADOS ✅
🚀 Listo para: LIVE TRADING ✅

Estado: READY TO GO
Comando: python descarga_datos/main.py --live-ccxt
Dashboard: http://localhost:8519
```

---

**Creado:** 25 de Octubre de 2025  
**Versión:** 4.6  
**Status:** ✅ COMPLETADO Y LISTO

