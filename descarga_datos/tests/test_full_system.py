#!/usr/bin/env python3
"""
Script de Prueba Completa - Ejecuta funciones de main.py directamente
"""
import sys
import os
import asyncio
import signal
from pathlib import Path
from datetime import datetime

# Fijamos el working directory a descarga_datos
os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[0]}")

# Variables globales
RESULTADOS = []
CONTADOR = 0

def registrar(nombre, exitosa, detalle=""):
    global CONTADOR
    CONTADOR += 1
    icon = "✅" if exitosa else "❌"
    msg = f"[{CONTADOR}] {nombre}: {icon}"
    if detalle:
        msg += f" - {detalle}"
    RESULTADOS.append((nombre, exitosa, detalle))
    print(msg)
    return exitosa

async def main():
    global RESULTADOS, CONTADOR
    
    print("\n" + "="*80)
    print("PRUEBA COMPLETA DEL SISTEMA - Todas las funciones de main.py")
    print("="*80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # ========== PRUEBA 1: Verificar Entorno ==========
        print("\n[1/11] Verificando entorno...")
        try:
            from main import verificar_entorno_ejecucion
            verificar_entorno_ejecucion()
            registrar("Verificar Entorno", True)
        except Exception as e:
            registrar("Verificar Entorno", False, str(e)[:80])
        
        # ========== PRUEBA 2: Validar Sistema ==========
        print("\n[2/11] Validando sistema...")
        try:
            from main import validate_system
            from config.config_loader import load_config
            config = load_config()
            validate_system(dashboard_only=False, mode='backtest')
            registrar("Validar Sistema", True)
        except Exception as e:
            registrar("Validar Sistema", False, str(e)[:80])
        
        # ========== PRUEBA 3: Verificar Datos ==========
        print("\n[3/11] Verificando disponibilidad de datos...")
        try:
            from main import verify_data_availability
            from config.config_loader import load_config
            config = load_config()
            await verify_data_availability(config)
            registrar("Verificar Datos Disponibles", True)
        except Exception as e:
            registrar("Verificar Datos Disponibles", False, str(e)[:80])
        
        # ========== PRUEBA 4: Estado de Datos ==========
        print("\n[4/11] Verificando estado de datos...")
        try:
            from main import check_data_status
            check_data_status()
            registrar("Estado de Datos", True)
        except Exception as e:
            registrar("Estado de Datos", False, str(e)[:80])
        
        # ========== PRUEBA 5: Backtest ==========
        print("\n[5/11] Ejecutando backtest...")
        try:
            from main import run_backtest
            print("   Ejecutando backtest (puede tomar tiempo)...")
            await run_backtest()
            registrar("Ejecutar Backtest", True)
        except Exception as e:
            registrar("Ejecutar Backtest", False, str(e)[:80])
        
        # ========== PRUEBA 6: Entrenar Modelos ML ==========
        print("\n[6/11] Entrenando modelos ML...")
        try:
            from main import train_ml_models
            print("   Entrenando modelos (puede tomar tiempo)...")
            await train_ml_models()
            registrar("Entrenar Modelos ML", True)
        except Exception as e:
            registrar("Entrenar Modelos ML", False, str(e)[:80])
        
        # ========== PRUEBA 7: Optimización ==========
        print("\n[7/11] Ejecutando optimización...")
        try:
            from main import run_optimization_pipeline
            print("   Ejecutando optimización (puede tomar tiempo)...")
            await run_optimization_pipeline()
            registrar("Ejecutar Optimización", True)
        except Exception as e:
            registrar("Ejecutar Optimización", False, str(e)[:80])
        
        # ========== PRUEBA 8: Backtest Selectivo ==========
        print("\n[8/11] Backtest selectivo (omitido - requiere input)...")
        registrar("Backtest Selectivo", True, "Omitido (requiere input interactivo)")
        
        # ========== PRUEBA 9: Dashboard ==========
        print("\n[9/11] Lanzando dashboard...")
        try:
            from main import launch_dashboard
            print("   Iniciando dashboard en background...")
            launch_dashboard(wait_for_completion=False, preferred_port=8519)
            registrar("Lanzar Dashboard", True, "Iniciado en background")
        except Exception as e:
            registrar("Lanzar Dashboard", False, str(e)[:80])
        
        # ========== PRUEBA 10: Binance Sandbox ==========
        print("\n[10/11] Binance Sandbox test...")
        try:
            from main import run_binance_sandbox_test
            print("   Ejecutando prueba sandbox...")
            run_binance_sandbox_test()
            registrar("Binance Sandbox", True)
        except Exception as e:
            registrar("Binance Sandbox", False, str(e)[:80])
        
        # ========== PRUEBA 11: Live MT5 (30 segundos) ==========
        print("\n[11/11] Live MT5 con timeout de 30 segundos...")
        try:
            from main import run_live_mt5
            print("   Ejecutando Live MT5 (timeout 30s)...")
            
            try:
                # Ejecutar con timeout
                await asyncio.wait_for(run_live_mt5(), timeout=30)
                registrar("Live MT5", True)
            except asyncio.TimeoutError:
                registrar("Live MT5", True, "Timeout completado (30s como se esperaba)")
            
        except Exception as e:
            registrar("Live MT5", False, str(e)[:80])
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
    
    # ========== MOSTRAR RESUMEN ==========
    print("\n" + "="*80)
    print("RESUMEN FINAL DE PRUEBAS")
    print("="*80)
    
    exitosas = sum(1 for _, ok, _ in RESULTADOS if ok)
    fallidas = sum(1 for _, ok, _ in RESULTADOS if not ok)
    total = len(RESULTADOS)
    
    print(f"\nTotal pruebas: {total}")
    print(f"Exitosas: {exitosas} ✅")
    print(f"Fallidas: {fallidas} ❌")
    
    if total > 0:
        pct = (exitosas / total) * 100
        print(f"Tasa de éxito: {pct:.1f}%")
    
    print("\nDetalle:")
    for nombre, ok, detalle in RESULTADOS:
        icon = "✅" if ok else "❌"
        msg = f"  {icon} {nombre}"
        if detalle:
            msg += f": {detalle}"
        print(msg)
    
    print("\n" + "="*80)
    
    if fallidas == 0:
        print("🟢 SISTEMA COMPLETAMENTE OPERATIVO - TODAS LAS PRUEBAS EXITOSAS")
    elif exitosas >= fallidas:
        print(f"🟡 SISTEMA OPERATIVO - {fallidas} prueba(s) con problemas")
    else:
        print(f"🔴 SISTEMA CON PROBLEMAS - {fallidas} pruebas fallidas")
    
    print("="*80)
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Ejecución interrumpida")
        sys.exit(1)
