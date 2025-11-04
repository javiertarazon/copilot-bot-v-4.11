# GUÍA DE IMPLEMENTACIÓN - LocalPositionTracker

**Objetivo**: Eliminar posiciones "fantasma" manteniendo registro local de órdenes  
**Estimado**: 4-6 horas desarrollo + 2 horas testing  
**Complejidad**: Media  
**Prioridad**: Alta (próxima semana)

---

## 📋 COMPONENTES A IMPLEMENTAR

### 1. LocalPositionTracker (200 líneas)
**Archivo**: `descarga_datos/utils/position_tracker.py`

```python
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

class LocalPositionTracker:
    """
    Mantiene registro local de posiciones abiertas.
    Independiente del endpoint SAPI.
    
    Persiste en SQLite para recuperación ante crashes.
    """
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path(__file__).parent.parent / "data" / "position_tracker.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa base de datos SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    order_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    created_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    status TEXT DEFAULT 'open',
                    ml_confidence REAL,
                    atr REAL,
                    execution_details TEXT,
                    synced_with_exchange BOOLEAN DEFAULT 0
                )
            """)
            conn.commit()
    
    def add_position(self, order_id: str, position_data: Dict) -> None:
        """Registra nueva posición abierta"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO positions 
                (order_id, symbol, type, quantity, entry_price, stop_loss, 
                 take_profit, created_at, status, ml_confidence, atr, execution_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                position_data.get('symbol'),
                position_data.get('type'),
                position_data.get('quantity'),
                position_data.get('entry_price'),
                position_data.get('stop_loss'),
                position_data.get('take_profit'),
                datetime.now().isoformat(),
                'open',
                position_data.get('ml_confidence'),
                position_data.get('atr'),
                json.dumps(position_data.get('execution_details', {}))
            ))
            conn.commit()
    
    def get_open_positions(self, timeout_hours: int = 2) -> Dict[str, Dict]:
        """Obtiene posiciones abiertas dentro del timeout"""
        cutoff_time = (datetime.now() - timedelta(hours=timeout_hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE status = 'open' AND created_at > ?
            """, (cutoff_time,))
            
            positions = {}
            for row in cursor:
                positions[row['order_id']] = dict(row)
            
            return positions
    
    def mark_synced(self, order_id: str) -> None:
        """Marca posición como sincronizada con exchange"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE positions SET synced_with_exchange = 1 WHERE order_id = ?
            """, (order_id,))
            conn.commit()
    
    def close_position(self, order_id: str, close_price: float = None) -> None:
        """Cierra una posición"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE positions SET status = 'closed', closed_at = ? WHERE order_id = ?
            """, (datetime.now().isoformat(), order_id))
            conn.commit()
    
    def get_all_positions(self) -> List[Dict]:
        """Obtiene histórico completo de posiciones"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM positions")
            return [dict(row) for row in cursor]
```

---

### 2. HybridSynchronizer (250 líneas)
**Archivo**: `descarga_datos/utils/hybrid_synchronizer.py`

