"""
Script para migrar datos CSV existentes a SQLite con nombres correctos
"""
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import DataStorage, save_data_method
import pandas as pd

def migrate_csv_to_sqlite():
    """Migrar datos CSV existentes a SQLite"""
    
    csv_dir = Path(__file__).parent.parent / 'data' / 'csv'
    storage = DataStorage()
    
    # Datos a migrar
    migrations = [
        {
            'csv_file': 'Volatility_75_Index_15m.csv',
            'symbol': 'Volatility 75 Index',
            'timeframe': '15m'
        }
    ]
    
    for migration in migrations:
        csv_path = csv_dir / migration['csv_file']
        
        if not csv_path.exists():
            print(f"⚠️ Archivo no encontrado: {csv_path}")
            continue
        
        print(f"\n📁 Procesando: {migration['csv_file']}")
        print(f"   Símbolo: {migration['symbol']}")
        print(f"   Timeframe: {migration['timeframe']}")
        
        try:
            # Leer CSV
            print("   🔄 Leyendo CSV...")
            df = pd.read_csv(csv_path)
            print(f"   ✅ Leído: {len(df)} filas")
            
            # Verificar columnas requeridas
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"   ❌ Faltan columnas: {missing_cols}")
                continue
            
            # Guardar en SQLite
            print("   💾 Guardando en SQLite...")
            result = save_data_method(storage, df, migration['symbol'], migration['timeframe'])
            
            if result:
                print(f"   ✅ Migración exitosa")
                
                # Verificar que se guardó correctamente
                table_name = f"{migration['symbol'].replace('/', '_').replace(' ', '_')}_{migration['timeframe']}"
                if storage.table_exists(table_name):
                    print(f"   ✅ Tabla '{table_name}' verificada")
                else:
                    print(f"   ⚠️ Tabla '{table_name}' no se pudo verificar")
            else:
                print(f"   ❌ Error en migración")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    migrate_csv_to_sqlite()
