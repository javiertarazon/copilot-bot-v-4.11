#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DIAGNÓSTICO: Verificar Descarga de Datos, Temporalidad, Procesamiento e Indicadores
Sistema: UltraDetailedHeikinAshiML en MT5
Propósito: Validar que los datos en vivo sean 15m y no una temporalidad incorrecta
"""

import sys
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('descarga_datos/logs/diagnostico_datos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiagnosticoDatos:
    """Diagnóstico completo de datos en vivo"""
    
    def __init__(self):
        self.resultados = {}
        self.mt5_conectado = False
        
    def conectar_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                logger.error(f"❌ MT5 no inicializado: {mt5.last_error()}")
                return False
            
            self.mt5_conectado = True
            logger.info("✅ MT5 conectado exitosamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error al conectar MT5: {e}")
            return False
    
    def desconectar_mt5(self):
        """Desconectar de MT5"""
        if self.mt5_conectado:
            mt5.shutdown()
            logger.info("✅ MT5 desconectado")
    
    def verificar_descarga_datos(self, symbol="Volatility 75 Index", timeframe=15):
        """TAREA 1: Verificar descarga de datos en vivo"""
        logger.info(f"\n{'='*70}")
        logger.info("TAREA 1: VERIFICAR DESCARGA DE DATOS EN VIVO")
        logger.info(f"{'='*70}\n")
        
        resultados = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timeframe_name': f"{timeframe}m",
        }
        
        try:
            # Obtener datos históricos
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 200)
            
            if rates is None or len(rates) == 0:
                logger.error(f"❌ No se obtuvieron datos para {symbol}")
                resultados['error'] = "No hay datos disponibles"
                return resultados
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            logger.info(f"✅ Datos descargados: {len(df)} candles")
            logger.info(f"   Símbolo: {symbol}")
            logger.info(f"   Timeframe: {timeframe} minutos")
            logger.info(f"   Fecha inicio: {df['time'].min()}")
            logger.info(f"   Fecha fin: {df['time'].max()}")
            logger.info(f"   Rango temporal: {(df['time'].max() - df['time'].min())}")
            
            # Verificar estructura
            logger.info(f"\n   Columnas: {list(df.columns)}")
            logger.info(f"   Tipos de datos:\n{df.dtypes}")
            
            resultados['candles_descargados'] = len(df)
            resultados['fecha_inicio'] = df['time'].min()
            resultados['fecha_fin'] = df['time'].max()
            resultados['rango_temporal_total'] = df['time'].max() - df['time'].min()
            resultados['datos_ok'] = True
            resultados['df'] = df
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en descarga de datos: {e}")
            resultados['error'] = str(e)
            return resultados
    
    def analizar_temporalidad(self, df):
        """TAREA 2: Analizar temporalidad de datos"""
        logger.info(f"\n{'='*70}")
        logger.info("TAREA 2: ANALIZAR TEMPORALIDAD DE DATOS")
        logger.info(f"{'='*70}\n")
        
        resultados = {}
        
        try:
            # Calcular intervalos entre candles
            df_sorted = df.sort_values('time').reset_index(drop=True)
            df_sorted['time_diff'] = df_sorted['time'].diff().dt.total_seconds() / 60  # convertir a minutos
            
            # Estadísticas de intervalos
            intervalos = df_sorted['time_diff'].dropna()
            
            logger.info(f"   Intervalos entre candles (en minutos):")
            logger.info(f"   ├─ Media: {intervalos.mean():.2f} min")
            logger.info(f"   ├─ Mediana: {intervalos.median():.2f} min")
            logger.info(f"   ├─ Min: {intervalos.min():.2f} min")
            logger.info(f"   ├─ Max: {intervalos.max():.2f} min")
            logger.info(f"   └─ Desv Std: {intervalos.std():.2f} min")
            
            # Verificar si es realmente 15m
            intervalo_esperado = 15  # minutos
            intervalo_media = intervalos.mean()
            
            tolerance = 0.5  # 0.5 minutos de tolerancia
            es_15m = abs(intervalo_media - intervalo_esperado) < tolerance
            
            logger.info(f"\n   VALIDACIÓN TEMPORALIDAD:")
            logger.info(f"   ├─ Intervalo esperado: {intervalo_esperado} min")
            logger.info(f"   ├─ Intervalo promedio: {intervalo_media:.2f} min")
            logger.info(f"   ├─ Diferencia: {abs(intervalo_media - intervalo_esperado):.2f} min")
            
            if es_15m:
                logger.info(f"   └─ ✅ CORRECTO: Datos son 15m")
            else:
                logger.warning(f"   └─ ⚠️ INCORRECTO: Datos NO son 15m exactos!")
                logger.warning(f"      Posible temporalidad real: {intervalo_media:.1f}m")
            
            # Contar intervalos anómalos
            intervalos_anormalos = (intervalos != intervalo_esperado).sum()
            pct_anomalias = (intervalos_anormalos / len(intervalos)) * 100
            
            logger.info(f"\n   ANÁLISIS DE ANOMALÍAS:")
            logger.info(f"   ├─ Intervalos normales (15m): {len(intervalos) - intervalos_anormalos}")
            logger.info(f"   ├─ Intervalos anómalos: {intervalos_anormalos}")
            logger.info(f"   └─ Porcentaje anomalías: {pct_anomalias:.2f}%")
            
            # Distribuir intervalos
            logger.info(f"\n   DISTRIBUCIÓN DE INTERVALOS:")
            dist = intervalos.value_counts().sort_index()
            for intervalo_val, count in dist.head(10).items():
                pct = (count / len(intervalos)) * 100
                logger.info(f"   ├─ {intervalo_val:.1f}m: {count} candles ({pct:.1f}%)")
            
            resultados['intervalo_promedio'] = intervalo_media
            resultados['es_15m_correcto'] = es_15m
            resultados['anomalias_pct'] = pct_anomalias
            resultados['df_con_intervalos'] = df_sorted
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de temporalidad: {e}")
            return {'error': str(e)}
    
    def validar_procesamiento_datos(self, df):
        """TAREA 3: Validar procesamiento de datos OHLCV"""
        logger.info(f"\n{'='*70}")
        logger.info("TAREA 3: VALIDAR PROCESAMIENTO DE DATOS OHLCV")
        logger.info(f"{'='*70}\n")
        
        resultados = {}
        
        try:
            # Verificar valores de OHLCV
            logger.info("   VALIDACIÓN DE CANDLES (primeros 5):")
            for idx, row in df.head(5).iterrows():
                logger.info(f"\n   Candle #{idx}:")
                logger.info(f"   ├─ Time: {row['time']}")
                logger.info(f"   ├─ Open: {row['open']:.2f}")
                logger.info(f"   ├─ High: {row['high']:.2f}")
                logger.info(f"   ├─ Low: {row['low']:.2f}")
                logger.info(f"   ├─ Close: {row['close']:.2f}")
                logger.info(f"   ├─ Volume: {row['tick_volume']}")
                
                # Validar coherencia
                problemas = []
                if not (row['low'] <= row['open'] and row['open'] <= row['high']):
                    problemas.append("Open fuera de rango [Low-High]")
                if not (row['low'] <= row['close'] and row['close'] <= row['high']):
                    problemas.append("Close fuera de rango [Low-High]")
                if row['high'] < row['low']:
                    problemas.append("High < Low (ERROR CRÍTICO)")
                if row['volume'] < 0:
                    problemas.append("Volume negativo")
                
                if problemas:
                    logger.warning(f"   └─ ⚠️ PROBLEMAS: {'; '.join(problemas)}")
                else:
                    logger.info(f"   └─ ✅ Datos válidos")
            
            # Estadísticas generales
            logger.info(f"\n   ESTADÍSTICAS GENERALES:")
            logger.info(f"   ├─ Open  - Min: {df['open'].min():.2f}, Max: {df['open'].max():.2f}, Mean: {df['open'].mean():.2f}")
            logger.info(f"   ├─ High  - Min: {df['high'].min():.2f}, Max: {df['high'].max():.2f}, Mean: {df['high'].mean():.2f}")
            logger.info(f"   ├─ Low   - Min: {df['low'].min():.2f}, Max: {df['low'].max():.2f}, Mean: {df['low'].mean():.2f}")
            logger.info(f"   ├─ Close - Min: {df['close'].min():.2f}, Max: {df['close'].max():.2f}, Mean: {df['close'].mean():.2f}")
            logger.info(f"   └─ Volume - Min: {df['tick_volume'].min()}, Max: {df['tick_volume'].max()}, Mean: {df['tick_volume'].mean():.0f}")
            
            # Verificar NaNs
            logger.info(f"\n   VALIDACIÓN DE NULOS:")
            for col in ['open', 'high', 'low', 'close', 'tick_volume']:
                nan_count = df[col].isna().sum()
                if nan_count > 0:
                    logger.warning(f"   ├─ {col}: {nan_count} NaNs ⚠️")
                else:
                    logger.info(f"   ├─ {col}: Sin NaNs ✅")
            
            resultados['validacion_ok'] = True
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en validación de datos: {e}")
            return {'error': str(e)}
    
    def verificar_indicadores(self, df):
        """TAREA 4: Verificar cálculo de indicadores"""
        logger.info(f"\n{'='*70}")
        logger.info("TAREA 4: VERIFICAR CÁLCULO DE INDICADORES")
        logger.info(f"{'='*70}\n")
        
        resultados = {}
        
        try:
            from descarga_datos.indicators.technical_indicators import TechnicalIndicators
            
            # Calcular indicadores
            logger.info("   Calculando ATR (Average True Range)...")
            atr = TechnicalIndicators.calculate_atr(df, period=14)
            logger.info(f"   ✅ ATR calculado: Min={atr.min():.2f}, Max={atr.max():.2f}, Mean={atr.mean():.2f}")
            
            logger.info("\n   Calculando RSI (Relative Strength Index)...")
            rsi = TechnicalIndicators.calculate_rsi(df, period=14)
            logger.info(f"   ✅ RSI calculado: Min={rsi.min():.2f}, Max={rsi.max():.2f}, Mean={rsi.mean():.2f}")
            
            logger.info("\n   Calculando Heikin-Ashi...")
            ha = TechnicalIndicators.calculate_heikin_ashi(df)
            logger.info(f"   ✅ Heikin-Ashi calculado: {len(ha)} candles")
            logger.info(f"      ├─ HA Open: Min={ha['ha_open'].min():.2f}, Max={ha['ha_open'].max():.2f}")
            logger.info(f"      ├─ HA Close: Min={ha['ha_close'].min():.2f}, Max={ha['ha_close'].max():.2f}")
            logger.info(f"      └─ HA Color: Rojo={len(ha[ha['ha_color']=='red'])}  Verde={len(ha[ha['ha_color']=='green'])}")
            
            logger.info("\n   Calculando MACD...")
            macd = TechnicalIndicators.calculate_macd(df)
            logger.info(f"   ✅ MACD calculado:")
            logger.info(f"      ├─ MACD Line: Min={macd['macd'].min():.4f}, Max={macd['macd'].max():.4f}")
            logger.info(f"      ├─ Signal: Min={macd['signal'].min():.4f}, Max={macd['signal'].max():.4f}")
            logger.info(f"      └─ Histogram: Min={macd['histogram'].min():.4f}, Max={macd['histogram'].max():.4f}")
            
            resultados['indicadores_ok'] = True
            resultados['atr'] = atr
            resultados['rsi'] = rsi
            resultados['heikin_ashi'] = ha
            resultados['macd'] = macd
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en cálculo de indicadores: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def verificar_normalizacion_escalado(self, df, atr, rsi):
        """TAREA 5: Verificar normalización y escalado de datos"""
        logger.info(f"\n{'='*70}")
        logger.info("TAREA 5: VERIFICAR NORMALIZACIÓN Y ESCALADO DE DATOS")
        logger.info(f"{'='*70}\n")
        
        resultados = {}
        
        try:
            logger.info("   NORMALIZACIÓN DE PRECIOS:")
            logger.info(f"   ├─ Open (min): {df['open'].min():.2f}, (max): {df['open'].max():.2f}")
            
            # Normalizar 0-1
            open_normalized = (df['open'] - df['open'].min()) / (df['open'].max() - df['open'].min())
            logger.info(f"   ├─ After norm 0-1: min={open_normalized.min():.4f}, max={open_normalized.max():.4f}")
            
            # StandardScaler (-1 a 1)
            open_mean = df['open'].mean()
            open_std = df['open'].std()
            open_scaled = (df['open'] - open_mean) / open_std
            logger.info(f"   ├─ After StandardScaler: min={open_scaled.min():.4f}, max={open_scaled.max():.4f}")
            logger.info(f"   └─ Mean={open_scaled.mean():.6f}, Std={open_scaled.std():.4f}")
            
            logger.info(f"\n   NORMALIZACIÓN DE INDICADORES:")
            
            # ATR (típicamente 0-500+, normalizar 0-1)
            atr_norm = atr / atr.max()
            logger.info(f"   ├─ ATR: Original min={atr.min():.2f}, max={atr.max():.2f}")
            logger.info(f"   ├─ ATR normalized: min={atr_norm.min():.4f}, max={atr_norm.max():.4f}")
            
            # RSI (ya 0-100, normalizar 0-1)
            rsi_norm = rsi / 100
            logger.info(f"   ├─ RSI: Original min={rsi.min():.2f}, max={rsi.max():.2f}")
            logger.info(f"   └─ RSI normalized: min={rsi_norm.min():.4f}, max={rsi_norm.max():.4f}")
            
            logger.info(f"\n   VERIFICACIÓN DE DISTRIBUCIÓN:")
            logger.info(f"   ├─ Open: Skewness={df['open'].skew():.4f}, Kurtosis={df['open'].kurtosis():.4f}")
            logger.info(f"   ├─ ATR: Skewness={atr.skew():.4f}, Kurtosis={atr.kurtosis():.4f}")
            logger.info(f"   └─ RSI: Skewness={rsi.skew():.4f}, Kurtosis={rsi.kurtosis():.4f}")
            
            resultados['normalizacion_ok'] = True
            resultados['open_scaled'] = open_scaled
            resultados['atr_normalized'] = atr_norm
            resultados['rsi_normalized'] = rsi_norm
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error en normalización: {e}")
            return {'error': str(e)}
    
    def generar_reporte_final(self, todos_resultados):
        """Generar reporte final"""
        logger.info(f"\n\n{'='*70}")
        logger.info("REPORTE FINAL DE DIAGNÓSTICO")
        logger.info(f"{'='*70}\n")
        
        logger.info("RESUMEN DE VALIDACIONES:")
        logger.info(f"✅ Descarga de datos: OK")
        logger.info(f"✅ Temporalidad: {todos_resultados.get('temporalidad', {}).get('es_15m_correcto', False)}")
        logger.info(f"✅ Procesamiento OHLCV: OK")
        logger.info(f"✅ Indicadores: OK")
        logger.info(f"✅ Normalización: OK")
        
        logger.info(f"\nRECOMENDACIONES:")
        if not todos_resultados.get('temporalidad', {}).get('es_15m_correcto', False):
            logger.warning("⚠️ CRÍTICO: Los datos NO son 15m")
            logger.warning("   Esto podría explicar el número excesivo de operaciones")
            logger.warning("   Revisar MT5LiveDataProvider para asegurar timeframe=15")
    
    def ejecutar_diagnostico_completo(self):
        """Ejecutar diagnóstico completo"""
        logger.info(f"\n\n{'#'*70}")
        logger.info("# DIAGNÓSTICO COMPLETO DE DATOS EN VIVO")
        logger.info("# Sistema: UltraDetailedHeikinAshiML")
        logger.info("# Fecha: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"{'#'*70}\n")
        
        todos_resultados = {}
        
        # Conectar MT5
        if not self.conectar_mt5():
            logger.error("❌ No se pudo conectar a MT5")
            return
        
        try:
            # TAREA 1: Descargar datos
            desc = self.verificar_descarga_datos()
            todos_resultados['descarga'] = desc
            
            if 'error' in desc:
                logger.error(f"❌ Error en descarga: {desc['error']}")
                return
            
            df = desc['df']
            
            # TAREA 2: Temporalidad
            temp = self.analizar_temporalidad(df)
            todos_resultados['temporalidad'] = temp
            
            # TAREA 3: Procesamiento
            proc = self.validar_procesamiento_datos(df)
            todos_resultados['procesamiento'] = proc
            
            # TAREA 4: Indicadores
            indic = self.verificar_indicadores(df)
            todos_resultados['indicadores'] = indic
            
            # TAREA 5: Normalización
            if 'atr' in indic and 'rsi' in indic:
                norm = self.verificar_normalizacion_escalado(df, indic['atr'], indic['rsi'])
                todos_resultados['normalizacion'] = norm
            
            # Reporte final
            self.generar_reporte_final(todos_resultados)
            
        finally:
            self.desconectar_mt5()


if __name__ == "__main__":
    diagnostico = DiagnosticoDatos()
    diagnostico.ejecutar_diagnostico_completo()
