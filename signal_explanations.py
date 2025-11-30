"""
Detailed signal explanations for ICT trading strategies
"""

def explain_signal_in_detail(reasoning_list, signal_type, confidence):
    """
    Convert technical signal reasoning into detailed, beginner-friendly explanations
    
    Args:
        reasoning_list: List of technical reasons from signal generator
        signal_type: LONG, SHORT, or NEUTRAL
        confidence: Confidence percentage
        
    Returns:
        List of detailed, easy-to-understand explanations
    """
    detailed_explanations = []
    
    # Add opening context
    if signal_type == "LONG":
        detailed_explanations.append(f"📈 **{confidence}% confident this is a good time to BUY (go LONG)**")
        detailed_explanations.append("")
        detailed_explanations.append("**Here's why in simple terms:**")
    elif signal_type == "SHORT":
        detailed_explanations.append(f"📉 **{confidence}% confident this is a good time to SELL (go SHORT)**")
        detailed_explanations.append("")
        detailed_explanations.append("**Here's why in simple terms:**")
    else:
        detailed_explanations.append(f"😐 **No clear signal right now ({confidence}% confidence)**")
        detailed_explanations.append("")
        detailed_explanations.append("**Why we're waiting:**")
    
    detailed_explanations.append("")
    
    # Translate each technical reason
    for i, reason in enumerate(reasoning_list, 1):
        explanation = f"**{i}.** "
        
        # Order Blocks
        if "Order Block" in reason:
            if "Bullish" in reason:
                explanation += "🟩 **BIG BUYERS stepped in here before**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Think of this like a 'support zone' where smart money bought heavily\n"
                explanation += "   • When price comes back here, those big buyers often return\n"
                explanation += "   • Strong institutional buying pressure = price likely to bounce UP"
            else:  # Bearish
                explanation += "🟥 **BIG SELLERS stepped in here before**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • This is a 'resistance zone' where institutions sold aggressively\n"
                explanation += "   • Price returning here often triggers more selling\n"
                explanation += "   • Strong institutional selling pressure = price likely to drop DOWN"
        
        # Fair Value Gaps (FVG)
        elif "FVG" in reason:
            if "Bullish" in reason:
                explanation += "⬆️ **PRICE GAP needs to be filled (bullish)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price jumped up so fast it left a 'gap' - unfair pricing\n"
                explanation += "   • Markets love 'fair value' - gaps usually get filled\n"
                explanation += "   • This gap acts like a magnet pulling price UP to fill it"
            else:  # Bearish
                explanation += "⬇️ **PRICE GAP needs to be filled (bearish)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price dropped so fast it left a 'gap' - unfair pricing\n"
                explanation += "   • Markets seek balance - these gaps tend to get filled\n"
                explanation += "   • This gap acts like a magnet pulling price DOWN"
        
        # Liquidity Sweeps
        elif "liquidity sweep" in reason.lower():
            if "bullish" in reason.lower():
                explanation += "💧 **LIQUIDITY GRAB happened (bullish reversal)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Smart money 'faked out' traders by briefly dropping price\n"
                explanation += "   • This triggered stop losses (grabbed liquidity)\n"
                explanation += "   • Now they reverse and push price UP - classic trap for amateurs"
            else:  # Bearish
                explanation += "💧 **LIQUIDITY GRAB happened (bearish reversal)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Smart money 'faked out' traders by briefly spiking price\n"
                explanation += "   • This triggered buy stops (grabbed liquidity)\n"
                explanation += "   • Now they reverse and push price DOWN - trap set and sprung"
        
        # Market Structure
        elif "market structure" in reason.lower() or "Break of Structure" in reason:
            if "Bullish" in reason:
                explanation += "📊 **TREND CHANGED to BULLISH**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price broke above previous resistance - major shift\n"
                explanation += "   • Higher highs and higher lows forming\n"
                explanation += "   • The 'structure' of the chart now favors buyers"
            else:  # Bearish
                explanation += "📊 **TREND CHANGED to BEARISH**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price broke below previous support - major shift\n"
                explanation += "   • Lower highs and lower lows forming\n"
                explanation += "   • The 'structure' of the chart now favors sellers"
        
        # Displacement
        elif "displacement" in reason.lower():
            if "bullish" in reason.lower():
                explanation += "🚀 **EXPLOSIVE MOVE UP (displacement)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price moved up EXTREMELY fast with strong momentum\n"
                explanation += "   • Shows institutions are aggressively buying\n"
                explanation += "   • This kind of power move usually continues in the same direction"
            else:  # Bearish
                explanation += "💥 **EXPLOSIVE MOVE DOWN (displacement)**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • Price moved down EXTREMELY fast with strong momentum\n"
                explanation += "   • Shows institutions are aggressively selling\n"
                explanation += "   • This kind of power move usually continues in the same direction"
        
        # OTE (Optimal Trade Entry)
        elif "OTE" in reason or "0.62" in reason or "0.705" in reason or "0.79" in reason:
            explanation += "🎯 **PERFECT ENTRY ZONE (Fibonacci sweet spot)**\n"
            explanation += f"   • {reason}\n"
            explanation += "   • Price is at a 'golden ratio' level (62-79% retracement)\n"
            explanation += "   • This is where smart money often enters trades\n"
            explanation += "   • Optimal Trade Entry = highest probability price level"
        
        # Breaker Blocks
        elif "Breaker" in reason:
            if "Bullish" in reason:
                explanation += "🔄 **FAILED RESISTANCE became SUPPORT**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • What was once resistance got broken and flipped\n"
                explanation += "   • Now acts as support - role reversal\n"
                explanation += "   • Very powerful signal when this happens"
            else:  # Bearish
                explanation += "🔄 **FAILED SUPPORT became RESISTANCE**\n"
                explanation += f"   • {reason}\n"
                explanation += "   • What was once support got broken and flipped\n"
                explanation += "   • Now acts as resistance - role reversal\n"
                explanation += "   • Very powerful signal when this happens"
        
        # Volume Imbalance
        elif "Volume Imbalance" in reason or "volume imbalance" in reason.lower():
            explanation += "📊 **UNUSUAL VOLUME PATTERN detected**\n"
            explanation += f"   • {reason}\n"
            explanation += "   • Trading volume shows clear imbalance between buyers/sellers\n"
            explanation += "   • When volume is lopsided, price often continues that direction\n"
            explanation += "   • This confirms the move is real, not just noise"
        
        # Premium/Discount
        elif "Premium" in reason:
            explanation += "💰 **PRICE IN EXPENSIVE ZONE (premium)**\n"
            explanation += f"   • {reason}\n"
            explanation += "   • Price is in the upper range - considered 'expensive'\n"
            explanation += "   • Good for selling, not ideal for buying\n"
            explanation += "   • Smart money often distributes (sells) in premium zones"
        elif "Discount" in reason:
            explanation += "💵 **PRICE IN CHEAP ZONE (discount)**\n"
            explanation += f"   • {reason}\n"
            explanation += "   • Price is in the lower range - considered 'cheap'\n"
            explanation += "   • Good for buying, not ideal for selling\n"
            explanation += "   • Smart money often accumulates (buys) in discount zones"
        
        # Generic fallback for any other reasons
        else:
            explanation += f"📌 {reason}\n"
            explanation += "   • Additional confluence supporting this signal"
        
        detailed_explanations.append(explanation)
    
    # Add closing summary
    detailed_explanations.append("")
    detailed_explanations.append("---")
    detailed_explanations.append("")
    
    if signal_type in ["LONG", "SHORT"]:
        detailed_explanations.append(f"**💡 Bottom Line:** All these factors together give us **{confidence}% confidence** " +
                                    f"that price will move **{'UP ⬆️' if signal_type == 'LONG' else 'DOWN ⬇️'}** soon.")
    else:
        detailed_explanations.append(f"**💡 Bottom Line:** Not enough clear signals right now. Better to wait for a clearer setup.")
    
    return detailed_explanations
