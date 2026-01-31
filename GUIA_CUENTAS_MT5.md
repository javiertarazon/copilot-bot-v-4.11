# 🏦 GUÍA DE CUENTAS MT5 DEMO - Sistema Multi-Cuenta

## 📋 CUENTAS DEMO DISPONIBLES

### 🥇 ThinkMarkets Demo (ACTIVA)
- **Login**: 175399
- **Password**: Jatr28037#
- **Servidor**: ThinkMarkets-Demo
- **Tipo**: Demo Standard
- **Moneda**: USD
- **Apalancamiento**: 1:500

### 🥈 ICMarkets Demo (BACKUP)
- **Login**: 52600804
- **Password**: Yl$eFUMT0@P4Tq
- **Servidor**: ICMarketsSC-Demo
- **Tipo**: Demo Standard
- **Moneda**: USD
- **Apalancamiento**: 1:500

## 🛠️ GESTIÓN DE CUENTAS

### Ver Cuentas Disponibles
```bash
python utils/mt5_account_manager.py
```

### Cambiar a ICMarkets
```bash
python utils/mt5_account_manager.py icmarkets
```

### Cambiar a ThinkMarkets
```bash
python utils/mt5_account_manager.py thinkmarkets
```

### Verificar Instalación MT5
```bash
python utils/mt5_account_manager.py verify
# O también:
python tests/verificar_mt5_instalacion.py
```

## 📥 INSTALACIÓN DE MT5

### Opción 1: ThinkMarkets (Recomendado)
1. Descargar: https://www.thinkmarkets.com/en/trading-platforms/metatrader-5/
2. Instalar MT5
3. Abrir MT5
4. File → Login to Trade Account
5. Introducir credenciales ThinkMarkets
6. Habilitar AutoTrading

### Opción 2: ICMarkets (Alternativa)
1. Descargar: https://www.icmarkets.com/global/en/metatrader-5
2. Instalar MT5
3. Abrir MT5
4. File → Login to Trade Account
5. Introducir credenciales ICMarkets
6. Habilitar AutoTrading

## ⚙️ CONFIGURACIÓN AUTOTRADING

### Paso 1: Habilitar AutoTrading en MT5
1. Abrir MetaTrader 5
2. Ir a: **Tools** → **Options**
3. Pestaña: **Expert Advisors**
4. ✅ Marcar: **Allow automated trading**
5. ✅ Marcar: **Allow DLL imports**
6. Click: **OK**
7. **Reiniciar MT5 completamente**

### Paso 2: Verificar Estado
```bash
python tests/diagnose_simple.py
```
**Debe mostrar**: `Trading permitido: True ✅`

## 🔧 ARCHIVOS DE CONFIGURACIÓN

### Archivo Principal: `config/mt5_accounts.yaml`
```yaml
active_account: "thinkmarkets"  # Cuenta activa

accounts:
  thinkmarkets:
    login: 175399
    server: "ThinkMarkets-Demo"
    # ... más configuración
    
  icmarkets:
    login: 52600804
    server: "ICMarketsSC-Demo"
    # ... más configuración
```

### Variables de Entorno: `.env`
```bash
# Se actualiza automáticamente al cambiar cuenta
MT5_LOGIN=175399
MT5_PASSWORD=Jatr28037#
MT5_SERVER=ThinkMarkets-Demo
```

### Configuración Principal: `config/config.yaml`
```yaml
mt5:
  enabled: true
  login: 175399  # Se sincroniza con cuenta activa
  server: 'ThinkMarkets-Demo'
```

## 🚀 FLUJO DE TRABAJO COMPLETO

### 1. Instalación Inicial
```bash
# Verificar si MT5 está instalado
python tests/verificar_mt5_instalacion.py

# Si no está instalado, descargar e instalar desde ThinkMarkets
```

### 2. Configuración de Cuenta
```bash
# Ver cuentas disponibles
python utils/mt5_account_manager.py

# Cambiar a cuenta deseada (si es necesario)
python utils/mt5_account_manager.py thinkmarkets
```

### 3. Configuración MT5
```
1. Abrir MT5
2. Conectar con credenciales mostradas
3. Habilitar AutoTrading
4. Verificar conexión
```

### 4. Verificación del Sistema
```bash
# Verificar que MT5 está conectado y AutoTrading habilitado
python tests/diagnose_simple.py

# Debe mostrar: Trading permitido: True ✅
```

### 5. Ejecutar Bot
```bash
# Backtest
python main.py --backtest

# Live Trading
python main.py --live-mt5
```

## 🔒 SEGURIDAD

### ✅ Cuentas Demo Seguras
- **Solo cuentas DEMO** - Sin riesgo de dinero real
- **Credenciales públicas** - Seguro guardar en repositorio
- **Múltiples opciones** - Backup disponible si una falla

### 🔄 Cambio Rápido de Cuentas
- **Sin edición manual** - Cambio automático de configuración
- **Sincronización completa** - .env, config.yaml y mt5_accounts.yaml
- **Verificación integrada** - Scripts de diagnóstico incluidos

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "MetaTrader 5 x64 not found"
```bash
# Verificar instalación
python tests/verificar_mt5_instalacion.py

# Si no está instalado, descargar desde ThinkMarkets o ICMarkets
```

### Error: "Trading permitido: False"
```bash
# Habilitar AutoTrading en MT5:
# Tools → Options → Expert Advisors → Allow automated trading
# Reiniciar MT5
```

### Error: "Authorization failed"
```bash
# Verificar credenciales en MT5
# File → Login to Trade Account
# Usar credenciales de la cuenta activa
```

### Cambiar de Broker
```bash
# Si ThinkMarkets no funciona, cambiar a ICMarkets
python utils/mt5_account_manager.py icmarkets

# Luego reconectar MT5 con nuevas credenciales
```

## 📞 SOPORTE

### Archivos de Diagnóstico
- `tests/diagnose_simple.py` - Diagnóstico básico MT5
- `tests/verificar_mt5_instalacion.py` - Verificar instalación
- `utils/mt5_account_manager.py` - Gestión de cuentas

### Logs de Sistema
- `logs/live_trading.log` - Logs de trading en vivo
- `logs/bot_trader.log` - Logs generales del sistema

### Documentación Adicional
- `INSTRUCCIONES_PRIORITARIAS.md` - Reglas fundamentales
- `AUDITORIA_TECNICA_COMPLETA.md` - Análisis técnico completo
- `ACCION_INMEDIATA.txt` - Problemas críticos conocidos

---

**Fecha**: 31 de enero de 2026  
**Sistema**: Bot Trader Copilot v4.11  
**Estado**: ✅ Sistema multi-cuenta implementado y documentado