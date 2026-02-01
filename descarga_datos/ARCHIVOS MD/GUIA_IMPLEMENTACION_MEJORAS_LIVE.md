# 🚀 GUÍA DE IMPLEMENTACIÓN - MEJORAS MODO LIVE MT5

**Basado en**: Análisis exhaustivo y mejores prácticas de bots MT5 probados  
**Objetivo**: Equivalencia funcional entre backtest y live trading  
**Prioridad**: CRÍTICA - Sistema no ejecuta operaciones correctamente en live

---

## 📦 CAMBIOS REQUERIDOS POR ARCHIVO

### 1. `descarga_datos/core/mt5_live_data.py`

#### Fix #1: Incrementar Barras Históricas
```python
# LÍNEA ~169 - CAMBIAR
def get_live_data_efficient(self, symbol: str, timeframe: str, 
                           bars: int = 200, use_ticks: bool = False):
# A:
def get_live_data_efficient(self, symbol: str, timeframe: str, 
                           bars: int = 1000, use_ticks: bool = False):
    """
    Aumentado de 200 a 1000 para contexto ML equivalente al backtest.
    Para 15m: 1000 barras = ~10 días
    Para 4h: 1000 barras = ~166 días
    """
```

#### Fix #2: Validación de Velas Completas
```python
# AGREGAR NUEVO MÉTODO después de línea ~350
def is_candle_complete(self, candle_time, timeframe):
    """
    Verifica si una vela está completa (cerrada).
    
    Args:
        candle_time: Timestamp de la vela
        timeframe: Timeframe (15m, 4h, etc.)
    
    Returns:
        bool: True si la vela está completa
    """
    now = datetime.now()
    candle_dt = pd.to_datetime(candle_time)
    
    # Mapeo de timeframes a minutos
    tf_map = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '4h': 240, '1d': 1440
    }
    tf_minutes = tf_map.get(timeframe.lower(), 15)
    
    # Calcular tiempo de cierre de la vela
    candle_close_time = candle_dt + timedelta(minutes=tf_minutes)
    
    # Vela completa si ahora >= tiempo de cierre + buffer
    buffer_seconds = 10  # Buffer de seguridad
    return now >= (candle_close_time + timedelta(seconds=buffer_seconds))

def get_only_complete_candles(self, data, timeframe):
    """
    Filtra solo velas completas del DataFrame.
    
    Args:
        data: DataFrame con columna 'time'
        timeframe: Timeframe actual
    
    Returns:
        DataFrame con solo velas completas
    """
    if data is None or len(data) == 0:
        return data
    
    # Verificar cada vela
    complete_mask = data.apply(
        lambda row: self.is_candle_complete(row['time'], timeframe),
        axis=1
    )
    
    filtered_data = data[complete_mask].copy()
    self.logger.debug(
        f"Filtradas {len(data) - len(filtered_data)} velas en formación, "
        f"quedaron {len(filtered_data)} completas"
    )
    
    return filtered_data
```

#### Fix #3: Usar Filtro en get_live_data_efficient
```python
# MODIFICAR línea ~239 (antes del return)
# ANTES:
return data.copy()

# DESPUÉS:
# Filtrar solo velas completas
complete_data = self.get_only_complete_candles(data, timeframe)
if complete_data is None or len(complete_data) == 0:
    self.logger.debug(f"No hay velas completas disponibles para {symbol} {timeframe}")
    return None

return complete_data.copy()
```

---

### 2. `descarga_datos/core/live_trading_orchestrator.py`

