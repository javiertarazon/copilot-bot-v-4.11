# AI Agent Instructions for Bot Trader Copilot

## Architecture Overview
This is a modular trading system with centralized entry via `descarga_datos/main.py`. Key components:
- **Core**: Data providers (CCXT for crypto, MT5 for forex), order executors, live trading orchestrators
- **Strategies**: ML-enhanced strategies like `UltraDetailedHeikinAshiML` using trained models from `models/`
- **Backtesting**: Parallel optimization with Optuna, results in `data/dashboard_results/`
- **Data Flow**: SQLite primary → CSV fallback → auto-download via `utils/storage.py`
- **Config**: Centralized in `descarga_datos/config/config.yaml` (YAML format)

## Critical Workflows
- **Backtest**: `python descarga_datos/main.py --backtest` (uses config.yaml symbols/timeframes)
- **Optimize**: `python descarga_datos/main.py --optimize` (Optuna trials, saves to models/)
- **Live Trading**: `python descarga_datos/main.py --live` (sandbox mode by default in config)
- **Tests**: `python -m pytest descarga_datos/tests/test_quick_backtest.py` (smoke test)
- **Data Download**: Handled automatically by `ensure_data_availability()` in backtests

## Project Conventions
- **Sandbox First**: Always enable `sandbox: true` in exchange configs for testing
- **ML Models**: Train via optimization, load from `models/` using `ModelManager`
- **Indicators**: Use TALIB via `utils/talib_wrapper.py`, fallback to pandas implementations
- **Risk Management**: ATR-based stops, max drawdown limits from config
- **Logging**: Structured via `utils/logger.py`, metrics in `utils/logger_metrics.py`
- **Dependencies**: Install from root `requirements.txt`, uses virtual env `.venv/`

## Integration Points
- **Exchanges**: CCXT for crypto (Binance/Bybit), MT5 for forex
- **Data Sources**: Yahoo Finance fallback, auto-download for missing data
- **External APIs**: Streamlit dashboard, Plotly for visualization
- **Cross-Component**: Strategies call indicators, risk management applies to all trades

## Examples
- Add new strategy: Extend `strategies/base_strategy.py`, register in config.yaml `strategies:` section
- Modify indicators: Update `indicators/technical_indicators.py`, ensure TALIB compatibility
- Change config: Edit `config/config.yaml`, reload via `config_loader.py`

## AI Response Guidelines
- **Language**: All responses must be in Spanish.
- **Code Modifications**: The strategy (`strategies/ultra_detailed_heikin_ashi_ml_strategy.py`) and main modules (`descarga_datos/main.py`, core modules) are blocked from structural modifications. Only parameter improvements are allowed that enhance functionality and profitability without altering the core structure.
- **Documentation Creation Policy**: 🚨 **CRITICAL** - Do NOT create documentation files (*.md, *.txt, guides, reference documents, analysis reports, etc.) unless explicitly requested by the user. Only create code files when necessary for functionality. Examples of documentation NOT to create without request: implementation guides, step-by-step tutorials, summary reports, quick reference guides, changelog entries, or analysis documentation. If user says "no solicites documentos" or similar, strictly respect this preference.

## 📁 File Storage Policy - MANDATORY

🚨 **STRICT ENFORCEMENT**: All files MUST be saved in their designated folders. NO EXCEPTIONS.

### File Type → Storage Location

| File Type | Storage Folder | Rules |
|-----------|----------------|-------|
| **Documentation** (*.md) | `descarga_datos/ARCHIVOS MD/` | ALL markdown files here |
| **Tests** (test_*.py, check_*.py, validation_*.py, quick_*.py) | `descarga_datos/tests/` | ALL test/validation files here |
| **Functional Scripts** (utilities, helpers, tools) | `descarga_datos/utils/` | ALL system scripts here |
| **Data Files** (CSV, JSON, pickle, DB, results) | `descarga_datos/data/` | ALL generated data here |
| **Logs** (*.log, error files) | `descarga_datos/logs/` | ALL log files here |
| **Root Level** | Root only if `.py` (main entry points) or `.txt` (requirements.txt only) | NO other files at root |

