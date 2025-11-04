# 📌 ESTRUCTURA DE ARCHIVOS - GUÍA RÁPIDA

Esta es una guía rápida para entender la estructura actual después de la limpieza de raíz.

## 📂 DIRECTORIO RAÍZ - Archivos Esenciales

Solo contiene **6 archivos esenciales**:

```
botcopilot-sar/
├── README.md ........................ 📖 Documentación principal del proyecto
├── requirements.txt ................. 📦 Dependencias Python (usar: pip install -r requirements.txt)
├── run_bot.bat ...................... 🤖 Ejecutador del bot (menú principal)
├── start_backtest.bat ............... 📊 Script para backtesting
├── start_live_ccxt.bat .............. 💱 Script para trading vivo (CCXT)
└── start_tests.bat .................. ✔️ Script para ejecutar tests
```

## 📁 ESTRUCTURA COMPLETA

```
botcopilot-sar/
├── README.md
├── requirements.txt
├── run_bot.bat
├── start_backtest.bat
├── start_live_ccxt.bat
├── start_tests.bat
│
└── descarga_datos/
    ├── main.py ..................... 🎯 Entrada principal del sistema
    ├── .env ........................ 🔐 Credenciales MT5 (privado)
    ├── .env.example ............... 📋 Template de variables
    ├── .env.example.sandbox ....... 🧪 Template sandbox
    │
    ├── ARCHIVOS MD/ ............... 📚 Centro de documentación
    │   ├── README.md .............. Índice de documentación
    │   ├── AUDITORIA_RAIZ_COMPLETADA.md
    │   ├── RESUMEN_LIMPIEZA_RAIZ_v1.md
    │   ├── LIMPIEZA_RAIZ_RESUMEN_1PG.md
    │   ├── [+40 archivos MD históricos]
    │
    ├── logs/ ....................... 📝 Archivos de log
    │   ├── backtest_output.log
    │   ├── dashboard_launch.log
    │   ├── [+otros logs]
    │
    ├── data/ ....................... 💾 Datos históricos (SQLite + CSV)
    │   ├── data.db ................ SQLite database (3.77 MB)
    │   ├── csv/ ................... CSV backups
    │   └── [dashboards y resultados]
    │
    ├── config/ ..................... ⚙️ Configuración
    │   └── config.yaml ............ YAML centralizado
    │
    ├── core/ ....................... 🔧 Módulos core del sistema
    ├── indicators/ ................. 📈 Indicadores técnicos
    ├── strategies/ ................. 🎯 Estrategias de trading
    ├── models/ ..................... 🤖 Modelos ML entrenados
    ├── utils/ ...................... 🛠️ Utilidades del sistema (23 módulos)
    ├── backtesting/ ................ 📊 Backtesting
    ├── optimizacion/ ............... 🔍 Optimización Optuna
    ├── risk_management/ ............ 🛡️ Gestión de riesgo
    ├── auditorias/ ................. 📋 Auditorías
    └── tests/ ...................... ✔️ Tests (6 esenciales)
```

## 🎯 ARCHIVOS CLAVE POR FUNCIÓN

### Para Iniciar el Bot
```bash
# Windows
run_bot.bat

# Linux/Mac
descarga_datos/run_bot.sh
```

### Para Backtesting
```bash
start_backtest.bat
```

### Para Trading Vivo
```bash
start_live_ccxt.bat
```

### Para Tests
```bash
start_tests.bat
```

### Para Documentación
1. `README.md` (esta carpeta) - Descripción general
2. `descarga_datos/ARCHIVOS MD/README.md` - Centro de documentación
3. `descarga_datos/ARCHIVOS MD/AUDITORIA_RAIZ_COMPLETADA.md` - Detalles de limpieza

### Para Configuración
```
descarga_datos/config/config.yaml
```

### Para Datos
```
descarga_datos/data/data.db (SQLite principal)
descarga_datos/data/csv/ (Backups CSV)
```

## 🔐 CREDENCIALES (.env)

```
Ubicación: descarga_datos/.env
Uso: Credenciales privadas MT5
Template: descarga_datos/.env.example
```

⚠️ **NUNCA** commits archivos `.env` (ya está en .gitignore)

## 📊 DOCUMENTACIÓN IMPORTANTE

### Auditoría Reciente (2 nov 2025)
Consultar: `descarga_datos/ARCHIVOS MD/LIMPIEZA_RAIZ_RESUMEN_1PG.md`

### Histórico Completo
Ver: `descarga_datos/ARCHIVOS MD/AUDITORIA_RAIZ_COMPLETADA.md`

## ✅ VERIFICACIÓN DE INTEGRIDAD

Para verificar que todo está en su lugar:

```python
python descarga_datos/tests/check_data_paths_consolidated.py
```

Para ejecutar smoke test:
```python
python -m pytest descarga_datos/tests/test_quick_backtest.py
```

## 🚀 PRÓXIMOS PASOS

1. ✅ Estructura limpia y organizada
2. ✅ Todos los archivos en ubicaciones correctas
3. ✅ Documentación accesible
4. 🔄 Próximo: Revisar `descarga_datos/ARCHIVOS MD/README.md` para guías completas

---

**Última actualización**: 2 nov 2025  
**Estado**: ✅ Sistema Operativo
