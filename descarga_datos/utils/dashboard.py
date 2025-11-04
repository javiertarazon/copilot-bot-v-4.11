"""
Dashboard de Visualización - Bot Trader Copilot
Utiliza Streamlit para mostrar resultados de backtesting con gráficos avanzados
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path
from datetime import datetime
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Bot Trader Copilot - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .metric-card {
        background-color: f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success { color: #31a71b; font-weight: bold; }
    .warning { color: #ff9800; font-weight: bold; }
    .danger { color: #d32f2f; font-weight: bold; }
    h1, h2, h3 { color: #1f77b4; }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("# 📊 Bot Trader Copilot - Dashboard Completo")
st.markdown("#### Análisis Detallado de Resultados de Backtesting")
st.markdown("---")

# Cargar resultados
results_dir = Path(__file__).parent.parent / "data" / "dashboard_results"

def load_results():
    """Cargar resultados del JSON"""
    try:
        results_file = results_dir / "Volatility 75 Index_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error cargando resultados: {e}")
    return None

def load_global_summary():
    """Cargar resumen global"""
    try:
        summary_file = results_dir / "global_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        pass
    return None

# Cargar datos
results = load_results()
global_summary = load_global_summary()

# Cargar datos
results = load_results()
global_summary = load_global_summary()

if results:
    data = results.get("strategies", {}).get("UltraDetailedHeikinAshiML", {})
    trades = data.get('trades', [])
    
    # ========================
    # SECCIÓN 1: TABLA RESUMEN SUPERIOR
    # ========================
    st.markdown("## 🎯 RESUMEN EJECUTIVO")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="P&L TOTAL",
            value=f"${data.get('total_pnl', 0):,.0f}",
            delta=f"+{(data.get('total_pnl', 0) / data.get('initial_capital', 1)) * 100:.1f}%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="CAPITAL FINAL",
            value=f"${data.get('initial_capital', 0) + data.get('total_pnl', 0):,.0f}",
            delta=f"Inicial: ${data.get('initial_capital', 0):,.0f}",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            label="WIN RATE",
            value=f"{data.get('win_rate', 0) * 100:.1f}%",
            delta=f"{data.get('winning_trades', 0):,} / {data.get('total_trades', 0):,}",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            label="MAX DRAWDOWN",
            value=f"{data.get('max_drawdown', 0) * 100:.1f}%",
            delta="Pérdida máxima",
            delta_color="inverse"
        )
    
    with col5:
        st.metric(
            label="SHARPE RATIO",
            value=f"{data.get('sharpe_ratio', 0):.2f}",
            delta="Rendimiento/Riesgo",
            delta_color="off"
        )
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 2: GRÁFICOS PRINCIPALES (Capital + Drawdown)
    # ========================
    st.markdown("## 📈 GRÁFICOS DE RENDIMIENTO")
    
    col1, col2 = st.columns(2)
    
    # Calcular evolución del capital y drawdown
    if trades:
        pnl_list = np.array([t.get('pnl', 0) for t in trades])
        cumulative_pnl = np.cumsum(pnl_list)
        initial_capital = data.get('initial_capital', 100000)
        capital_evolution = initial_capital + cumulative_pnl
        
        # Calcular drawdown
        running_max = np.maximum.accumulate(capital_evolution)
        drawdown = (capital_evolution - running_max) / running_max * 100
        
        # Gráfico 1: Capital Evolution
        with col1:
            fig_capital = go.Figure()
            fig_capital.add_trace(go.Scatter(
                y=capital_evolution,
                mode='lines',
                name='Capital',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            fig_capital.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color="red",
                annotation_text="Capital Inicial",
                annotation_position="right"
            )
            fig_capital.update_layout(
                title='<b>Evolución del Capital</b>',
                xaxis_title='Trade #',
                yaxis_title='Capital ($)',
                hovermode='x unified',
                height=450,
                template='plotly_white',
                font=dict(size=11)
            )
            st.plotly_chart(fig_capital, width='stretch')
        
        # Gráfico 2: Drawdown
        with col2:
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                y=drawdown,
                mode='lines',
                name='Drawdown',
                line=dict(color='#d32f2f', width=3),
                fill='tozeroy',
                fillcolor='rgba(211, 47, 47, 0.2)'
            ))
            fig_dd.add_hline(
                y=data.get('max_drawdown', 0) * -100,
                line_dash="dash",
                line_color="darkred",
                annotation_text=f"Max DD: {data.get('max_drawdown', 0) * 100:.1f}%",
                annotation_position="right"
            )
            fig_dd.update_layout(
                title='<b>Drawdown del Capital</b>',
                xaxis_title='Trade #',
                yaxis_title='Drawdown (%)',
                hovermode='x unified',
                height=450,
                template='plotly_white',
                font=dict(size=11)
            )
            st.plotly_chart(fig_dd, width='stretch')
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 3: P&L Y DISTRIBUCIÓN
    # ========================
    st.markdown("## 💰 ANÁLISIS DE P&L POR TRADE")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if trades:
            pnl_list = [t.get('pnl', 0) for t in trades]
            
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=pnl_list,
                nbinsx=60,
                name='P&L Trades',
                marker=dict(color='#31a71b', opacity=0.7),
                showlegend=True
            ))
            fig_dist.add_vline(
                x=0,
                line_dash="dash",
                line_color="black",
                annotation_text="Break Even"
            )
            fig_dist.update_layout(
                title='<b>Distribución de P&L por Trade</b>',
                xaxis_title='P&L ($)',
                yaxis_title='Frecuencia',
                hovermode='x',
                height=400,
                template='plotly_white',
                font=dict(size=11)
            )
            st.plotly_chart(fig_dist, width='stretch')
    
    with col2:
        if trades:
            # P&L acumulado con media móvil
            cumulative_pnl = np.cumsum([t.get('pnl', 0) for t in trades])
            
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                y=cumulative_pnl,
                mode='lines',
                name='P&L Acumulado',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # Agregar media móvil (100 trades)
            if len(cumulative_pnl) > 100:
                ma100 = pd.Series(cumulative_pnl).rolling(100).mean()
                fig_cum.add_trace(go.Scatter(
                    y=ma100,
                    mode='lines',
                    name='MA(100)',
                    line=dict(color='#ff7f0e', width=2, dash='dash')
                ))
            
            fig_cum.update_layout(
                title='<b>P&L Acumulado en el Tiempo</b>',
                xaxis_title='Trade #',
                yaxis_title='P&L Acumulado ($)',
                hovermode='x unified',
                height=400,
                template='plotly_white',
                font=dict(size=11)
            )
            st.plotly_chart(fig_cum, width='stretch')
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 4: TABLA DE MÉTRICAS DETALLADAS
    # ========================
    st.markdown("## 📊 MÉTRICAS DETALLADAS")    # ========================
    # SECCIÓN 4: TABLA DE MÉTRICAS DETALLADAS
    # ========================
    st.markdown("## 📊 MÉTRICAS DETALLADAS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📈 Rentabilidad")
        metrics_pnl = {
            "P&L Total": f"${data.get('total_pnl', 0):,.2f}",
            "P&L Ajustado": f"${data.get('adjusted_total_pnl', 0):,.2f}",
            "P&L Promedio/Trade": f"${data.get('avg_trade_pnl', 0):.2f}",
            "Ganancia Promedio": f"${data.get('avg_win_pnl', 0):.2f}",
            "Pérdida Promedio": f"${data.get('avg_loss_pnl', 0):.2f}",
            "Ganancia Máxima": f"${data.get('largest_win', 0):.2f}",
            "Pérdida Máxima": f"${data.get('largest_loss', 0):.2f}",
        }
        df_pnl = pd.DataFrame(list(metrics_pnl.items()), columns=["Métrica", "Valor"])
        st.dataframe(df_pnl, width='stretch', hide_index=True)
    
    with col2:
        st.markdown("### 📊 Estadísticas de Trades")
        metrics_trades = {
            "Total Trades": f"{data.get('total_trades', 0):,}",
            "Trades Ganadores": f"{data.get('winning_trades', 0):,}",
            "Trades Perdedores": f"{data.get('losing_trades', 0):,}",
            "Win Rate": f"{data.get('win_rate', 0) * 100:.2f}%",
            "Profit Factor": f"{data.get('profit_factor', 0):.2f}",
            "Compensation Ratio": f"{data.get('compensation_ratio', 0):.2f}",
            "Trades Compensados": f"{data.get('compensated_trades', 0)}",
        }
        df_trades = pd.DataFrame(list(metrics_trades.items()), columns=["Métrica", "Valor"])
        st.dataframe(df_trades, width='stretch', hide_index=True)
    
    with col3:
        st.markdown("### 🎯 Ratios de Rendimiento")
        metrics_ratios = {
            "Sharpe Ratio": f"{data.get('sharpe_ratio', 0):.4f}",
            "Sortino Ratio": f"{data.get('sortino_ratio', 0):.4f}",
            "Calmar Ratio": f"{data.get('calmar_ratio', 0):.4f}",
            "Max Drawdown": f"{data.get('max_drawdown', 0) * 100:.2f}%",
            "Capital Inicial": f"${data.get('initial_capital', 0):,.0f}",
            "Capital Final": f"${data.get('initial_capital', 0) + data.get('total_pnl', 0):,.0f}",
            "Retorno Total": f"{(data.get('total_pnl', 0) / data.get('initial_capital', 1)) * 100:.2f}%",
        }
        df_ratios = pd.DataFrame(list(metrics_ratios.items()), columns=["Métrica", "Valor"])
        st.dataframe(df_ratios, width='stretch', hide_index=True)
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 5: GRÁFICOS ADICIONALES
    # ========================
    st.markdown("## � ANÁLISIS ADICIONALES")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if trades:
            # Win Rate por ventanas de 100 trades
            window_size = 100
            windows = []
            win_counts = []
            
            for i in range(0, len(trades), window_size):
                window = trades[i:i+window_size]
                wins = sum(1 for t in window if t.get('pnl', 0) > 0)
                win_rate_window = (wins / len(window) * 100) if window else 0
                windows.append(f"{i//window_size + 1}")
                win_counts.append(win_rate_window)
            
            fig_winrate = go.Figure()
            fig_winrate.add_trace(go.Bar(
                x=windows,
                y=win_counts,
                name='Win Rate %',
                marker=dict(
                    color=win_counts,
                    colorscale='RdYlGn',
                    line=dict(color='rgba(0,0,0,0.5)', width=1)
                ),
                text=[f"{x:.1f}%" for x in win_counts],
                textposition='outside'
            ))
            fig_winrate.update_layout(
                title='<b>Win Rate por Ventana (100 trades)</b>',
                xaxis_title='Ventana',
                yaxis_title='Win Rate (%)',
                height=400,
                template='plotly_white',
                font=dict(size=11),
                showlegend=False
            )
            st.plotly_chart(fig_winrate, width='stretch')
    
    with col2:
        if trades:
            # Dirección de trades
            directions = [t.get('direction', 'unknown') for t in trades]
            direction_counts = pd.Series(directions).value_counts()
            
            fig_direction = go.Figure(data=[
                go.Pie(
                    labels=direction_counts.index,
                    values=direction_counts.values,
                    marker=dict(colors=['#1f77b4', '#ff7f0e']),
                    hole=.4,
                    textposition='inside',
                    textinfo='label+percent'
                )
            ])
            fig_direction.update_layout(
                title='<b>Distribución Long vs Short</b>',
                height=400,
                template='plotly_white',
                font=dict(size=11)
            )
            st.plotly_chart(fig_direction, width='stretch')
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 6: TABLA DE TRADES DETALLADA
    # ========================
    st.markdown("## 📋 DETALLE DE TRADES")
    
    if trades:
        # Crear DataFrame con todos los trades
        trades_df = pd.DataFrame(trades)
        
        # Seleccionar columnas relevantes y reordenarlas
        cols_display = ['entry_time', 'entry_price', 'exit_time', 'exit_price', 
                       'direction', 'position_size', 'pnl', 'pnl_percent', 
                       'exit_reason', 'ml_confidence']
        
        trades_df_display = trades_df[[c for c in cols_display if c in trades_df.columns]].copy()
        
        # Formatear números
        if 'entry_price' in trades_df_display.columns:
            trades_df_display['entry_price'] = trades_df_display['entry_price'].apply(lambda x: f"${x:,.2f}")
        if 'exit_price' in trades_df_display.columns:
            trades_df_display['exit_price'] = trades_df_display['exit_price'].apply(lambda x: f"${x:,.2f}")
        if 'pnl' in trades_df_display.columns:
            trades_df_display['pnl'] = trades_df_display['pnl'].apply(lambda x: f"${x:,.2f}")
        if 'pnl_percent' in trades_df_display.columns:
            trades_df_display['pnl_percent'] = trades_df_display['pnl_percent'].apply(lambda x: f"{x*100:.2f}%")
        if 'position_size' in trades_df_display.columns:
            trades_df_display['position_size'] = trades_df_display['position_size'].apply(lambda x: f"{x:.4f}")
        if 'ml_confidence' in trades_df_display.columns:
            trades_df_display['ml_confidence'] = trades_df_display['ml_confidence'].apply(lambda x: f"{x:.2f}")
        
        # Mostrar tabla con scroll
        st.dataframe(trades_df_display, width='stretch', height=500)
        
        # Descargar datos
        csv = trades_df_display.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Trades en CSV",
            data=csv,
            file_name="trades_export.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 7: ESTADÍSTICAS AVANZADAS
    # ========================
    st.markdown("## 🔬 ESTADÍSTICAS AVANZADAS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if trades:
            pnl_list = np.array([t.get('pnl', 0) for t in trades])
            st.metric(
                "Desv. Estándar P&L",
                f"${np.std(pnl_list):.2f}",
                f"Media: ${np.mean(pnl_list):.2f}"
            )
    
    with col2:
        if trades:
            consecutive_wins = 0
            max_consecutive_wins = 0
            for t in trades:
                if t.get('pnl', 0) > 0:
                    consecutive_wins += 1
                    max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
                else:
                    consecutive_wins = 0
            
            st.metric(
                "Max Ganancias Consecutivas",
                f"{max_consecutive_wins}",
                "Rachas de victorias"
            )
    
    with col3:
        if trades:
            consecutive_losses = 0
            max_consecutive_losses = 0
            for t in trades:
                if t.get('pnl', 0) < 0:
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0
            
            st.metric(
                "Max Pérdidas Consecutivas",
                f"{max_consecutive_losses}",
                "Rachas de pérdidas"
            )
    
    st.markdown("---")
    
    # ========================
    # SECCIÓN 8: INFORMACIÓN DEL SISTEMA
    # ========================
    st.markdown("## ℹ️ INFORMACIÓN DEL SISTEMA")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Símbolo",
            data.get('symbol', 'N/A')
        )
    
    with col2:
        if global_summary:
            st.metric(
                "Última Ejecución",
                global_summary.get('timestamp', 'N/A')[:10]
            )
    
    with col3:
        st.metric(
            "Total Velas",
            f"{len(trades) if trades else 0:,}"
        )
    
    with col4:
        st.metric(
            "Período",
            "2024-06-01 a 2025-10-24"
        )
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px; margin-top: 20px; padding: 20px;'>
    <b>Bot Trader Copilot © 2025</b> | Dashboard de Visualización v2.0 | 
    Estrategia: UltraDetailedHeikinAshiML | Capital: $100,000 USD
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ No se encontraron resultados de backtesting. Ejecuta un backtest primero con: `python main.py --backtest-only`")
