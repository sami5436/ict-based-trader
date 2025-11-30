"""
ICT (Inner Circle Trader) Strategy Detection Module

Implements all major ICT concepts:
- Order Blocks
- Fair Value Gaps (FVG)
- Liquidity Sweeps
- Market Structure Shifts (MSS/BOS)
- Breaker Blocks
- Optimal Trade Entry (OTE)
- Displacement
- Balanced Price Range (BPR)
- Volume Imbalance
"""
import pandas as pd
import numpy as np

def detect_order_blocks(df, lookback=20, displacement_threshold=0.015):
    """
    Detect Order Blocks - last opposite candle before strong displacement
    
    Returns:
        List of dicts with {type, start_idx, end_idx, high, low, strength}
    """
    order_blocks = []
    
    for i in range(lookback, len(df)):
        # Calculate displacement (strong move)
        curr_close = df['close'].iloc[i]
        prev_close = df['close'].iloc[i-1]
        displacement = abs(curr_close - prev_close) / prev_close
        
        if displacement > displacement_threshold:
            # Bullish displacement - look for last bearish candle
            if curr_close > prev_close:
                for j in range(i-1, max(i-lookback, 0), -1):
                    if df['close'].iloc[j] < df['open'].iloc[j]:  # Bearish candle
                        order_blocks.append({
                            'type': 'bullish_ob',
                            'start_idx': j,
                            'end_idx': i,
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'strength': displacement,
                            'timestamp': df.index[j]
                        })
                        break
            
            # Bearish displacement - look for last bullish candle
            elif curr_close < prev_close:
                for j in range(i-1, max(i-lookback, 0), -1):
                    if df['close'].iloc[j] > df['open'].iloc[j]:  # Bullish candle
                        order_blocks.append({
                            'type': 'bearish_ob',
                            'start_idx': j,
                            'end_idx': i,
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'strength': displacement,
                            'timestamp': df.index[j]
                        })
                        break
    
    return order_blocks

def detect_fair_value_gaps(df):
    """
    Detect Fair Value Gaps (FVG) - 3 candle pattern with gap
    
    Returns:
        List of dicts with {type, start_idx, end_idx, gap_high, gap_low}
    """
    fvgs = []
    
    for i in range(2, len(df)):
        candle1_high = df['high'].iloc[i-2]
        candle1_low = df['low'].iloc[i-2]
        candle3_high = df['high'].iloc[i]
        candle3_low = df['low'].iloc[i]
        
        # Bullish FVG: gap between candle 1 high and candle 3 low
        if candle3_low > candle1_high:
            fvgs.append({
                'type': 'bullish_fvg',
                'start_idx': i-2,
                'end_idx': i,
                'gap_high': candle3_low,
                'gap_low': candle1_high,
                'timestamp': df.index[i-2]
            })
        
        # Bearish FVG: gap between candle 1 low and candle 3 high
        elif candle3_high < candle1_low:
            fvgs.append({
                'type': 'bearish_fvg',
                'start_idx': i-2,
                'end_idx': i,
                'gap_high': candle1_low,
                'gap_low': candle3_high,
                'timestamp': df.index[i-2]
            })
    
    return fvgs

def detect_liquidity_sweeps(df, lookback=50, sweep_threshold=0.001):
    """
    Detect Liquidity Sweeps - price sweeps high/low then reverses
    
    Returns:
        List of dicts with {type, idx, price, reversal}
    """
    sweeps = []
    
    for i in range(lookback, len(df) - 1):
        # Find recent high/low
        recent_high = df['high'].iloc[i-lookback:i].max()
        recent_low = df['low'].iloc[i-lookback:i].min()
        
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        next_close = df['close'].iloc[i+1]
        curr_close = df['close'].iloc[i]
        
        # Sweep high then drop (bearish)
        if curr_high > recent_high * (1 + sweep_threshold):
            if next_close < curr_close:
                sweeps.append({
                    'type': 'high_sweep',
                    'idx': i,
                    'price': curr_high,
                    'reversal': 'bearish',
                    'timestamp': df.index[i]
                })
        
        # Sweep low then rally (bullish)
        if curr_low < recent_low * (1 - sweep_threshold):
            if next_close > curr_close:
                sweeps.append({
                    'type': 'low_sweep',
                    'idx': i,
                    'price': curr_low,
                    'reversal': 'bullish',
                    'timestamp': df.index[i]
                })
    
    return sweeps

