# 🔍 Verificador de Credenciales Kraken Futures

Este script permite verificar las credenciales de Kraken Futures y consultar el saldo de la cuenta antes de usarlas en operaciones de trading.

## 🚀 Uso Rápido

### Opción 1: Script Batch (Recomendado)
```batch
verify_kraken_credentials.bat
```

### Opción 2: Python Directo
```bash
python descarga_datos/utils/verify_kraken_credentials.py
```

### Opción 3: Módulo Python
```bash
python -m utils.verify_kraken_credentials
```

## 📋 Requisitos

- **Python 3.11+** con CCXT instalado
- **Credenciales válidas** en `descarga_datos/.env`:
  - `KRAKEN_FUTURES_API_KEY`
  - `KRAKEN_FUTURES_API_SECRET`

## 🔧 Configuración

### 1. Obtener Credenciales de Kraken Futures

1. Ve a [Kraken Futures Demo](https://demo-futures.kraken.com/)
2. Regístrate para obtener cuenta demo
3. Ve a **Settings** → **API**
4. Crea una nueva API Key con permisos:
   - ✅ **Perm_R_Orders**: Leer órdenes
   - ✅ **Perm_W_Orders**: Crear órdenes
   - ✅ **Perm_R_Balances**: Leer balances

### 2. Configurar Variables de Entorno

Edita `descarga_datos/.env` y agrega:

```env
# 🔐 CREDENCIALES KRAKEN FUTURES DEMO
KRAKEN_FUTURES_API_KEY=tu_api_key_aqui
KRAKEN_FUTURES_API_SECRET=tu_api_secret_aqui
```

## 📊 Qué Verifica el Script

### ✅ Paso 1: Carga de Credenciales
- Busca credenciales en múltiples ubicaciones de `.env`
- Valida que no estén vacías
- Muestra confirmación (ocultando valores sensibles)

### ✅ Paso 2: Conexión con Exchange
- Inicializa conexión con Kraken Futures
- Configura timeouts y rate limiting
- Verifica conectividad básica

### ✅ Paso 3: Prueba de Autenticación
- Realiza llamada de prueba a la API
- Carga lista de mercados disponibles
- Confirma que la API responde

### ✅ Paso 4: Consulta de Saldo
- Obtiene balance completo de la cuenta
- Muestra monedas con saldo positivo
- Detalla balance libre vs. en uso

## 🎯 Resultados Esperados

### ✅ Credenciales Válidas
```
============================================================
🔍 VERIFICACIÓN DE CREDENCIALES KRAKEN FUTURES
============================================================
⏰ Timestamp: 2025-10-26 18:19:54

1️⃣ CARGANDO CREDENCIALES...
✅ API Key: ***vZjB
✅ API Secret: ***jwto

2️⃣ INICIALIZANDO CONEXIÓN...
✅ Exchange Kraken Futures inicializado correctamente

3️⃣ PROBANDO CREDENCIALES...
✅ Conexión exitosa - 1308 mercados cargados

4️⃣ OBTENIENDO SALDO...
✅ Saldo obtenido correctamente

💰 SALDO DE CUENTA KRAKEN FUTURES
============================================================
📊 RESUMEN DE BALANCE:
   Total de activos: X diferentes

💵 MONEDAS CON BALANCE:
   USDT: 1000.00000000 (Libre: 1000.00000000)

✅ VERIFICACIÓN COMPLETA EXITOSA
   🔑 Credenciales válidas
   💰 Saldo obtenido correctamente
   🚀 Listo para usar en trading
```

### ❌ Credenciales Inválidas
```
3️⃣ PROBANDO CREDENCIALES...
❌ ERROR DE AUTENTICACIÓN: kraken {"error":["EAPI:Invalid key"]}
❌ FALLÓ: Las credenciales no son válidas
```

## 🔧 Solución de Problemas

### Error: "EAPI:Invalid key"
- **Causa**: Las credenciales no son válidas para Kraken Futures
- **Solución**:
  1. Verifica que uses credenciales de **Kraken Futures**, no Kraken Spot
  2. Asegúrate de usar la cuenta **Demo**, no producción
  3. Regenera las API keys en Kraken Futures

### Error: "No se encontró archivo .env"
- **Causa**: El archivo `.env` no existe o no está en la ubicación correcta
- **Solución**: Crea el archivo `descarga_datos/.env` con las variables requeridas

### Error: "CCXT no está instalado"
- **Causa**: Falta la librería CCXT
- **Solución**: `pip install ccxt`

## 📁 Ubicación del Script

```
descarga_datos/
├── utils/
│   └── verify_kraken_credentials.py  ← Script principal
├── .env                              ← Credenciales
└── ...
verify_kraken_credentials.bat         ← Launcher (raíz)
```

## 🎯 Integración con el Sistema

Este script es compatible con la configuración del bot trader:

- ✅ **Credenciales**: Usa las mismas variables de entorno que el bot
- ✅ **Exchange**: Configurado para Kraken Futures (igual que `config_kraken_live.yaml`)
- ✅ **Logging**: Integra con el sistema de logs del proyecto
- ✅ **Error Handling**: Manejo robusto de errores y excepciones

## 🚀 Próximos Pasos

Después de verificar las credenciales exitosamente:

1. **Actualizar configuración**: Cambia `active_exchange: kraken` en `config.yaml`
2. **Probar bot**: `python descarga_datos/main.py --live-ccxt`
3. **Monitorear**: Revisa logs en `descarga_datos/logs/`

---

**Estado**: ✅ **LISTO PARA USAR**
**Versión**: 1.0
**Fecha**: Octubre 2025