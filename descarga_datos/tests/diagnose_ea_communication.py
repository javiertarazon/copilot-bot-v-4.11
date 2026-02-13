"""
Diagnóstico de comunicación EA - verifica archivos y procesos
"""
import os
from pathlib import Path
import time
from datetime import datetime

# Directorio base de MT5 Common Files
base_dir = Path(os.getenv('APPDATA')) / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'

print("\n" + "="*70)
print("  DIAGNÓSTICO DE COMUNICACIÓN EA")
print("="*70)

# 1. Verificar directorios
print("\n📁 VERIFICANDO DIRECTORIOS:")
for dir_name in ['Bot_Commands', 'Bot_Responses', 'Bot_Status.txt', 'Bot_Ticks', 'Bot_Data']:
    path = base_dir / dir_name
    exists = "✅" if path.exists() else "❌"
    print(f"   {exists} {dir_name}: {path}")
    if path.exists() and path.is_dir():
        files = list(path.glob('*'))
        print(f"      Archivos: {len(files)}")
        if files:
            for f in files[:5]:  # Mostrar primeros 5
                age = time.time() - f.stat().st_mtime
                print(f"        - {f.name} (hace {age:.0f}s)")

# 2. Verificar Bot_Status.txt
print("\n📄 BOT_STATUS.TXT:")
status_file = base_dir / 'Bot_Status.txt'
if status_file.exists():
    age = time.time() - status_file.stat().st_mtime
    content = status_file.read_text()
    print(f"   ✅ Actualizado hace {age:.0f} segundos")
    print(f"   Contenido:\n{content}")
else:
    print("   ❌ No existe")

# 3. Crear archivo de comando TEST
print("\n🔧 CREANDO COMANDO DE PRUEBA:")
cmd_file = base_dir / 'Bot_Commands' / 'TEST_MANUAL.cmd'
cmd_content = """ACTION=HEARTBEAT
TIMESTAMP={}
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

try:
    cmd_file.write_text(cmd_content)
    print(f"   ✅ Comando creado: {cmd_file.name}")
    print(f"   Contenido:\n{cmd_content}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Esperar respuesta
print("\n⏳ ESPERANDO RESPUESTA (15 segundos)...")
rsp_file = base_dir / 'Bot_Responses' / 'TEST_MANUAL.rsp'
start = time.time()
found = False

for i in range(15):
    time.sleep(1)
    if rsp_file.exists():
        found = True
        age = time.time() - rsp_file.stat().st_mtime
        content = rsp_file.read_text()
        print(f"\n   ✅ RESPUESTA RECIBIDA (después de {i+1}s)")
        print(f"   Contenido:\n{content}")
        break
    else:
        print(f"   {i+1}s... ", end='', flush=True)

if not found:
    print("\n   ❌ NO SE RECIBIÓ RESPUESTA")
    
    # Verificar si el comando sigue ahí
    if cmd_file.exists():
        print("   ⚠️  El archivo .cmd SIGUE EXISTIENDO - EA no lo procesó")
    else:
        print("   ⚠️  El archivo .cmd fue eliminado - EA lo procesó pero no generó respuesta")

# 5. Listar todos los archivos recientes
print("\n📋 ARCHIVOS RECIENTES EN BOT_COMMANDS:")
cmd_dir = base_dir / 'Bot_Commands'
if cmd_dir.exists():
    files = sorted(cmd_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[:10]:
        age = time.time() - f.stat().st_mtime
        print(f"   - {f.name} (hace {age:.0f}s)")

print("\n📋 ARCHIVOS RECIENTES EN BOT_RESPONSES:")
rsp_dir = base_dir / 'Bot_Responses'
if rsp_dir.exists():
    files = sorted(rsp_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[:10]:
        age = time.time() - f.stat().st_mtime
        print(f"   - {f.name} (hace {age:.0f}s)")

print("\n" + "="*70)
print("INSTRUCCIONES:")
print("  1. Si el comando NO fue procesado → EA no está leyendo comandos")
print("  2. Si el comando fue eliminado pero no hay respuesta → EA tiene error al escribir")
print("  3. Revisa logs en MT5: Herramientas → Journal (pestaña 'Experts')")
print("="*70)