#### Fix #1: Validación AutoTrading al Inicio
```python
# AGREGAR NUEVO MÉTODO después de línea ~100
def validate_mt5_autotrading(self):
    """
    Valida que AutoTrading esté habilitado en MT5.
    Lanza excepción si no está habilitado.
    """
    if not MT5_AVAILABLE:
        raise RuntimeError("MetaTrader5 no está disponible")
    
    if not mt5.initialize():
        raise ConnectionError("No se pudo conectar a MT5")
    
    account_info = mt5.account_info()
    if account_info is None:
        raise ConnectionError("No se pudo obtener información de cuenta MT5")
    
    # Verificar si trading está permitido
    if not account_info.trade_allowed:
        error_msg = """
❌ ERROR CRÍTICO: AutoTrading está DESHABILITADO en MetaTrader 5

SOLUCIÓN REQUERIDA (5 minutos):
1. Abrir MetaTrader 5
2. Clic en: Tools → Options
3. Tab: Expert Advisors
4. ✅ Marcar: "Allow automated trading"
5. ✅ Marcar: "Allow DLL imports"
6. Clic: OK
7. Reiniciar MT5
8. Ejecutar bot nuevamente

Estado actual:
  - Cuenta: {account}
  - Trading permitido: {allowed}
  - Balance: ${balance:.2f}
        """.format(
            account=account_info.login,
            allowed=account_info.trade_allowed,
            balance=account_info.balance
        )
        raise PermissionError(error_msg)
    
    logger.info(f"✅ AutoTrading verificado: Cuenta {account_info.login}, Balance ${account_info.balance:.2f}")
    return True

# MODIFICAR __init__ línea ~60 para llamar validación
def __init__(self, config_path: str = None):
    # ... código existente ...
    
    # AGREGAR después de inicializar data_provider:
    # Validar AutoTrading antes de comenzar
    if MT5_AVAILABLE:
        try:
            self.validate_mt5_autotrading()
        except PermissionError as e:
            logger.error(str(e))
            raise
```

#### Fix #2: Sincronización con Cierre de Vela
```python
# AGREGAR NUEVO MÉTODO después de validate_mt5_autotrading
def calculate_seconds_to_next_candle(self, timeframe):
    """
    Calcula segundos hasta el cierre de la próxima vela.
    
    Args:
        timeframe: Timeframe actual (15m, 4h, etc.)
    
    Returns:
        int: Segundos hasta cierre + buffer
    """
    now = datetime.now()
    
    # Mapeo de timeframes a minutos
    tf_map = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '4h': 240, '1d': 1440
    }
    tf_minutes = tf_map.get(timeframe.lower(), 15)
    
    # Calcular minutos transcurridos en vela actual
    if tf_minutes < 60:
        # Para timeframes menores a 1h
        minutes_in_current_candle = now.minute % tf_minutes
    elif tf_minutes < 1440:
        # Para timeframes de horas
        hours_in_tf = tf_minutes // 60
        hours_in_current_candle = now.hour % hours_in_tf
        minutes_in_current_candle = (hours_in_current_candle * 60) + now.minute
    else:
        # Para timeframes diarios
        minutes_in_current_candle = (now.hour * 60) + now.minute
    
    # Calcular segundos hasta próximo cierre
    minutes_to_next = tf_minutes - minutes_in_current_candle
    seconds_to_next = (minutes_to_next * 60) - now.second
    
    # Agregar buffer de seguridad (10 segundos)
    buffer_seconds = 10
    
    return max(seconds_to_next + buffer_seconds, 10)
```

#### Fix #3: Modificar Ciclo Principal
```python
# BUSCAR el ciclo principal (around línea ~400-500)
# REEMPLAZAR:
while self.running:
    # ... procesamiento ...
    await asyncio.sleep(5)  # ← CAMBIAR ESTO

# POR:
while self.running:
    try:
        # ... procesamiento normal ...
        
        # Calcular espera dinámica hasta próxima vela
        wait_seconds = self.calculate_seconds_to_next_candle(
            self.strategy_live_configs[strategy_name].get('timeframes', ['15m'])[0]
        )
        
        logger.debug(f"💤 Esperando {wait_seconds} segundos hasta próxima vela completa")
        await asyncio.sleep(wait_seconds)
        
    except Exception as e:
        logger.error(f"Error en ciclo de trading: {e}")
        await asyncio.sleep(60)  # Espera de recuperación
```

---

### 3. `descarga_datos/config/config.yaml`

#### Fix #1: Alinear Timeframes
```yaml
# LÍNEA ~95 - CAMBIAR si es necesario
backtesting:
  timeframe: 15m  # ← ASEGURAR que coincida con live

# LÍNEA ~130 - VERIFICAR
live_trading:
  # Agregar timeframe explícito
  default_timeframe: 15m  # ← Debe coincidir con backtest
  
  # Configuración por estrategia
  strategy_mapping:
    UltraDetailedHeikinAshiML:
      active: true
      timeframes: ['15m']  # ← Mismo que backtest
      symbols: ['Volatility 75 Index']
```

#### Fix #2: Incrementar Barras de Historia Inicial
```yaml
# AGREGAR o MODIFICAR (búsqueda en live_trading section)
live_trading:
  initial_history_bars: 1000  # ← CAMBIAR de 200 a 1000
  update_interval_seconds: 900  # ← 15 minutos (sincronizado con vela)
```

---

