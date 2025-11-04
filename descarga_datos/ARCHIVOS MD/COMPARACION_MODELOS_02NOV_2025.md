# 🧪 Comparación de Modelos RandomForest - 02 Noviembre 2025

## Objetivo

Tenemos **6 modelos RandomForest** guardados en `models/Volatility 75 Index/`:
- RandomForest_20251102_090102.joblib
- RandomForest_20251102_162529.joblib
- RandomForest_20251102_162735.joblib
- RandomForest_20251102_194413.joblib
- RandomForest_20251102_195423.joblib
- RandomForest_20251102_200051.joblib

**Pregunta**: ¿Cuál de estos modelos genera el MAYOR P&L en backtest?

## Metodología

El script `utils/compare_all_models.py`:

1. Copia cada modelo al nombre estándar (`randomforest.pkl`)
2. Ejecuta: `python main.py --backtest-only`
3. Captura P&L del resultado
4. Compara todos los modelos

## Resultados Esperados

Formato:
```
[Rank] [Tiempo del modelo] [P&L] [Trades] [Win%]
1      09:01:02            $XXX  YYYY     ZZ.Z%
2      16:25:29            $YYY  ...      ...
...
```

## Análisis Preliminar de Metadata

Se analizaron los metadatos JSON de los 6 modelos:

| Timestamp | CV Mean | Val AUC | Val Accuracy | Val F1 |
|-----------|---------|---------|--------------|--------|
| 09:01:02  | 0.518272| 0.510445| 0.504180     | 0.571748|
| 16:25:29  | 0.507667| **0.522692** | 0.492320 | **0.597439** |
| 16:27:35  | 0.507667| **0.522692** | 0.492320 | **0.597439** |
| 19:44:13  | 0.507667| **0.522692** | 0.492320 | **0.597439** |
| 19:54:23  | 0.507667| **0.522692** | 0.492320 | **0.597439** |
| 20:00:51  | 0.507667| **0.522692** | 0.492320 | **0.597439** |

### Hallazgos:
- El modelo de 09:01:02 tiene mejor CV Mean pero peor AUC y F1
- Los últimos 5 modelos (16:25:29 a 20:00:51) tienen **métricas idénticas**
- Mejor modelo por validación: **16:25:29 y posteriores** (AUC=0.5227, F1=0.5974)

## Resultados de Backtests

### Ejecución 1: 2 Modelos Candidatos

Testeando:
1. **RandomForest_20251102_200051.joblib** (20:00:51 - Más reciente, mejor F1)
2. **RandomForest_20251102_090102.joblib** (09:01:02 - Primero)

**[Ejecutándose...]**

---

Duración aproximada: 3-5 minutos para 2 modelos
Directorio: `descarga_datos/`
Log: Ver terminal o `data/model_comparison_results/`

