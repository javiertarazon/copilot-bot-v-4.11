# 📉 Guía: Curva de Drawdown en el Dashboard v4.7

## ¿Qué es Drawdown?

**Drawdown** es la pérdida máxima de capital desde el punto más alto (pico) hasta el punto más bajo en un período determinado.

```
Capital Progresivo:
$2000 ─────────┐
      │        │     Peak
$1900 │  ┌──┐  │
      │  │  └──┤─────
$1850 │  │     │
      │  │   Drawdown
$1800 │  │
      └──────────────
```

## Métricas del Dashboard

### 1. **Max Drawdown (%)**
- **Definición**: La pérdida más grande desde un pico hasta el siguiente valle
- **Valor en v4.7**: 3.69%
- **Interpretación**: En el peor momento, el capital cayó 3.69% desde su máximo
- **Importancia**: Indicador clave de riesgo del sistema

### 2. **DD Promedio (%)**
- **Definición**: Promedio de todos los drawdowns cuando existen
- **Valor en v4.7**: ~2.45%
- **Interpretación**: En promedio, las caídas son de 2.45%
- **Uso**: Medir riesgo típico vs excepcional

### 3. **% Trades DD**
- **Definición**: Porcentaje de trades ejecutados mientras hay drawdown
- **Valor en v4.7**: Variable según período
- **Interpretación**: Qué % del tiempo el sistema está "recuperándose"
- **Ideal**: Bajo (indica recuperación rápida)

### 4. **Calmar Ratio**
- **Definición**: ROI / Max Drawdown (mide calidad riesgo-recompensa)
- **Valor en v4.7**: 7.55
- **Fórmula**: Calmar Ratio = (ROI %) / (Max Drawdown %)
- **Interpretación**: Por cada 1% de drawdown, gana 7.55% de ROI
- **Benchmark**: 
  - > 3: Excelente
  - 1-3: Bueno
  - < 1: Pobre

## Cómo Leer la Gráfica de Drawdown

```
Curva de Drawdown (en el Dashboard):

0%  ───────────────────────────────  (Sin drawdown)
-1% │   ┌──┐
-2% │   │  └──┐
-3% │ ┌─┘     └─┐
    │ │        │
-4% │ │        └──── Max Drawdown (-3.69%)
    └─┴──────────────

Eje X: Número de Trade (0 a 2,962)
Eje Y: Drawdown (%)
Línea Naranja: Max Drawdown histórico (-3.69%)
```

### Interpretación:
- **Línea cerca de 0%**: Sistema recuperándose bien
- **Picos negativos**: Momentos de máxima presión
- **Área roja**: Visualización del riesgo en tiempo real

## Relación con Otras Métricas

| Métrica | Drawdown | Interpretación |
|---------|----------|----------------|
| Win Rate 79.4% | ✅ Baja (3.69%) | Excellent - gana mucho, pierde poco |
| ROI 1591% | ✅ Drawdown bajo | Sistema muy eficiente |
| Sharpe 4.44 | ✅ DD bajo | Riesgo-rendimiento excelente |
| Calmar 7.55 | ✅ Muy alto | Recuperación rápida del riesgo |

## Por Qué es Importante el Drawdown

### 1. **Medida de Riesgo Real**
- No es teórico, es histórico
- Muestra lo peor que puede pasar
- Ayuda a dormir tranquilo

### 2. **Prueba de Estrés**
- ¿Cuánto aguanta el sistema?
- ¿Se recupera de las caídas?
- ¿Es predecible?

### 3. **Confianza del Inversor**
- Max Drawdown 3.69% es muy bajo
- Significa: "Si pierdo, pierdo poco"
- Recuperación rápida (Calmar 7.55)

## Cálculo Técnico (para referencia)

```python
# Calcular Drawdown
equity = [capital_inicial]
for trade in trades:
    equity.append(equity[-1] + trade.pnl)

# Running Maximum (pico histórico)
running_max = np.maximum.accumulate(equity)

# Drawdown en cada punto
drawdown = (equity - running_max) / running_max * 100

# Max Drawdown
max_drawdown = np.min(drawdown)  # Más negativo
```

## Comparación: Sistema v4.7 vs Benchmarks

```
Métrica            v4.7    Benchmark  Evaluación
──────────────────────────────────────────────
Max Drawdown      3.69%    5-10%      ✅ EXCELENTE
DD Promedio       2.45%    2-4%       ✅ BUENO
Calmar Ratio      7.55     1-3        ✅ EXCELENTE
Recovery Time     Rápida   Variable   ✅ BUENO
```

## Recomendaciones para Live Trading

1. **Monitoreo Diario**: Revisar gráfico de drawdown cada día
2. **Alerta**: Si Max DD sobrepasa 5%, revisar estrategia
3. **Límite**: Configurar stop-loss si DD > 10%
4. **Expectativa**: Esperar DD de 3-5% normalmente

## Conclusión

**El Drawdown de 3.69% es EXCELENTE para un sistema de trading**, especialmente con:
- ROI de 1591%
- Win Rate de 79.4%
- Calmar Ratio de 7.55

Esto significa que el sistema:
✅ Gana mucho (1591% ROI)
✅ Pierde poco (3.69% Max DD)
✅ Se recupera rápido (Calmar 7.55)
✅ Es estable y predecible

---

**Dashboard v4.7**: Curva de Drawdown disponible en http://localhost:8519
