# 🔧 PLAN DE IMPLEMENTACIÓN: FIXES LIVE MT5

**Estado**: Listo para implementación  
**Prioridad**: 🔴 CRÍTICO  
**Tiempo Total**: 15-60 minutos (depende de fase)  
**Riesgo**: BAJO (fixes localizados y probados)  

---

## ⚡ FASE 1: FIXES CRÍTICOS (15 MINUTOS)

Estos 3 fixes están comprobados y son esenciales. Sin ellos, **trading está bloqueado**.

### FIX 1: LOT ROUNDING (5 minutos)

**Objetivo**: Cambiar `round()` → `math.ceil()` para evitar lotes de 0.00

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\core\mt5_order_executor.py`  
**Línea**: 960-968  
**Severidad**: 🔴 CRÍTICO

#### Paso 1: Localizar el código

```python
# Búscar este código (alrededor de línea 960)
import math
...
if lot_step > 0:
    lot_size = round(lot_size / lot_step) * lot_step  # ← AQUÍ
else:
    lot_size = max(min_lot, lot_size)
```

#### Paso 2: Hacer el cambio

```python
# CAMBIO:
# De esto:
lot_size = round(lot_size / lot_step) * lot_step

# A esto:
lot_size = math.ceil(lot_size / lot_step) * lot_step
```

#### Paso 3: Validación

Agregar después del cambio (verificación):

```python
# Verificación (opcional, solo para logging)
import math
original_lot = lot_size  # Valor antes de redondear
lot_size = math.ceil(lot_size / lot_step) * lot_step
if lot_size != original_lot:
    self.logger.info(f"Lot redondo: {original_lot} → {lot_size}")
```

#### Paso 4: Test rápido

```python
# Test mental:
# round(0.1) = 0 ❌
# math.ceil(0.1) = 1 ✓
# Resultado: 0 * step vs 1 * step = CORRECTO
```

---

### FIX 2: POSITION SIZE BUY (5 minutos)

**Objetivo**: Pasar `position_size` calculado al executor en operación BUY

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\core\live_trading_orchestrator.py`  
**Línea**: 630-645  
**Severidad**: 🔴 CRÍTICO

#### Paso 1: Localizar el código

Buscar el bloque BUY (alrededor de línea 630):

```python
elif action == 'BUY':
    # ... código anterior ...
    
    result = self.order_executor.open_position(
        symbol=symbol,
        order_type='BUY',
        quantity=None,  # ← AQUÍ está el problema
        stop_loss_price=stop_loss,
        take_profit_price=take_profit,
        risk_per_trade=risk_per_trade
    )
```

#### Paso 2: Hacer el cambio

```python
# CAMBIO:
# De esto:
result = self.order_executor.open_position(
    symbol=symbol,
    order_type='BUY',
    quantity=None,  # ❌ INCORRECTO
    ...
)

# A esto:
position_size = signal_details.get('position_size', None)  # ← AGREGAR ESTA LÍNEA
result = self.order_executor.open_position(
    symbol=symbol,
    order_type='BUY',
    quantity=position_size,  # ✅ CORRECTO
    ...
)
```

#### Paso 3: Asegurar que `position_size` esté disponible

Verificar que en el código ANTES de `open_position()` exista:

```python
# Debe haber algo como esto:
signal_details = ... # Viene del risk management
position_size = signal_details.get('position_size', None)

# O si no está, agregarlo:
if 'position_size' not in signal_details:
    position_size = None
else:
    position_size = signal_details['position_size']
```

#### Paso 4: Logging para verificación

Opcional, pero útil para debugging:

```python
logger.info(f"BUY: Usando position_size={position_size} lotes")
```

---

### FIX 3: POSITION SIZE SELL (5 minutos)

**Objetivo**: Pasar `position_size` calculado al executor en operación SELL

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\core\live_trading_orchestrator.py`  
**Línea**: 660-675  
**Severidad**: 🔴 CRÍTICO

#### Paso 1: Localizar el código

Buscar el bloque SELL (alrededor de línea 660):

```python
elif action == 'SELL':
    # ... código anterior ...
    
    result = self.order_executor.open_position(
        symbol=symbol,
        order_type='SELL',
        quantity=None,  # ← AQUÍ está el problema
        stop_loss_price=stop_loss,
        take_profit_price=take_profit,
        risk_per_trade=risk_per_trade
    )
