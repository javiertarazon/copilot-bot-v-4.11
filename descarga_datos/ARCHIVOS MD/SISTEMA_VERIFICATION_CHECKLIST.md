# ✅ VERIFICACIÓN DEL SISTEMA - PRE-SANDBOX
## Checklist completo antes de ejecutar en vivo

**Documento:** SISTEMA_VERIFICATION_CHECKLIST.md  
**Versión:** 1.0  
**Fecha:** 26/10/2025  
**Estado:** Ready for Use

---

## 🔍 SECCIÓN 1: CONFIGURACIÓN (5 min)

### 1.1 Config.yaml existe y es correcto
```bash
# Terminal: Verificar archivo existe
cat descarga_datos/config/config.yaml | head -20

# Debe mostrar:
✅ exchanges:
✅ binance:
✅ sandbox: true/false (dependiendo de qué quieras)
✅ apiKey: ${BINANCE_API_KEY}
✅ secret: ${BINANCE_API_SECRET}
✅ enableRateLimit: true
✅ trading:
✅ position_size: 0.01
```

### 1.2 Variables de entorno (.env) configuradas
```bash
# Terminal: Verificar .env existe
ls -la descarga_datos/.env

# Debe mostrar:
✅ BINANCE_API_KEY=xxx
✅ BINANCE_API_SECRET=yyy
✅ BINANCE_SANDBOX=true (si es testnet)
```

### 1.3 Credenciales correctas
```bash
# Terminal: Test API connection
python -c "
import os
from dotenv import load_dotenv
load_dotenv('descarga_datos/.env')
api_key = os.getenv('BINANCE_API_KEY')
print(f'✅ API Key loaded: {api_key[:10]}...' if api_key else '❌ API Key missing')
"

# Debe mostrar:
✅ API Key loaded: xxx...
```

### 1.4 Python version correcto
```bash
# Terminal: Check Python version
python --version

# Debe ser:
✅ Python 3.9+ (recomendado 3.11+)
❌ Python 2.x (NO soportado)
```

### 1.5 Dependencias instaladas
```bash
# Terminal: Check installed packages
pip list | grep -E "ccxt|pandas|numpy"

# Debe mostrar:
✅ ccxt 4.5.12+ 
✅ pandas 1.5.0+
✅ numpy 1.20.0+
✅ python-dotenv
```

**Si faltan:** 
```bash
pip install -r requirements.txt
```

---

## 📡 SECCIÓN 2: CONEXIÓN CON EXCHANGE (10 min)

### 2.1 Test CCXT connection
```bash
# Terminal: Test basic connection
python -c "
import ccxt
from dotenv import load_dotenv
import os

load_dotenv('descarga_datos/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'sandbox': True,
    'enableRateLimit': True
})

try:
    balance = exchange.fetch_balance()
    print('✅ CCXT Connection: OK')
    print(f'✅ Total Balance: {balance[\"total\"].get(\"USDT\", 0):.2f} USDT')
except Exception as e:
    print(f'❌ Connection Error: {e}')
"

# Debe mostrar:
✅ CCXT Connection: OK
✅ Total Balance: XXX.XX USDT
```

### 2.2 Test tickers fetching
```bash
# Terminal: Test fetch ticker
python -c "
import ccxt
from dotenv import load_dotenv
import os

load_dotenv('descarga_datos/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'sandbox': True,
    'enableRateLimit': True
})

try:
    ticker = exchange.fetch_ticker('BTC/USDT')
    print('✅ Ticker Fetch: OK')
    print(f'✅ BTC Price: {ticker[\"last\"]:.2f} USDT')
    print(f'✅ Bid: {ticker[\"bid\"]:.2f} / Ask: {ticker[\"ask\"]:.2f}')
except Exception as e:
    print(f'❌ Ticker Error: {e}')
"

# Debe mostrar:
✅ Ticker Fetch: OK
✅ BTC Price: XXXXX.XX USDT
✅ Bid: XXX.XX / Ask: YYY.YY
```

