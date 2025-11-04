# 🔧 CÓDIGO EXACTO DE LOS FIXES - REFERENCE RÁPIDA

## Fix #1: sync_positions_with_exchange()

### Ubicación
`ccxt_live_trading_orchestrator.py` - Líneas ~810-880  
(Antes de `_manage_open_positions()`)

### Código de Integración en _manage_open_positions()
```python
async def _manage_open_positions(self):
    # ✅ NUEVO: Sincronizar cada iteración
    self.sync_positions_with_exchange()
    
    positions_to_close = []
    # ... resto del método
```

### Método Completo (75 líneas)
Ver archivo: `ccxt_live_trading_orchestrator.py` líneas ~810-880

---

## Fix #2: _update_trailing_stop() - Fórmula Correcta

### Ubicación
`ccxt_live_trading_orchestrator.py` - Líneas 734-830

### Fórmula Vieja (Incorrecta)
```python
# ❌ WRONG - REEMPLAZADO
new_stop_distance = profit_amount * trailing_stop_pct
```

### Fórmula Nueva (Correcta)
```python
# ✅ CORRECT
highest_price = position.get('highest_price', current_price)
if current_price > highest_price:
    position['highest_price'] = current_price
    highest_price = current_price

max_profit = highest_price - entry_price
risk_distance = max_profit * (1 - trailing_stop_pct)
new_stop_price = highest_price - risk_distance

# Para SHORT: usar lowest_price en lugar de highest_price
if position['type'] == 'short':
    lowest_price = position.get('lowest_price', current_price)
    if current_price < lowest_price:
        position['lowest_price'] = current_price
        lowest_price = current_price
    max_loss = lowest_price - entry_price  # Será negativo
    risk_distance = abs(max_loss) * (1 - trailing_stop_pct)
    new_stop_price = lowest_price + risk_distance
```

---

## Fix #3: close_position_safe() - Método Nuevo

### Ubicación
`ccxt_order_executor.py` - Líneas ~845-930

### Código Completo
```python
def close_position_safe(self, ticket: str, force_close: bool = False) -> bool:
    """
    Cierra posición de forma segura verificando su estado en Binance.
    
    Validaciones:
    1. Verifica que ticket existe en sistema
    2. Fetch estado REAL en Binance
    3. Si ya cerrado en Binance: limpiar sistema, retornar True
    4. Si parcialmente rellenado: cancelar orden parcial
    5. Si aún abierto: ejecutar orden de cierre MARKET
    6. Eliminar de open_positions si éxito
    
    Args:
        ticket: ID de la orden a cerrar
        force_close: Si True, cierra incluso si no en sistema
        
    Returns:
        bool: True si cierre exitoso, False si error
    """
    try:
        # 1. Validar que existe
        if ticket not in self.open_positions and not force_close:
            self.logger.warning(f"Posición {ticket} no en sistema, asumiendo ya cerrada")
            return True
        
        position = self.open_positions.get(ticket, {})
        symbol = position.get('symbol', 'BTC/USDT')
        
        # 2. Fetch estado real en Binance
        try:
            real_order = self.exchange.fetch_order(ticket, symbol)
        except Exception as e:
            self.logger.error(f"Error fetching orden {ticket} en Binance: {e}")
            return False
        
        # 3. Si ya cerrado en Binance
        if real_order['status'] in ['closed', 'canceled']:
            self.logger.info(f"Posición {ticket} ya cerrada en Binance, limpiando sistema")
            if ticket in self.open_positions:
                del self.open_positions[ticket]
            return True
        
        # 4. Si parcialmente rellenado
        if real_order.get('filled', 0) < real_order.get('amount', 0):
            self.logger.warning(f"Orden {ticket} parcialmente rellenada, cancelando")
            try:
                self.exchange.cancel_order(ticket, symbol)
            except Exception as e:
                self.logger.error(f"Error cancelando orden {ticket}: {e}")
        
        # 5. Si aún abierto, ejecutar cierre
        if real_order['status'] == 'open':
            side = 'sell' if position.get('type') == 'buy' else 'buy'
            close_order = self.exchange.create_market_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=position.get('quantity', 0)
            )
            
            self.logger.info(f"Posición {ticket} cerrada exitosamente: {close_order}")
            
            # 6. Eliminar de sistema
            if ticket in self.open_positions:
                del self.open_positions[ticket]
            
            return True
        
        return False
        
    except Exception as e:
        self.logger.error(f"Error cerrando posición {ticket}: {e}")
        return False
```