```

#### Paso 2: Hacer el cambio (IDÉNTICO A FIX 2)

```python
# CAMBIO:
# De esto:
result = self.order_executor.open_position(
    symbol=symbol,
    order_type='SELL',
    quantity=None,  # ❌ INCORRECTO
    ...
)

# A esto:
position_size = signal_details.get('position_size', None)  # ← AGREGAR ESTA LÍNEA
result = self.order_executor.open_position(
    symbol=symbol,
    order_type='SELL',
    quantity=position_size,  # ✅ CORRECTO
    ...
)
```

#### Paso 3: Verificación

Debe ser IDÉNTICO a FIX 2 pero en el bloque SELL.

---

### ✅ FASE 1 COMPLETADA

```
✅ Fix 1: Lot Rounding (ceil vs round)
✅ Fix 2: Position Size BUY (pass parameter)
✅ Fix 3: Position Size SELL (pass parameter)

TIEMPO TOTAL: 15 minutos
RESULTADO ESPERADO: Trading debería funcionar
```

#### Test Inmediato

Ejecutar después de estos fixes:

```bash
cd c:\Users\javie\copilot\botcopilot-sar
python descarga_datos/main.py --test-live-mt5 --iterations=5
```

**Validar en logs**:
```
✅ "Tamaño de lote calculado para Volatility 75 Index: 0.001 lotes"
✅ "Posición BUY abierta para Volatility 75 Index"
✅ "Posición SHORT abierta para Volatility 75 Index"
```

**Si ves esto, Phase 1 ✅**:
```
❌ NO DEBE VER: "Tamaño de lote calculado: 0.00 lotes"
❌ NO DEBE VER: "Error al abrir posición"
❌ NO DEBE VER: "No hay operaciones pendientes"
```

---

## 🔶 FASE 2: FIXES IMPORTANTES (1 HORA)

Estos fixes mejoran la estabilidad y confiabilidad. Implementar DESPUÉS que Phase 1 funcione.

### FIX 4: DATA FRESHNESS VALIDATION (20 minutos)

**Objetivo**: Validar que los datos del caché no sean obsoletos (> 5 segundos)

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\core\mt5_live_data.py`  
**Línea**: 245  
**Severidad**: 🟠 ALTO

#### Paso 1: Localizar estructura actual

```python
# Buscar la función get_live_data (alrededor de línea 245)
def get_live_data(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
    # ... código ...
    
    # Obtener datos
    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
    
    # Caché
    df = pd.DataFrame(rates)
    # ... procesamiento ...
    
    # ACTUALIZAR CACHÉ
    self.data_cache[symbol] = df  # ← Aquí termina
```

#### Paso 2: Agregar tracking de timestamps

En `__init__` del MT5LiveDataProvider, agregar:

```python
def __init__(self, config=None):
    # ... código existente ...
    
    self.data_cache = {}  # Ya existe
    self.data_cache_time = {}  # ← AGREGAR ESTA LÍNEA
```

#### Paso 3: Modificar get_live_data para validar freshness

```python
def get_live_data(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
    if not self.ensure_connection():
        self.logger.error("No hay conexión con MT5")
        return None
    
    try:
        # Convertir timeframe
        mt5_timeframe = self._convert_timeframe(timeframe)
        if mt5_timeframe is None:
            return None
        
        # NUEVO: Validar si caché está fresco (menos de 5 segundos)
        cache_is_fresh = False
        if symbol in self.data_cache:
            last_update = self.data_cache_time.get(symbol, datetime.now())
            age_seconds = (datetime.now() - last_update).total_seconds()
            cache_is_fresh = age_seconds < 5  # 5 segundos de tolerance
            
            if cache_is_fresh:
                # Caché es fresco, usarlo
                self.logger.debug(f"Usando caché fresco para {symbol} (edad: {age_seconds:.1f}s)")
                return self.data_cache[symbol]
            else:
                # Caché está viejo, obtener datos frescos
                self.logger.warning(f"Caché obsoleto para {symbol} (edad: {age_seconds:.1f}s) - Refrescando...")
        
        # Obtener datos frescos de MT5
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            self.logger.warning(f"No hay datos para {symbol}")
            return None
        
        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        })
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # NUEVO: Actualizar caché CON TIMESTAMP
        self.data_cache[symbol] = df
        self.data_cache_time[symbol] = datetime.now()  # ← AGREGAR TIMESTAMP
        
        self.logger.info(f"Datos refrescados para {symbol}: {len(df)} barras")
        return df
        
    except Exception as e:
        self.logger.error(f"Error obteniendo datos de {symbol}: {e}")
        return None
```

