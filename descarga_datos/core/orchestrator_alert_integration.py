"""
✅ PHASE 2.1: INTEGRACIÓN DE ALERTAS EN ORCHESTRATOR

Integra el AlertManager con el CCXTLiveTradingOrchestrator
para monitoreo automático en tiempo real.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from utils.alert_manager import (
    AlertManager, AlertType, AlertSeverity, 
    AlertValidator, setup_alert_manager
)


class OrchestratorAlertIntegration:
    """
    Integración de alertas en el orchestrator de trading
    
    Responsabilidades:
    1. Monitorear sincronización de posiciones
    2. Detectar posiciones fantasma
    3. Validar balance
    4. Verificar trailing stops
    5. Detectar anomalías de P&L
    """
    
    def __init__(self, 
                 orchestrator: Any,
                 alert_manager: Optional[AlertManager] = None,
                 alert_config: Optional[Dict] = None):
        """
        Inicializar integración de alertas
        
        Args:
            orchestrator: CCXTLiveTradingOrchestrator instance
            alert_manager: AlertManager existente (opcional)
            alert_config: Configuración de alertas
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger('OrchestratorAlerts')
        
        # Crear o usar AlertManager existente
        if alert_manager:
            self.alert_manager = alert_manager
        else:
            self.alert_manager = setup_alert_manager(alert_config or {})
        
        # Validador
        self.validator = AlertValidator(self.alert_manager)
        
        # Estado de monitoreo
        self.last_balance_check = datetime.now()
        self.last_sync_check = datetime.now()
        self.last_trailing_stop_check = datetime.now()
        self.last_pnl_check = datetime.now()
        
        # Métricas anteriores para comparación
        self.prev_portfolio_value = 0.0
        self.prev_pnl = 0.0
        
        self.logger.info("Integración de alertas inicializada")
    
    # ========================================================================
    # MÉTODOS DE MONITOREO
    # ========================================================================
    
    async def check_sync_status(self) -> bool:
        """
        Verificar estado de sincronización con Binance
        
        Returns:
            bool: True si sincronización está OK
        """
        try:
            # Verificar tiempo desde última sincronización exitosa
            time_since_sync = (
                datetime.now() - self.alert_manager.last_sync_success
            ).total_seconds()
            
            max_age = self.alert_manager.thresholds.sync_max_age_seconds
            
            if time_since_sync > max_age:
                self.logger.warning(
                    f"Sincronización antigua: {time_since_sync:.0f}s "
                    f"(máximo: {max_age}s)"
                )
                self.alert_manager.create_alert(
                    alert_type=AlertType.SYNC_FAILED,
                    severity=AlertSeverity.WARNING,
                    title="⚠️ Sincronización antigua",
                    message=f"Última sincronización hace {time_since_sync:.0f}s",
                    additional_data={'seconds_since_sync': time_since_sync}
                )
                return False
            
            # Sincronización OK
            self.alert_manager.report_sync_success()
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando sincronización: {e}")
            self.alert_manager.report_sync_failure()
            return False
    
    async def check_balance_consistency(self) -> Optional[Dict]:
        """
        Verificar consistencia de balance entre sistema y Binance
        
        Returns:
            Dict con {system_balance, exchange_balance, mismatch_pct} o None
        """
        try:
            # Verificar si es hora de revisar
            time_since_check = (
                datetime.now() - self.last_balance_check
            ).total_seconds()
            
            if time_since_check < self.alert_manager.thresholds.balance_check_interval_seconds:
                return None
            
            self.last_balance_check = datetime.now()
            
            # Obtener balance del sistema
            system_balance = self.orchestrator.get_effective_portfolio_value()
            
            # Obtener balance de Binance
            exchange_balance = 0.0
            if hasattr(self.orchestrator, 'order_executor'):
                exchange = self.orchestrator.order_executor.exchange
                balance = exchange.fetch_balance()
                exchange_balance = balance.get('USDT', {}).get('total', 0.0)
            
            # Verificar discrepancia
            if exchange_balance > 0:
                mismatch_pct = abs(system_balance - exchange_balance) / exchange_balance * 100
            else:
                mismatch_pct = 0.0
            
            # Crear alerta si necesario
            result = {
                'system_balance': system_balance,
                'exchange_balance': exchange_balance,
                'mismatch_pct': mismatch_pct
            }
            
            self.alert_manager.check_balance_mismatch(
                system_balance, 
                exchange_balance
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando balance: {e}")
            return None
    
    async def check_phantom_positions(self) -> int:
        """
        Verificar y reportar posiciones fantasma
        
        Returns:
            int: Número de posiciones fantasma detectadas
        """
        try:
            phantom_count = 0
            
            # Comparar posiciones del sistema con Binance
            if hasattr(self.orchestrator, 'active_positions'):
                for ticket, position in self.orchestrator.active_positions.items():
                    # Verificar si existe en Binance
                    # TODO: Implementar verificación contra órdenes de Binance
                    pass
            
            return phantom_count
            
        except Exception as e:
            self.logger.error(f"Error verificando posiciones fantasma: {e}")
            return 0
    
    async def check_trailing_stops(self) -> Optional[Dict]:
        """
        Verificar estado de trailing stops
        
        Returns:
            Dict con número de posiciones sin actualizar trailing stop
        """
        try:
            # Verificar si es hora de revisar
            time_since_check = (
                datetime.now() - self.last_trailing_stop_check
            ).total_seconds()
            
            if time_since_check < self.alert_manager.thresholds.trailing_stop_check_interval_seconds:
                return None
            
            self.last_trailing_stop_check = datetime.now()
            
            not_updated = 0
            
            if hasattr(self.orchestrator, 'active_positions'):
                for ticket, position in self.orchestrator.active_positions.items():
                    # Verificar si trailing stop fue actualizado
                    if 'last_trailing_update' in position:
                        time_since_update = (
                            datetime.now() - position['last_trailing_update']
                        ).total_seconds()
                        
                        if time_since_update > self.alert_manager.thresholds.trailing_stop_check_interval_seconds * 2:
                            not_updated += 1
            
            # Generar alerta si hay muchas sin actualizar
            threshold = self.alert_manager.thresholds.trailing_stop_max_positions_not_updated
            if not_updated >= threshold:
                self.alert_manager.report_trailing_stop_error(not_updated)
            
            return {'positions_not_updated': not_updated}
            
        except Exception as e:
            self.logger.error(f"Error verificando trailing stops: {e}")
            return None
    
    async def check_pnl_anomalies(self) -> Optional[Dict]:
        """
        Verificar anomalías en P&L
        
        Returns:
            Dict con información de P&L o None
        """
        try:
            # Verificar si es hora de revisar
            time_since_check = (
                datetime.now() - self.last_pnl_check
            ).total_seconds()
            
            if time_since_check < self.alert_manager.thresholds.pnl_check_interval_seconds:
                return None
            
            self.last_pnl_check = datetime.now()
            
            # Obtener P&L actual
            current_pnl = 0.0  # TODO: Calcular desde posiciones cerradas
            
            # Comparar con anterior
            if self.prev_pnl != 0:
                pct_change = abs(current_pnl - self.prev_pnl) / abs(self.prev_pnl) * 100
                
                if pct_change > self.alert_manager.thresholds.pnl_spike_threshold_pct:
                    self.alert_manager.report_pnl_anomaly(
                        self.prev_pnl,
                        current_pnl,
                        pct_change
                    )
            
            self.prev_pnl = current_pnl
            
            return {'pnl': current_pnl}
            
        except Exception as e:
            self.logger.error(f"Error verificando P&L: {e}")
            return None
    
    # ========================================================================
    # MÉTODO PRINCIPAL DE MONITOREO
    # ========================================================================
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Ejecutar todas las verificaciones de alertas
        
        Returns:
            Dict con resultados de todas las verificaciones
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'active_alerts': len(self.alert_manager.get_active_alerts())
        }
        
        # Ejecutar todas las verificaciones
        results['checks']['sync'] = await self.check_sync_status()
        results['checks']['balance'] = await self.check_balance_consistency()
        results['checks']['phantom_positions'] = await self.check_phantom_positions()
        results['checks']['trailing_stops'] = await self.check_trailing_stops()
        results['checks']['pnl_anomalies'] = await self.check_pnl_anomalies()
        
        # Log resumen
        self.logger.debug(f"Verificaciones completadas: {results['checks']}")
        
        return results
    
    # ========================================================================
    # MÉTODOS DE UTILIDAD
    # ========================================================================
    
    def get_active_alerts(self):
        """Obtener alertas activas"""
        return self.alert_manager.get_active_alerts()
    
    def get_alert_summary(self) -> Dict:
        """Obtener resumen de alertas activas"""
        alerts = self.alert_manager.get_active_alerts()
        
        critical = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        warning = len([a for a in alerts if a.severity == AlertSeverity.WARNING])
        info = len([a for a in alerts if a.severity == AlertSeverity.INFO])
        
        return {
            'total': len(alerts),
            'critical': critical,
            'warning': warning,
            'info': info,
            'alerts': [
                {
                    'type': a.type.value,
                    'severity': a.severity.name,
                    'title': a.title,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in alerts
            ]
        }
    
    def configure_discord(self, webhook_url: str) -> None:
        """Configurar webhook de Discord"""
        self.alert_manager.enable_discord = True
        self.alert_manager.discord_webhook_url = webhook_url
        self.logger.info(f"Discord configurado: {webhook_url[:50]}...")
    
    def register_alert_callback(self, alert_type: AlertType, callback) -> None:
        """Registrar callback personalizado para alertas"""
        self.alert_manager.register_callback(alert_type, callback)
        self.logger.info(f"Callback registrado para {alert_type.value}")


# ============================================================================
# DECORADORES PARA MONITOREO AUTOMÁTICO
# ============================================================================

def monitored_operation(alert_integration: OrchestratorAlertIntegration):
    """
    Decorador para envolver operaciones del orchestrator
    con monitoreo automático de alertas
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Ejecutar checks después de operación
                await alert_integration.run_all_checks()
                
                return result
            except Exception as e:
                alert_integration.alert_manager.create_alert(
                    alert_type=AlertType.CONNECTION_ERROR,
                    severity=AlertSeverity.CRITICAL,
                    title=f"❌ Error en operación: {func.__name__}",
                    message=str(e),
                    additional_data={'function': func.__name__}
                )
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test
    print("✅ Módulo de integración de alertas cargado exitosamente")
