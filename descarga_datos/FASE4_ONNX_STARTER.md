# 🚀 FASE 4: ONNX ML Implementation Starter

## Quick Integration Guide

### Paso 1: Instalar ONNX (5 minutos)

```bash
pip install onnx onnxruntime skl2onnx onnxmltools
python -c "import onnxruntime; print(f'ONNX Runtime {onnxruntime.__version__} ready')"
```

### Paso 2: Convertir Modelo (10 minutos)

**Script**: `convert_model_to_onnx.py`

```python
from v411_optimizations.onnx_model_predictor import SklearnToONNXConverter
import pickle
import logging

logging.basicConfig(level=logging.INFO)

# Cargar modelo sklearn actual
with open('models/rf_model.pkl', 'rb') as f:
    rf_model = pickle.load(f)

# Convertir a ONNX
success = SklearnToONNXConverter.convert_random_forest(
    rf_model,
    n_features=25,
    output_path='models/rf_model.onnx',
    optimize=True
)

if success:
    print("✅ Model converted successfully")
    import os
    size_pkl = os.path.getsize('models/rf_model.pkl') / 1024 / 1024
    size_onnx = os.path.getsize('models/rf_model.onnx') / 1024 / 1024
    print(f"   Size: {size_pkl:.1f}MB (pickle) → {size_onnx:.1f}MB (ONNX)")
else:
    print("❌ Conversion failed")
```

**Ejecutar**:
```bash
python convert_model_to_onnx.py
```

### Paso 3: Integrar ONNX Predictor (10 minutos)

**Archivo**: `strategies/ultra_detailed_heikin_ashi_ml_strategy.py`

**Agregar en __init__**:
```python
from v411_optimizations.onnx_model_predictor import create_predictor

class UltraDetailedHeikinAshiML:
    def __init__(self, config):
        # Antes: self.model = pickle.load('models/rf_model.pkl')
        # Después:
        self.ml_predictor = create_predictor(
            'models/rf_model.onnx',
            use_cuda=True  # Si disponible
        )
        logger.info("✅ ONNX ML model loaded")
```

**Reemplazar prediction**:
```python
def get_live_signal(self, features):
    """Get BUY/SELL/HOLD signal from ONNX model."""
    # Antes: prediction = self.model.predict([features])
    # Después:
    prediction = self.ml_predictor.predict(features)  # 1ms vs 20ms
    return prediction[0][0]
```

### Paso 4: Validación Cruzada (10 minutos)

```python
# Generar 100 features
import numpy as np
features_batch = np.random.rand(100, 25).astype(np.float32)

# Comparar predicciones
from sklearn.ensemble import RandomForestClassifier
import pickle

# Cargar modelos
with open('models/rf_model.pkl', 'rb') as f:
    sklearn_model = pickle.load(f)

from v411_optimizations.onnx_model_predictor import ONNXModelPredictor
onnx_model = ONNXModelPredictor('models/rf_model.onnx')

# Predicciones
sklearn_pred = sklearn_model.predict(features_batch)
onnx_pred = onnx_model.predict_batch(features_batch).flatten().astype(int)

# Validar match
match = np.allclose(sklearn_pred, onnx_pred)
accuracy = (sklearn_pred == onnx_pred).sum() / len(sklearn_pred)

print(f"Match: {match}, Accuracy: {accuracy*100:.1f}%")
# Esperado: Match: True, Accuracy: 100.0%
```

### Paso 5: Tests (5 minutos)

```bash
pytest tests/test_v411_optimizations.py::TestONNXModel -v
```

**Output esperado**:
```
test_mock_predictor_creation PASSED   [ 33%]
test_mock_predictor_inference PASSED  [ 67%]
test_batch_prediction PASSED          [100%]

====== 3 passed in 0.05s ======
```

### Paso 6: Live Validation (24 horas)

```bash
python main.py --live
```

**Monitorear**:
- Predicciones correctas
- Timing mejorado
- P&L accuracy

### Paso 7: Benchmark (5 minutos)

```bash
python v411_optimizations/onnx_model_predictor.py
```

**Output esperado**:
```
Inference Speed (mock)
   Batch size   1: 1.00ms/batch (1.000ms/sample)
   Batch size  10: 1.00ms/batch (0.100ms/sample)
   Batch size 100: 1.00ms/batch (0.010ms/sample)

Expected Performance (vs sklearn RandomForest)
   sklearn RandomForest: 20ms per prediction
   ONNX Runtime:         1ms per prediction
   Speedup:              20x faster ⚡
```

### Paso 8: Commit

```bash
git add -A
git commit -m "OPTIM3: ONNX ML Acceleration (20x)

- Model converted: rf_model.pkl → rf_model.onnx
- ONNX predictor integrated in strategy
- Cross-validation: 100% accuracy match
- Tests passing
- Live trading validated
- Benchmark: 20ms → 1ms (20x speedup)"
```

---

## ✅ FASE 4 Checklist

- [ ] ONNX Runtime installed
- [ ] Model converted to .onnx (2-5 MB)
- [ ] rf_model.onnx file exists
- [ ] ONNXModelPredictor imported
- [ ] Predictions integrated in get_live_signal()
- [ ] Cross-validation script confirms 100% match
- [ ] Tests: TestONNXModel all pass
- [ ] Live trading 24h validated
- [ ] Signals correct
- [ ] Benchmark validates 20x
- [ ] Commit made

---

**FASE 4 Starter Guide**
**Expected Duration**: 4 days
**Target**: 20ms → 1ms (20x)
**Status**: Ready to implement