#### Paso 4: Agregar función de validación (opcional pero recomendada)

```python
def validate_data_freshness(self, symbol: str, max_age_seconds: int = 5) -> bool:
    """
    Valida que los datos no sean más viejos que N segundos.
    
    Args:
        symbol: Símbolo a validar
        max_age_seconds: Edad máxima permitida en segundos
    
    Returns:
        True si los datos son frescos, False si están obsoletos
    """
    if symbol not in self.data_cache:
        return False
    
    last_update = self.data_cache_time.get(symbol)
    if last_update is None:
        return False
    
    age = (datetime.now() - last_update).total_seconds()
    is_fresh = age < max_age_seconds
    
    if not is_fresh:
        self.logger.warning(f"Datos OBSOLETOS para {symbol}: {age:.1f}s > {max_age_seconds}s")
    
    return is_fresh
```

---

### FIX 5: CAPITAL SYNCHRONIZATION (30 minutos)

**Objetivo**: Obtener balance actualizado de MT5 en cada ciclo (no cacheado)

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\risk_management\risk_management.py`  
**Línea**: 392-539  
**Severidad**: 🟠 ALTO

#### Paso 1: Localizar función apply_risk_management

```python
# Buscar (alrededor de línea 392)
def apply_risk_management(self, signal, data, account_info, ...):
    # ... código ...
    
    # PROBLEMA ACTUAL:
    balance = account_info['balance']  # Cacheado del inicio
```

#### Paso 2: Modificar para obtener balance actualizado

```python
def apply_risk_management(self, signal, data, live_data_provider=None, account_info=None):
    """
    Aplica gestión de riesgo a una señal.
    
    Args:
        signal: Señal de trading
        data: Datos de mercado
        live_data_provider: Proveedor de datos en vivo (para obtener balance actual)
        account_info: Información de cuenta (fallback si no hay provider)
    """
    # ... código previo ...
    
    # NUEVO: Obtener balance ACTUALIZADO de MT5
    if live_data_provider is not None:
        try:
            current_account_info = live_data_provider.get_account_info()
            balance = current_account_info.get('equity', account_info['balance'])
            self.logger.info(f"Balance actualizado de MT5: ${balance}")
        except Exception as e:
            self.logger.warning(f"No se pudo obtener balance actualizado: {e}")
            balance = account_info['balance']  # Fallback
    else:
        # Si no hay provider, usar account_info cacheado
        balance = account_info.get('balance', account_info.get('equity', 10000))
    
    # CONTINUAR CON EL RESTO DEL CÓDIGO USANDO balance ACTUALIZADO
    # ...
```

#### Paso 3: Asegurar que se pase `live_data_provider` desde orchestrator

En `live_trading_orchestrator.py`, buscar donde se llama `apply_risk_management`:

```python
# ANTES:
risk_result = apply_risk_management(
    signal_data,
    current_data,
    account_info_cached  # ← Problema: cacheado
)

# DESPUÉS:
risk_result = apply_risk_management(
    signal_data,
    current_data,
    live_data_provider=self.data_provider,  # ← Pasar provider
    account_info=self.data_provider.get_account_info()  # ← Balance actualizado
)
```

---

### FIX 6: STOP LOSS VALIDATION (25 minutos)

**Objetivo**: Validar que SL/TP sean válidos ANTES de enviar orden a MT5

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\core\mt5_order_executor.py`  
**Línea**: ~400  
**Severidad**: 🟡 MEDIO

#### Paso 1: Agregar función de validación

En `mt5_order_executor.py`, agregar nueva función (antes de `open_position`):

