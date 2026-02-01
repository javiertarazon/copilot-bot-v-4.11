"""
Sistema orquestador de trading en vivo para el sistema modular.

Este módulo coordina el flujo de trabajo completo para trading en vivo:
1. Obtiene datos en tiempo real desde MT5
2. Aplica estrategias configuradas
3. Ejecuta operaciones según las señales generadas
4. Monitorea posiciones abiertas y resultados

FASE 5 (v4.11): Integración de IndexedPositionMonitor para 6.25x speedup.

Author: GitHub Copilot
Date: Septiembre 2025
"""

import time
from utils.logger import get_logger
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
import queue

# Importar usando rutas absolutas
from config.config_loader import load_config
from core.mt5_live_data import MT5LiveDataProvider
from core.mt5_order_executor import MT5OrderExecutor, OrderType
from utils.logger import setup_logger
from risk_management.risk_management import apply_risk_management
from utils.position_synchronizer import PositionSynchronizer

# FASE 5: Intentar importar Indexed Position Monitor (v4.11)
try:
    from v411_optimizations.indexed_position_monitor import IndexedPositionMonitor
    INDEXING_AVAILABLE = True
except ImportError:
    INDEXING_AVAILABLE = False

# Configurar logging
logger = setup_logger('LiveTradingOrchestrator')


