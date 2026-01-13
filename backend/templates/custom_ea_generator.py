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
    breakeven_activation_r: float = 1.0
    breakeven_buffer_pips: float = 5.0
    use_trailing_stop: bool = False
    trailing_stop_pips: float = 30.0
    trailing_step_pips: float = 10.0
    
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
    
    Example usage:
    ```python
    settings = EASettings(
        ea_name="XAUUSD_Scalper",
        symbol="XAUUSD",
        ema_fast_period=50,
        ema_slow_period=200,
        rsi_buy_min=20,
        rsi_buy_max=35,
        risk_percent=1.0,
        risk_reward_ratio=2.0
    )
    
    generator = CustomEAGenerator(settings)
    code = generator.generate()
    generator.save("./output/experts/")
    ```
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
input bool     UseTrendFilter = {'true' if s.use_trend_filter else 'false'};   // Use Trend Filter

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
input bool     UseMACD = {'true' if s.use_macd_confirmation else 'false'}; // Use MACD Confirmation
input bool     UseCandleConfirm = {'true' if s.use_candle_confirmation else 'false'}; // Use Candle Confirmation
input double   PullbackPips = {s.pullback_distance_pips};  // Max Pullback Distance (pips)

//--- Volatility Filter
input group "=== Volatility Filter ==="
input int      ATR_Period = {s.atr_period};                // ATR Period
input int      ATR_SMA_Period = {s.atr_sma_period};        // ATR SMA Period
input double   MinATRRatio = {s.min_atr_ratio};            // Min ATR/ATR_SMA Ratio
input bool     UseVolatilityFilter = {'true' if s.use_volatility_filter else 'false'}; // Use Volatility Filter

//--- Risk Management
input group "=== Risk Management ==="
input double   RiskPercent = {s.risk_percent};             // Risk per trade (%)
input double   RiskRewardRatio = {s.risk_reward_ratio};    // Risk:Reward Ratio (1:X)
input bool     UseSwingStopLoss = {'true' if s.use_swing_sl else 'false'}; // Use Swing SL
input int      SwingLookback = {s.swing_lookback};         // Swing Lookback Bars
input double   MinStopLossPips = {s.min_sl_pips};          // Minimum SL (pips)
input double   MaxStopLossPips = {s.max_sl_pips};          // Maximum SL (pips)
input bool     UseBreakeven = {'true' if s.use_breakeven else 'false'}; // Use Breakeven
input double   BreakevenBuffer = {s.breakeven_buffer_pips}; // Breakeven Buffer (pips)
input bool     UseTrailingStop = {'true' if s.use_trailing_stop else 'false'}; // Use Trailing Stop
input double   TrailingStopPips = {s.trailing_stop_pips};  // Trailing Stop (pips)
input double   TrailingStepPips = {s.trailing_step_pips};  // Trailing Step (pips)

//--- Trade Filters
input group "=== Trade Filters ==="
input double   MaxSpreadPoints = {s.max_spread_points};    // Max Spread (points)
input bool     UseTradingHours = {'true' if s.use_trading_hours else 'false'}; // Use Trading Hours
input int      TradingHourStart = {s.trading_hour_start};  // Trading Start Hour (UTC)
input int      TradingHourEnd = {s.trading_hour_end};      // Trading End Hour (UTC)
input int      MaxOpenTrades = {s.max_open_trades};        // Max Open Trades