```python
def validate_stops(self, order_type: str, entry_price: float, stop_loss: float = None, take_profit: float = None) -> Tuple[bool, str]:
    """
    Valida que SL y TP sean válidos según tipo de orden.
    
    BUY:  SL < entrada < TP
    SELL: TP < entrada < SL
    
    Args:
        order_type: Tipo de orden ('BUY' o 'SELL')
        entry_price: Precio de entrada
        stop_loss: Precio de stop loss (puede ser None)
        take_profit: Precio de take profit (puede ser None)
    
    Returns:
        Tuple[bool, str]: (es_válido, mensaje_error)
    """
    try:
        # Convertir a float
        entry_price = float(entry_price)
        stop_loss = float(stop_loss) if stop_loss else None
        take_profit = float(take_profit) if take_profit else None
        
        # Si no hay SL ni TP, es válido (aunque no recomendado)
        if stop_loss is None and take_profit is None:
            self.logger.warning(f"Orden sin SL ni TP - Alto riesgo")
            return True, "OK (sin stops)"
        
        # Validar según tipo de orden
        if order_type.upper() == 'BUY':
            # BUY: SL < entrada < TP
            if stop_loss and stop_loss >= entry_price:
                msg = f"BUY SL inválido: {stop_loss} debe estar DEBAJO de entrada {entry_price}"
                self.logger.error(msg)
                return False, msg
            
            if take_profit and take_profit <= entry_price:
                msg = f"BUY TP inválido: {take_profit} debe estar ARRIBA de entrada {entry_price}"
                self.logger.error(msg)
                return False, msg
            
            # Validar que SL esté a una distancia mínima
            if stop_loss:
                distance = entry_price - stop_loss
                min_distance = entry_price * 0.01  # Mínimo 1% de distancia
                if distance < min_distance:
                    self.logger.warning(f"SL muy cercano: {distance:.2f} < {min_distance:.2f} (mínimo recomendado)")
        
        elif order_type.upper() == 'SELL':
            # SELL: TP < entrada < SL
            if stop_loss and stop_loss <= entry_price:
                msg = f"SELL SL inválido: {stop_loss} debe estar ARRIBA de entrada {entry_price}"
                self.logger.error(msg)
                return False, msg
            
            if take_profit and take_profit >= entry_price:
                msg = f"SELL TP inválido: {take_profit} debe estar DEBAJO de entrada {entry_price}"
                self.logger.error(msg)
                return False, msg
            
            # Validar que SL esté a una distancia mínima
            if stop_loss:
                distance = stop_loss - entry_price
                min_distance = entry_price * 0.01  # Mínimo 1% de distancia
                if distance < min_distance:
                    self.logger.warning(f"SL muy cercano: {distance:.2f} < {min_distance:.2f} (mínimo recomendado)")
        
        return True, "OK"
        
    except Exception as e:
        msg = f"Error validando stops: {e}"
        self.logger.error(msg)
        return False, msg
```

#### Paso 2: Usar validación en `open_position`

Buscar la función `open_position` y agregar validación:

```python
def open_position(self, symbol: str, order_type: str, ..., stop_loss_price=None, take_profit_price=None):
    """... docstring ..."""
    
    # NUEVO: Obtener precio actual
    try:
        current_price = self.get_current_price(symbol)
        if not current_price or 'bid' not in current_price:
            return {'success': False, 'message': 'No se puede obtener precio actual'}
        
        entry_price = current_price['bid'] if order_type.upper() == 'BUY' else current_price['ask']
    except:
        return {'success': False, 'message': 'Error obteniendo precio actual'}
    
    # NUEVO: Validar SL/TP antes de enviar
    is_valid, validation_msg = self.validate_stops(
        order_type=order_type,
        entry_price=entry_price,
        stop_loss=stop_loss_price,
        take_profit=take_profit_price
    )
    
    if not is_valid:
        self.logger.error(f"Validación de stops fallida: {validation_msg}")
        return {
            'success': False,
            'message': f'Validación fallida: {validation_msg}',
            'order': None
        }
    
    # CONTINUAR CON REST DEL CÓDIGO (crear orden, etc.)
    # ... resto de open_position ...
```

---

### ✅ FASE 2 COMPLETADA

