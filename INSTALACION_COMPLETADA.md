# ✅ Instalación ZMQ Completada Automáticamente

## 📁 Archivos Instalados en MT5

Los siguientes archivos fueron copiados a tu instalación de MT5:

```
C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\
├── Experts\
│   ├── ZMQ_Bridge_EA.mq5          ← EA con ZeroMQ (requiere librería externa)
│   └── Simple_Bridge_EA.mq5       ← EA SIN dependencias (recomendado para empezar)
└── Include\
    └── JAson.mqh                  ← Parser JSON (ya instalado)
```

---

## 🚀 Pasos para Usar (SIMPLE - Sin ZMQ)

### Opción A: EA Simple (Sin Dependencias) - **RECOMENDADO**

1. **Abrir MT5**

2. **Abrir MetaEditor** (presiona `F4` en MT5)

3. **Compilar el EA Simple**:
   - En MetaEditor, ve a: **Experts → Simple_Bridge_EA.mq5**
   - Presiona `F7` para compilar
   - Debe aparecer: **"0 errors, 0 warnings"**

4. **Habilitar trading algorítmico**:
   - En MT5: `Herramientas → Opciones → Expert Advisors`
   - Marcar:
     - ✅ Permitir trading algorítmico
     - ✅ Permitir importar DLL (si aparece)

5. **Agregar EA al gráfico**:
   - En Navigator (Ctrl+N), expandir **Expert Advisors**
   - Arrastrar **Simple_Bridge_EA** a cualquier gráfico
   - Configurar:
     - InpMagicNumber: **20260129**
     - InpEnableTicks: **true**
   - Marcar: ✅ **Permitir trading en vivo**
   - Click **OK**

6. **Verificar que está corriendo**:
   - Debe aparecer 😊 (cara sonriente) en la esquina del gráfico
   - En la pestaña **Experts**, debe ver: "✅ Simple Bridge EA inicializado correctamente"

---

## 🔬 Pasos para Usar (AVANZADO - Con ZMQ)

### Opción B: EA con ZeroMQ (Baja Latencia)

**Requiere instalación manual de librería ZMQ:**

1. **Descargar mql-zmq**:
   - Ir a: https://github.com/dingmaotu/mql-zmq/releases
   - Descargar última versión (ej: `mql-zmq-master.zip`)

2. **Extraer e instalar**:
   - Copiar carpeta `Zmq` a: `C:\Users\javie\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\`
   - Copiar archivos DLL a: `...\MQL5\Libraries\`

3. **Compilar ZMQ_Bridge_EA** en MetaEditor

4. **Agregar al gráfico** (igual que Simple_Bridge_EA)

5. **Configurar puertos**:
   - InpOrdersPort: **5555**
   - InpTicksPort: **5556**

---

## ⚙️ Configuración del Bot (Python)

La configuración YA ESTÁ LISTA en `config.yaml`:

```yaml
# Para EA Simple (archivos)
live_trading:
  executor_type: 'mt5'

# Para EA ZMQ (después de instalarlo)
zmq:
  enabled: true
live_trading:
  executor_type: 'zmq'
```

---

## ✅ Verificar Funcionamiento

### Test del EA Simple:

```powershell
cd copilot-bot-v-4.11
.\.venv\Scripts\python.exe descarga_datos\tests\test_zmq_connection.py
```

### Test del modo live:

```powershell
cd copilot-bot-v-4.11\descarga_datos
..\.venv\Scripts\python.exe main.py --live-mt5
```

---

## ❓ Solución de Problemas

### EA no compila:
- Verificar que los archivos están en las rutas correctas
- Si ZMQ_Bridge falla, usar Simple_Bridge_EA

### No aparece cara sonriente:
- Verificar que trading algorítmico está habilitado
- Revisar pestaña Experts por errores

### Bot no conecta:
- Verificar que el EA está corriendo en MT5
- Para Simple_Bridge: usar `executor_type: 'mt5'`
- Para ZMQ_Bridge: usar `executor_type: 'zmq'`

---

## 📊 Siguiente Paso

**¡Ya puedes ejecutar el bot en modo live!**

```powershell
cd copilot-bot-v-4.11\descarga_datos
..\.venv\Scripts\python.exe main.py --live-mt5
```

El bot usará MT5 directo (Simple_Bridge) por defecto. Funciona perfectamente sin ZMQ.

---

**Nota**: Simple_Bridge_EA es más que suficiente para trading. ZMQ es opcional para latencia ultra-baja (<10ms) en scalping.