//--- News Filter
input group "=== News Filter ==="
input bool     UseNewsFilter = {'true' if s.use_news_filter else 'false'}; // Disable During News
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
   Print("==========================================");
   
   //--- Initialize trade object
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetMarginMode();
   trade.SetTypeFillingBySymbol(_Symbol);
   trade.SetDeviationInPoints(30);
   
   //--- Initialize symbol info
   if(!symbolInfo.Name(_Symbol))
   {{
      Print("ERROR: Failed to initialize symbol info");
      return(INIT_FAILED);
   }}
   
   //--- Calculate pip multiplier
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   
   // Handle different symbol types
   string symbolName = _Symbol;
   if(StringFind(symbolName, "XAU") >= 0 || StringFind(symbolName, "GOLD") >= 0)
   {{
      // Gold: typically 2 digits, 1 pip = 0.01
      pipMultiplier = (digits == 2) ? 1.0 : (digits == 3) ? 10.0 : 1.0;
   }}
   else if(StringFind(symbolName, "JPY") >= 0)
   {{
      // JPY pairs: typically 3 digits
      pipMultiplier = (digits == 3) ? 1.0 : 10.0;
   }}
   else if(StringFind(symbolName, "Volatility") >= 0 || 
           StringFind(symbolName, "Boom") >= 0 || 
           StringFind(symbolName, "Crash") >= 0)
   {{
      // Synthetic indices
      pipMultiplier = 1.0;
   }}
   else
   {{
      // Standard forex: usually 5 digits
      pipMultiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
   }}
   
   Print("Digits: ", digits, " | Pip Multiplier: ", pipMultiplier);
   
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
      Print("ERROR: Failed to create indicator handles");
      return(INIT_FAILED);
   }}
   
   Print("All indicators initialized successfully!");
   Print("Risk: ", RiskPercent, "% | R:R = 1:", RiskRewardRatio);
   Print("==========================================");
   
   return(INIT_SUCCEEDED);
}}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{{
   IndicatorRelease(handle_ema_fast);
   IndicatorRelease(handle_ema_slow);
   IndicatorRelease(handle_rsi);
   IndicatorRelease(handle_macd);
   IndicatorRelease(handle_atr);
   
   Print("{s.ea_name} deinitialized. Reason: ", reason);
}}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{{
   //--- Manage existing positions first
   ManageOpenPositions();
   
   //--- Only check for new entries on new bar
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   
   if(currentBarTime == lastBarTime)
      return;
   lastBarTime = currentBarTime;
   
   //--- Check all filters
   if(!PassesAllFilters())
      return;
   
   //--- Check trend direction
   int trend = CheckTrend();
   if(UseTrendFilter && trend == 0)
      return;
   
   //--- Check entry conditions
   int signal = CheckEntry(trend);
   
   if(signal == 0)
      return;
   
   //--- Check if we can open trade
   if(!CanOpenTrade(signal))
      return;
   
   //--- Place trade
   PlaceTrade(signal);
}}

//+------------------------------------------------------------------+
//| CHECK TREND DIRECTION                                             |
//+------------------------------------------------------------------+
int CheckTrend()
{{
   double ema_fast[], ema_slow[];
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(ema_slow, true);
   
   if(CopyBuffer(handle_ema_fast, 0, 0, 3, ema_fast) < 3) return 0;
   if(CopyBuffer(handle_ema_slow, 0, 0, 3, ema_slow) < 3) return 0;
   
   if(ema_fast[0] > ema_slow[0] && ema_fast[1] > ema_slow[1])
   {{
      LogMessage("Trend: BULLISH");
      return 1;
   }}
   
   if(ema_fast[0] < ema_slow[0] && ema_fast[1] < ema_slow[1])
   {{
      LogMessage("Trend: BEARISH");
      return -1;
   }}
   
   return 0;
}}