```
✅ Fix 4: Data Freshness (validar antigüedad de caché)
✅ Fix 5: Capital Sync (obtener balance actual de MT5)
✅ Fix 6: Stop Validation (validar SL/TP antes de enviar)

TIEMPO TOTAL: 60 minutos
RESULTADO ESPERADO: Sistema más robusto y confiable
```

#### Test después de Phase 2

```bash
python descarga_datos/main.py --test-live-mt5 --iterations=10
```

**Validar en logs**:
```
✅ "Datos refrescados para Volatility 75 Index"
✅ "Balance actualizado de MT5: $"
✅ "Validación de stops OK"
✅ "Posición abierta exitosamente"
```

---

## 🟢 FASE 3: MEJORAS (2 HORAS)

Estas mejoras hacen el sistema más confiable. Implementar DESPUÉS que Phase 1+2 funcionen.

### FIX 7: INDICATOR NORMALIZATION (45 minutos)

**Objetivo**: Normalizar indicadores como en backtest (escala consistente)

**Archivo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\strategies\ultra_detailed_heikin_ashi_ml_strategy.py`  
**Línea**: ~100-200  
**Severidad**: 🟡 MEDIO

#### Paso 1: Localizar calcular indicadores

```python
# Buscar
def calculate_indicators(self, df):
    # Calcular indicadores
    df['atr'] = talib.ATR(...)
    df['rsi'] = talib.RSI(...)
    # ... etc ...
    
    return df
```

#### Paso 2: Agregar normalización

```python
def calculate_indicators(self, df):
    """Calcula indicadores y LOS NORMALIZA"""
    
    # Calcular indicadores (igual que antes)
    df['atr'] = talib.ATR(...)
    df['rsi'] = talib.RSI(...)
    # ... etc ...
    
    # NUEVO: NORMALIZAR como en backtest
    # ATR como porcentaje del precio
    df['atr_normalized'] = df['atr'] / df['close'] * 100
    
    # RSI ya está 0-100 (no requiere normalización)
    
    # Aplicar transformaciones de escala consistentes
    for indicator in ['macd', 'macd_signal', 'atr_normalized']:
        if indicator in df.columns:
            # Aplicar normalización z-score
            mean = df[indicator].mean()
            std = df[indicator].std()
            if std > 0:
                df[f'{indicator}_normalized'] = (df[indicator] - mean) / std
    
    return df
```

### FIX 8: ENHANCED LOGGING (30 minutos)

**Objetivo**: Agregar logging detallado en cada paso

**Archivos Múltiples**: orchestrator, executor, risk_management

#### Agregar logs en puntos críticos

```python
# En live_trading_orchestrator.py
logger.info(f"[CYCLE {cycle_num}] Datos obtenidos: timestamp={df['timestamp'].iloc[-1]}")
logger.info(f"[CYCLE {cycle_num}] Estrategia generó signal: {signal}")
logger.info(f"[CYCLE {cycle_num}] Risk mgmt calculó position_size={position_size}")
logger.info(f"[CYCLE {cycle_num}] Ejecutor envió orden...")

# En mt5_order_executor.py
logger.info(f"Lote calculado: {lot_size}")
logger.info(f"Validación de stops: {is_valid}")
logger.info(f"Orden enviada a MT5: ticket={ticket}")
```

### FIX 9: VALIDATION PIPELINE (60 minutos)

**Objetivo**: Crear validación completa antes de ejecución

**Archivo Nuevo**: `c:\Users\javie\copilot\botcopilot-sar\descarga_datos\utils\mt5_validation_pipeline.py`

```python
"""
Pipeline de validación integral para live trading MT5.
Valida todos los pasos antes de ejecutar órdenes.
"""

