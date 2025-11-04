# 🧪 Guía de Tests de Deriv MT5

## 📋 Información de Credenciales Requeridas

Para ejecutar los tests completos de Deriv, necesitas tener:

### 1️⃣ Cuenta Demo de Deriv MT5

**Cómo obtenerla (GRATIS):**

1. **Ir a**: https://deriv.com
2. **Registrarse** (email + password)
3. **Ir a Dashboard** → Menú lateral → "Trading"
4. **Seleccionar "Deriv MT5"** → "Demo Account"
5. **Obtener credenciales**:
   - **Login**: Número de cuenta (ej: 12345678)
   - **Password**: Password de MT5 (diferente al de Deriv web)
   - **Servidor**: `Deriv-Demo`

### 2️⃣ Información de la Cuenta Demo

- **Balance inicial**: $10,000 USD
- **Moneda**: USD
- **Apalancamiento**: 1:500 (configurable)
- **Duración**: ✅ ILIMITADA (no expira)
- **Recarga**: ✅ Recargable en cualquier momento
- **Trading**: ✅ 24/7 real (sin interrupciones)

---

## 🚀 Ejecución de Tests

### Opción 1: Modo Interactivo (Recomendado)

```bash
# Activar entorno virtual
.\.venv\Scripts\activate

# Ejecutar test completo
cd descarga_datos
python tests\test_deriv_complete.py
```

**El script te pedirá:**
- Login (número de cuenta)
- Password
- Servidor (default: Deriv-Demo)

### Opción 2: Variables de Entorno

```powershell
# Configurar credenciales
$env:DERIV_LOGIN = "12345678"
$env:DERIV_PASSWORD = "tu_password"
$env:DERIV_SERVER = "Deriv-Demo"

# Ejecutar test
python tests\test_deriv_complete.py
```

### Opción 3: Archivo de Configuración

Crear archivo `descarga_datos\.env.deriv`:

```env
DERIV_LOGIN=12345678
DERIV_PASSWORD=tu_password
DERIV_SERVER=Deriv-Demo
```

Ejecutar:

```bash
python tests\test_deriv_complete.py --use-env
```

---

## 📊 Tests Incluidos

El script ejecuta 9 tests completos:

| # | Test | Descripción | Duración |
|---|------|-------------|----------|
| 1 | **Conectividad** | Verifica conexión a Deriv MT5 | 5s |
| 2 | **Símbolos** | Verifica disponibilidad de Volatility Indices | 10s |
| 3 | **Datos Históricos** | Descarga 30 días de datos (15m timeframe) | 15s |
| 4 | **Datos en Vivo** | Stream de datos en tiempo real | 20s |
| 5 | **Apertura BUY** | Abre posición de compra con SL/TP | 5s |
| 6 | **Modificar SL/TP** | Modifica stop loss y take profit | 5s |
| 7 | **Trailing Stop** | Implementa trailing stop dinámico | 30s |
| 8 | **Cierre Posición** | Cierra la posición de prueba | 5s |
| 9 | **Balance Final** | Verifica balance y P&L | 5s |

**Duración total**: ~2 minutos

---

## ✅ Resultados Esperados

### Test Exitoso

```
📊 RESUMEN DE TESTS
======================================================================
   ✅ connectivity: PASSED
   ✅ symbol_availability: PASSED
   ✅ historical_data_Volatility 75 Index: PASSED
   ✅ live_data_Volatility 75 Index: PASSED
   ✅ open_buy_Volatility 75 Index: PASSED
   ✅ modify_sltp_12345678: PASSED
   ✅ trailing_stop_12345678: PASSED
   ✅ close_position_12345678: PASSED
   ✅ final_balance: PASSED

📈 RESULTADO FINAL:
   Total tests: 9
   Exitosos: 9
   Fallidos: 0
   Tasa de éxito: 100.0%

🎉 ¡TODOS LOS TESTS PASARON! Sistema listo para operar.
```

