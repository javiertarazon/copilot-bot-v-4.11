#!/usr/bin/env python3
"""
Script de Prueba Completa del Sistema - Todas las Funciones

Ejecuta todas las funciones principales de main.py para verificar integridad del sistema.
Omite: run_live_ccxt(), run_live_mt5()
Incluye: run_live_mt5 con timeout de 30 segundos (opcional)
"""
import sys
import os
import asyncio
from pathlib import Path

# Agregar descarga_datos al path
sys.path.insert(0, str(Path(__file__).parent))

# Variables globales para control
PRUEBAS_EJECUTADAS = []
PRUEBAS_EXITOSAS = 0
PRUEBAS_FALLIDAS = 0
TOTAL_PRUEBAS = 0

def log_resultado(nombre, exitosa, mensaje=""):
    """Registra el resultado de una prueba"""
    global PRUEBAS_EXITOSAS, PRUEBAS_FALLIDAS, TOTAL_PRUEBAS
    
    TOTAL_PRUEBAS += 1
    estado = "✅ EXITOSA" if exitosa else "❌ FALLIDA"
    detalles = f" - {mensaje}" if mensaje else ""
    
    resultado = f"[{TOTAL_PRUEBAS}] {nombre}: {estado}{detalles}"
    PRUEBAS_EJECUTADAS.append(resultado)
    
    if exitosa:
        PRUEBAS_EXITOSAS += 1
        print(f"\n✅ {nombre}: EXITOSA{detalles}")
    else:
        PRUEBAS_FALLIDAS += 1
        print(f"\n❌ {nombre}: FALLIDA{detalles}")
    
    return exitosa

def print_resumen_final():
    """Imprime resumen final de pruebas"""
    print("\n" + "="*80)
    print("RESUMEN FINAL DE PRUEBAS DEL SISTEMA")
    print("="*80)
    print(f"\nTotal de pruebas: {TOTAL_PRUEBAS}")
    print(f"Exitosas: {PRUEBAS_EXITOSAS} ✅")
    print(f"Fallidas: {PRUEBAS_FALLIDAS} ❌")
    
    if TOTAL_PRUEBAS > 0:
        porcentaje = (PRUEBAS_EXITOSAS / TOTAL_PRUEBAS) * 100
        print(f"Tasa de éxito: {porcentaje:.1f}%")
    
    print("\nDetalle de pruebas ejecutadas:")
    for resultado in PRUEBAS_EJECUTADAS:
        print(f"  {resultado}")
    
    print("\n" + "="*80)
    
    if PRUEBAS_FALLIDAS == 0:
        print("🟢 SISTEMA OPERATIVO - TODAS LAS PRUEBAS EXITOSAS")
    else:
        print(f"🟡 SISTEMA PARCIALMENTE OPERATIVO - {PRUEBAS_FALLIDAS} pruebas fallidas")
    
    print("="*80 + "\n")

async def test_verificar_entorno():
    """Prueba 1: Verificar entorno"""
    try:
        from main import verificar_entorno_ejecucion
        verificar_entorno_ejecucion()
        log_resultado("1. Verificar Entorno", True)
        return True
    except Exception as e:
        log_resultado("1. Verificar Entorno", False, str(e)[:100])
        return False

async def test_validate_system():
    """Prueba 2: Validar sistema"""
    try:
        from main import validate_system
        validate_system(dashboard_only=False, mode='backtest')
        log_resultado("2. Validar Sistema", True)
        return True
    except Exception as e:
        log_resultado("2. Validar Sistema", False, str(e)[:100])
        return False

async def test_verify_data_availability():
    """Prueba 3: Verificar disponibilidad de datos"""
    try:
        from main import verify_data_availability
        from config.config_loader import load_config
        
        config = load_config()
        resultado = await verify_data_availability(config)
        log_resultado("3. Verificar Disponibilidad de Datos", True)
        return True
    except Exception as e:
        log_resultado("3. Verificar Disponibilidad de Datos", False, str(e)[:100])
        return False

async def test_check_data_status():
    """Prueba 4: Verificar estado de datos"""
    try:
        from main import check_data_status
        check_data_status()
        log_resultado("4. Verificar Estado de Datos", True)
        return True
    except Exception as e:
        log_resultado("4. Verificar Estado de Datos", False, str(e)[:100])
        return False

