"""
✅ PHASE 2.1: SISTEMA DE ALERTAS AUTOMÁTICAS

Módulo que implementa alertas en tiempo real para:
1. Posiciones fantasma detectadas
2. Sincronización fallida con Binance
3. Discrepancia de balance > umbral
4. Trailing stop no actualizado
5. P&L inesperado
6. Comisiones anormales

Las alertas se envían por:
- Logs (siempre)
- Email (críticas)
- Discord webhook (todas)
- Dashboard (todas)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

# ============================================================================
# CONFIGURACIÓN DE ALERTAS
# ============================================================================

class AlertSeverity(Enum):
    """Niveles de severidad de alerta"""
    INFO = 1
    WARNING = 2
    CRITICAL = 3


class AlertType(Enum):
    """Tipos de alertas del sistema"""
    PHANTOM_POSITION = "phantom_position"
    SYNC_FAILED = "sync_failed"
    BALANCE_MISMATCH = "balance_mismatch"
    TRAILING_STOP_ERROR = "trailing_stop_error"
    PNL_ANOMALY = "pnl_anomaly"
    FEE_ANOMALY = "fee_anomaly"
    ORDER_TIMEOUT = "order_timeout"
    CONNECTION_ERROR = "connection_error"
    DATA_ERROR = "data_error"


# ============================================================================
# CLASES DE DATOS
# ============================================================================

@dataclass
class Alert:
    """Estructura de una alerta"""
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    additional_data: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario serializable"""
        return {
            'type': self.type.value,
            'severity': self.severity.name,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'additional_data': self.additional_data,
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }


@dataclass
class AlertThresholds:
    """Umbrales para alertas automáticas"""
    # Balance
    balance_mismatch_pct: float = 0.1  # Alerta si diferencia > 0.1%
    balance_check_interval_seconds: int = 300  # Cada 5 minutos
    
    # Sincronización
    sync_max_failures_consecutive: int = 3  # Alerta si 3 fallos seguidos
    sync_max_age_seconds: int = 120  # Alerta si última sync > 2 minutos
    
    # Trailing Stop
    trailing_stop_check_interval_seconds: int = 60  # Cada 1 minuto
    trailing_stop_max_positions_not_updated: int = 5  # Alerta si 5+ posiciones no actualizadas
    
    # P&L
    pnl_spike_threshold_pct: float = 50.0  # Alerta si P&L cambia > 50% de repente
    pnl_check_interval_seconds: int = 60
    
    # Comisiones
    fee_anomaly_threshold: float = 0.003  # Alerta si comisión > 0.3%
    
    # Conexión
    connection_timeout_seconds: int = 30


# ============================================================================
# SISTEMA DE ALERTAS
# ============================================================================