### Callsites de Reemplazo (3 total)

**Callsite 1 - Línea 679** (Contexto: `_handle_strategy_signal()`)
```python
# ANTES:
close_success = self.order_executor.close_position(...)

# DESPUÉS:
close_success = self.order_executor.close_position_safe(...)
```

**Callsite 2 - Línea 984** (Contexto: `_manage_open_positions()` loop)
```python
# ANTES:
self.order_executor.close_position(ticket)

# DESPUÉS:
self.order_executor.close_position_safe(ticket)
```

**Callsite 3 - Línea 1289** (Contexto: `shutdown()`)
```python
# ANTES:
for ticket in list(self.active_positions.keys()):
    logger.info(f"Cerrando posición abierta {ticket}")
    self.order_executor.close_position(ticket)

# DESPUÉS:
for ticket in list(self.active_positions.keys()):
    logger.info(f"Cerrando posición abierta {ticket}")
    self.order_executor.close_position_safe(ticket)
```

---

## Fix #4A: _calculate_pnl_with_fees()

### Ubicación
`ccxt_order_executor.py` - Líneas ~1055-1110

### Código Completo
```python
def _calculate_pnl_with_fees(self, position: Dict) -> Dict[str, float]:
    """
    ✅ FIX #4: Calcula PnL REAL incluyendo comisiones de Binance (0.1%).
    
    Problema Original: Sistema calculaba PnL sin incluir comisiones,
    lo que generaba discrepancia de $225 USDT entre sistema y realidad.
    
    Args:
        position: Dict con {
            'entry_price': float,
            'exit_price': float,
            'quantity': float,
            'type': 'buy' or 'sell'
        }
    
    Returns:
        Dict con {
            'pnl_gross': float,        # PnL antes de comisiones
            'entry_fee': float,        # Comisión entrada (0.1%)
            'exit_fee': float,         # Comisión salida (0.1%)
            'total_fees': float,       # Suma de ambas comisiones
            'pnl_net': float,          # PnL después de comisiones
            'pnl_net_pct': float       # PnL neto en porcentaje
        }
    """
    try:
        entry_price = position.get('entry_price', 0)
        exit_price = position.get('exit_price', 0)
        quantity = position.get('quantity', 0)
        position_type = position.get('type', 'buy')
        
        # Binance SPOT comisión: 0.1% (0.001)
        BINANCE_FEE_RATE = 0.001
        
        # Calcular PnL bruto (sin comisiones)
        if position_type == 'buy':
            pnl_gross = (exit_price - entry_price) * quantity
        else:  # sell
            pnl_gross = (entry_price - exit_price) * quantity
        
        # Calcular comisiones
        # Comisión de entrada: 0.1% sobre capital invertido
        entry_capital = entry_price * quantity
        entry_fee = entry_capital * BINANCE_FEE_RATE
        
        # Comisión de salida: 0.1% sobre cantidad de criptos vendidos
        exit_capital = exit_price * quantity
        exit_fee = exit_capital * BINANCE_FEE_RATE
        
        # Total de comisiones
        total_fees = entry_fee + exit_fee
        
        # PnL neto (restando comisiones)
        pnl_net = pnl_gross - total_fees
        
        # PnL neto en porcentaje
        if entry_capital > 0:
            pnl_net_pct = (pnl_net / entry_capital) * 100
        else:
            pnl_net_pct = 0.0
        
        result = {
            'pnl_gross': round(pnl_gross, 8),
            'entry_fee': round(entry_fee, 8),
            'exit_fee': round(exit_fee, 8),
            'total_fees': round(total_fees, 8),
            'pnl_net': round(pnl_net, 8),
            'pnl_net_pct': round(pnl_net_pct, 4)
        }
        
        self.logger.debug(
            f"PnL con comisiones - Bruto: ${pnl_gross:.8f}, "
            f"Comisiones: ${total_fees:.8f}, Neto: ${pnl_net:.8f} ({pnl_net_pct:.4f}%)"
        )
        
        return result
        
    except Exception as e:
        self.logger.error(f"Error calculando PnL con comisiones: {e}")
        return {
            'pnl_gross': 0.0,
            'entry_fee': 0.0,
            'exit_fee': 0.0,
            'total_fees': 0.0,
            'pnl_net': 0.0,
            'pnl_net_pct': 0.0
        }
```

