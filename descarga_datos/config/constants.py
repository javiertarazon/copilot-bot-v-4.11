"""
CONSTANTES GLOBALES DEL BOT DE TRADING v4.11
=============================================

Este archivo centraliza todos los "magic numbers" y constantes utilizadas
en el sistema para mejorar la mantenibilidad y legibilidad del código.

Creado durante auditoría: 29-Ene-2026
"""

# ==============================================================================
# CONSTANTES DE ML (Machine Learning)
# ==============================================================================

# Número mínimo de muestras requeridas para entrenamiento ML
MIN_TRAINING_SAMPLES = 100

# Número mínimo de velas para que los indicadores se estabilicen (warmup period)
MIN_INDICATOR_WARMUP = 20

# Período máximo de velas en posición antes de time exit
MAX_POSITION_BARS = 80

# Umbral de confianza ML por defecto
ML_CONFIDENCE_DEFAULT = 0.5

# Rango óptimo de confianza ML
ML_THRESHOLD_MIN_DEFAULT = 0.40
ML_THRESHOLD_MAX_DEFAULT = 0.85

# ==============================================================================
# CONSTANTES DE INDICADORES TÉCNICOS
# ==============================================================================

# Períodos de EMAs estándar
EMA_FAST_PERIOD = 10
EMA_MEDIUM_PERIOD = 20
EMA_SLOW_PERIOD = 200

# Período ATR por defecto
ATR_PERIOD_DEFAULT = 14

# Multiplicadores ATR para Stop Loss y Take Profit
STOP_LOSS_ATR_MULTIPLIER_DEFAULT = 2.5
TAKE_PROFIT_ATR_MULTIPLIER_DEFAULT = 3.75
TRAILING_STOP_ATR_MULTIPLIER_DEFAULT = 1.5

# RSI umbrales
RSI_OVERBOUGHT_DEFAULT = 70
RSI_OVERSOLD_DEFAULT = 30

# Stochastic umbrales
STOCH_OVERBOUGHT_DEFAULT = 85
STOCH_OVERSOLD_DEFAULT = 35

# CCI umbral
CCI_THRESHOLD_DEFAULT = 170

# ==============================================================================
# CONSTANTES DE GESTIÓN DE RIESGO
# ==============================================================================

# Riesgo máximo por trade (porcentaje del capital)
MAX_RISK_PER_TRADE_PERCENT = 1.0  # 1%

# Riesgo máximo por trade en USD
MAX_RISK_PER_TRADE_USD = 200.0  # $200 (conservador para live)

# Drawdown máximo permitido
MAX_DRAWDOWN_PERCENT = 0.25  # 25%

# Posiciones concurrentes máximas
MAX_CONCURRENT_TRADES_DEFAULT = 3

# Kelly Fraction conservador (cuarto-Kelly)
KELLY_FRACTION_DEFAULT = 0.25

# Límite de portfolio heat (exposición máxima)
MAX_PORTFOLIO_HEAT_DEFAULT = 0.15  # 15%

# Tamaño mínimo de posición
MIN_POSITION_SIZE = 0.01

# Tamaño máximo de posición en lotes
MAX_POSITION_SIZE_LOTS = 5.0

# ==============================================================================
# CONSTANTES DE COMPENSACIÓN (Reversal Strategy)
# ==============================================================================

# Umbral de pérdida para activar compensación (en USD)
COMPENSATION_LOSS_THRESHOLD = 2.0

# Número máximo de compensaciones consecutivas
MAX_CONSECUTIVE_COMPENSATIONS = 1

# Multiplicador de ATR para TP en compensación
COMPENSATION_TP_ATR_MULTIPLIER = 1.0

# Multiplicador de ATR para SL en compensación
COMPENSATION_SL_ATR_MULTIPLIER = 1.0

# Máximo de ATRs para objetivo de recuperación
MAX_RECOVERY_ATR_DISTANCE = 4.0

# ==============================================================================
# CONSTANTES DE BACKTESTING
# ==============================================================================

# Capital inicial por defecto
INITIAL_CAPITAL_DEFAULT = 10000.0

# Comisión por defecto (0.05%)
COMMISSION_DEFAULT = 0.0005

# Slippage por defecto (0.02%)
SLIPPAGE_DEFAULT = 0.0002

# Ratio Riesgo/Recompensa mínimo
MIN_RISK_REWARD_RATIO = 2.0

# ==============================================================================
# CONSTANTES DE TRAILING STOP
# ==============================================================================

# Porcentaje de activación del trailing stop
TRAILING_STOP_ACTIVATION_PCT = 0.65

# Porcentaje de protección del profit en trailing
TRAILING_STOP_PROTECTION_PCT = 0.65

# Umbral para activar trailing (% del riesgo inicial)
TRAILING_ACTIVATION_THRESHOLD = 0.35

# ==============================================================================
# CONSTANTES DE TIEMPO Y REINTENTOS
# ==============================================================================

# Máximo de reintentos para operaciones
MAX_RETRIES = 3

# Delay entre reintentos (segundos)
RETRY_DELAY_SECONDS = 5

# Timeout para operaciones (segundos)
OPERATION_TIMEOUT_SECONDS = 30

# Intervalo de sincronización de posiciones (segundos)
POSITION_SYNC_INTERVAL = 30

# ==============================================================================
# CONSTANTES DE VALIDACIÓN DE DATOS
# ==============================================================================

# Porcentaje máximo de NaN permitido en indicadores críticos
MAX_NAN_PERCENTAGE = 0.05  # 5%

# Mínimo de velas válidas después de limpieza
MIN_VALID_BARS_AFTER_CLEANING = 50

# ==============================================================================
# CONSTANTES DE LOGGING
# ==============================================================================

# Nivel de log por defecto
LOG_LEVEL_DEFAULT = "INFO"

# Máximo de mensajes de debug a mostrar en loops
MAX_DEBUG_MESSAGES_IN_LOOP = 30

# ==============================================================================
# CONSTANTES DE VOLUMEN (para índices sintéticos)
# ==============================================================================

# Umbral de volumen para instrumentos sintéticos (0 = deshabilitado)
SYNTHETIC_VOLUME_THRESHOLD = 0

# Ratio mínimo de volumen
VOLUME_RATIO_MIN_DEFAULT = 0.0

# Score mínimo de liquidez
LIQUIDITY_SCORE_MIN_DEFAULT = 5

# ==============================================================================
# CONSTANTES DE MÉTRICAS
# ==============================================================================

# Días de trading anuales (para Sharpe/Sortino)
ANNUAL_TRADING_DAYS = 252

# Tasa libre de riesgo por defecto
RISK_FREE_RATE_DEFAULT = 0.02  # 2%

# Período de lookback para métricas
METRICS_LOOKBACK_PERIOD = 100
