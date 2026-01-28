# ============================================================================== 
# SINGLETON FACTORY IMPLEMENTATION
# ==============================================================================

_RISK_MANAGER_INSTANCE = None

def get_risk_manager(config: Optional[Any] = None) -> AdvancedRiskManager:
    """
    Patrón Singleton robusto para obtener el RiskManager.
    Si se pasa 'config', se intentará configurar / actualizar la instancia.
    """
    global _RISK_MANAGER_INSTANCE
    
    if _RISK_MANAGER_INSTANCE is None:
        if config is None:
            # Si no hay configuración, intentar cargar valores por defecto seguros
            logger.warning("[RISK_FACTORY] Inicializando RiskManager sin configuración explícita.")
            _RISK_MANAGER_INSTANCE = AdvancedRiskManager()
        else:
            _RISK_MANAGER_INSTANCE = AdvancedRiskManager()
            _RISK_MANAGER_INSTANCE.configure(config)
            
    return _RISK_MANAGER_INSTANCE
