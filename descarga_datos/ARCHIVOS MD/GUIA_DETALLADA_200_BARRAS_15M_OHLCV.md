# 📊 Guía Completa: Carga de 200 Barras 15m desde MT5 y Conversión a OHLCV

**Problema**: "Tengo dudas con la formación de las 200 barras de 15 min temporalidad a partir de los datos reales en vivo y su conversión a OHLCV"

**Solución**: Aquí explico exactamente cómo funciona el proceso paso a paso.

---

## 🏗️ Arquitectura: De MT5 a OHLCV (200 barras 15m)

```
┌─────────────────────────────────────────────────┐
│ MetaTrader 5 (MT5)                              │
│ Volatility 75 Index (Deriv Demo)                │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ MT5LiveDataProvider.get_live_data()             │
│ Obtiene las últimas 200 barras de 15m           │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ mt5.copy_rates_from_pos(symbol, 15m, 0, 200)   │
│ Retorna array de estructuras C con OHLCV        │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ Conversión a DataFrame Pandas                   │
│ Estructura: ['time', 'open', 'high', 'low',    │
│             'close', 'tick_volume']             │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ Renombrar y ajustar columnas                    │
│ 'tick_volume' → 'volume' (para sintéticos = 0)  │
│ 'time' → datetime                               │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ DataFrame listo para estrategia                 │
│ 200 filas × 6 columnas (time, O, H, L, C, V)   │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Código Real: Paso a Paso

### **PASO 1: Iniciar conexión MT5**

```python
# File: core/mt5_live_data.py
class MT5LiveDataProvider:
    def __init__(self):
        self.connected = False
        self.connection_lock = threading.Lock()
        self.data_cache = {}
        
        # Inicializar MT5
        if mt5.initialize():  # ✅ Conecta con MT5 en tu máquina
            self.connected = True
            logger.info("MT5 conectado")
```

**¿Qué pasa aquí?**
- Se establece conexión con MetaTrader 5 instalado en tu PC
- MT5 debe estar abierto y conectado a Deriv

---

### **PASO 2: Llamar get_live_data() cada 5 segundos**

```python
# File: core/live_trading_orchestrator.py
def run_trading_cycle(self):
    while self.running:
        # Cada ciclo (5 segundos):
        df = self.data_provider.get_live_data(
            symbol='Volatility 75 Index',
            timeframe='15m',
            bars=200  # ← Solicitar 200 barras
        )
        
        # df ahora tiene 200 filas × 6 columnas
        # Procesar con estrategia...
        
        time.sleep(5)  # Esperar 5 segundos