### Archivos Generados

Después de ejecutar los tests, encontrarás:

```
descarga_datos/data/deriv_tests/
├── test_results_20251101_143025.txt         # Log completo
├── Volatility_75_Index_15m.csv              # Datos históricos
├── Volatility_100_Index_15m.csv
└── Volatility_50_Index_15m.csv
```

---

## 🔧 Configuración de Tests

Puedes modificar parámetros en `test_deriv_complete.py`:

```python
TEST_CONFIG = {
    "timeframe": "15m",           # Cambiar a: 1m, 5m, 15m, 1h, 4h, 1d
    "days_back": 30,              # Cambiar días de historia
    "test_volume": 0.01,          # Volumen de prueba (0.01 - 10 lotes)
    "test_sl_points": 500,        # Stop Loss en puntos
    "test_tp_points": 1000,       # Take Profit en puntos
    "trailing_stop_points": 300,  # Trailing stop en puntos
    "max_test_duration": 60,      # Duración streaming
}
```

---

## 🔍 Símbolos Disponibles

El script prueba automáticamente estos símbolos:

| Símbolo | Volatilidad | Recomendado | Uso |
|---------|-------------|-------------|-----|
| **Volatility 75 Index** | 7.5% | ⭐⭐⭐ | Principal - Similar a BTC |
| **Volatility 100 Index** | 10% | ⭐⭐ | Alta volatilidad - Altcoins |
| **Volatility 50 Index** | 5% | ⭐ | Conservador - Similar SOL |

---

## ❌ Solución de Problemas

### Error: "Login/Password incorrectos"

**Solución:**
1. Verifica credenciales en https://deriv.com
2. Usa el password de **MT5**, no el de Deriv web
3. Si olvidaste el password: Dashboard → MT5 → "Reset Password"

### Error: "Símbolo no disponible"

**Solución:**
1. Abrir MT5 desktop app
2. Market Watch → Click derecho → "Show All"
3. Buscar "Volatility" y añadir símbolos
4. Reintentar test

### Error: "Insufficient margin"

**Solución:**
- Recargar balance demo: Dashboard → MT5 → "Top Up"
- Reducir volumen en `TEST_CONFIG["test_volume"]`

### Error: "Trade not allowed"

**Solución:**
1. Verificar que la cuenta sea **DEMO** (no real)
2. Verificar conexión a internet
3. Reiniciar MT5 si está abierto

---

## 📱 Instalación de MT5 (Opcional)

Para visualizar operaciones en tiempo real:

1. **Descargar MT5**: https://deriv.com/dmt5
2. **Instalar** en Windows/Mac/Linux
3. **Login** con credenciales demo
4. **Ver gráficos** de Volatility Indices

⚠️ **Nota**: No es necesario tener MT5 abierto para que los tests funcionen.

---

## 🔐 Seguridad

- ✅ Usa siempre cuenta **DEMO** para tests
- ✅ Nunca uses cuenta **REAL** para pruebas automatizadas
- ✅ No compartas credenciales en código público
- ✅ Usa variables de entorno o archivos `.env`

---

## 📞 Soporte

Si los tests fallan:

1. **Verificar logs** en `descarga_datos/data/deriv_tests/test_results_*.txt`
2. **Revisar sección** de solución de problemas arriba
3. **Contactar soporte Deriv**: https://deriv.com/contact

---

## 🎯 Próximos Pasos

Una vez que los tests pasen exitosamente:

1. ✅ **Backtest con datos reales**:
   ```bash
   python main.py --backtest
   ```

2. ✅ **Optimización de parámetros**:
   ```bash
   python main.py --optimize
   ```

3. ✅ **Live trading en demo**:
   ```bash
   python main.py --live
   ```

---

**Última actualización**: 1 Noviembre 2025
**Versión**: 1.0
**Autor**: GitHub Copilot
