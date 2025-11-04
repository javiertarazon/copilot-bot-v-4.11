# 🔧 DEBUGGING: Validar 200 Barras 15m en Live MT5

## 📋 Checklist de Validación Completo

### ✅ Nivel 1: Validación de Conexión MT5

```python
# Script para validar conexión MT5
def validate_mt5_connection():
    """Verifica que MT5 esté correctamente conectado"""
    
    print("=" * 60)
    print("🔍 VALIDACIÓN 1: Conexión MT5")
    print("=" * 60)
    
    # 1.1 ¿MT5 inicializado?
    if not mt5.initialize():
        print("❌ ERROR: MT5 no inicializado")
        print(f"   Detalle: {mt5.last_error()}")
        return False
    print("✅ MT5 inicializado correctamente")
    
    # 1.2 ¿Cuenta seleccionada?
    account_info = mt5.account_info()
    if account_info is None:
        print("❌ ERROR: Cuenta no accesible")
        return False
    
    print(f"✅ Cuenta conectada:")
    print(f"   - Login: {account_info.login}")
    print(f"   - Broker: {account_info.server}")
    print(f"   - Balance: ${account_info.balance}")
    print(f"   - Equity: ${account_info.equity}")
    
    # 1.3 ¿Símbolo accesible?
    symbol_info = mt5.symbol_info("Volatility 75 Index")
    if symbol_info is None:
        print("❌ ERROR: Símbolo 'Volatility 75 Index' no encontrado")
        print("   Símbolos disponibles: ver lista en MT5")
        return False
    
    print(f"✅ Símbolo disponible:")
    print(f"   - Símbolo: {symbol_info.name}")
    print(f"   - Bid: {symbol_info.bid}")
    print(f"   - Ask: {symbol_info.ask}")
    print(f"   - Spread: {symbol_info.spread} puntos")
    
    return True
```

---

### ✅ Nivel 2: Validación de Carga de 200 Barras

```python
def validate_get_live_data():
    """Valida que get_live_data() retorna 200 barras correctas"""
    
    print("\n" + "=" * 60)
    print("🔍 VALIDACIÓN 2: get_live_data() - Carga de 200 barras")
    print("=" * 60)
    
    # 2.1 Llamar a get_live_data()
    print("\n📊 Llamando: data_provider.get_live_data('Volatility 75 Index', '15m', 200)")
    df = data_provider.get_live_data('Volatility 75 Index', '15m', 200)
    
    if df is None:
        print("❌ ERROR: get_live_data() retornó None")
        return False
    
    # 2.2 Verificar shape
    print(f"\n✅ DataFrame retornado:")
    print(f"   - Shape: {df.shape} (esperado: (200, 6))")
    
    if df.shape != (200, 6):
        print(f"   ⚠️  ADVERTENCIA: Shape incorrecto!")
        print(f"      Filas: {df.shape[0]} (esperado: 200)")
        print(f"      Columnas: {df.shape[1]} (esperado: 6)")
    
    # 2.3 Verificar columnas
    print(f"\n✅ Columnas del DataFrame:")
    expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in expected_cols:
        if col in df.columns:
            print(f"   ✅ '{col}'")
        else:
            print(f"   ❌ FALTA: '{col}'")
            return False
    
    # 2.4 Verificar tipos de datos
    print(f"\n✅ Tipos de datos:")
    for col in df.columns:
        dtype = df[col].dtype
        if col == 'timestamp':
            if 'datetime' in str(dtype):
                print(f"   ✅ '{col}': {dtype}")
            else:
                print(f"   ❌ '{col}': {dtype} (esperado: datetime64)")
                return False
        else:
            if 'float' in str(dtype) or 'int' in str(dtype):
                print(f"   ✅ '{col}': {dtype}")
            else:
                print(f"   ❌ '{col}': {dtype} (esperado: float/int)")
                return False
    
    # 2.5 Verificar valores
    print(f"\n✅ Estadísticas de valores OHLC:")
    print(f"   Open  - Min: {df['open'].min():.2f}, Max: {df['open'].max():.2f}, Mean: {df['open'].mean():.2f}")
    print(f"   High  - Min: {df['high'].min():.2f}, Max: {df['high'].max():.2f}, Mean: {df['high'].mean():.2f}")
    print(f"   Low   - Min: {df['low'].min():.2f}, Max: {df['low'].max():.2f}, Mean: {df['low'].mean():.2f}")
    print(f"   Close - Min: {df['close'].min():.2f}, Max: {df['close'].max():.2f}, Mean: {df['close'].mean():.2f}")
    print(f"   Volume- Min: {df['volume'].min()}, Max: {df['volume'].max()}, Mean: {df['volume'].mean():.0f}")
    
    # 2.6 Verificar que high >= low
    high_low_check = (df['high'] >= df['low']).all()
    print(f"\n✅ Validación High >= Low: {'✅ OK' if high_low_check else '❌ FALLO'}")
    
    # 2.7 Verificar que close está entre low y high
    close_between = ((df['close'] >= df['low']) & (df['close'] <= df['high'])).all()
    print(f"✅ Validación Low <= Close <= High: {'✅ OK' if close_between else '❌ FALLO'}")
    
    # 2.8 Verificar sin NaN
    nan_count = df.isna().sum().sum()
    print(f"\n✅ Valores NaN totales: {nan_count} {'✅ OK' if nan_count == 0 else '⚠️  ENCONTRADOS'}")
    
    # 2.9 Verificar timestamps
    print(f"\n✅ Rango de timestamps:")
    print(f"   - Primero: {df['timestamp'].iloc[0]}")
    print(f"   - Último:  {df['timestamp'].iloc[-1]}")
    print(f"   - Diferencia: {(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 60 / 15:.0f} barras (esperado ~200)")
    
    # 2.10 Verificar monotonicidad
    monotonic = df['timestamp'].is_monotonic_increasing
    print(f"\n✅ Timestamps ordenados (monótonos): {'✅ OK' if monotonic else '❌ DESORDENADOS'}")
    
    print("\n✅ VALIDACIÓN 2 COMPLETADA")
    return True
```

