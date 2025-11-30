"""
Chart Building Module using Plotly
Creates interactive candlestick charts with ICT zones
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_candlestick_chart(df, indicators, signal_info, ticker):
    """
    Create interactive candlestick chart with ICT zones
    
    Args:
        df: OHLCV dataframe
        indicators: Dict of ICT indicators from get_all_ict_indicators()
        signal_info: Dict from generate_signal()
        ticker: Stock ticker symbol
    
    Returns:
        Plotly figure
    """
    # Create figure with secondary y-axis for volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} - ICT Analysis', 'Volume')
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    colors = ['#26a69a' if close >= open else '#ef5350' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Color settings for zones
    zone_colors = {
        'bullish_ob': 'rgba(38, 166, 154, 0.2)',
        'bearish_ob': 'rgba(239, 83, 80, 0.2)',
        'bullish_fvg': 'rgba(102, 187, 106, 0.3)',
        'bearish_fvg': 'rgba(239, 154, 154, 0.3)',
        'bpr': 'rgba(158, 158, 158, 0.2)'
    }
    
    # Add Order Blocks
    for ob in indicators.get('order_blocks', [])[-20:]:  # Show last 20
        fig.add_shape(
            type="rect",
            x0=df.index[ob['start_idx']],
            x1=df.index[-1],
            y0=ob['low'],
            y1=ob['high'],
            fillcolor=zone_colors.get(ob['type'], 'rgba(128, 128, 128, 0.2)'),
            line=dict(color=zone_colors.get(ob['type']).replace('0.2', '0.5'), width=1),
            layer='below',
            row=1, col=1
        )
        
        # Add label
        fig.add_annotation(
            x=df.index[ob['start_idx']],
            y=ob['high'],
            text="OB+" if ob['type'] == 'bullish_ob' else "OB-",
            showarrow=False,
            font=dict(size=10, color='white'),
            bgcolor=zone_colors.get(ob['type']).replace('0.2', '0.8'),
            row=1, col=1
        )
    
    # Add Fair Value Gaps
    for fvg in indicators.get('fair_value_gaps', [])[-15:]:  # Show last 15
        fig.add_shape(
            type="rect",
            x0=df.index[fvg['start_idx']],
            x1=df.index[-1],
            y0=fvg['gap_low'],
            y1=fvg['gap_high'],
            fillcolor=zone_colors.get(fvg['type'], 'rgba(128, 128, 128, 0.3)'),
            line=dict(color=zone_colors.get(fvg['type']).replace('0.3', '0.6'), width=1, dash='dot'),
            layer='below',
            row=1, col=1
        )
        
        # Add label
        fig.add_annotation(
            x=df.index[fvg['start_idx']],
            y=fvg['gap_high'],
            text="FVG+",
            showarrow=False,
            font=dict(size=9, color='white'),
            bgcolor=zone_colors.get(fvg['type']).replace('0.3', '0.8'),
            row=1, col=1
        )
    
    # Add Liquidity Sweeps
    for sweep in indicators.get('liquidity_sweeps', [])[-10:]:
        marker_color = '#26a69a' if sweep['reversal'] == 'bullish' else '#ef5350'
        fig.add_trace(
            go.Scatter(
                x=[df.index[sweep['idx']]],
                y=[sweep['price']],
                mode='markers',
                marker=dict(
                    symbol='triangle-up' if sweep['reversal'] == 'bullish' else 'triangle-down',
                    size=15,
                    color=marker_color,
                    line=dict(color='white', width=2)
                ),
                name=f"Sweep ({sweep['reversal']})",
                showlegend=False
            ),
            row=1, col=1
        )
    
    # Add OTE Levels (Fibonacci)
    if 'ote_levels' in signal_info:
        for level_name, price in signal_info['ote_levels'].items():
            fig.add_hline(
                y=price,
                line=dict(color='rgba(255, 193, 7, 0.5)', width=1, dash='dash'),
                annotation_text=f"OTE {level_name}",
                annotation_position="right",
                row=1, col=1
            )
    
    # Add current signal annotation
    current_price = signal_info.get('current_price', df['close'].iloc[-1])
    signal = signal_info.get('signal', 'NEUTRAL')
    confidence = signal_info.get('confidence', 0)
    
    signal_color = {
        'LONG': '#26a69a',
        'SHORT': '#ef5350',
        'NEUTRAL': '#9e9e9e'
    }.get(signal, '#9e9e9e')
    
    fig.add_annotation(
        x=df.index[-1],
        y=current_price,
        text=f"{signal}<br>({confidence}%)",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor=signal_color,
        font=dict(size=14, color='white', family='Arial Black'),
        bgcolor=signal_color,
        bordercolor='white',
        borderwidth=2,
        row=1, col=1
    )
    
    # Add entry/exit levels if available
    if 'entry_levels' in signal_info and signal_info['entry_levels']:
        levels = signal_info['entry_levels']
        
        if 'entry' in levels:
            fig.add_hline(
                y=levels['entry'],
                line=dict(color='blue', width=2, dash='solid'),
                annotation_text=f"Entry: ${levels['entry']:.2f}",
                annotation_position="left",
                row=1, col=1
            )
        
        if 'stop_loss' in levels:
            fig.add_hline(
                y=levels['stop_loss'],
                line=dict(color='red', width=2, dash='dot'),
                annotation_text=f"SL: ${levels['stop_loss']:.2f}",
                annotation_position="left",
                row=1, col=1
            )
        
        if 'take_profit1' in levels:
            fig.add_hline(
                y=levels['take_profit1'],
                line=dict(color='green', width=2, dash='dot'),
                annotation_text=f"TP1: ${levels['take_profit1']:.2f}",
                annotation_position="left",
                row=1, col=1
            )
        
        if 'take_profit2' in levels:
            fig.add_hline(
                y=levels['take_profit2'],
                line=dict(color='green', width=1, dash='dot'),
                annotation_text=f"TP2: ${levels['take_profit2']:.2f}",
                annotation_position="left",
                row=1, col=1
            )
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} ICT Analysis - Signal: {signal} ({confidence}% confidence)',
        yaxis_title='Price ($)',
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=800,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

def create_backtest_chart(df, backtest_results):
    """
    Create chart showing backtest results over time
    
    Args:
        df: Historical dataframe
        backtest_results: List of backtest result dicts
    
    Returns:
        Plotly figure
    """
    if not backtest_results:
        return None
    
    results_df = pd.DataFrame(backtest_results)
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Backtest Performance', 'Cumulative Returns'),
        row_heights=[0.6, 0.4]
    )
    
    # Add scatter plot of results
    colors = ['green' if r else 'red' for r in results_df['correct']]
    
    fig.add_trace(
        go.Scatter(
            x=results_df['date'],
            y=results_df['price_change_pct'],
            mode='markers',
            marker=dict(
                size=results_df['confidence'] / 5,  # Size based on confidence
                color=colors,
                line=dict(color='white', width=1)
            ),
            text=[f"Signal: {s}<br>Confidence: {c}%<br>Return: {p:.2f}%" 
                  for s, c, p in zip(results_df['signal'], results_df['confidence'], results_df['price_change_pct'])],
            hoverinfo='text',
            name='Signals'
        ),
        row=1, col=1
    )
    
    # Add zero line
    fig.add_hline(y=0, line=dict(color='gray', width=1, dash='dash'), row=1, col=1)
    
    # Calculate and plot cumulative returns
    results_df['cumulative_return'] = (1 + results_df['price_change_pct'] / 100).cumprod() - 1
    
    fig.add_trace(
        go.Scatter(
            x=results_df['date'],
            y=results_df['cumulative_return'] * 100,
            mode='lines',
            line=dict(color='#2196F3', width=2),
            fill='tozeroy',
            name='Cumulative Return'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=700,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Return (%)", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Return (%)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    return fig
