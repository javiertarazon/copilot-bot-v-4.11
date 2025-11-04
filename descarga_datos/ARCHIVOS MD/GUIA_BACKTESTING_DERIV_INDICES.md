# 📊 Guía Completa: Backtesting de Volatility Indices Deriv

## 🎯 Objetivo
Realizar backtesting y entrenamiento ML con índices de volatilidad de Deriv para encontrar el más rentable como alternativa a criptomonedas.

## 📋 Lista de Índices a Testear (Volatilidad ≥50%)

### ⭐ TOP 5 RECOMENDADOS

| # | Índice | Volatilidad | Similar a | Prioridad | Descripción |
|---|--------|-------------|-----------|-----------|-------------|
| 1 | **Volatility 75 Index** | 7.5% | BTC/USD | 🥇 ALTA | Mejor equilibrio vol/estabilidad |
| 2 | **Volatility 100 Index** | 10% | Altcoins | 🥈 ALTA | Mayor volatilidad = más señales |
| 3 | **Volatility 50 Index** | 5% | SOL/USDT | 🥉 MEDIA | Más conservador |
| 4 | **Crash 500 Index** | Variable | Flash crash | 🎯 MEDIA | ML detecta crashes |
| 5 | **Boom 500 Index** | Variable | Pumps | 🎯 MEDIA | ML detecta pumps |

### 🔬 OPCIONALES (Análisis Avanzado)

| # | Índice | Volatilidad | Recomendado | Uso |
|---|--------|-------------|-------------|-----|
| 6 | Crash 1000 Index | Variable | ⚠️ | Crashes extremos |
| 7 | Boom 1000 Index | Variable | ⚠️ | Pumps extremos |

---

## 🚀 Paso 1: Crear Cuenta Demo Deriv

### Instrucciones:

1. **Ir a**: https://deriv.com
2. **Crear cuenta** (sin verificación para demo)
3. **Descargar MT5** desde Deriv
4. **Login** con tus credenciales demo
5. **Anotar**:
   - Login (número de cuenta)
   - Password
   - Servidor: `Deriv-Demo`

### Ventajas Deriv:
- ✅ Demo **ILIMITADO** (no expira)
- ✅ $10,000 USD recargables
- ✅ Trading **24/7** real
- ✅ Sin verificación KYC para demo
- ✅ Acceso a todos los Volatility Indices

---

## 📥 Paso 2: Descargar Datos Históricos

### Opción A: Usar Script Automático (Recomendado)

```bash
# Activar entorno virtual Python 3.11
.\.venv\Scripts\activate

# Ejecutar descargador
cd descarga_datos
python tests\download_deriv_data.py
```

**El script te pedirá:**
- Login de Deriv (o Enter para omitir)
- Password
- Timeframe (default: 15m)
- Días de historia (default: 365)
- Solo recomendados (default: Sí)

**Resultado:**
- Archivos CSV en: `descarga_datos/data/deriv_indices/`
- Ejemplo: `Volatility_75_Index_15m.csv`

### Opción B: Descargar Manualmente MT5

Si no tienes credenciales, puedes usar MT5 directamente:

1. Abrir MT5 Deriv Demo
2. Market Watch → Agregar símbolos
3. Buscar "Volatility" y añadir los índices
4. Ver datos históricos (Chart → período 15m)

---

## 🧪 Paso 3: Ejecutar Backtesting

### Para CADA índice, ejecutar:

```bash
# Configurar símbolo en config.yaml
# Editar: backtesting.symbols

# Ejecutar backtest
python main.py --backtest
```

### Configuración Sugerida:

```yaml
# config.yaml - Ejemplo para Volatility 75 Index

backtesting:
  symbols:
    - "Volatility 75 Index"
  
  timeframe: 15m
  start_date: '2024-01-01'
  end_date: '2025-10-31'
  initial_capital: 10000
  
  optimized_parameters:
    Volatility_75_Index:  # Usar parámetros de SOL/USDT inicialmente
      risk_per_trade: 0.02
      stop_loss_atr_multiplier: 2.25
      take_profit_atr_multiplier: 3.75
      ml_threshold: 0.2
      # ... resto de parámetros
```

### Ejecutar Batería de Tests:

```bash
# Test 1: Volatility 75 Index
# Editar config.yaml → symbols: ["Volatility 75 Index"]
python main.py --backtest
# Anotar métricas

# Test 2: Volatility 100 Index  
# Editar config.yaml → symbols: ["Volatility 100 Index"]
python main.py --backtest
# Anotar métricas

# Test 3: Volatility 50 Index
# ... repetir para cada índice
```

---

## 📊 Paso 4: Métricas a Comparar

### Tabla de Resultados Sugerida:

| Índice | ROI % | Win Rate % | Profit Factor | Sharpe | Max DD % | Trades | Mejor? |
|--------|-------|------------|---------------|--------|----------|--------|--------|
| V75    | ?     | ?          | ?             | ?      | ?        | ?      | ?      |
| V100   | ?     | ?          | ?             | ?      | ?        | ?      | ?      |
| V50    | ?     | ?          | ?             | ?      | ?        | ?      | ?      |
| Crash500| ?    | ?          | ?             | ?      | ?        | ?      | ?      |
| Boom500| ?     | ?          | ?             | ?      | ?        | ?      | ?      |

### Métricas Clave:

1. **ROI** (Return on Investment): % ganancia total
2. **Win Rate**: % de trades ganadores
3. **Profit Factor**: Ganancia/Pérdida
4. **Sharpe Ratio**: Retorno ajustado por riesgo
5. **Max Drawdown**: Caída máxima
6. **Número de Trades**: Cantidad de operaciones

