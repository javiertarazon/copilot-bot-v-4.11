#!/usr/bin/env python3
"""
Módulo de Backtesting - Sistema Modular de Trading
Contiene toda la lógica de backtesting, carga dinámica de estrategias y ejecución
"""
import asyncio
import os
import sys
# Evitar side-effects durante import: no ejecutar prints al importar el módulo.
# Añadir rutas al path solo si no están ya presentes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
current_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from config.config_loader import load_config_from_yaml
from core.downloader import AdvancedDataDownloader
# NOTA: Evitamos imports ansiosos de estrategias para reducir tiempo/bloqueos en validación inicial.
# Las estrategias se importan dinámicamente en load_strategies_from_config() usando __import__.
from backtesting.backtester import AdvancedBacktester
from utils.logger import setup_logging, get_logger
import pandas as pd

# Variable global para las estrategias disponibles
# 🎯 SISTEMA COMPLETO - Estrategia principal con ML real + estrategia de pruebas
STRATEGY_CLASSES = {
    'UltraDetailedHeikinAshiML': ('strategies.ultra_detailed_heikin_ashi_ml_strategy', 'UltraDetailedHeikinAshiMLStrategy'),
    'HeikinNeuronalMLPruebas': ('strategies.heikin_neuronal_ml_pruebas', 'HeikinNeuronalMLPruebasStrategy'),
    'SimpleTechnical': ('strategies.simple_technical_strategy', 'SimpleTechnicalStrategy'),
}

def load_strategies_from_config(config):
    """
    Carga dinámicamente TODAS las estrategias activas desde la configuración central.
    Sistema completamente modular - cualquier estrategia puede activarse/desactivarse desde config.yaml
    """
    strategies = {}

    # Obtener configuración de estrategias desde backtesting
    # Manejar tanto objetos Config (dataclasses) como diccionarios
    if hasattr(config, 'backtesting'):
        # Es un objeto Config (dataclass)
        backtesting_config = config.backtesting
        strategy_config = backtesting_config.strategies
    else:
        # Es un diccionario (compatibilidad hacia atrás)
        backtesting_config = config.get('backtesting', {})
        strategy_config = backtesting_config.get('strategies', {})

    # 🎯 SISTEMA COMPLETO - Mapeo de estrategia principal con ML real
    strategy_classes = {
        'UltraDetailedHeikinAshiML': ('strategies.ultra_detailed_heikin_ashi_ml_strategy', 'UltraDetailedHeikinAshiMLStrategy'),
        'HeikinNeuronalMLPruebas': ('strategies.heikin_neuronal_ml_pruebas', 'HeikinNeuronalMLPruebasStrategy'),
        'SimpleTechnical': ('strategies.simple_technical_strategy', 'SimpleTechnicalStrategy'),
    }
    
    # Exportamos como variable global para las pruebas
    global STRATEGY_CLASSES
    STRATEGY_CLASSES = strategy_classes

    # Estrategias que requieren estado continuo (procesamiento completo)
    stateful_strategies = {
        # Todas las estrategias actuales procesan en lotes eficientemente
    }

    print(f"[BACKTEST] 📋 Cargando estrategias activas desde configuración central...")
    print(f"[BACKTEST] 📋 Configuración de estrategias: {strategy_config}")

    # Cargar TODAS las estrategias marcadas como activas en la configuración
    active_count = 0
    for strategy_name, is_active in strategy_config.items():
        if is_active:  # Solo cargar si está activada en config
            active_count += 1
            print(f"[BACKTEST] 🔄 Procesando estrategia activa: {strategy_name}")

            if strategy_name in strategy_classes:
                try:
                    module_name, class_name = strategy_classes[strategy_name]
                    module = __import__(module_name, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)

                    # Instanciar estrategia con configuración
                    try:
                        # Intentar instanciar con config para estrategias que lo soportan
                        strategy_instance = strategy_class(config=config, initial_balance=config.backtesting.initial_capital)
                    except TypeError:
                        # Fallback para estrategias que no aceptan config
                        strategy_instance = strategy_class()

                    # Marcar si requiere estado continuo
                    strategy_instance._requires_continuous_state = strategy_name in stateful_strategies

                    strategies[strategy_name] = strategy_instance
                    print(f"[BACKTEST] ✅ {strategy_name} cargada exitosamente desde {module_name}")

                except ImportError as e:
                    print(f"[BACKTEST] ❌ Error importando {strategy_name}: Módulo {module_name} no encontrado - {e}")
                except AttributeError as e:
                    print(f"[BACKTEST] ❌ Error importando {strategy_name}: Clase {class_name} no encontrada en {module_name} - {e}")
                except Exception as e:
                    print(f"[BACKTEST] ❌ Error instanciando {strategy_name}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[BACKTEST] ⚠️  Estrategia '{strategy_name}' activada pero no implementada en strategy_classes")
        else:
            print(f"[BACKTEST] ⏭️  {strategy_name} está desactivada en configuración")

    print(f"[BACKTEST] 📊 Total estrategias activas en config: {active_count}")
    print(f"[BACKTEST] 📋 Estrategias cargadas exitosamente: {len(strategies)}")
    print(f"[BACKTEST] 📋 Lista final: {list(strategies.keys())}")

    if not strategies:
        print(f"[BACKTEST] ❌ ERROR: No se pudo cargar ninguna estrategia activa")
        print(f"[BACKTEST] 💡 Verifica que al menos una estrategia esté activada en config.yaml")

    return strategies