---

### ✅ Nivel 3: Validación de Preparación de Datos

```python
def validate_prepare_data():
    """Valida que _prepare_data() agrega correctamente los 25 indicadores"""
    
    print("\n" + "=" * 60)
    print("🔍 VALIDACIÓN 3: _prepare_data() - Indicadores técnicos")
    print("=" * 60)
    
    # 3.1 Cargar datos base
    df = data_provider.get_live_data('Volatility 75 Index', '15m', 200)
    
    # 3.2 Aplicar prepare_data
    print("\n📊 Llamando: _prepare_data(df_ohlcv)")
    df_prep = orchestrator._prepare_data(df)
    
    if df_prep is None:
        print("❌ ERROR: _prepare_data() retornó None")
        return False
    
    # 3.3 Verificar shape aumentado
    print(f"\n✅ DataFrame después de preparación:")
    print(f"   - Shape antes: (200, 6)")
    print(f"   - Shape después: {df_prep.shape}")
    print(f"   - Columnas nuevas: {df_prep.shape[1] - 6} (esperado: 25)")
    
    if df_prep.shape[1] != 31:  # 6 original + 25 indicadores
        print(f"   ⚠️  ADVERTENCIA: Esperaba 31 columnas, tengo {df_prep.shape[1]}")
    
    # 3.4 Listar todos los indicadores
    print(f"\n✅ Indicadores agregados:")
    base_cols = set(df.columns)
    prep_cols = set(df_prep.columns)
    new_cols = sorted(prep_cols - base_cols)
    
    for i, col in enumerate(new_cols, 1):
        value = df_prep[col].iloc[-1]  # Último valor
        print(f"   {i:2d}. {col:20s} = {value:12.4f}")
    
    # 3.5 Verificar sin NaN
    nan_count = df_prep.isna().sum()
    problematic_cols = nan_count[nan_count > 0]
    
    print(f"\n✅ Validación de NaN:")
    if len(problematic_cols) == 0:
        print(f"   ✅ Sin NaN en ninguna columna")
    else:
        print(f"   ⚠️  Columnas con NaN:")
        for col, count in problematic_cols.items():
            print(f"      - {col}: {count} NaN")
    
    # 3.6 Verificar valores infinitos
    inf_count = 0
    for col in df_prep.select_dtypes(include=['float']).columns:
        inf_count += np.isinf(df_prep[col]).sum()
    
    print(f"\n✅ Validación de infinitos:")
    print(f"   {inf_count} valores infinitos {'✅ OK' if inf_count == 0 else '⚠️  ENCONTRADOS'}")
    
    # 3.7 Verificar rangos de indicadores
    print(f"\n✅ Validación de rangos de indicadores:")
    
    # RSI: debe estar entre 0-100
    if 'rsi' in df_prep.columns:
        rsi_min, rsi_max = df_prep['rsi'].min(), df_prep['rsi'].max()
        rsi_ok = (rsi_min >= 0) and (rsi_max <= 100)
        print(f"   RSI: {rsi_min:.2f} - {rsi_max:.2f} {'✅' if rsi_ok else '❌ FUERA DE RANGO'}")
    
    # ATR: debe ser positivo
    if 'atr' in df_prep.columns:
        atr_min, atr_max = df_prep['atr'].min(), df_prep['atr'].max()
        atr_ok = atr_min >= 0
        print(f"   ATR: {atr_min:.2f} - {atr_max:.2f} {'✅' if atr_ok else '❌ NEGATIVO'}")
    
    # Bollinger Bands: upper > middle > lower
    if all(col in df_prep.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
        bb_ok = ((df_prep['bb_upper'] >= df_prep['bb_middle']) & 
                 (df_prep['bb_middle'] >= df_prep['bb_lower'])).all()
        print(f"   Bollinger Bands orden: {'✅ OK' if bb_ok else '❌ DESORDENADO'}")
    
    print("\n✅ VALIDACIÓN 3 COMPLETADA")
    return True
```