//+------------------------------------------------------------------+
//| CHECK ENTRY CONDITIONS                                            |
//+------------------------------------------------------------------+
int CheckEntry(int trend)
{{
   double ema_fast[], rsi[], macd_main[], macd_signal[], atr[];
   double close[], open[];
   
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   
   if(CopyBuffer(handle_ema_fast, 0, 0, 5, ema_fast) < 5) return 0;
   if(CopyBuffer(handle_rsi, 0, 0, 5, rsi) < 5) return 0;
   if(CopyBuffer(handle_macd, 0, 0, 5, macd_main) < 5) return 0;
   if(CopyBuffer(handle_macd, 1, 0, 5, macd_signal) < 5) return 0;
   if(CopyBuffer(handle_atr, 0, 0, ATR_SMA_Period + 5, atr) < ATR_SMA_Period + 5) return 0;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, close) < 5) return 0;
   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 5, open) < 5) return 0;
   
   //--- Volatility filter
   if(UseVolatilityFilter)
   {{
      double atr_sum = 0;
      for(int i = 1; i <= ATR_SMA_Period; i++)
         atr_sum += atr[i];
      double atr_sma = atr_sum / ATR_SMA_Period;
      
      if(atr_sma > 0 && atr[0] / atr_sma < MinATRRatio)
      {{
         LogMessage("Volatility too low");
         return 0;
      }}
   }}
   
   //--- MACD histogram
   double hist_now = macd_main[1] - macd_signal[1];
   double hist_prev = macd_main[2] - macd_signal[2];
   
   //--- Pullback distance
   double pullback_pips = MathAbs(close[1] - ema_fast[1]) / (pipMultiplier * _Point);
   
   //=== BUY ENTRY ===
   if(trend >= 0)
   {{
      bool nearEMA = (pullback_pips <= PullbackPips);
      bool rsiOK = (rsi[1] >= RSI_Buy_Min && rsi[1] <= RSI_Buy_Max);
      bool macdOK = !UseMACD || (hist_now > hist_prev);
      bool candleOK = !UseCandleConfirm || (close[1] > open[1]);
      
      if(nearEMA && rsiOK && macdOK && candleOK)
      {{
         LogMessage("BUY SIGNAL: RSI=" + DoubleToString(rsi[1], 1));
         return 1;
      }}
   }}
   
   //=== SELL ENTRY ===
   if(trend <= 0)
   {{
      bool nearEMA = (pullback_pips <= PullbackPips);
      bool rsiOK = (rsi[1] >= RSI_Sell_Min && rsi[1] <= RSI_Sell_Max);
      bool macdOK = !UseMACD || (hist_now < hist_prev);
      bool candleOK = !UseCandleConfirm || (close[1] < open[1]);
      
      if(nearEMA && rsiOK && macdOK && candleOK)
      {{
         LogMessage("SELL SIGNAL: RSI=" + DoubleToString(rsi[1], 1));
         return -1;
      }}
   }}
   
   return 0;
}}

//+------------------------------------------------------------------+
//| CHECK ALL FILTERS                                                 |
//+------------------------------------------------------------------+
bool PassesAllFilters()
{{
   //--- Spread filter
   double spread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread > MaxSpreadPoints)
   {{
      LogMessage("Spread too high: " + DoubleToString(spread, 0));
      return false;
   }}
   
   //--- Trading hours
   if(UseTradingHours)
   {{
      MqlDateTime dt;
      TimeToStruct(TimeGMT(), dt);
      if(dt.hour < TradingHourStart || dt.hour >= TradingHourEnd)
      {{
         return false;
      }}
   }}
   
   //--- News filter
   if(UseNewsFilter)
   {{
      MqlDateTime dt;
      TimeToStruct(TimeGMT(), dt);
      
      // NFP
      if(dt.day_of_week == FRIDAY && dt.day <= 7 && dt.hour >= 13 && dt.hour <= 14)
         return false;
      
      // FOMC
      if(dt.day_of_week == WEDNESDAY && dt.hour >= 18 && dt.hour <= 20)
         return false;
   }}
   
   return true;
}}

//+------------------------------------------------------------------+
//| CAN OPEN NEW TRADE                                                |
//+------------------------------------------------------------------+
bool CanOpenTrade(int direction)
{{
   int count = 0;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {{
      if(positionInfo.SelectByIndex(i))
      {{
         if(positionInfo.Symbol() == _Symbol && (int)positionInfo.Magic() == MagicNumber)
         {{
            if(direction == 1 && positionInfo.PositionType() == POSITION_TYPE_BUY)
               count++;
            else if(direction == -1 && positionInfo.PositionType() == POSITION_TYPE_SELL)
               count++;
         }}
      }}
   }}
   
   return (count < MaxOpenTrades);
}}

