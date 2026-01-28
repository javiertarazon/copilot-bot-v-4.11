# INFORME DE PRUEBA: ESTRATEGIA DE RECUPERACIÓN (BREAKEVEN)

## 1. Contexto de la Prueba
- **Objetivo**: Probar si una estrategia de "Reversal Inmediato" con objetivo moderado (solo recuperar la pérdida = Breakeven) funciona mejor que la versión agresiva.
- **Hipótesis**: Al reducir el Take Profit (TP) solo a la distancia necesaria para recuperar la pérdida, la operación debería cerrar más rápido y evitar reversiones del mercado.

## 2. Implementación Técnica
- Se modificó `UltraDetailedHeikinAshiMLStrategy` para calcular el TP dinámicamente:
  - `loss_to_recover = abs(pnl) * 1.01` (Recuperar pérdida + 1% gastos).
  - `TP_Distance = loss_to_recover / position_size`.
- **Corrección de Bug**: Se detectó que operaciones en "Breakeven" (pérdida $0) estaban activando reversiones innecesarias, generando solo gastos de comisión. Se añadió un filtro (`pnl < -2.0 USD`) para activar la recuperación solo en pérdidas reales.

## 3. Resultados Comparativos

| Escenario | Estrategia | P&L Final | Win Rate | Resultado |
|-----------|------------|-----------|----------|-----------|
| **Fase 2 (Base)** | High WR + Smart BE | **+$1,576.53** | **62%** | ✅ ÓPTIMO |
| **Test A** | Reversal Agresivo (1.0 ATR) | -$953.76 | 13% | ❌ FALLIDO |
| **Test B** | **Reversal Breakeven (Actual)**| **-$490.96** | **23%** | ❌ MEJORÓ PERO PIERDE |

## 4. Análisis del Fallo
1. **Whipsaw de Mercado**: El mercado actual muestra alta volatilidad lateral. Cuando una operación toca Stop Loss y revertimos inmediatamente, el precio a menudo se gira de nuevo, tocando el Stop Loss de la operación de recuperación.
2. **Impacto Negativo**: Aunque el "Breakeven Reversal" perdió menos que el agresivo (reducción de pérdidas del 50%), sigue destruyendo la rentabilidad de la estrategia base (pasó de +$1500 a -$490).
3. **Double Jeopardy**: Intentar recuperar una pérdida inmediatamente expone la cuenta a una "doble pérdida" en condiciones de rango.

## 5. Recomendación
**Descartar la lógica de Compensación/Reversal inmediata para este activo.**
La estrategia **Fase 2 (High Win Rate + Smart Breakeven)** es superior robustamente. Intentar "forzar" la recuperación de pérdidas está convirtiendo un sistema ganador en uno perdedor.

### Próximos Pasos Sugeridos
1. Revertir a la configuración de la **Fase 2** (Profit estimado: $1,500+).
2. Enfocarse en la **Fase 4 (ONNX)** para optimizar la velocidad de ejecución, o **Fase 5 (Multi-Símbolo)** para diversificar el riesgo, en lugar de intentar arreglar las pérdidas individuales con martingala/reversión.
