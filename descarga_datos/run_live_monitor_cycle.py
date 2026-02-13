import time
import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add core path to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'core'))

from core.live_trading_orchestrator import LiveTradingOrchestrator
from utils.logger import initialize_system_logging, get_logger

# Constants
CYCLE_DURATION_HOURS = 2
CHECK_INTERVAL_SECONDS = 60
LOG_FILE = os.path.join(current_dir, "logs", "live_monitor_cycle.log")
REPORTS_DIR = os.path.join(current_dir, "reports")

def ensure_directories():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_report(orchestrator, start_time, end_time):
    logger = get_logger("ReportGenerator")
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORTS_DIR, f"cycle_report_{report_id}.txt")
    
    logger.info(f"📝 Generando informe de ciclo sin operaciones: {report_path}")
    
    try:
        # 1. Market Status
        market_status = "Unknown"
        prices = {}
        try:
            # Check a few symbols
            symbols = orchestrator.live_config.get('symbols', [])
            for symbol in symbols:
                price_info = orchestrator.order_executor.get_current_price(symbol)
                if price_info:
                    prices[symbol] = price_info
            market_status = "Active" if prices else "No Price Data"
        except Exception as e:
            market_status = f"Error checking market: {str(e)}"

        # 2. Strategy Status
        strategy_status = {}
        for name, strategy in orchestrator.strategy_instances.items():
            strategy_status[name] = "Loaded"
            # If strategy has internal state, we could try to read it here
            
        # 3. Connection Status
        mt5_connected = orchestrator.order_executor.is_connected()
        account_info = "Unknown"
        try:
            import MetaTrader5 as mt5
            if mt5_connected:
                acc = mt5.account_info()
                if acc:
                    account_info = f"Login: {acc.login}, Server: {acc.server}, Balance: {acc.balance}, Equity: {acc.equity}"
        except:
            pass

        # 4. Logs (last 50 lines from log file)
        recent_logs = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_logs = lines[-50:]
            except:
                recent_logs = ["Error reading log file"]

        # Write Report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"=== INFORME DE CICLO DE SUPERVISIÓN: {report_id} ===\n")
            f.write(f"Período: {start_time} - {end_time}\n")
            f.write(f"Razón: No se generaron operaciones (trades) en 2 horas.\n\n")
            
            f.write(f"--- 1. ESTADO DEL MERCADO ---\n")
            f.write(f"Estado General: {market_status}\n")
            if prices:
                f.write("Precios actuales:\n")
                for sym, p in prices.items():
                    f.write(f"  {sym}: Bid={p.get('bid')}, Ask={p.get('ask')}\n")
            else:
                f.write("  No se pudieron obtener precios.\n")
            f.write("\n")
            
            f.write(f"--- 2. ESTADO DE LA ESTRATEGIA ---\n")
            for name, status in strategy_status.items():
                f.write(f"  Estrategia: {name} - Estado: {status}\n")
            f.write("  Nota: Revise los logs para ver por qué no se activaron las condiciones de entrada.\n")
            f.write("\n")
            
            f.write(f"--- 3. CONEXIÓN Y CUENTA ---\n")
            f.write(f"  Conexión MT5: {'✅ Conectado' if mt5_connected else '❌ Desconectado'}\n")
            f.write(f"  Info Cuenta: {account_info}\n")
            f.write("\n")
            
            f.write(f"--- 4. LOGS DE ACTIVIDAD (Últimas líneas) ---\n")
            for line in recent_logs:
                f.write(line)
            f.write("\n=== FIN DEL INFORME ===\n")
            
        logger.info(f"✅ Informe generado correctamente en {report_path}")
        
    except Exception as e:
        logger.error(f"❌ Error generando informe: {str(e)}")

def run_cycle():
    ensure_directories()
    initialize_system_logging({'level': 'INFO', 'file': LOG_FILE})
    logger = get_logger("LiveMonitor")
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        logger.info(f"\n{'='*50}")
        logger.info(f"🚀 INICIANDO CICLO #{cycle_count}")
        logger.info(f"⏱️  Duración programada: {CYCLE_DURATION_HOURS} horas")
        logger.info(f"{'='*50}\n")
        
        # Initialize orchestrator
        orchestrator = LiveTradingOrchestrator()
        
        if not orchestrator.start():
            logger.error("❌ Fallo al iniciar orquestador. Reintentando en 60 segundos...")
            time.sleep(60)
            continue
            
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=CYCLE_DURATION_HOURS)
        
        # Get initial trade count (safe access)
        cycle_trades_start = 0
        if hasattr(orchestrator, 'tracker') and hasattr(orchestrator.tracker, 'total_trades'):
            cycle_trades_start = orchestrator.tracker.total_trades
        
        cycle_interrupted = False
        
        try:
            while datetime.now() < end_time:
                if not orchestrator.running:
                    logger.error("⚠️ El orquestador se detuvo inesperadamente.")
                    cycle_interrupted = True
                    break 
                
                # Monitor connection
                if not orchestrator.order_executor.is_connected():
                     logger.warning("⚠️ Conexión MT5 perdida. Monitor: Esperando reconexión automática...")
                
                # Calculate remaining time
                remaining = end_time - datetime.now()
                mins, secs = divmod(remaining.total_seconds(), 60)
                hours, mins = divmod(mins, 60)
                
                # Log status every 15 minutes roughly (every 15th check)
                # But we check every minute
                logger.info(f"⏳ Tiempo restante del ciclo: {int(hours)}h {int(mins)}m - Supervisando sistema...")
                
                time.sleep(CHECK_INTERVAL_SECONDS)
            
            # End of cycle logic
            if not cycle_interrupted:
                logger.info("🏁 Ciclo de 2 horas completado.")
                
                # Check trades
                current_trades = 0
                if hasattr(orchestrator, 'tracker') and hasattr(orchestrator.tracker, 'total_trades'):
                    current_trades = orchestrator.tracker.total_trades
                
                trades_in_cycle = current_trades - cycle_trades_start
                logger.info(f"📊 Operaciones generadas en este ciclo: {trades_in_cycle}")
                
                if trades_in_cycle == 0:
                    logger.warning("⚠️ ALERTA: 0 Operaciones en 2 horas. Generando informe detallado...")
                    generate_report(orchestrator, start_time, datetime.now())
                else:
                    logger.info("✅ Se generaron operaciones. El sistema funciona correctamente.")
            
        except KeyboardInterrupt:
            logger.info("🛑 Detención manual solicitada por usuario.")
            orchestrator.stop()
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Error crítico en el ciclo de supervisión: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            if orchestrator.running:
                logger.info("⏹️ Deteniendo orquestador para reinicio de ciclo...")
                orchestrator.stop()
                
        logger.info("🔄 Reiniciando ciclo automáticamente en 10 segundos...")
        time.sleep(10)

if __name__ == "__main__":
    run_cycle()
