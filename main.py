"""
ICT-Based Trading Application
MAG7 + SPY Trading Signals using Inner Circle Trader Strategies
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Import custom modules
from data_fetcher import fetch_stock_data, fetch_stock_data_range, get_available_tickers
from ict_strategies import get_all_ict_indicators
from signal_generator import generate_signal, backtest_signal
from chart_builder import create_candlestick_chart, create_backtest_chart
from signal_explanations import explain_signal_in_detail

# Page configuration
st.set_page_config(
    page_title="ICT Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size: 30px !important;
        font-weight: bold;
    }
    .signal-long {
        color: #26a69a;
        font-size: 40px;
        font-weight: bold;
    }
    .signal-short {
        color: #ef5350;
        font-size: 40px;
        font-weight: bold;
    }
    .signal-neutral {
        color: #9e9e9e;
        font-size: 40px;
        font-weight: bold;
    }
    .confidence {
        font-size: 24px;
        font-weight: bold;
    }
    .zone-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📈 ICT-Based Trading Signals")
st.markdown("*Inner Circle Trader Strategies for MAG7 & SPY*")

# Sidebar
st.sidebar.header("Settings")

# Stock selector
tickers = get_available_tickers()
selected_ticker = st.sidebar.selectbox(
    "Select Stock",
    options=list(tickers.keys()),
    format_func=lambda x: f"{x} - {tickers[x]}"
)

# Timeframe selector
timeframe = st.sidebar.selectbox(
    "Timeframe",
    options=["Daily", "4-Hour", "1-Hour", "30-Minute"],
    index=2
)

# Map timeframe to yfinance parameters
timeframe_map = {
    "Daily": ("1y", "1d", "2y", "1d"),
    "4-Hour": ("60d", "1h", "60d", "1h"),
    "1-Hour": ("10d", "1h", "30d", "1h"),
    "30-Minute": ("5d", "30m", "15d", "30m")
}

period, interval, backtest_period, backtest_interval = timeframe_map[timeframe]

# Info section
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 ICT Strategies Included")
st.sidebar.markdown("""
- ✅ Order Blocks (OB)
- ✅ Fair Value Gaps (FVG)
- ✅ Liquidity Sweeps
- ✅ Market Structure Shifts
- ✅ Breaker Blocks
- ✅ Optimal Trade Entry (OTE)
- ✅ Displacement
- ✅ Balanced Price Range (BPR)
- ✅ Volume Imbalance
""")

# Main tabs
tab1, tab2, tab3 = st.tabs(["🔴 Live Analysis", "⏰ Time Machine Backtest", "⭐ High Confidence Signals"])

# ========== TAB 1: LIVE ANALYSIS ==========
with tab1:
    st.header(f"Live Analysis - {selected_ticker}")
    
    with st.spinner(f"Fetching data for {selected_ticker}..."):
        df = fetch_stock_data(selected_ticker, period=period, interval=interval)
        
        # Resample to 4-hour if needed
        if timeframe == "4-Hour" and interval == "1h" and df is not None:
            df = df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        if df is not None and not df.empty:
            # Fetch higher timeframe data for multi-TF confirmation
            htf_df = None
            try:
                if timeframe == "30-Minute":
                    # For 30min, use 4H as HTF
                    htf_df = fetch_stock_data(selected_ticker, period="60d", interval="1h")
                    if htf_df is not None and not htf_df.empty:
                        htf_df = htf_df.resample('4H').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()
                elif timeframe == "1-Hour":
                    # For 1H, use Daily as HTF
                    htf_df = fetch_stock_data(selected_ticker, period="1y", interval="1d")
                elif timeframe == "4-Hour":
                    # For 4H, use Daily as HTF
                    htf_df = fetch_stock_data(selected_ticker, period="1y", interval="1d")
                elif timeframe == "Daily":
                    # For Daily, use Weekly as HTF (resample from daily)
                    htf_df = fetch_stock_data(selected_ticker, period="2y", interval="1d")
                    if htf_df is not None and not htf_df.empty:
                        htf_df = htf_df.resample('W').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()
            except Exception as e:
                st.warning(f"Could not fetch HTF data: {e}")
                htf_df = None
            
            # Generate signal with HTF confirmation
            signal_info = generate_signal(df, htf_df=htf_df)
            
            # Debug: Show HTF status
            if htf_df is not None and not htf_df.empty:
                st.caption(f"✅ HTF data loaded: {len(htf_df)} candles")
            else:
                st.caption(f"⚠️ HTF data not available - running without multi-timeframe confirmation")
            
            # Display main signal
            col1, col2, col3 = st.columns([2, 2, 3])
            
            with col1:
                st.markdown("### Current Signal")
                signal = signal_info['signal']
                if signal == 'LONG':
                    st.markdown(f'<p class="signal-long">🟢 {signal}</p>', unsafe_allow_html=True)
                elif signal == 'SHORT':
                    st.markdown(f'<p class="signal-short">🔴 {signal}</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="signal-neutral">⚪ {signal}</p>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("### Confidence")
                confidence = signal_info['confidence']
                st.markdown(f'<p class="confidence">{confidence}%</p>', unsafe_allow_html=True)
                st.progress(confidence / 100)
            
            with col3:
                st.markdown("### Current Price")
                current_price = signal_info['current_price']
                st.markdown(f'<p class="big-font">${current_price:.2f}</p>', unsafe_allow_html=True)
                
                # Price change
                price_change = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
                change_color = "green" if price_change > 0 else "red"
                st.markdown(f'<p style="color:{change_color}; font-size:18px;">{price_change:+.2f}%</p>', unsafe_allow_html=True)
            
            # Advanced ICT Metrics
            st.markdown("---")
            st.markdown("### 🎯 ICT Analysis Metrics")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                kill_zone = signal_info.get('kill_zone', 'OUTSIDE')
                if kill_zone == 'NEW_YORK_AM':
                    kz_display = "⭐ NY AM (BEST)"
                    kz_color = "green"
                elif kill_zone != 'OUTSIDE':
                    kz_display = kill_zone.replace('_', ' ')
                    kz_color = "orange"
                else:
                    kz_display = "❌ Outside Zones"
                    kz_color = "gray"
                
                st.markdown(f"**Kill Zone**")
                st.markdown(f'<p style="color:{kz_color}; font-size:18px; font-weight:bold;">{kz_display}</p>', unsafe_allow_html=True)
            
            with metric_col2:
                pd_info = signal_info.get('premium_discount', {})
                zone_detail = pd_info.get('detailed_zone', 'N/A')
                zone_pos = pd_info.get('price_position', 0.5)
                
                if 'PREMIUM' in zone_detail:
                    pd_color = "red"
                    pd_icon = "🔴"
                else:
                    pd_color = "green"
                    pd_icon = "🟢"
                
                st.markdown(f"**Price Zone**")
                st.markdown(f'<p style="color:{pd_color}; font-size:18px; font-weight:bold;">{pd_icon} {zone_detail}</p>', unsafe_allow_html=True)
                st.caption(f"Position: {zone_pos:.1%} of range")
            
            with metric_col3:
                p3_phase = signal_info.get('power_of_3', 'N/A')
                
                if p3_phase == 'DISTRIBUTION':
                    p3_color = "green"
                    p3_icon = "✅"
                elif p3_phase == 'MANIPULATION':
                    p3_color = "orange"
                    p3_icon = "⚠️"
                else:
                    p3_color = "gray"
                    p3_icon = "⏳"
                
                st.markdown(f"**Power of 3**")
                st.markdown(f'<p style="color:{p3_color}; font-size:18px; font-weight:bold;">{p3_icon} {p3_phase}</p>', unsafe_allow_html=True)
            
            with metric_col4:
                htf_info = signal_info.get('htf_bias', {})
                htf_bias = htf_info.get('bias', 'N/A')
                htf_strength = htf_info.get('strength', 0)
                
                if htf_bias == 'BULLISH':
                    htf_color = "green"
                    htf_icon = "📈"
                elif htf_bias == 'BEARISH':
                    htf_color = "red"
                    htf_icon = "📉"
                else:
                    htf_color = "gray"
                    htf_icon = "➖"
                
                st.markdown(f"**HTF Bias**")
                st.markdown(f'<p style="color:{htf_color}; font-size:18px; font-weight:bold;">{htf_icon} {htf_bias}</p>', unsafe_allow_html=True)
                if htf_bias != 'N/A':
                    st.caption(f"Strength: {htf_strength}%")
            
            # Reasoning - Detailed and beginner-friendly
            st.markdown("---")
            with st.expander("📋 Why this signal? (Click for detailed explanation)", expanded=True):
                if signal_info['reasoning']:
                    detailed_reasons = explain_signal_in_detail(
                        signal_info['reasoning'], 
                        signal_info['signal'], 
                        signal_info['confidence']
                    )
                    for reason in detailed_reasons:
                        st.markdown(reason)
                else:
                    st.info("No strong signals detected - waiting for clearer setup.")
            
            # Entry/Exit Levels
            if signal_info['entry_levels']:
                st.markdown("---")
                st.markdown("### 🎯 Suggested Levels")
                
                levels_col1, levels_col2, levels_col3, levels_col4 = st.columns(4)
                
                levels = signal_info['entry_levels']
                
                with levels_col1:
                    if 'entry' in levels:
                        st.metric("Entry", f"${levels['entry']:.2f}")
                
                with levels_col2:
                    if 'stop_loss' in levels:
                        st.metric("Stop Loss", f"${levels['stop_loss']:.2f}", 
                                delta=f"{((levels['stop_loss'] - current_price) / current_price * 100):.2f}%")
                
                with levels_col3:
                    if 'take_profit1' in levels:
                        st.metric("TP1", f"${levels['take_profit1']:.2f}",
                                delta=f"{((levels['take_profit1'] - current_price) / current_price * 100):.2f}%")
                
                with levels_col4:
                    if 'take_profit2' in levels:
                        st.metric("TP2", f"${levels['take_profit2']:.2f}",
                                delta=f"{((levels['take_profit2'] - current_price) / current_price * 100):.2f}%")
            
            # Active Zones
            st.markdown("---")
            st.markdown("### 🎯 Active ICT Zones")
            
            if signal_info['active_zones']:
                zone_cols = st.columns(2)
                col_idx = 0
                
                for zone_type, zones in signal_info['active_zones'].items():
                    with zone_cols[col_idx % 2]:
                        st.markdown(f'<div class="zone-card">', unsafe_allow_html=True)
                        st.markdown(f"**{zone_type.replace('_', ' ').title()}**")
                        for zone in zones[:3]:  # Show first 3 zones of each type
                            if 'high' in zone and 'low' in zone:
                                st.markdown(f"- ${zone['low']:.2f} - ${zone['high']:.2f}")
                            elif 'gap_high' in zone and 'gap_low' in zone:
                                st.markdown(f"- ${zone['gap_low']:.2f} - ${zone['gap_high']:.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    col_idx += 1
            else:
                st.info("No active zones near current price.")
            
            # Chart
            st.markdown("---")
            st.markdown("### 📊 Price Chart with ICT Levels")
            
            indicators = signal_info['all_indicators']
            fig = create_candlestick_chart(df, indicators, signal_info, selected_ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            # Score breakdown
            st.markdown("---")
            col_score1, col_score2 = st.columns(2)
            
            with col_score1:
                st.metric("Bullish Score", signal_info.get('bullish_score', 0))
            
            with col_score2:
                st.metric("Bearish Score", signal_info.get('bearish_score', 0))
        
        else:
            st.error(f"Unable to load data for {selected_ticker}")

# ========== TAB 2: BACKTEST ==========
with tab2:
    st.header(f"🕐 Time Machine - {selected_ticker}")
    
    st.markdown(f"""
    **Pick a specific time, see what signal the system would have given, and check if it was right.**
    
    Simple: Choose a {timeframe.lower()} candle → See LONG/SHORT/NEUTRAL → Was it profitable in the next hour?
    """)
    
    # Fetch full historical data
    with st.spinner("Loading historical data..."):
        full_df = fetch_stock_data(selected_ticker, period=backtest_period, interval=backtest_interval)
        
        # Resample if needed
        if timeframe == "4-Hour" and backtest_interval == "1h":
            full_df = full_df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
    
    if full_df is not None and not full_df.empty:
        # Show available time range
        st.caption(f"📅 Available data: {full_df.index[0].strftime('%Y-%m-%d %I:%M %p')} to {full_df.index[-1].strftime('%Y-%m-%d %I:%M %p')}")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            target_date = st.date_input(
                "📅 Date",
                value=datetime.now() - timedelta(days=7),
                min_value=full_df.index[50].date(),
                max_value=full_df.index[-2].date()
            )
        
        with col2:
            # Get available times for selected date
            date_mask = full_df.index.date == target_date
            available_times = full_df.index[date_mask]
            
            if len(available_times) > 0:
                time_options = [t.strftime('%I:%M %p') for t in available_times]
                selected_time_str = st.selectbox(
                    "⏰ Time",
                    options=time_options,
                    index=min(len(time_options)//2, len(time_options)-1)  # Default to middle or last
                )
                selected_time_idx = time_options.index(selected_time_str)
                selected_datetime = available_times[selected_time_idx]
            else:
                st.warning(f"No data available for {target_date}")
                selected_datetime = None
        
        with col3:
            st.markdown("")
            st.markdown("")
            run_test = st.button("🔍 Test", type="primary", use_container_width=True)
        
        if run_test and selected_datetime is not None:
            with st.spinner("Analyzing..."):
                # Calculate how many periods = 1 hour
                if timeframe == "30-Minute":
                    forward_periods = 2  # 2 x 30min = 1 hour
                elif timeframe == "1-Hour":
                    forward_periods = 1  # 1 x 1hour = 1 hour
                elif timeframe == "4-Hour":
                    forward_periods = 1  # Just check next 4-hour candle
                else:  # Daily
                    forward_periods = 1  # Next day
                
                result = backtest_signal(full_df, selected_datetime, forward_periods)
                
                if result:
                    # Display results
                    st.markdown("---")
                    
                    # Big result display
                    if result['correct']:
                        st.success(f"### ✅ CORRECT - Signal was {result['signal']}")
                    else:
                        st.error(f"### ❌ WRONG - Signal was {result['signal']}")
                    
                    result_col1, result_col2, result_col3 = st.columns(3)
                    
                    with result_col1:
                        st.metric(
                            "Entry Price", 
                            f"${result['entry_price']:.2f}"
                        )
                    
                    with result_col2:
                        change_delta = result['price_change_pct']
                        st.metric(
                            f"Price After {forward_periods}{'h' if timeframe in ['1-Hour', '30-Minute'] else ' period'}",
                            f"${result['end_price']:.2f}",
                            f"{change_delta:+.2f}%"
                        )
                    
                    with result_col3:
                        st.metric("Confidence", f"{result['confidence']}%")
                    
                    # Why did it give this signal? - Detailed explanation
                    with st.expander("📋 Why this signal? (Detailed explanation)", expanded=False):
                        detailed_reasons = explain_signal_in_detail(
                            result['reasoning'], 
                            result['signal'], 
                            result['confidence']
                        )
                        for reason in detailed_reasons:
                            st.markdown(reason)
                    
                    # Chart
                    st.markdown("---")
                    st.markdown("### 📊 Chart at That Time")
                    
                    # Get data around that time
                    target_idx = full_df.index.get_indexer([selected_datetime], method='nearest')[0]
                    chart_df = full_df.iloc[max(0, target_idx-100):min(len(full_df), target_idx+forward_periods+10)]
                    
                    # Generate indicators for chart
                    signal_info_hist = generate_signal(chart_df)
                    
                    fig_hist = create_candlestick_chart(
                        chart_df, 
                        signal_info_hist['all_indicators'],
                        signal_info_hist,
                        selected_ticker
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.error("Unable to test this time - not enough data available.")
        
        # Optional: Date range backtest (collapsed by default)
        with st.expander("🔬 Advanced: Test Multiple Dates", expanded=False):
            # Date range backtest
            col_range1, col_range2 = st.columns(2)
            
            with col_range1:
                # Calculate a safe default start date within the available range
                safe_start = max(
                    full_df.index[50].date(),
                    full_df.index[-6].date() - timedelta(days=30)
                )
                start_date = st.date_input(
                    "Start Date",
                    value=safe_start,
                    min_value=full_df.index[50].date(),
                    max_value=full_df.index[-6].date()
                )
            
            with col_range2:
                # Safe default end date
                safe_end = full_df.index[-6].date()
                end_date = st.date_input(
                    "End Date",
                    value=safe_end,
                    min_value=full_df.index[50].date(),
                    max_value=full_df.index[-6].date()
                )
            
            test_frequency = st.slider("Test Every N Periods", 1, 50, 10)
            forward_periods_range = st.slider("Periods Forward to Check", 1, 50, 10)
            
            if st.button("Run Range Backtest", type="primary"):
                with st.spinner("Running backtest on date range..."):
                    # Generate test dates - sample evenly across the range
                    total_points = len(full_df.loc[start_date:end_date])
                    test_indices = range(0, total_points, test_frequency)
                    test_dates = [full_df.loc[start_date:end_date].index[i] for i in test_indices if i < total_points]
                    
                    results = []
                    progress_bar = st.progress(0)
                    
                    for i, test_date in enumerate(test_dates):
                        result = backtest_signal(full_df, test_date, forward_periods_range)
                        if result:
                            results.append(result)
                        progress_bar.progress((i + 1) / len(test_dates))
                    
                    progress_bar.empty()
                    
                    if results:
                        # Calculate metrics
                        total_signals = len(results)
                        correct_signals = sum(r['correct'] for r in results)
                        accuracy = (correct_signals / total_signals) * 100
                        
                        avg_return = sum(r['price_change_pct'] for r in results) / total_signals
                        
                        # Filter by signal type
                        long_signals = [r for r in results if r['signal'] == 'LONG']
                        short_signals = [r for r in results if r['signal'] == 'SHORT']
                        
                        long_accuracy = (sum(r['correct'] for r in long_signals) / len(long_signals) * 100) if long_signals else 0
                        short_accuracy = (sum(r['correct'] for r in short_signals) / len(short_signals) * 100) if short_signals else 0
                        
                        # Display summary metrics
                        st.markdown("---")
                        st.markdown("### 📊 Backtest Summary")
                        
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        with metric_col1:
                            st.metric("Total Signals", total_signals)
                        
                        with metric_col2:
                            st.metric("Overall Accuracy", f"{accuracy:.1f}%")
                        
                        with metric_col3:
                            st.metric("Avg Return", f"{avg_return:.2f}%")
                        
                        with metric_col4:
                            st.metric("Win Rate", f"{correct_signals}/{total_signals}")
                        
                        # Signal type breakdown
                        st.markdown("---")
                        acc_col1, acc_col2, acc_col3 = st.columns(3)
                        
                        with acc_col1:
                            st.metric("LONG Signals", len(long_signals))
                            st.metric("LONG Accuracy", f"{long_accuracy:.1f}%")
                        
                        with acc_col2:
                            st.metric("SHORT Signals", len(short_signals))
                            st.metric("SHORT Accuracy", f"{short_accuracy:.1f}%")
                        
                        with acc_col3:
                            neutral_count = total_signals - len(long_signals) - len(short_signals)
                            st.metric("NEUTRAL Signals", neutral_count)
                        
                        # Performance chart
                        st.markdown("---")
                        st.markdown("### 📈 Performance Over Time")
                        
                        fig_backtest = create_backtest_chart(full_df, results)
                        if fig_backtest:
                            st.plotly_chart(fig_backtest, use_container_width=True)
                        
                        # Detailed results table
                        st.markdown("---")
                        st.markdown("### 📋 Detailed Results")
                        
                        results_df = pd.DataFrame(results)
                        results_df['date'] = pd.to_datetime(results_df['date']).dt.date
                        
                        display_df = results_df[[
                            'date', 'signal', 'confidence', 'entry_price', 
                            'price_change_pct', 'correct'
                        ]].copy()
                        
                        display_df.columns = [
                            'Date', 'Signal', 'Confidence (%)', 'Entry Price ($)',
                            'Return (%)', 'Correct'
                        ]
                        
                        display_df['Correct'] = display_df['Correct'].map({True: '✅', False: '❌'})
                        
                        st.dataframe(
                            display_df.style.background_gradient(
                                subset=['Return (%)'],
                                cmap='RdYlGn',
                                vmin=-5,
                                vmax=5
                            ),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.warning("No valid backtest results for the selected range.")
    else:
        st.error("Unable to load historical data.")

# ========== TAB 3: HIGH CONFIDENCE SIGNALS ==========
with tab3:
    st.header(f"⭐ High Confidence Signals - {selected_ticker}")
    
    st.markdown(f"""
    **Showing all signals from the last 20 days with 70%+ confidence.**
    
    These are the strongest setups identified by the system - the ones where multiple ICT strategies aligned perfectly.
    """)
    
    with st.spinner(f"Scanning last 20 days for high confidence signals..."):
        # Fetch data for signal scanning
        scan_df = fetch_stock_data(selected_ticker, period="20d", interval=interval)
        
        # Resample if needed
        if timeframe == "4-Hour" and interval == "1h" and scan_df is not None:
            scan_df = scan_df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
    
    if scan_df is not None and not scan_df.empty:
        # Scan through each candle for high confidence signals
        high_conf_signals = []
        
        min_required = min(50, len(scan_df) // 3)
        
        for idx in range(min_required, len(scan_df)):
            # Generate signal for this point in time
            historical_slice = scan_df.iloc[:idx+1].copy()
            signal_result = generate_signal(historical_slice)
            
            # Only keep if confidence >= 70%
            if signal_result['confidence'] >= 70 and signal_result['signal'] != 'NEUTRAL':
                # Calculate what happened after
                forward_check = 2 if timeframe == "30-Minute" else 1
                if idx + forward_check < len(scan_df):
                    entry_price = scan_df['close'].iloc[idx]
                    future_price = scan_df['close'].iloc[idx + forward_check]
                    price_change = ((future_price - entry_price) / entry_price) * 100
                    
                    # Was it correct?
                    was_correct = False
                    if signal_result['signal'] == 'LONG' and price_change > 0.05:
                        was_correct = True
                    elif signal_result['signal'] == 'SHORT' and price_change < -0.05:
                        was_correct = True
                    
                    high_conf_signals.append({
                        'datetime': scan_df.index[idx],
                        'signal': signal_result['signal'],
                        'confidence': signal_result['confidence'],
                        'entry_price': entry_price,
                        'price_change': price_change,
                        'correct': was_correct,
                        'reasoning': signal_result['reasoning']
                    })
        
        if high_conf_signals:
            st.success(f"🎯 Found {len(high_conf_signals)} high-confidence (70%+) signals in the last 20 days!")
            
            # Summary stats
            correct_count = sum(1 for s in high_conf_signals if s['correct'])
            accuracy = (correct_count / len(high_conf_signals)) * 100 if high_conf_signals else 0
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("Total Signals", len(high_conf_signals))
            
            with stat_col2:
                st.metric("Correct", f"{correct_count}/{len(high_conf_signals)}")
            
            with stat_col3:
                st.metric("Accuracy", f"{accuracy:.1f}%")
            
            with stat_col4:
                avg_conf = sum(s['confidence'] for s in high_conf_signals) / len(high_conf_signals)
                st.metric("Avg Confidence", f"{avg_conf:.0f}%")
            
            st.markdown("---")
            st.markdown("### 📜 Signal History")
            
            # Display each signal
            for i, sig in enumerate(reversed(high_conf_signals), 1):  # Most recent first
                result_icon = "✅" if sig['correct'] else "❌"
                signal_icon = "🔼" if sig['signal'] == 'LONG' else "🔻"
                
                with st.expander(
                    f"{result_icon} {sig['datetime'].strftime('%m/%d %I:%M %p')} - "
                    f"{signal_icon} {sig['signal']} ({sig['confidence']}% conf) - "
                    f"{sig['price_change']:+.2f}%",
                    expanded=False
                ):
                    res_col1, res_col2, res_col3 = st.columns(3)
                    
                    with res_col1:
                        st.metric("Entry", f"${sig['entry_price']:.2f}")
                    
                    with res_col2:
                        st.metric("Result", f"{sig['price_change']:+.2f}%")
                    
                    with res_col3:
                        outcome = "CORRECT ✅" if sig['correct'] else "WRONG ❌"
                        st.metric("Outcome", outcome)
                    
                    st.markdown("**Why this signal:**")
                    for j, reason in enumerate(sig['reasoning'], 1):
                        st.markdown(f"{j}. {reason}")
        else:
            st.info("🔍 No 70%+ confidence signals found in the last 20 days. This means there haven't been many high-probability setups recently.")
    else:
        st.error("Unable to load data for signal scanning.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>ICT Trading Signals | Data provided by Yahoo Finance (yfinance)</p>
        <p><small>⚠️ This tool is for educational purposes only. Not financial advice.</small></p>
    </div>
""", unsafe_allow_html=True)