### 2.3 Test OHLCV data
```bash
# Terminal: Test fetch OHLCV
python -c "
import ccxt
from dotenv import load_dotenv
import os

load_dotenv('descarga_datos/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'sandbox': True,
    'enableRateLimit': True
})

try:
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=10)
    print('✅ OHLCV Fetch: OK')
    print(f'✅ Candles fetched: {len(ohlcv)}')
    print(f'✅ First candle: Open={ohlcv[0][1]:.2f}, High={ohlcv[0][2]:.2f}')
except Exception as e:
    print(f'❌ OHLCV Error: {e}')
"

# Debe mostrar:
✅ OHLCV Fetch: OK
✅ Candles fetched: 10
✅ First candle: Open=XXXXX.XX, High=XXXXX.XX
```

### 2.4 Test order creation (on testnet)
```bash
# Terminal: Test create order (limit order, no execution)
python -c "
import ccxt
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv('descarga_datos/.env')

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'sandbox': True,  # CRÍTICO: testnet
    'enableRateLimit': True
})

try:
    # Crear orden a precio muy bajo (no se ejecutará)
    order = exchange.create_order(
        'BTC/USDT',
        'limit',
        'buy',
        0.001,  # 0.001 BTC
        1.0,    # Precio $1 (será rechazada pero eso está ok)
        {'clientOrderId': f'test_{datetime.now().timestamp()}'}
    )
    print('✅ Order Creation: OK')
    print(f'✅ Order ID: {order[\"id\"]}')
    
    # Inmediatamente cancelar
    exchange.cancel_order(order['id'], 'BTC/USDT')
    print('✅ Order Cancellation: OK')
except Exception as e:
    print(f'❌ Order Error: {e}')
"

# Debe mostrar:
✅ Order Creation: OK
✅ Order ID: XXXXXXXXX
✅ Order Cancellation: OK
```

---

## 🗄️ SECCIÓN 3: BASE DE DATOS (5 min)

### 3.1 Database exists and is readable
```bash
# Terminal: Check database
ls -lh descarga_datos/data/*.db

# Debe mostrar:
✅ database.db (o similar) - tamaño > 0

# Si NO existe:
# ❌ El bot lo creará automáticamente en primera ejecución
```

### 3.2 Database tables
```bash
# Terminal: Check tables
python -c "
import sqlite3
from pathlib import Path

db_path = Path('descarga_datos/data/database.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = cursor.fetchall()
    print(f'✅ Database found: {len(tables)} tables')
    for table in tables:
        print(f'   - {table[0]}')
    conn.close()
else:
    print('⚠️  Database not created yet (normal, se creará en primera ejecución)')
"

# Debe mostrar:
✅ Database found: X tables
   - trades (o similar)
   - positions (o similar)
   - etc.
```

---

## 📊 SECCIÓN 4: BACKTESTING VALIDATION (5 min)

### 4.1 Run quick backtest test
```bash
# Terminal: Run smoke test
python -m pytest descarga_datos/tests/test_quick_backtest.py -v

# Debe mostrar:
✅ test_backtester.py::test_something PASSED
✅ ... (varios tests)
✅ ======= X passed in Y.XXs =======

# Si FALLA:
❌ Ver error en output
❌ Debug antes de continuar
```

### 4.2 Backtesting results
```bash
# Terminal: Check backtest results
ls -lh descarga_datos/data/dashboard_results/

# Debe mostrar:
✅ backtest_YYYYMMDD_HHmmss.json (o similar)
✅ Último archivo tiene tamaño > 1KB
```

### 4.3 Last backtest metrics
```bash
# Terminal: View last backtest P&L
python -c "
import json
from pathlib import Path

results_dir = Path('descarga_datos/data/dashboard_results')
if results_dir.exists():
    files = sorted(results_dir.glob('*.json'))
    if files:
        with open(files[-1]) as f:
            data = json.load(f)
        metrics = data.get('metrics', {})
        print(f'✅ Last Backtest:')
        print(f'   P&L: {metrics.get(\"total_pnl\", \"N/A\")}')
        print(f'   Trades: {metrics.get(\"total_trades\", \"N/A\")}')
        print(f'   Win Rate: {metrics.get(\"win_rate\", \"N/A\")}')
    else:
        print('⚠️  No backtest results yet')
else:
    print('⚠️  Results directory not found')
"

# Debe mostrar:
✅ Last Backtest:
   P&L: \$XXXXX.XX
   Trades: XXXX
   Win Rate: XX.X%
```

---

## 📈 SECCIÓN 5: DASHBOARD (5 min)

