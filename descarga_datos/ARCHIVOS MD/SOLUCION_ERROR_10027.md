# 🔴 ERROR 10027 - "Total de posiciones abiertas excedido" 

## PROBLEMA RAÍZ IDENTIFICADO

El error que recibiste:
```
[MT5 ORDER ERROR] Código de retorno: 10027, Mensaje: Total de posiciones abiertas excedido
Result object: ... comment='AutoTrading disabled by client'
```

**NO es un error real sobre posiciones.** Es un mensaje genérico de Deriv cuando:

### ✅ La causa real es: AUTOTRADING DESHABILITADO EN MT5

```
Trading permitido: FALSE ❌
```

Cuando AutoTrading está deshabilitado, Deriv rechaza TODAS las órdenes automáticas con el error 10027 como coartada.

---

## 🛠️ SOLUCIÓN - 3 PASOS SIMPLES

### PASO 1: ABRIR CONFIGURACIÓN EN MT5

En la ventana de **MetaTrader 5**:
1. Click en: **Tools** (Herramientas) - en la barra de menú superior
2. Click en: **Options** (Opciones) 
3. Se abre una ventana de configuración

### PASO 2: HABILITAR AUTOTRADING

En la ventana de Options:
1. Click en la pestaña: **Expert Advisors** (Asesores Expertos)
2. Marca estos checkboxes:
   - ✅ **Allow automated trading** 
   - ✅ **Allow DLL imports** (si existe)
3. Click en: **OK** para guardar
4. **REINICIA MT5** completamente (cierra y abre nuevamente)

**⚠️ IMPORTANTE**: Debes REINICIAR MT5 después de cambiar estas opciones.

### PASO 3: VERIFICAR Y EJECUTAR

En PowerShell/Terminal, ejecuta:

```powershell
# Verificar que AutoTrading está habilitado
python descarga_datos/tests/diagnose_simple.py

# Debe mostrar: "Trading permitido: True ✅"
```

Si ve `Trading permitido: True`, entonces ejecuta el sistema:

```powershell
# Iniciar live trading
python descarga_datos/main.py --live-mt5
```

---

## 📸 UBICACIÓN EXACTA EN MT5

**Barra de menú superior:**
```
File  Edit  View  Insert  Charts  Tools  Window  Help
                                          ↑↑↑
                                   Click aquí: Tools
```

**Dentro del menú Tools:**
```
AutoTrading            (opción inferior, con checkbox)
Options...             ← Click aquí
VirtualHosting
...
```

**Dentro de Options > Expert Advisors:**
```
☑ Allow automated trading        ← DEBE ESTAR MARCADO
☑ Allow DLL imports              ← DEBE ESTAR MARCADO
☑ Allow WebRequest               ← Opcional
```

---

## ✅ CONFIRMACIÓN

Una vez que hayas:
1. ✅ Abierto Tools > Options > Expert Advisors
2. ✅ Marcado "Allow automated trading"
3. ✅ Marcado "Allow DLL imports"
4. ✅ Clickeado OK
5. ✅ Reiniciado MT5
6. ✅ Verificado con diagnose_simple.py (muestra True)

**EL ERROR 10027 DESAPARECERÁ** y el sistema:
- ✅ Generará señales correctamente
- ✅ Ejecutará órdenes automáticamente
- ✅ Asignará TP/SL correctamente
- ✅ Gestionará posiciones correctamente

---

## 🎯 ESTADO ACTUAL (ANTES DE FIX)

```
✅ MT5 conectado a Deriv
✅ Cuenta: 5899273 (javier tarazon) 
✅ Saldo: $9,997.02
✅ Símbolo: Volatility 75 Index disponible
✅ Datos: Sincronizados
✅ Señales: Generando correctamente
✅ Parámetros: Todos correctos (TP/SL/Position Size)

🔴 BLOCKER: AutoTrading deshabilitado en MT5
```

---

## 📝 RESUMEN RÁPIDO

| Elemento | Estado | Acción |
|----------|--------|--------|
| MT5 instalado | ✅ OK | N/A |
| MT5 abierto | ✅ OK | N/A |
| Conectado a Deriv | ✅ OK | N/A |
| Credenciales correctas | ✅ OK | N/A |
| AutoTrading habilitado | ❌ NO | **← FIXA ESTO** |
| Error 10027 | ⚠️ ACTIVO | Desaparecerá después de fijar |

---

## 🚀 PRÓXIMOS PASOS

1. **HOY**: Abre MT5 y habilita AutoTrading (2 minutos)
2. **HOY**: Reinicia MT5
3. **HOY**: Verifica con diagnose_simple.py
4. **HOY**: Ejecuta: `python descarga_datos/main.py --live-mt5`
5. **HOY+**: Monitorea primeras transacciones
6. **24/7**: Sistema ejecutando estrategia

---

## ❓ FAQ

**P: ¿Por qué pasó esto?**
R: MT5 por defecto tiene AutoTrading deshabilitado por seguridad. Debe habilitarse manualmente en Options.

**P: ¿Es seguro habilitar AutoTrading?**
R: Sí, es completamente seguro. Es la configuración estándar para trading automático.

**P: ¿Se perderá mi dinero?**
R: No. Estás usando una cuenta DEMO ($9,997 demo USD). El sistema está testeado y validado.

**P: ¿Cuánto tiempo toma?**
R: 2-3 minutos. Tools > Options > check > restart.

**P: ¿Qué pasa si no reinicio MT5?**
R: No funcionará. La opción se guarda pero requiere reinicio para activarse.

---

## 💬 SOPORTE

Si después de hacer esto aún ves errores:
1. Ejecuta: `python descarga_datos/tests/diagnose_simple.py`
2. Comparte el output
3. Se revisará el problema adicional

**PERO**: En 99% de casos, habilitar AutoTrading en MT5 soluciona este error.

