"""
Test con modo debug - verifica logs del EA
"""
import time
from pathlib import Path

print("\n" + "="*70)
print("  INSTRUCCIONES PARA ACTIVAR DEBUG MODE")
print("="*70)
print("""
1. En MT5, ve a la pestaña 'Experts' (abajo)
2. Haz clic derecho en el gráfico donde está el EA
3. Selecciona 'Expert Advisors' → 'Properties'
4. En la pestaña 'Inputs', cambia:
   - InpDebugMode: false → true
5. Click OK

6. Observa los logs en la pestaña 'Experts':
   - ⏱️ Timer #X - Buscando comandos...
   - 📝 Procesando comando: XXXX.cmd
   - ✅ Comando abierto correctamente
   - 💾 Guardando respuesta: XXXX.rsp

7. Si NO ves "📝 Procesando comando" → EA no encuentra archivos
8. Si ves error al abrir → Problema de permisos o ruta
9. Si ves error al guardar → Problema escribiendo respuesta
""")

print("\n🔄 ESPERANDO 10 SEGUNDOS PARA QUE ACTIVES DEBUG MODE...")
for i in range(10, 0, -1):
    print(f"   {i}...", end=' ', flush=True)
    time.sleep(1)

print("\n\n📝 AHORA EJECUTANDO TEST...")
print("="*70)

# Crear comando de prueba
from datetime import datetime
base_dir = Path.home() / 'AppData' / 'Roaming' / 'MetaQuotes' / 'Terminal' / 'Common' / 'Files'
cmd_file = base_dir / 'Bot_Commands' / 'DEBUG_TEST.cmd'

cmd_content = f"""ACTION=HEARTBEAT
TIMESTAMP={datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

cmd_file.write_text(cmd_content)
print(f"\n✅ Comando creado: {cmd_file.name}")

print("\n⏳ ESPERANDO RESPUESTA (15 segundos)...")
print("   Observa la pestaña 'Experts' en MT5 para ver los logs\n")

rsp_file = base_dir / 'Bot_Responses' / 'DEBUG_TEST.rsp'
found = False

for i in range(15):
    time.sleep(1)
    if rsp_file.exists():
        found = True
        content = rsp_file.read_text()
        print(f"\n   ✅ RESPUESTA RECIBIDA (después de {i+1}s)")
        print(f"   Contenido:\n{content}")
        break
    else:
        print(f"   {i+1}s...", end=' ', flush=True)

if not found:
    print("\n\n   ❌ NO SE RECIBIÓ RESPUESTA")
    if cmd_file.exists():
        print("   ⚠️  El archivo .cmd SIGUE EXISTIENDO")
    
    print("\n🔍 REVISA LOS LOGS EN MT5 (pestaña 'Experts'):")
    print("   - Si ves '⏱️ Timer' → Timer funciona")
    print("   - Si NO ves '📝 Procesando' → FileFindFirst falla")
    print("   - Si ves '❌ ERROR abriendo' → Problema al leer archivo")
    print("   - Si ves '❌ ERROR guardando' → Problema al escribir respuesta")

print("\n" + "="*70)