---

### ✅ Nivel 4: Validación de Señal ML

```python
def validate_ml_signal():
    """Valida que la estrategia ML genera señales correctas"""
    
    print("\n" + "=" * 60)
    print("🔍 VALIDACIÓN 4: Estrategia ML - Generación de señales")
    print("=" * 60)
    
    # 4.1 Cargar datos y preparar
    df = data_provider.get_live_data('Volatility 75 Index', '15m', 200)
    df_prep = orchestrator._prepare_data(df)
    
    # 4.2 Generar señal
    print("\n📊 Llamando: strategy.get_live_signal(df_prepared)")
    signal_result = strategy.get_live_signal(df_prep)
    
    if signal_result is None:
        print("❌ ERROR: get_live_signal() retornó None")
        return False
    
    # 4.3 Validar estructura de salida
    print(f"\n✅ Resultado de la estrategia:")
    print(f"   Signal: {signal_result.get('signal', 'N/A')}")
    
    if 'signal_data' in signal_result:
        signal_data = signal_result['signal_data']
        print(f"\n✅ Datos de la señal:")
        for key, value in signal_data.items():
            print(f"   - {key:20s}: {value}")
    
    # 4.4 Validar que la señal es uno de los valores esperados
    valid_signals = ['BUY', 'SELL', 'HOLD']
    if signal_result['signal'] not in valid_signals:
        print(f"❌ ERROR: Señal '{signal_result['signal']}' no reconocida")
        print(f"   Esperado uno de: {valid_signals}")
        return False
    
    print(f"\n✅ Señal válida: {signal_result['signal']}")
    
    # 4.5 Validar valores de la señal (si es BUY/SELL)
    if signal_result['signal'] in ['BUY', 'SELL']:
        sd = signal_result['signal_data']
        
        # entry_price > 0
        if sd.get('entry_price', 0) <= 0:
            print(f"❌ ERROR: entry_price inválido: {sd.get('entry_price')}")
            return False
        
        # position_size > 0
        if sd.get('position_size', 0) <= 0:
            print(f"❌ ERROR: position_size inválido: {sd.get('position_size')}")
            return False
        
        # SL y TP válidos según dirección
        if signal_result['signal'] == 'BUY':
            if sd.get('stop_loss_price', 0) >= sd.get('entry_price', float('inf')):
                print(f"❌ ERROR: SL >= entry en BUY")
                return False
            if sd.get('take_profit_price', 0) <= sd.get('entry_price', 0):
                print(f"❌ ERROR: TP <= entry en BUY")
                return False
        else:  # SELL
            if sd.get('stop_loss_price', 0) <= sd.get('entry_price', 0):
                print(f"❌ ERROR: SL <= entry en SELL")
                return False
            if sd.get('take_profit_price', 0) >= sd.get('entry_price', float('inf')):
                print(f"❌ ERROR: TP >= entry en SELL")
                return False
        
        print(f"✅ Parámetros de señal válidos")
    
    print("\n✅ VALIDACIÓN 4 COMPLETADA")
    return True
```