### Specific Rules

**Documentation:**
```
✅ Markdown files (.md)     → descarga_datos/ARCHIVOS MD/
✅ Text summaries (.txt)    → descarga_datos/ARCHIVOS MD/
❌ NO .md or .txt at root
❌ NO .md or .txt in other folders
```

**Testing & Validation:**
```
✅ test_*.py               → descarga_datos/tests/
✅ check_*.py              → descarga_datos/tests/
✅ validation_*.py         → descarga_datos/tests/
✅ quick_*.py              → descarga_datos/tests/
❌ NO test files in scripts/
❌ NO test files in utils/
```

**Functional Code:**
```
✅ Helper functions        → descarga_datos/utils/
✅ Utility modules         → descarga_datos/utils/
✅ Common tools            → descarga_datos/utils/
❌ NO scripts in root
❌ NO scripts in other folders
```

**Generated Data:**
```
✅ CSV files               → descarga_datos/data/
✅ JSON results            → descarga_datos/data/
✅ Pickle files            → descarga_datos/data/
✅ Database files          → descarga_datos/data/
✅ Dashboard results       → descarga_datos/data/
✅ Backtest results        → descarga_datos/data/
❌ NO data at root
❌ NO data in other folders
```

**Logs:**
```
✅ Application logs        → descarga_datos/logs/
✅ Error logs              → descarga_datos/logs/
✅ Trade logs              → descarga_datos/logs/
❌ NO logs at root
❌ NO logs in other folders
```

### Violation Consequences
- **Missing Documentation**: STOP - Ask user for explicit request
- **Wrong Folder**: Move file immediately to correct location
- **Duplicates**: DELETE all duplicates, keep only in designated folder
- **Root Pollution**: REMOVE immediately, relocate to correct folder

### Path Examples

```python
# ✅ CORRECT
doc_path = Path(__file__).parent.parent / "ARCHIVOS MD" / "my_doc.md"
test_path = Path(__file__).parent.parent / "tests" / "test_my_feature.py"
script_path = Path(__file__).parent.parent / "utils" / "helper.py"
data_path = Path(__file__).parent.parent / "data" / "results.csv"
log_path = Path(__file__).parent.parent / "logs" / "app.log"

# ❌ WRONG - NEVER DO THIS
root_md = Path(".") / "my_doc.md"
data_at_root = Path(".") / "data.csv"
test_in_utils = Path("utils") / "test_something.py"
```

### Verification Checklist Before Saving
```
[ ] Is this a .md file?           → ARCHIVOS MD/
[ ] Is this a test_*.py file?     → tests/
[ ] Is this a utility function?   → utils/
[ ] Is this data/results?         → data/
[ ] Is this a log file?           → logs/
[ ] Am I creating at root?        → ONLY if requirements.txt or main entry
[ ] Does file go elsewhere?       → ASK USER FIRST
```

## Data Management Rules
- **Centralized Configuration**: All configuration is centralized in `descarga_datos/config/config.yaml`. Use this for all parameters.
- **Data Verification Flow**: When executing any main function requiring historical data (backtest, optimization, data download, data audit, model training), first verify if data exists in the SQLite database. If present, use those data. If not, proceed to download with corresponding modules, process, verify, calculate necessary indicators, and execute the corresponding main function.
- **Data Priority**: SQLite primary → CSV fallback → auto-download. Never skip verification steps.

## Directory Structure Policy - STRICT ENFORCEMENT

### **🚨 DUPLICATE DIRECTORIES PROHIBITED**
**Critical Policy**: Duplicate directory structures are strictly forbidden and will be immediately corrected.

#### **📁 CORRECT STRUCTURE (MANDATORY):**
```
botcopilot-sar/
├── descarga_datos/           ✅ ONLY ALLOWED LOCATION
│   ├── data/                 ✅ CENTRALIZED DATA STORAGE
│   │   ├── csv/              ✅ CSV files
│   │   ├── dashboard_results/ ✅ Backtest results
│   │   ├── optimization_pipeline/ ✅ Optimization data
│   │   ├── optimization_results/ ✅ Strategy optimization
│   │   └── [other data folders]
│   └── [other descarga_datos folders]
└── [root level files only]
```

