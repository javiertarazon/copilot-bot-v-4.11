"""
Módulo de almacenamiento de datos con manejo consistente de timestamps.
"""
import sqlite3
import os
import json
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
from core.base_data_handler import BaseDataHandler, DataValidationResult
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_VALID_TS = int(pd.Timestamp('1980-01-01').timestamp())
MAX_VALID_TS = int(pd.Timestamp('2050-01-01').timestamp())

def _normalize_timestamp_series(series: pd.Series) -> pd.Series:
    """Normaliza timestamps a segundos Unix."""
    if pd.api.types.is_datetime64_any_dtype(series) or pd.api.types.is_datetime64tz_dtype(series):
        numeric = pd.to_numeric(pd.to_datetime(series, errors='coerce'), errors='coerce')
        max_abs = numeric.dropna().abs().max() if not numeric.dropna().empty else 0
        if max_abs > 10**17:
            numeric = numeric // 10**9  # nanosegundos -> segundos
        elif max_abs > 10**14:
            numeric = numeric // 10**6  # microsegundos -> segundos
        elif max_abs > 10**11:
            numeric = numeric // 10**3  # milisegundos -> segundos
        return numeric.astype('Int64')

    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors='coerce')
        max_abs = numeric.dropna().abs().max() if not numeric.dropna().empty else 0
        if max_abs > 10**14:
            numeric = numeric // 10**9  # nanosegundos -> segundos
        elif max_abs > 10**11:
            numeric = numeric // 10**3  # milisegundos -> segundos
        return numeric.astype('Int64')

    dt = pd.to_datetime(series, errors='coerce')
    return ((dt.astype('int64') // 10**9).astype('Int64'))

def _get_sqlite_type(dtype) -> str:
    """Maps pandas dtype to SQLite data type."""
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "REAL"
    # Timestamps and other objects will be stored as TEXT or INTEGER after conversion
    return "TEXT"

def _escape_table_name(table_name: str) -> str:
    """Escapa el nombre de tabla para SQL, usando comillas dobles si contiene espacios."""
    if ' ' in table_name or '-' in table_name:
        return f'"{table_name}"'
    return table_name

class DataStorage(BaseDataHandler):
    """Clase para el manejo de almacenamiento de datos."""
    
    def __init__(self, db_path: str = None):
        super().__init__()
        # Si no se proporciona path, usar ruta relativa desde este archivo
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'data.db')
        # Normalizar ruta: si comienza con "data/", cambiar a descarga_datos/data/
        elif db_path.startswith("data/"):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        self.db_path = db_path
        self._ensure_db_path()
        # Compatibilidad: algunas llamadas antiguas referencian self.logger
        # Asignamos el logger de módulo para evitar AttributeError
        # Garantizar siempre un logger operativo (evita AttributeError en llamadas heredadas)
        try:
            if not hasattr(self, 'logger') or self.logger is None:
                self.logger = logger
        except Exception:
            # Fallback silencioso; en el peor caso se usará el logger de módulo directamente
            pass
    
    def _ensure_db_path(self):
        """Asegura que el directorio de la base de datos existe."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Directorio creado: {db_dir}")
    
    def validate_data(self, data: Any) -> DataValidationResult:
        """
        Valida los datos proporcionados.

        Args:
            data: Datos a validar (DataFrame o lista de diccionarios)

        Returns:
            DataValidationResult con el resultado de la validación
        """
        try:
            # Convertir a DataFrame si es necesario
            df = pd.DataFrame(data) if isinstance(data, list) else data

            # Usar la validación específica de timestamp
            return self.validate_timestamp_column(df)

        except Exception as e:
            return DataValidationResult(
                False,
                [f"Error en validación de datos: {str(e)}"],
                []
            )
    
    def validate_timestamp_column(self, df: pd.DataFrame) -> DataValidationResult:
        """
        Valida la columna de timestamp en el DataFrame.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            DataValidationResult con el resultado de la validación
        """
        errors = []
        warnings = []
        
        # Verificar que existe columna timestamp
        if 'timestamp' not in df.columns:
            errors.append("Columna 'timestamp' no encontrada")
            return DataValidationResult(False, errors, warnings)
        
        # Verificar que no hay valores nulos
        null_count = df['timestamp'].isnull().sum()
        if null_count > 0:
            errors.append(f"Columna 'timestamp' tiene {null_count} valores nulos")
        
        # Verificar que los valores son válidos
        try:
            ts_series = pd.to_datetime(df['timestamp'], errors='coerce')
            invalid_count = ts_series.isnull().sum()
            if invalid_count > 0:
                errors.append(f"Columna 'timestamp' tiene {invalid_count} valores inválidos")
        except Exception as e:
            errors.append(f"Error convirtiendo timestamps: {e}")
        
        # Verificar orden temporal
        if len(df) > 1:
            is_sorted = df['timestamp'].is_monotonic_increasing
            if not is_sorted:
                warnings.append("Los timestamps no están en orden ascendente")
        
        return DataValidationResult(len(errors) == 0, errors, warnings)
    
    def save_to_sqlite(self, data: Union[pd.DataFrame, List[Dict[str, Any]]], 
                      table_name: str,
                      validate: bool = True) -> bool:
        """
        Guarda datos en SQLite con manejo consistente de timestamps.
        
        Args:
            data: DataFrame o lista de diccionarios con los datos
            table_name: Nombre de la tabla
            validate: Si se debe validar los datos antes de guardar
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Convertir a DataFrame si es necesario
            df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
            
            # Asegurar que el índice sea parte de las columnas si es timestamp
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
            
            # Validar datos si se requiere
            if validate:
                validation_result = self.validate_timestamp_column(df)
                if not validation_result.is_valid:
                    for error in validation_result.errors:
                        logger.error(f"Error de validación: {error}")
                    return False
                
                for warning in validation_result.warnings:
                    logger.warning(warning)
            
            # Preparar tipos de datos y convertir timestamps
            # Cuando se lee desde un CSV o DataFrame, asegurarse de que los timestamps estén en el formato correcto
            if 'timestamp' in df.columns:
                df['timestamp'] = _normalize_timestamp_series(df['timestamp'])
                df = df.dropna(subset=['timestamp'])
                df['timestamp'] = df['timestamp'].astype(np.int64)
                # Validar rango temporal
                if (df['timestamp'] < MIN_VALID_TS).any() or (df['timestamp'] > MAX_VALID_TS).any():
                    raise ValueError(f"Timestamps fuera del rango válido: 1970-01-01 a 2050-01-01")
            
            # Preparar tipos de datos para SQLite
            for col in df.columns:
                # Serializar objetos complejos
                if df[col].dtype == 'object':
                    if any(isinstance(x, (dict, list)) for x in df[col].dropna()):
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            
            # Guardar en SQLite con transacción atómica
            with sqlite3.connect(self.db_path) as conn:
                # Iniciar transacción
                conn.execute("BEGIN")
                
                try:
                    escaped_table = _escape_table_name(table_name)

                    # Fusionar históricos existentes por timestamp para conservar datos de distintos periodos
                    if self.table_exists(table_name):
                        try:
                            existing_df = pd.read_sql_query(f"SELECT * FROM {escaped_table}", conn)
                            if not existing_df.empty and 'timestamp' in existing_df.columns:
                                existing_df['timestamp'] = _normalize_timestamp_series(existing_df['timestamp'])
                                df['timestamp'] = _normalize_timestamp_series(df['timestamp'])
                                existing_df = existing_df.dropna(subset=['timestamp'])
                                df = df.dropna(subset=['timestamp'])
                                existing_df = existing_df[
                                    (existing_df['timestamp'] >= MIN_VALID_TS) &
                                    (existing_df['timestamp'] <= MAX_VALID_TS)
                                ]
                                df = df[
                                    (df['timestamp'] >= MIN_VALID_TS) &
                                    (df['timestamp'] <= MAX_VALID_TS)
                                ]
                                df = pd.concat([existing_df, df], ignore_index=True)
                                df = df.drop_duplicates(subset=['timestamp'], keep='last')
                                df = df.sort_values('timestamp').reset_index(drop=True)
                        except Exception as merge_error:
                            logger.warning(f"No se pudo fusionar histórico existente en {table_name}: {merge_error}")

                    # Crear tabla si no existe
                    column_definitions = []
                    for col in df.columns:
                        if col == 'timestamp':
                            dtype = 'INTEGER'
                        elif pd.api.types.is_float_dtype(df[col]):
                            dtype = 'REAL'
                        elif pd.api.types.is_integer_dtype(df[col]):
                            dtype = 'INTEGER'
                        else:
                            dtype = 'TEXT'
                        column_definitions.append(f"{col} {dtype}")
                    
                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {escaped_table} (
                        {', '.join(column_definitions)}
                    )
                    """
                    
                    # Recrear tabla con el histórico fusionado
                    conn.execute(f"DROP TABLE IF EXISTS {escaped_table}")
                    conn.execute(create_table_sql)
                    
                    # Guardar los datos
                    df.to_sql(table_name, conn, if_exists='append', index=False)
                    
                    # Confirmar transacción
                    conn.commit()
                    return True
                    
                except Exception as e:
                    # Revertir transacción en caso de error
                    conn.rollback()
                    raise e
                
        except Exception as e:
            logger.error(f"Error guardando datos en SQLite: {e}")
            return False
    
    def save_data(self, table_name: str, data: pd.DataFrame) -> bool:
        """
        Método principal para guardar datos. Limpia la tabla si existe.
        
        Args:
            table_name: Nombre de la tabla
            data: DataFrame con los datos a guardar
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Si la tabla existe, eliminar sus datos
            if self.table_exists(table_name):
                escaped_table = _escape_table_name(table_name)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(f"DROP TABLE IF EXISTS {escaped_table}")
            
            # Guardar los nuevos datos
            return self.save_to_sqlite(data, table_name)
        except Exception as e:
            logger.error(f"Error en save_data: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica si una tabla existe en la base de datos.
        
        Args:
            table_name: Nombre de la tabla a verificar
            
        Returns:
            bool: True si la tabla existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando tabla: {e}")
            return False
    
    def query_data(self, table_name: str, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta datos de la base de datos con filtros opcionales de timestamp.
        
        Args:
            table_name: Nombre de la tabla
            start_ts: Timestamp inicial en segundos (opcional)
            end_ts: Timestamp final en segundos (opcional)
            
        Returns:
            pd.DataFrame: DataFrame con los datos consultados
        """
        try:
            # Verificar si la tabla existe
            if not self.table_exists(table_name):
                # Usar tanto self.logger (si existe) como logger de módulo para robustez
                try:
                    self.logger.error(f"La tabla {table_name} no existe")
                except Exception:
                    logger.error(f"La tabla {table_name} no existe")
                return pd.DataFrame()

            # Construir la consulta SQL
            escaped_table = _escape_table_name(table_name)
            query = f"SELECT * FROM {escaped_table}"
            params = []
            
            if start_ts is not None and end_ts is not None:
                query += " WHERE timestamp >= ? AND timestamp <= ?"
                params.extend([start_ts, end_ts])
            
            query += " ORDER BY timestamp"
            
            # Ejecutar la consulta
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=params if params else None)
            
            if df.empty:
                try:
                    self.logger.warning(f"No se encontraron datos en la tabla {table_name}")
                except Exception:
                    logger.warning(f"No se encontraron datos en la tabla {table_name}")
                return pd.DataFrame()
            
            # Verificar que existe la columna timestamp
            if 'timestamp' not in df.columns:
                try:
                    self.logger.error(f"La columna timestamp no existe en la tabla {table_name}")
                except Exception:
                    logger.error(f"La columna timestamp no existe en la tabla {table_name}")
                return pd.DataFrame()
            
            # Convertir timestamp a datetime y establecer como índice
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
                
            return df
            
        except Exception as e:
            try:
                self.logger.error(f"Error consultando datos: {e}")
            except Exception:
                logger.error(f"Error consultando datos: {e}")
            return pd.DataFrame()

    # ===================== METADATA SUPPORT =====================
    def _ensure_metadata_table(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS data_metadata (
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        start_ts INTEGER,
                        end_ts INTEGER,
                        records INTEGER,
                        coverage_pct REAL,
                        asset_class TEXT,
                        source_exchange TEXT,
                        last_update_ts INTEGER DEFAULT (strftime('%s','now')),
                        PRIMARY KEY(symbol,timeframe)
                    )
                    """
                )
        except Exception as e:
            try:
                self.logger.error(f"Error creando tabla metadata: {e}")
            except Exception:
                logger.error(f"Error creando tabla metadata: {e}")

    def upsert_metadata(self, row: dict):
        self._ensure_metadata_table()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO data_metadata(symbol,timeframe,start_ts,end_ts,records,coverage_pct,asset_class,source_exchange,last_update_ts)
                    VALUES(?,?,?,?,?,?,?, ?,strftime('%s','now'))
                    ON CONFLICT(symbol,timeframe) DO UPDATE SET
                        start_ts=excluded.start_ts,
                        end_ts=excluded.end_ts,
                        records=excluded.records,
                        coverage_pct=excluded.coverage_pct,
                        asset_class=excluded.asset_class,
                        source_exchange=excluded.source_exchange,
                        last_update_ts=strftime('%s','now')
                    """,
                    (
                        row.get('symbol'),
                        row.get('timeframe'),
                        row.get('start_ts'),
                        row.get('end_ts'),
                        row.get('records'),
                        row.get('coverage_pct'),
                        row.get('asset_class'),
                        row.get('source_exchange', 'unknown')
                    )
                )
        except Exception as e:
            try:
                self.logger.error(f"Error upsert metadata: {e}")
            except Exception:
                logger.error(f"Error upsert metadata: {e}")

    def get_metadata(self, symbol: str, timeframe: str) -> Optional[dict]:
        self._ensure_metadata_table()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT symbol,timeframe,start_ts,end_ts,records,coverage_pct,asset_class,source_exchange,last_update_ts FROM data_metadata WHERE symbol=? AND timeframe=?",
                    (symbol, timeframe)
                )
                row = cur.fetchone()
                if not row:
                    return None
                keys = ['symbol','timeframe','start_ts','end_ts','records','coverage_pct','asset_class','source_exchange','last_update_ts']
                return dict(zip(keys,row))
        except Exception as e:
            try:
                self.logger.error(f"Error get_metadata: {e}")
            except Exception:
                logger.error(f"Error get_metadata: {e}")
            return None

def save_to_csv(data: Union[pd.DataFrame, List[Dict[str, Any]]], 
              filepath: str,
              storage: Optional[DataStorage] = None) -> bool:
    """
    Guarda datos en CSV con manejo consistente de timestamps.
    
    Args:
        data: DataFrame o lista de diccionarios con los datos
        filepath: Ruta del archivo CSV
        storage: Instancia opcional de DataStorage para validación
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Convertir a DataFrame si es necesario
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
        
        # Validar si hay storage
        if storage:
            validation_result = storage.validate_timestamp_column(df)
            if not validation_result.is_valid:
                logger.error("Datos inválidos para guardar en CSV")
                return False
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Guardar en CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Data saved to CSV: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando datos en CSV: {str(e)}")
        return False



# Additional functions for specific data types can be added here

# Métodos adicionales para compatibilidad con código centralizado
def get_data_without_validation(self, symbol: str, timeframe: str, start_date: str = None, end_date: str = None):
    """
    Método para obtener datos SIN validación de autenticidad.
    Este método está diseñado para ser utilizado SOLO por validadores de datos.
    
    Args:
        symbol: Símbolo a obtener
        timeframe: Timeframe a obtener
        start_date: Fecha inicial opcional en formato 'YYYY-MM-DD'
        end_date: Fecha final opcional en formato 'YYYY-MM-DD'
        
    Returns:
        pd.DataFrame o None si no hay datos
    """
    try:
        # Generar nombre de tabla estándar - eliminar espacios y caracteres especiales
        table_name = f"{symbol.replace('/', '_').replace(':', '_').replace(' ', '_')}_{timeframe}"
        
        # Convertir fechas a timestamps si se proporcionan
        start_ts = None
        end_ts = None
        
        if start_date:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            start_ts = int(start_dt.timestamp())
        
        if end_date:
            from datetime import datetime
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_ts = int(end_dt.timestamp())
        
        # Usar query_data existente
        data = self.query_data(table_name, start_ts, end_ts)
        
        if data.empty:
            return None
        
        return data
        
    except Exception as e:
        logger.error(f"Error en get_data_without_validation: {e}")
        return None

def get_data_method(self, symbol: str, timeframe: str, start_date: str = None, end_date: str = None):
    """
    Método de compatibilidad para obtener datos con la interfaz esperada por main.py.
    Incluye validación opcional de autenticidad de datos.
    
    Args:
        symbol: Símbolo a obtener
        timeframe: Timeframe a obtener
        start_date: Fecha inicial opcional en formato 'YYYY-MM-DD'
        end_date: Fecha final opcional en formato 'YYYY-MM-DD'
        
    Returns:
        pd.DataFrame o None si no hay datos
    """
    try:
        # Obtener datos sin validación
        data = self.get_data_without_validation(symbol, timeframe, start_date, end_date)
        
        if data is None or data.empty:
            return None
            
        # Verificar si se requiere validación de autenticidad
        try:
            import os
            validate_auth = os.environ.get('BT_VALIDATE_AUTH', '').lower() == 'true'
            
            if validate_auth and len(data) >= 100:
                # Importar validador solo si es necesario
                from utils.audit_real_data import validate_data_authenticity
                
                # Validar autenticidad
                validation = validate_data_authenticity(data, symbol, timeframe)
                
                # Registrar advertencia si los datos son sospechosos
                if not validation['is_authentic'] and validation['confidence'] < 50:
                    logger.warning(f"⚠️ ADVERTENCIA: Datos de {symbol} ({timeframe}) son sospechosos - {validation['reason']}")
                    # No bloqueamos el acceso, solo advertimos
        except ImportError:
            # Si no se puede importar el validador, continuamos sin validación
            pass
        except Exception as e:
            logger.error(f"Error en validación de datos para {symbol}: {e}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error en get_data: {e}")
        return None

def save_data_method(self, data: pd.DataFrame, symbol: str, timeframe: str):
    """
    Método de compatibilidad para guardar datos con la interfaz esperada por main.py
    """
    try:
        # Generar nombre de tabla estándar - eliminar espacios y caracteres especiales
        table_name = f"{symbol.replace('/', '_').replace(':', '_').replace(' ', '_')}_{timeframe}"
        
        # Usar save_data existente
        return self.save_data(table_name, data)
        
    except Exception as e:
        logger.error(f"Error en save_data: {e}")
        return False

# Asignar método de conveniencia para acceso directo
DataStorage.get_data_without_validation = get_data_without_validation

# Agregar métodos a la clase DataStorage
DataStorage.get_data = get_data_method
DataStorage.get_data_without_validation = get_data_without_validation
DataStorage.save_data_compat = save_data_method

# Sobreescribir save_data para manejar ambas interfaces
original_save_data = DataStorage.save_data
def save_data_unified(self, table_name_or_data, data_or_symbol=None, timeframe=None):
    """Método unificado que maneja ambas interfaces de save_data"""
    if isinstance(table_name_or_data, pd.DataFrame) and data_or_symbol and timeframe:
        # Nueva interfaz: save_data(dataframe, symbol, timeframe)
        return save_data_method(self, table_name_or_data, data_or_symbol, timeframe)
    else:
        # Interfaz original: save_data(table_name, dataframe)
        return original_save_data(self, table_name_or_data, data_or_symbol)

DataStorage.save_data = save_data_unified

# Alias para compatibilidad con código centralizado
StorageManager = DataStorage

async def ensure_data_availability(symbol: str, timeframe: str = '4h', 
                                 start_date: str = None, end_date: str = None,
                                 config: dict = None) -> pd.DataFrame:
    """
    Función centralizada para asegurar disponibilidad de datos históricos.
    
    FLUJO CENTRALIZADO:
    1. Verificar SQLite (prioridad #1)
    2. Si no existe en SQLite, verificar CSV (fallback)
    3. Si no existe en ninguno, descargar automáticamente
    4. Retornar datos disponibles
    
    Args:
        symbol: Símbolo a verificar (ej: 'BTC/USDT', 'TSLA/US')
        timeframe: Timeframe deseado (ej: '4h', '1d')
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        config: Configuración del sistema
        
    Returns:
        DataFrame con datos históricos
    """
    logger.info(f"🔍 Verificando disponibilidad de datos para {symbol} en {timeframe}")
    
    # Cargar configuración si no se proporciona
    if config is None:
        try:
            from config.config_loader import load_config_from_yaml
            config = load_config_from_yaml()
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            raise
    
    # Determinar fechas si no se especifican
    if start_date is None or end_date is None:
        # Usar fechas por defecto del config o valores razonables
        try:
            if hasattr(config, 'backtesting'):
                if start_date is None:
                    start_date = getattr(config.backtesting, 'start_date', '2019-01-01')
                if end_date is None:
                    end_date = getattr(config.backtesting, 'end_date', pd.Timestamp.now().strftime('%Y-%m-%d'))
            else:
                if start_date is None:
                    start_date = '2019-01-01'
                if end_date is None:
                    end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Error obteniendo fechas de config, usando valores por defecto: {e}")
            if start_date is None:
                start_date = '2019-01-01'
            if end_date is None:
                end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # 1. PRIMERO: Verificar SQLite (prioridad máxima)
    storage = DataStorage()
    table_name = f"{symbol.replace('/', '_').replace(' ', '_')}_{timeframe}"
    
    try:
        sqlite_data = storage.get_data_without_validation(symbol, timeframe, start_date, end_date)
        if sqlite_data is not None and not sqlite_data.empty:
            # Verificar que los datos cubren el período solicitado
            if _data_covers_period(sqlite_data, start_date, end_date):
                logger.info(f"✅ Datos encontrados en SQLite para {symbol}: {len(sqlite_data)} filas")
                return sqlite_data
            else:
                logger.warning(f"⚠️ Datos en SQLite incompletos para {symbol}, descargando datos adicionales")
    except Exception as e:
        logger.warning(f"Error verificando SQLite para {symbol}: {e}")
    
    # 2. SEGUNDO: Verificar CSV (fallback)
    try:
        csv_data = _load_csv_data(symbol, timeframe)
        if csv_data is not None and not csv_data.empty:
            # Verificar que los datos cubren el período solicitado
            if _data_covers_period(csv_data, start_date, end_date):
                logger.info(f"✅ Datos encontrados en CSV para {symbol}: {len(csv_data)} filas")
                # Guardar en SQLite para futuras consultas
                try:
                    storage.save_data(csv_data, symbol, timeframe)
                    logger.info(f"💾 Datos CSV guardados en SQLite para {symbol}")
                except Exception as e:
                    logger.warning(f"No se pudo guardar CSV en SQLite: {e}")
                return csv_data
            else:
                logger.warning(f"⚠️ Datos en CSV incompletos para {symbol}, descargando datos adicionales")
    except Exception as e:
        logger.warning(f"Error verificando CSV para {symbol}: {e}")
    
    # 3. TERCERO: Descargar automáticamente si no existen datos
    logger.info(f"🔄 Descargando datos automáticamente para {symbol} ({start_date} → {end_date})")
    
    try:
        downloaded_data = await _download_symbol_data(symbol, timeframe, start_date, end_date, config)
        if downloaded_data is not None and not downloaded_data.empty:
            logger.info(f"✅ Datos descargados exitosamente para {symbol}: {len(downloaded_data)} filas")
            return downloaded_data
        else:
            raise Exception(f"No se pudieron descargar datos para {symbol}")
    except Exception as e:
        logger.error(f"❌ Error descargando datos para {symbol}: {e}")
        raise Exception(f"No se pudieron obtener datos para {symbol}: {e}")

def _data_covers_period(data: pd.DataFrame, start_date: str, end_date: str) -> bool:
    """Verifica si los datos cubren el período solicitado con tolerancia de mercado cerrado."""
    try:
        if data.empty or 'timestamp' not in data.columns:
            return False

        requested_start = pd.Timestamp(start_date).normalize()
        requested_end = pd.Timestamp(end_date).normalize()
        data_start = pd.to_datetime(data['timestamp'].min()).normalize()
        data_end = pd.to_datetime(data['timestamp'].max()).normalize()

        tolerance = pd.Timedelta(days=3)
        return data_start <= (requested_start + tolerance) and data_end >= (requested_end - tolerance)
    except Exception:
        return False

def _load_csv_data(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """Carga datos desde archivo CSV"""
    try:
        import os
        from pathlib import Path
        
        # Normalizar nombre de símbolo: reemplazar espacios por guiones bajos
        csv_filename = f"{symbol.replace('/', '_').replace(' ', '_')}_{timeframe}.csv"
        csv_path = Path(__file__).parent.parent / 'data' / 'csv' / csv_filename
        
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
        
        return None
    except Exception as e:
        logger.warning(f"Error cargando CSV para {symbol}: {e}")
        return None

async def _download_symbol_data(symbol: str, timeframe: str, start_date: str, 
                              end_date: str, config: dict) -> Optional[pd.DataFrame]:
    """Descarga datos para un símbolo específico"""
    try:
        from core.downloader import AdvancedDataDownloader
        
        downloader = AdvancedDataDownloader(config)
        # Inicializar el downloader (necesario para configurar exchanges)
        await downloader.initialize()
        
        # Determinar el tipo de descarga basado en el símbolo
        if symbol in ['SOL/USDT', 'ETH/USDT', 'BTC/USDT', 'ADA/USD', 'DOT/USD', 
                     'MATIC/USD', 'XRP/USDT', 'LTC/USD', 'DOGE/USDT']:
            # Descarga CCXT para criptomonedas
            downloaded_data = await downloader.download_multiple_symbols([symbol], timeframe, start_date, end_date)
            data = downloaded_data.get(symbol) if downloaded_data else None
        else:
            # Descarga MT5 para acciones y forex
            downloaded_data = await downloader.download_multiple_symbols([symbol], timeframe, start_date, end_date)
            data = downloaded_data.get(symbol) if downloaded_data else None
        
        if data is not None and not data.empty:
            # Guardar automáticamente en SQLite
            storage = DataStorage()
            storage.save_data(data, symbol, timeframe)
            logger.info(f"💾 Datos descargados guardados en SQLite para {symbol}")
            
            return data
        
        return None
    except Exception as e:
        logger.error(f"Error en descarga automática para {symbol}: {e}")
        return None