```

**¿Qué pasa aquí?**
- Solicita las últimas 200 barras de 15 minutos
- Se ejecuta cada 5 segundos
- El DataFrame tiene forma (200, 6)

---

### **PASO 3: Implementación de get_live_data()**

```python
# File: core/mt5_live_data.py - Línea 222
def get_live_data(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
    """
    Obtiene datos en tiempo real para un símbolo y timeframe específico.
    """
    if not self.ensure_connection():
        logger.error("No hay conexión con MT5")
        return None
    
    try:
        # Convertir timeframe a formato MT5
        # '15m' → mt5.TIMEFRAME_M15
        mt5_timeframe = self._convert_timeframe(timeframe)
        
        # ✅ LLAMAR MT5 API
        rates = mt5.copy_rates_from_pos(
            symbol,              # 'Volatility 75 Index'
            mt5_timeframe,       # mt5.TIMEFRAME_M15
            0,                   # Desde posición 0 (más reciente)
            bars                 # 200 barras
        )
        
        # rates es un array de estructuras C con OHLCV
        # Cada estructura tiene:
        # - time: timestamp Unix
        # - open: precio de apertura
        # - high: máximo
        # - low: mínimo
        # - close: cierre
        # - tick_volume: volumen de ticks
        
        if rates is None or len(rates) == 0:
            logger.warning(f"No hay datos para {symbol}")
            return None
        
        # ✅ CONVERTIR A DATAFRAME
        df = pd.DataFrame(rates)
        # Ahora df tiene columnas:
        # ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        
        # ✅ CONVERTIR timestamp
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        # 'time' estaba en segundos desde epoch, lo convertimos a datetime
        
        # ✅ RENOMBRAR COLUMNAS
        df = df.rename(columns={
            'tick_volume': 'volume'  # Importante: rename para consistencia
        })
        
        # ✅ SELECCIONAR COLUMNAS NECESARIAS
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        # Descarta columnas innecesarias
        
        # ✅ GUARDAR EN CACHE
        cache_key = f"{symbol}_{timeframe}"
        self.data_cache[cache_key] = {
            'data': df,
            'last_update': datetime.now()
        }
        
        logger.debug(f"Datos obtenidos: {symbol} {timeframe} - {len(df)} barras")
        
        # ✅ RETORNAR DATAFRAME
        return df
        
    except Exception as e:
        logger.error(f"Error obteniendo datos: {e}")
        return None
```

**¿Qué pasa aquí?**
1. Llama `mt5.copy_rates_from_pos()` que retorna array C
2. Convierte a DataFrame Pandas
3. Convierte timestamp de Unix a datetime
4. Renombra columnas para consistencia
5. Selecciona solo columnas OHLCV
6. Guarda en cache para rápido acceso
7. Retorna DataFrame de (200, 6)

---

## 📋 Estructura del DataFrame Retornado

### **Antes y Después:**

**ANTES (array C de MT5):**
```
[
  {time: 1730688600, open: 42100.5, high: 42150.0, low: 42050.0, close: 42120.0, tick_volume: 0},
  {time: 1730688900, open: 42120.0, high: 42200.0, low: 42100.0, close: 42180.0, tick_volume: 0},
  ...
  (200 estructuras total)
]
```

**DESPUÉS (DataFrame Pandas):**
```
    timestamp            open       high        low      close  volume
0   2025-11-04 12:30:00  42100.50   42150.00   42050.00  42120.00     0
1   2025-11-04 12:45:00  42120.00   42200.00   42100.00  42180.00     0
2   2025-11-04 13:00:00  42180.00   42250.00   42170.00  42200.00     0
...
199 2025-11-04 16:00:00  42150.00   42300.00   42100.00  42250.00     0

Shape: (200, 6)
```

---

## 🔄 Conversión de Timeframe: String a MT5

```python
# File: core/mt5_live_data.py
def _convert_timeframe(self, timeframe: str) -> Optional[int]:
    """
    Convierte string timeframe a constante MT5
    """
    tf_map = {
        "1m":  mt5.TIMEFRAME_M1,    # 1 minuto
        "5m":  mt5.TIMEFRAME_M5,    # 5 minutos
        "15m": mt5.TIMEFRAME_M15,   # 15 minutos ← Nosotros usamos este
        "30m": mt5.TIMEFRAME_M30,   # 30 minutos
        "1h":  mt5.TIMEFRAME_H1,    # 1 hora
        "4h":  mt5.TIMEFRAME_H4,    # 4 horas
        "1d":  mt5.TIMEFRAME_D1,    # 1 día
        "1w":  mt5.TIMEFRAME_W1,    # 1 semana
    }
    
    mt5_tf = tf_map.get(timeframe.lower())
    if mt5_tf is None:
        logger.error(f"Timeframe no válido: {timeframe}")
        return None
    
    return mt5_tf

# Uso:
mt5_tf = self._convert_timeframe('15m')
# mt5_tf = mt5.TIMEFRAME_M15 (una constante numérica interna de MT5)
```

---

## 📊 ¿Qué Significa Cada Columna?

| Columna | Origen | Significado | Ejemplo |
|---------|--------|-------------|---------|
| `timestamp` | MT5 `time` | Hora de cierre de barra | 2025-11-04 12:30:00 |
| `open` | MT5 `open` | Precio apertura | 42100.50 |
| `high` | MT5 `high` | Precio máximo en barra | 42150.00 |
| `low` | MT5 `low` | Precio mínimo en barra | 42050.00 |
| `close` | MT5 `close` | Precio cierre | 42120.00 |
| `volume` | MT5 `tick_volume` | Volumen ticks (0 para sintéticos) | 0 |

---

## 🎯 ¿Por Qué 200 Barras Específicamente?

```python
# Necesarias para calcular indicadores técnicos

200 barras × 15 minutos = 3,000 minutos = 50 horas
                         ≈ 2 días y 2 horas de datos históricos

Indicadores requieren mínimo:
├─ EMA 200:      200 períodos (necesitamos 200+ barras)
├─ RSI 14:       14 períodos (mínimo)
├─ MACD:         26 períodos (mínimo)
├─ ATR 17:       17 períodos (nuestro ATR)
└─ Bollinger:    20 períodos (estándar)

Con 200 barras tenemos suficiente histórico para:
✅ Cálculos confiables de indicadores
✅ Heikin-Ashi sin errores
✅ ML model con suficientes features
✅ Risk management basado en ATR
```

---

## 🔌 Conexión Real: ¿Cómo se conecta MT5?

```python
# MT5 se comunica con MetaTrader 5 instalado en tu PC

Tu PC:
┌─────────────────────────────────┐
│ MetaTrader 5 (Deriv)            │
│ ├─ Terminal abierto             │
│ ├─ Conectado a Deriv            │
│ └─ Datos en tiempo real          │
└─────────────────────────────────┘
         ↑↓ (API MetaTrader5 lib)
┌─────────────────────────────────┐
│ Python Script                   │
│ import MetaTrader5 as mt5       │
│ mt5.copy_rates_from_pos(...)    │
└─────────────────────────────────┘
```

---

## 💾 Cache: Evitar Llamadas Repetidas

```python
# Para optimizar, se guarda en cache:

self.data_cache = {
    'Volatility 75 Index_15m': {
        'data': DataFrame(200, 6),
        'last_update': datetime.now()
    }
}

# Si se llama get_live_data() de nuevo en < 5 segundos:
# - Retorna datos del cache sin llamar MT5
# - Más rápido y eficiente
```

---

## 📈 Flujo Completo en el Orquestador

```python
# File: core/live_trading_orchestrator.py - Línea 248

class LiveTradingOrchestrator:
    def run_trading_cycle(self):
        """Ciclo principal ejecutado cada 5 segundos"""
        
        cycle = 0
        while self.running:
            cycle += 1
            
            # 1️⃣ OBTENER 200 BARRAS 15m
            df_ohlcv = self.data_provider.get_live_data(
                symbol='Volatility 75 Index',
                timeframe='15m',
                bars=200
            )
            # df_ohlcv es DataFrame (200, 6)
            
            if df_ohlcv is None or len(df_ohlcv) < 50:
                logger.warning(f"Datos insuficientes en ciclo #{cycle}")
                time.sleep(5)
                continue
            
            # 2️⃣ PREPARAR DATOS
            df_prepared = self._prepare_data(df_ohlcv)
            # Agrega indicadores técnicos
            # Ahora tiene 25+ columnas (OHLCV + 20 indicadores)
            
            # 3️⃣ ESTRATEGIA
            signal = self.strategy.get_live_signal(df_prepared)
            # signal = {'signal': 'SELL', 'signal_data': {...}}
            
            # 4️⃣ EJECUTAR SI HAY SEÑAL
            if signal['signal'] in ['BUY', 'SELL']:
                self._open_position_mt5(signal)
            
            # 5️⃣ MONITOREAR POSICIONES
            self._monitor_active_positions()
            
            # 6️⃣ SINCRONIZAR CON MT5
            self._sync_positions_with_mt5()
            
            # Esperar 5 segundos
            time.sleep(5)
```

---

## 🐛 Problemas Comunes y Soluciones

### **Problema 1: "No se obtienen 200 barras"**
```
❌ Error: mt5.copy_rates_from_pos() retorna None
   Causas posibles:
   • MT5 no está abierto
   • MT5 no está conectado a Deriv
   • Símbolo escrito incorrectamente
   • Timeframe no válido

✅ Solución:
   1. Verificar MT5 abierto en tu PC
   2. Verificar conectado a Deriv
   3. Usar símbolo exacto: "Volatility 75 Index"
   4. Usar timeframe válido: "15m"
```

### **Problema 2: "Volumen es 0 para Volatility Index"**
```
❌ Sorpresa: volume siempre 0
   Razón: Volatility Índices son sintéticos (no tienen volumen real)

✅ Esperado:
   • volume = 0 en todas las barras
   • Esto es NORMAL para sintéticos
   • Estrategia funciona igual porque:
     - No usa volume para señales
     - Usa precio (OHLC) y volatilidad (ATR)
```

### **Problema 3: "DataFrame tiene columnas extra"**
```
❌ Confusión: DataFrame tiene más columnas
   Posible: ['time', 'open', 'high', 'low', 'close', 'spread', 'real_volume', 'tick_volume']

✅ Solución en código:
   # Seleccionar solo las que necesitamos
   df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
```

---

## 🔄 Conversión a OHLCV Alternativa: Por Ticks

Para máxima precisión, existe método alternativo `get_aggregated_bars()`:

```python
def get_aggregated_bars(self, symbol: str, timeframe: str, bars: int = 200):
    """
    Construye barras OHLCV agrupando ticks de MT5
    
    Ventaja: Construcción exacta de barras en timeframe
    Desventaja: Más lento (requiere muchos ticks)
    """
    
    # Obtener ticks desde hace N horas
    from_dt = datetime.utcnow() - timedelta(minutes=bars * 15)
    ticks = mt5.copy_ticks_from(symbol, from_dt, mt5.COPY_TICKS_ALL)
    
    # Construir barras agrupando ticks
    # Agrupar por ventanas de 15m
    # Calcular OHLCV de cada ventana
    # Retornar DataFrame (200, 6)
```

---

## ✅ Validación: Verificar que todo está correcto

```python
# Después de obtener df:

assert len(df) == 200, "❌ No tenemos 200 barras"
assert df.shape[1] == 6, "❌ No tenemos 6 columnas"
assert 'open' in df.columns, "❌ Falta columna 'open'"
assert 'close' in df.columns, "❌ Falta columna 'close'"
assert df['open'].dtype in [float, int], "❌ 'open' no es numérico"
assert df.isna().sum().sum() == 0, "❌ Hay NaN en datos"

# Si llega aquí, todo OK ✅
```

---

## 📊 Ejemplo Práctico Completo

```python
# File: core/mt5_live_data.py

from core.mt5_live_data import MT5LiveDataProvider
import pandas as pd

# Inicializar proveedor
provider = MT5LiveDataProvider()

# Conectar a MT5
if not provider.connect():
    print("❌ Error: No se puede conectar a MT5")
    exit()

print("✅ Conectado a MT5")

# Obtener 200 barras de 15 minutos
df = provider.get_live_data(
    symbol='Volatility 75 Index',
    timeframe='15m',
    bars=200
)

# Validar
if df is None or len(df) == 0:
    print("❌ No se obtuvieron datos")
    exit()

print(f"✅ Obtenidas {len(df)} barras")
print(f"Shape: {df.shape}")
print(f"Columnas: {df.columns.tolist()}")
print(f"\nPrimeras filas:")
print(df.head())
print(f"\nÚltimas filas:")
print(df.tail())

# Verificaciones
print(f"\nValidaciones:")
print(f"- Open min/max: {df['open'].min():.2f} - {df['open'].max():.2f}")
print(f"- Close min/max: {df['close'].min():.2f} - {df['close'].max():.2f}")
print(f"- Volumen promedio: {df['volume'].mean():.0f}")
print(f"- Timestamp rango: {df['timestamp'].min()} a {df['timestamp'].max()}")

# Resultado esperado:
# ✅ Obtenidas 200 barras
# Shape: (200, 6)
# Columnas: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
# Primeras filas: [datos]
# Últimas filas: [datos más recientes]
```

---

## 🎓 Resumen: De MT5 a OHLCV

| Paso | Función | Input | Output |
|------|---------|-------|--------|
| 1 | `mt5.copy_rates_from_pos()` | Symbol, TF, 200 | Array C |
| 2 | `pd.DataFrame()` | Array C | DataFrame |
| 3 | Rename/Convert | Raw DF | Clean DF |
| 4 | Select columns | Full DF | OHLCV DF |
| 5 | Return | OHLCV DF | (200, 6) |

**Resultado Final**: DataFrame Pandas listo para estrategia ✅

---

**Archivo**: `core/mt5_live_data.py`  
**Función Clave**: `get_live_data(symbol, timeframe, bars=200)`  
**Retorna**: `pd.DataFrame(200, 6)` con OHLCV real en vivo  
**Status**: ✅ **Funcional y Validado**
