"""
Signal Generation Module
Aggregates all ICT strategies to provide trading signals
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ict_strategies import get_all_ict_indicators, calculate_ote_levels

def filter_recent_zones(zones, current_idx, lookback=50):
    """Filter zones that are still relevant (recent)"""
    if not zones:
        return []
    return [z for z in zones if current_idx - z.get('idx', z.get('start_idx', 0)) <= lookback]

def check_price_near_zone(current_price, zone_high, zone_low, tolerance=0.02):
    """Check if current price is near a zone"""
    zone_range = zone_high - zone_low
    buffer = zone_range * tolerance if zone_range > 0 else current_price * tolerance
    
    return (current_price >= zone_low - buffer and 
            current_price <= zone_high + buffer)

def generate_signal(df, lookback_days=60, htf_df=None):
    """
    Generate trading signal based on ICT strategies with WEIGHTED CONFLUENCE
    
    New system uses proper ICT confluence weighting:
    - Order Block + OTE + Kill Zone = 12 points
    - CHOCH + Liquidity Sweep = 10 points
    - FVG in Premium/Discount = 9 points
    - Etc.
    
    Confidence tiers:
    - 0-5 points: NEUTRAL (0-30%)
    - 6-12 points: WEAK (30-60%)
    - 13-20 points: MODERATE (60-80%)
    - 21+ points: STRONG (80-100%)
    
    Args:
        df: Current timeframe dataframe
        lookback_days: Days to look back for patterns
        htf_df: Higher timeframe dataframe (optional, for multi-TF confirmation)
    
    Returns:
        Dict with signal, confidence, reasoning, zones, and levels
    """
    if df is None or len(df) < 50:
        return {
            'signal': 'NEUTRAL',
            'confidence': 0,
            'reasoning': ['Insufficient data'],
            'active_zones': {},
            'entry_levels': {},
            'current_price': 0
        }
    
    # Import advanced ICT functions
    from ict_advanced import (
        is_in_kill_zone, detect_choch, calculate_premium_discount_zone,
        get_power_of_3_phase, get_htf_bias
    )
    
    # Get all ICT indicators
    indicators = get_all_ict_indicators(df)
    
    current_idx = len(df) - 1
    current_price = df['close'].iloc[-1]
    current_timestamp = df.index[-1]
    
    # Initialize scoring
    bullish_points = 0
    bearish_points = 0
    reasoning = []
    active_zones = {}
    confluence_details = []  # Track what contributed points
    
    # =================================================================
    # 1. KILL ZONE CHECK (Critical - affects all signals)
    # =================================================================
    in_kill_zone, zone_name, kz_weight = is_in_kill_zone(current_timestamp, return_zone=True)
    
    if in_kill_zone:
        reasoning.append(f"⏰ Inside {zone_name.replace('_', ' ')} Kill Zone")
        if zone_name == 'NEW_YORK_AM':
            reasoning.append("   → PRIME TIME for ICT setups (7-10 AM EST)")
    else:
        reasoning.append(f"⚠️ Outside kill zones (current weight: {kz_weight:.0%})")
        reasoning.append("   → Lower probability - institutional activity is minimal")
    
    # =================================================================
    # 2. PREMIUM/DISCOUNT ZONE (Critical - filters bad trades)
    # =================================================================
    pd_zone = calculate_premium_discount_zone(df, lookback=lookback_days)
    zone = pd_zone['zone']
    zone_position = pd_zone['price_position']
    
    reasoning.append(f"📍 Price in {pd_zone['detailed_zone']} zone ({zone_position:.1%} of range)")
    
    # =================================================================
    # 3. POWER OF 3 PHASE
    # =================================================================
    p3_phase = get_power_of_3_phase(current_timestamp)
    reasoning.append(f"📊 {p3_phase['phase']} phase - {p3_phase['description']}")
    
    # =================================================================
    # 3.5. HIGHER TIMEFRAME BIAS (Multi-TF confirmation)
    # =================================================================
    htf_bias_info = {'bias': 'NEUTRAL', 'strength': 0, 'reasoning': 'No HTF data'}
    htf_adjustment = 0
    
    if htf_df is not None:
        htf_bias_info = get_htf_bias(htf_df)
        htf_bias = htf_bias_info['bias']
        
        reasoning.append(f"📈 HTF Bias: {htf_bias} ({htf_bias_info['strength']}%)")
        reasoning.append(f"   → {htf_bias_info['reasoning']}")
        
        # Will apply htf_adjustment after calculating signal points
    else:
        reasoning.append("📈 HTF Bias: Not available")
    
    # =================================================================
    # 4. CHOCH DETECTION (High priority for reversals)
    # =================================================================
    choch_signals = detect_choch(df, lookback=50)
    recent_choch = [c for c in choch_signals if current_idx - c['idx'] <= 10]
    
    for choch in recent_choch[-2:]:  # Last 2 CHOCH
        if choch['direction'] == 'bullish':
            points = 10  # CHOCH is high value
            bullish_points += points
            reasoning.append(f"🔄 Bullish CHOCH detected (reversal signal)")
            confluence_details.append(('CHOCH_BULLISH', points))
        elif choch['direction'] == 'bearish':
            points = 10
            bearish_points += points
            reasoning.append(f"🔄 Bearish CHOCH detected (reversal signal)")
            confluence_details.append(('CHOCH_BEARISH', points))
    
    # =================================================================
    # 5. ORDER BLOCKS (Tier 1 - Highest Priority)
    # =================================================================
    recent_obs = filter_recent_zones(indicators['order_blocks'], current_idx, lookback=lookback_days)
    bullish_obs = [ob for ob in recent_obs if ob['type'] == 'bullish_ob']
    bearish_obs = [ob for ob in recent_obs if ob['type'] == 'bearish_ob']
    
    # Calculate OTE levels
    swing_high = df['high'].iloc[-lookback_days:].max()
    swing_low = df['low'].iloc[-lookback_days:].min()
    ote_levels = calculate_ote_levels(swing_high, swing_low)
    
    # Check bullish OBs
    for ob in bullish_obs[:2]:  # Top 2 recent OBs
        if check_price_near_zone(current_price, ob['high'], ob['low']):
            # Check if at OTE level
            at_ote = any(abs(current_price - level) / current_price < 0.015 
                        for level in ote_levels.values())
            
            if at_ote and in_kill_zone:
                points = 12  # MAXIMUM confluence
                bullish_points += points
                reasoning.append(f"🟩 Bullish Order Block at OTE in Kill Zone (${ob['low']:.2f}-${ob['high']:.2f})")
                confluence_details.append(('OB_OTE_KILLZONE', points))
            elif at_ote:
                points = 9
                bullish_points += points
                reasoning.append(f"🟩 Bullish Order Block at OTE level")
                confluence_details.append(('OB_OTE', points))
            else:
                points = 6
                bullish_points += points
                reasoning.append(f"🟩 Bullish Order Block (${ob['low']:.2f}-${ob['high']:.2f})")
                confluence_details.append(('OB_BULLISH', points))
            
            active_zones['bullish_ob'] = active_zones.get('bullish_ob', []) + [ob]
            break
    
    # Check bearish OBs
    for ob in bearish_obs[:2]:
        if check_price_near_zone(current_price, ob['high'], ob['low']):
            at_ote = any(abs(current_price - level) / current_price < 0.015 
                        for level in ote_levels.values())
            
            if at_ote and in_kill_zone:
                points = 12
                bearish_points += points
                reasoning.append(f"🟥 Bearish Order Block at OTE in Kill Zone (${ob['low']:.2f}-${ob['high']:.2f})")
                confluence_details.append(('OB_OTE_KILLZONE_BEAR', points))
            elif at_ote:
                points = 9
                bearish_points += points
                reasoning.append(f"🟥 Bearish Order Block at OTE level")
                confluence_details.append(('OB_OTE_BEAR', points))
            else:
                points = 6
                bearish_points += points
                reasoning.append(f"🟥 Bearish Order Block (${ob['low']:.2f}-${ob['high']:.2f})")
                confluence_details.append(('OB_BEARISH', points))
            
            active_zones['bearish_ob'] = active_zones.get('bearish_ob', []) + [ob]
            break
    
    # =================================================================
    # 6. FAIR VALUE GAPS (Tier 2 - Strong in P/D zones)
    # =================================================================
    recent_fvgs = filter_recent_zones(indicators['fair_value_gaps'], current_idx, lookback=lookback_days)
    bullish_fvgs = [fvg for fvg in recent_fvgs if fvg['type'] == 'bullish_fvg']
    bearish_fvgs = [fvg for fvg in recent_fvgs if fvg['type'] == 'bearish_fvg']
    
    for fvg in bullish_fvgs[:2]:
        if current_price < fvg['gap_high'] and current_price > fvg['gap_low'] * 0.95:
            # FVG in discount zone = high value
            if zone == 'DISCOUNT':
                points = 9
                bullish_points += points
                reasoning.append(f"⬆️ Bullish FVG in DISCOUNT zone (${fvg['gap_low']:.2f}-${fvg['gap_high']:.2f})")
                confluence_details.append(('FVG_DISCOUNT', points))
            else:
                points = 4
                bullish_points += points
                reasoning.append(f"⬆️ Bullish FVG (${fvg['gap_low']:.2f}-${fvg['gap_high']:.2f})")
                confluence_details.append(('FVG_BULLISH', points))
            
            active_zones['bullish_fvg'] = active_zones.get('bullish_fvg', []) + [fvg]
            break
    
    for fvg in bearish_fvgs[:2]:
        if current_price > fvg['gap_low'] and current_price < fvg['gap_high'] * 1.05:
            if zone == 'PREMIUM':
                points = 9
                bearish_points += points
                reasoning.append(f"⬇️ Bearish FVG in PREMIUM zone (${fvg['gap_low']:.2f}-${fvg['gap_high']:.2f})")
                confluence_details.append(('FVG_PREMIUM', points))
            else:
                points = 4
                bearish_points += points
                reasoning.append(f"⬇️ Bearish FVG (${fvg['gap_low']:.2f}-${fvg['gap_high']:.2f})")
                confluence_details.append(('FVG_BEARISH', points))
            
            active_zones['bearish_fvg'] = active_zones.get('bearish_fvg', []) + [fvg]
            break
    
    # =================================================================
    # 7. LIQUIDITY SWEEPS (Tier 2 - Reversal confirming)
    # =================================================================
    recent_sweeps = filter_recent_zones(indicators['liquidity_sweeps'], current_idx, lookback=15)
    for sweep in recent_sweeps[-2:]:
        if sweep['reversal'] == 'bullish':
            points = 6
            bullish_points += points
            reasoning.append(f"💧 Bullish liquidity sweep at ${sweep['price']:.2f}")
            confluence_details.append(('LIQ_SWEEP_BULL', points))
        elif sweep['reversal'] == 'bearish':
            points = 6
            bearish_points += points
            reasoning.append(f"💧 Bearish liquidity sweep at ${sweep['price']:.2f}")
            confluence_details.append(('LIQ_SWEEP_BEAR', points))
    
    # =================================================================
    # 8. MARKET STRUCTURE (BOS - Tier 3, lower than CHOCH)
    # =================================================================
    recent_structure = filter_recent_zones(indicators['market_structure'], current_idx, lookback=30)
    bullish_bos = [s for s in recent_structure if s.get('direction') == 'bullish']
    bearish_bos = [s for s in recent_structure if s.get('direction') == 'bearish']
    
    if len(bullish_bos) > len(bearish_bos):
        points = 4
        bullish_points += points
        reasoning.append("📈 Bullish market structure (BOS)")
        confluence_details.append(('BOS_BULLISH', points))
    elif len(bearish_bos) > len(bullish_bos):
        points = 4
        bearish_points += points
        reasoning.append("📉 Bearish market structure (BOS)")
        confluence_details.append(('BOS_BEARISH', points))
    
    # =================================================================
    # 9. DISPLACEMENT (Tier 2 - Institutional move)
    # =================================================================
    recent_displacements = filter_recent_zones(indicators['displacements'], current_idx, lookback=10)
    for disp in recent_displacements[-1:]:  # Most recent
        if disp['type'] == 'bullish':
            points = 7
            bullish_points += points
            reasoning.append(f"🚀 Bullish displacement (strength: {disp['strength']:.2f})")
            confluence_details.append(('DISPLACEMENT_BULL', points))
        elif disp['type'] == 'bearish':
            points = 7
            bearish_points += points
            reasoning.append(f"💥 Bearish displacement (strength: {disp['strength']:.2f})")
            confluence_details.append(('DISPLACEMENT_BEAR', points))
    
    # =================================================================
    # 10. APPLY PENALTIES & ADJUSTMENTS
    # =================================================================
    # Kill zone weight
    bullish_points *= kz_weight
    bearish_points *= kz_weight
    
    # Premium/Discount zone penalties
    # CRITICAL: Don't buy in premium, don't sell in discount
    if zone == 'PREMIUM' and bullish_points > 0:
        penalty = bullish_points * 0.3  # 30% penalty
        bullish_points -= penalty
        reasoning.append(f"⚠️ LONG in PREMIUM zone - reduced confidence by {penalty:.1f} points")
    
    if zone == 'DISCOUNT' and bearish_points > 0:
        penalty = bearish_points * 0.3
        bearish_points -= penalty
        reasoning.append(f"⚠️ SHORT in DISCOUNT zone - reduced confidence by {penalty:.1f} points")
    
    # HTF bias adjustments (Multi-timeframe confirmation)
    if htf_df is not None:
        htf_bias = htf_bias_info['bias']
        
        # Determine signal direction first (preliminary)
        if bullish_points > bearish_points and bullish_points >= 5:
            signal_direction = 'LONG'
        elif bearish_points > bullish_points and bearish_points >= 5:
            signal_direction = 'SHORT'
        else:
            signal_direction = 'NEUTRAL'
        
        # Apply HTF adjustments based on alignment
        if signal_direction == 'LONG':
            if htf_bias == 'BULLISH':
                adjustment = bullish_points * 0.1  # +10% bonus
                bullish_points += adjustment
                reasoning.append(f"✅ HTF ALIGNED with LONG - bonus +{adjustment:.1f} points")
            elif htf_bias == 'BEARISH':
                penalty = bullish_points * 0.2  # -20% penalty
                bullish_points -= penalty
                reasoning.append(f"❌ HTF AGAINST LONG (counter-trend) - penalty -{penalty:.1f} points")
        
        elif signal_direction == 'SHORT':
            if htf_bias == 'BEARISH':
                adjustment = bearish_points * 0.1  # +10% bonus
                bearish_points += adjustment
                reasoning.append(f"✅ HTF ALIGNED with SHORT - bonus +{adjustment:.1f} points")
            elif htf_bias == 'BULLISH':
                penalty = bearish_points * 0.2  # -20% penalty
                bearish_points -= penalty
                reasoning.append(f"❌ HTF AGAINST SHORT (counter-trend) - penalty -{penalty:.1f} points")
    
    # =================================================================
    # 11. CALCULATE FINAL SIGNAL & CONFIDENCE
    # =================================================================
    total_points = bullish_points + bearish_points
    
    # Determine signal direction
    if bullish_points > bearish_points and bullish_points >= 5:
        signal = 'LONG'
        signal_points = bullish_points
    elif bearish_points > bullish_points and bearish_points >= 5:
        signal = 'SHORT'
        signal_points = bearish_points
    else:
        signal = 'NEUTRAL'
        signal_points = 0
        reasoning.append("🤷 Insufficient confluence - no clear signal")
    
    # Calculate confidence based on points
    if signal_points >= 21:
        confidence = min(100, 80 + int(signal_points - 21))  # 80-100%
    elif signal_points >= 13:
        confidence = 60 + int((signal_points - 13) * 2.5)  # 60-80%
    elif signal_points >= 6:
        confidence = 30 + int((signal_points - 6) * 5)  # 30-60%
    else:
        confidence = min(30, int(signal_points * 6))  # 0-30%
    
    # Add summary
    reasoning.insert(0, f"💯 Total Confluence: {signal_points:.1f} points → {confidence}% confidence")
    
    # Calculate entry/exit levels (same as before)
    entry_levels = {}
    if signal == 'LONG':
        if 'bullish_ob' in active_zones and active_zones['bullish_ob']:
            entry_levels['entry'] = active_zones['bullish_ob'][0]['low']
            entry_levels['stop_loss'] = entry_levels['entry'] * 0.98
            entry_levels['take_profit1'] = entry_levels['entry'] * 1.03
            entry_levels['take_profit2'] = entry_levels['entry'] * 1.05
        else:
            entry_levels['entry'] = current_price
            entry_levels['stop_loss'] = swing_low
            entry_levels['take_profit1'] = current_price * 1.03
            entry_levels['take_profit2'] = swing_high
    elif signal == 'SHORT':
        if 'bearish_ob' in active_zones and active_zones['bearish_ob']:
            entry_levels['entry'] = active_zones['bearish_ob'][0]['high']
            entry_levels['stop_loss'] = entry_levels['entry'] * 1.02
            entry_levels['take_profit1'] = entry_levels['entry'] * 0.97
            entry_levels['take_profit2'] = entry_levels['entry'] * 0.95
        else:
            entry_levels['entry'] = current_price
            entry_levels['stop_loss'] = swing_high
            entry_levels['take_profit1'] = current_price * 0.97
            entry_levels['take_profit2'] = swing_low
    
    return {
        'signal': signal,
        'confidence': confidence,
        'reasoning': reasoning,
        'active_zones': active_zones,
        'entry_levels': entry_levels,
        'current_price': current_price,
        'ote_levels': ote_levels,
        'bullish_score': bullish_points,
        'bearish_score': bearish_points,
        'all_indicators': indicators,
        'kill_zone': zone_name if in_kill_zone else 'OUTSIDE',
        'premium_discount': pd_zone,
        'power_of_3': p3_phase['phase'],
        'htf_bias': htf_bias_info,  # Multi-timeframe bias
        'confluence_breakdown': confluence_details  # For debugging
    }

def backtest_signal(df, target_date, forward_periods=5):
    """
    Generate signal for a historical date and check outcome
    
    Args:
        df: Full historical dataframe
        target_date: Date to generate signal for (datetime.date or pd.Timestamp)
        forward_periods: Periods (candles) forward to check outcome
    
    Returns:
        Dict with signal and actual outcome
    """
    try:
        # Convert target_date to pd.Timestamp
        if not isinstance(target_date, pd.Timestamp):
            target_date = pd.Timestamp(target_date)
        
        # Match the timezone of the DataFrame index if it has one
        if df.index.tz is not None:
            if target_date.tz is None:
                target_date = target_date.tz_localize(df.index.tz)
            else:
                target_date = target_date.tz_convert(df.index.tz)
        
        # For hourly data, find the closest timestamp on or after the target date
        # For daily data, this will match the exact date
        target_idx = df.index.get_indexer([target_date], method='nearest')[0]
        
        # Require minimum data points (adjust based on available data)
        min_required = min(50, len(df) // 3)  # At least 1/3 of data as history, max 50
        
        if target_idx < min_required or target_idx >= len(df) - forward_periods:
            return None
        
        # Get data up to target date
        historical_df = df.iloc[:target_idx+1].copy()
        
        # Generate signal
        signal_result = generate_signal(historical_df)
        
        # Get future prices to check outcome
        future_prices = df['close'].iloc[target_idx+1:target_idx+forward_periods+1]
        
        if len(future_prices) == 0:
            return None
            
        signal_price = df['close'].iloc[target_idx]
        
        # Calculate outcome
        max_future_price = future_prices.max()
        min_future_price = future_prices.min()
        end_price = future_prices.iloc[-1]
        
        price_change_pct = ((end_price - signal_price) / signal_price) * 100
        max_gain_pct = ((max_future_price - signal_price) / signal_price) * 100
        max_loss_pct = ((min_future_price - signal_price) / signal_price) * 100
        
        # Determine if signal was correct
        # Using 0.05% (5 basis points) threshold - realistic for short timeframes
        # Even small moves in the right direction should count as "correct"
        correct = False
        if signal_result['signal'] == 'LONG':
            correct = price_change_pct > 0.05  # Profit > 0.05%
        elif signal_result['signal'] == 'SHORT':
            correct = price_change_pct < -0.05  # Profit > 0.05%
        
        return {
            'date': target_date,
            'signal': signal_result['signal'],
            'confidence': signal_result['confidence'],
            'reasoning': signal_result['reasoning'],
            'entry_price': signal_price,
            'end_price': end_price,
            'price_change_pct': price_change_pct,
            'max_gain_pct': max_gain_pct,
            'max_loss_pct': max_loss_pct,
            'correct': correct,
            'active_zones': signal_result['active_zones']
        }
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()
        return None