async def run_full_backtesting_with_batches():
    print("[BACKTEST] 🚀 BACKTESTING COMPLETO CON DESCARGAS POR LOTES")
    print("=" * 70)

    try:
        # Cargar configuración
        config = load_config_from_yaml()
        print(f"[BACKTEST] ✅ Config cargada: {config.backtesting.start_date} a {config.backtesting.end_date}")
        print(f"[BACKTEST] 📊 Timeframe: {config.backtesting.timeframe}")
        print(f"[BACKTEST] 🎯 Símbolos: {config.backtesting.symbols}")

        # Calcular estadísticas del período
        from datetime import datetime
        start = datetime.strptime(config.backtesting.start_date, "%Y-%m-%d")
        end = datetime.strptime(config.backtesting.end_date, "%Y-%m-%d")
        days = (end - start).days
        from utils.market_sessions import expected_candles_for_range, get_asset_class
        expected_velas = expected_candles_for_range(
            pd.Timestamp(config.backtesting.start_date),
            pd.Timestamp(config.backtesting.end_date),
            config.backtesting.timeframe,
            get_asset_class(config.backtesting.symbols[0]) if config.backtesting.symbols else "forex",
        )

        print(f"[BACKTEST] 📅 Período: {days} días (~{expected_velas:,} velas esperadas)")

        # Configurar logging
        setup_logging(config.system.log_level, config.system.log_file)
        logger = get_logger(__name__)

        # Inicializar downloader (con tolerancia a fallos si ya hay datos)
        downloader = AdvancedDataDownloader(config)
        success = await downloader.initialize()
        if not success:
            print("[BACKTEST] ⚠️  Downloader no inicializado - verificando datos existentes...")

            # Verificar si ya tenemos datos suficientes en SQLite
            from utils.storage import DataStorage
            storage = DataStorage()
            data_available = True

            for symbol in config.backtesting.symbols:
                try:
                    table_name = f"{symbol.replace('/', '_').replace('.', '_').replace(':', '_')}_{config.backtesting.timeframe}"
                    start_ts = int(pd.Timestamp(config.backtesting.start_date).timestamp()) if getattr(config.backtesting, 'start_date', None) else None
                    end_ts = int(pd.Timestamp(config.backtesting.end_date).timestamp()) if getattr(config.backtesting, 'end_date', None) else None
                    existing_data = storage.query_data(table_name, start_ts, end_ts)
                    if existing_data is None or len(existing_data) < 100:  # Mínimo flexible para fallback diario
                        data_available = False
                        print(f"[BACKTEST] ❌ Datos insuficientes para {symbol} en SQLite")
                        break
                    else:
                        print(f"[BACKTEST] ✅ Datos existentes encontrados para {symbol}: {len(existing_data)} filas")
                except Exception as e:
                    print(f"[BACKTEST] ❌ Error verificando datos existentes para {symbol}: {e}")
                    data_available = False
                    break

            if not data_available:
                print("[BACKTEST] ❌ No hay datos suficientes disponibles y downloader falló")
                return
            else:
                print("[BACKTEST] ✅ Usando datos existentes - continuando sin downloader")
                # Continuar con datos existentes
                return await run_backtest_with_existing_data(config)
        else:
            print("[BACKTEST] ✅ Downloader inicializado (con soporte para lotes)")

        # Descargar datos con lotes
        # Overrides rápidos desde CLI (variables de entorno configuradas en main.py)
        override_symbols = os.environ.get('BT_OVERRIDE_SYMBOLS', '').strip()
        override_timeframe = os.environ.get('BT_OVERRIDE_TIMEFRAME', '').strip()

        if override_symbols:
            try:
                parsed_symbols = [s.strip() for s in override_symbols.split(',') if s.strip()]
                if parsed_symbols:
                    print(f"[BACKTEST] 🛠️ Override de símbolos aplicado: {parsed_symbols}")
                    active_symbols = parsed_symbols
                else:
                    active_symbols = config.backtesting.symbols
            except Exception:
                active_symbols = config.backtesting.symbols
        else:
            active_symbols = config.backtesting.symbols

        if override_timeframe:
            print(f"[BACKTEST] 🛠️ Override de timeframe aplicado: {override_timeframe}")
            timeframe_used = override_timeframe
        else:
            timeframe_used = config.backtesting.timeframe

        print(f"[BACKTEST] 📦 Descargando {len(active_symbols)} símbolos usando lotes...")

        try:
            symbol_data = await downloader.download_multiple_symbols(
                active_symbols,
                timeframe=timeframe_used,
                start_date=config.backtesting.start_date,
                end_date=config.backtesting.end_date
            )
        except asyncio.CancelledError:
            print("[BACKTEST] ❌ Descarga cancelada")
            return
        except Exception as e:
            print(f"[BACKTEST] ❌ Error descargando datos: {e}")
            return

        if not symbol_data:
            print("[BACKTEST] ❌ No se pudieron descargar datos")
            return

        downloaded_count = len([s for s in active_symbols if s in symbol_data and symbol_data[s] is not None])
        print(f"[BACKTEST] ✅ Datos descargados: {downloaded_count}/{len(active_symbols)} símbolos")

        # Mostrar estadísticas detalladas de datos
        print(f"\n[BACKTEST] 📊 ESTADÍSTICAS DE DATOS:")
        print("-" * 50)

        total_velas = 0
        for symbol in active_symbols:
            if symbol in symbol_data and symbol_data[symbol] is not None:
                df = symbol_data[symbol]
                velas = len(df)
                total_velas += velas

                # Calcular cobertura
                coverage = (velas / expected_velas) * 100 if expected_velas > 0 else 0

                # Rango de fechas
                min_date = df['timestamp'].min().strftime("%Y-%m-%d") if not df.empty else "N/A"
                max_date = df['timestamp'].max().strftime("%Y-%m-%d") if not df.empty else "N/A"

                print(f"📊 {symbol}: {velas:,} velas ({coverage:.1f}%) | {min_date} → {max_date}")

        print(f"📈 TOTAL: {total_velas:,} velas de {len(active_symbols)} símbolos")

        # Procesar datos
        print(f"\n[BACKTEST] 💾 Procesando y guardando datos...")
        processed_symbol_data = await downloader.process_and_save_data(
            symbol_data,
            timeframe_used,
            save_csv=True
        )

        if not processed_symbol_data:
            print("[BACKTEST] ❌ Error procesando datos")
            return

        print(f"[BACKTEST] ✅ Datos procesados para {len(processed_symbol_data)} símbolos")

        # Ejecutar backtesting SECUENCIAL OPTIMIZADO para todos los símbolos y estrategias
        print(f"\n[BACKTEST] 🔄 Iniciando backtesting SECUENCIAL OPTIMIZADO para {len(processed_symbol_data)} símbolos")
        print(f"[BACKTEST] 📋 Símbolos a procesar: {list(processed_symbol_data.keys())}")

        # Cargar estrategias activas UNA SOLA VEZ (optimización)
        active_strategies = load_strategies_from_config(config)
        if not active_strategies:
            print("[BACKTEST] ❌ ERROR: No hay estrategias activas configuradas")
            return

        print(f"[BACKTEST] 🎯 Estrategias activas cargadas: {list(active_strategies.keys())}")

        # Procesamiento secuencial optimizado
        backtest_results = {}
        total_trades_global = 0

        print(f"[DEBUG] Antes del bucle: processed_symbol_data tiene {len(processed_symbol_data)} items")
        print(f"[DEBUG] Contenido: {list(processed_symbol_data.keys())}")

        for symbol_idx, (symbol, df) in enumerate(processed_symbol_data.items(), 1):
            print(f"\n[BACKTEST] 📈 [{symbol_idx}/{len(processed_symbol_data)}] PROCESANDO: {symbol}")
            print("-" * 70)

            try:
                # Ejecutar TODAS las estrategias para este símbolo
                symbol_results = {}
                symbol_total_trades = 0

                for strategy_name, strategy in active_strategies.items():
                    print(f"[BACKTEST] ⚡ Ejecutando {strategy_name}...")

                    try:
                        # Crear backtester independiente para cada estrategia
                        strategy_backtester = AdvancedBacktester()
                        
                        # Configurar parámetros desde config (si el backtester los soporta)
                        if hasattr(strategy_backtester, 'configure'):
                            strategy_backtester.configure({
                                'initial_capital': config.backtesting.initial_capital,
                                'commission': config.backtesting.commission,
                                'slippage': config.backtesting.slippage
                            })

                        # Verificar si requiere estado continuo
                        requires_state = hasattr(strategy, '_requires_continuous_state') and strategy._requires_continuous_state

                        if requires_state:
                            # Cargar datos completos desde CSV para estrategias stateful
                            from pathlib import Path
                            csv_path = Path(__file__).parent.parent / "data" / "csv" / f"{symbol.replace('/', '_')}_{timeframe_used}.csv"
                            if csv_path.exists():
                                full_df = pd.read_csv(csv_path)
                                full_df['timestamp'] = pd.to_datetime(full_df['timestamp'])
                                full_df.set_index('timestamp', inplace=True)
                                result_df = full_df
                                print(f"[BACKTEST] 📊 {strategy_name}: Usando datos completos ({len(full_df)} filas)")
                            else:
                                result_df = df
                                print(f"[BACKTEST] ⚠️  {strategy_name}: Datos completos no disponibles, usando datos por lotes")
                        else:
                            result_df = df

                        # Ejecutar estrategia
                        result = strategy_backtester.run(strategy, result_df, symbol, timeframe_used)

                        if result:
                            symbol_results[strategy_name] = result
                            trades = result.get('total_trades', 0)
                            symbol_total_trades += trades
                            pnl = result.get('total_pnl', 0)
                            win_rate = result.get('win_rate', 0) * 100

                            print(f"[BACKTEST] ✅ {strategy_name}: {trades} trades | P&L: ${pnl:.2f} | Win Rate: {win_rate:.1f}%")
                        else:
                            print(f"[BACKTEST] ❌ {strategy_name}: Sin resultados")

                    except Exception as e:
                        print(f"[BACKTEST] ❌ Error en {strategy_name}: {e}")
                        continue

                # Resultados del símbolo
                if symbol_results:
                    backtest_results[symbol] = symbol_results
                    total_trades_global += symbol_total_trades
                    print(f"[BACKTEST] 📊 {symbol} COMPLETADO: {symbol_total_trades} trades totales")
                else:
                    print(f"[BACKTEST] ❌ {symbol}: Sin resultados válidos de ninguna estrategia")

            except Exception as e:
                print(f"[BACKTEST] ❌ Error general procesando {symbol}: {e}")
                continue

        # Resultados finales
        print(f"\n[BACKTEST] 🏆 RESULTADOS FINALES - BACKTESTING SECUENCIAL OPTIMIZADO")
        print("=" * 80)
        print(f"[BACKTEST] 📊 Símbolos procesados: {len(backtest_results)}")
        print(f"[BACKTEST] 📊 Total operaciones: {total_trades_global}")
        print(f"[BACKTEST] 📊 Velas totales analizadas: {total_velas:,}")

        if backtest_results:
            print(f"\n[BACKTEST] 📈 DETALLE POR ESTRATEGIA:")
            print("-" * 80)
            print(f"{'Símbolo':<12} {'Estrategia':<20} {'Trades':<8} {'P&L':<12} {'Win Rate':<10}")
            print("-" * 80)

            for symbol, strategies in backtest_results.items():
                for strategy_name, result in strategies.items():
                    trades = result.get('total_trades', 0)
                    pnl = result.get('total_pnl', 0)
                    win_rate = result.get('win_rate', 0) * 100

                    print(f"{symbol:<12} {strategy_name:<20} {trades:<8} ${pnl:<11.2f} {win_rate:<9.1f}%")

            # Ranking final
            print(f"\n[BACKTEST] 🥇 RANKING FINAL (por P&L) - CON LOTES:")
            print("-" * 80)

            all_results = []
            for symbol, strategies in backtest_results.items():
                for strategy_name, result in strategies.items():
                    all_results.append({
                        'symbol': symbol,
                        'strategy': strategy_name,
                        'pnl': result.get('total_pnl', 0),
                        'trades': result.get('total_trades', 0),
                        'win_rate': result.get('win_rate', 0) * 100
                    })

            # Ordenar por P&L descendente
            all_results.sort(key=lambda x: x['pnl'], reverse=True)

            for i, result in enumerate(all_results[:10], 1):  # Top 10
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}"
                print(f"{medal} {result['symbol']:<8} {result['strategy']:<20} ${result['pnl']:>10.2f} ({result['trades']} trades)")

            # Estadísticas generales
            total_pnl = sum(r['pnl'] for r in all_results)
            avg_win_rate = (sum(r['win_rate'] for r in all_results) / len(all_results)) if all_results else 0
            # Guardar resultados para dashboard
            try:
                import json
                from pathlib import Path
                # Directorio de salida para dashboard
                out_dir = Path(__file__).parent.parent / "data" / "dashboard_results"
                # Limpiar resultados antiguos para evitar datos obsoletos
                if out_dir.exists():
                    for old in out_dir.glob("*.json"):
                        try:
                            old.unlink()
                        except Exception:
                            pass
                out_dir.mkdir(parents=True, exist_ok=True)
                # Guardar por símbolo - MEJORADO: Guardar TODAS las métricas
                for symbol, strategies in backtest_results.items():
                    # Reemplazar "/" por "_" para nombres de archivo válidos
                    safe_symbol = symbol.replace("/", "_")
                    file_path = out_dir / f"{safe_symbol}_results.json"

                    # Convertir int64/float64 a tipos nativos de Python para JSON
                    def convert_to_native(obj):
                        import numpy as np
                        if isinstance(obj, dict):
                            return {k: convert_to_native(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_to_native(item) for item in obj]
                        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
                            return int(obj)
                        elif isinstance(obj, (np.float64, np.float32)):
                            return float(obj)
                        else:
                            return obj

                    strategies_native = convert_to_native(strategies)

                    # DEBUG: Verificar qué se está guardando
                    print(f"[BACKTEST] 💾 Guardando resultados para {symbol}: {len(strategies_native)} estrategias")
                    for strat_name, strat_data in strategies_native.items():
                        if isinstance(strat_data, dict):
                            trades_count = len(strat_data.get('trades', []))
                            print(f"[BACKTEST] 💾   {strat_name}: {strat_data.get('total_trades', 0)} trades, {trades_count} trades en lista")

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({'symbol': symbol, 'strategies': strategies_native}, f, indent=2, ensure_ascii=False)
                # Resumen global
                summary = {
                    'total_symbols': len(backtest_results),
                    'period': {
                        'start_date': config.backtesting.start_date,
                        'end_date': config.backtesting.end_date,
                        'timeframe': config.backtesting.timeframe
                    },
                    'metrics': {
                        'total_pnl': total_pnl,
                        'total_trades': total_trades_global,
                        'avg_win_rate': avg_win_rate
                    }
                }
                with open(out_dir / 'global_summary.json', 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print(f"[BACKTEST] ✅ Resultados guardados para dashboard en {out_dir}")
            except Exception as e:
                print(f"[BACKTEST] ❌ Error guardando resultados para dashboard: {e}")

            print(f"\n[BACKTEST] 📊 ESTADÍSTICAS GENERALES:")
            print(f"   • P&L Total: ${total_pnl:.2f}")
            print(f"   • Win Rate Promedio: {avg_win_rate:.1f}%")
            print(f"   • Velas Analizadas: {total_velas:,}")
            print(f"   • Período: {config.backtesting.start_date} a {config.backtesting.end_date}")
            print(f"   • Método: Procesamiento secuencial optimizado")

        await downloader.shutdown()
        print("[BACKTEST] ✅ Backtesting completado exitosamente con descargas por lotes")

    except Exception as e:
        print(f"[BACKTEST] ❌ Error general: {e}")
        import traceback
        traceback.print_exc()

async def save_backtest_results(backtest_results, config):
    """
    Guarda los resultados del backtesting en formato JSON para el dashboard
    """
    try:
        import json
        from pathlib import Path

        # Directorio de salida para dashboard
        out_dir = Path(__file__).parent.parent / "data" / "dashboard_results"

        # Limpiar resultados antiguos
        if out_dir.exists():
            for old in out_dir.glob("*.json"):
                try:
                    old.unlink()
                except Exception:
                    pass

        out_dir.mkdir(parents=True, exist_ok=True)

        # Guardar por símbolo
        for symbol, strategies in backtest_results.items():
            safe_symbol = symbol.replace("/", "_").replace(":", "_")
            file_path = out_dir / f"{safe_symbol}_results.json"

            # Convertir tipos numpy a nativos de Python
            def convert_to_native(obj):
                import numpy as np
                from datetime import datetime
                import pandas as pd

                if isinstance(obj, dict):
                    # Para el dashboard, incluir métricas principales y trades simplificados
                    result = {}
                    for k, v in obj.items():
                        # Excluir datos pesados que no necesita el dashboard
                        if k in ['compensation_trades_data']:
                            continue  # No incluir datos de compensación
                        elif k == 'trades':
                            # Convertir trades a formato serializable, excluyendo campos problemáticos
                            if isinstance(v, list) and len(v) > 0:
                                simplified_trades = []
                                for trade in v:
                                    if isinstance(trade, dict):
                                        simplified_trade = {}
                                        for trade_k, trade_v in trade.items():
                                            # Excluir campos que causan problemas de serialización
                                            if trade_k not in ['entry_time', 'exit_time', 'ml_confidence', 'atr_at_entry']:
                                                if isinstance(trade_v, (datetime, pd.Timestamp)):
                                                    simplified_trade[trade_k] = trade_v.isoformat()
                                                elif isinstance(trade_v, (np.int64, np.int32, np.float64, np.float32)):
                                                    simplified_trade[trade_k] = float(trade_v) if '.' in str(trade_v) else int(trade_v)
                                                else:
                                                    simplified_trade[trade_k] = convert_to_native(trade_v)
                                        simplified_trades.append(simplified_trade)
                                result[k] = simplified_trades
                        elif k == 'equity_curve':
                            # Convertir equity_curve a lista serializable
                            if isinstance(v, (list, np.ndarray)):
                                result[k] = [float(x) for x in v]
                            elif hasattr(v, 'tolist'):
                                result[k] = [float(x) for x in v.tolist()]
                            else:
                                result[k] = []
                        else:
                            result[k] = convert_to_native(v)
                    return result
                elif isinstance(obj, list):
                    return [convert_to_native(item) for item in obj]
                elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
                    return int(obj)
                elif isinstance(obj, (np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, (datetime, pd.Timestamp)):
                    return obj.isoformat()  # Convertir timestamps a string ISO
                elif hasattr(obj, 'timestamp'):  # Otro tipo de timestamp
                    try:
                        return obj.timestamp()
                    except:
                        return str(obj)
                else:
                    return obj

            strategies_native = convert_to_native(strategies)

            print(f"[BACKTEST] 💾 Guardando resultados para {symbol}: {len(strategies_native)} estrategias")

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'symbol': symbol, 'strategies': strategies_native}, f, indent=2, ensure_ascii=False)

        print(f"[BACKTEST] ✅ Resultados guardados en {out_dir}")

    except Exception as e:
        print(f"[BACKTEST] ❌ Error guardando resultados: {e}")
        import traceback
        traceback.print_exc()

async def run_backtest_with_existing_data(config):
    """
    Ejecuta backtesting usando datos existentes en SQLite cuando el downloader falla
    """
    print("[BACKTEST] 🔄 BACKTESTING CON DATOS EXISTENTES")
    print("=" * 60)

    try:
        # Cargar datos existentes desde SQLite
        from utils.storage import DataStorage
        storage = DataStorage()

        processed_symbol_data = {}
        total_velas = 0

        for symbol in config.backtesting.symbols:
            try:
                print(f"[BACKTEST] 📥 Cargando datos existentes para {symbol}...")
                table_name = f"{symbol.replace('/', '_').replace('.', '_').replace(':', '_')}_{config.backtesting.timeframe}"
                print(f"[DEBUG] Buscando tabla: {table_name}")
                start_ts = int(pd.Timestamp(config.backtesting.start_date).timestamp()) if getattr(config.backtesting, 'start_date', None) else None
                end_ts = int(pd.Timestamp(config.backtesting.end_date).timestamp()) if getattr(config.backtesting, 'end_date', None) else None
                df = storage.query_data(table_name, start_ts, end_ts)
                print(f"[DEBUG] query_data devolvió: {type(df)}, len: {len(df) if df is not None else 'None'}")

                if df is not None and not df.empty:
                    # Asegurar que el índice sea timestamp
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)

                    processed_symbol_data[symbol] = df
                    velas = len(df)
                    total_velas += velas

                    # Calcular período disponible
                    min_date = df.index.min().strftime("%Y-%m-%d") if not df.empty else "N/A"
                    max_date = df.index.max().strftime("%Y-%m-%d") if not df.empty else "N/A"

                    print(f"[BACKTEST] ✅ {symbol}: {velas:,} velas cargadas | {min_date} → {max_date}")
                else:
                    print(f"[BACKTEST] ❌ No se pudieron cargar datos para {symbol}")
                    continue

            except Exception as e:
                print(f"[BACKTEST] ❌ Error cargando datos para {symbol}: {e}")
                continue

        if not processed_symbol_data:
            print("[BACKTEST] ❌ No se pudieron cargar datos para ningún símbolo")
            return

        print(f"[BACKTEST] 📊 Datos cargados: {len(processed_symbol_data)} símbolos, {total_velas:,} velas totales")

        # Ejecutar backtesting con datos existentes
        print(f"\n[BACKTEST] 🔄 Iniciando backtesting con datos existentes...")

        # Cargar estrategias activas
        active_strategies = load_strategies_from_config(config)
        if not active_strategies:
            print("[BACKTEST] ❌ ERROR: No hay estrategias activas configuradas")
            return

        print(f"[BACKTEST] 🎯 Estrategias activas: {list(active_strategies.keys())}")

        # Procesamiento secuencial
        backtest_results = {}
        total_trades_global = 0

        for symbol_idx, (symbol, df) in enumerate(processed_symbol_data.items(), 1):
            print(f"\n[BACKTEST] 📈 [{symbol_idx}/{len(processed_symbol_data)}] PROCESANDO: {symbol}")
            print("-" * 70)

            try:
                symbol_results = {}
                symbol_total_trades = 0

                for strategy_name, strategy in active_strategies.items():
                    print(f"[BACKTEST] ⚡ Ejecutando {strategy_name}...")

                    try:
                        # Crear backtester
                        strategy_backtester = AdvancedBacktester()

                        # Configurar parámetros
                        if hasattr(strategy_backtester, 'configure'):
                            strategy_backtester.configure({
                                'initial_capital': config.backtesting.initial_capital,
                                'commission': config.backtesting.commission,
                                'slippage': config.backtesting.slippage
                            })

                        # Ejecutar estrategia
                        result = strategy_backtester.run(strategy, df, symbol, config.backtesting.timeframe)

                        if result:
                            symbol_results[strategy_name] = result
                            trades = result.get('total_trades', 0)
                            symbol_total_trades += trades
                            pnl = result.get('total_pnl', 0)
                            win_rate = result.get('win_rate', 0) * 100

                            print(f"[BACKTEST] ✅ {strategy_name}: {trades} trades | P&L: ${pnl:.2f} | Win Rate: {win_rate:.1f}%")
                        else:
                            print(f"[BACKTEST] ❌ {strategy_name}: Sin resultados")

                    except Exception as e:
                        print(f"[BACKTEST] ❌ Error en {strategy_name}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                # Resultados del símbolo
                if symbol_results:
                    backtest_results[symbol] = symbol_results
                    total_trades_global += symbol_total_trades
                    print(f"[BACKTEST] 📊 {symbol} COMPLETADO: {symbol_total_trades} trades totales")
                else:
                    print(f"[BACKTEST] ❌ {symbol}: Sin resultados válidos")

            except Exception as e:
                print(f"[BACKTEST] ❌ Error procesando {symbol}: {e}")
                continue

        # Resultados finales
        print(f"\n[BACKTEST] 🏆 RESULTADOS FINALES - BACKTESTING CON DATOS EXISTENTES")
        print("=" * 80)
        print(f"[BACKTEST] 📊 Símbolos procesados: {len(backtest_results)}")
        print(f"[BACKTEST] 📊 Total operaciones: {total_trades_global}")

        if backtest_results:
            print(f"\n[BACKTEST] 📈 DETALLE POR ESTRATEGIA:")
            print("-" * 80)
            print(f"{'Símbolo':<12} {'Estrategia':<20} {'Trades':<8} {'P&L':<12} {'Win Rate':<10}")
            print("-" * 80)

            for symbol, strategies in backtest_results.items():
                for strategy_name, result in strategies.items():
                    trades = result.get('total_trades', 0)
                    pnl = result.get('total_pnl', 0)
                    win_rate = result.get('win_rate', 0) * 100

                    print(f"{symbol:<12} {strategy_name:<20} {trades:<8} ${pnl:<11.2f} {win_rate:<9.1f}%")

            # Guardar resultados
            await save_backtest_results(backtest_results, config)

            print(f"\n[BACKTEST] 💾 Resultados guardados en dashboard_results/")
            print(f"[BACKTEST] 📊 Para ver resultados: python main.py --dashboard-only")

        print("[BACKTEST] ✅ Backtesting completado exitosamente con datos existentes")

    except Exception as e:
        print(f"[BACKTEST] ❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ejecutar backtest completo
    asyncio.run(run_full_backtesting_with_batches())
    # Lanzar dashboard con resultados generados usando Streamlit
    try:
        import subprocess, sys
        from pathlib import Path
        dash_file = Path(__file__).parent.parent / 'utils' / 'dashboard.py'
        workdir = str(Path(__file__).parent.parent)
        print(f"[BACKTEST] 🚀 Lanzando dashboard con Streamlit: {dash_file}")
        cmd = [sys.executable, '-m', 'streamlit', 'run', str(dash_file), '--server.port', '8501']
        process = subprocess.Popen(cmd, cwd=workdir)
        print("\n  You can now view your Streamlit app in your browser.")
        print("  Local URL: http://localhost:8501")
        print(f"[BACKTEST] ✅ Dashboard iniciado con PID: {process.pid}")
        try:
            import webbrowser, time
            time.sleep(2)
            webbrowser.open_new_tab("http://localhost:8501")
            print("[BACKTEST] 🌐 Navegador abierto automáticamente")
        except Exception as browser_error:
            print(f"[BACKTEST] ⚠️ No se pudo abrir navegador automáticamente: {browser_error}")
        print("[BACKTEST] ✅ Sistema modular completado exitosamente")
    except Exception as e:
        print(f"[BACKTEST] ❌ No se pudo lanzar el dashboard: {e}")