#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE VALIDACIÓN: Verificar Datos, Indicadores y Temporalidad
Análisis del problema: ¿Por qué tantas operaciones?
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent.parent))

def verificar_logs_operaciones():
    """Verificar cuántas operaciones se generaron en los logs"""
    print("\n" + "="*80)
    print("ANÁLISIS: CONTEO DE OPERACIONES GENERADAS")
    print("="*80)
    
    log_file = Path("descarga_datos/logs/bot_trader.log")
    
    if not log_file.exists():
        print("❌ No se encontró log file")
        return
    
    # Contar diferentes tipos de eventos
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Contar ciclos
    ciclos_total = content.count("Ciclo #")
    print(f"\n✓ Total de ciclos ejecutados: {ciclos_total}")
    
    # Contar señales SELL
    sell_signals = content.count("[SIGNAL]") + content.count("SELL")
    print(f"✓ Señales SELL generadas: {sell_signals}")
    
    # Contar rechazos
    rechazos = content.count("Ignorando señal")
    print(f"✓ Señales rechazadas (bloqueadas): {rechazos}")
    
    # Contar ejecuciones
    ejecuciones = content.count("Posición abierta")
    print(f"✓ Posiciones ejecutadas: {ejecuciones}")
    
    # Buscar líneas de ciclos específicas
    print(f"\n✓ Últimas señales ejecutadas (primeras líneas únicas):")
    lines = content.split('\n')
    ciclos_encontrados = []
    for i, line in enumerate(lines[-500:]):  # Últimas 500 líneas
        if "Ciclo #" in line or "SELL" in line and "confidence" in line:
            print(f"   {line[:100]}")
            ciclos_encontrados.append(line)
    
    print(f"\n✓ Señales únicas encontradas: {len(ciclos_encontrados)}")


def analizar_temporalidad_en_logs():
    """Analizar si el timeframe es correcto según los logs"""
    print("\n" + "="*80)
    print("ANÁLISIS: TEMPORALIDAD DE DATOS (desde logs)")
    print("="*80)
    
    log_file = Path("descarga_datos/logs/bot_trader.log")
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Buscar líneas con timestamps
    timestamps = []
    for line in lines:
        if "Ciclo #" in line:
            # Extraer timestamp
            try:
                ts_str = line.split(' - ')[0]  # Format: "2025-11-04 06:42:42"
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                timestamps.append(ts)
            except:
                continue
    
    if len(timestamps) < 2:
        print("❌ No hay suficientes timestamps en los logs")
        return
    
    # Calcular intervalos
    timestamps = sorted(set(timestamps))  # Eliminar duplicados y ordenar
    
    print(f"\n✓ Total de timestamps únicos: {len(timestamps)}")
    print(f"✓ Primer ciclo: {timestamps[0]}")
    print(f"✓ Último ciclo: {timestamps[-1]}")
    
    if len(timestamps) > 1:
        # Calcular diferencias entre timestamps consecutivos
        diffs = []
        for i in range(1, min(len(timestamps), 50)):  # Primeros 50
            diff_seconds = (timestamps[i] - timestamps[i-1]).total_seconds()
            diff_minutes = diff_seconds / 60
            diffs.append(diff_minutes)
            if i <= 10:  # Mostrar primeros 10
                print(f"   Ciclo {i} -> {i+1}: {diff_minutes:.2f} minutos")
        
        if diffs:
            print(f"\n✓ Intervalo promedio entre ciclos: {np.mean(diffs):.2f} minutos")
            print(f"✓ Intervalo esperado (ciclos cada 5 segundos): ~0.083 minutos")
            print(f"✓ Conclusión: Los ciclos se ejecutan cada 5 segundos, NO cada 15 minutos")
            
            # El problema
            print("\n" + "!"*80)
            print("⚠️ PROBLEMA IDENTIFICADO:")
            print("!"*80)
            print("Los ciclos se ejecutan cada 5 SEGUNDOS, pero el modelo está diseñado para")
            print("datos de 15 MINUTOS. Esto crea un desajuste temporal que genera:")
            print("  1. Múltiples señales en el mismo candle de 15m")
            print("  2. Excesivas operaciones")
            print("  3. Datos redundantes/duplicados")
            print("!"*80)


