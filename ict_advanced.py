"""
Advanced ICT Strategy Functions
- Kill Zones
- CHOCH (Change of Character) Detection
- Premium/Discount Zones
- Session Tracking
"""
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# Kill Zone definitions (EST timezone)
KILL_ZONES = {
    'LONDON_KILLZONE': (2, 5),      # 2:00 AM - 5:00 AM EST
    'NEW_YORK_AM': (7, 10),         # 7:00 AM - 10:00 AM EST (⭐ BEST)
    'NEW_YORK_PM': (13, 16),        # 1:00 PM - 4:00 PM EST  
    'ASIAN_SESSION': (20, 24),      # 8:00 PM - 11:59 PM EST
}

KILL_ZONE_WEIGHTS = {
    'NEW_YORK_AM': 1.0,      # Best zone - no penalty
    'LONDON_KILLZONE': 0.9,  # Good zone - minor penalty
    'NEW_YORK_PM': 0.85,     # Decent zone
    'ASIAN_SESSION': 0.7,    # Lower probability
    'OUTSIDE': 0.6,          # Significant penalty
}

def is_in_kill_zone(timestamp, return_zone=False):
    """
    Check if timestamp is within a kill zone
    
    Args:
        timestamp: pandas Timestamp (timezone aware or naive)
        return_zone: If True, return tuple (is_in_zone, zone_name, weight)
        
    Returns:
        If return_zone=False: Boolean
        If return_zone=True: Tuple (is_in_zone, zone_name, weight)
    """
    # Convert to EST timezone
    est = pytz.timezone('US/Eastern')
    if timestamp.tz is None:
        # Assume UTC if no timezone
        timestamp = pytz.UTC.localize(timestamp)
    
    est_time = timestamp.astimezone(est)
    hour = est_time.hour
    
    # Check which kill zone we're in
    for zone_name, (start_hour, end_hour) in KILL_ZONES.items():
        if start_hour <= hour < end_hour:
            weight = KILL_ZONE_WEIGHTS[zone_name]
            if return_zone:
                return (True, zone_name, weight)
            return True
    
    # Outside all kill zones
    if return_zone:
        return (False, 'OUTSIDE', KILL_ZONE_WEIGHTS['OUTSIDE'])
    return False

def detect_choch(df, swing_length=5, lookback=50):
    """
    Detect Change of Character (CHOCH) - signals trend exhaustion
    
    CHOCH differs from BOS:
    - BOS = Strong break with continuation
    - CHOCH = Break with weakening momentum (reversal signal)
    
    Returns:
        List of dicts with {type, idx, price, direction, strength}
    """
    choch_signals = []
    swing_highs = []
    swing_lows = []
    
    # Find swing highs and lows
    for i in range(swing_length, min(len(df) - swing_length, lookback)):
        # Swing high
        if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
            swing_highs.append({'idx': i, 'price': df['high'].iloc[i]})
        
        # Swing low
        if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
            swing_lows.append({'idx': i, 'price': df['low'].iloc[i]})
    
    # Look for CHOCH patterns in recent candles
    for i in range(lookback, len(df)):
        curr_close = df['close'].iloc[i]
        
        # Check volume and momentum
        if i >= 5:
            recent_volume = df['volume'].iloc[i-5:i].mean()
            curr_volume = df['volume'].iloc[i]
            volume_decreasing = curr_volume < recent_volume * 0.8
            
            # Price change momentum
            price_momentum = abs(df['close'].iloc[i] - df['close'].iloc[i-3]) / df['close'].iloc[i-3]
            
            # Bullish CHOCH: Broke swing low but failed to continue down
            for sl in swing_lows:
                if sl['idx'] < i - 5 and sl['idx'] > i - lookback:
                    if curr_close < sl['price']:  # Broke below swing low
                        # Check if momentum is weak (this is key difference from BOS)
                        if volume_decreasing or price_momentum < 0.01:
                            # Look ahead to see if it reversed
                            if i < len(df) - 2:
                                next_close = df['close'].iloc[i+1]
                                if next_close > curr_close:  # Price reversed up
                                    choch_signals.append({
                                        'type': 'choch',
                                        'direction': 'bullish',  # Expecting reversal up
                                        'idx': i,
                                        'price': curr_close,
                                        'broken_level': sl['price'],
                                        'strength': 1.0 - price_momentum,  # Weaker = stronger CHOCH
                                        'timestamp': df.index[i]
                                    })
                                    break
            
            # Bearish CHOCH: Broke swing high but failed to continue up
            for sh in swing_highs:
                if sh['idx'] < i - 5 and sh['idx'] > i - lookback:
                    if curr_close > sh['price']:  # Broke above swing high
                        if volume_decreasing or price_momentum < 0.01:
                            if i < len(df) - 2:
                                next_close = df['close'].iloc[i+1]
                                if next_close < curr_close:  # Price reversed down
                                    choch_signals.append({
                                        'type': 'choch',
                                        'direction': 'bearish',  # Expecting reversal down
                                        'idx': i,
                                        'price': curr_close,
                                        'broken_level': sh['price'],
                                        'strength': 1.0 - price_momentum,
                                        'timestamp': df.index[i]
                                    })
                                    break
    
    return choch_signals

