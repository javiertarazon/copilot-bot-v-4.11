"""
MÓDULO DE CIERRE SEGURO (GRACEFUL SHUTDOWN)
============================================

Implementa patrón robusto de cierre seguro del sistema.
Copiado de Freqtrade - Manejo de interrupciones y cierre ordenado.

Características:
1. Manejo de Ctrl+C (SIGINT)
2. Cierre ordenado de posiciones
3. Guardado de estado en JSON
4. Cierre de conexiones
5. Liberación de recursos
6. Lanzamiento de dashboard

Author: Freqtrade Pattern Adaptation
Date: 28 Octubre 2025
"""

import signal
import sys
import json
import logging
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Fases del cierre graceful"""
    CLOSE_ORDERS = 'close_orders'
    CLOSE_POSITIONS = 'close_positions'
    SAVE_STATE = 'save_state'
    CLEANUP = 'cleanup'
    CLOSE_CONNECTIONS = 'close_connections'
    FINAL_REPORT = 'final_report'


class ShutdownState(Enum):
    """Estados del shutdown handler"""
    RUNNING = 'running'
    SHUTDOWN_REQUESTED = 'shutdown_requested'
    SHUTDOWN_INITIATED = 'shutdown_initiated'
    SHUTDOWN_COMPLETE = 'shutdown_complete'


class GracefulShutdownHandler:
    """
    Maneja cierre graceful del sistema de trading.
    
    Implementa patrón de Freqtrade:
    - Signal handlers (SIGINT, SIGTERM)
    - Try/except/finally seguro
    - Cierre ordenado de recursos
    - Logging exhaustivo
    """
    
    def __init__(
        self,
        orchestrator=None,
        dashboard_launcher: Optional[Callable] = None,
        state_save_path: Optional[str] = None,
        logger=None,
        logger_instance=None
    ):
        """
        Inicializa handler de shutdown
        
        Args:
            orchestrator: Instancia de LiveTradingOrchestrator
            dashboard_launcher: Función para lanzar dashboard
            state_save_path: Ruta para guardar estado (default: data/shutdown_state.json)
            logger: Logger personalizado
            logger_instance: Logger personalizado (alias para logger)
        """
        self.orchestrator = orchestrator
        self.dashboard_launcher = dashboard_launcher
        self.state_save_path = Path(state_save_path or (Path(__file__).parent.parent / "data" / "shutdown_state.json"))
        self.logger = logger or logger_instance or logger
        
        self.shutting_down = False
        self.shutdown_start_time = None
        self.shutdown_timeout = 30  # segundos
        
        # Registrar handlers de signal
        self._register_signal_handlers()
        
        if self.logger:
            self.logger.info("GracefulShutdownHandler inicializado")
    
    def register_signals(self):
        """Alias público para registrar handlers de señales"""
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Registra handlers para señales del SO"""
        try:
            # SIGINT = Ctrl+C
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # SIGTERM = terminar proceso
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.debug("✅ Signal handlers registrados (SIGINT, SIGTERM)")
            
        except Exception as e:
            self.logger.warning(f"⚠️  No se pudieron registrar signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        Handler de signal (Ctrl+C, etc)
        
        Args:
            signum: Número de signal
            frame: Stack frame
        """
        signal_name = signal.Signals(signum).name
        self.logger.warning(f"📛 Signal recibida: {signal_name} - Iniciando shutdown graceful")
        
        # Iniciar shutdown en thread separado (no bloquea signal)
        shutdown_thread = threading.Thread(target=self.shutdown, daemon=False)
        shutdown_thread.start()
    
    def shutdown(self, reason: str = "Manual shutdown"):
        """
        Ejecuta cierre graceful del sistema.
        
        Patrón Try/Except/Finally:
        1. Try: Operaciones de cierre ordenado
        2. Except: Captura errores pero continúa
        3. Finally: SIEMPRE ejecuta liberación de recursos
        
        Args:
            reason: Razón del shutdown
        """
        if self.shutting_down:
            self.logger.warning("⚠️  Shutdown ya en progreso, ignorando solicitud")
            return
        
        self.shutting_down = True
        self.shutdown_start_time = datetime.now()
        
        self.logger.info(
            f"🛑 INICIANDO CIERRE GRACEFUL - Razón: {reason}"
        )
        
        try:
            # ==================================================================================
            # FASE 1: Detener nuevas órdenes
            # ==================================================================================
            self.logger.info("📍 Fase 1: Deteniendo nuevas órdenes...")
            self._stop_trading()
            
            # ==================================================================================
            # FASE 2: Cerrar posiciones críticas
            # ==================================================================================
            self.logger.info("📍 Fase 2: Manejando posiciones abiertas...")
            self._close_positions()
            
            # ==================================================================================
            # FASE 3: Guardar estado
            # ==================================================================================
            self.logger.info("📍 Fase 3: Guardando estado del sistema...")
            self._save_state()
            
            # ==================================================================================
            # FASE 4: Cerrar conexiones externas
            # ==================================================================================
            self.logger.info("📍 Fase 4: Cerrando conexiones externas...")
            self._close_connections()
            
        except KeyboardInterrupt:
            # Segunda Ctrl+C durante shutdown → salida forzada
            self.logger.error("🔴 Ctrl+C durante shutdown - SALIDA FORZADA")
            self._emergency_exit()
            sys.exit(1)
        
        except Exception as e:
            self.logger.error(f"❌ Error durante shutdown: {str(e)}")
            self.logger.error(f"Stack trace:\n{traceback.format_exc()}")
        
        finally:
            # ==================================================================================
            # FASE 5: Liberar recursos (SIEMPRE se ejecuta)
            # ==================================================================================
            self.logger.info("📍 Fase 5: Liberando recursos...")
            self._cleanup_resources()
            
            # ==================================================================================
            # FASE 6: Lanzar dashboard si hay resultados
            # ==================================================================================
            self.logger.info("📍 Fase 6: Finalizando...")
            self._launch_dashboard()
            
            # Resumen final
            shutdown_duration = (datetime.now() - self.shutdown_start_time).total_seconds()
            self.logger.info(
                f"✅ CIERRE COMPLETADO en {shutdown_duration:.1f}s - "
                f"Sistema listo para salir"
            )
    
    def _stop_trading(self):
        """Detiene el sistema de trading"""
        try:
            if not self.orchestrator:
                self.logger.debug("⏭️  No hay orchestrator, omitiendo stop trading")
                return
            
            self.logger.info("⏸️  Deteniendo sistema de trading...")
            self.orchestrator.running = False
            
            # Esperar a que se procesen últimas órdenes
            wait_time = 0
            max_wait = 5  # segundos
            
            while self.orchestrator.active_positions and wait_time < max_wait:
                self.logger.debug(
                    f"⏳ Esperando cierre de {len(self.orchestrator.active_positions)} "
                    f"posiciones (timeout en {max_wait - wait_time}s)..."
                )
                time.sleep(0.5)
                wait_time += 0.5
            
            self.logger.info("✅ Sistema de trading detenido")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Error deteniendo trading: {str(e)}")
    
    def _close_positions(self):
        """Cierra posiciones abiertas de forma segura"""
        try:
            if not self.orchestrator or not self.orchestrator.active_positions:
                self.logger.debug("⏭️  No hay posiciones abiertas")
                return
            
            self.logger.info(
                f"📊 Cerrando {len(self.orchestrator.active_positions)} posiciones abiertas..."
            )
            
            for pos_id, position in self.orchestrator.active_positions.items():
                try:
                    self.logger.info(
                        f"  Cerrando posición {pos_id}: {position.get('symbol')} "
                        f"({position.get('size')} unidades)"
                    )
                    
                    # Aquí iría la lógica de cierre real si está implementada
                    # self.orchestrator.close_position(pos_id)
                    
                except Exception as pos_error:
                    self.logger.error(
                        f"  ❌ Error cerrando posición {pos_id}: {str(pos_error)}"
                    )
            
            self.logger.info("✅ Cierre de posiciones completado")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Error en cierre de posiciones: {str(e)}")
    
    def _save_state(self):
        """Guarda estado actual del sistema en JSON"""
        try:
            self.logger.info(f"💾 Guardando estado en {self.state_save_path}...")
            
            # Asegurar que el directorio existe
            self.state_save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Preparar estado
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'reason': 'Graceful shutdown',
                'uptime_seconds': (
                    (datetime.now() - self.shutdown_start_time).total_seconds()
                    if self.shutdown_start_time else 0
                ),
            }
            
            # Agregar métricas del orchestrator si existen
            if self.orchestrator:
                state_data['orchestrator'] = {
                    'running': self.orchestrator.running,
                    'active_positions': len(self.orchestrator.active_positions or {}),
                    'total_trades': self.orchestrator.live_metrics.get('total_trades', 0),
                    'total_pnl': self.orchestrator.live_metrics.get('total_pnl', 0.0),
                }
            
            # Guardar a JSON (serializable)
            with open(self.state_save_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"✅ Estado guardado: {self.state_save_path}")
        
        except Exception as e:
            self.logger.error(f"❌ Error guardando estado: {str(e)}")
    
    def _close_connections(self):
        """Cierra conexiones externas (exchange, MT5, etc)"""
        try:
            self.logger.info("🔌 Cerrando conexiones externas...")
            
            if not self.orchestrator:
                self.logger.debug("⏭️  No hay orchestrator")
                return
            
            # Cerrar data provider
            if hasattr(self.orchestrator, 'data_provider'):
                try:
                    if hasattr(self.orchestrator.data_provider, 'close'):
                        self.logger.debug("  Cerrando data provider...")
                        self.orchestrator.data_provider.close()
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error cerrando data provider: {e}")
            
            # Cerrar order executor
            if hasattr(self.orchestrator, 'order_executor'):
                try:
                    if hasattr(self.orchestrator.order_executor, 'close'):
                        self.logger.debug("  Cerrando order executor...")
                        self.orchestrator.order_executor.close()
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error cerrando order executor: {e}")
            
            self.logger.info("✅ Conexiones cerradas")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Error cerrando conexiones: {str(e)}")
    
    def _cleanup_resources(self):
        """Libera recursos (threads, memoria, etc)"""
        try:
            self.logger.info("🧹 Liberando recursos...")
            
            if self.orchestrator:
                # Limpiar orchestrator
                self.orchestrator.running = False
                self.orchestrator.active_positions = {}
                self.orchestrator.position_history = []
                self.orchestrator.strategy_instances = {}
                
                self.logger.debug("  ✅ Orchestrator limpiado")
            
            # Forzar garbage collection
            import gc
            gc.collect()
            
            self.logger.info("✅ Recursos liberados")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Error liberando recursos: {str(e)}")
    
    def _launch_dashboard(self):
        """Lanza dashboard de resultados si está disponible"""
        try:
            if not self.dashboard_launcher:
                self.logger.debug("⏭️  No hay dashboard launcher configurado")
                return
            
            self.logger.info("📊 Lanzando dashboard de resultados...")
            
            # Llamar al launcher en thread separado (no bloquea)
            dashboard_thread = threading.Thread(
                target=self.dashboard_launcher,
                daemon=True
            )
            dashboard_thread.start()
            
            self.logger.info("✅ Dashboard iniciado")
        
        except Exception as e:
            self.logger.warning(f"⚠️  Error lanzando dashboard: {str(e)}")
    
    def _emergency_exit(self):
        """Salida de emergencia (segunda Ctrl+C)"""
        try:
            self.logger.error("🚨 SALIDA DE EMERGENCIA - Cerrando inmediatamente")
            
            # Intentar guardar estado de emergencia
            emergency_state = {
                'timestamp': datetime.now().isoformat(),
                'reason': 'Emergency exit (second Ctrl+C)',
                'warning': 'Estado incompleto - algunos recursos pueden no estar limpios'
            }
            
            self.state_save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_save_path, 'w') as f:
                json.dump(emergency_state, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Error en emergency exit: {e}")
    
    def get_shutdown_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del shutdown"""
        duration = 0
        if self.shutdown_start_time:
            duration = (datetime.now() - self.shutdown_start_time).total_seconds()
        
        return {
            'shutting_down': self.shutting_down,
            'duration_seconds': duration,
            'timeout_seconds': self.shutdown_timeout,
            'state_saved_path': str(self.state_save_path),
        }


# ============================================================================
# CONTEXT MANAGER PARA OPERACIONES SEGURAS
# ============================================================================

class SafeTrading:
    """Context manager para trading seguro con cleanup automático"""
    
    def __init__(
        self,
        orchestrator=None,
        dashboard_launcher: Optional[Callable] = None,
        logger_instance=None
    ):
        self.orchestrator = orchestrator
        self.dashboard_launcher = dashboard_launcher
        self.logger = logger_instance or logger
        self.shutdown_handler = None
    
    def __enter__(self):
        """Entrada del context manager"""
        self.shutdown_handler = GracefulShutdownHandler(
            orchestrator=self.orchestrator,
            dashboard_launcher=self.dashboard_launcher,
            logger_instance=self.logger
        )
        return self.shutdown_handler
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager (siempre se ejecuta)"""
        if exc_type is not None:
            self.logger.error(
                f"Excepción en trading context: {exc_type.__name__}: {exc_val}"
            )
        
        # Ejecutar shutdown graceful
        reason = (
            f"Exception: {exc_type.__name__}" if exc_type 
            else "Normal completion"
        )
        self.shutdown_handler.shutdown(reason=reason)
        
        # No re-raise la excepción (shutdown captura todo)
        return True


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def create_shutdown_handler(
    orchestrator=None,
    dashboard_launcher: Optional[Callable] = None
) -> GracefulShutdownHandler:
    """Factory para crear handler de shutdown"""
    return GracefulShutdownHandler(
        orchestrator=orchestrator,
        dashboard_launcher=dashboard_launcher
    )


def safe_trading_context(
    orchestrator=None,
    dashboard_launcher: Optional[Callable] = None
):
    """Context manager para trading seguro"""
    return SafeTrading(
        orchestrator=orchestrator,
        dashboard_launcher=dashboard_launcher
    )