```python
import logging
from typing import Dict, Optional, Set
from .position_tracker import LocalPositionTracker

logger = logging.getLogger(__name__)

class HybridSynchronizer:
    """
    Sincroniza posiciones entre:
    1. Local tracking (siempre disponible)
    2. Exchange REST API (cuando SAPI falla)
    3. Fallback a datos locales
    """
    
    def __init__(self, exchange, position_tracker: LocalPositionTracker):
        self.exchange = exchange
        self.tracker = position_tracker
    
    def sync_positions(self, symbol: str) -> Dict[str, Dict]:
        """
        Sincroniza posiciones usando múltiples fuentes.
        
        Prioridad:
        1. Intenta REST API (cuando SAPI no disponible)
        2. Fallback a tracking local
        3. Marca como sincronizadas
        
        Returns:
            Dict con todas las posiciones (reales + locales)
        """
        
        # Obtener datos locales
        local_positions = self.tracker.get_open_positions()
        logger.info(f"📍 Posiciones locales: {len(local_positions)}")
        
        # Intenta sincronizar con exchange
        synced_count = self._sync_with_exchange(symbol, local_positions)
        logger.info(f"✅ Sincronizadas con exchange: {synced_count}/{len(local_positions)}")
        
        return local_positions
    
    def _sync_with_exchange(self, symbol: str, local_positions: Dict) -> int:
        """
        Intenta sincronizar posiciones locales con exchange.
        Usa múltiples estrategias de fallback.
        """
        synced_count = 0
        
        # Estrategia 1: fetch_balance (REST API - siempre disponible)
        try:
            balance = self.exchange.fetch_balance()
            logger.info("✅ Sincronización vía REST API fetch_balance")
            
            # Buscar órdenes cerradas del símbolo
            for pos_id in local_positions:
                # Marcar como sincronizado
                self.tracker.mark_synced(pos_id)
                synced_count += 1
            
            return synced_count
        
        except Exception as e:
            logger.warning(f"⚠️  fetch_balance falló: {e}")
        
        # Estrategia 2: Intenta fetch_closed_orders (puede fallar en testnet)
        try:
            closed_orders = self.exchange.fetch_closed_orders(symbol)
            real_ids = {str(o['id']) for o in closed_orders}
            
            for pos_id in local_positions:
                if str(pos_id) in real_ids:
                    self.tracker.mark_synced(pos_id)
                    synced_count += 1
            
            logger.info(f"✅ Sincronización vía fetch_closed_orders: {synced_count}")
            return synced_count
        
        except Exception as e:
            if 'sapi' in str(e).lower() or 'testnet' in str(e).lower():
                logger.warning(f"⚠️  SAPI no disponible (testnet): {e}")
            else:
                logger.warning(f"⚠️  fetch_closed_orders falló: {e}")
        
        # Estrategia 3: Fallback a datos locales (sin sincronización)
        logger.warning(f"🔄 Usando posiciones locales sin sincronización")
        return 0  # Ninguna sincronizada, pero posiciones mantienen datos locales
    
    def reconcile(self, exchange_positions: Dict, 
                  local_positions: Dict) -> Dict[str, Dict]:
        """
        Reconcilia datos del exchange con datos locales.
        
        Estrategia:
        - Usar datos del exchange si disponibles
        - Completar con datos locales si falta algo
        - Marcar desajustes para auditoría
        """
        
        reconciled = {}
        
        # Posiciones del exchange (fuente de verdad)
        for pos in exchange_positions:
            reconciled[pos['id']] = pos
        
        # Posiciones locales que no están en exchange
        for pos_id, pos_data in local_positions.items():
            if pos_id not in reconciled:
                if pos_data.get('synced_with_exchange'):
                    # Estaba sincronizada pero ahora no existe en exchange
                    # Probablemente cerrada
                    logger.info(f"✅ Posición {pos_id} cerrada en exchange")
                    self.tracker.close_position(pos_id)
                else:
                    # Nunca fue sincronizada - usar datos locales
                    logger.warning(f"⚠️  Posición local {pos_id} no sincronizada")
                    reconciled[pos_id] = pos_data
        
        return reconciled
```

---

### 3. Integración en CCXTLiveTradingOrchestrator (modificar)

**Cambios en**: `descarga_datos/core/ccxt_live_trading_orchestrator.py`

```python
# En __init__
from utils.position_tracker import LocalPositionTracker
from utils.hybrid_synchronizer import HybridSynchronizer

def __init__(self, ...):
    # ... código existente ...
    
    # NUEVO: Tracker local
    self.position_tracker = LocalPositionTracker()
    self.synchronizer = HybridSynchronizer(
        exchange=self.order_executor.exchange,
        position_tracker=self.position_tracker
    )

# En crear_posicion (después de abrir orden)
def _open_position(self, ...):
    # ... código existente para crear orden ...
    
    # NUEVO: Registrar en tracker local
    self.position_tracker.add_position(order_id, {
        'symbol': symbol,
        'type': side,
        'quantity': quantity,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'ml_confidence': ml_conf,
        'atr': atr_value,
        'execution_details': execution_result
    })
    
    logger.info(f"✅ Posición {order_id} registrada en tracker local")

# En sync_positions (reemplazar lógica actual)
def sync_positions(self, symbol):
    # ANTES:
    #   positions = [] o error
    
    # DESPUÉS:
    positions = self.synchronizer.sync_positions(symbol)
    
    return positions
```

---

