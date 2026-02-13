#!/usr/bin/env python3
"""
Verificador de Estado - Simple Bridge EA
Muestra el estado actual del EA y archivos de comunicación
"""

import sys
import os
from pathlib import Path
from datetime import datetime

def check_status():
    print("\n" + "="*70)
    print("  VERIFICADOR DE ESTADO - SIMPLE BRIDGE EA")
    print("="*70)
    
    # Directorio MT5 Common
    mt5_common = Path(os.getenv('APPDATA')).parent / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
    
    print(f"\n📁 Directorio Base MT5:")
    print(f"   {mt5_common}")
    print(f"   Existe: {'✅' if mt5_common.exists() else '❌'}")
    
    # Directorios de comunicación
    dirs = {
        'Comandos': mt5_common / 'Bot_Commands',
        'Respuestas': mt5_common / 'Bot_Responses',
        'Ticks': mt5_common / 'Bot_Ticks',
        'Datos': mt5_common / 'Bot_Data'
    }
    
    print(f"\n📂 Directorios de Comunicación:")
    for name, path in dirs.items():
        exists = path.exists()
        files = len(list(path.glob('*'))) if exists else 0
        print(f"   {name:12} {'✅' if exists else '❌'} - {files} archivos - {path}")
    
    # Archivo de estado
    status_file = mt5_common / 'Bot_Status.txt'
    print(f"\n📄 Archivo de Estado:")
    print(f"   {status_file}")
    
    if status_file.exists():
        print(f"   Estado: ✅ EXISTE")
        try:
            with open(status_file, 'r') as f:
                content = f.read()
                print(f"\n   Contenido:")
                for line in content.split('\n'):
                    if line.strip():
                        print(f"      {line}")
            
            # Verificar frescura del archivo
            mtime = datetime.fromtimestamp(status_file.stat().st_mtime)
            age = (datetime.now() - mtime).total_seconds()
            
            print(f"\n   Última actualización: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Antigüedad: {age:.1f} segundos")
            
            if age > 60:
                print(f"   ⚠️  Archivo muy antiguo - EA podría no estar ejecutándose")
            else:
                print(f"   ✅ Archivo reciente - EA probablemente activo")
                
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
    else:
        print(f"   Estado: ❌ NO EXISTE")
        print(f"   ⚠️  El EA no se ha ejecutado o no tiene permisos")
    
    # Verificar archivos pendientes
    cmd_dir = dirs['Comandos']
    rsp_dir = dirs['Respuestas']
    
    if cmd_dir.exists():
        cmd_files = list(cmd_dir.glob('*.cmd'))
        if cmd_files:
            print(f"\n⚠️  Comandos pendientes: {len(cmd_files)}")
            for f in cmd_files[:5]:  # Mostrar máximo 5
                print(f"      {f.name}")
    
    if rsp_dir.exists():
        rsp_files = list(rsp_dir.glob('*.rsp'))
        if rsp_files:
            print(f"\n📥 Respuestas sin leer: {len(rsp_files)}")
            for f in rsp_files[:5]:
                print(f"      {f.name}")
    
    # Verificar EA en MT5
    print(f"\n🔍 Verificación MT5:")
    
    terminal_paths = list(Path(os.getenv('APPDATA')).parent.glob('Roaming/MetaQuotes/Terminal/*/MQL5/Experts/Simple_Bridge_EA.ex5'))
    
    if terminal_paths:
        print(f"   ✅ EA compilado encontrado:")
        for path in terminal_paths:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            print(f"      {path}")
            print(f"      Compilado: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"   ❌ EA compilado NO encontrado")
        print(f"   📝 Compila Simple_Bridge_EA.mq5 en MetaEditor (F7)")
    
    # Resumen final
    print(f"\n" + "="*70)
    print(f"  RESUMEN")
    print(f"="*70)
    
    checks = {
        'Directorio MT5': mt5_common.exists(),
        'Dirs comunicación': all(p.exists() for p in dirs.values()),
        'Archivo estado': status_file.exists(),
        'EA compilado': len(terminal_paths) > 0
    }
    
    all_ok = all(checks.values())
    
    for check, status in checks.items():
        icon = '✅' if status else '❌'
        print(f"   {icon} {check}")
    
    print(f"\n{'='*70}")
    
    if all_ok:
        print(f"  ✅ SISTEMA LISTO - Ejecuta tests para verificar funcionalidad")
    else:
        print(f"  ⚠️  CONFIGURACIÓN INCOMPLETA - Revisa los items marcados con ❌")
        print(f"\n  📝 SIGUIENTE PASO:")
        if not terminal_paths:
            print(f"     1. Abre MetaEditor en MT5")
            print(f"     2. Compila Simple_Bridge_EA.mq5 (F7)")
            print(f"     3. Arrastra Simple_Bridge_EA.ex5 a un gráfico")
        elif not status_file.exists():
            print(f"     1. Verifica que MT5 esté abierto")
            print(f"     2. Verifica que el EA esté en un gráfico")
            print(f"     3. Habilita AutoTrading (botón verde)")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    check_status()