### 5.1 Dashboard file exists
```bash
# Terminal: Check dashboard file
ls -l descarga_datos/data/dashboard.html

# Debe mostrar:
✅ dashboard.html - tamaño > 50KB

# Si NO existe:
# ❌ Será generado por el bot automáticamente
```

### 5.2 Open dashboard in browser
```
Abrir en navegador:
http://localhost:8888/dashboard.html

Debe mostrar:
✅ Página HTML con gráficos
✅ Secciones: Overview, Trades, Statistics, etc
✅ Botones de control (si aplica)

Si da error:
❌ Bot aún no está corriendo
❌ O el puerto 8888 está ocupado
```

### 5.3 Check dashboard port availability
```bash
# Terminal: Check port 8888
python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 8888))
if result == 0:
    print('⚠️  Port 8888 already in use (bot running?)')
else:
    print('✅ Port 8888 available')
sock.close()
"

# Debe mostrar:
✅ Port 8888 available

# Si dice "in use":
# ⚠️  Otro proceso usa el puerto
# Solución: Kill process o usar puerto diferente en config
```

---

## 🔐 SECCIÓN 6: SEGURIDAD (5 min)

### 6.1 .env file permissions
```bash
# Terminal: Check .env not readable by others
ls -l descarga_datos/.env

# Debe mostrar:
✅ -rw------- (solo owner puede leer)

# Si dice -rw-r--r--:
❌ Archivo demasiado público
❌ Solución: chmod 600 descarga_datos/.env
```

### 6.2 Credenciales not in config.yaml
```bash
# Terminal: Check config.yaml no tiene credenciales
grep -E "apiKey|secret|password" descarga_datos/config/config.yaml | head -3

# Debe mostrar:
✅ apiKey: ${BINANCE_API_KEY}  (variables, NO valores reales)
✅ secret: ${BINANCE_API_SECRET}

# Si muestra valores reales:
❌ PROBLEMA CRÍTICO
❌ Credenciales expuestas en config
❌ Solución: Mover a .env inmediatamente
```

### 6.3 API key permissions (Binance)
```
Verificar en Binance API Management:
✅ Spot Trading: Enabled
✅ Margin Trading: Disabled (a menos que uses margin)
✅ Futures Trading: Enabled (si vas a usar futures)
✅ Withdrawing: DISABLED (CRÍTICO)
✅ IP Whitelist: Enabled con tu IP

Haz click "Enable Restrictions" en Binance
```

### 6.4 Git ignores credentials
```bash
# Terminal: Check .gitignore
cat .gitignore | grep -E "\.env|\.env\.*|secrets"

# Debe mostrar:
✅ .env (o .env.*)
✅ Archivos de credenciales ignorados

# Si NO está:
# ❌ Solución: Agregar a .gitignore ANTES de commit
```

---

## 🚀 SECCIÓN 7: READY FOR SANDBOX (2 min)

### 7.1 Final checklist
```
ANTES DE EJECUTAR SANDBOX:

Core Setup:
  [✅] config.yaml existe y es correcto
  [✅] .env configurado con credenciales
  [✅] Python 3.9+ instalado
  [✅] Dependencias instaladas (pip list)
  
Connection Tests:
  [✅] CCXT connection OK
  [✅] Ticker fetching OK
  [✅] OHLCV data OK
  [✅] Order creation (testnet) OK
  
Data & Testing:
  [✅] Database accessible (o será creado)
  [✅] Backtest tests passan
  [✅] Dashboard file accessible
  
Security:
  [✅] .env permisos restringidos
  [✅] No credenciales en config.yaml
  [✅] API key permisos correctos
  [✅] .gitignore incluye .env

Port Availability:
  [✅] Puerto 8888 available (dashboard)
  
If everything checked:
  ✅ LISTO PARA EJECUTAR SANDBOX
```

### 7.2 Start sandbox
```bash
# Terminal: Ejecutar bot en sandbox
cd descarga_datos
python main.py --live

# Debe mostrar:
✅ Bot starting...
✅ Loading config...
✅ Connecting to exchange...
✅ Starting dashboard at http://localhost:8888
✅ Ready for live trading (sandbox mode)

# Logs location:
descarga_datos/logs/trading.log
```

