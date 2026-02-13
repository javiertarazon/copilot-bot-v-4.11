# 🔌 Guía de Instalación ZMQ Bridge para MT5

## Descripción

El ZMQ Bridge permite comunicación de baja latencia (<10ms) entre Python y MetaTrader 5 
mediante ZeroMQ sockets. Esto proporciona:

- **Ejecución nativa** de órdenes en MT5 via Expert Advisor
- **Datos tick-by-tick** en tiempo real
- **Heartbeats** para detectar desconexiones
- **Alta rentabilidad** al capturar volatilidad real-time

## Requisitos

1. **MetaTrader 5** instalado con cuenta (demo o real)
2. **Python 3.11+** con pyzmq instalado
3. **Librería ZMQ para MQL5** (mql-zmq)

---

## Paso 1: Instalar pyzmq en Python

```bash
cd copilot-bot-v-4.11
.\.venv\Scripts\pip.exe install pyzmq
```

---

## Paso 2: Instalar ZMQ para MQL5

### Opción A: Descargar desde GitHub (Recomendado)

1. Descargar la librería de: https://github.com/dingmaotu/mql-zmq/releases
2. Extraer el contenido
3. Copiar la carpeta `Zmq` a:
   ```
   C:\Users\[TU_USUARIO]\AppData\Roaming\MetaQuotes\Terminal\[ID_TERMINAL]\MQL5\Include\
   ```
4. Copiar los archivos DLL a:
   ```
   C:\Users\[TU_USUARIO]\AppData\Roaming\MetaQuotes\Terminal\[ID_TERMINAL]\MQL5\Libraries\
   ```

### Opción B: Instalación Manual

1. Descargar ZeroMQ para Windows: https://zeromq.org/download/
2. Copiar `libzmq.dll` a `MQL5\Libraries\`
3. Descargar mql-zmq headers y copiar a `MQL5\Include\Zmq\`

---

## Paso 3: Instalar los Archivos del EA

Copiar los archivos del proyecto a MT5:

```
Desde: copilot-bot-v-4.11\descarga_datos\mql5\
Hacia: C:\Users\[TU_USUARIO]\AppData\Roaming\MetaQuotes\Terminal\[ID_TERMINAL]\MQL5\

Archivos a copiar:
├── Experts\
│   └── ZMQ_Bridge_EA.mq5    → MQL5\Experts\ZMQ_Bridge_EA.mq5
└── Include\
    └── JAson.mqh            → MQL5\Include\JAson.mqh
```

---

## Paso 4: Compilar el EA en MetaEditor

1. Abrir MetaEditor (F4 desde MT5)
2. Navegar a `Experts\ZMQ_Bridge_EA.mq5`
3. Compilar (F7)
4. Verificar que no hay errores

---

## Paso 5: Configurar MT5

### Habilitar Trading Algorítmico

1. En MT5: `Herramientas` → `Opciones` → `Expert Advisors`
2. Marcar:
   - ✅ Permitir trading algorítmico
   - ✅ Permitir importar DLL

### Agregar EA al Gráfico

1. En el Navigator, expandir `Expert Advisors`
2. Arrastrar `ZMQ_Bridge_EA` a cualquier gráfico
3. Configurar parámetros:
   - **InpOrdersPort**: 5555 (puerto para órdenes)
   - **InpTicksPort**: 5556 (puerto para ticks)
   - **InpMagicNumber**: 20260129 (identificador del bot)
   - **InpEnableTicks**: true (enviar ticks en tiempo real)
   - **InpSlippage**: 10 (slippage máximo en puntos)
4. Marcar ✅ "Permitir trading en vivo"
5. Hacer clic en OK

---

## Paso 6: Configurar config.yaml

Agregar la configuración ZMQ al archivo `config/config.yaml`:

```yaml
# ========== CONFIGURACIÓN ZMQ ==========
zmq:
  enabled: true                    # Habilitar comunicación ZMQ
  orders_url: "tcp://localhost:5555"  # URL para órdenes
  ticks_url: "tcp://localhost:5556"   # URL para ticks
  timeout_ms: 5000                 # Timeout en milisegundos
  heartbeat_interval: 10           # Intervalo de heartbeat (segundos)

# En live_trading, elegir executor:
live_trading:
  executor_type: 'zmq'             # 'mt5' o 'zmq'