#### **❌ FORBIDDEN STRUCTURES (NEVER CREATE):**
```
❌ descarga_datos/descarga_datos/data/  ← DUPLICATE - ELIMINATE IMMEDIATELY
❌ data/ (at root level)               ← DUPLICATE - ELIMINATE IMMEDIATELY  
❌ logs/ (at root level)               ← DUPLICATE - ELIMINATE IMMEDIATELY
❌ descarga_datos/data/descarga_datos/ ← NESTED DUPLICATE - FIX ROUTES
```

### **🔧 CORRECTIONS IMPLEMENTED - v4.5**

#### **Fixed Path Issues:**
1. **Configuration Files**: Changed `path: data` → `path: descarga_datos/data` in all YAML configs
2. **Default Parameters**: Updated default paths in storage classes and indicators
3. **Optimization Scripts**: Fixed relative paths in `run_optimization_pipeline2.py` and `strategy_optimizer.py`
4. **Environment Files**: Corrected database URLs in `.env` files

#### **Code Corrections Applied:**
```python
# ❌ BEFORE (Created duplicates)
results_dir = Path("descarga_datos/data/optimization_pipeline")

# ✅ AFTER (Correct relative paths)  
results_dir = Path(__file__).parent.parent / "data" / "optimization_pipeline"
```

#### **Files Corrected:**
- `descarga_datos/config/config.yaml`
- `descarga_datos/config/*.yaml` (all backups)
- `descarga_datos/utils/storage.py`
- `descarga_datos/utils/market_data_validator.py` 
- `descarga_datos/indicators/technical_indicators.py`
- `descarga_datos/.env.example*`
- `descarga_datos/optimizacion/run_optimization_pipeline2.py`
- `descarga_datos/optimizacion/strategy_optimizer.py`

### **🛡️ PREVENTION MEASURES**
- **Path Validation**: All paths must be relative to script location using `Path(__file__).parent.parent`
- **Configuration Audit**: YAML configs must use `descarga_datos/data` prefix
- **Code Review**: Any hardcoded "data/" paths trigger immediate correction
- **Testing**: Directory structure validation in CI/CD pipeline

### **🚨 IMMEDIATE ACTION REQUIRED**
If duplicate directories are detected:
1. **STOP ALL OPERATIONS**
2. **Move data** to correct location (`descarga_datos/data/`)
3. **Delete duplicates** 
4. **Fix code paths** causing the duplication
5. **Test thoroughly** before resuming operations

**Violation Severity**: HIGH - Duplicate directories corrupt data integrity and system stability.

## Error Prevention Rules
- **Avoid SQL Metadata Errors**: Ensure correct column count in INSERT statements (e.g., 9 values for 9 columns in data_metadata). Reference `utils/storage.py` fixes.
- **Handle KeyboardInterrupt Gracefully**: Implement try/except/finally blocks for shutdown, always launch dashboard if results exist.
- **Normalize Metrics Consistently**: Win rate must be decimal (0-1), not percentage. Validate in tests.
- **Dashboard Port Fallback**: Check port availability (8519-8523) and use fallback if occupied.
- **Async Shutdown Handling**: Manage `asyncio.CancelledError` and close connections properly.
- **Avoid Synthetic Data**: Never use or generate synthetic data; all operations must use real downloaded or live data.

## Critical Error Prevention - v4.0 Lessons Learned

### **🚨 JSON Serialization Errors - PREVENIR SIEMPRE**
**Problema v3.5**: Objetos `datetime` no serializables causaban errores recurrentes al guardar historial de posiciones.
**Lección**: NUNCA guardar objetos datetime directamente en estructuras que serán serializadas a JSON.
**Regla de Oro**:
```
✅ SIEMPRE usar convert_to_json_serializable() antes de json.dump()
✅ Convertir datetime.now() a datetime.now().isoformat() inmediatamente
✅ Validar tipos antes de serialización
✅ Implementar try/catch en todas las operaciones de guardado
```

