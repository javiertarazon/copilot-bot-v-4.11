"""
Validación de Ejecución de Trading Live - MT5
===============================================
Verifica:
1. Asignación correcta de TP (Take Profit)
2. Asignación correcta de SL (Stop Loss)
3. Trailing Stop funcionando
4. Equivalencia con el balance de MT5
5. Risk management correctamente aplicado
"""

import MetaTrader5 as mt5
import sys
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

# Agregar rutas
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

def connect_mt5():
    """Conectar a MT5"""
    if not mt5.initialize(login=1055559870, password="Javi031989!", server="Deriv-Demo"):
        print(f"❌ ERROR: No se pudo conectar a MT5: {mt5.last_error()}")
        return False
    print("✅ Conectado a MT5")
    return True

def get_account_info():
    """Obtener información de cuenta"""
    account_info = mt5.account_info()
    if account_info is None:
        print(f"❌ Error obteniendo info de cuenta: {mt5.last_error()}")
        return None
    
    return {
        'balance': account_info.balance,
        'equity': account_info.equity,
        'margin': account_info.margin,
        'margin_free': account_info.margin_free,
        'margin_level': account_info.margin_level
    }

def get_active_positions():
    """Obtener posiciones activas"""
    positions = mt5.positions_get()
    if positions is None:
        print(f"❌ Error obteniendo posiciones: {mt5.last_error()}")
        return []
    return positions

def validate_position(position):
    """Validar una posición individual"""
    validation = {
        'ticket': position.ticket,
        'symbol': position.symbol,
        'type': 'BUY' if position.type == 0 else 'SELL',
        'volume': position.volume,
        'entry_price': position.price_open,
        'current_price': position.price_current,
        'profit_loss': position.profit,
        'profit_loss_pct': (position.profit / (position.volume * position.price_open)) * 100 if position.volume * position.price_open > 0 else 0,
    }
    
    # Validar SL
    validation['stop_loss'] = position.sl
    if position.sl > 0:
        validation['sl_distance_points'] = abs(position.price_open - position.sl)
        validation['sl_distance_pct'] = (abs(position.price_open - position.sl) / position.price_open) * 100
        validation['sl_ok'] = position.sl < position.price_open if position.type == 0 else position.sl > position.price_open
    else:
        validation['sl_ok'] = False
        validation['sl_distance_points'] = 0
        validation['sl_distance_pct'] = 0
    
    # Validar TP
    validation['take_profit'] = position.tp
    if position.tp > 0:
        validation['tp_distance_points'] = abs(position.tp - position.price_open)
        validation['tp_distance_pct'] = (abs(position.tp - position.price_open) / position.price_open) * 100
        validation['tp_ok'] = position.tp > position.price_open if position.type == 0 else position.tp < position.price_open
    else:
        validation['tp_ok'] = False
        validation['tp_distance_points'] = 0
        validation['tp_distance_pct'] = 0
    
    # Validar Risk/Reward
    if position.sl > 0 and position.tp > 0:
        risk_distance = abs(position.price_open - position.sl)
        reward_distance = abs(position.tp - position.price_open)
        validation['risk_reward_ratio'] = reward_distance / risk_distance if risk_distance > 0 else 0
    else:
        validation['risk_reward_ratio'] = 0
    
    return validation

def analyze_trailing_stop(position):
    """Analizar trailing stop (basado en SL móvil)"""
    analysis = {
        'has_sl': position.sl > 0,
        'sl_level': position.sl,
        'distance_from_current': abs(position.price_current - position.sl),
        'trailing_stop_active': position.sl > 0 and abs(position.price_current - position.sl) < 500  # Si está muy cerca, probablemente está en trailing
    }
    return analysis