def calculate_premium_discount_zone(df, lookback=24):
    """
    Calculate if current price is in premium or discount zone
    
    Premium = Upper 50% of range (expensive, good for selling)
    Discount = Lower 50% of range (cheap, good for buying)
    
    Returns:
        Dict with {zone, range_high, range_low, midpoint, price_position}
    """
    # Use recent high/low for the range
    recent_high = df['high'].iloc[-lookback:].max()
    recent_low = df['low'].iloc[-lookback:].min()
    midpoint = (recent_high + recent_low) / 2
    current_price = df['close'].iloc[-1]
    
    # Calculate where price is in the range (0 = bottom, 1 = top)
    price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
    
    # Determine zone
    if price_position > 0.5:
        zone = 'PREMIUM'  # Good for selling
    else:
        zone = 'DISCOUNT'  # Good for buying
    
    # More granular zones
    if price_position > 0.7:
        detailed_zone = 'EXTREME_PREMIUM'
    elif price_position > 0.5:
        detailed_zone = 'PREMIUM'
    elif price_position < 0.3:
        detailed_zone = 'EXTREME_DISCOUNT'
    else:
        detailed_zone = 'DISCOUNT'
    
    return {
        'zone': zone,
        'detailed_zone': detailed_zone,
        'range_high': recent_high,
        'range_low': recent_low,
        'midpoint': midpoint,
        'price_position': price_position,
        'current_price': current_price
    }

def get_power_of_3_phase(timestamp):
    """
    Determine which Power of 3 phase we're in
    
    Phases (EST):
    - Accumulation: 00:00 - 08:00 (Setup formation, ranging)
    - Manipulation: 08:00 - 11:00 (Liquidity sweeps, false moves)
    - Distribution: 11:00 - 16:00 (True institutional direction)
    - After Hours: 16:00 - 23:59 (Low activity)
    
    Returns:
        Dict with {phase, hour, description}
    """
    est = pytz.timezone('US/Eastern')
    if timestamp.tz is None:
        timestamp = pytz.UTC.localize(timestamp)
    
    est_time = timestamp.astimezone(est)
    hour = est_time.hour
    
    if 0 <= hour < 8:
        return {
            'phase': 'ACCUMULATION',
            'hour': hour,
            'description': 'Consolidation & Setup Formation',
            'trade_recommendation': 'WAIT - Mark key levels'
        }
    elif 8 <= hour < 11:
        return {
            'phase': 'MANIPULATION',
            'hour': hour,
            'description': 'Liquidity Sweeps & False Moves',
            'trade_recommendation': 'CAUTIOUS - Watch for reversals'
        }
    elif 11 <= hour < 16:
        return {
            'phase': 'DISTRIBUTION',
            'hour': hour,
            'description': 'True Institutional Direction',
            'trade_recommendation': 'ACTIVE - Best time to trade'
        }
    else:
        return {
            'phase': 'AFTER_HOURS',
            'hour': hour,
            'description': 'Low Activity Period',
            'trade_recommendation': 'AVOID - Low liquidity'
        }