```

---

## Paso 7: Verificar Conexión

Ejecutar el script de prueba:

```bash
cd copilot-bot-v-4.11
.\.venv\Scripts\python.exe -c "
from descarga_datos.core.zmq_order_executor import ZMQOrderExecutor
executor = ZMQOrderExecutor()
if executor.initialize():
    print('✅ Conexión ZMQ exitosa!')
    info = executor.get_account_info()
    print(f'Balance: \${info[\"balance\"]:.2f}')
    executor.shutdown()
else:
    print('❌ Error de conexión')
"
```

---

## Uso

### Desde Python

```python
from descarga_datos.core.zmq_order_executor import ZMQOrderExecutor, ZMQOrderType

# Crear executor
executor = ZMQOrderExecutor(
    zmq_orders_url='tcp://localhost:5555',
    zmq_ticks_url='tcp://localhost:5556'
)

# Inicializar
if executor.initialize():
    # Enviar orden
    ticket = executor.send_order(
        symbol='TM_VOLATILITY_75',
        order_type=ZMQOrderType.BUY,
        volume=0.01,
        sl=40000.0,
        tp=45000.0
    )
    
    # Obtener posiciones
    positions = executor.get_positions()
    
    # Cerrar posición
    executor.close_position(ticket)
    
    # Obtener ticks
    ticks = executor.get_ticks('TM_VOLATILITY_75', count=100)
    
    executor.shutdown()
```

---

## Solución de Problemas

### Error: "No se pudo bind al puerto"
- Verificar que no hay otro proceso usando los puertos 5555/5556
- Ejecutar `netstat -an | findstr 5555`

### Error: "Timeout en heartbeat"
- Verificar que el EA está corriendo en MT5
- Verificar que el trading algorítmico está habilitado
- Verificar firewall de Windows

### Error: "DLL no encontrado"
- Copiar `libzmq.dll` a `MQL5\Libraries\`
- Habilitar "Permitir importar DLL" en opciones de EA

### Error: "Symbol not found"
- Verificar nombre exacto del símbolo en MT5
- Para ThinkMarkets: usar `TM_VOLATILITY_50/75/100`
- Para Deriv: usar `Volatility 50/75/100 Index`

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        PYTHON BOT                               │
│  ┌────────────────────┐    ┌────────────────────┐              │
│  │ live_trading_      │    │ zmq_order_         │              │
│  │ orchestrator.py    │───►│ executor.py        │              │
│  └────────────────────┘    └─────────┬──────────┘              │
│                                      │                          │
│                            REQ/REP   │   SUB                    │
│                            (órdenes) │   (ticks)                │
└────────────────────────────────┬─────┼───┬──────────────────────┘
                                 │     │   │
                        ZMQ      ▼     │   ▼
                        ─────────────────────────
                                 │     │   │
┌────────────────────────────────┴─────┼───┴──────────────────────┐
│                        METATRADER 5                             │
│  ┌────────────────────────────┬─────┴───┐                      │
│  │    ZMQ_Bridge_EA.mq5       │         │                      │
│  │    ├─ REP Socket ◄─────────┘         │                      │
│  │    │  (recibe órdenes)               │                      │
│  │    ├─ PUB Socket ─────────────────►  │                      │
│  │    │  (publica ticks)                │                      │
│  │    └─ CTrade (ejecuta)               │                      │
│  └──────────────────────────────────────┘                      │
│                                                                 │
│  ┌──────────────────────────────────────┐                      │
│  │         Broker Server                 │                      │
│  │    (ThinkMarkets / Deriv / etc)      │                      │
│  └──────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparación: MT5 Directo vs ZMQ

| Característica | MT5 Directo | ZMQ Bridge |
|----------------|-------------|------------|
| Latencia | ~50-100ms | <10ms |
| Datos | Barras | Tick-by-tick |
| Ejecución | Python → MT5 API | EA nativo |
| Complejidad | Baja | Media |
| Confiabilidad | Alta | Alta (con heartbeat) |
| Slippage | Mayor | Menor |

---

## Notas

- El EA debe estar corriendo en un gráfico de MT5 para funcionar
- Los puertos 5555/5556 deben estar libres
- El Magic Number (20260129) identifica las órdenes del bot
- El heartbeat cada 10 segundos verifica la conexión