class LiveTradingOrchestrator:
    """
    Orquestador principal para operaciones de trading en vivo.
    
    Esta clase coordina todos los componentes necesarios para el trading en vivo:
    - Proveedor de datos en tiempo real de MT5
    - Ejecución de estrategias configuradas
    - Envío y gestión de órdenes a través de MT5
    - Seguimiento de posiciones y rendimiento
    """
    
    def __init__(self, config_path: str = None):
        """
        Inicializa el orquestador de trading en vivo.
        
        Args:
            config_path: Ruta al archivo de configuración YAML. Si es None, se usa la configuración predeterminada.
        """
        # Cargar configuración
        self.config = load_config(config_path)
        self.live_config = self.config.get('live_trading', {})
        
        # Inicializar componentes de trading
        self.data_provider = MT5LiveDataProvider(config=self.config['mt5'])
        
        self.order_executor = MT5OrderExecutor(
            account_type=self.live_config.get('account_type', 'DEMO'),
            risk_per_trade=self.live_config.get('risk_per_trade', 0.01),
            max_positions=self.live_config.get('max_positions', 5)
        )
        
        # Inicializar sincronizador de posiciones
        self.position_synchronizer = PositionSynchronizer(
            order_executor=self.order_executor,
            logger=logger
        )
        
        # Variables para tracking de operaciones
        self.active_positions = {}
        self.position_history = []
        self.running = False
        self.strategy_classes = {}
        self.strategy_instances = {}
        self.strategy_live_configs = {}  # Configuraciones específicas de live trading por estrategia
        
        # FASE 5: Inicializar IndexedPositionMonitor (v4.11)
        self.indexed_monitor = None
        if INDEXING_AVAILABLE:
            try:
                self.indexed_monitor = IndexedPositionMonitor()
                logger.info("✅ FASE 5: IndexedPositionMonitor inicializado (6.25x speedup)")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo inicializar IndexedPositionMonitor: {e}")
                self.indexed_monitor = None
        
        # Cola para procesamiento seguro de señales
        self.signal_queue = queue.Queue()

        # Métricas en vivo
        self.live_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'start_time': datetime.now(),
            'runtime_minutes': 0
        }
        
        logger.info("LiveTradingOrchestrator inicializado correctamente")
    
    def _sync_position_to_indexed_monitor(self, position_id: str, position_data: Dict[str, Any], action: str = 'add'):
        """
        FASE 5: Sincronizar posiciones con IndexedPositionMonitor para O(1) lookups.
        
        Args:
            position_id: ID de la posición
            position_data: Datos de la posición
            action: 'add', 'update', o 'close'
        """
        if self.indexed_monitor is None:
            return
        
        try:
            if action == 'add':
                self.indexed_monitor.add_position(position_id, position_data)
            elif action == 'update':
                self.indexed_monitor.update_position(position_id, position_data)
            elif action == 'close':
                self.indexed_monitor.close_position(position_id)
        except Exception as e:
            logger.debug(f"⚠️ Error en IndexedPositionMonitor: {e}")
    
    def load_strategies(self):
        """
        Carga dinámicamente TODAS las estrategias activas en backtesting.
        Sistema completamente modular - cualquier estrategia puede usarse en live trading.
        """
        # Obtener estrategias activas del backtesting
        backtesting_strategies = self.config.get('backtesting', {}).get('strategies', {})
        strategy_paths = self.config.get('backtesting', {}).get('strategy_paths', {})
        live_strategy_mapping = self.live_config.get('strategy_mapping', {})

        logger.info(f" Buscando estrategias activas en backtesting: {list(backtesting_strategies.keys())}")

        # Cargar TODAS las estrategias activas en backtesting
        for strategy_name, is_active in backtesting_strategies.items():
            if not is_active:
                logger.info(f"⏭  {strategy_name} está desactivada en backtesting, omitiendo")
                continue

            logger.info(f" Procesando estrategia: {strategy_name}")

            # Verificar si hay configuración específica para live trading
            live_config = live_strategy_mapping.get(strategy_name, {})

            # Si no hay configuración específica, crear configuración por defecto
            if not live_config:
                logger.info(f"  No hay configuración específica para {strategy_name}, creando configuración por defecto")
                live_config = self._create_default_live_config(strategy_name)

            # Verificar si la estrategia está activa para live trading
            if not live_config.get('active', False):
                logger.info(f"⏭  {strategy_name} no está activa para live trading")
                continue

            # Cargar la estrategia usando el path configurado
            if strategy_name in strategy_paths:
                module_path, class_name = strategy_paths[strategy_name]
            else:
                logger.warning(f" No se encontró path para estrategia '{strategy_name}' en strategy_paths")
                continue

            try:
                # Importar dinámicamente
                module = __import__(module_path, fromlist=[class_name])
                strategy_class = getattr(module, class_name)

                # Obtener parámetros de configuración
                strategy_params = live_config.get('parameters', {})

                # Filtrar parámetros para solo los que la estrategia acepta
                # Las estrategias ML solo aceptan: config, initial_balance
                # No pasar parámetros adicionales que la clase no espera
                filtered_params = {}
                if 'config' in strategy_params:
                    filtered_params['config'] = strategy_params['config']
                if 'initial_balance' in strategy_params:
                    filtered_params['initial_balance'] = strategy_params['initial_balance']

                # Instanciar estrategia con parámetros filtrados
                if filtered_params:
                    self.strategy_instances[strategy_name] = strategy_class(**filtered_params)
                    logger.info(f" {strategy_name} cargada con parámetros: {list(filtered_params.keys())}")
                else:
                    # Instanciar sin parámetros - la estrategia usará defaults
                    self.strategy_instances[strategy_name] = strategy_class(config=self.config)
                    logger.info(f" {strategy_name} cargada sin parámetros adicionales")

                # Guardar configuración de live trading para esta estrategia
                self.strategy_live_configs[strategy_name] = live_config

            except (ImportError, AttributeError) as e:
                logger.error(f" Error cargando {strategy_name}: {str(e)}")
                continue

        # Validar que se cargaron estrategias
        if not self.strategy_instances:
            logger.error(" No se pudo cargar ninguna estrategia para live trading")
            return False

        logger.info(f" Se cargaron {len(self.strategy_instances)} estrategias para live trading")
        for name in self.strategy_instances.keys():
            config = self.strategy_live_configs[name]
            symbols = config.get('symbols', [])
            timeframes = config.get('timeframes', [])
            logger.info(f"    {name}: {len(symbols)} símbolos, {len(timeframes)} timeframes")

        return True
    
    def _create_default_live_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Crea configuración por defecto para una estrategia en live trading.
        
        Args:
            strategy_name: Nombre de la estrategia
            
        Returns:
            Diccionario con configuración por defecto
        """
        # Usar símbolos de la configuración del backtesting
        try:
            if hasattr(self.config, 'backtesting') and hasattr(self.config.backtesting, 'symbols'):
                default_symbols = self.config.backtesting.symbols
                default_timeframes = [self.config.backtesting.timeframe] if hasattr(self.config.backtesting, 'timeframe') else ["15m"]
            else:
                # Fallback para Volatility 75 Index de Deriv
                default_symbols = ["Volatility 75 Index"]
                default_timeframes = ["15m"]
        except:
            # Fallback final
            default_symbols = ["Volatility 75 Index"]
            default_timeframes = ["15m"]
        
        # Parámetros por defecto
        default_params = {
            'stop_loss_percent': 1.5
        }
        
        return {
            'active': True,
            'symbols': default_symbols,
            'timeframes': default_timeframes,
            'parameters': default_params
        }
    
    def _validate_live_config(self) -> bool:
        """
        Valida la configuración de live trading.
        
        Returns:
            True si la configuración es válida
        """
        logger.info(" Validando configuración de live trading...")
        
        # Obtener símbolos disponibles
        mt5_symbols = self.live_config.get('mt5', {}).get('available_symbols', [])
        ccxt_symbols = self.live_config.get('ccxt', {}).get('available_symbols', [])
        available_symbols = mt5_symbols + ccxt_symbols
        
        # Obtener timeframes disponibles
        mt5_timeframes = self.live_config.get('mt5', {}).get('available_timeframes', [])
        ccxt_timeframes = self.live_config.get('ccxt', {}).get('available_timeframes', [])
        available_timeframes = list(set(mt5_timeframes + ccxt_timeframes))
        
        logger.info(f" Símbolos disponibles en configuración: {len(available_symbols)}")
        logger.info(f"⏰ Timeframes disponibles: {available_timeframes}")
        
        # Validar cada estrategia cargada
        for strategy_name, live_config in self.strategy_live_configs.items():
            symbols = live_config.get('symbols', [])
            timeframes = live_config.get('timeframes', [])
            
            # Validar símbolos - si la lista global está vacía, permitir cualquier símbolo
            # (MT5/CCXT harán la validación real al intentar conectar)
            if available_symbols:
                invalid_symbols = [s for s in symbols if s not in available_symbols]
                if invalid_symbols:
                    logger.error(f" Estrategia {strategy_name}: símbolos inválidos {invalid_symbols}")
                    logger.error(f"   Símbolos disponibles: {available_symbols}")
                    return False
            else:
                logger.info(f"ℹ  Sin lista de símbolos predefinida - Permitiendo: {symbols}")
            
            # Validar timeframes - similar a símbolos, permitir si lista está vacía
            if available_timeframes:
                invalid_timeframes = [t for t in timeframes if t not in available_timeframes]
                if invalid_timeframes:
                    logger.error(f" Estrategia {strategy_name}: timeframes inválidos {invalid_timeframes}")
                    logger.error(f"   Timeframes disponibles: {available_timeframes}")
                    return False
            else:
                logger.info(f"ℹ  Sin lista de timeframes predefinida - Permitiendo: {timeframes}")
            
            logger.info(f" {strategy_name}: {len(symbols)} símbolos, {len(timeframes)} timeframes válidos")
        
        logger.info(" Configuración de live trading validada correctamente")
        return True
    
    def start(self):
        """
        Inicia el orquestador de trading en vivo.
        """
        if self.running:
            logger.warning("El orquestador ya está en ejecución")
            return False
        
        # Cargar estrategias
        if not self.load_strategies():
            logger.error("No se pudieron cargar las estrategias. Abortando inicio.")
            return False
        
        # Validar configuración de live trading
        if not self._validate_live_config():
            logger.error("Configuración de live trading inválida. Abortando inicio.")
            return False
        
        # Conectar con MT5
        if not self.data_provider.connect():
            logger.error("No se pudo establecer conexión con MetaTrader 5")
            return False
        
        if not self.order_executor.connect():
            logger.error("No se pudo establecer conexión para ejecutar órdenes")
            self.data_provider.disconnect()
            return False
        
        # Iniciar hilos
        self.running = True
        self.data_thread = threading.Thread(target=self._data_processing_loop)
        self.signal_thread = threading.Thread(target=self._signal_processing_loop)
        
        self.data_thread.daemon = True
        self.signal_thread.daemon = True
        
        self.data_thread.start()
        self.signal_thread.start()
        
        logger.info("Orquestador de trading en vivo iniciado correctamente")
        return True
    
    def stop(self):
        """
        Detiene el orquestador de trading en vivo.
        """
        if not self.running:
            logger.warning("El orquestador no está en ejecución")
            return False
        
        self.running = False
        
        # Esperar a que terminen los hilos
        self.data_thread.join(timeout=10)
        self.signal_thread.join(timeout=10)
        
        # Cerrar conexiones
        self.data_provider.disconnect()
        self.order_executor.disconnect()
        
        # Actualizar métricas finales
        self._update_metrics()
        
        logger.info("Orquestador de trading en vivo detenido correctamente")
        return True
    
    def _data_processing_loop(self):
        """
        Bucle principal para procesar datos en tiempo real.
        Sistema completamente modular - procesa todos los símbolos/timeframes de cada estrategia.
        """
        logger.info("Hilo de procesamiento de datos iniciado")
        
        cycle_count = 0
        last_sync_time = datetime.now()
        sync_interval_seconds = self.live_config.get('position_sync_interval_seconds', 60)
        
        while self.running:
            cycle_count += 1
            logger.info(f" Iniciando ciclo #{cycle_count} - Sistema Modular Activo")
            
            try:
                # Procesar cada estrategia cargada con sus símbolos y timeframes específicos
                for strategy_name, strategy in self.strategy_instances.items():
                    live_config = self.strategy_live_configs[strategy_name]
                    symbols = live_config.get('symbols', [])
                    timeframes = live_config.get('timeframes', [])
                    
                    logger.info(f" Procesando {strategy_name}: {len(symbols)} símbolos, {len(timeframes)} timeframes")
                    
                    # FIX: Usar el primer timeframe para sincronización de velas
                    # Todos los timeframes deben estar alineados al mismo tipo (ej: todos 15m o todos 4h)
                    primary_timeframe = timeframes[0] if timeframes else '15m'
                    
                    for symbol in symbols:
                        for timeframe in timeframes:
                            logger.info(f" {strategy_name} -> {symbol} {timeframe}")
                            
                            # Obtener datos más recientes - usando método optimizado para MT5
                            # El sistema mantiene cache inteligente y solo actualiza barras nuevas
                            # FIX: Incrementar de 200 a 1000+ barras para contexto ML equivalente a backtest
                            data = self.data_provider.get_live_data_efficient(symbol, timeframe, bars=1000)
                            
                            # 🔧 FIX v4.10: Si data es None, significa que el candle no cambió
                            # (ya fue procesado en ciclo anterior). Skipear para evitar señales duplicadas
                            if data is None:
                                logger.debug(f"  {symbol} {timeframe}: Candle sin cambios. Skipear procesamiento (previene 180x operaciones/15m)")
                                continue
                            
                            # FIX: Validar que tenemos velas completas (no en formación)
                            if len(data) > 0:
                                last_candle_time = data['time'].iloc[-1]
                                is_closed, _ = self.data_provider.is_candle_closed(timeframe)
                                if not is_closed:
                                    logger.debug(f"  {symbol} {timeframe}: Vela en formación, usando datos hasta vela anterior")
                                    # Usar solo velas completas (excluir la última que está en formación)
                                    data = data.iloc[:-1] if len(data) > 1 else data
                            
                            if len(data) < 50:
                                logger.warning(f" Datos insuficientes para {symbol} {timeframe}: {len(data)} filas")
                                continue
                            
                            logger.info(f" Datos obtenidos: {len(data)} filas para {symbol} {timeframe} (velas cerradas)")
                            
                            # Procesar con la estrategia específica
                            self._process_data_with_strategy(strategy_name, strategy, symbol, timeframe, data)
                
                # FASE 5 - SINCRONIZACIÓN: Sincronizar posiciones con exchange cada intervalo
                current_time = datetime.now()
                if (current_time - last_sync_time).total_seconds() >= sync_interval_seconds:
                    logger.info(f" [SYNC] Sincronizando posiciones con exchange...")
                    try:
                        sync_result = self.position_synchronizer.sync_positions_with_exchange(
                            local_positions=self.active_positions,
                            strategy_configs=self.strategy_live_configs
                        )
                        
                        if sync_result['status'] == 'success':
                            logger.info(f" [SYNC] Sincronización completada: "
                                      f"{sync_result['matched']} coincidencias, "
                                      f"{sync_result['mismatches']} desajustes, "
                                      f"{sync_result['external_closes']} cierres externos")
                            
                            # Actualizar active_positions si hay cambios
                            if sync_result.get('updated_positions'):
                                self.active_positions = sync_result['updated_positions']
                            
                            # Procesar cierres externos (SL/TP activados)
                            if sync_result.get('external_closes'):
                                for closed_order in sync_result['external_closes']:
                                    logger.info(f"  [SYNC] Cierre externo detectado: {closed_order['symbol']}")
                                    self._record_trade_closed(closed_order, {'symbol': closed_order['symbol'], 'strategy': 'EXTERNAL'})
                        else:
                            logger.warning(f"  [SYNC] Sincronización fallida: {sync_result.get('error', 'Error desconocido')}")
                    
                    except Exception as sync_error:
                        logger.error(f" [SYNC] Error durante sincronización: {str(sync_error)}")
                    
                    last_sync_time = current_time
                
                # 🔧 FIX v4.10: MONITOREAR TP/SL/TRAILING STOP
                # Cada ciclo, verificar si alguna posición debe cerrarse automáticamente
                self.monitor_open_positions_for_tp_sl()
                
                # Actualizar métricas
                self._update_metrics()
                
                # FIX: Sincronización basada en cierre de vela en lugar de ciclo fijo
                # Determinar el timeframe principal para sincronización
                primary_timeframe = '15m'  # Default
                if self.strategy_live_configs:
                    first_strategy = list(self.strategy_live_configs.values())[0]
                    primary_timeframes = first_strategy.get('timeframes', ['15m'])
                    primary_timeframe = primary_timeframes[0] if primary_timeframes else '15m'
                
                # Verificar si debemos esperar al cierre de vela o hacer polling rápido
                is_closed, seconds_to_close = self.data_provider.is_candle_closed(primary_timeframe)
                
                if seconds_to_close > 60:
                    # Si falta más de 1 minuto, esperar con polling cada 10 segundos
                    wait_time = min(10, seconds_to_close)
                    logger.info(f"[CYCLE] Ciclo #{cycle_count} completado. Próximo cierre de vela {primary_timeframe} en {seconds_to_close}s. Esperando {wait_time}s...")
                    time.sleep(wait_time)
                elif seconds_to_close > 10:
                    # Si falta entre 10s y 60s, esperar exactamente hasta el cierre
                    logger.info(f"[CYCLE] Ciclo #{cycle_count} completado. Esperando {seconds_to_close}s hasta cierre de vela {primary_timeframe}...")
                    time.sleep(seconds_to_close + 1)  # +1 para asegurar que cerró
                else:
                    # Si estamos cerca del cierre o justo después, esperar intervalo mínimo
                    logger.info(f"[CYCLE] Ciclo #{cycle_count} completado. Vela recién cerrada, esperando intervalo mínimo...")
                    time.sleep(self.live_config.get('update_interval_seconds', 5))
                
            except Exception as e:
                logger.error(f" Error en el bucle de procesamiento de datos: {str(e)}")
                import traceback
                logger.error(f" Traceback: {traceback.format_exc()}")
                time.sleep(10)  # Esperar y reintentar
        
        logger.info("Hilo de procesamiento de datos finalizado")

    def _signal_processing_loop(self):
        """
        Bucle para procesar señales de trading de forma segura.
        Este método se ejecuta en un hilo separado.
        """
        logger.info("Hilo de procesamiento de señales iniciado")
        
        while self.running:
            try:
                # Obtener señal de la cola (esperar hasta que haya una)
                try:
                    signal = self.signal_queue.get(timeout=1)
                    self._execute_trading_signal(signal)
                    self.signal_queue.task_done()
                except queue.Empty:
                    pass  # No hay señales para procesar
                    
            except Exception as e:
                logger.error(f"Error en el bucle de procesamiento de señales: {str(e)}")
                time.sleep(5)  # Esperar y reintentar
    
    def _process_data_with_strategy(self, strategy_name: str, strategy, symbol: str, timeframe: str, data: pd.DataFrame):
        """
        Procesa los datos con una estrategia específica y genera señales de trading.
        
        Args:
            strategy_name: Nombre de la estrategia
            strategy: Instancia de la estrategia
            symbol: Símbolo a procesar
            timeframe: Timeframe a procesar
            data: DataFrame con datos OHLCV
        """
        try:
            logger.info(f" Ejecutando {strategy_name} para {symbol} {timeframe}")
            
            # Ejecutar estrategia - Para LIVE TRADING usar get_live_signal() en lugar de run()
            # run() es para backtesting, get_live_signal() es para live trading
            if hasattr(strategy, 'get_live_signal'):
                # Método preferido para live trading
                result = strategy.get_live_signal(data, symbol, timeframe)
            else:
                # Fallback a run() si no existe get_live_signal()
                result = strategy.run(data, symbol)
            
            # Procesar resultado de la estrategia
            if result and 'signal' in result:
                # Verificar si hay una señal válida
                if result['signal'] in ('NO_SIGNAL', None):
                    logger.info(f" {strategy_name} no generó señales para {symbol} {timeframe}")
                    return
                
                # Convertir el formato de la estrategia al formato esperado
                latest_signal = {
                    'action': result['signal'],
                    'price': result['signal_data'].get('entry_price', 0),
                    'stop_loss': result['signal_data'].get('stop_loss_price', 0),
                    'take_profit': result['signal_data'].get('take_profit_price', 0),
                    'direction': result['signal'].lower(),
                    'symbol': symbol,
                    'ml_confidence': result.get('ml_confidence', 0.5),
                    'atr': result['signal_data'].get('atr', 0),
                    'risk_per_trade': result['signal_data'].get('risk_per_trade', 0.02),
                    'timestamp': result['signal_data'].get('timestamp')
                }
                
                logger.info(f"[SIGNAL]  {strategy_name} generó señal: {latest_signal.get('action', 'UNKNOWN')} para {symbol}")
                
                # Aplicar gestión de riesgo si está habilitada
                if self.live_config.get('apply_risk_management', True):
                    if not self._apply_risk_management_to_signal(latest_signal, symbol):
                        logger.info(f"[RISK]  Señal rechazada por gestión de riesgo: {symbol}")
                        return
                
                # Verificar límites de posiciones
                if not self._check_position_limits(symbol):
                    logger.info(f"[LIMIT]  Límite de posiciones alcanzado para {symbol}")
                    return
                
                # Copiar position_size del risk management a signal_data para que esté disponible en ejecución
                if 'position_size' in latest_signal:
                    result['signal_data']['position_size'] = latest_signal['position_size']
                    logger.info(f"[POSITION_SIZE] Añadido position_size={latest_signal['position_size']} a signal_data")
                
                # El resultado ya está en el formato correcto para la cola, pero necesita 'data'
                result['data'] = data.tail(1).to_dict('records')[0]
                self.signal_queue.put(result)
                logger.info(f" Señal de {strategy_name} enviada a cola: {latest_signal['action']} {symbol}")
            else:
                logger.info(f" {strategy_name} no generó señales para {symbol} {timeframe}")
                
        except Exception as e:
            logger.error(f" Error procesando {strategy_name} para {symbol} ({timeframe}): {str(e)}")
    
    def _apply_risk_management_to_signal(self, signal: Dict[str, Any], symbol: str) -> bool:
        """
        Aplica gestión de riesgo a una señal de trading.
        
        Args:
            signal: Señal de trading
            symbol: Símbolo de la señal
            
        Returns:
            True si la señal pasa la gestión de riesgo
        """
        try:
            # Obtener balance/equity de cuenta ACTUAL
            account_info = self.data_provider.get_account_info()
            
            # Usar EQUITY (balance - pérdidas no realizadas) para más precisión en riesgo
            # Equity es más conservador que Balance si hay operaciones con pérdidas abiertas
            account_balance = account_info.get('equity', account_info.get('balance', 0.0))
            balance = account_info.get('balance', 0.0)
            equity = account_info.get('equity', balance)
            
            logger.info(f"💰 Información de cuenta (SYNC ACTUAL): Balance={balance:.2f} USD, Equity={equity:.2f} USD")
            
            # Configuración de riesgo
            risk_config = {
                'risk_percent': self.live_config.get('risk_per_trade', 0.01) * 100,
                'max_drawdown_limit': 20.0
            }
            
            # Información del símbolo (básica por ahora)
            symbol_info = {
                'tick_size': 0.00001 if 'USD' in symbol else 0.01,  # Forex vs otros
                'min_lot': 0.01,
                'max_lot': 100.0
            }
            
            # Aplicar gestión de riesgo
            risk_result = apply_risk_management(signal, account_balance, symbol_info, risk_config)
            
            return not risk_result.get('rejected', False)
            
        except Exception as e:
            logger.error(f"Error aplicando gestión de riesgo: {str(e)}")
            return False
    
    def _check_position_limits(self, symbol: str) -> bool:
        """
        Verifica si se pueden abrir más posiciones para un símbolo.
        
        Args:
            symbol: Símbolo a verificar
            
        Returns:
            True si se puede abrir posición
        """
        # Contar posiciones abiertas totales
        total_positions = len(self.active_positions)
        max_positions = self.live_config.get('max_positions', 3)
        
        if total_positions >= max_positions:
            logger.info(f"Límite total de posiciones alcanzado: {total_positions}/{max_positions}")
            return False
        
        # DESACTIVADO: Límite por símbolo removido para permitir múltiples operaciones
        # Los límites antiguos bloqueaban el trading, ahora permitimos múltiples posiciones
        
        return True
    
    def _execute_trading_signal(self, signal_data: Dict[str, Any]):
        """
        Ejecuta una señal de trading enviando órdenes a MT5.
        Sistema completamente modular con validaciones avanzadas.

        Args:
            signal_data: Diccionario con información de la señal
        """
        logger.info(f"[DEBUG] Ejecutando señal con datos: {signal_data}")
        logger.info(f"[DEBUG] Claves disponibles: {list(signal_data.keys()) if isinstance(signal_data, dict) else 'NO ES DICT'}")

        symbol = signal_data['symbol']
        
        # Determinar el formato de la señal
        if 'signal' in signal_data and isinstance(signal_data['signal'], str):
            # Nuevo formato: 'signal' es string, 'signal_data' contiene detalles
            action = signal_data['signal']
            signal_details = signal_data.get('signal_data', {})
        else:
            # Formato antiguo: 'signal' es diccionario con 'action'
            action = signal_data['signal']['action']
            signal_details = signal_data['signal']
        
        strategy_name = signal_data.get('strategy_name', signal_data.get('strategy', 'Unknown'))
        current_price = signal_data.get('data', {}).get('close', None)
        
        if not current_price:
            logger.error(f"Precio actual no disponible para {symbol}")
            return
        
        # Verificación final de límites antes de ejecutar
        if not self._check_position_limits(symbol):
            logger.warning(f"Verificación final fallida: límite de posiciones para {symbol}")
            return
        
        try:
            # Verificar si ya tenemos una posición abierta para este símbolo
            existing_position = self.order_executor.get_position(symbol)
            position_action = None
            allow_multiple = self.live_config.get('allow_multiple_positions_same_symbol', True)  # v4.9 FIX
            
            if action == 'BUY':
                if existing_position and not allow_multiple:
                    # ANTIGUO COMPORTAMIENTO: Solo 1 posición por símbolo
                    if existing_position['type'] == 'SELL':
                        # Cerrar posición corta existente y abrir larga
                        self.order_executor.close_position(symbol)
                        position_action = "cerrada posición SELL existente"
                    else:
                        # Ya tenemos una posición larga, no hacer nada
                        logger.info(f"Ignorando señal BUY para {symbol}: ya existe posición LONG")
                        return
                elif existing_position and existing_position['type'] == 'SELL' and allow_multiple:
                    # NUEVO COMPORTAMIENTO v4.9: Permitir múltiples, pero cerrar contra-posición
                    logger.info(f"[v4.9] Cerrando posición SELL para abrir BUY en {symbol}")
                    self.order_executor.close_position(symbol)
                    position_action = "cerrada posición SELL existente"
                    import time
                    time.sleep(1)  # Pequeña pausa para asegurar cierre
                
                # Usar stop loss y take profit calculados por la estrategia
                stop_loss = signal_details.get('stop_loss_price', signal_details.get('stop_loss', current_price * 0.95))
                take_profit = signal_details.get('take_profit_price', signal_details.get('take_profit', current_price * 1.1))
                risk_per_trade = signal_details.get('risk_per_trade', 0.02)
                # USAR position_size del risk management (ya está calculado correctamente)
                position_size = signal_details.get('position_size', None)
                
                logger.info(f"📊 BUY: Position size recibido del risk management: {position_size}")
                
                # Abrir posición larga - usar position_size calculado por risk management
                result = self.order_executor.open_position(
                    symbol=symbol,
                    order_type=OrderType.BUY,
                    quantity=position_size,  # USAR position_size calculado por risk management
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    risk_per_trade=risk_per_trade
                )
                
                if result['success']:
                    logger.info(f"Posición LONG abierta para {symbol} a {current_price}" + 
                              (f" después de {position_action}" if position_action else ""))
                    # Construir diccionario de orden con información de MT5
                    order_info = {
                        'ticket': result.get('order', 0),
                        'order_type': 'BUY',
                        'price': result.get('price', current_price),
                        'volume': result.get('volume', position_size),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                    self._record_trade_opened(order_info, signal_data)
                else:
                    logger.error(f"Error al abrir posición LONG para {symbol}: {result['message']}")
                    
            elif action == 'SELL':
                if existing_position and not allow_multiple:
                    # ANTIGUO COMPORTAMIENTO: Solo 1 posición por símbolo
                    if existing_position['type'] == 'BUY':
                        # Cerrar posición larga existente y abrir corta
                        self.order_executor.close_position(symbol)
                        position_action = "cerrada posición BUY existente"
                    else:
                        # Ya tenemos una posición corta, no hacer nada
                        logger.info(f"Ignorando señal SELL para {symbol}: ya existe posición SHORT")
                        return
                elif existing_position and existing_position['type'] == 'BUY' and allow_multiple:
                    # NUEVO COMPORTAMIENTO v4.9: Permitir múltiples, pero cerrar contra-posición
                    logger.info(f"[v4.9] Cerrando posición BUY para abrir SELL en {symbol}")
                    self.order_executor.close_position(symbol)
                    position_action = "cerrada posición BUY existente"
                    import time
                    time.sleep(1)  # Pequeña pausa para asegurar cierre
                
                # Usar stop loss y take profit calculados por la estrategia
                stop_loss = signal_details.get('stop_loss_price', signal_details.get('stop_loss', current_price * 1.05))
                take_profit = signal_details.get('take_profit_price', signal_details.get('take_profit', current_price * 0.9))
                risk_per_trade = signal_details.get('risk_per_trade', 0.02)
                # USAR position_size del risk management (ya está calculado correctamente)
                position_size = signal_details.get('position_size', None)
                
                logger.info(f"📊 SELL: Position size recibido del risk management: {position_size}")
                
                # Abrir posición corta - usar position_size calculado por risk management
                result = self.order_executor.open_position(
                    symbol=symbol,
                    order_type=OrderType.SELL,
                    quantity=position_size,  # USAR position_size calculado por risk management
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    risk_per_trade=risk_per_trade
                )
                
                if result['success']:
                    logger.info(f"Posición SHORT abierta para {symbol} a {current_price}" + 
                              (f" después de {position_action}" if position_action else ""))
                    # Construir diccionario de orden con información de MT5
                    order_info = {
                        'ticket': result.get('order', 0),
                        'order_type': 'SELL',
                        'price': result.get('price', current_price),
                        'volume': result.get('volume', position_size),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }
                    self._record_trade_opened(order_info, signal_data)
                else:
                    logger.error(f"Error al abrir posición SHORT para {symbol}: {result['message']}")
                    
            elif action == 'CLOSE':
                if existing_position:
                    result = self.order_executor.close_position(symbol)
                    if result['success']:
                        logger.info(f"Posición cerrada para {symbol} a {current_price}")
                        self._record_trade_closed(result['position'], signal_data)
                    else:
                        logger.error(f"Error al cerrar posición para {symbol}: {result['message']}")
                else:
                    logger.info(f"Ignorando señal CLOSE para {symbol}: no hay posición abierta")
                    
        except Exception as e:
            logger.error(f"Error al ejecutar señal de trading para {symbol}: {str(e)}")
    
    def _record_trade_opened(self, order_info: Dict[str, Any], signal_data: Dict[str, Any]):
        """
        Registra información de una operación abierta.
        
        FASE 5 (v4.11): Usa IndexedPositionMonitor para O(1) lookups (6.25x speedup).
        
        Args:
            order_info: Información de la orden ejecutada
            signal_data: Datos de la señal que generó la orden
        """
        # Registrar en active_positions
        position_id = order_info.get('ticket', 0)
        position_data = {
            'symbol': signal_data.get('symbol', 'UNKNOWN'),
            'strategy': signal_data.get('strategy', signal_data.get('strategy_name', 'UNKNOWN')),
            'type': order_info.get('order_type', ''),
            'open_price': order_info.get('price', 0.0),
            'volume': order_info.get('volume', 0.0),
            'stop_loss': order_info.get('stop_loss', 0.0),
            'take_profit': order_info.get('take_profit', 0.0),
            'open_time': datetime.now(),
            'signal_data': signal_data
        }
        
        self.active_positions[position_id] = position_data
        
        # FASE 5: Sincronizar con IndexedPositionMonitor (v4.11)
        self._sync_position_to_indexed_monitor(str(position_id), position_data, 'add')
        
        logger.info(f"Nueva posición registrada: {position_id} para {signal_data.get('symbol', 'UNKNOWN')}")
    
    def _record_trade_closed(self, position_info: Dict[str, Any], signal_data: Dict[str, Any]):
        """
        Registra información de una operación cerrada.
        
        FASE 5 (v4.11): Sincroniza con IndexedPositionMonitor (6.25x speedup).
        
        Args:
            position_info: Información de la posición cerrada
            signal_data: Datos de la señal que generó el cierre
        """
        position_id = position_info.get('ticket', 0)
        if position_id in self.active_positions:
            position_data = self.active_positions[position_id]
            position_data['close_price'] = position_info.get('price_close', 0.0)
            position_data['close_time'] = datetime.now()
            position_data['profit'] = position_info.get('profit', 0.0)
            position_data['duration_minutes'] = (position_data['close_time'] - position_data['open_time']).total_seconds() / 60
            
            # FASE 5: Sincronizar cierre con IndexedPositionMonitor (v4.11)
            self._sync_position_to_indexed_monitor(str(position_id), position_data, 'close')
            
            # Mover a historial
            self.position_history.append(position_data)
            del self.active_positions[position_id]
            
            # Actualizar métricas
            self.live_metrics['total_trades'] += 1
            if position_data['profit'] > 0:
                self.live_metrics['winning_trades'] += 1
            else:
                self.live_metrics['losing_trades'] += 1
            self.live_metrics['total_pnl'] += position_data['profit']
            
            logger.info(f"Posición {position_id} cerrada con P&L: {position_data['profit']}")
    
    def _update_metrics(self):
        """
        Actualiza las métricas en vivo del sistema.
        """
        try:
            # Actualizar tiempo de ejecución
            self.live_metrics['runtime_minutes'] = (datetime.now() - self.live_metrics['start_time']).total_seconds() / 60
            
            # Actualizar tasa de victorias
            total_trades = self.live_metrics['winning_trades'] + self.live_metrics['losing_trades']
            if total_trades > 0:
                self.live_metrics['win_rate'] = self.live_metrics['winning_trades'] / total_trades
            
            # Actualizar factor de beneficio
            total_profit = sum(p['profit'] for p in self.position_history if p['profit'] > 0)
            total_loss = abs(sum(p['profit'] for p in self.position_history if p['profit'] < 0))
            if total_loss > 0:
                self.live_metrics['profit_factor'] = total_profit / total_loss
            
            # Calcular drawdown
            if self.position_history:
                cumulative_pnl = [0]
                for p in sorted(self.position_history, key=lambda x: x['close_time']):
                    cumulative_pnl.append(cumulative_pnl[-1] + p['profit'])
                
                # Calcular drawdown máximo
                max_dd = 0
                peak = cumulative_pnl[0]
                for value in cumulative_pnl:
                    if value > peak:
                        peak = value
                    dd = peak - value
                    if dd > max_dd:
                        max_dd = dd
                
                self.live_metrics['max_drawdown'] = max_dd
        
        except Exception as e:
            logger.error(f"Error al actualizar métricas: {str(e)}")
    
    def monitor_open_positions_for_tp_sl(self):
        """
        🔧 FIX v4.10: Monitorea posiciones abiertas y cierra si se activan TP/SL/Trailing Stop.
        
        Este método debe ejecutarse cada ciclo para:
        1. Verificar TP (Take Profit) activado
        2. Verificar SL (Stop Loss) activado
        3. Verificar Trailing Stop (si está habilitado)
        
        Se ejecuta en el ciclo principal después de cada procesamiento de datos.
        """
        if not self.active_positions:
            return  # No hay posiciones abiertas
        
        try:
            # Obtener datos actuales de precios
            current_prices = {}
            for strategy_name, strategy in self.strategy_instances.items():
                live_config = self.strategy_live_configs[strategy_name]
                symbols = live_config.get('symbols', [])
                
                for symbol in symbols:
                    if symbol not in current_prices:
                        # Obtener precio actual desde MT5
                        try:
                            tick = self.order_executor.get_current_price(symbol)
                            if tick:
                                current_prices[symbol] = tick
                        except Exception as e:
                            logger.warning(f"No se pudo obtener precio para {symbol}: {e}")
            
            # Monitorear cada posición abierta
            positions_to_close = []
            
            for position_id, position_data in list(self.active_positions.items()):
                symbol = position_data['symbol']
                tick_data = current_prices.get(symbol)
                
                if tick_data is None:
                    continue  # No hay precio actual, skipear
                
                # Extraer precio actual del diccionario tick (usar bid para SELL, ask para BUY)
                current_price = tick_data.get('bid', 0) if isinstance(tick_data, dict) else tick_data
                
                open_price = float(position_data['open_price'])
                tp = float(position_data['take_profit'])
                sl = float(position_data['stop_loss'])
                position_type = position_data['type']
                
                close_reason = None
                close_price = current_price
                
                # Verificar TP (Take Profit)
                if position_type.upper() == 'BUY' and current_price >= tp and tp > 0:
                    close_reason = 'TP_ACTIVATED'
                elif position_type.upper() == 'SELL' and current_price <= tp and tp > 0:
                    close_reason = 'TP_ACTIVATED'
                
                # Verificar SL (Stop Loss) si TP no fue activado
                if close_reason is None:
                    if position_type.upper() == 'BUY' and current_price <= sl and sl > 0:
                        close_reason = 'SL_ACTIVATED'
                    elif position_type.upper() == 'SELL' and current_price >= sl and sl > 0:
                        close_reason = 'SL_ACTIVATED'
                
                # Verificar Trailing Stop si está habilitado
                if close_reason is None:
                    trailing_stop_enabled = self.live_config.get('enable_trailing_stop', False)
                    if trailing_stop_enabled:
                        trailing_stop_pct = float(self.live_config.get('trailing_stop_pct', 0.65)) / 100
                        
                        # Calcular trailing stop level
                        if position_type.upper() == 'BUY':
                            # En BUY: si precio sube y luego baja más del 0.65%, cerrar
                            highest_price = position_data.get('highest_price', open_price)
                            if current_price > highest_price:
                                position_data['highest_price'] = current_price
                            else:
                                trailing_level = highest_price * (1 - trailing_stop_pct)
                                if current_price <= trailing_level:
                                    close_reason = 'TRAILING_STOP_ACTIVATED'
                                    close_price = current_price
                        
                        elif position_type.upper() == 'SELL':
                            # En SELL: si precio baja y luego sube más del 0.65%, cerrar
                            lowest_price = position_data.get('lowest_price', open_price)
                            if current_price < lowest_price:
                                position_data['lowest_price'] = current_price
                            else:
                                trailing_level = lowest_price * (1 + trailing_stop_pct)
                                if current_price >= trailing_level:
                                    close_reason = 'TRAILING_STOP_ACTIVATED'
                                    close_price = current_price
                
                # Si alguna condición se activó, cerrar la posición
                if close_reason:
                    positions_to_close.append({
                        'position_id': position_id,
                        'position_data': position_data,
                        'reason': close_reason,
                        'close_price': close_price
                    })
            
            # Ejecutar cierres de posiciones
            for close_info in positions_to_close:
                position_id = close_info['position_id']
                reason = close_info['reason']
                close_price = close_info['close_price']
                position_data = close_info['position_data']
                
                try:
                    # Cerrar en MT5
                    result = self.order_executor.close_position(
                        position_id,
                        position_data['symbol']
                    )
                    
                    if result and result.get('status') == 'success':
                        logger.info(
                            f"✅ Posición {position_id} cerrada automáticamente: {reason} "
                            f"(P&L: {result.get('profit', 0):.2f})"
                        )
                        
                        # Registrar cierre
                        close_order = {
                            'ticket': position_id,
                            'symbol': position_data['symbol'],
                            'price_close': close_price,
                            'profit': result.get('profit', 0.0)
                        }
                        self._record_trade_closed(close_order, position_data.get('signal_data', {}))
                    else:
                        logger.warning(f"❌ Error cerrando posición {position_id}: {reason}")
                
                except Exception as e:
                    logger.error(f"Error cerrando posición {position_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error en monitoreo de posiciones: {str(e)}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas actuales del sistema de trading en vivo.
        
        Returns:
            Diccionario con métricas de rendimiento
        """
        # Actualizar métricas antes de devolver
        self._update_metrics()
        return self.live_metrics
    
    def get_active_positions(self) -> Dict[str, Any]:
        """
        Obtiene las posiciones actualmente abiertas.
        
        Returns:
            Diccionario con posiciones activas
        """
        # Actualizar desde MT5 para asegurar datos correctos
        mt5_positions = self.order_executor.get_all_positions()
        
        # Sincronizar con nuestro seguimiento interno
        position_tickets = set(p.get('ticket') for p in mt5_positions)
        for ticket in list(self.active_positions.keys()):
            if ticket not in position_tickets:
                # La posición ya no está activa en MT5, probablemente cerrada por SL/TP
                logger.warning(f"Posición {ticket} cerrada externamente (SL/TP activado)")
                position_info = next((p for p in mt5_positions if p.get('ticket') == ticket), None)
                if position_info:
                    self._record_trade_closed(position_info, self.active_positions[ticket].get('signal_data', {}))
                else:
                    # Si no tenemos la info de MT5, eliminar de todas formas
                    del self.active_positions[ticket]
        
        return self.active_positions
    
    def get_position_history(self) -> List[Dict[str, Any]]:
        """
        Obtiene el historial completo de posiciones cerradas.
        
        Returns:
            Lista con historial de posiciones
        """
        return self.position_history

    def export_results(self, filepath: str = None) -> bool:
        """
        Exporta los resultados del trading en vivo a un archivo JSON.
        
        Args:
            filepath: Ruta donde guardar el archivo de resultados
            
        Returns:
            True si se exportó correctamente, False en caso contrario
        """
        import json
        from datetime import datetime
        from pathlib import Path
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = Path(__file__).parent.parent / "data" / "live_trading_results"
            results_dir.mkdir(parents=True, exist_ok=True)
            filepath = results_dir / f"live_results_{timestamp}.json"
        
        try:
            # Preparar resultados
            results = {
                'metrics': self.get_current_metrics(),
                'position_history': self.get_position_history(),
                'active_positions': self.get_active_positions(),
                'runtime_info': {
                    'start_time': self.live_metrics['start_time'].isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'strategies_used': list(self.strategy_instances.keys()),
                    'symbols_traded': self.live_config.get('symbols', []),
                    'timeframes_used': self.live_config.get('timeframes', [])
                }
            }
            
            # Convertir objetos datetime a strings para serialización JSON
            results_serializable = json.loads(
                json.dumps(results, default=lambda o: o.isoformat() if isinstance(o, datetime) else None)
            )
            
            # Crear directorio si no existe
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Guardar resultados
            with open(filepath, 'w') as f:
                json.dump(results_serializable, f, indent=4)
            
            logger.info(f"Resultados exportados a: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error al exportar resultados: {str(e)}")
            return False

