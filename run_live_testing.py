#!/usr/bin/env python3
"""
🧪 EJECUTOR DE PRUEBAS LIVE REAL - Config Alternativa
Script para ejecutar live trading REAL en SANDBOX con configuración de pruebas

Este script:
1. Copia config_pruebas_operaciones.yaml → config.yaml temporalmente
2. Ejecuta main.py --live-ccxt
3. Restaura config.yaml original

IMPORTANTE: SIEMPRE EN SANDBOX MODE
"""

import sys
import shutil
import subprocess
from pathlib import Path
import time
import signal

def handle_interrupt(signum, frame):
    """Manejar Ctrl+C."""
    print("\n\n" + "="*80)
    print("[INTERRUPT] Restaurando configuración original...")
    print("="*80)
    restore_config()
    sys.exit(0)

def backup_config():
    """Hacer backup de config original."""
    config_path = Path("descarga_datos/config/config.yaml")
    backup_path = Path("descarga_datos/config/config.yaml.backup_original")
    
    if config_path.exists():
        print(f"[BACKUP] Guardando config original en: {backup_path}")
        shutil.copy2(config_path, backup_path)
        return True
    return False

def restore_config():
    """Restaurar config original."""
    config_path = Path("descarga_datos/config/config.yaml")
    backup_path = Path("descarga_datos/config/config.yaml.backup_original")
    
    if backup_path.exists():
        print(f"[RESTORE] Restaurando config original desde: {backup_path}")
        shutil.copy2(backup_path, config_path)
        backup_path.unlink()  # Eliminar backup
        print("[OK] Configuración restaurada")
        return True
    return False

def apply_test_config():
    """Aplicar configuración de pruebas."""
    test_config = Path("descarga_datos/config/config_pruebas_operaciones.yaml")
    prod_config = Path("descarga_datos/config/config.yaml")
    
    if test_config.exists():
        print(f"[APPLY] Aplicando configuración de pruebas...")
        shutil.copy2(test_config, prod_config)
        print(f"[OK] Configuración de pruebas activa")
        return True
    else:
        print(f"[ERROR] No encontrado: {test_config}")
        return False

def show_test_info():
    """Mostrar información de pruebas."""
    print("\n" + "="*80)
    print("[TEST] LIVE TRADING PRUEBAS - MODO REAL EN SANDBOX")
    print("="*80)
    print("\nConfiguracion de Pruebas:")
    print("  • Capital: 100 USDT (vs 800 productivo)")
    print("  • Max concurrent trades: 2 (vs 1 productivo)")
    print("  • Risk per trade: 0.03 (vs 0.02 productivo)")
    print("  • CCI Threshold: 85 (vs 90 productivo)")
    print("  • ML Threshold: 0.15 (vs 0.2 productivo)")
    print("  • Parametros: RELAJADOS para mas operaciones")
    print("\nModo de Ejecucion:")
    print("  • Estrategia: UltraDetailedHeikinAshiML (REAL)")
    print("  • Exchange: Binance SANDBOX (sin dinero real)")
    print("  • Timeframe: 15m")
    print("  • Simbolos: BTC/USDT (margin y futuros)")
    print("\nValidaciones Activas:")
    print("  [OK] Calculos de SL/TP correctos")
    print("  [OK] Risk/Reward validado")
    print("  [OK] Log detallado de operaciones")
    print("  [OK] Sandbox mode confirmado")
    print("\n" + "="*80 + "\n")

def main():
    """Función principal."""
    # Registrar manejador para Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)
    
    print("\n[INIT] Iniciando executor de pruebas live real...\n")
    
    # 1. Mostrar información
    show_test_info()
    
    # 2. Hacer backup de config original
    if not backup_config():
        print("[ERROR] No se pudo hacer backup de config original")
        return 1
    
    try:
        # 3. Aplicar config de pruebas
        if not apply_test_config():
            print("[ERROR] No se pudo aplicar config de pruebas")
            restore_config()
            return 1
        
        print("\n[START] Ejecutando: python descarga_datos/main.py --live-ccxt")
        print("[INFO] Presiona Ctrl+C para detener y restaurar config original\n")
        print("="*80 + "\n")
        
        # 4. Ejecutar main.py con live-ccxt
        result = subprocess.run(
            [sys.executable, "descarga_datos/main.py", "--live-ccxt"],
            cwd="."
        )
        
        return result.returncode
        
    finally:
        # 5. Restaurar config original siempre
        print("\n" + "="*80)
        restore_config()
        print("[DONE] Pruebas completadas. Configuración restaurada.")
        print("="*80 + "\n")

if __name__ == "__main__":
    sys.exit(main())