---

## 🐛 Troubleshooting: Problemas Comunes

### Problema 1: "get_live_data() retorna None"

```python
# DIAGNÓSTICO
def debug_get_live_data():
    print("Debugging get_live_data()...")
    
    # Paso 1: ¿MT5 conectado?
    if not mt5.initialize():
        print("❌ MT5 NO inicializado")
        return
    
    # Paso 2: ¿Símbolo existe?
    sym_info = mt5.symbol_info('Volatility 75 Index')
    if sym_info is None:
        print("❌ Símbolo NO encontrado")
        print("   Intenta: mt5.symbols_get()")
        return
    
    # Paso 3: ¿Timeframe válido?
    tf_map = {
        '1m': mt5.TIMEFRAME_M1,
        '5m': mt5.TIMEFRAME_M5,
        '15m': mt5.TIMEFRAME_M15,
        '1h': mt5.TIMEFRAME_H1,
    }
    if '15m' not in tf_map:
        print("❌ Timeframe NO válido")
        return
    
    # Paso 4: ¿Llamada a MT5 OK?
    rates = mt5.copy_rates_from_pos('Volatility 75 Index', mt5.TIMEFRAME_M15, 0, 200)
    if rates is None:
        print(f"❌ MT5 retornó None")
        print(f"   Error: {mt5.last_error()}")
        return
    
    if len(rates) == 0:
        print("❌ MT5 retornó array vacío")
        return
    
    print(f"✅ MT5 retornó {len(rates)} barras")
    print(f"   Primera barra: {rates[0]}")
    print(f"   Última barra:  {rates[-1]}")

debug_get_live_data()
```

---

### Problema 2: "DataFrame tiene NaN después de preparación"

```python
# DIAGNÓSTICO
def debug_nan_values(df_prep):
    print("Debugging valores NaN...")
    
    nan_cols = df_prep.columns[df_prep.isna().any()].tolist()
    
    if not nan_cols:
        print("✅ Sin NaN")
        return
    
    print(f"❌ {len(nan_cols)} columnas con NaN:")
    for col in nan_cols:
        nan_count = df_prep[col].isna().sum()
        nan_indices = df_prep[df_prep[col].isna()].index.tolist()
        
        print(f"\n   {col}:")
        print(f"   - Cantidad NaN: {nan_count}")
        print(f"   - Índices: {nan_indices[:5]}...")
        print(f"   - Posibles causas:")
        
        # Si es EMA o indicador que necesita warmup
        if col in ['ema_10', 'ema_20', 'ema_200']:
            print(f"     → Indicador necesita ~{col.split('_')[1]} barras para calentar")
        
        # Si es SAR
        elif col == 'sar':
            print(f"     → SAR necesita 5+ barras para inicializar")
        
        # Si es MACD
        elif col in ['macd', 'macd_signal']:
            print(f"     → MACD necesita 26+ barras para inicializar")
        
        # Si es ADX
        elif col == 'adx':
            print(f"     → ADX necesita 14+ barras para inicializar")
        
        # Si es indicador ML
        elif col in ['volume_ratio', 'price_position', 'trend_strength', 'returns']:
            print(f"     → Feature ML: revisar cálculo en add_indicators()")

# Uso:
debug_nan_values(df_prep)
```

---

### Problema 3: "Señal ML siempre HOLD"