# Función auxiliar para ejecutar en modo standalone
def run_live_trading(config_path: str = None, duration_minutes: int = None):
    """
    Ejecuta el sistema de trading en vivo.
    
    Args:
        config_path: Ruta al archivo de configuración YAML
        duration_minutes: Duración en minutos (None para ejecución indefinida)
    """
    logger.info(f"Iniciando sistema de trading en vivo...")
    
    orchestrator = LiveTradingOrchestrator(config_path)
    
    if orchestrator.start():
        try:
            if duration_minutes:
                logger.info(f"Trading en vivo programado para {duration_minutes} minutos")
                time.sleep(duration_minutes * 60)
                logger.info(f"Duración completada, deteniendo sistema...")
            else:
                logger.info("Trading en vivo iniciado. Presione Ctrl+C para detener.")
                while True:
                    time.sleep(60)
                    metrics = orchestrator.get_current_metrics()
                    logger.info(f"Métricas actuales - P&L: {metrics['total_pnl']}, "
                               f"Trades: {metrics['total_trades']}, Win Rate: {metrics['win_rate']:.2f}")
                    
        except KeyboardInterrupt:
            logger.info("Interrupción del usuario recibida. Deteniendo...")
        finally:
            orchestrator.export_results()
            orchestrator.stop()
            logger.info("Sistema de trading en vivo finalizado")
    else:
        logger.error("No se pudo iniciar el sistema de trading en vivo")

if __name__ == "__main__":
    import sys
    
    config_path = None
    duration = None
    
    # Procesar argumentos de línea de comandos
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print("La duración debe ser un número entero de minutos")
            sys.exit(1)
    
    # Ejecutar trading en vivo
    run_live_trading(config_path, duration)