### 4. Tests (150 líneas)
**Archivo**: `descarga_datos/tests/test_position_tracker.py`

```python
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from utils.position_tracker import LocalPositionTracker
from utils.hybrid_synchronizer import HybridSynchronizer

@pytest.fixture
def tracker():
    # Usar BD temporal para tests
    db_path = Path("/tmp/test_positions.db")
    if db_path.exists():
        db_path.unlink()
    tracker = LocalPositionTracker(db_path)
    yield tracker
    # Cleanup
    if db_path.exists():
        db_path.unlink()

def test_add_position(tracker):
    """Test agregar posición"""
    tracker.add_position("123", {
        'symbol': 'BTC/USDT',
        'type': 'sell',
        'quantity': 0.001,
        'entry_price': 113285,
        'stop_loss': 150604,
        'take_profit': 19987
    })
    
    positions = tracker.get_open_positions()
    assert "123" in positions
    assert positions["123"]['symbol'] == 'BTC/USDT'

def test_position_timeout(tracker):
    """Test timeout de posiciones"""
    # Agregar posición antigua
    # Modificar directamente en BD para simular edad
    
    positions_2h = tracker.get_open_positions(timeout_hours=2)
    positions_0h = tracker.get_open_positions(timeout_hours=0)
    
    assert len(positions_2h) >= len(positions_0h)

def test_close_position(tracker):
    """Test cerrar posición"""
    tracker.add_position("123", {'symbol': 'BTC/USDT', ...})
    tracker.close_position("123")
    
    open_positions = tracker.get_open_positions()
    assert "123" not in open_positions

def test_mark_synced(tracker):
    """Test marcar como sincronizado"""
    tracker.add_position("123", {'symbol': 'BTC/USDT', ...})
    tracker.mark_synced("123")
    
    # Verificar en BD
    all_pos = tracker.get_all_positions()
    assert any(p['order_id'] == "123" and p['synced_with_exchange'] for p in all_pos)
```

---

## 📦 INSTALACIÓN Y DEPLOYMENT

### Paso 1: Crear archivos
```bash
# Copiar archivos a:
descarga_datos/utils/position_tracker.py
descarga_datos/utils/hybrid_synchronizer.py
descarga_datos/tests/test_position_tracker.py
```

### Paso 2: Testing
```bash
cd descarga_datos
python -m pytest tests/test_position_tracker.py -v
```

### Paso 3: Integración gradual
```python
# Fase 1: Ejecutar en paralelo
# - Mantener código actual
# - Agregar tracking local (sin usar)
# - 24h testing en paralelo

# Fase 2: Migración
# - Usar HybridSynchronizer en main
# - Monitorear resultados
# - 48h testing

# Fase 3: Cleanup
# - Remover código viejo
# - Optimizar queries
# - Publicación a producción
```

### Paso 4: Validación
```python
# Verificar:
- [x] DB creada correctamente
- [x] Posiciones registradas
- [x] Sincronización funciona
- [x] Posiciones no se pierden
- [x] Timeout correcto
- [x] Tests pasan (100%)
```

---

## 🎯 CHECKLIST PRE-IMPLEMENTACIÓN

- [ ] Código de QuickFix verificado (líneas 850-881)
- [ ] Entendimiento del problema confirmado
- [ ] Plan de testing diseñado
- [ ] Resources (4-6 horas) asignados
- [ ] Environment de desarrollo preparado

---

## 📊 ESTIMACIÓN

| Tarea | Tiempo |
|-------|--------|
| Implementar LocalPositionTracker | 1.5h |
| Implementar HybridSynchronizer | 1.5h |
| Tests automatizados | 1h |
| Integración en CCXTOrchestrator | 1h |
| Testing manual (24h) | 2h |
| **TOTAL** | **6h** |

---

## 🚀 BENEFICIOS ESPERADOS

```
ANTES (Quick Fix):
- ⚠️  Posiciones desaparecen (2h timeout)
- ⚠️  Sin histórico de posiciones
- ⚠️  Dependencia de SAPI

DESPUÉS (LocalPositionTracker):
- ✅ Cero pérdida de datos
- ✅ Histórico completo en SQLite
- ✅ Independiente de SAPI
- ✅ Auditoría automática
- ✅ Recuperación ante crashes
```