### 7.3 Monitor first execution
```bash
# Terminal 2: Watch logs
tail -f descarga_datos/logs/trading.log

# Debe mostrar:
✅ 2025-10-26 10:30:00 - Bot started
✅ 2025-10-26 10:30:01 - Connecting to Binance sandbox
✅ 2025-10-26 10:30:02 - Loaded markets
✅ 2025-10-26 10:30:03 - Dashboard started

# Si hay ERROR:
❌ Revisar error message
❌ Usar CCXT_BEST_PRACTICES_LIVE_TRADING.md para debugging
❌ No continuar hasta que arranque limpio
```

---

## 🎯 TROUBLESHOOTING RÁPIDO

### Bot no arranca
```
1. Verificar config.yaml syntax:
   python -c "import yaml; yaml.safe_load(open('descarga_datos/config/config.yaml'))"
   
2. Verificar credenciales en .env:
   cat descarga_datos/.env | head -3
   
3. Verificar CCXT connection:
   python -c "import ccxt; print(ccxt.binance())"
```

### Error "ModuleNotFoundError"
```
Solución: Instalar dependencias
  pip install -r requirements.txt
  
O en virtual env:
  source venv/bin/activate  (Linux/Mac)
  venv\Scripts\activate     (Windows)
  pip install -r requirements.txt
```

### Error "Invalid API Key"
```
1. Verificar credenciales en .env están correctas
2. Verificar no hay espacios extras
3. Generar nuevas API keys en Binance
4. Actualizar .env
5. Reintentar
```

### Port 8888 already in use
```
Opción 1: Matar proceso anterior
  pkill -f "python main.py"  (Linux/Mac)
  taskkill /F /IM python.exe  (Windows)
  
Opción 2: Usar puerto diferente
  En config.yaml: dashboard_port: 8889
```

### Dashboard no actualiza
```
1. Verificar bot está corriendo
2. Abrir browser console (F12)
3. Ver si hay errores JavaScript
4. Forzar refresh: Ctrl+Shift+R
5. Reiniciar bot si persiste
```

---

## ✅ DECISIÓN FINAL

Si pasaste TODAS las verificaciones anteriores:

```
✅ SISTEMA VERIFICADO - LISTO PARA SANDBOX

Ejecutar:
  cd descarga_datos
  python main.py --live
  
Monitorear:
  - Dashboard: http://localhost:8888/dashboard.html
  - Logs: tail -f logs/trading.log
  
Duración:
  - 24-48 horas mínimo
  
Go/No-Go Decision:
  - Si TODO OK: Proceder a producción
  - Si hay issues: Debug + retest
```

Si hay CUALQUIER error:
```
❌ NO PROCEDER A PRODUCCIÓN

Pasos:
1. Anotar error exacto
2. Buscar en CCXT_BEST_PRACTICES_LIVE_TRADING.md
3. Implementar fix
4. Retest con esta checklist
5. Cuando esté OK: lanzar sandbox
```

---

**Document:** SISTEMA_VERIFICATION_CHECKLIST.md  
**Version:** 1.0  
**Date:** 26/10/2025  
**Status:** ✅ Ready to Use

**Run this BEFORE executing:** `python descarga_datos/main.py --live`

---

## 📊 QUICK VERIFICATION SCRIPT

Si prefieres automatizado:

```bash
# Guardar como: verify_system.py
#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import ccxt

print("🔍 VERIFICANDO SISTEMA...\n")

checks = {
    "config.yaml existe": Path("descarga_datos/config/config.yaml").exists(),
    ".env existe": Path("descarga_datos/.env").exists(),
    "Python 3.9+": sys.version_info >= (3, 9),
}

try:
    import ccxt
    checks["ccxt instalado"] = True
except:
    checks["ccxt instalado"] = False

try:
    load_dotenv("descarga_datos/.env")
    api_key = os.getenv("BINANCE_API_KEY")
    checks["BINANCE_API_KEY en .env"] = bool(api_key)
except:
    checks["BINANCE_API_KEY en .env"] = False

# Mostrar resultados
passed = sum(1 for v in checks.values() if v)
total = len(checks)

for check, result in checks.items():
    icon = "✅" if result else "❌"
    print(f"{icon} {check}")

print(f"\n✅ Pasaron: {passed}/{total} checks")

if passed == total:
    print("\n🚀 SISTEMA LISTO PARA SANDBOX")
    sys.exit(0)
else:
    print("\n❌ PROBLEMAS DETECTADOS - Ver arriba")
    sys.exit(1)
```

Ejecutar:
```bash
python verify_system.py
```
