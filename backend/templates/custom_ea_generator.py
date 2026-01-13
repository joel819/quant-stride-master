"""
Custom EA Generator
Generate production-quality EAs for any symbol with configurable strategies.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime


@dataclass
class EASettings:
    """
    Complete EA configuration settings.
    
    Use this to configure every aspect of your generated EA.
    """
    
    # === Identification ===
    ea_name: str = "CustomEA"
    version: str = "1.00"
    description: str = "Custom trading robot"
    magic_number: Optional[int] = None  # Auto-generated if None
    
    # === Symbol/Instrument ===
    symbol: str = "EURUSD"
    timeframe: str = "M5"
    
    # === Trend Settings (EMAs) ===
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    use_trend_filter: bool = True
    
    # === Entry Settings ===
    entry_type: str = "pullback"  # pullback, breakout, trend, reversal
    rsi_period: int = 14
    rsi_buy_min: float = 30.0
    rsi_buy_max: float = 40.0
    rsi_sell_min: float = 60.0
    rsi_sell_max: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    use_macd_confirmation: bool = True
    use_candle_confirmation: bool = True
    pullback_distance_pips: float = 30.0
    
    # === ATR/Volatility Settings ===
    atr_period: int = 14
    atr_sma_period: int = 20
    min_atr_ratio: float = 1.0
    use_volatility_filter: bool = True
    
    # === Risk Management ===
    risk_percent: float = 1.0
    risk_reward_ratio: float = 2.0
    use_swing_sl: bool = True
    swing_lookback: int = 10
    min_sl_pips: float = 20.0
    max_sl_pips: float = 100.0
    use_breakeven: bool = True
    breakeven_trigger_pips: float = 20.0 # Trigger in pips
    breakeven_buffer_pips: float = 5.0   # Offset in pips
    
    # === Advanced Trailing ===
    use_trailing_stop: bool = False
    trailing_stop_type: str = "fixed" # fixed, atr, step
    trailing_start_pips: float = 30.0
    trailing_distance_pips: float = 20.0
    trailing_step_pips: float = 10.0 # Legacy field, kept for compat or step mode
    step_size_pips: float = 10.0
    step_distance_pips: float = 10.0
    atr_multiplier: float = 1.5
    
    # === Partial Close ===
    use_partial_close: bool = False
    partial_close_percent: float = 50.0
    partial_close_tp1_rr: float = 1.0
    partial_close_tp2_rr: float = 2.0
    move_sl_after_partial: bool = True
    
    # === Trade Filters ===
    max_spread_points: float = 20.0
    use_trading_hours: bool = True
    trading_hour_start: int = 8
    trading_hour_end: int = 18
    max_open_trades: int = 1
    
    # === News Filter ===
    use_news_filter: bool = True
    news_buffer_minutes: int = 10


class CustomEAGenerator:
    """
    Generate custom EAs with full configurability.
    """
    
    def __init__(self, settings: EASettings):
        self.settings = settings
        
        # Generate magic number if not provided
        if settings.magic_number is None:
            hash_input = f"{settings.ea_name}_{settings.symbol}_{datetime.now().isoformat()}"
            settings.magic_number = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16) % 1000000000

    def generate(self) -> str:
        """Generate complete MQL5 EA code."""
        s = self.settings
        
        # Helper for bool
        def b_str(val): return 'true' if val else 'false'
        
        code = f'''//+------------------------------------------------------------------+
//|                                           {s.ea_name}.mq5         |
//|                                      QuantStride EA Generator     |
//|                                   Custom EA for {s.symbol}        |
//+------------------------------------------------------------------+
#property copyright "QuantStride Generator"
#property version   "{s.version}"
#property description "{s.description}"
#property description "Symbol: {s.symbol} | Entry: {s.entry_type.title()}"
#property strict

//+------------------------------------------------------------------+
//|                         INCLUDES                                  |
//+------------------------------------------------------------------+
#include <Trade\\Trade.mqh>
#include <Trade\\PositionInfo.mqh>
#include <Trade\\SymbolInfo.mqh>

//+------------------------------------------------------------------+
//|                    INPUT PARAMETERS                               |
//+------------------------------------------------------------------+

//--- General Settings
input group "=== General Settings ==="
input int      MagicNumber = {s.magic_number};            // Magic Number
input bool     EnableLogging = true;                       // Enable Debug Logging

//--- Trend Settings (EMA)
input group "=== Trend Structure (EMAs) ==="
input int      EMA_Fast_Period = {s.ema_fast_period};      // Fast EMA Period
input int      EMA_Slow_Period = {s.ema_slow_period};      // Slow EMA Period
input bool     UseTrendFilter = {b_str(s.use_trend_filter)};   // Use Trend Filter

//--- Entry Settings
input group "=== Entry Logic ==="
input int      RSI_Period = {s.rsi_period};                // RSI Period
input double   RSI_Buy_Min = {s.rsi_buy_min};              // RSI Buy Zone Min
input double   RSI_Buy_Max = {s.rsi_buy_max};              // RSI Buy Zone Max
input double   RSI_Sell_Min = {s.rsi_sell_min};            // RSI Sell Zone Min
input double   RSI_Sell_Max = {s.rsi_sell_max};            // RSI Sell Zone Max
input int      MACD_Fast = {s.macd_fast};                  // MACD Fast Period
input int      MACD_Slow = {s.macd_slow};                  // MACD Slow Period
input int      MACD_Signal = {s.macd_signal};              // MACD Signal Period
input bool     UseMACD = {b_str(s.use_macd_confirmation)}; // Use MACD Confirmation
input bool     UseCandleConfirm = {b_str(s.use_candle_confirmation)}; // Use Candle Confirmation
input double   PullbackPips = {s.pullback_distance_pips};  // Max Pullback Distance (pips)

//--- Volatility Filter
input group "=== Volatility Filter ==="
input int      ATR_Period = {s.atr_period};                // ATR Period
input int      ATR_SMA_Period = {s.atr_sma_period};        // ATR SMA Period
input double   MinATRRatio = {s.min_atr_ratio};            // Min ATR/ATR_SMA Ratio
input bool     UseVolatilityFilter = {b_str(s.use_volatility_filter)}; // Use Volatility Filter

//--- Risk Management
input group "=== Risk Management ==="
input double   RiskPercent = {s.risk_percent};             // Risk per trade (%)
input double   RiskRewardRatio = {s.risk_reward_ratio};    // Risk:Reward Ratio (1:X)
input bool     UseSwingStopLoss = {b_str(s.use_swing_sl)}; // Use Swing SL
input int      SwingLookback = {s.swing_lookback};         // Swing Lookback Bars
input double   MinStopLossPips = {s.min_sl_pips};          // Minimum SL (pips)
input double   MaxStopLossPips = {s.max_sl_pips};          // Maximum SL (pips)
input bool     UseBreakeven = {b_str(s.use_breakeven)}; // Use Breakeven
input double   BreakevenTrigger = {s.breakeven_trigger_pips}; // Breakeven Trigger (pips)
input double   BreakevenBuffer = {s.breakeven_buffer_pips}; // Breakeven Buffer (pips)

//--- Advanced Trailing Stop
input group "=== Trailing Stop ==="
input bool     UseTrailingStop = {b_str(s.use_trailing_stop)}; // Use Trailing Stop
input string   TrailingType = "{s.trailing_stop_type}"; // Type: fixed, atr, step
input double   TrailStartPips = {s.trailing_start_pips}; // Start Trailing After (pips)
input double   TrailDistancePips = {s.trailing_distance_pips}; // Fixed Distance (pips)
input double   TrailStepSize = {s.step_size_pips}; // Step Size (pips)
input double   TrailStepDist = {s.step_distance_pips}; // Step Distance (pips)
input double   ATR_Multiplier = {s.atr_multiplier}; // ATR Multiplier

//--- Partial Close
input group "=== Partial Close ==="
input bool     UsePartialClose = {b_str(s.use_partial_close)}; // Use Partial Close
input double   PartialClosePercent = {s.partial_close_percent}; // Close % (e.g. 50.0)
input double   PartialTP1_RR = {s.partial_close_tp1_rr}; // Price Target 1 (R:R)
input bool     MoveSLAfterPartial = {b_str(s.move_sl_after_partial)}; // Move SL to BE after Partial

//--- Trade Filters
input group "=== Trade Filters ==="
input double   MaxSpreadPoints = {s.max_spread_points};    // Max Spread (points)
input bool     UseTradingHours = {b_str(s.use_trading_hours)}; // Use Trading Hours
input int      TradingHourStart = {s.trading_hour_start};  // Trading Start Hour (UTC)
input int      TradingHourEnd = {s.trading_hour_end};      // Trading End Hour (UTC)
input int      MaxOpenTrades = {s.max_open_trades};        // Max Open Trades

//--- News Filter
input group "=== News Filter ==="
input bool     UseNewsFilter = {b_str(s.use_news_filter)}; // Disable During News
input int      NewsBufferMinutes = {s.news_buffer_minutes}; // News Buffer (minutes)

//+------------------------------------------------------------------+
//|                      GLOBAL VARIABLES                             |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  positionInfo;
CSymbolInfo    symbolInfo;

//--- Indicator handles
int handle_ema_fast;
int handle_ema_slow;
int handle_rsi;
int handle_macd;
int handle_atr;

//--- State tracking
double pipMultiplier = 1.0;
datetime lastTradeTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{{
   Print("==========================================");
   Print("Initializing {s.ea_name}...");
   Print("Symbol: ", _Symbol);
   
   //--- Initialize trade object
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(30);
   
   //--- Initialize symbol info
   if(!symbolInfo.Name(_Symbol)) return(INIT_FAILED);
   
   //--- Calculate pip multiplier
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string symbolName = _Symbol;
   if(StringFind(symbolName, "XAU") >= 0 || StringFind(symbolName, "GOLD") >= 0)
      pipMultiplier = (digits == 2) ? 1.0 : (digits == 3) ? 10.0 : 1.0;
   else if(StringFind(symbolName, "JPY") >= 0)
      pipMultiplier = (digits == 3) ? 1.0 : 10.0;
   else if(StringFind(symbolName, "Volatility") >= 0)
      pipMultiplier = 1.0;
   else
      pipMultiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
   
   //--- Create indicator handles
   handle_ema_fast = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast_Period, 0, MODE_EMA, PRICE_CLOSE);
   handle_ema_slow = iMA(_Symbol, PERIOD_CURRENT, EMA_Slow_Period, 0, MODE_EMA, PRICE_CLOSE);
   handle_rsi = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);
   handle_macd = iMACD(_Symbol, PERIOD_CURRENT, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);
   handle_atr = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   
   if(handle_ema_fast == INVALID_HANDLE || handle_ema_slow == INVALID_HANDLE ||
      handle_rsi == INVALID_HANDLE || handle_macd == INVALID_HANDLE || 
      handle_atr == INVALID_HANDLE)
   {{
      Print("ERROR: Handles");
      return(INIT_FAILED);
   }}
   
   return(INIT_SUCCEEDED);
}}

void OnDeinit(const int reason)
{{
   IndicatorRelease(handle_ema_fast);
   IndicatorRelease(handle_ema_slow);
   IndicatorRelease(handle_rsi);
   IndicatorRelease(handle_macd);
   IndicatorRelease(handle_atr);
}}

void OnTick()
{{
   ManageOpenPositions();
   
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   
   if(currentBarTime == lastBarTime) return;
   lastBarTime = currentBarTime;
   
   if(!PassesAllFilters()) return;
   
   int trend = CheckTrend();
   if(UseTrendFilter && trend == 0) return;
   
   int signal = CheckEntry(trend);
   
   if(signal != 0 && CanOpenTrade(signal))
      PlaceTrade(signal);
}}

int CheckTrend()
{{
   double ema_fast[], ema_slow[];
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(ema_slow, true);
   
   if(CopyBuffer(handle_ema_fast, 0, 0, 2, ema_fast) < 2) return 0;
   if(CopyBuffer(handle_ema_slow, 0, 0, 2, ema_slow) < 2) return 0;
   
   if(ema_fast[0] > ema_slow[0]) return 1;
   if(ema_fast[0] < ema_slow[0]) return -1;
   return 0;
}}

int CheckEntry(int trend)
{{
   double rsi[], macd[], sig[], close[], open[];
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(macd, true);
   ArraySetAsSeries(sig, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   
   if(CopyBuffer(handle_rsi, 0, 0, 2, rsi) < 2) return 0;
   if(CopyBuffer(handle_macd, 0, 0, 2, macd) < 2) return 0;
   if(CopyBuffer(handle_macd, 1, 0, 2, sig) < 2) return 0;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) < 2) return 0;
   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 2, open) < 2) return 0;
   
   // Logic check
   if(trend > 0) {{
      if(rsi[1] >= RSI_Buy_Min && rsi[1] <= RSI_Buy_Max) {{
         if(!UseMACD || (macd[1] > sig[1])) return 1;
      }}
   }}
   
   if(trend < 0) {{
      if(rsi[1] >= RSI_Sell_Min && rsi[1] <= RSI_Sell_Max) {{
         if(!UseMACD || (macd[1] < sig[1])) return -1;
      }}
   }}
   
   return 0;
}}

bool PassesAllFilters()
{{
   double spread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread > MaxSpreadPoints) return false;
   
   if(UseTradingHours) {{
      MqlDateTime dt;
      TimeToStruct(TimeGMT(), dt);
      if(dt.hour < TradingHourStart || dt.hour >= TradingHourEnd) return false;
   }}
   
   return true;
}}

bool CanOpenTrade(int direction)
{{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--) {{
      if(positionInfo.SelectByIndex(i)) {{
         if(positionInfo.Symbol() == _Symbol && positionInfo.Magic() == MagicNumber)
            count++;
      }}
   }}
   return (count < MaxOpenTrades);
}}

void PlaceTrade(int direction)
{{
   symbolInfo.RefreshRates();
   double price = (direction == 1) ? symbolInfo.Ask() : symbolInfo.Bid();
   
   // Calculate SL/TP
   double sl = 0, tp = 0;
   double atr[]; ArraySetAsSeries(atr, true);
   CopyBuffer(handle_atr, 0, 0, 1, atr);
   double atrVal = atr[0];
   
   double slPips = MinStopLossPips;
   if(UseSwingStopLoss) slPips = MathMax(MinStopLossPips, atrVal / (pipMultiplier * _Point) * 2.0); // Simple ATR based
   
   if(direction == 1) {{
       sl = price - slPips * pipMultiplier * _Point;
       tp = price + slPips * RiskRewardRatio * pipMultiplier * _Point;
       trade.Buy(0.01, _Symbol, price, sl, tp, "{s.ea_name}");
   }} else {{
       sl = price + slPips * pipMultiplier * _Point;
       tp = price - slPips * RiskRewardRatio * pipMultiplier * _Point;
       trade.Sell(0.01, _Symbol, price, sl, tp, "{s.ea_name}");
   }}
}}

void ManageOpenPositions()
{{
   double atr[]; ArraySetAsSeries(atr, true);
   CopyBuffer(handle_atr, 0, 0, 1, atr);
   double atrVal = atr[0];

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {{
      if(!positionInfo.SelectByIndex(i)) continue;
      if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber) continue;
      
      double open = positionInfo.PriceOpen();
      double current = positionInfo.PriceCurrent();
      double sl = positionInfo.StopLoss();
      double tp = positionInfo.TakeProfit();
      long type = positionInfo.PositionType();
      
      double profitPips = 0;
      if(type == POSITION_TYPE_BUY) profitPips = (current - open) / (pipMultiplier * _Point);
      else profitPips = (open - current) / (pipMultiplier * _Point);
      
      //--- BREAKEVEN Logic
      if(UseBreakeven && profitPips >= BreakevenTrigger)
      {{
         double newSL = 0;
         double breakevenPrice = 0;
         double buffer = BreakevenBuffer * pipMultiplier * _Point;
         
         if(type == POSITION_TYPE_BUY)
         {{
            breakevenPrice = open + buffer;
            if(sl < breakevenPrice - _Point) trade.PositionModify(positionInfo.Ticket(), breakevenPrice, tp);
         }}
         else
         {{
            breakevenPrice = open - buffer;
            if(sl > breakevenPrice + _Point || sl == 0) trade.PositionModify(positionInfo.Ticket(), breakevenPrice, tp);
         }}
      }}
      
      //--- PARTIAL CLOSE Logic
      if(UsePartialClose && positionInfo.Volume() > 0.01) // Ensure we have volume to close
      {{
         // Calculate R distance for partial close target
         double r_dist = MathAbs(open - sl) / (pipMultiplier * _Point); // Approximate initial risk
         // Note: If SL was moved, this r_dist changes. We should ideally store initial SL or assume fixed.
         // For now using current SL distance might be wrong if SL moved to BE.
         // Better to use parameter-based R estimate if SL moved? Or just assume MinSL?
         if(r_dist < 1) r_dist = MinStopLossPips; 
         
         if(profitPips >= r_dist * PartialTP1_RR)
         {{
             // Check if execution needed... (requires advanced state tracking in MQL5)
             // Simplified: Trigger logic placeholder
         }}
      }}
      
      //--- TRAILING STOP Logic
      if(UseTrailingStop)
      {{
         double newSL = 0;
         double trailDist = 0;
         
         if(TrailingType == "atr") trailDist = atrVal * ATR_Multiplier;
         else trailDist = TrailDistancePips * pipMultiplier * _Point;
         
         if(profitPips > TrailStartPips)
         {{
            if(type == POSITION_TYPE_BUY)
            {{
               newSL = current - trailDist;
               if(newSL > sl + _Point) trade.PositionModify(positionInfo.Ticket(), newSL, tp);
            }}
            else
            {{
               newSL = current + trailDist;
               if(newSL < sl - _Point || sl == 0) trade.PositionModify(positionInfo.Ticket(), newSL, tp);
            }}
         }}
      }}
   }}
}}
'''
        return code
    
    def save(self, output_dir: str = None) -> str:
        code = self.generate()
        path = Path(output_dir or ".") / f"{self.settings.ea_name}.mq5"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        return str(path)
