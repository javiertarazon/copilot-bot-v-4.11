#!/usr/bin/env python3
"""
Test para validar que los parámetros BASE dan el PNL esperado (~$400k)
Confirma que la configuración base + estructura de símbolos está funcionando correctamente
"""
import asyncio
import sys
from pathlib import Path

# Agregar ruta para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_base_parameters_backtest():
    """
    Ejecuta backtest con parámetros BASE y valida PNL
    """
    from config.config_loader import load_config_from_yaml, get_strategy_parameters
    from strategies.ultra_detailed_heikin_ashi_ml_strategy import UltraDetailedHeikinAshiMLStrategy
    from utils.backtest_validator import BacktestValidator
    
    print("\n" + "="*80)
    print("🧪 TEST: Validar parámetros BASE dan PNL esperado (~$400k)")
    print("="*80)
    
    # Cargar configuración
    config = load_config_from_yaml()
    print(f"\n✅ Configuración cargada")
    
    # Obtener símbolo
    symbol = config.backtesting.symbols[0] if config.backtesting.symbols else "Volatility 75 Index"
    print(f"📊 Símbolo: {symbol}")
    
    # Obtener parámetros (debería usar BASE)
    params = get_strategy_parameters(config, symbol)
    print(f"📋 Parámetros cargados:")
    print(f"   • ml_threshold: {params.get('ml_threshold')}")
    print(f"   • cci_threshold: {params.get('cci_threshold')}")
    print(f"   • atr_period: {params.get('atr_period')}")
    print(f"   • kelly_fraction: {params.get('kelly_fraction')}")
    
    # Instanciar estrategia
    try:
        strategy = UltraDetailedHeikinAshiMLStrategy(config=config)
        print(f"\n✅ Estrategia instanciada exitosamente")
        print(f"   • Symbol: {strategy.symbol}")
        print(f"   • ML Threshold: {strategy.ml_threshold}")
        print(f"   • Stoch OB: {strategy.stoch_overbought}, OS: {strategy.stoch_oversold}")
    except Exception as e:
        print(f"❌ Error instanciando estrategia: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Ejecutar backtest
    try:
        print(f"\n🚀 Ejecutando backtest...")
        validator = BacktestValidator(config)
        results = validator.run_backtest()
        
        if results:
            pnl = results.get('total_pnl', 0)
            trades = results.get('total_trades', 0)
            win_rate = results.get('win_rate', 0)
            
            print(f"\n📈 Resultados del backtest:")
            print(f"   • P&L Total: ${pnl:,.2f}")
            print(f"   • Total Trades: {trades}")
            print(f"   • Win Rate: {win_rate*100:.2f}%")
            
            # Validar que el PNL es razonable (esperamos alrededor de $400k)
            if pnl > 200000:  # Al menos $200k como referencia mínima
                print(f"\n✅ ¡Parámetros BASE validados! PNL es significativo: ${pnl:,.2f}")
                return True
            else:
                print(f"\n⚠️ PNL es menor a lo esperado: ${pnl:,.2f} (esperado > $200k)")
                return False
        else:
            print(f"❌ No se obtuvieron resultados del backtest")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando backtest: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_base_parameters_backtest())
    sys.exit(0 if result else 1)