def detect_market_structure_shift(df, swing_length=5):
    """
    Detect Market Structure Shifts (MSS) and Break of Structure (BOS)
    
    Returns:
        List of dicts with {type, idx, price, structure_type}
    """
    structure_shifts = []
    swing_highs = []
    swing_lows = []
    
    # Find swing highs and lows
    for i in range(swing_length, len(df) - swing_length):
        # Swing high
        if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
            swing_highs.append({'idx': i, 'price': df['high'].iloc[i]})
        
        # Swing low
        if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
            swing_lows.append({'idx': i, 'price': df['low'].iloc[i]})
    
    # Detect structure breaks
    for i in range(len(df)):
        curr_price = df['close'].iloc[i]
        
        # Check if recent swing high broken (bullish BOS/continuation)
        for sh in swing_highs:
            if sh['idx'] < i and curr_price > sh['price']:
                structure_shifts.append({
                    'type': 'bos',
                    'direction': 'bullish',
                    'idx': i,
                    'price': curr_price,
                    'broken_level': sh['price'],
                    'timestamp': df.index[i]
                })
                break
        
        # Check if recent swing low broken (bearish BOS/continuation)
        for sl in swing_lows:
            if sl['idx'] < i and curr_price < sl['price']:
                structure_shifts.append({
                    'type': 'bos',
                    'direction': 'bearish',
                    'idx': i,
                    'price': curr_price,
                    'broken_level': sl['price'],
                    'timestamp': df.index[i]
                })
                break
    
    return structure_shifts

def calculate_ote_levels(high, low):
    """
    Calculate Optimal Trade Entry levels (Fibonacci retracements)
    
    Returns:
        Dict with OTE levels
    """
    diff = high - low
    
    return {
        '62%': low + (diff * 0.62),
        '70.5%': low + (diff * 0.705),
        '79%': low + (diff * 0.79),
        '50%': low + (diff * 0.50)
    }

def detect_displacement(df, lookback=10, threshold=0.02):
    """
    Detect Displacement - strong directional moves
    
    Returns:
        List of dicts with {type, idx, magnitude, strength}
    """
    displacements = []
    
    for i in range(lookback, len(df)):
        # Calculate average candle size
        avg_range = df['high'].iloc[i-lookback:i].sub(df['low'].iloc[i-lookback:i]).mean()
        
        curr_range = df['high'].iloc[i] - df['low'].iloc[i]
        body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
        
        # Strong move with large body
        if curr_range > avg_range * 1.5 and body_size / curr_range > 0.7:
            price_change = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
            
            if abs(price_change) > threshold:
                displacements.append({
                    'type': 'bullish' if price_change > 0 else 'bearish',
                    'idx': i,
                    'magnitude': price_change,
                    'strength': body_size / avg_range,
                    'timestamp': df.index[i]
                })
    
    return displacements

def detect_bpr(df, lookback=20, tolerance=0.005):
    """
    Detect Balanced Price Range - consolidation zones
    
    Returns:
        List of dicts with {start_idx, end_idx, high, low}
    """
    bprs = []
    
    for i in range(lookback, len(df)):
        window = df.iloc[i-lookback:i]
        high_range = window['high'].max()
        low_range = window['low'].min()
        
        # Check if highs and lows are relatively equal
        high_std = window['high'].std()
        low_std = window['low'].std()
        
        if high_std / high_range < tolerance and low_std / low_range < tolerance:
            bprs.append({
                'start_idx': i-lookback,
                'end_idx': i,
                'high': high_range,
                'low': low_range,
                'timestamp': df.index[i-lookback]
            })
    
    return bprs

def detect_volume_imbalance(df):
    """
    Detect Volume Imbalance - single candles with no overlap
    
    Returns:
        List of dicts with {type, idx, gap_high, gap_low}
    """
    imbalances = []
    
    for i in range(1, len(df) - 1):
        prev_high = df['high'].iloc[i-1]
        prev_low = df['low'].iloc[i-1]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        next_high = df['high'].iloc[i+1]
        next_low = df['low'].iloc[i+1]
        
        # Bullish imbalance: current candle doesn't overlap with previous or next
        if curr_low > prev_high and curr_low > next_high:
            imbalances.append({
                'type': 'bullish_imbalance',
                'idx': i,
                'gap_high': curr_low,
                'gap_low': max(prev_high, next_high),
                'timestamp': df.index[i]
            })
        
        # Bearish imbalance
        elif curr_high < prev_low and curr_high < next_low:
            imbalances.append({
                'type': 'bearish_imbalance',
                'idx': i,
                'gap_high': min(prev_low, next_low),
                'gap_low': curr_high,
                'timestamp': df.index[i]
            })
    
    return imbalances

def get_all_ict_indicators(df):
    """
    Run all ICT detection algorithms and return results
    
    Returns:
        Dict with all ICT indicators
    """
    return {
        'order_blocks': detect_order_blocks(df),
        'fair_value_gaps': detect_fair_value_gaps(df),
        'liquidity_sweeps': detect_liquidity_sweeps(df),
        'market_structure': detect_market_structure_shift(df),
        'displacements': detect_displacement(df),
        'bpr': detect_bpr(df),
        'volume_imbalances': detect_volume_imbalance(df)
    }