### 4. `descarga_datos/tests/validate_live_setup.py` (NUEVO ARCHIVO)

```python
"""
Script de validación para verificar configuración de live trading.
Ejecutar ANTES de iniciar live trading para detectar problemas.
"""

import MetaTrader5 as mt5
from pathlib import Path
import sys

# Agregar path al proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import load_config_from_yaml
from utils.logger import setup_logger

logger = setup_logger('ValidateLiveSetup')

def validate_mt5_connection():
    """Valida conexión a MT5."""
    print("\n🔌 Validando conexión MT5...")
    
    if not mt5.initialize():
        print("❌ No se pudo conectar a MT5")
        print("   Solución: Asegurar que MT5 esté abierto y corriendo")
        return False
    
    print("✅ MT5 conectado exitosamente")
    return True

def validate_autotrading():
    """Valida que AutoTrading esté habilitado."""
    print("\n🤖 Validando AutoTrading...")
    
    account_info = mt5.account_info()
    if account_info is None:
        print("❌ No se pudo obtener información de cuenta")
        return False
    
    if not account_info.trade_allowed:
        print("❌ AutoTrading DESHABILITADO")
        print("   Solución:")
        print("   1. Tools → Options → Expert Advisors")
        print("   2. ✅ Marcar 'Allow automated trading'")
        print("   3. Reiniciar MT5")
        return False
    
    print(f"✅ AutoTrading habilitado")
    print(f"   Cuenta: {account_info.login}")
    print(f"   Balance: ${account_info.balance:.2f}")
    return True

def validate_symbol(symbol):
    """Valida que el símbolo esté disponible."""
    print(f"\n📊 Validando símbolo {symbol}...")
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"❌ Símbolo {symbol} no disponible")
        print(f"   Solución: Verificar nombre del símbolo en MT5")
        return False
    
    print(f"✅ Símbolo {symbol} disponible")
    print(f"   Spread: {symbol_info.spread}")
    print(f"   Digits: {symbol_info.digits}")
    return True

def validate_data_availability(symbol, timeframe):
    """Valida que haya datos disponibles."""
    print(f"\n📈 Validando datos para {symbol} {timeframe}...")
    
    tf_map = {
        '1m': mt5.TIMEFRAME_M1,
        '5m': mt5.TIMEFRAME_M5,
        '15m': mt5.TIMEFRAME_M15,
        '30m': mt5.TIMEFRAME_M30,
        '1h': mt5.TIMEFRAME_H1,
        '4h': mt5.TIMEFRAME_H4,
        '1d': mt5.TIMEFRAME_D1
    }
    
    mt5_tf = tf_map.get(timeframe.lower())
    if mt5_tf is None:
        print(f"❌ Timeframe {timeframe} no soportado")
        return False
    
    rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
    if rates is None or len(rates) == 0:
        print(f"❌ No hay datos disponibles para {symbol} {timeframe}")
        return False
    
    print(f"✅ Datos disponibles: {len(rates)} velas")
    return True

def validate_config():
    """Valida configuración del sistema."""
    print("\n⚙️  Validando configuración...")
    
    try:
        config = load_config_from_yaml()
        
        # Verificar timeframes consistentes
        backtest_tf = config.backtesting.timeframe
        live_tf = config.live_trading.get('default_timeframe', '15m')
        
        if backtest_tf != live_tf:
            print(f"⚠️  ADVERTENCIA: Timeframes inconsistentes")
            print(f"   Backtest: {backtest_tf}")
            print(f"   Live: {live_tf}")
            print(f"   Recomendación: Alinear ambos timeframes")
        else:
            print(f"✅ Timeframes alineados: {backtest_tf}")
        
        # Verificar barras de historia
        history_bars = config.live_trading.get('initial_history_bars', 200)
        if history_bars < 500:
            print(f"⚠️  ADVERTENCIA: Pocas barras de historia ({history_bars})")
            print(f"   Recomendación: Incrementar a 1000+ para contexto ML")
        else:
            print(f"✅ Barras de historia adecuadas: {history_bars}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validando configuración: {e}")
        return False

def main():
    """Ejecuta todas las validaciones."""
    print("="*70)
    print("🔍 VALIDACIÓN DE CONFIGURACIÓN LIVE TRADING")
    print("="*70)
    
    checks = [
        validate_mt5_connection(),
        validate_autotrading(),
        validate_config()
    ]
    
    # Validar símbolos de configuración
    try:
        config = load_config_from_yaml()
        symbols = config.backtesting.symbols
        timeframe = config.backtesting.timeframe
        
        for symbol in symbols:
            checks.append(validate_symbol(symbol))
            checks.append(validate_data_availability(symbol, timeframe))
    except:
        pass
    
    print("\n" + "="*70)
    if all(checks):
        print("✅ TODAS LAS VALIDACIONES PASARON")
        print("🚀 Sistema listo para live trading")
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON")
        print("⚠️  Corregir problemas antes de iniciar live trading")
    print("="*70)
    
    mt5.shutdown()
    return all(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## 🔧 ORDEN DE IMPLEMENTACIÓN

### Paso 1: Validación Pre-Implementación (15 min)
```bash
# Ejecutar script de validación
cd /home/runner/work/copilot-bot-v-4.11/copilot-bot-v-4.11/descarga_datos
python tests/validate_live_setup.py