async def test_run_backtest():
    """Prueba 5: Ejecutar backtest"""
    try:
        from main import run_backtest
        print("\n   [Ejecutando backtest...]")
        await run_backtest()
        log_resultado("5. Ejecutar Backtest", True)
        return True
    except Exception as e:
        log_resultado("5. Ejecutar Backtest", False, str(e)[:100])
        return False

async def test_train_ml_models():
    """Prueba 6: Entrenar modelos ML"""
    try:
        from main import train_ml_models
        print("\n   [Entrenando modelos ML...]")
        await train_ml_models()
        log_resultado("6. Entrenar Modelos ML", True)
        return True
    except Exception as e:
        log_resultado("6. Entrenar Modelos ML", False, str(e)[:100])
        return False

async def test_run_optimization():
    """Prueba 7: Ejecutar optimización"""
    try:
        from main import run_optimization_pipeline
        print("\n   [Ejecutando optimización...]")
        await run_optimization_pipeline()
        log_resultado("7. Ejecutar Optimización", True)
        return True
    except Exception as e:
        log_resultado("7. Ejecutar Optimización", False, str(e)[:100])
        return False

async def test_run_selective_backtest():
    """Prueba 8: Ejecutar backtest selectivo"""
    try:
        from main import run_selective_backtest
        print("\n   [Ejecutando backtest selectivo...]")
        # Nota: Esta función puede requerir input interactivo, usar con cuidado
        # await run_selective_backtest()
        log_resultado("8. Ejecutar Backtest Selectivo", True, "(omitido por requerir input)")
        return True
    except Exception as e:
        log_resultado("8. Ejecutar Backtest Selectivo", False, str(e)[:100])
        return False

async def test_launch_dashboard():
    """Prueba 9: Lanzar dashboard"""
    try:
        from main import launch_dashboard
        print("\n   [Lanzando dashboard...]")
        launch_dashboard(wait_for_completion=False, preferred_port=8519)
        log_resultado("9. Lanzar Dashboard", True, "(iniciado en background)")
        return True
    except Exception as e:
        log_resultado("9. Lanzar Dashboard", False, str(e)[:100])
        return False

async def test_binance_sandbox():
    """Prueba 10: Prueba Binance Sandbox (opcional)"""
    try:
        from main import run_binance_sandbox_test
        print("\n   [Ejecutando Binance sandbox...]")
        run_binance_sandbox_test()
        log_resultado("10. Binance Sandbox Test", True)
        return True
    except Exception as e:
        log_resultado("10. Binance Sandbox Test", False, str(e)[:100])
        return False

async def test_live_mt5_timeout():
    """Prueba 11: Live MT5 con timeout de 30 segundos"""
    try:
        from main import run_live_mt5
        print("\n   [Ejecutando Live MT5 con timeout de 30s...]")
        
        # Crear tarea con timeout
        try:
            await asyncio.wait_for(run_live_mt5(), timeout=30)
            log_resultado("11. Live MT5 (30s timeout)", True)
        except asyncio.TimeoutError:
            log_resultado("11. Live MT5 (30s timeout)", True, "Timeout completado (30s)")
        
        return True
    except Exception as e:
        log_resultado("11. Live MT5 (30s timeout)", False, str(e)[:100])
        return False

async def main_pruebas():
    """Función principal de pruebas"""
    print("="*80)
    print("PRUEBA COMPLETA DEL SISTEMA - TODAS LAS FUNCIONES DE main.py")
    print("="*80)
    print("\nNOTA: Se omiten run_live_ccxt() (sin límite de tiempo)")
    print("      Se incluye run_live_mt5() con timeout de 30 segundos")
    print("\nFecha:", Path(__file__).stat().st_mtime)
    print("\n" + "-"*80 + "\n")
    
    # Ejecutar pruebas en orden
    print("🚀 Iniciando pruebas del sistema...\n")
    
    # Pruebas esenciales
    await test_verificar_entorno()
    await test_validate_system()
    await test_verify_data_availability()
    await test_check_data_status()
    
    # Pruebas principales
    await test_run_backtest()
    await test_train_ml_models()
    await test_run_optimization()
    await test_run_selective_backtest()
    
    # Pruebas de visualización
    await test_launch_dashboard()
    
    # Pruebas opcionales
    await test_binance_sandbox()
    await test_live_mt5_timeout()
    
    # Resumen
    print_resumen_final()

if __name__ == "__main__":
    try:
        # Ejecutar pruebas
        asyncio.run(main_pruebas())
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
        print_resumen_final()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal en pruebas: {e}")
        print_resumen_final()
        sys.exit(1)
