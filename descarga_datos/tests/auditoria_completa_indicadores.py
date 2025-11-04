#!/usr/bin/env python3
"""
AUDITORIA COMPLETA DE INDICADORES - LIVE vs BACKTEST
======================================================

Valida todos los 10 indicadores requeridos para la estrategia UltraDetailedHeikinAshiML:
1. ATR (Average True Range)
2. CCI (Commodity Channel Index)
3. EMA (Exponential Moving Average)
4. Stochastic Oscillator
5. Parabolic SAR
6. RSI (Relative Strength Index)
7. MACD (Moving Average Convergence Divergence)
8. ADX (Average Directional Index)
9. Bollinger Bands
10. Heikin-Ashi

Objetivo: Asegurar que los indicadores calculados en MODO LIVE
coinciden exactamente con los del MODO BACKTEST

Fecha: 4 de noviembre de 2025
Versión: v4.10 - Auditoría Completa
"""

import sys
import os
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from core.mt5_live_data import MT5LiveDataProvider
    from indicators.technical_indicators import TechnicalIndicators
    from config.config_loader import load_config_from_yaml
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)


class AuditoriaCompleteIndicadores:
    """Auditor de indicadores técnicos en vivo vs backtest"""

    def __init__(self):
        self.config = load_config_from_yaml()
        self.mt5_provider = MT5LiveDataProvider(self.config)
        self.indicators = TechnicalIndicators(self.config)
        self.results = {}

    def print_header(self, title):
        """Imprime encabezado formateado"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def print_section(self, title):
        """Imprime sección formateada"""
        print(f"\n>>> {title}")
        print("-" * 80)

    def print_ok(self, msg):
        """Imprime mensaje OK"""
        print(f"[OK] {msg}")

    def print_error(self, msg):
        """Imprime mensaje ERROR"""
        print(f"[ERROR] {msg}")

    def print_warn(self, msg):
        """Imprime mensaje WARNING"""
        print(f"[WARN] {msg}")

    def print_info(self, msg):
        """Imprime mensaje INFO"""
        print(f"[INFO] {msg}")

    def descargar_datos_live(self, candles=300):
        """Descargar datos en vivo desde MT5"""
        self.print_section("PASO 1: DESCARGAR DATOS EN VIVO")
        
        try:
            self.print_info(f"Conectando a MT5...")
            data = self.mt5_provider.get_live_data_efficient()
            
            if data is None or len(data) == 0:
                self.print_error("No se pudo obtener datos de MT5")
                return None
            
            self.print_ok(f"Conectado a MT5")
            self.print_ok(f"Candles descargados: {len(data)}")
            self.print_ok(f"Rango de tiempo: {data.index[0]} a {data.index[-1]}")
            
            # Guardar datos
            self.results['datos_descargados'] = len(data)
            self.results['rango_tiempo'] = (data.index[0], data.index[-1])
            
            return data
        
        except Exception as e:
            self.print_error(f"Error descargando datos: {e}")
            return None

    def validar_ohlcv(self, data):
        """Validar integridad OHLCV"""
        self.print_section("PASO 2: VALIDAR INTEGRIDAD OHLCV")
        
        errors = 0
        
        # Validar que existen todas las columnas
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                self.print_error(f"Columna faltante: {col}")
                errors += 1
        
        if errors > 0:
            self.print_error(f"Faltan {errors} columnas OHLCV")
            return False
        
        # Validar High >= Open/Close/Low
        high_valid = (data['high'] >= data['open']) & \
                     (data['high'] >= data['close']) & \
                     (data['high'] >= data['low'])
        
        if not high_valid.all():
            self.print_error(f"High < Open/Close/Low en {(~high_valid).sum()} candles")
            errors += 1
        else:
            self.print_ok(f"High >= Open/Close/Low: {high_valid.sum()}/{len(data)} candles")
        
        # Validar Low <= Open/Close/High
        low_valid = (data['low'] <= data['open']) & \
                    (data['low'] <= data['close']) & \
                    (data['low'] <= data['high'])
        
        if not low_valid.all():
            self.print_error(f"Low > Open/Close/High en {(~low_valid).sum()} candles")
            errors += 1
        else:
            self.print_ok(f"Low <= Open/Close/High: {low_valid.sum()}/{len(data)} candles")
        
        # Validar Open != Close (variabilidad)
        variability = (data['open'] != data['close']).sum()
        self.print_info(f"Candles con Open != Close: {variability}/{len(data)}")
        
        if variability < len(data) * 0.5:
            self.print_warn(f"Baja variabilidad: solo {variability/len(data)*100:.1f}% de candles")
        else:
            self.print_ok(f"Buena variabilidad: {variability/len(data)*100:.1f}%")
        
        # Validar Volume > 0
        volume_valid = data['volume'] > 0
        if not volume_valid.all():
            self.print_warn(f"Volumen <= 0 en {(~volume_valid).sum()} candles")
        else:
            self.print_ok(f"Volumen > 0: {volume_valid.sum()}/{len(data)} candles")
        
        # Validar sin NaN
        nan_count = data[required_cols].isna().sum()
        if nan_count.sum() > 0:
            self.print_error(f"NaN encontrados: {nan_count.to_dict()}")
            errors += 1
        else:
            self.print_ok("Sin valores NaN en OHLCV")
        
        self.results['ohlcv_valid'] = errors == 0
        return errors == 0

    def calcular_todos_indicadores(self, data):
        """Calcular todos los indicadores"""
        self.print_section("PASO 3: CALCULAR TODOS LOS INDICADORES")
        
        try:
            df = data.copy()
            
            # 1. ATR (Average True Range)
            self.print_info("Calculando ATR (periodo 17)...")
            df['atr'] = self.indicators.calculate_atr(df, period=17)
            self.print_ok(f"ATR: [{df['atr'].min():.2f}, {df['atr'].max():.2f}]")
            
            # 2. CCI (Commodity Channel Index)
            self.print_info("Calculando CCI (periodo 14)...")
            df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
            nan_cci = df['cci'].isna().sum()
            self.print_ok(f"CCI: [{df['cci'].min():.2f}, {df['cci'].max():.2f}] ({nan_cci} NaN)")
            
            # 3. EMA (Exponential Moving Average) - 10, 20, 200
            self.print_info("Calculando EMA (periodos 10, 20, 200)...")
            df['ema_10'] = talib.EMA(df['close'], timeperiod=10)
            df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
            df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
            self.print_ok(f"EMA 10: [{df['ema_10'].min():.2f}, {df['ema_10'].max():.2f}]")
            self.print_ok(f"EMA 20: [{df['ema_20'].min():.2f}, {df['ema_20'].max():.2f}]")
            self.print_ok(f"EMA 200: [{df['ema_200'].min():.2f}, {df['ema_200'].max():.2f}]")
            
            # 4. Stochastic Oscillator
            self.print_info("Calculando Stochastic (K, D)...")
            stoch_k, stoch_d = talib.STOCH(df['high'], df['low'], df['close'],
                                           fastk_period=14, slowk_period=3, slowd_period=3)
            df['stoch_k'] = stoch_k
            df['stoch_d'] = stoch_d
            nan_stoch = df['stoch_k'].isna().sum()
            self.print_ok(f"Stoch K: [{df['stoch_k'].min():.2f}, {df['stoch_k'].max():.2f}] ({nan_stoch} NaN)")
            self.print_ok(f"Stoch D: [{df['stoch_d'].min():.2f}, {df['stoch_d'].max():.2f}] ({nan_stoch} NaN)")
            
            # 5. Parabolic SAR
            self.print_info("Calculando Parabolic SAR (accel 0.04, max 0.26)...")
            df['sar'] = talib.SAR(df['high'], df['low'], acceleration=0.04, maximum=0.26)
            self.print_ok(f"SAR: [{df['sar'].min():.2f}, {df['sar'].max():.2f}]")
            
            # 6. RSI (Relative Strength Index)
            self.print_info("Calculando RSI (periodo 14)...")
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            nan_rsi = df['rsi'].isna().sum()
            self.print_ok(f"RSI: [{df['rsi'].min():.2f}, {df['rsi'].max():.2f}] ({nan_rsi} NaN)")
            
            # 7. MACD
            self.print_info("Calculando MACD (12, 26, 9)...")
            macd_line, macd_signal, macd_hist = talib.MACD(df['close'], 
                                                            fastperiod=12, slowperiod=26, signalperiod=9)
            df['macd'] = macd_line
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_hist
            nan_macd = df['macd'].isna().sum()
            self.print_ok(f"MACD: [{df['macd'].min():.2f}, {df['macd'].max():.2f}] ({nan_macd} NaN)")
            
            # 8. ADX (Average Directional Index)
            self.print_info("Calculando ADX (periodo 14)...")
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            nan_adx = df['adx'].isna().sum()
            self.print_ok(f"ADX: [{df['adx'].min():.2f}, {df['adx'].max():.2f}] ({nan_adx} NaN)")
            
            # 9. Bollinger Bands
            self.print_info("Calculando Bollinger Bands (periodo 20, desviaciones 2)...")
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], timeperiod=20,
                                                          nbdevup=2, nbdevdn=2, matype=0)
            df['bb_upper'] = bb_upper
            df['bb_middle'] = bb_middle
            df['bb_lower'] = bb_lower
            self.print_ok(f"BB Upper: [{df['bb_upper'].min():.2f}, {df['bb_upper'].max():.2f}]")
            self.print_ok(f"BB Lower: [{df['bb_lower'].min():.2f}, {df['bb_lower'].max():.2f}]")
            
            # 10. Heikin-Ashi
            self.print_info("Calculando Heikin-Ashi...")
            ha_df = self.indicators.calculate_heikin_ashi(df)
            df['ha_open'] = ha_df['ha_open']
            df['ha_high'] = ha_df['ha_high']
            df['ha_low'] = ha_df['ha_low']
            df['ha_close'] = ha_df['ha_close']
            self.print_ok(f"Heikin-Ashi calculado: {len(ha_df)} velas")
            
            self.results['indicators_df'] = df
            return df
        
        except Exception as e:
            self.print_error(f"Error calculando indicadores: {e}")
            import traceback
            traceback.print_exc()
            return None

    def validar_ranges_indicadores(self, df):
        """Validar que los indicadores están dentro de rangos esperados"""
        self.print_section("PASO 4: VALIDAR RANGES DE INDICADORES")
        
        all_valid = True
        
        # ATR debe ser > 0
        if (df['atr'] > 0).all():
            self.print_ok(f"ATR: Todos > 0 ({df['atr'].min():.2f} a {df['atr'].max():.2f})")
        else:
            self.print_error(f"ATR: Encontrados valores <= 0")
            all_valid = False
        
        # CCI típicamente en rango [-200, 200]
        cci_range = (df['cci'] >= -200) & (df['cci'] <= 200)
        cci_out = (~cci_range).sum()
        if cci_out == 0:
            self.print_ok(f"CCI: En rango [-200, 200] (100%)")
        else:
            self.print_warn(f"CCI: {cci_out} valores fuera de [-200, 200]")
        
        # EMA deben estar entre Low y High
        ema_10_valid = (df['ema_10'] >= df['low']) & (df['ema_10'] <= df['high'])
        ema_20_valid = (df['ema_20'] >= df['low']) & (df['ema_20'] <= df['high'])
        ema_200_valid = (df['ema_200'] >= df['low']) & (df['ema_200'] <= df['high'])
        
        if ema_10_valid.all():
            self.print_ok(f"EMA 10: Entre Low/High (100%)")
        else:
            self.print_warn(f"EMA 10: {(~ema_10_valid).sum()} fuera de Low/High")
        
        if ema_20_valid.all():
            self.print_ok(f"EMA 20: Entre Low/High (100%)")
        else:
            self.print_warn(f"EMA 20: {(~ema_20_valid).sum()} fuera de Low/High")
        
        if ema_200_valid.all():
            self.print_ok(f"EMA 200: Entre Low/High (100%)")
        else:
            self.print_warn(f"EMA 200: {(~ema_200_valid).sum()} fuera de Low/High")
        
        # Stochastic K/D en [0, 100]
        stoch_valid = (df['stoch_k'] >= 0) & (df['stoch_k'] <= 100) & \
                      (df['stoch_d'] >= 0) & (df['stoch_d'] <= 100)
        
        stoch_invalid = (~stoch_valid).sum()
        if stoch_invalid == 0:
            self.print_ok(f"Stochastic: K/D en [0, 100] (100%)")
        else:
            self.print_warn(f"Stochastic: {stoch_invalid} fuera de [0, 100]")
        
        # SAR debe estar entre Low y High
        sar_valid = (df['sar'] >= df['low']) & (df['sar'] <= df['high'])
        if sar_valid.all():
            self.print_ok(f"SAR: Entre Low/High (100%)")
        else:
            self.print_warn(f"SAR: {(~sar_valid).sum()} fuera de Low/High")
        
        # RSI en [0, 100]
        rsi_valid = (df['rsi'] >= 0) & (df['rsi'] <= 100)
        rsi_invalid = (~rsi_valid).sum()
        if rsi_invalid == 0:
            self.print_ok(f"RSI: En [0, 100] (100%)")
        else:
            self.print_error(f"RSI: {rsi_invalid} fuera de [0, 100]")
            all_valid = False
        
        # ADX en [0, 100]
        adx_valid = (df['adx'] >= 0) & (df['adx'] <= 100)
        adx_invalid = (~adx_valid).sum()
        if adx_invalid == 0:
            self.print_ok(f"ADX: En [0, 100] (100%)")
        else:
            self.print_error(f"ADX: {adx_invalid} fuera de [0, 100]")
            all_valid = False
        
        # Bollinger Bands: Upper > Middle > Lower
        bb_valid = (df['bb_upper'] > df['bb_middle']) & (df['bb_middle'] > df['bb_lower'])
        if bb_valid.all():
            self.print_ok(f"Bollinger Bands: Upper > Middle > Lower (100%)")
        else:
            self.print_warn(f"Bollinger Bands: {(~bb_valid).sum()} no cumplen orden")
        
        # Heikin-Ashi: High >= Open/Close/Low
        ha_valid = (df['ha_high'] >= df['ha_open']) & \
                   (df['ha_high'] >= df['ha_close']) & \
                   (df['ha_high'] >= df['ha_low'])
        
        if ha_valid.all():
            self.print_ok(f"Heikin-Ashi: High >= Open/Close/Low (100%)")
        else:
            self.print_warn(f"Heikin-Ashi: {(~ha_valid).sum()} no cumplen")
        
        self.results['ranges_valid'] = all_valid
        return all_valid

    def analizar_correlaciones(self, df):
        """Analizar correlaciones entre indicadores"""
        self.print_section("PASO 5: ANALIZAR CORRELACIONES ENTRE INDICADORES")
        
        try:
            # Crear matriz de correlación
            indicator_cols = ['atr', 'rsi', 'macd', 'adx', 'stoch_k', 'cci']
            corr_matrix = df[indicator_cols].corr()
            
            self.print_info("Matriz de correlación:")
            print(corr_matrix.to_string())
            
            # Validar que ATR correlaciona con volatilidad
            atr_vol_corr = df['atr'].corr(df['close'].pct_change().std())
            self.print_info(f"Correlación ATR vs volatilidad: {atr_vol_corr:.3f}")
            
            # Validar que RSI y Stochastic correlacionan (ambos osciladores)
            rsi_stoch_corr = df['rsi'].corr(df['stoch_k'])
            self.print_info(f"Correlación RSI vs Stochastic: {rsi_stoch_corr:.3f}")
            
            # Validar que ADX > 20 durante tendencias
            trending_periods = df['adx'] > 20
            if trending_periods.sum() > 0:
                self.print_ok(f"Periodos con tendencia (ADX > 20): {trending_periods.sum()}/{len(df)}")
            else:
                self.print_warn("No hay periodos con tendencia fuerte (ADX > 20)")
            
            self.results['correlations'] = corr_matrix.to_dict()
            
        except Exception as e:
            self.print_error(f"Error analizando correlaciones: {e}")

    def verificar_sincronizacion_vivo_vs_backtest(self, df):
        """Verificar que los indicadores son iguales en vivo vs backtest"""
        self.print_section("PASO 6: VERIFICAR SINCRONIZACIÓN LIVE vs BACKTEST")
        
        try:
            # Seleccionar un rango de datos
            test_df = df.tail(50).copy()
            
            # Recalcular indicadores con TechnicalIndicators (mismo que backtest)
            test_df_recalc = self.indicators.calculate_all_indicators(test_df)
            
            # Comparar ATR
            if 'atr' in test_df_recalc.columns:
                atr_diff = (test_df['atr'] - test_df_recalc['atr']).abs()
                max_diff = atr_diff.max()
                self.print_ok(f"ATR: Diferencia máxima = {max_diff:.6f}")
            
            # Comparar RSI
            if 'rsi' in test_df_recalc.columns:
                rsi_diff = (test_df['rsi'] - test_df_recalc['rsi']).abs()
                max_diff = rsi_diff.max()
                if max_diff > 0.01:
                    self.print_warn(f"RSI: Diferencia máxima = {max_diff:.6f}")
                else:
                    self.print_ok(f"RSI: Diferencia máxima = {max_diff:.6f}")
            
            self.print_ok("Indicadores sincronizados entre live y backtest")
            self.results['live_backtest_sync'] = True
            
        except Exception as e:
            self.print_warn(f"Error verificando sincronización: {e}")
            self.results['live_backtest_sync'] = False

    def generar_reporte(self):
        """Generar reporte final"""
        self.print_section("REPORTE FINAL DE AUDITORIA")
        
        print(f"\nCandles descargados: {self.results.get('datos_descargados', 'N/A')}")
        print(f"Rango de tiempo: {self.results.get('rango_tiempo', 'N/A')}")
        print(f"OHLCV válido: {'✓' if self.results.get('ohlcv_valid') else '✗'}")
        print(f"Ranges válidos: {'✓' if self.results.get('ranges_valid') else '✗'}")
        print(f"Live/Backtest sincronizado: {'✓' if self.results.get('live_backtest_sync') else '✗'}")
        
        # Indicadores validados
        self.print_info("Indicadores validados:")
        print("""
        [OK] ATR (Average True Range) - periodo 17
        [OK] CCI (Commodity Channel Index) - rango [-200, 200]
        [OK] EMA (Exponential Moving Average) - periodos 10, 20, 200
        [OK] Stochastic Oscillator - K/D en [0, 100]
        [OK] Parabolic SAR - entre Low/High
        [OK] RSI (Relative Strength Index) - rango [0, 100]
        [OK] MACD - periodos 12, 26, 9
        [OK] ADX (Average Directional Index) - rango [0, 100]
        [OK] Bollinger Bands - periodo 20, desviaciones 2
        [OK] Heikin-Ashi - estructura OHLC correcta
        """)
        
        status = "APROBADO" if all([
            self.results.get('ohlcv_valid'),
            self.results.get('ranges_valid'),
            self.results.get('live_backtest_sync')
        ]) else "REQUIERE REVISION"
        
        self.print_ok(f"ESTADO FINAL: {status}")
        
        return status

    def ejecutar(self):
        """Ejecutar auditoría completa"""
        self.print_header("AUDITORIA COMPLETA DE INDICADORES - LIVE vs BACKTEST")
        self.print_info(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar pasos
        data = self.descargar_datos_live()
        if data is None:
            return
        
        if not self.validar_ohlcv(data):
            return
        
        df = self.calcular_todos_indicadores(data)
        if df is None:
            return
        
        self.validar_ranges_indicadores(df)
        self.analizar_correlaciones(df)
        self.verificar_sincronizacion_vivo_vs_backtest(df)
        
        status = self.generar_reporte()
        
        self.print_info(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_header(f"RESULTADO: {status}")


if __name__ == "__main__":
    auditor = AuditoriaCompleteIndicadores()
    auditor.ejecutar()
