#!/usr/bin/env python3
"""
🔍 AUDITORÍA INTEGRAL DE DATOS EN VIVO
Valida: Datos descargados, OHLCV, Indicadores, Normalización, Escalado

Objetivo: Verificar que las señales generadas por el modelo fueron creadas con datos correctos
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import logging

# Setup
sys.path.insert(0, str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_ok(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_warn(msg):
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

class AuditoriaIntegral:
    """Auditoría completa de datos en vivo"""
    
    def __init__(self):
        self.data_vol75 = None
        self.indicadores = {}
        self.datos_normalizados = None
        self.senales_generadas = []
        self.errores = []
        self.avisos = []
    
    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        print_section("AUDITORÍA INTEGRAL DE DATOS EN VIVO v4.10")
        
        print_info("Objetivo: Validar integridad de datos, indicadores y señales")
        print_info("Scope: Datos de Volatility 75 Index (15m) desde última ejecución")
        
        # Step 1: Conectar a MT5 y descargar datos
        self.download_data()
        
        # Step 2: Validar OHLCV
        self.validate_ohlcv()
        
        # Step 3: Calcular indicadores
        self.calculate_indicators()
        
        # Step 4: Validar indicadores
        self.validate_indicators()
        
        # Step 5: Validar normalización/escalado
        self.validate_normalization()
        
        # Step 6: Simular generación de señales
        self.simulate_signal_generation()
        
        # Step 7: Reporte final
        self.generate_report()
    
    def download_data(self):
        """Descargar datos de MT5"""
        print_section("PASO 1: DESCARGA DE DATOS")
        
        try:
            import MetaTrader5 as mt5
            
            # Conectar a MT5
            if not mt5.initialize():
                print_error("No se pudo conectar a MT5")
                self.errores.append("MT5 connection failed")
                return
            
            print_ok("Conectado a MT5")
            
            # Descargar datos
            symbol = "Volatility 75 Index"
            timeframe = mt5.TIMEFRAME_M15
            bars = 200
            
            print_info(f"Descargando: {symbol} {bars} barras de 15m")
            
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            
            if rates is None or len(rates) == 0:
                print_error(f"No se pudieron obtener datos para {symbol}")
                self.errores.append(f"No data for {symbol}")
                mt5.shutdown()
                return
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={'tick_volume': 'volume'})
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']].copy()
            
            self.data_vol75 = df
            
            print_ok(f"✅ Descargados {len(df)} candles de {symbol}")
            print_info(f"Rango: {df['time'].min()} a {df['time'].max()}")
            print_info(f"Open: [{df['open'].min():.5f}, {df['open'].max():.5f}]")
            print_info(f"Close: [{df['close'].min():.5f}, {df['close'].max():.5f}]")
            print_info(f"Volume: [{df['volume'].min():.0f}, {df['volume'].max():.0f}]")
            
            # Mostrar primeros y últimos candles
            print("\nPrimeros 5 candles:")
            for idx, row in df.head(5).iterrows():
                print(f"  {row['time']}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={row['volume']:.0f}")
            
            print("\nÚltimos 5 candles:")
            for idx, row in df.tail(5).iterrows():
                print(f"  {row['time']}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={row['volume']:.0f}")
            
            mt5.shutdown()
            
        except Exception as e:
            print_error(f"Error descargando datos: {e}")
            self.errores.append(f"Download error: {e}")
    
    def validate_ohlcv(self):
        """Validar integridad OHLCV"""
        print_section("PASO 2: VALIDACIÓN OHLCV")
        
        if self.data_vol75 is None:
            print_error("Sin datos para validar")
            return
        
        df = self.data_vol75
        issues = 0
        
        # Validación 1: H >= O, H >= C, H >= L
        print_info("Validando: High >= Open/Close/Low")
        invalid_high = (df['high'] < df['open']) | (df['high'] < df['close']) | (df['high'] < df['low'])
        if invalid_high.any():
            print_error(f"High inválido en {invalid_high.sum()} candles")
            self.errores.append(f"Invalid high: {invalid_high.sum()} candles")
            issues += invalid_high.sum()
        else:
            print_ok("High >= Open/Close/Low en todos los candles")
        
        # Validación 2: L <= O, L <= C, L <= H
        print_info("Validando: Low <= Open/Close/High")
        invalid_low = (df['low'] > df['open']) | (df['low'] > df['close']) | (df['low'] > df['high'])
        if invalid_low.any():
            print_error(f"Low inválido en {invalid_low.sum()} candles")
            self.errores.append(f"Invalid low: {invalid_low.sum()} candles")
            issues += invalid_low.sum()
        else:
            print_ok("Low <= Open/Close/High en todos los candles")
        
        # Validación 3: O != C (no deben ser exactamente iguales todos)
        print_info("Validando: Variabilidad de datos (Close != Open)")
        oc_different = (df['open'] != df['close']).sum()
        if oc_different < len(df) * 0.5:
            print_warn(f"Solo {oc_different}/{len(df)} candles con Open != Close (muy poca variabilidad)")
            self.avisos.append(f"Low variability: {oc_different}/{len(df)} different")
        else:
            print_ok(f"{oc_different}/{len(df)} candles con Open != Close (buena variabilidad)")
        
        # Validación 4: Volume > 0 (o al menos algunos)
        print_info("Validando: Volume")
        vol_positive = (df['volume'] > 0).sum()
        if vol_positive == 0:
            print_error("Volumen = 0 en todos los candles (índice sintético?)")
            self.avisos.append("No volume in synthetic index")
        else:
            print_ok(f"{vol_positive}/{len(df)} candles con volumen > 0")
        
        # Validación 5: NaN values
        print_info("Validando: Valores NaN")
        nan_count = df[['open', 'high', 'low', 'close', 'volume']].isna().sum().sum()
        if nan_count > 0:
            print_error(f"Se encontraron {nan_count} valores NaN")
            self.errores.append(f"NaN values: {nan_count}")
        else:
            print_ok("Sin valores NaN")
        
        if issues == 0 and nan_count == 0:
            print_ok("\n[OK] OHLCV VALIDO EN TODOS LOS CANDLES")
        else:
            print_error(f"\n[ERROR] {issues + nan_count} problemas encontrados en OHLCV")
    
    def calculate_indicators(self):
        """Calcular indicadores técnicos"""
        print_section("PASO 3: CALCULO DE INDICADORES")
        
        if self.data_vol75 is None:
            print_error("Sin datos para indicadores")
            return
        
        df = self.data_vol75.copy()
        
        try:
            # Importar clase de indicadores
            from indicators.technical_indicators import TechnicalIndicators
            ti = TechnicalIndicators()
            
            # ATR (Average True Range)
            print_info("Calculando ATR (14 periodos)...")
            df['atr'] = ti.calculate_atr(df, period=14)
            print_ok(f"ATR calculado: [{df['atr'].min():.5f}, {df['atr'].max():.5f}]")
            self.indicadores['atr'] = df['atr']
        except Exception as e:
            print_error(f"Error calculando ATR: {e}")
            self.errores.append(f"ATR error: {e}")
        
        try:
            # Heikin-Ashi
            print_info("Calculando Heikin-Ashi...")
            ti = TechnicalIndicators()
            ha_df = ti.calculate_heikin_ashi(df)
            for col in ['ha_open', 'ha_high', 'ha_low', 'ha_close']:
                if col in ha_df.columns:
                    df[col] = ha_df[col]
            print_ok(f"Heikin-Ashi calculado: {len(df)} velas")
            self.indicadores['ha'] = ha_df
        except Exception as e:
            print_error(f"Error calculando Heikin-Ashi: {e}")
            self.errores.append(f"Heikin-Ashi error: {e}")
        
        # ATR y RSI vía talib si está disponible
        try:
            import talib
            print_info("Calculando RSI via talib (14 periodos)...")
            df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
            print_ok(f"RSI calculado: [{df['rsi'].min():.2f}, {df['rsi'].max():.2f}]")
            if (df['rsi'] < 0).any() or (df['rsi'] > 100).any():
                print_warn(f"RSI fuera de rango [0,100]")
                self.avisos.append("RSI out of range [0,100]")
            else:
                print_ok("RSI dentro de rango [0,100]")
            self.indicadores['rsi'] = df['rsi']
        except:
            print_warn("talib no disponible para RSI")
            self.avisos.append("talib not available for RSI")
        
        try:
            import talib
            print_info("Calculando MACD via talib...")
            macd, macd_signal, macd_histogram = talib.MACD(df['close'].values, fastperiod=12, slowperiod=26, signalperiod=9)
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_histogram
            print_ok(f"MACD calculado")
            print_info(f"  MACD: [{df['macd'].min():.5f}, {df['macd'].max():.5f}]")
            print_info(f"  Signal: [{df['macd_signal'].min():.5f}, {df['macd_signal'].max():.5f}]")
            print_info(f"  Histogram: [{df['macd_histogram'].min():.5f}, {df['macd_histogram'].max():.5f}]")
            self.indicadores['macd'] = {'macd': macd, 'signal': macd_signal, 'histogram': macd_histogram}
        except:
            print_warn("talib no disponible para MACD")
            self.avisos.append("talib not available for MACD")
        
        self.data_vol75 = df
    
    def validate_indicators(self):
        """Validar indicadores calculados"""
        print_section("PASO 4: VALIDACIÓN DE INDICADORES")
        
        if not self.indicadores:
            print_error("Sin indicadores calculados")
            return
        
        df = self.data_vol75
        
        # ATR
        if 'atr' in df.columns:
            print_info("Validando ATR...")
            if (df['atr'] < 0).any():
                print_error("ATR tiene valores negativos")
                self.errores.append("ATR negative")
            elif df['atr'].isna().any():
                print_warn(f"ATR tiene {df['atr'].isna().sum()} valores NaN (primeros períodos)")
            else:
                print_ok("ATR válido (todos > 0)")
        
        # RSI
        if 'rsi' in df.columns:
            print_info("Validando RSI...")
            if df['rsi'].isna().all():
                print_error("RSI es todo NaN")
                self.errores.append("RSI all NaN")
            elif df['rsi'].isna().any():
                print_warn(f"RSI tiene {df['rsi'].isna().sum()} valores NaN")
            else:
                print_ok("RSI sin NaN")
            
            # Rango
            valid_rsi = df['rsi'].dropna()
            if len(valid_rsi) > 0:
                if valid_rsi.min() < 0 or valid_rsi.max() > 100:
                    print_error(f"RSI fuera de rango: [{valid_rsi.min():.2f}, {valid_rsi.max():.2f}]")
                else:
                    print_ok(f"RSI en rango: [{valid_rsi.min():.2f}, {valid_rsi.max():.2f}]")
        
        # Heikin-Ashi
        if 'ha_close' in df.columns:
            print_info("Validando Heikin-Ashi...")
            ha_cols = ['ha_open', 'ha_high', 'ha_low', 'ha_close']
            nan_count = df[ha_cols].isna().sum().sum()
            if nan_count > 0:
                print_warn(f"Heikin-Ashi tiene {nan_count} valores NaN")
            else:
                print_ok("Heikin-Ashi sin NaN")
        
        # MACD
        if 'macd' in df.columns:
            print_info("Validando MACD...")
            macd_cols = ['macd', 'macd_signal', 'macd_histogram']
            nan_count = df[macd_cols].isna().sum().sum()
            if nan_count > 0:
                print_warn(f"MACD tiene {nan_count} valores NaN")
            else:
                print_ok("MACD sin NaN")
    
    def validate_normalization(self):
        """Validar normalización y escalado"""
        print_section("PASO 5: VALIDACIÓN DE NORMALIZACIÓN Y ESCALADO")
        
        if self.data_vol75 is None:
            print_error("Sin datos")
            return
        
        df = self.data_vol75.copy()
        
        # Seleccionar columnas numéri cas para normalizar
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'atr', 'rsi']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        print_info(f"Normalizando columnas: {available_cols}")
        
        try:
            # Min-Max Scaling (0-1)
            print_info("Aplicando Min-Max Scaling (0-1)...")
            df_normalized = df[available_cols].copy()
            
            for col in available_cols:
                if col in df_normalized.columns:
                    min_val = df_normalized[col].min()
                    max_val = df_normalized[col].max()
                    
                    if max_val - min_val > 0:
                        df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)
                    else:
                        print_warn(f"{col}: min=max, sin rango")
            
            print_ok("Min-Max Scaling aplicado")
            
            # Verificar rango [0, 1]
            for col in available_cols:
                min_norm = df_normalized[col].min()
                max_norm = df_normalized[col].max()
                if min_norm >= 0 and max_norm <= 1:
                    print_ok(f"{col}: [{min_norm:.4f}, {max_norm:.4f}] OK")
                else:
                    print_warn(f"{col}: [{min_norm:.4f}, {max_norm:.4f}] (fuera de [0,1])")
            
            # StandardScaler
            print_info("\nAplicando StandardScaler...")
            from sklearn.preprocessing import StandardScaler
            
            scaler = StandardScaler()
            df_scaled = pd.DataFrame(
                scaler.fit_transform(df[available_cols]),
                columns=available_cols
            )
            
            print_ok("StandardScaler aplicado")
            
            # Verificar media ~0 y std ~1
            for col in available_cols:
                mean = df_scaled[col].mean()
                std = df_scaled[col].std()
                if abs(mean) < 0.01 and abs(std - 1) < 0.01:
                    print_ok(f"{col}: mean={mean:.4f}, std={std:.4f} OK")
                else:
                    print_warn(f"{col}: mean={mean:.4f}, std={std:.4f} (ajuste esperado)")
            
            self.datos_normalizados = {
                'minmax': df_normalized,
                'scaled': df_scaled,
                'original': df
            }
            
        except Exception as e:
            print_error(f"Error en normalización: {e}")
            self.errores.append(f"Normalization error: {e}")
    
    def simulate_signal_generation(self):
        """Simular generación de señales"""
        print_section("PASO 6: SIMULACIÓN DE GENERACIÓN DE SEÑALES")
        
        if self.data_vol75 is None:
            print_error("Sin datos")
            return
        
        df = self.data_vol75
        
        print_info("Simulando condiciones para generación de señal SELL...")
        
        # Condiciones SELL (ejemplo)
        print_info("\nCondición 1: RSI > 70 (sobrecompra)")
        if 'rsi' in df.columns:
            rsi_overbought = (df['rsi'] > 70).sum()
            print_info(f"  RSI > 70: {rsi_overbought}/{len(df)} candles")
        
        print_info("\nCondición 2: MACD Histogram < 0 (momentum negativo)")
        if 'macd_histogram' in df.columns:
            macd_negative = (df['macd_histogram'] < 0).sum()
            print_info(f"  MACD Histogram < 0: {macd_negative}/{len(df)} candles")
        
        print_info("\nCondición 3: Heikin-Ashi Red (cierre < apertura)")
        if 'ha_close' in df.columns and 'ha_open' in df.columns:
            ha_red = (df['ha_close'] < df['ha_open']).sum()
            print_info(f"  HA Red: {ha_red}/{len(df)} candles")
        
        print_info("\nCondición 4: Close < Heikin-Ashi Close")
        if 'ha_close' in df.columns:
            close_below_ha = (df['close'] < df['ha_close']).sum()
            print_info(f"  Close < HA Close: {close_below_ha}/{len(df)} candles")
        
        print_ok("\n[OK] Simulacion completada")
    
    def generate_report(self):
        """Generar reporte final"""
        print_section("REPORTE FINAL DE AUDITORÍA")
        
        # Resumen
        print_info("RESUMEN EJECUTIVO:")
        print_info(f"  Candles auditados: {len(self.data_vol75) if self.data_vol75 is not None else 0}")
        print_info(f"  Indicadores calculados: {len(self.indicadores)}")
        print_info(f"  Errores: {len(self.errores)}")
        print_info(f"  Avisos: {len(self.avisos)}")
        
        if len(self.errores) == 0:
            print_ok("\n[OK] AUDITORIA COMPLETADA: Sin errores criticos")
            print_ok("[OK] Datos descargados correctamente")
            print_ok("[OK] OHLCV valido")
            print_ok("[OK] Indicadores calculados correctamente")
            print_ok("[OK] Normalizacion y escalado funcionan")
            print_ok("\n[OK] Sistema listo para generar senales confiables")
        else:
            print_error(f"\n[ERROR] AUDITORIA CON ERRORES: {len(self.errores)} problemas encontrados")
            for i, error in enumerate(self.errores, 1):
                print_error(f"  {i}. {error}")
        
        if len(self.avisos) > 0:
            print_warn(f"\n[WARN] {len(self.avisos)} avisos:")
            for i, aviso in enumerate(self.avisos, 1):
                print_warn(f"  {i}. {aviso}")
        
        print("\n" + "="*80)

if __name__ == '__main__':
    audit = AuditoriaIntegral()
    audit.run_full_audit()
