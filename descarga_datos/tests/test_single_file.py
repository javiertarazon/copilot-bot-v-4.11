"""
Test simple con archivo único ACTIVE_COMMAND
"""
import time
from pathlib import Path
from datetime import datetime

base_dir = Path.home() / 'AppData' / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
cmd_file = base_dir / 'Bot_Commands' / 'ACTIVE_COMMAND.cmd'
rsp_file = base_dir / 'Bot_Responses' / 'ACTIVE_COMMAND.rsp'

print("\n" + "="*70)
print("  TEST SIMPLE - ARCHIVO ÚNICO")
print("="*70)

# Limpiar archivos anteriores
if cmd_file.exists():
    cmd_file.unlink()
    print("🗑️  Comando anterior eliminado")
if rsp_file.exists():
    rsp_file.unlink()
    print("🗑️  Respuesta anterior eliminada")

time.sleep(0.2)

# Crear comando
cmd_content = f"""ACTION=HEARTBEAT
TIMESTAMP={datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

print(f"\n📝 Creando comando: ACTIVE_COMMAND.cmd")
cmd_file.write_text(cmd_content)
print(f"✅ Comando creado")
print(f"📄 Contenido:\n{cmd_content}")

print(f"\n⏳ Esperando respuesta (15 segundos)...")
print("   Observa la pestaña 'Experts' en MT5 si tienes DEBUG activado\n")

found = False
start = time.time()

for i in range(150):  # 15 segundos (150 x 0.1s)
    time.sleep(0.1)
    
    if rsp_file.exists():
        found = True
        elapsed = time.time() - start
        
        # Leer respuesta
        try:
            content = rsp_file.read_text(encoding='utf-16')
        except:
            try:
                content = rsp_file.read_text()
            except:
                content = "[NO SE PUDO LEER]"
        
        print(f"\n✅ ¡RESPUESTA RECIBIDA! (después de {elapsed:.2f}s)")
        print(f"📄 Contenido:\n{content}")
        
        # Limpiar
        rsp_file.unlink()
        print("\n🧹 Archivos limpiados")
        break
    
    if (i + 1) % 10 == 0:
        print(f"   {(i+1)/10:.0f}s...", end=' ', flush=True)

if not found:
    print(f"\n\n❌ NO SE RECIBIÓ RESPUESTA")
    
    if cmd_file.exists():
        print("⚠️  El archivo ACTIVE_COMMAND.cmd SIGUE EXISTIENDO")
        print("   → EA no está procesando comandos")
    else:
        print("✅ El archivo .cmd fue eliminado")
        print("   → EA lo procesó pero no generó respuesta")
    
    print("\n🔍 VERIFICA EN MT5:")
    print("   1. EA está en el gráfico (icono en esquina superior derecha)")
    print("   2. AutoTrading está habilitado (botón verde)")
    print("   3. Pestaña 'Experts' muestra logs del EA")
    print("   4. Si ves '⏱️ Timer' → Timer funciona")
    print("   5. Si ves '📝 Comando pendiente detectado' → Encontró el comando")
    print("   6. Si ves '❌ ERROR' → Revisa el mensaje de error")

print("\n" + "="*70)