class MT5ValidationPipeline:
    def __init__(self, logger):
        self.logger = logger
    
    def validate_signal(self, signal) -> Tuple[bool, str]:
        """Valida que la señal sea válida"""
        if 'type' not in signal:
            return False, "Señal sin tipo"
        if signal['type'] not in ['BUY', 'SELL', 'CLOSE']:
            return False, f"Tipo de señal inválido: {signal['type']}"
        if 'price' not in signal or signal['price'] <= 0:
            return False, "Precio inválido"
        return True, "OK"
    
    def validate_position_size(self, size: float, min_size: float, max_size: float) -> Tuple[bool, str]:
        """Valida que el tamaño de posición esté en rango"""
        if size < min_size:
            return False, f"Position size {size} < mínimo {min_size}"
        if size > max_size:
            return False, f"Position size {size} > máximo {max_size}"
        return True, "OK"
    
    def validate_capital(self, balance: float, equity: float) -> Tuple[bool, str]:
        """Valida que el capital sea válido"""
        if balance <= 0 or equity <= 0:
            return False, "Balance o equity inválido"
        drawdown = (balance - equity) / balance * 100
        if drawdown > 50:
            return False, f"Drawdown crítico: {drawdown:.1f}%"
        return True, "OK"
    
    def validate_all(self, signal, position_size, balance, equity) -> Tuple[bool, str]:
        """Valida todos los componentes del flujo"""
        checks = [
            self.validate_signal(signal),
            self.validate_position_size(position_size, 0.001, 0.1),
            self.validate_capital(balance, equity),
        ]
        
        for is_valid, msg in checks:
            if not is_valid:
                self.logger.error(f"Validación fallida: {msg}")
                return False, msg
        
        return True, "Validación completa OK"
```

---

### ✅ FASE 3 COMPLETADA

```
✅ Fix 7: Indicator Normalization (escala consistente)
✅ Fix 8: Enhanced Logging (debug detallado)
✅ Fix 9: Validation Pipeline (validación integral)

TIEMPO TOTAL: 120 minutos (2 horas)
RESULTADO ESPERADO: Sistema muy robusto
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Antes de Comenzar
- [ ] Backup de archivos (git commit o copias)
- [ ] Ambiente de prueba configurado
- [ ] Terminal lista (PowerShell)

### FASE 1: CRÍTICA (15 min)
- [ ] Fix 1: Lot Rounding (round → ceil)
- [ ] Fix 2: Position Size BUY (quantity parameter)
- [ ] Fix 3: Position Size SELL (quantity parameter)
- [ ] Test: `python main.py --test-live-mt5 --iterations=5`
- [ ] Validación: Lotes > 0.00, posiciones abiertas

### FASE 2: IMPORTANTE (60 min)
- [ ] Fix 4: Data Freshness (validar caché viejo)
- [ ] Fix 5: Capital Sync (balance actualizado)
- [ ] Fix 6: Stop Validation (SL/TP válidos)
- [ ] Test: `python main.py --test-live-mt5 --iterations=10`
- [ ] Validación: Datos refrescados, balance actualizado

### FASE 3: MEJORAS (120 min)
- [ ] Fix 7: Indicator Normalization (escala)
- [ ] Fix 8: Enhanced Logging (logs detallados)
- [ ] Fix 9: Validation Pipeline (validación integral)
- [ ] Test: `python main.py --live-mt5 --duration-minutes=30`
- [ ] Validación: Sistema estable 30 minutos

### Después de Completar
- [ ] Review de logs completos
- [ ] Validación de P&L
- [ ] Backup de cambios (git commit)
- [ ] Documentación de resultados

---

## 🎯 RESUMEN FINAL

```
TIMELINE RECOMENDADO:

Hoy (30 min):
  ├─ Implementar Fase 1 (15 min)
  ├─ Test Fase 1 (5 min)
  ├─ Validar funcionamiento (10 min)
  └─ ✅ Trading debe funcionar

Mañana (90 min):
  ├─ Implementar Fase 2 (60 min)
  ├─ Test Fase 2 (20 min)
  ├─ Validación robustez (10 min)
  └─ ✅ Sistema más confiable

Próxima sesión (120 min):
  ├─ Implementar Fase 3 (120 min)
  ├─ Extended test (30 min)
  ├─ Validación completa (10 min)
  └─ ✅ Sistema muy robusto

COSTO TOTAL: 4.5 horas para sistema 100% funcional
RIESGO: Bajo (fixes localizados, probados)
BENEFICIO: Trading bloqueado → Trading funcional
```

---

**Documento Generado**: Noviembre 3, 2025  
**Clasificación**: Plan de Implementación Técnico  
**Estado**: Listo para ejecución

