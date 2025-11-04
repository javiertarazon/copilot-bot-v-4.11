#!/usr/bin/env python3
"""
Utilidad para cálculo de Stop Loss y Take Profit válidos según restricciones del broker.

Resuelve el problema de error MT5 10016 (Invalid stops) asegurando que SL/TP
cumplan con la distancia mínima requerida por el broker.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

# Agregar repo al path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: MetaTrader5 no instalado")
    sys.exit(1)


@dataclass
class BrokerConstraints:
    """Restricciones de broker para órdenes."""
    symbol: str
    point: float
    min_stop_distance_points: int
    min_distance_value: float
    digits: int
    
    def __str__(self):
        return (f"BrokerConstraints({self.symbol})\n"
                f"  Point: {self.point}\n"
                f"  Min Stop Distance: {self.min_stop_distance_points} puntos ({self.min_distance_value:.5f})\n"
                f"  Digits: {self.digits}")


class StopLossTakeProfitCalculator:
    """Calcula SL/TP válidos según restricciones del broker."""
    
    @staticmethod
    def get_broker_constraints(symbol: str) -> Optional[BrokerConstraints]:
        """
        Obtiene las restricciones de broker para un símbolo.
        
        Args:
            symbol: Nombre del símbolo (ej: "Volatility 75 Index")
            
        Returns:
            BrokerConstraints con los parámetros del broker, o None si falla
        """
        symbol_info = mt5.symbol_info(symbol)
        
        if symbol_info is None:
            print(f"ERROR: No se pudo obtener información de {symbol}")
            return None
        
        # Distancia mínima en puntos (trade_stops_distance está en puntos)
        min_stop_distance_points = symbol_info.trade_stops_distance
        
        # Convertir puntos a valor de precio
        min_distance_value = min_stop_distance_points * symbol_info.point
        
        constraints = BrokerConstraints(
            symbol=symbol,
            point=symbol_info.point,
            min_stop_distance_points=min_stop_distance_points,
            min_distance_value=min_distance_value,
            digits=symbol_info.digits
        )
        
        return constraints
    
    @staticmethod
    def validate_stop_distance(price_open: float, sl: float, tp: float, 
                              constraints: BrokerConstraints) -> Tuple[bool, str]:
        """
        Valida que SL y TP cumplan con la distancia mínima del broker.
        
        Args:
            price_open: Precio de apertura
            sl: Stop Loss propuesto
            tp: Take Profit propuesto
            constraints: Restricciones del broker
            
        Returns:
            Tupla (es_válido, mensaje)
        """
        errors = []
        
        # Validar SL
        if sl != 0.0:  # 0.0 significa SL no establecido
            sl_distance = abs(price_open - sl)
            if sl_distance < constraints.min_distance_value:
                errors.append(
                    f"SL distancia insuficiente: {sl_distance:.5f} < {constraints.min_distance_value:.5f} "
                    f"({int(sl_distance / constraints.point)} < {constraints.min_stop_distance_points} puntos)"
                )
        
        # Validar TP
        if tp != 0.0:  # 0.0 significa TP no establecido
            tp_distance = abs(price_open - tp)
            if tp_distance < constraints.min_distance_value:
                errors.append(
                    f"TP distancia insuficiente: {tp_distance:.5f} < {constraints.min_distance_value:.5f} "
                    f"({int(tp_distance / constraints.point)} < {constraints.min_stop_distance_points} puntos)"
                )
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "OK"
    
    @staticmethod
    def calculate_valid_sl_tp(price_open: float, position_type: int, 
                             desired_sl_points: int, desired_tp_points: int,
                             constraints: BrokerConstraints) -> Tuple[float, float, bool, str]:
        """
        Calcula SL/TP válidos asegurando que cumplen con distancia mínima del broker.
        
        Ajusta automáticamente si es necesario para cumplir con restricciones.
        
        Args:
            price_open: Precio de apertura
            position_type: mt5.ORDER_TYPE_BUY o mt5.ORDER_TYPE_SELL
            desired_sl_points: SL deseado en puntos
            desired_tp_points: TP deseado en puntos
            constraints: Restricciones del broker
            
        Returns:
            Tupla (sl_ajustado, tp_ajustado, cumple_restricciones, mensaje)
        """
        is_buy = position_type == mt5.ORDER_TYPE_BUY
        point = constraints.point
        
        # Calcular SL/TP propuestos
        if is_buy:
            # Para BUY: SL debajo, TP arriba
            proposed_sl = price_open - (desired_sl_points * point)
            proposed_tp = price_open + (desired_tp_points * point)
        else:
            # Para SELL: SL arriba, TP debajo
            proposed_sl = price_open + (desired_sl_points * point)
            proposed_tp = price_open - (desired_tp_points * point)
        
        # Validar y ajustar SL si es necesario
        adjusted_sl = proposed_sl
        min_sl_distance_points = constraints.min_stop_distance_points
        
        actual_sl_distance = abs(price_open - adjusted_sl)
        actual_sl_points = int(actual_sl_distance / point)
        
        if actual_sl_points < min_sl_distance_points:
            # Ajustar SL para cumplir con distancia mínima
            if is_buy:
                adjusted_sl = price_open - (min_sl_distance_points * point)
            else:
                adjusted_sl = price_open + (min_sl_distance_points * point)
        
        # Validar y ajustar TP si es necesario
        adjusted_tp = proposed_tp
        
        actual_tp_distance = abs(price_open - adjusted_tp)
        actual_tp_points = int(actual_tp_distance / point)
        
        if actual_tp_points < min_sl_distance_points:
            # Ajustar TP para cumplir con distancia mínima
            if is_buy:
                adjusted_tp = price_open + (min_sl_distance_points * point)
            else:
                adjusted_tp = price_open - (min_sl_distance_points * point)
        
        # Redondear según dígitos del símbolo
        adjusted_sl = round(adjusted_sl, constraints.digits)
        adjusted_tp = round(adjusted_tp, constraints.digits)
        
        # Validar resultado final
        is_valid, validation_msg = StopLossTakeProfitCalculator.validate_stop_distance(
            price_open, adjusted_sl, adjusted_tp, constraints
        )
        
        details = []
        if actual_sl_points < min_sl_distance_points:
            details.append(f"SL ajustado: {desired_sl_points}pt → {int(abs(price_open - adjusted_sl) / point)}pt")
        if actual_tp_points < min_sl_distance_points:
            details.append(f"TP ajustado: {desired_tp_points}pt → {int(abs(price_open - adjusted_tp) / point)}pt")
        
        msg = "; ".join(details) if details else "Sin ajustes (dentro de límites)"
        
        return adjusted_sl, adjusted_tp, is_valid, msg


def main():
    """Ejemplo de uso."""
    print("\n" + "="*80)
    print("🧪 PRUEBA: Calculadora de SL/TP válidos")
    print("="*80)
    
    # Inicializar MT5
    if not mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe"):
        print("ERROR: No se pudo inicializar MT5")
        return
    
    # Obtener restricciones del broker
    symbol = "Volatility 75 Index"
    print(f"\n📊 Obteniendo restricciones de broker para {symbol}...")
    
    constraints = StopLossTakeProfitCalculator.get_broker_constraints(symbol)
    if constraints is None:
        print("ERROR: No se pudo obtener restricciones")
        mt5.shutdown()
        return
    
    print(f"✅ {constraints}")
    
    # Ejemplo: Calcular SL/TP para una orden BUY
    print(f"\n📌 Escenario: Orden BUY en 50,000")
    price_open = 50000.0
    position_type = mt5.ORDER_TYPE_BUY
    desired_sl_points = 1000  # 10 en precio real
    desired_tp_points = 2000  # 20 en precio real
    
    adjusted_sl, adjusted_tp, is_valid, msg = StopLossTakeProfitCalculator.calculate_valid_sl_tp(
        price_open, position_type, desired_sl_points, desired_tp_points, constraints
    )
    
    print(f"  Precio apertura: {price_open:.2f}")
    print(f"  SL deseado: {desired_sl_points} puntos")
    print(f"  TP deseado: {desired_tp_points} puntos")
    print(f"\n  ✅ SL ajustado: {adjusted_sl:.5f} ({int(abs(price_open - adjusted_sl) / constraints.point)} puntos)")
    print(f"  ✅ TP ajustado: {adjusted_tp:.5f} ({int(abs(price_open - adjusted_tp) / constraints.point)} puntos)")
    print(f"  ✅ Válido: {is_valid}")
    print(f"  📝 Notas: {msg}")
    
    mt5.shutdown()
    print("\n✅ Prueba completada")


if __name__ == '__main__':
    main()