---

## Fix #4B: _calculate_unrealized_pnl()

### Ubicación
`ccxt_order_executor.py` - Líneas ~1112-1160

### Código Completo
```python
def _calculate_unrealized_pnl(self, position: Dict, current_price: float) -> Dict[str, float]:
    """
    ✅ FIX #4 (Parte 2): Calcula PnL NO REALIZADO para posiciones abiertas.
    
    Para posiciones abiertas, NO se incluyen comisiones de salida
    porque la posición aún no ha sido cerrada.
    Se incluye solo la comisión de entrada que ya fue pagada.
    
    Args:
        position: Dict con {
            'entry_price': float,
            'quantity': float,
            'type': 'buy' or 'sell'
        }
        current_price: Precio actual del activo
    
    Returns:
        Dict con {
            'unrealized_pnl': float,     # PnL no realizado (sin comisión salida)
            'unrealized_pnl_pct': float, # En porcentaje
            'entry_fee_paid': float      # Comisión ya pagada (entrada)
        }
    """
    try:
        entry_price = position.get('entry_price', 0)
        quantity = position.get('quantity', 0)
        position_type = position.get('type', 'buy')
        
        BINANCE_FEE_RATE = 0.001
        
        # Calcular PnL sin considerar comisión de salida (aún no cerrado)
        if position_type == 'buy':
            pnl_gross = (current_price - entry_price) * quantity
        else:  # sell
            pnl_gross = (entry_price - current_price) * quantity
        
        # Restar solo comisión de entrada (que ya fue pagada)
        entry_capital = entry_price * quantity
        entry_fee_paid = entry_capital * BINANCE_FEE_RATE
        
        unrealized_pnl = pnl_gross - entry_fee_paid
        
        # Porcentaje
        if entry_capital > 0:
            unrealized_pnl_pct = (unrealized_pnl / entry_capital) * 100
        else:
            unrealized_pnl_pct = 0.0
        
        result = {
            'unrealized_pnl': round(unrealized_pnl, 8),
            'unrealized_pnl_pct': round(unrealized_pnl_pct, 4),
            'entry_fee_paid': round(entry_fee_paid, 8)
        }
        
        self.logger.debug(
            f"PnL no realizado - Gross: ${pnl_gross:.8f}, "
            f"Comisión entrada: ${entry_fee_paid:.8f}, Neto: ${unrealized_pnl:.8f} ({unrealized_pnl_pct:.4f}%)"
        )
        
        return result
        
    except Exception as e:
        self.logger.error(f"Error calculando PnL no realizado: {e}")
        return {
            'unrealized_pnl': 0.0,
            'unrealized_pnl_pct': 0.0,
            'entry_fee_paid': 0.0
        }
```

---

## Integración en close_position()

### Ubicación
`ccxt_order_executor.py` - Líneas ~835-845

### Código Original (Sin Comisiones)
```python
# ❌ ANTES
position['pnl'] = self._calculate_pnl(position)
```

### Código Nuevo (Con Comisiones)
```python
# ✅ DESPUÉS
# ✅ FIX #4: Usar PnL CON comisiones (nuevo) en lugar de PnL sin comisiones
pnl_details = self._calculate_pnl_with_fees(position)
position['pnl'] = pnl_details['pnl_net']  # PnL neto después de comisiones
position['pnl_gross'] = pnl_details['pnl_gross']
position['entry_fee'] = pnl_details['entry_fee']
position['exit_fee'] = pnl_details['exit_fee']
position['total_fees'] = pnl_details['total_fees']
```

---

## ✅ Verificación Rápida

### Compilar
```bash
python -m py_compile descarga_datos/core/ccxt_live_trading_orchestrator.py
python -m py_compile descarga_datos/core/ccxt_order_executor.py
```

### Buscar Métodos
```bash
grep -n "def sync_positions_with_exchange" descarga_datos/core/ccxt_live_trading_orchestrator.py
grep -n "def _calculate_pnl_with_fees" descarga_datos/core/ccxt_order_executor.py
grep -n "def close_position_safe" descarga_datos/core/ccxt_order_executor.py
grep -n "def _update_trailing_stop" descarga_datos/core/ccxt_live_trading_orchestrator.py
```

---

**Octubre 2025** | Ready for Production