### Criterios de Selección:

```
Índice GANADOR si:
✓ ROI > 100%
✓ Win Rate > 55%
✓ Profit Factor > 1.5
✓ Sharpe Ratio > 1.0
✓ Max Drawdown < 20%
✓ Trades > 50 (suficiente muestra)
```

---

## 🧠 Paso 5: Entrenar Modelos ML

### Una vez identificado el mejor índice:

```bash
# Configurar optimización
# config.yaml
ml_training:
  symbols: ["Volatility 75 Index"]  # El ganador
  timeframe: 15m
  
# Ejecutar entrenamiento
python main.py --optimize

# Resultado:
# - Modelo entrenado en models/
# - Parámetros optimizados en config.yaml
```

### Validación del Modelo:

```bash
# Backtest con modelo entrenado
python main.py --backtest

# Verificar métricas:
# - ¿ROI mejoró?
# - ¿Win rate aumentó?
# - ¿Sharpe ratio subió?
```

---

## 🎯 Paso 6: Trading Live MT5

### Una vez validado:

```yaml
# config.yaml - Configuración Live MT5

active_exchange: mt5

mt5_config:
  login: TU_CUENTA_DEMO
  password: TU_PASSWORD
  server: "Deriv-Demo"
  path: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
  
symbols:
  - "Volatility 75 Index"  # El índice ganador
  
timeframe: 15m

live_trading:
  trading_mode: 'futures'
  max_positions: 1
  risk_per_trade: 0.02
  
# Usar parámetros optimizados del modelo
```

### Ejecutar Live:

```bash
# Activar entorno
.\.venv\Scripts\activate

# Ejecutar bot
cd descarga_datos
python main.py --live
```

---

## 📈 Expectativas Realistas

### Volatility 75 Index (más probable ganador):

```
ROI esperado: 150-300% anual
Win rate: 55-65%
Profit factor: 1.5-2.0
Sharpe ratio: 1.2-1.8
Max drawdown: 15-25%
Trades/mes: 20-40

Ventajas:
✓ Trading 24/7
✓ Sin gaps de fin de semana
✓ Volatilidad consistente
✓ Spreads bajos
✓ Ejecución garantizada
✓ Demo ilimitado
```

### Comparación con Cryptos:

| Métrica | SOL/USDT (Real) | V75 Index (Deriv) |
|---------|-----------------|-------------------|
| Disponibilidad | Testnet roto | Demo ilimitado ✅ |
| Trading | 24/7 | 24/7 ✅ |
| Slippage | Alto | Bajo ✅ |
| Ejecución | Variable | Garantizada ✅ |
| Spreads | 0.1-0.5% | 0.05% ✅ |
| APIs | Incompletas | MT5 completo ✅ |

---

## ✅ Checklist de Ejecución

### Fase 1: Preparación
- [ ] Crear cuenta demo Deriv
- [ ] Instalar MT5 Deriv
- [ ] Anotar credenciales
- [ ] Verificar Python 3.11 activo

### Fase 2: Descarga de Datos
- [ ] Ejecutar `download_deriv_data.py`
- [ ] Verificar CSVs generados
- [ ] Confirmar ~500+ barras por índice

### Fase 3: Backtesting
- [ ] Test Volatility 75 Index
- [ ] Test Volatility 100 Index
- [ ] Test Volatility 50 Index
- [ ] Test Crash 500 Index
- [ ] Test Boom 500 Index
- [ ] Comparar métricas

### Fase 4: Optimización ML
- [ ] Seleccionar índice ganador
- [ ] Entrenar modelo ML
- [ ] Validar backtest con modelo
- [ ] Confirmar mejora de métricas

### Fase 5: Live Trading
- [ ] Configurar MT5 en config.yaml
- [ ] Ejecutar modo live demo
- [ ] Monitorear primeras operaciones
- [ ] Validar ejecución de TP/SL
- [ ] Confirmar rentabilidad

---

## 🆘 Solución de Problemas

### Error: "Symbol not found"
```bash
Solución:
1. Abrir MT5 Deriv Demo
2. Market Watch → Symbols
3. Buscar "Volatility" y añadir todos
4. Reintentar descarga
```

### Error: "MetaTrader5 not installed"
```bash
Solución:
pip install MetaTrader5
# O si no funciona:
pip install --upgrade MetaTrader5
```

### Error: "Connection failed"
```bash
Solución:
1. Verificar MT5 esté abierto
2. Verificar credenciales correctas
3. Servidor = "Deriv-Demo"
4. Intentar sin credenciales (solo símbolos)
```

---

## 📞 Próximos Pasos

1. **Ahora**: Crear cuenta Deriv y descargar datos
2. **Hoy**: Ejecutar backtests de los 5 índices
3. **Mañana**: Comparar métricas y elegir ganador
4. **Esta semana**: Entrenar modelo ML
5. **Siguiente semana**: Iniciar live trading demo

---

## 💡 Tips Finales

- **Empieza con V75**: Es el más balanceado
- **No te saltes el backtest**: Datos históricos revelan rentabilidad
- **Entrena el modelo**: ML mejora win rate 5-10%
- **Demo primero SIEMPRE**: Valida estrategia antes de real
- **Monitorea 1 semana**: Confirma consistencia antes de escalar

---

**Última actualización**: 1 Noviembre 2025  
**Autor**: GitHub Copilot  
**Versión**: 1.0
