from typing import Dict, Any
import json
import os
from openai import OpenAI
from fastapi import HTTPException

# Initialize OpenAI client
client = None

def get_client():
    global client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    if not client:
        client = OpenAI(api_key=api_key)
    return client

SYSTEM_PROMPT = """You are an expert MQL5 algorithmic trading strategist.
Your task is to analyze the user's natural language description of a trading strategy and convert it into a strict JSON configuration.

Output MUST be a single valid JSON object. Do not include markdown formatting (like ```json).

The JSON object must match this schema for a Trend/Pullback/Breakout EA:

{
    "ea_name": "string (creative name based on strategy)",
    "symbol": "string (e.g. XAUUSD, EURUSD, US30)",
    
    "ema_fast_period": int (default 50),
    "ema_slow_period": int (default 200),
    "use_trend_filter": bool,
    
    "rsi_period": int (default 14),
    "rsi_buy_min": float (30.0),
    "rsi_buy_max": float (40.0),
    "rsi_sell_min": float (60.0),
    "rsi_sell_max": float (70.0),
    "pullback_distance_pips": float,
    
    "risk_percent": float (1.0),
    "risk_reward_ratio": float (2.0),
    "min_sl_pips": float,
    "max_sl_pips": float,
    "use_breakeven": bool,
    "breakeven_trigger_pips": float,
    "breakeven_offset_pips": float,
    
    "use_trailing_stop": bool,
    "trailing_stop_type": "fixed" | "atr" | "step",
    "trailing_start_pips": float,
    "trailing_distance_pips": float,
    "atr_period": int,
    "atr_multiplier": float,
    "step_size_pips": float,
    "step_distance_pips": float,
    
    "use_partial_close": bool,
    "partial_close_percent": float,
    "partial_close_tp1_rr": float,
    "partial_close_tp2_rr": float,
    "move_sl_after_partial": bool,
    
    "max_spread_points": float,
    "use_trading_hours": bool,
    "trading_hour_start": int (0-23),
    "trading_hour_end": int (0-23),
    "use_news_filter": bool
}

Interpret terms like "Aggressive" to mean tighter stops, higher risk, or less filtering.
Interpret "Safe" or "Conservative" to mean trend filters, lower risk, wider confirmation zones.
"""

async def generate_settings_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Call OpenAI to generate strategy settings from a text prompt.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")
        
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cost effective and sufficient
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a strategy settings configuration for: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up if markdown was included despite instructions
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        settings = json.loads(content)
        return settings
        
    except Exception as e:
        print(f"AI Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
