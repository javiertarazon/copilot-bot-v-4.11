"""
Dashboard Streamlit Simple y Directo para Backtest v4.7
Visualiza resultados de backtesting con gráficos y tablas
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="📊 Dashboard Bot Trader v4.7",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

@st.cache_data
def load_results():
    """Cargar datos de resultados de backtesting"""
    data_dir = Path(__file__).parent.parent / "data" / "dashboard_results"
    
    if not data_dir.exists():
        return None, None
    
    # Cargar resultados de BTC/USDT
    results_file = data_dir / "BTC_USDT_results.json"
    if not results_file.exists():
        return None, None
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Cargar resumen global
    global_file = data_dir / "global_summary.json"
    global_summary = {}
    if global_file.exists():
        with open(global_file, 'r', encoding='utf-8') as f:
            global_summary = json.load(f)
    
    return results, global_summary


def get_strategy_metrics(results):
    """Extraer métricas de la estrategia"""
    if not results or 'strategies' not in results:
        return None
    
    strategies = results['strategies']
    strategy_name = list(strategies.keys())[0]  # Obtener primera estrategia
    return strategy_name, strategies[strategy_name]


# ============================================================================
# MAIN - RENDERIZAR DASHBOARD
# ============================================================================

def main():
    # Cargar datos
    results, global_summary = load_results()
    
    if results is None:
        st.error("❌ No se encontraron datos de backtesting en descarga_datos/data/dashboard_results/")
        st.info("Por favor, ejecuta un backtest primero: python descarga_datos/main.py --backtest-only")
        return
    
    # Obtener métricas
    strategy_name, metrics = get_strategy_metrics(results)
    
    # ========================================================================
    # TÍTULO Y RESUMEN PRINCIPAL
    # ========================================================================
    st.title("🤖 Dashboard Bot Trader v4.7")
    st.markdown("### 📈 Análisis de Backtesting - 16 Meses (01-06-2024 a 24-10-2025)")
    
    # Resumen en 4 columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 P&L Total",
            f"${metrics['total_pnl']:,.2f}",
            delta=f"+{(metrics['total_pnl']/800)*100:.1f}% ROI"
        )
    
    with col2:
        st.metric(
            "📊 Total Trades",
            f"{metrics['total_trades']:,}",
            delta=f"{metrics['winning_trades']} ganadores"
        )
    
    with col3:
        st.metric(
            "✅ Win Rate",
            f"{metrics['win_rate']*100:.1f}%",
            delta=f"({metrics['winning_trades']}/{metrics['total_trades']})"
        )
    
    with col4:
        st.metric(
            "📉 Max Drawdown",
            f"{metrics['max_drawdown']:.2f}%",
            delta=f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f}"
        )
    
    st.divider()
    
    # ========================================================================
    # SECCIÓN 1: GRÁFICOS DE RENTABILIDAD
    # ========================================================================
    
    st.subheader("1️⃣ Análisis de Rentabilidad")
    
    # Obtener trades
    trades = metrics.get('trades', [])
    
    if trades:
        # Calcular equity curve
        equity = [800.0]  # Capital inicial
        cumulative_pnl = 0
        for trade in trades:
            cumulative_pnl += trade.get('pnl', 0)
            equity.append(800 + cumulative_pnl)
        
        # Gráfico de Equity Curve
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            y=equity,
            mode='lines',
            name='Equity Curve',
            line=dict(color='#2E86AB', width=2),
            fill='tozeroy'
        ))
        
        fig_equity.update_layout(
            title="Curva de Equity (Capital Progresivo)",
            xaxis_title="Trade #",
            yaxis_title="Capital ($)",
            hovermode='x unified',
            height=400,
            template='plotly_dark'
        )
        
        st.plotly_chart(fig_equity, use_container_width=True)
    
    # ========================================================================
    # SECCIÓN 2: DISTRIBUCIÓN DE TRADES
    # ========================================================================
    
    st.subheader("2️⃣ Distribución de Operaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de Win vs Loss
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Ganadores', 'Perdedores'],
            values=[metrics['winning_trades'], metrics['losing_trades']],
            marker=dict(colors=['#06A77D', '#D62828']),
            textposition='inside',
            textinfo='label+percent'
        )])
        
        fig_pie.update_layout(
            title=f"Distribution: {metrics['winning_trades']} Ganadores vs {metrics['losing_trades']} Perdedores",
            height=400,
            template='plotly_dark'
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Estadísticas de P&L
        fig_stats = go.Figure()
        
        categories = ['Ganancia<br>Promedio', 'Pérdida<br>Promedio', 'Mayor<br>Ganancia', 'Mayor<br>Pérdida']
        values = [
            metrics['avg_win_pnl'],
            abs(metrics['avg_loss_pnl']),
            metrics['largest_win'],
            abs(metrics['largest_loss'])
        ]
        colors = ['#06A77D', '#D62828', '#06A77D', '#D62828']
        
        fig_stats.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'${v:.2f}' for v in values],
            textposition='outside'
        ))
        
        fig_stats.update_layout(
            title="Estadísticas de P&L",
            height=400,
            template='plotly_dark',
            showlegend=False,
            yaxis_title="Valor ($)"
        )
        
        st.plotly_chart(fig_stats, use_container_width=True)
    
    # ========================================================================
    # SECCIÓN 3: HISTOGRAMA DE P&L POR TRADE
    # ========================================================================
    
    st.subheader("3️⃣ Histograma de P&L por Trade")
    
    if trades:
        pnl_values = [trade.get('pnl', 0) for trade in trades]
        
        fig_histogram = go.Figure()
        fig_histogram.add_trace(go.Histogram(
            x=pnl_values,
            nbinsx=50,
            marker_color='#2E86AB',
            name='P&L Distribution'
        ))
        
        fig_histogram.add_vline(
            x=np.mean(pnl_values),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Promedio: ${np.mean(pnl_values):.2f}",
            annotation_position="top right"
        )
        
        fig_histogram.update_layout(
            title="Distribución de P&L por Trade",
            xaxis_title="P&L ($)",
            yaxis_title="Cantidad de Trades",
            height=400,
            template='plotly_dark',
            showlegend=False
        )
        
        st.plotly_chart(fig_histogram, use_container_width=True)
    
    # ========================================================================
    # SECCIÓN 4: MÉTRICAS DETALLADAS
    # ========================================================================
    
    st.subheader("4️⃣ Métricas Detalladas de Rendimiento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Capital Inicial", f"${metrics['initial_capital']:,.2f}")
        st.metric("Capital Final", f"${metrics['initial_capital'] + metrics['total_pnl']:,.2f}")
        st.metric("ROI Total", f"{(metrics['total_pnl']/metrics['initial_capital'])*100:.1f}%")
    
    with col2:
        st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
        st.metric("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.2f}")
        st.metric("Calmar Ratio", f"{metrics.get('calmar_ratio', 0):.2f}")
    
    with col3:
        st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        st.metric("Avg Trade P&L", f"${metrics['avg_trade_pnl']:.2f}")
        st.metric("Max Drawdown %", f"{metrics['max_drawdown']:.2f}%")
    
    # ========================================================================
    # SECCIÓN 5: ÚLTIMOS TRADES
    # ========================================================================
    
    st.subheader("5️⃣ Últimos 20 Trades Ejecutados")
    
    if trades:
        # Obtener últimos 20 trades
        recent_trades = trades[-20:]
        
        # Crear tabla
        trade_data = []
        for i, trade in enumerate(recent_trades, 1):
            trade_data.append({
                '#': i,
                'Entrada': datetime.fromtimestamp(trade.get('entry_time', 0)).strftime('%Y-%m-%d %H:%M') if trade.get('entry_time', 0) > 1000000 else f"T{trade.get('entry_time', 0)}",
                'Precio Entrada': f"${trade['entry_price']:.2f}",
                'Tamaño': f"{trade['position_size']:.6f}",
                'Dirección': trade['direction'].upper(),
                'Salida': trade.get('exit_reason', 'N/A').replace('_', ' '),
                'P&L': f"${trade['pnl']:.2f}",
                'Retorno %': f"{trade.get('pnl_percent', 0)*100:.2f}%"
            })
        
        df_trades = pd.DataFrame(trade_data)
        
        # Aplicar colores
        def color_pnl(val):
            try:
                num = float(val.replace('$', ''))
                return 'background-color: #06A77D' if num >= 0 else 'background-color: #D62828'
            except:
                return ''
        
        styled_df = df_trades.style.applymap(color_pnl, subset=['P&L', 'Retorno %'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    # ========================================================================
    # SECCIÓN 6: INFORMACIÓN GENERAL
    # ========================================================================
    
    st.divider()
    st.subheader("ℹ️ Información de Backtesting")
    
    info_cols = st.columns(4)
    
    with info_cols[0]:
        st.info(f"**Estrategia:** {strategy_name}")
    
    with info_cols[1]:
        st.info(f"**Símbolo:** BTC/USDT")
    
    with info_cols[2]:
        st.info(f"**Timeframe:** 15 minutos")
    
    with info_cols[3]:
        period = global_summary.get('period', {})
        st.info(f"**Período:** {period.get('start_date')} a {period.get('end_date')}")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.8rem;'>
    📊 Dashboard Bot Trader v4.7 | Backtesting Results | 
    Última actualización: 2025-10-25
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