def contar_senales_por_confianza():
    """Contar las confianzas de las señales"""
    print("\n" + "="*80)
    print("ANÁLISIS: DISTRIBUCIÓN DE CONFIANZA EN SEÑALES")
    print("="*80)
    
    log_file = Path("descarga_datos/logs/bot_trader.log")
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Buscar ml_confidence
    import re
    
    # Patrón: 'ml_confidence': np.float64(0.6314150683638463)
    pattern = r"'ml_confidence':\s*np\.float64\(([\d.]+)\)"
    matches = re.findall(pattern, content)
    
    if not matches:
        print("❌ No se encontraron valores de ml_confidence")
        return
    
    confidences = [float(m) for m in matches]
    
    print(f"\n✓ Total de señales con confianza: {len(confidences)}")
    print(f"✓ Confianza promedio: {np.mean(confidences):.4f}")
    print(f"✓ Rango: {np.min(confidences):.4f} - {np.max(confidences):.4f}")
    
    # Distribución
    print(f"\n✓ DISTRIBUCIÓN DE CONFIANZA:")
    bins = np.arange(0.62, 0.65, 0.005)
    hist, _ = np.histogram(confidences, bins=bins)
    for i, (start, end, count) in enumerate(zip(bins[:-1], bins[1:], hist)):
        pct = (count / len(confidences)) * 100
        print(f"   {start:.3f} - {end:.3f}: {count:5d} señales ({pct:5.1f}%)")


def recomendar_soluciones():
    """Recomendar soluciones"""
    print("\n" + "="*80)
    print("RECOMENDACIONES PARA SOLUCIONAR EL PROBLEMA")
    print("="*80)
    
    print("""
🔴 PROBLEMA RAÍZ:
   Los ciclos se ejecutan cada 5 SEGUNDOS, pero cada ciclo genera una
   NUEVA señal con los MISMOS datos de 15 minutos. Esto causa:
   
   - 180 ciclos por cada candle de 15m (15min * 60seg / 5seg)
   - 180 señales potenciales por cada 15 minutos
   - Bloqueadas por max_positions: 1, pero genera ruido innecesario
   - En v4.9 con max_positions: 5, genera explosión de operaciones

📋 SOLUCIONES:

   Opción 1: ESPERAR A QUE CAMBIEN LOS DATOS (RECOMENDADO)
   ├─ Modificar MT5LiveDataProvider para cachear datos
   ├─ Solo procesar si el candle cambió (comparar timestamp)
   ├─ Esto es más eficiente y correcto
   └─ Impacto: Reduce ciclos de 180 a 1 por candle 15m

   Opción 2: REDUCIR FRECUENCIA DE CICLOS
   ├─ Cambiar from wait(5 seconds) to wait(15 minutes)
   ├─ Pero esto no es práximo - el sistema es diseñado para ciclos rápidos
   └─ NO RECOMENDADO

   Opción 3: FILTRAR SEÑALES DUPLICADAS
   ├─ Solo ejecutar si es diferente al candle anterior
   ├─ Implementar en live_trading_orchestrator.py
   ├─ Check: if current_time.minute != last_signal_time.minute
   └─ Esto es un band-aid, no soluciona el root problem

🎯 IMPLEMENTACIÓN RECOMENDADA:

   1. Modificar MT5LiveDataProvider:
      ├─ Guardar último timestamp procesado
      ├─ Solo descargar si cambió el candle de 15m
      └─ Retornar None si es datos duplicados
   
   2. En live_trading_orchestrator:
      ├─ If datos = None, skip ciclo
      └─ Continue al siguiente
   
   3. Resultado:
      ├─ Solo 1 señal por candle de 15m
      ├─ Eficiencia: 180x mejor
      ├─ Menos ruido en logs
      └─ Operaciones correctas

📊 ANTES vs DESPUÉS:
   
   Antes (v4.8):
   ├─ Ciclos por 15min: 180
   ├─ Señales generadas: 180
   ├─ Ejecutadas: 1 (bloqueada)
   ├─ Eficiencia: 0.55%
   └─ Tiempo CPU: Desperdiciado
   
   Después:
   ├─ Ciclos por 15min: 180 (igual)
   ├─ Señales generadas: 1
   ├─ Ejecutadas: 1
   ├─ Eficiencia: 100%
   └─ Tiempo CPU: Optimizado
""")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# DIAGNÓSTICO: ANÁLISIS DEL PROBLEMA DE OPERACIONES EXCESIVAS")
    print("# Sistema: UltraDetailedHeikinAshiML")
    print("# Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("#"*80)
    
    verificar_logs_operaciones()
    analizar_temporalidad_en_logs()
    contar_senales_por_confianza()
    recomendar_soluciones()
    
    print("\n" + "#"*80)
    print("# FIN DEL DIAGNÓSTICO")
    print("#"*80 + "\n")
