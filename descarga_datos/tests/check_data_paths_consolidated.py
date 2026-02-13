#!/usr/bin/env python3
"""
Validador de consolidación de carpetas de datos.
Verifica que solo exista una carpeta descarga_datos/data/ y que todas las rutas se resuelvan correctamente.
"""

import os
import sys
from pathlib import Path

# Agregar descarga_datos al path
repo_root = Path(__file__).parent.parent.parent
descarga_datos_path = repo_root / "descarga_datos"
if str(descarga_datos_path) not in sys.path:
    sys.path.insert(0, str(descarga_datos_path))

def check_duplicate_directories():
    """Verificar que no existan carpetas de datos duplicadas"""
    print("🔍 Verificando estructura de carpetas...")
    print("=" * 70)
    
    issues = []
    
    # Buscar carpetas "data" fuera de .venv
    for root, dirs, files in os.walk(str(repo_root)):
        # Excluir .venv y .git
        dirs[:] = [d for d in dirs if not d.startswith('.venv') and d != '.git' and d != '__pycache__']
        
        for dir_name in dirs:
            if dir_name == 'data' and 'descarga_datos' in root:
                data_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(data_path, str(repo_root))
                
                if rel_path != os.path.join('descarga_datos', 'data'):
                    issues.append(f"❌ Carpeta duplicada encontrada: {rel_path}")
                else:
                    print(f"✅ Carpeta de datos correcta: {rel_path}")
    
    # Verificar que NO exista descarga_datos/descarga_datos
    if (descarga_datos_path / "descarga_datos").exists():
        issues.append(f"❌ Carpeta anidada encontrada: descarga_datos/descarga_datos")
    else:
        print(f"✅ No existe carpeta anidada descarga_datos/descarga_datos")
    
    # Verificar que NO exista data en raíz
    if (repo_root / "data").exists():
        issues.append(f"❌ Carpeta data en raíz encontrada (debe estar solo en descarga_datos)")
    else:
        print(f"✅ No existe carpeta data duplicada en raíz")
    
    return issues

def check_file_references():
    """Verificar que los archivos utilicen rutas correctas"""
    print("\n🔍 Verificando referencias a rutas en código...")
    print("=" * 70)
    
    issues = []
    
    # Patrones de rutas incorrectas (excluir este mismo archivo)
    bad_patterns = [
        ('descarga_datos/descarga_datos', 'descarga_datos/descarga_datos'),
        ('descarga_datos/data/descarga_datos', 'descarga_datos/data/descarga_datos'),
        ("Path('data')", "Path('data')"),
    ]
    
    # Buscar en archivos Python
    python_files = list(descarga_datos_path.rglob("*.py"))
    
    for py_file in python_files:
        if '.venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        # Saltar este mismo archivo de validación
        if py_file.name == 'check_data_paths_consolidated.py':
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern, label in bad_patterns:
                    if pattern in content:
                        # Contar líneas
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern in line and not line.strip().startswith('#'):
                                rel_path = py_file.relative_to(repo_root)
                                issues.append(f"⚠️  {rel_path}:{i} - Ruta sospechosa: {label}")
        except Exception as e:
            pass
    
    if not issues:
        print("✅ No se encontraron referencias a rutas duplicadas en código")
    
    return issues

def check_data_integrity():
    """Verificar que los datos estén accesibles"""
    print("\n🔍 Verificando integridad de datos...")
    print("=" * 70)
    
    issues = []
    data_dir = descarga_datos_path / "data"
    
    if not data_dir.exists():
        issues.append(f"❌ Carpeta descarga_datos/data no existe!")
        return issues
    
    print(f"✅ Carpeta descarga_datos/data existe")
    
    # Verificar subcarpetas importantes
    important_dirs = [
        'csv',
        'backtests',
        'deriv_tests',
    ]
    
    for subdir in important_dirs:
        subdir_path = data_dir / subdir
        if subdir_path.exists():
            file_count = len(list(subdir_path.glob('*')))
            print(f"✅ {subdir}: {file_count} elementos")
        else:
            # Subcarpetas opcionales que se crean al usar el sistema - no son errores
            print(f"ℹ️  Subcarpeta {subdir} no encontrada (se creará cuando sea necesaria)")
    
    # Verificar base de datos
    db_path = data_dir / "data.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Base de datos: {size_mb:.2f} MB")
    else:
        print(f"ℹ️  Base de datos no existe aún (se creará en primera ejecución)")
    
    return issues

def check_module_imports():
    """Verificar que los módulos se carguen correctamente con las rutas actualizadas"""
    print("\n🔍 Verificando imports de módulos...")
    print("=" * 70)
    
    issues = []
    
    try:
        # Intentar importar módulos críticos
        from utils.storage import DataStorage
        print("✅ utils.storage importado correctamente")
    except ImportError as e:
        issues.append(f"❌ Error importando utils.storage: {e}")
    
    try:
        from utils.market_data_validator import MarketDataValidator
        print("✅ utils.market_data_validator importado correctamente")
    except ImportError as e:
        issues.append(f"❌ Error importando utils.market_data_validator: {e}")
    
    try:
        from utils.graceful_shutdown import GracefulShutdownHandler
        print("✅ utils.graceful_shutdown importado correctamente")
    except ImportError as e:
        issues.append(f"❌ Error importando utils.graceful_shutdown: {e}")
    
    return issues

def main():
    """Ejecutar todas las verificaciones"""
    print("\n" + "=" * 70)
    print("🔍 VALIDACIÓN DE CONSOLIDACIÓN DE DATOS")
    print("=" * 70)
    
    all_issues = []
    
    # Ejecutar checks
    all_issues.extend(check_duplicate_directories())
    all_issues.extend(check_file_references())
    all_issues.extend(check_data_integrity())
    all_issues.extend(check_module_imports())
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    
    if all_issues:
        print(f"\n⚠️  Se encontraron {len(all_issues)} problema(s):\n")
        for issue in all_issues:
            print(f"  {issue}")
        print("\n❌ VALIDACIÓN FALLIDA")
        return 1
    else:
        print("\n✅ VALIDACIÓN EXITOSA - Estructura de datos consolidada correctamente!")
        print("\n📋 Estructura verificada:")
        print("  ✅ Única carpeta de datos: descarga_datos/data/")
        print("  ✅ Sin carpetas duplicadas")
        print("  ✅ Referencias de rutas correctas en código")
        print("  ✅ Datos accesibles")
        print("  ✅ Módulos importan correctamente")
        return 0

if __name__ == '__main__':
    sys.exit(main())