def detect_session_liquidity(df):
    """
    Track high/low liquidity levels from different trading sessions
    
    Sessions:
    - Asian: 7 PM - 12 AM EST
    - London: 2 AM - 10 AM EST
    - New York: 7 AM - 4 PM EST
    
    Returns:
        Dict with session highs/lows
    """
    est = pytz.timezone('US/Eastern')
    
    session_levels = {
        'asian': {'high': None, 'low': None, 'swept': False},
        'london': {'high': None, 'low': None, 'swept': False},
        'newyork': {'high': None, 'low': None, 'swept': False}
    }
    
    for i, timestamp in enumerate(df.index):
        if timestamp.tz is None:
            timestamp = pytz.UTC.localize(timestamp)
        est_time = timestamp.astimezone(est)
        hour = est_time.hour
        
        price_high = df['high'].iloc[i]
        price_low = df['low'].iloc[i]
        
        # Asian session (19:00 - 23:59 EST)
        if 19 <= hour <= 23:
            if session_levels['asian']['high'] is None or price_high > session_levels['asian']['high']:
                session_levels['asian']['high'] = price_high
            if session_levels['asian']['low'] is None or price_low < session_levels['asian']['low']:
                session_levels['asian']['low'] = price_low
        
        # London session (2:00 - 10:00 EST)
        elif 2 <= hour < 10:
            if session_levels['london']['high'] is None or price_high > session_levels['london']['high']:
                session_levels['london']['high'] = price_high
            if session_levels['london']['low'] is None or price_low < session_levels['london']['low']:
                session_levels['london']['low'] = price_low
        
        # New York session (7:00 - 16:00 EST)
        elif 7 <= hour < 16:
            if session_levels['newyork']['high'] is None or price_high > session_levels['newyork']['high']:
                session_levels['newyork']['high'] = price_high
            if session_levels['newyork']['low'] is None or price_low < session_levels['newyork']['low']:
                session_levels['newyork']['low'] = price_low
    
    return session_levels

def get_htf_bias(df, current_timeframe='1h'):
    """
    Determine higher timeframe bias for multi-timeframe confirmation
    
    Analyzes recent market structure on the current timeframe to determine
    if price is bullish or bearish trending.
    
    Args:
        df: DataFrame of higher timeframe data
        current_timeframe: Current trading timeframe (for context)
        
    Returns:
        Dict with {bias, strength, reasoning}
    """
    if df is None or len(df) < 20:
        return {
            'bias': 'NEUTRAL',
            'strength': 0,
            'reasoning': 'Insufficient HTF data'
        }
    
    # Analyze recent structure
    lookback = min(20, len(df) - 1)
    recent_df = df.iloc[-lookback:]
    
    # Calculate trend strength using highs/lows
    recent_highs = recent_df['high']
    recent_lows = recent_df['low']
    recent_closes = recent_df['close']
    
    # Check for higher highs and higher lows (bullish)
    hh_count = 0
    hl_count = 0
    lh_count = 0
    ll_count = 0
    
    for i in range(5, len(recent_df)):
        current_high = recent_df['high'].iloc[i]
        previous_high = recent_df['high'].iloc[i-5:i].max()
        current_low = recent_df['low'].iloc[i]
        previous_low = recent_df['low'].iloc[i-5:i].min()
        
        if current_high > previous_high:
            hh_count += 1
        if current_low > previous_low:
            hl_count +=1
        if current_high < previous_high:
            lh_count += 1
        if current_low < previous_low:
            ll_count += 1
    
    # Determine bias
    bullish_structure = (hh_count + hl_count)
    bearish_structure = (lh_count + ll_count)
    
    # Also check price relative to moving averages
    ma_20 = recent_closes.rolling(window=min(20, len(recent_closes))).mean().iloc[-1]
    current_price = recent_closes.iloc[-1]
    
    # Price above MA = bullish, below = bearish
    price_vs_ma = 'BULLISH' if current_price > ma_20 else 'BEARISH'
    
    # Combine structure and MA for final bias
    if bullish_structure > bearish_structure and price_vs_ma == 'BULLISH':
        bias = 'BULLISH'
        strength = min(100, int((bullish_structure / max(bullish_structure + bearish_structure, 1)) * 100))
        reasoning = f"Higher highs/lows forming, price above MA ({strength}% bullish structure)"
    elif bearish_structure > bullish_structure and price_vs_ma == 'BEARISH':
        bias = 'BEARISH'
        strength = min(100, int((bearish_structure / max(bullish_structure + bearish_structure, 1)) * 100))
        reasoning = f"Lower highs/lows forming, price below MA ({strength}% bearish structure)"
    else:
        bias = 'NEUTRAL'
        strength = 50
        reasoning = "Mixed signals - no clear HTF trend"
    
    return {
        'bias': bias,
        'strength': strength,
        'reasoning': reasoning,
        'price_vs_ma': 'above' if current_price > ma_20 else 'below'
    }