class AlertManager:
    """
    Gestor centralizado de alertas del sistema.
    
    Responsabilidades:
    1. Recibir alertas de diferentes módulos
    2. Filtrar y deduplicar
    3. Persistir en historial
    4. Enviar notificaciones
    5. Mantener estado de alertas activas
    """
    
    def __init__(self, 
                 log_file: Optional[Path] = None,
                 alert_history_file: Optional[Path] = None,
                 enable_discord: bool = False,
                 enable_email: bool = False,
                 discord_webhook_url: Optional[str] = None,
                 email_config: Optional[Dict] = None):
        """
        Inicializar gestor de alertas
        
        Args:
            log_file: Archivo para guardar logs de alertas
            alert_history_file: Archivo para historial de alertas
            enable_discord: Habilitar notificaciones Discord
            enable_email: Habilitar notificaciones email
            discord_webhook_url: URL webhook de Discord
            email_config: Configuración de email
        """
        self.logger = logging.getLogger('AlertManager')
        self.log_file = log_file or Path(__file__).parent.parent / "logs" / "alerts.log"
        self.alert_history_file = alert_history_file or Path(__file__).parent.parent / "data" / "alert_history.json"
        
        # Estado
        self.active_alerts: Dict[str, Alert] = {}  # Alertas activas por ID
        self.alert_history: List[Alert] = []  # Historial de todas las alertas
        self.sync_failure_count = 0
        self.last_sync_success = datetime.now()
        
        # Configuración
        self.thresholds = AlertThresholds()
        self.enable_discord = enable_discord
        self.enable_email = enable_email
        self.discord_webhook_url = discord_webhook_url
        self.email_config = email_config
        
        # Callbacks personalizados
        self.callbacks: Dict[AlertType, List[Callable]] = {}
        
        # Guardar configuración inicial
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar historial previo
        self._load_history()
    
    def register_callback(self, alert_type: AlertType, callback: Callable) -> None:
        """Registrar callback personalizado para tipo de alerta"""
        if alert_type not in self.callbacks:
            self.callbacks[alert_type] = []
        self.callbacks[alert_type].append(callback)
    
    def _generate_alert_id(self, alert_type: AlertType) -> str:
        """Generar ID único para alerta (por tipo, se deduplica)"""
        return f"{alert_type.value}"
    
    def create_alert(self,
                     alert_type: AlertType,
                     severity: AlertSeverity,
                     title: str,
                     message: str,
                     additional_data: Optional[Dict] = None) -> Alert:
        """
        Crear y registrar nueva alerta
        
        Args:
            alert_type: Tipo de alerta
            severity: Nivel de severidad
            title: Título corto
            message: Mensaje detallado
            additional_data: Datos adicionales
            
        Returns:
            Alert: Alerta creada
        """
        alert = Alert(
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            additional_data=additional_data
        )
        
        alert_id = self._generate_alert_id(alert_type)
        
        # Si alerta de mismo tipo está activa, actualizar
        if alert_id in self.active_alerts:
            old_alert = self.active_alerts[alert_id]
            self.logger.warning(
                f"Alerta duplicada: {title}\n"
                f"  Anterior: {old_alert.timestamp}\n"
                f"  Nueva: {alert.timestamp}\n"
                f"  Diferencia: {(alert.timestamp - old_alert.timestamp).total_seconds()}s"
            )
        
        # Guardar como activa
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Log
        self._log_alert(alert)
        
        # Notificaciones
        self._send_notifications(alert)
        
        # Callbacks
        if alert_type in self.callbacks:
            for callback in self.callbacks[alert_type]:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error en callback: {e}")
        
        # Persistir
        self._save_history()
        
        return alert
    
    def resolve_alert(self, alert_type: AlertType) -> Optional[Alert]:
        """Resolver alerta de tipo específico"""
        alert_id = self._generate_alert_id(alert_type)
        
        if alert_id not in self.active_alerts:
            return None
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolution_time = datetime.now()
        
        self.logger.info(
            f"✅ Alerta resuelta: {alert.title}\n"
            f"  Duración: {(alert.resolution_time - alert.timestamp).total_seconds()}s"
        )
        
        # Guardar resolución
        self._save_history()
        
        del self.active_alerts[alert_id]
        return alert
    
    def _log_alert(self, alert: Alert) -> None:
        """Registrar alerta en log"""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🔴"
        }
        
        emoji = severity_emoji.get(alert.severity, "❓")
        
        log_msg = (
            f"\n{emoji} ALERTA [{alert.severity.name}]: {alert.title}\n"
            f"   Tipo: {alert.type.value}\n"
            f"   Tiempo: {alert.timestamp.isoformat()}\n"
            f"   Mensaje: {alert.message}"
        )
        
        if alert.additional_data:
            log_msg += f"\n   Datos: {json.dumps(alert.additional_data, default=str, indent=2)}"
        
        if alert.severity == AlertSeverity.CRITICAL:
            self.logger.critical(log_msg)
        elif alert.severity == AlertSeverity.WARNING:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
    
    def _send_notifications(self, alert: Alert) -> None:
        """Enviar notificaciones (Discord, email, etc)"""
        
        # Discord webhook
        if self.enable_discord and self.discord_webhook_url:
            self._send_discord_notification(alert)
        
        # Email
        if self.enable_email and self.email_config:
            self._send_email_notification(alert)
    
    def _send_discord_notification(self, alert: Alert) -> None:
        """Enviar alerta a Discord"""
        try:
            import requests
            
            color_map = {
                AlertSeverity.INFO: 3447003,  # Blue
                AlertSeverity.WARNING: 16776960,  # Yellow
                AlertSeverity.CRITICAL: 15158332  # Red
            }
            
            payload = {
                "embeds": [{
                    "title": alert.title,
                    "description": alert.message,
                    "color": color_map.get(alert.severity, 3447003),
                    "fields": [
                        {"name": "Tipo", "value": alert.type.value, "inline": True},
                        {"name": "Severidad", "value": alert.severity.name, "inline": True},
                        {"name": "Tiempo", "value": alert.timestamp.isoformat(), "inline": False}
                    ]
                }]
            }
            
            if alert.additional_data:
                payload["embeds"][0]["fields"].append({
                    "name": "Datos",
                    "value": f"```json\n{json.dumps(alert.additional_data, indent=2)}\n```",
                    "inline": False
                })
            
            requests.post(self.discord_webhook_url, json=payload, timeout=5)
            self.logger.debug("Notificación Discord enviada")
        except Exception as e:
            self.logger.error(f"Error enviando notificación Discord: {e}")
    
    def _send_email_notification(self, alert: Alert) -> None:
        """Enviar alerta por email"""
        # TODO: Implementar si es necesario
        pass
    
    def _save_history(self) -> None:
        """Guardar historial de alertas a archivo"""
        try:
            alerts_data = [alert.to_dict() for alert in self.alert_history]
            with open(self.alert_history_file, 'w') as f:
                json.dump(alerts_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error guardando historial de alertas: {e}")
    
    def _load_history(self) -> None:
        """Cargar historial previo de alertas"""
        try:
            if self.alert_history_file.exists():
                with open(self.alert_history_file, 'r') as f:
                    alerts_data = json.load(f)
                    self.logger.info(f"Cargadas {len(alerts_data)} alertas del historial")
        except Exception as e:
            self.logger.error(f"Error cargando historial de alertas: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtener todas las alertas activas"""
        return list(self.active_alerts.values())
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Obtener alertas de un tipo específico"""
        return [a for a in self.alert_history if a.type == alert_type]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Obtener alertas por severidad"""
        return [a for a in self.alert_history if a.severity == severity]
    
    def report_sync_failure(self) -> None:
        """Reportar fallo de sincronización"""
        self.sync_failure_count += 1
        
        if self.sync_failure_count >= self.thresholds.sync_max_failures_consecutive:
            self.create_alert(
                alert_type=AlertType.SYNC_FAILED,
                severity=AlertSeverity.CRITICAL,
                title="❌ Sincronización de Binance fallando",
                message=f"Ha fallado {self.sync_failure_count} sincronizaciones consecutivas. "
                        "El sistema puede estar desincronizado.",
                additional_data={
                    'failures': self.sync_failure_count,
                    'threshold': self.thresholds.sync_max_failures_consecutive
                }
            )
    
    def report_sync_success(self) -> None:
        """Reportar sincronización exitosa"""
        self.sync_failure_count = 0
        self.last_sync_success = datetime.now()
        
        # Resolver alerta si estaba activa
        self.resolve_alert(AlertType.SYNC_FAILED)
    
    def check_balance_mismatch(self, system_balance: float, exchange_balance: float) -> Optional[Alert]:
        """Verificar discrepancia de balance"""
        if exchange_balance <= 0:
            return None
        
        mismatch_pct = abs(system_balance - exchange_balance) / exchange_balance * 100
        
        if mismatch_pct > self.thresholds.balance_mismatch_pct:
            alert = self.create_alert(
                alert_type=AlertType.BALANCE_MISMATCH,
                severity=AlertSeverity.WARNING,
                title=f"⚠️ Discrepancia de balance: {mismatch_pct:.4f}%",
                message=f"Balance del sistema: ${system_balance:.2f}\n"
                        f"Balance en Binance: ${exchange_balance:.2f}\n"
                        f"Diferencia: ${abs(system_balance - exchange_balance):.2f}",
                additional_data={
                    'system_balance': system_balance,
                    'exchange_balance': exchange_balance,
                    'mismatch_pct': mismatch_pct
                }
            )
            return alert
        else:
            # Resolver alerta si estaba activa
            self.resolve_alert(AlertType.BALANCE_MISMATCH)
        
        return None
    
    def report_phantom_position(self, position_id: str, side: str, quantity: float, price: float) -> Alert:
        """Reportar posición fantasma detectada"""
        return self.create_alert(
            alert_type=AlertType.PHANTOM_POSITION,
            severity=AlertSeverity.CRITICAL,
            title="🔴 Posición fantasma detectada",
            message=f"Posición sin pareja encontrada: {side.upper()} {quantity} @ ${price}",
            additional_data={
                'position_id': position_id,
                'side': side,
                'quantity': quantity,
                'price': price
            }
        )
    
    def report_trailing_stop_error(self, num_positions: int) -> Alert:
        """Reportar error en actualización de trailing stop"""
        return self.create_alert(
            alert_type=AlertType.TRAILING_STOP_ERROR,
            severity=AlertSeverity.WARNING,
            title=f"⚠️ {num_positions} posiciones sin actualizar trailing stop",
            message=f"Se encontraron {num_positions} posiciones sin actualizar su trailing stop "
                    "en el último ciclo de revisión.",
            additional_data={'affected_positions': num_positions}
        )
    
    def report_pnl_anomaly(self, expected_pnl: float, actual_pnl: float, pct_diff: float) -> Alert:
        """Reportar anomalía en P&L"""
        return self.create_alert(
            alert_type=AlertType.PNL_ANOMALY,
            severity=AlertSeverity.WARNING,
            title=f"⚠️ Anomalía en P&L: {pct_diff:+.2f}%",
            message=f"P&L esperado: ${expected_pnl:.2f}\n"
                    f"P&L actual: ${actual_pnl:.2f}\n"
                    f"Diferencia: {pct_diff:+.2f}%",
            additional_data={
                'expected_pnl': expected_pnl,
                'actual_pnl': actual_pnl,
                'pct_diff': pct_diff
            }
        )


# ============================================================================
# VALIDADORES DE ALERTAS
# ============================================================================

class AlertValidator:
    """Validador que ejecuta checks y genera alertas automáticamente"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.logger = logging.getLogger('AlertValidator')
        self.last_pnl_value = 0.0
    
    async def validate_all(self,
                           orchestrator: Optional[Any] = None,
                           executor: Optional[Any] = None) -> List[Alert]:
        """
        Ejecutar todas las validaciones
        
        Args:
            orchestrator: Trading orchestrator
            executor: Order executor
            
        Returns:
            Lista de alertas generadas
        """
        alerts = []
        
        if orchestrator:
            # Validar sync
            time_since_sync = (datetime.now() - self.alert_manager.last_sync_success).total_seconds()
            if time_since_sync > self.alert_manager.thresholds.sync_max_age_seconds:
                alerts.append(self.alert_manager.create_alert(
                    alert_type=AlertType.SYNC_FAILED,
                    severity=AlertSeverity.WARNING,
                    title="⚠️ Última sincronización hace mucho tiempo",
                    message=f"Última sincronización: {time_since_sync:.0f}s atrás",
                    additional_data={'seconds_since_sync': time_since_sync}
                ))
        
        if executor:
            # Validar comisiones
            pass
        
        return alerts


# ============================================================================
# SETUP INICIAL
# ============================================================================

def setup_alert_manager(config: Optional[Dict] = None) -> AlertManager:
    """Factory para crear AlertManager con configuración"""
    
    if config is None:
        config = {}
    
    # Crear logger para alertas
    logger = logging.getLogger('AlertManager')
    handler = logging.FileHandler(
        config.get('log_file', Path(__file__).parent.parent / "logs" / "alerts.log")
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Crear gestor
    alert_manager = AlertManager(
        enable_discord=config.get('enable_discord', False),
        enable_email=config.get('enable_email', False),
        discord_webhook_url=config.get('discord_webhook_url'),
        email_config=config.get('email_config')
    )
    
    return alert_manager


if __name__ == "__main__":
    # Test básico
    manager = setup_alert_manager()
    
    # Crear alerta de prueba
    alert = manager.create_alert(
        alert_type=AlertType.SYNC_FAILED,
        severity=AlertSeverity.WARNING,
        title="Test Alert",
        message="This is a test alert",
        additional_data={'test': True}
    )
    
    print(f"Alerta creada: {alert.title}")
    print(f"Alertas activas: {len(manager.get_active_alerts())}")
