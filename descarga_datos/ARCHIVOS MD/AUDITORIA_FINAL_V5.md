# Auditoría Técnica Integral y Plan de Optimización (v5.0)

**Fecha:** 26 de Enero, 2026
**Auditor:** Senior Quantitative Developer AI
**Versión del Sistema:** v4.11

## 1. Resumen Ejecutivo
El sistema presenta una arquitectura modular robusta con una clara separación de responsabilidades (Estrategia, Orquestación, Ejecución, Gestión de Riesgo). Sin embargo, la acumulación de capas de lógica defensiva ha creado **redundancias críticas** y **riesgos de inconsistencia** entre el Backtesting y el Live Trading. La estrategia de "Compensación" (tipo Martingala) representa el mayor riesgo de ruina si no se controla estrictamente.

## 2. Análisis Técnico Detallado

### A. Estructura y Código (Code Health)
*   **Redundancia Lógica (Critical):**
    *   **Trailing Stops:** Implementado en TRES lugares diferentes con lógica potencialmente conflictiva:
        1.  `UltraDetailedHeikinAshiMLStrategy.check_trailing_stop`: Lógica interna de la estrategia.
        2.  `LiveTradingOrchestrator.monitor_open_positions_for_tp_sl`: Monitor externo que cierra posiciones manualmente.
        3.  `MT5OrderExecutor.update_trailing_stops`: Modifica el SL nativo en MT5.
        *Riesgo:* Condiciones de carrera (Race Conditions) donde múltiples componentes intentan modificar/cerrar la misma posición, generando errores en logs o cierres prematuros.
    *   **Cálculo de Position Size:**
        *   Calculado en Estrategia (`_run_backtest`) y recalculado independientemente en `RiskManager.apply_risk_management`. Si la configuración difiere ligeramente, el Backtest no será representativo.

*   **Hardcoding y Configuración:**
    *   `mt5_order_executor.py`: Valores por defecto `max_risk_percent = 2.0`, `default_sl_pips = 50` hardcodeados en `__init__`.
    *   `live_trading_orchestrator.py`: Intervalos de sincronización (60s) y actualización (5s) hardcodeados en el código si no están en config.
    *   `risk_management.py`: Límites duros para cripto (`max_position_crypto = 0.001`) que pueden quedar obsoletos con cambios de precio.

### B. Consistencia Backtesting vs. Live
*   **Divergencia de Motores:**
    *   **Backtesting:** Utiliza el bucle interno de `UltraDetailedHeikinAshiMLStrategy._run_backtest`. Asume ejecución perfecta (o simulada simple).
    *   **Live:** Utiliza `LiveTradingOrchestrator` + `MT5OrderExecutor` + `AdvancedRiskManager`.
    *   *Hallazgo:* Aunque la estrategia intenta replicar la lógica (`_generate_live_signal_from_backtest_logic`), son implementaciones de código separadas. Cualquier cambio en una que no se replique en la otra rompe la validez del backtest.

*   **Look-ahead Bias:**
    *   No se detectó look-ahead bias obvio en la preparación de datos (`prepare_features`), ya que usa `shift` correctamente. Sin embargo, el uso de `compensación` inmediata (abrir reverso al cerrar) en la misma vela o inmediata siguiente asume liquidez y ejecución instantánea que podría no existir en alta volatilidad.

### C. Estrategia y Gestión de Riesgo
*   **Estrategia de Compensación (High Risk):**
    *   La lógica de abrir una posición inversa con factor de riesgo aumentado (`compensation_risk_factor`) inmediatamente después de una pérdida es una técnica de **Martingala**.
    *   *Riesgo:* En mercados en rango lateral (choppy), esto puede llevar a una "espiral de muerte" (pérdida -> reverso -> pérdida -> reverso mayor) vaciando la cuenta rápidamente.
    
*   **Risk Management Centralizado:**
    *   `AdvancedRiskManager` es una adición sólida, pero sus límites "duros" (ej. Max Drawdown) actúan como un "Kill Switch". Si el Backtest no simula este Kill Switch, los resultados son optimistas.

## 3. Plan de Acción (Roadmap)

### Fase 1: Limpieza y Consolidación (Inmediato)
1.  **Unificar Trailing Stop:**
    *   Decisión: Delegar el Trailing Stop EXCLUSIVAMENTE al `MT5OrderExecutor` (nivel nativo/más bajo) o al `LiveTradingOrchestrator` (nivel lógico).
    *   *Recomendación:* Desactivar la lógica de cierre manual en `Orchestrator` y dejar que `MT5OrderExecutor` gestione el SL dinámico en el exchange.
2.  **Centralizar Configuración de Riesgo:**
    *   Eliminar valores hardcodeados en `mt5_order_executor.py` y forzar la carga desde `config.yaml`.

### Fase 2: Sincronización Backtest-Live (Corto Plazo)
1.  **Refactorización de Estrategia:**
    *   Extraer la lógica de cálculo de señales y risk management de `_run_backtest` a métodos puros (stateless) compartidos que puedan ser llamados tanto por el Backtester como por el Orchestrator.
2.  **Validación de Compensación:**
    *   Añadir un límite estricto de "Intentos de Compensación Consecutivos" (ej. máx 1) en la configuración para evitar espirales de pérdida.

### Fase 3: Optimización (Medio Plazo)
1.  **Optimización de Hiperparámetros:**
    *   Utilizar el `Backtester` corregido para re-optimizar los parámetros de ATR y Factores de Compensación, ahora que la lógica es consistente.

## 4. Preguntas Técnicas para el Usuario

1.  **Política de Trailing Stop:** ¿Prefiere que el SL se mueva en el servidor del Broker (MT5 nativo, más seguro ante desconexiones) o que sea gestionado por el Bot (lógica oculta, más flexible)? Actualmente hay conflicto entre ambos.
2.  **Estrategia de Compensación:** ¿Es consciente del riesgo de ruina matemática de la estrategia de compensación en mercados laterales? ¿Autoriza limitar los intentos consecutivos a 1?
3.  **Límites Hardcodeados:** Los límites de `0.001 BTC` en `risk_management.py` parecen arbitrarios. ¿Desea reemplazarlos por un % dinámico del equity real?

---
*Fin del Informe de Auditoría*
