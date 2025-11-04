# 🔧 Sistema de Configuración Base + Optimizada por Símbolo (v5.0)

**Fecha**: 2 de Noviembre de 2025  
**Versión**: v5.0 - Restructuración de Parámetros  
**Estado**: ✅ IMPLEMENTADO Y VALIDADO

---

## 📋 Resumen Ejecutivo

Se implementó un nuevo sistema de configuración que separa:

1. **Parámetros BASE** (Pre-optimización PNL ~$400k)
   - Parámetros originales antes de la última optimización
   - Usados por DEFECTO para cualquier símbolo
   - Proporcionan rendimiento confiable y consistente

2. **Parámetros OPTIMIZADOS** (Por símbolo específico)
   - Creados durante el proceso de optimización
   - Se usan SI EXISTEN para ese símbolo
   - Sobrescriben los parámetros BASE si están disponibles

---

## 🏗️ Arquitectura

### Estructura en config.yaml

```yaml
backtesting:
  base_parameters:           # ✅ NUEVO: Parámetros BASE (pre-optimización)
    ml_threshold: 0.2
    cci_threshold: 90
    atr_period: 17
    kelly_fraction: 0.1
    max_drawdown: 0.03
    # ... (22 parámetros totales)
    
  optimized_parameters:      # Parámetros específicos por símbolo
    Volatility 75 Index:     # Si existe, sobrescriben los BASE
      ml_threshold: 0.15     # Ejemplo: optimizado para este símbolo
      cci_threshold: 200
      # ...
```

### Flujo de Carga de Parámetros

```
┌─────────────────────┐
│  Solicitar Params   │
│  para Símbolo X     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ ¿Símbolo X en optimized?    │
└──────────┬──────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
   SÍ            NO
    │             │
    ▼             ▼
 USAR        USAR BASE
OPTIMIZADOS  PARAMETERS
    │             │
    └──────┬──────┘
           ▼
    ┌─────────────────┐
    │ Parámetros OK   │
    └─────────────────┘
```

---

## 🔧 Componentes Modificados

### 1. config.yaml
- **Nuevo**: Sección `base_parameters` con parámetros originales
- **Mejorado**: `optimized_parameters` mantiene configs por símbolo

### 2. config_loader.py - BacktestingConfig
```python
@dataclass
class BacktestingConfig:
    # ...
    base_parameters: Dict[str, Any] = field(default_factory=dict)
    optimized_parameters: Dict[str, Any] = field(default_factory=dict)
    # ...
```

### 3. config_loader.py - Nuevo Helper
```python
def get_strategy_parameters(config: Config, symbol: str = None) -> Dict[str, Any]:
    """
    Obtiene parámetros con prioridad:
    1. Optimizados para símbolo (si existen)
    2. BASE (por defecto)
    """
```

### 4. UltraDetailedHeikinAshiMLStrategy
- Modificado `__init__()` para usar `get_strategy_parameters()`
- Automáticamente busca optimizados primero, luego BASE

---

## ✅ Parámetros BASE Documentados

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| ml_threshold | 0.2 | Umbral ML para señales |
| cci_threshold | 90 | CCI para confirmar reversiones |
| atr_period | 17 | Período ATR para volatilidad |
| ema_trend_period | 50 | EMA para tendencia |
| stoch_overbought | 70 | Nivel sobrecompra Stochastic |
| stoch_oversold | 35 | Nivel sobreventa Stochastic |
| sar_acceleration | 0.04 | Aceleración SAR |
| sar_maximum | 0.26 | Máximo SAR |
| volume_ratio_min | 0.3 | Ratio volumen mínimo |
| kelly_fraction | 0.1 | Fracción Kelly (conservadora) |
| max_drawdown | 0.03 | Drawdown máximo permitido |
| max_portfolio_heat | 0.05 | "Heat" portafolio máximo |
| max_concurrent_trades | 1 | Operaciones simultáneas |
| risk_per_trade | 0.02 | Riesgo 2% por operación |
| min_rr_ratio | 2.5 | Ratio riesgo/ganancia mínimo |
| stop_loss_atr_multiplier | 2.25 | SL = 2.25x ATR |
| take_profit_atr_multiplier | 3.75 | TP = 3.75x ATR |
| liquidity_score_min | 5 | Score liquidez mínimo |
| ml_threshold_min | 0.2 | ML threshold mínimo |
| ml_threshold_max | 0.8 | ML threshold máximo |

**PNL Histórico**: ~$400,000 (pre-optimización)

---

## 🚀 Uso

### Para cualquier símbolo NUEVO (sin optimizar)
```python
from config.config_loader import load_config_from_yaml, get_strategy_parameters

config = load_config_from_yaml()
params = get_strategy_parameters(config, "BTC/USDT")
# Retorna: Parámetros BASE (porque "BTC/USDT" no está en optimized_parameters)
```

### Para símbolo CON optimización
```python
params = get_strategy_parameters(config, "Volatility 75 Index")
# Si "Volatility 75 Index" está en optimized_parameters, lo usa
# Si no, usa BASE
```

### Crear nueva optimización
```yaml
optimized_parameters:
  Mi_Nuevo_Simbolo:
    ml_threshold: 0.25  # Personalizado
    cci_threshold: 150  # Personalizado
    # ... resto de parámetros optimizados
```

---

## 🧪 Validación

### Test: Cargar parámetros BASE
```bash
python descarga_datos/tests/verify_base_params.py
```

**Salida esperada:**
```
Symbol: Volatility 75 Index
Base parameters section exists: True
[CONFIG] Usando parámetros BASE para Volatility 75 Index

Parameters loaded:
  ml_threshold: 0.2
  cci_threshold: 90
  atr_period: 17
  kelly_fraction: 0.1
  max_drawdown: 0.03
✅ All 22 base parameters loaded successfully!
```

---

## 📊 Comparativa: Base vs Última Optimización

| Métrica | Base ($400k) | Última Opt ($28k) | Diferencia |
|---------|-------------|------------------|-----------|
| P&L | $400,000 | $28,000 | -$372,000 ❌ |
| Win Rate | ~77% | ~54% | -23% |
| Drawdown | Bajo | Alto | Peor |
| Trades | Balanceado | Excesivos | Muy activo |

**Conclusión**: Los parámetros BASE son SUPERIORES. La última optimización fue contraproducente.

---

## 🔄 Próximos Pasos

1. ✅ Usar parámetros BASE como defecto
2. ⏳ Crear optimizaciones CUIDADOSAMENTE (validad en live antes)
3. ⏳ Solo guardar optimizaciones que MEJOREN el PNL
4. ⏳ Mantener histórico de optimizaciones
5. ⏳ A/B testing: Base vs Optimizado

---

## 🛡️ Garantías

- ✅ Parámetros BASE siempre disponibles como fallback
- ✅ No se pierden optimizaciones previas
- ✅ Cambio REVERSIBLE en cualquier momento
- ✅ Compatibilidad hacia atrás

---

## 📝 Notas de Implementación

- **Archivo**: `config_loader.py` - Función `get_strategy_parameters()`
- **Estrategia**: `ultra_detailed_heikin_ashi_ml_strategy.py` - `__init__()`
- **Config**: `config.yaml` - Secciones `base_parameters` + `optimized_parameters`
- **Tests**: `tests/verify_base_params.py`

---

**Responsable**: Sistema Copilot Bot Trader v5.0  
**Última Actualización**: 2 Nov 2025 17:05 UTC