**Código Problemático (NUNCA REPETIR)**:
```python
# ❌ MAL - Causó errores cada 5 minutos
position['open_time'] = datetime.now()  # Objeto datetime
json.dump(position_history, file)       # ERROR: not JSON serializable

# ✅ BIEN - Implementado en v4.0
position['open_time'] = datetime.now().isoformat()  # String
serializable_data = [convert_to_json_serializable(pos) for pos in position_history]
json.dump(serializable_data, file)
```

### **🚨 Missing Method Errors - IMPLEMENTAR INTERFACES COMPLETAS**
**Problema v3.5**: Método `calculate_position_risk` faltante causaba errores cada 60 segundos.
**Lección**: NUNCA dejar métodos abstractos o interfaces sin implementar.
**Regla de Oro**:
```
✅ Verificar TODOS los métodos requeridos antes de commits
✅ Implementar interfaces 100% completas
✅ Usar @abstractmethod para forzar implementación
✅ Validar llamadas existentes antes de cambios
```

**Prevención**:
```python
# ✅ REQUERIDO - Verificación antes de commits
def validate_implementation(self):
    required_methods = ['calculate_position_risk', 'validate_position', 'update_stops']
    for method in required_methods:
        if not hasattr(self, method):
            raise NotImplementedError(f"Método requerido faltante: {method}")
```

### **🚨 Resource Leak Errors - SHUTDOWN GRACEFUL OBLIGATORIO**
**Problema v3.5**: Conexiones no cerradas causaban memory leaks y warnings.
**Lección**: NUNCA omitir manejo de recursos en shutdown.
**Regla de Oro**:
```
✅ try/except/finally en TODOS los shutdown
✅ await close() en conexiones async
✅ Manejar asyncio.CancelledError explícitamente
✅ Liberar recursos en finally block
```

**Patrón Correcto**:
```python
async def shutdown(self):
    try:
        # Operaciones de cierre
        await self.connection.close()
    except asyncio.CancelledError:
        pass  # Graceful cancellation
    except Exception as e:
        self.logger.error(f"Shutdown error: {e}")
    finally:
        # ✅ SIEMPRE ejecutar - liberación de recursos
        self.resources = None
        self.logger.info("Shutdown completo")
```

### **🚨 Data Type Errors - VALIDACIÓN ESTRICTA**
**Problema v3.5**: Tipos inconsistentes causaban operaciones erróneas.
**Lección**: NUNCA asumir tipos de datos sin validación.
**Regla de Oro**:
```
✅ Validar tipos antes de operaciones numéricas
✅ Normalizar None a valores por defecto
✅ Usar type hints estrictos
✅ Implementar validación de entrada en métodos públicos
```

**Validación Requerida**:
```python
def validate_numeric_input(self, value: Any, default: float = 0.0) -> float:
    """Valida entrada numérica, retorna default si inválido."""
    try:
        result = float(value) if value is not None else default
        return result if not (math.isnan(result) or math.isinf(result)) else default
    except (TypeError, ValueError):
        return default
```

### **🚨 Live Trading Stability - VALIDACIÓN OBLIGATORIA**
**Problema v3.5**: Sistema funcional pero con errores recurrentes.
**Lección**: NUNCA desplegar sin validación completa de estabilidad.
**Regla de Oro**:
```
✅ 24h testing mínimo antes de producción
✅ Validar sin errores JSON en logs
✅ Verificar shutdown graceful
✅ Confirmar integridad de datos
✅ Monitoreo de recursos sin leaks
```

## Data Integrity Rules
- **Real Data Only**: All metrics, results, and strategy executions must derive from real downloaded or live data. No artificial alterations, improvements, or synthetic enhancements.
- **Result Authenticity**: Metrics and results must be the direct outcome of strategy execution on real data, without manipulation or optimization beyond parameter tuning.

Reference: `descarga_datos/ARCHIVOS MD/README.md` for sandbox testing details.