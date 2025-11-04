# PASOS DETALLADOS - CON UBICACIONES EXACTAS

## 🎯 OBJETIVO
Habilitar AutoTrading en MT5 para que el sistema pueda ejecutar órdenes automáticamente.

---

## ✅ PASO 1: VERIFICA QUE MT5 ESTÁ ABIERTO

En tu escritorio o barra de tareas, busca el icono de **MetaTrader 5**.

Si no está abierto:
- Descarga e instala desde: https://deriv.com
- O desde tu programa instalado

---

## ✅ PASO 2: ABRE TOOLS MENU

En la ventana abierta de MetaTrader 5:

```
Mira la barra superior (donde está File, Edit, View, etc):

┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Insert  Charts  Tools  Window  Help   │
│                                        ↑↑↑               │
│                                    CLICK AQUÍ            │
└─────────────────────────────────────────────────────────┘

Click en: TOOLS (Herramientas)
```

---

## ✅ PASO 3: ABRE OPTIONS

Después de clickear Tools, verás un menú desplegable:

```
┌──────────────────────────┐
│ AutoTrading              │ ← Puede haber aquí un checkbox
├──────────────────────────┤
│ Options...               │ ← CLICK AQUÍ
├──────────────────────────┤
│ VirtualHosting           │
│ API Usage                │
│ ...más opciones...       │
└──────────────────────────┘
```

Click en: **Options...**

---

## ✅ PASO 4: VAL LA PESTAÑA EXPERT ADVISORS

Se abrirá una ventana grande de "Options". 

En el lado IZQUIERDO, verás varias pestañas:

```
┌─ Options ─────────────────────────────────┐
│ [+] General                                │
│ [+] Charts                                 │
│ [+] Colors                                 │
│ [+] Sounds                                 │
│ [+] Trading                                │
│ [+] Expert Advisors  ← CLICK AQUÍ          │
│ [+] Notifications                          │
│ [+] ...más...                              │
└────────────────────────────────────────────┘
```

Click en: **Expert Advisors**

---

## ✅ PASO 5: MARCA LOS CHECKBOXES

Ahora en el lado DERECHO verás opciones:

```
┌─ Expert Advisors ──────────────────────────┐
│                                             │
│  ☐ Allow automated trading                 │ ← MARCA ESTO
│                                             │
│  ☐ Allow DLL imports                       │ ← MARCA ESTO TAMBIÉN
│                                             │
│  ☐ Allow WebRequest                        │ (opcional)
│                                             │
│  ☐ Disable Expert Advisors                 │ (NO marques esto)
│                                             │
│               [OK]     [Cancel]             │
│                                             │
└─────────────────────────────────────────────┘
```

**IMPORTANTE**: 
- ☑ **Allow automated trading** ← DEBE ESTAR MARCADO (✅)
- ☑ **Allow DLL imports** ← DEBE ESTAR MARCADO (✅)
- ☑ **Allow WebRequest** ← Opcional, puedes dejar sin marcar

---

## ✅ PASO 6: CLICK EN OK

```
┌─ Expert Advisors ──────────────────────────┐
│                                             │
│  ☑ Allow automated trading                 │ ← Ahora está ☑
│                                             │
│  ☑ Allow DLL imports                       │ ← Ahora está ☑
│                                             │
│               [OK] ← CLICK AQUÍ             │
│                                             │
└─────────────────────────────────────────────┘
```

Click en: **OK**

---

## ✅ PASO 7: REINICIA MT5

**CRÍTICO**: Debes REINICIAR MT5 completamente.

```
1. Cierra MT5:
   - Click en la X (esquina superior derecha) de MT5
   - Confirma si te pide guardar

2. Abre MT5 nuevamente:
   - Click en icono de MT5
   - O desde Start Menu
   - O desde C:\Program Files\MetaTrader 5\terminal64.exe

3. Espera a conectar:
   - Verás proceso de login
   - En esquina inferior derecha verás "Connected" cuando esté listo
```

---

## ✅ PASO 8: VERIFICA QUE FUNCIONÓ

Abre **PowerShell** o **Command Prompt**:

```powershell
cd c:\Users\javie\copilot\botcopilot-sar

python descarga_datos/tests/diagnose_simple.py
```

Deberías ver:

```
✅ MT5 inicializado
✅ Cuenta conectada: javier tarazon
✅ Saldo: $9997.02
✅ Margen libre: $9997.02

💻 TERMINAL:
   Terminal conectada: True
   Trading permitido: True ✅ ← ESTO DEBE DECIR True

📈 POSICIONES ABIERTAS: 0
📋 ÓRDENES PENDIENTES: 0

================================================================================
✅ Trading está PERMITIDO - Sistema listo para ejecutar
```

Si ves `Trading permitido: True` ✅, ¡FUNCIONÓ!

---

## ✅ PASO 9: INICIA EL SISTEMA LIVE TRADING

Una vez que `Trading permitido: True`, ejecuta:

```powershell
python descarga_datos/main.py --live-mt5
```

El sistema ahora:
- ✅ Se conectará a MT5
- ✅ Generará señales
- ✅ Ejecutará órdenes automáticamente
- ✅ Gestionará TP/SL correctamente
- ✅ Rastreará P&L

---

## 🔄 SI ALGO SALE MAL

### Si todavía dice "Trading permitido: False"

1. Verifica que REINICIASTE MT5 (no solo minimizaste)
2. En MT5, mira las opciones Expert Advisors nuevamente
3. Los checkboxes deben estar ☑ (NO grises ☐)
4. Si están grises, significa que no se guardaron
5. Vuelve a marcar y OK
6. REINICIA MT5 de nuevo

### Si aparecen otros errores

Ejecuta:
```powershell
python descarga_datos/tests/diagnose_simple.py
```

Copia el output completo y comparte el error.

---

## ✨ RESULTADO ESPERADO

Después de completar todos los pasos, verás en PowerShell:

```
2025-11-03 23:45:00 - LiveTradingOrchestrator - INFO - Ciclo #1
2025-11-03 23:45:02 - LiveTradingOrchestrator - INFO - BUY: Position size 0.001
2025-11-03 23:45:03 - MT5OrderExecutor - INFO - ✅ Orden BUY ejecutada
2025-11-03 23:45:03 - MT5OrderExecutor - INFO - Entry: 42,500.00
2025-11-03 23:45:03 - MT5OrderExecutor - INFO - SL: 42,069.72 (ATR × 3.25)
2025-11-03 23:45:03 - MT5OrderExecutor - INFO - TP: 43,575.70 (ATR × 5.5)
2025-11-03 23:45:05 - Posición SHORT: ya existe
```

✅ **¡SISTEMA OPERANDO!**

---

## ⏰ DURACIÓN TOTAL

| Paso | Duración |
|------|----------|
| 1. Buscar MT5 | 30 segundos |
| 2. Abrir Tools | 30 segundos |
| 3. Abrir Options | 30 segundos |
| 4. Buscar Expert Advisors | 30 segundos |
| 5. Marcar checkboxes | 1 minuto |
| 6. Click OK | 30 segundos |
| 7. Reiniciar MT5 | 2 minutos |
| 8. Verificar diagnóstico | 1 minuto |
| 9. Iniciar sistema | 1 minuto |
| **TOTAL** | **≈ 7 minutos** |

---

## 📞 SOPORTE

Si necesitas ayuda:
1. Comparte screenshot de Tools > Options > Expert Advisors
2. Comparte output de `diagnose_simple.py`
3. Describe exactamente qué ves en MT5

Pero en 99% de casos, estos 9 pasos resuelven el problema.