# Verificar que todas las validaciones pasen
```

### Paso 2: Cambios en mt5_live_data.py (30 min)
1. Cambiar bars default de 200 a 1000
2. Agregar método `is_candle_complete()`
3. Agregar método `get_only_complete_candles()`
4. Modificar `get_live_data_efficient()` para filtrar

### Paso 3: Cambios en live_trading_orchestrator.py (45 min)
1. Agregar `validate_mt5_autotrading()`
2. Llamar validación en `__init__`
3. Agregar `calculate_seconds_to_next_candle()`
4. Modificar ciclo principal con espera dinámica

### Paso 4: Cambios en config.yaml (10 min)
1. Alinear timeframes
2. Incrementar initial_history_bars a 1000
3. Verificar estrategia mapping

### Paso 5: Testing (1-2 horas)
```bash
# Test 1: Validación de setup
python tests/validate_live_setup.py

# Test 2: Dry-run de 30 minutos
python main.py --live-mt5
# Observar logs, verificar que:
# - AutoTrading validado ✅
# - Velas completas detectadas ✅
# - Sincronización correcta ✅
# - Señales generadas ✅

# Test 3: Comparar métricas
# - Señales generadas vs backtest
# - Timing de operaciones
# - Equivalencia de datos
```

---

## 📊 VERIFICACIÓN DE ÉXITO

### Indicadores de que los cambios funcionan:

✅ **Logs muestran:**
```
[INFO] ✅ AutoTrading verificado: Cuenta XXXXX, Balance $XXX
[DEBUG] Filtradas 0 velas en formación, quedaron 1000 completas
[DEBUG] 💤 Esperando 847 segundos hasta próxima vela completa
[INFO] 📊 BUY: Position size recibido del risk management: 0.02
```

✅ **Operaciones ejecutadas:**
```
Antes: 1 operación en 10 horas
Después: 3-5 operaciones por día (para 15m)
```

✅ **Sin errores de:**
```
- "AutoTrading disabled"
- "Vela en formación procesada"
- "Datos insuficientes"
- "Señales rechazadas"
```

---

## 🚨 TROUBLESHOOTING

### Problema: "No hay velas completas disponibles"
```bash
# Verificar timeframe y hora actual
# Puede ser que justo se esté ejecutando entre velas

# Solución: Esperar 1-2 minutos y reintentar
```

### Problema: "Señales generadas pero no ejecutadas"
```bash
# Verificar logs de risk management
# Puede ser rechazo por límites de posiciones

# Verificar config.yaml:
# max_positions: 5
# allow_multiple_positions_same_symbol: true
```

### Problema: "AutoTrading validación falla"
```bash
# Seguir pasos en mensaje de error
# Reiniciar MT5 después de cambios
# Verificar con tests/validate_live_setup.py
```

---

## 📝 CHECKLIST FINAL

Antes de dar por completada la implementación:

- [ ] Todos los tests de `validate_live_setup.py` pasan
- [ ] Logs muestran validación de AutoTrading exitosa
- [ ] Logs muestran filtrado de velas correctamente
- [ ] Logs muestran espera sincronizada con velas
- [ ] Timeframes alineados en config.yaml
- [ ] Barras históricas incrementadas a 1000
- [ ] Sistema ejecuta 3-5 operaciones en 24h de prueba
- [ ] Win rate similar a backtest (70-80%)
- [ ] Sin errores de MT5 en logs
- [ ] Documentación actualizada

---

**Guía de Implementación**  
**Versión**: 1.0  
**Fecha**: 15-Nov-2025  
**Tiempo Estimado**: 3-4 horas total

