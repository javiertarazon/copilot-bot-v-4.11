# 🤖 SISTEMA BOT ANTIGRAVITY - INSTRUCCIONES MAESTRAS v5.0

## 1. MISIÓN Y FILOSOFÍA DEL SISTEMA
Este es un sistema de trading algorítmico profesional diseñado para operar en derivados (Deriv MT5) y Crypto (Kraken/Binance).
**Objetivo Fundamental:** Rentabilidad consistente con Drawdown máximo < 15%.
**Filosofía:** "Data over Hype". Toda decisión de trading debe estar respaldada por ML (Machine Learning) entrenado en datos históricos reales.

## 2. ARQUITECTURA DEL SISTEMA
El sistema es modular y centralizado.

### Estructura de Directorios Clave (Root: `descarga_datos/`)
*   `main.py`: **ÚNICO PUNTO DE ENTRADA**. Gestiona CLI, configuración y arranque.
*   `strategies/`: Contiene la lógica de decisión. Archivo principal: `base_strategy.py` y `ultra_detailed_heikin_ashi_ml_strategy.py`.
*   `backtesting/`: Motor de simulación personalizado (`backtester.py`).
*   `execution/` (o lógica integrada): Manejo de órdenes MT5/CCXT.
*   `models/`: Gestión de modelos ML (.pkl, .onnx).
*   `data/`: Almacenamiento SQLite/Parquet (No CSV para producción).

## 3. ESTÁNDARES DE CÓDIGO (COPILOT INSTRUCTIONS)
Al generar código para este proyecto, sigue estrictamente estas reglas:

1.  **Centralización:** No crees scripts sueltos. Todo debe ejecutarse a través de `main.py` o ser un módulo importable.
2.  **Manejo de Errores:** Usa bloques `try/except` robustos. Loggea errores críticos (Error 10027, desconexiones) con `utils.logger`.
3.  **No Mocking en Producción:** Nunca uses datos simulados (`random`, `mock`) para lógica de trading en vivo.
4.  **Type Hinting:** Usa tipos explícitos (`def funcion(a: int) -> bool:`).
5.  **Paths Absolutos:** Usa `pathlib` u `os.path` referenciando siempre desde la raíz del proyecto para evitar errores de "File not found".

## 4. PROTOCOLOS DE OPERACIÓN

### A. Fase de Entrenamiento (Machine Learning)
1.  Descarga de datos históricos (`main.py --download`).
2.  Generación de features (Indicadores Técnicos). **CRÍTICO:** `prepare_features` debe ser idéntico en entrenamiento y predicción.
3.  Entrenamiento de modelos (Random Forest / XGBoost).

### B. Fase de Backtesting
1.  Ejecutar `main.py --backtest`.
2.  Validar métricas: Win Rate > 55%, Profit Factor > 1.5.
3.  Si falla: **NO PASAR A LIVE**. Optimizar hiperparámetros.

### C. Fase Live (Trading en Vivo)
1.  Verificar conexión MT5 (Diagnóstico de inicio).
2.  Cargar modelos pre-entrenados/validados.
3.  Ejecutar bucle de trading (ciclo 5s).

## 5. PUNTOS CRÍTICOS DE MANTENIMIENTO
*   **Feature Parity:** Asegurar que `indicators.technical_indicators` genere los mismos valores en backtest y live.
*   **Data Leakage:** Revisar que el entrenamiento ML no use datos futuros.
*   **Gestión de Riesgo:** El `AdvancedRiskManager` es la autoridad final. Si dice "No trade", no se opera.

---
**Generado por GitHub Copilot para Proyecto Bot Antigravity**