//+------------------------------------------------------------------+
//| CALCULATE STOP LOSS                                               |
//+------------------------------------------------------------------+
double CalculateStopLoss(int direction)
{{
   double sl = 0;
   
   if(UseSwingStopLoss)
   {{
      double high[], low[];
      ArraySetAsSeries(high, true);
      ArraySetAsSeries(low, true);
      
      if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, SwingLookback + 1, high) >= SwingLookback + 1 &&
         CopyLow(_Symbol, PERIOD_CURRENT, 0, SwingLookback + 1, low) >= SwingLookback + 1)
      {{
         if(direction == 1)
            sl = low[ArrayMinimum(low, 1, SwingLookback)];
         else
            sl = high[ArrayMaximum(high, 1, SwingLookback)];
      }}
   }}
   
   if(sl == 0)
   {{
      double atr[];
      ArraySetAsSeries(atr, true);
      if(CopyBuffer(handle_atr, 0, 0, 1, atr) >= 1)
      {{
         if(direction == 1)
            sl = symbolInfo.Ask() - atr[0] * 2;
         else
            sl = symbolInfo.Bid() + atr[0] * 2;
      }}
   }}
   
   return NormalizeDouble(sl, _Digits);
}}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE                                                |
//+------------------------------------------------------------------+
double CalculateLotSize(double slPrice)
{{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (RiskPercent / 100.0);
   
   double entryPrice = (slPrice < symbolInfo.Ask()) ? symbolInfo.Ask() : symbolInfo.Bid();
   double slPips = MathAbs(entryPrice - slPrice) / (pipMultiplier * _Point);
   
   slPips = MathMax(MinStopLossPips, MathMin(MaxStopLossPips, slPips));
   
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   
   double pointValue = (tickValue / tickSize) * _Point;
   
   double lots = 0.0;
   if(pointValue > 0 && slPips > 0)
   {{
      lots = riskAmount / (slPips * pipMultiplier * pointValue);
   }}
   
   lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));
   
   return lots;
}}

//+------------------------------------------------------------------+
//| PLACE TRADE                                                       |
//+------------------------------------------------------------------+
void PlaceTrade(int direction)
{{
   symbolInfo.RefreshRates();
   
   double entryPrice, sl, tp;
   
   if(direction == 1)
   {{
      entryPrice = symbolInfo.Ask();
      sl = CalculateStopLoss(direction);
      
      double slPips = (entryPrice - sl) / (pipMultiplier * _Point);
      slPips = MathMax(MinStopLossPips, MathMin(MaxStopLossPips, slPips));
      sl = entryPrice - slPips * pipMultiplier * _Point;
      tp = entryPrice + slPips * RiskRewardRatio * pipMultiplier * _Point;
   }}
   else
   {{
      entryPrice = symbolInfo.Bid();
      sl = CalculateStopLoss(direction);
      
      double slPips = (sl - entryPrice) / (pipMultiplier * _Point);
      slPips = MathMax(MinStopLossPips, MathMin(MaxStopLossPips, slPips));
      sl = entryPrice + slPips * pipMultiplier * _Point;
      tp = entryPrice - slPips * RiskRewardRatio * pipMultiplier * _Point;
   }}
   
   double lots = CalculateLotSize(sl);
   if(lots <= 0) return;
   
   sl = NormalizeDouble(sl, _Digits);
   tp = NormalizeDouble(tp, _Digits);
   
   bool success = false;
   
   if(direction == 1)
      success = trade.Buy(lots, _Symbol, entryPrice, sl, tp, "{s.ea_name}");
   else
      success = trade.Sell(lots, _Symbol, entryPrice, sl, tp, "{s.ea_name}");
   
   if(success)
   {{
      Print("✓ Order placed! Ticket: ", trade.ResultOrder());
      lastTradeTime = TimeCurrent();
   }}
   else
   {{
      Print("✗ Order failed: ", GetLastError());
   }}
}}

//+------------------------------------------------------------------+
//| MANAGE OPEN POSITIONS                                             |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {{
      if(positionInfo.SelectByIndex(i))
      {{
         if(positionInfo.Symbol() != _Symbol || (int)positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current = positionInfo.PriceCurrent();
         double current_sl = positionInfo.StopLoss();
         double current_tp = positionInfo.TakeProfit();
         
         double profitPips = 0;
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
            profitPips = (current - entry) / (pipMultiplier * _Point);
         else
            profitPips = (entry - current) / (pipMultiplier * _Point);
         
         double slDistance = MathAbs(entry - current_sl) / (pipMultiplier * _Point);
         
         //=== BREAKEVEN ===
         if(UseBreakeven && profitPips >= slDistance)
         {{
            double buffer = BreakevenBuffer * pipMultiplier * _Point;
            double new_sl = 0;
            
            if(positionInfo.PositionType() == POSITION_TYPE_BUY)
            {{
               new_sl = entry + buffer;
               if(current_sl < entry && new_sl > current_sl)
                  trade.PositionModify(positionInfo.Ticket(), new_sl, current_tp);
            }}
            else
            {{
               new_sl = entry - buffer;
               if(current_sl > entry && new_sl < current_sl)
                  trade.PositionModify(positionInfo.Ticket(), new_sl, current_tp);
            }}
         }}
         
         //=== TRAILING STOP ===
         if(UseTrailingStop && profitPips > TrailingStopPips)
         {{
            double trail = TrailingStopPips * pipMultiplier * _Point;
            double step = TrailingStepPips * pipMultiplier * _Point;
            double new_sl = 0;
            
            if(positionInfo.PositionType() == POSITION_TYPE_BUY)
            {{
               new_sl = current - trail;
               if(new_sl > current_sl + step && new_sl > entry)
                  trade.PositionModify(positionInfo.Ticket(), new_sl, current_tp);
            }}
            else
            {{
               new_sl = current + trail;
               if(new_sl < current_sl - step && new_sl < entry)
                  trade.PositionModify(positionInfo.Ticket(), new_sl, current_tp);
            }}
         }}
      }}
   }}
}}

