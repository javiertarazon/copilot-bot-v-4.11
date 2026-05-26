# Package for strategies
# 🎯 SISTEMA LIMPIO - Solo estrategia exitosa activa

# Importaciones opcionales para evitar problemas de dependencias
try:
    from .ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
    ULTRA_AVAILABLE = True
except ImportError as e:
    ULTRA_AVAILABLE = False
    UltraDetailedHeikinAshiMLStrategy = None
    print(f"Advertencia: UltraDetailedHeikinAshiMLStrategy no disponible: {e}")

try:
    from .simple_technical_strategy import SimpleTechnicalStrategy
    SIMPLE_TECHNICAL_AVAILABLE = True
except ImportError as e:
    SIMPLE_TECHNICAL_AVAILABLE = False
    SimpleTechnicalStrategy = None
    print(f"Advertencia: SimpleTechnicalStrategy no disponible: {e}")

# Lista de exports disponible
__all__ = []
if ULTRA_AVAILABLE:
    __all__.append('UltraDetailedHeikinAshiMLStrategy')
if SIMPLE_TECHNICAL_AVAILABLE:
    __all__.append('SimpleTechnicalStrategy')