```python
# DIAGNÓSTICO
def debug_ml_always_hold():
    print("Debugging ML siempre retorna HOLD...")
    
    # 1. ¿Modelo cargado?
    if strategy.model is None:
        print("❌ Modelo NO cargado")
        print("   Verifica que existe: models/model.pkl")
        return
    
    # 2. ¿Features correctas?
    df = data_provider.get_live_data('Volatility 75 Index', '15m', 200)
    df_prep = orchestrator._prepare_data(df)
    
    expected_features = 25
    if len(strategy.feature_names) != expected_features:
        print(f"❌ Cantidad de features: {len(strategy.feature_names)} (esperado: {expected_features})")
        return
    
    # 3. ¿Predicción del modelo?
    features_last_row = df_prep[strategy.feature_names].iloc[-1].values
    prediction = strategy.model.predict([features_last_row])
    probabilities = strategy.model.predict_proba([features_last_row])
    
    print(f"✅ Predicción del modelo: {prediction[0]}")
    print(f"   Probabilidades: BUY={probabilities[0][0]:.2f}, SELL={probabilities[0][1]:.2f}")
    
    # 4. ¿Condiciones son muy estrictas?
    print(f"\n✅ Evaluación de condiciones:")
    print(f"   - trend_bearish (SELL): {df_prep['trend_bearish'].iloc[-1]}")
    print(f"   - trend_bullish (BUY): {df_prep['trend_bullish'].iloc[-1]}")
    print(f"   - rsi_ok_sell: {df_prep['rsi'].iloc[-1] < 50}")
    print(f"   - rsi_ok_buy: {df_prep['rsi'].iloc[-1] > 50}")
    print(f"   - ml_confidence: {probabilities[0].max():.2f}")
    print(f"   - threshold: 0.50")
    
    if probabilities[0].max() < 0.50:
        print(f"\n   ⚠️  CAUSA: Confianza del modelo < 0.50")
        print(f"      Soluciones:")
        print(f"      1. Reducir threshold en config.yaml")
        print(f"      2. Re-entrenar modelo con más datos")
        print(f"      3. Ajustar condiciones de entrada")

debug_ml_always_hold()
```

---

## 📈 Script de Validación Completo

```python
#!/usr/bin/env python3
"""
Validación completa del flujo: 200 barras → indicadores → señal
Ejecutar: python validate_live_flow.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Agregar rutas
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_validations():
    """Ejecuta todas las validaciones en secuencia"""
    
    print("\n" + "="*70)
    print("🔍 VALIDACIÓN COMPLETA: FLUJO DE 200 BARRAS 15M")
    print("="*70)
    
    validations = [
        ("Conexión MT5", validate_mt5_connection),
        ("Carga de 200 barras", validate_get_live_data),
        ("Preparación de datos", validate_prepare_data),
        ("Señal ML", validate_ml_signal),
    ]
    
    results = []
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            results.append((name, f"❌ ERROR: {str(e)[:50]}"))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE VALIDACIONES")
    print("="*70)
    
    for name, result in results:
        status_icon = "✅" if "PASS" in result else "❌"
        print(f"{status_icon} {name:30s} {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} validaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡SISTEMA VALIDADO! Todo funciona correctamente.")
        return True
    else:
        print(f"\n⚠️  {total - passed} validaciones fallaron. Revisar logs arriba.")
        return False

if __name__ == "__main__":
    success = run_all_validations()
    sys.exit(0 if success else 1)
```

---

## ✅ Validación Rápida (5 segundos)

```python
# Script de validación ultra rápida
def quick_validation():
    """Validación rápida de que 200 barras se cargan correctamente"""
    
    print("⚡ Quick Validation (5s)...")
    
    # 1. Conectar
    mt5.initialize()
    
    # 2. Cargar 200 barras
    df = data_provider.get_live_data('Volatility 75 Index', '15m', 200)
    
    # 3. Checks básicos
    checks = [
        ("DataFrame no None", df is not None),
        ("Shape correcto", df.shape == (200, 6)),
        ("Columnas correctas", list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']),
        ("Sin NaN", not df.isna().any().any()),
        ("Timestamps monótonos", df['timestamp'].is_monotonic_increasing),
        ("High >= Low", (df['high'] >= df['low']).all()),
    ]
    
    # 4. Mostrar resultados
    for check_name, check_result in checks:
        print(f"{'✅' if check_result else '❌'} {check_name}")
    
    # 5. Resumen
    all_pass = all(r for _, r in checks)
    print(f"\n{'✅ OK' if all_pass else '❌ FALLO'} - {'Sistema listo' if all_pass else 'Sistema con problemas'}")

quick_validation()
```

---

**Documento**: Debugging Completo  
**Versión**: v4.10  
**Status**: ✅ Listo para usar  
**Ubicación**: `descarga_datos/tests/validate_live_flow.py`