//+------------------------------------------------------------------+
//| LOG MESSAGE                                                       |
//+------------------------------------------------------------------+
void LogMessage(string message)
{{
   if(EnableLogging)
      Print(TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES), " | ", message);
}}
//+------------------------------------------------------------------+
'''
        return code
    
    def save(self, output_dir: str = None) -> str:
        """Save the generated EA to a file."""
        code = self.generate()
        
        if output_dir:
            path = Path(output_dir) / f"{self.settings.ea_name}.mq5"
        else:
            path = Path(f"{self.settings.ea_name}.mq5")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        
        return str(path)


# === PRESET CONFIGURATIONS ===

def create_xauusd_scalper() -> EASettings:
    """Preset for XAUUSD (Gold) scalping."""
    return EASettings(
        ea_name="XAUUSD_Scalper",
        symbol="XAUUSD",
        ema_fast_period=50,
        ema_slow_period=200,
        rsi_buy_min=20.0,
        rsi_buy_max=35.0,
        rsi_sell_min=65.0,
        rsi_sell_max=80.0,
        pullback_distance_pips=50.0,
        risk_percent=1.0,
        risk_reward_ratio=2.0,
        min_sl_pips=30.0,
        max_sl_pips=150.0,
        max_spread_points=25.0,
        trading_hour_start=8,
        trading_hour_end=18
    )


def create_eurusd_scalper() -> EASettings:
    """Preset for EURUSD scalping."""
    return EASettings(
        ea_name="EURUSD_Scalper",
        symbol="EURUSD",
        ema_fast_period=21,
        ema_slow_period=55,
        rsi_buy_min=30.0,
        rsi_buy_max=45.0,
        rsi_sell_min=55.0,
        rsi_sell_max=70.0,
        pullback_distance_pips=15.0,
        risk_percent=1.0,
        risk_reward_ratio=1.5,
        min_sl_pips=10.0,
        max_sl_pips=30.0,
        max_spread_points=15.0,
        trading_hour_start=8,
        trading_hour_end=17
    )


def create_us30_trader() -> EASettings:
    """Preset for US30 (Dow Jones) trading."""
    return EASettings(
        ea_name="US30_Trader",
        symbol="US30",
        ema_fast_period=20,
        ema_slow_period=50,
        rsi_buy_min=35.0,
        rsi_buy_max=50.0,
        rsi_sell_min=50.0,
        rsi_sell_max=65.0,
        pullback_distance_pips=100.0,
        risk_percent=0.5,
        risk_reward_ratio=2.0,
        min_sl_pips=50.0,
        max_sl_pips=200.0,
        max_spread_points=50.0,
        trading_hour_start=14,
        trading_hour_end=21
    )


def create_volatility_75_trader() -> EASettings:
    """Preset for Volatility 75 Index (Deriv)."""
    return EASettings(
        ea_name="V75_Trader",
        symbol="Volatility 75 Index",
        ema_fast_period=10,
        ema_slow_period=21,
        rsi_buy_min=25.0,
        rsi_buy_max=40.0,
        rsi_sell_min=60.0,
        rsi_sell_max=75.0,
        pullback_distance_pips=500.0,
        risk_percent=0.5,
        risk_reward_ratio=1.5,
        min_sl_pips=100.0,
        max_sl_pips=500.0,
        max_spread_points=100.0,
        use_trading_hours=False,  # 24/7 market
        use_news_filter=False
    )