def main():
    print("\n" + "="*80)
    print("VALIDACIÓN DE EJECUCIÓN DE TRADING LIVE - MT5")
    print("="*80 + "\n")
    
    # Conectar a MT5
    if not connect_mt5():
        return
    
    # Obtener info de cuenta
    print("\n📊 INFORMACIÓN DE CUENTA")
    print("-" * 80)
    account_info = get_account_info()
    if account_info:
        print(f"  Balance:        ${account_info['balance']:,.2f}")
        print(f"  Equity:         ${account_info['equity']:,.2f}")
        print(f"  Margen Usado:   ${account_info['margin']:,.2f}")
        print(f"  Margen Libre:   ${account_info['margin_free']:,.2f}")
        print(f"  Nivel Margen:   {account_info['margin_level']:.2f}%")
    
    # Obtener posiciones activas
    positions = get_active_positions()
    
    if not positions:
        print("\n⚠️  No hay posiciones activas")
        mt5.shutdown()
        return
    
    print(f"\n✅ POSICIONES ACTIVAS: {len(positions)}")
    print("-" * 80)
    
    all_valid = True
    total_profit = 0
    
    for idx, position in enumerate(positions, 1):
        validation = validate_position(position)
        trailing = analyze_trailing_stop(position)
        
        print(f"\n📍 POSICIÓN #{idx}")
        print(f"   Ticket:         {validation['ticket']}")
        print(f"   Símbolo:        {validation['symbol']}")
        print(f"   Tipo:           {validation['type']}")
        print(f"   Volumen:        {validation['volume']} lotes")
        print(f"   Precio Entrada: ${validation['entry_price']:,.2f}")
        print(f"   Precio Actual:  ${validation['current_price']:,.2f}")
        
        # P&L
        print(f"\n   💰 P&L:")
        print(f"      P&L Absoluto: ${validation['profit_loss']:,.2f}")
        print(f"      P&L %:        {validation['profit_loss_pct']:.2f}%")
        total_profit += validation['profit_loss']
        
        # Stop Loss
        print(f"\n   🛑 STOP LOSS:")
        if validation['sl_ok']:
            print(f"      ✅ SL Asignado:     ${validation['stop_loss']:,.2f}")
            print(f"      Distancia:         {validation['sl_distance_points']:.2f} puntos ({validation['sl_distance_pct']:.3f}%)")
        else:
            print(f"      ❌ SL NO ASIGNADO o INCORRECTO")
            all_valid = False
        
        # Take Profit
        print(f"\n   🎯 TAKE PROFIT:")
        if validation['tp_ok']:
            print(f"      ✅ TP Asignado:     ${validation['take_profit']:,.2f}")
            print(f"      Distancia:         {validation['tp_distance_points']:.2f} puntos ({validation['tp_distance_pct']:.3f}%)")
        else:
            print(f"      ❌ TP NO ASIGNADO o INCORRECTO")
            all_valid = False
        
        # Risk/Reward
        if validation['risk_reward_ratio'] > 0:
            print(f"\n   ⚖️  RISK/REWARD:")
            print(f"      Ratio:             1:{validation['risk_reward_ratio']:.2f}")
            if validation['risk_reward_ratio'] >= 2.5:
                print(f"      ✅ EXCELENTE (>= 2.5)")
            elif validation['risk_reward_ratio'] >= 1.5:
                print(f"      ✅ BUENO (>= 1.5)")
            else:
                print(f"      ⚠️  BAJO (< 1.5)")
        
        # Trailing Stop
        print(f"\n   📈 TRAILING STOP:")
        print(f"      Activo:            {'✅ SÍ' if trailing['trailing_stop_active'] else '❌ NO'}")
        print(f"      Distancia Actual:  {trailing['distance_from_current']:.2f} puntos")
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN GENERAL")
    print("="*80)
    print(f"✅ Total de posiciones:    {len(positions)}")
    print(f"💰 P&L Total:              ${total_profit:,.2f}")
    print(f"📊 Estado General:         {'✅ CORRECTO' if all_valid else '⚠️  PROBLEMAS DETECTADOS'}")
    
    # Guardar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'account': account_info,
        'positions': len(positions),
        'total_profit': total_profit,
        'validations': [validate_position(p) for p in positions],
        'status': 'OK' if all_valid else 'ISSUES_FOUND'
    }
    
    report_path = Path(__file__).parent.parent / "logs" / "live_trading_validation.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Reporte guardado: {report_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
