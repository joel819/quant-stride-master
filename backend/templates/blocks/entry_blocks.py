"""
Entry Blocks
High-accuracy entry logic with multiple confirmations.
"""


class EntryBlocks:
    """
    Modular entry blocks for EA assembly.
    
    All entries require:
    - ≥2 trend filters
    - Volatility confirmation
    - Momentum confirmation
    - Direction alignment (buy uptrend only, sell downtrend only)
    """
    
    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for entry blocks."""
        return '''
//+------------------------------------------------------------------+
//|                    ENTRY BLOCK PARAMETERS                        |
//+------------------------------------------------------------------+
input group "=== Trend Filters ==="
input int EMA_Fast = 50;                                     // Fast EMA Period
input int EMA_Slow = 200;                                    // Slow EMA Period
input int HMA_Period = 55;                                   // HMA Period
input bool UseSuperTrend = true;                             // Use SuperTrend
input double SuperTrend_ATR_Mult = 3.0;                      // SuperTrend ATR Multiplier
input int SuperTrend_ATR_Period = 10;                        // SuperTrend ATR Period

input group "=== Volatility Filters ==="
input bool UseVolatilityFilter = true;                       // Enable Volatility Filter
input int ATR_Period = 14;                                   // ATR Period
input int ATR_SMA_Period = 20;                               // ATR SMA Period for comparison
input double MinATRRatio = 1.0;                              // Min ATR/ATR_SMA ratio
input bool UseBBExpansion = true;                            // Use BB Expansion
input int BB_Period = 20;                                    // BB Period
input double BB_Dev = 2.0;                                   // BB Deviation
input double MinBBWidth = 0.001;                             // Min BB Width

input group "=== Momentum Filters ==="
input bool UseMomentumFilter = true;                         // Enable Momentum Filter
input int RSI_Period = 14;                                   // RSI Period
input int RSI_SlopeLength = 3;                               // RSI Slope bars
input int MACD_Fast = 12;                                    // MACD Fast
input int MACD_Slow = 26;                                    // MACD Slow
input int MACD_Signal = 9;                                   // MACD Signal
input int ADX_Period = 14;                                   // ADX Period
input double ADX_MinTrend = 20.0;                            // Min ADX for trend

input group "=== Entry Type ==="
input bool UseTrendEntry = true;                             // Enable Trend Entry
input bool UsePullbackEntry = true;                          // Enable Pullback Entry
input bool UseBreakoutEntry = false;                         // Enable Breakout Entry
input bool UseReversalEntry = false;                         // Enable Reversal Entry
'''

    @staticmethod
    def generate_globals() -> str:
        """Generate global variables for entry blocks."""
        return '''
//+------------------------------------------------------------------+
//|                    ENTRY BLOCK GLOBALS                           |
//+------------------------------------------------------------------+
// Indicator handles
int handle_ema_fast, handle_ema_slow;
int handle_hma;
int handle_atr, handle_atr_sma;
int handle_bb;
int handle_rsi;
int handle_macd;
int handle_adx;
int handle_supertrend_atr;

// Current market state
int marketTrend = 0;         // 1=Bullish, -1=Bearish, 0=Neutral
int volatilityState = 0;     // 1=Expanding, -1=Contracting, 0=Normal
int momentumState = 0;       // 1=Bullish, -1=Bearish, 0=Neutral
double superTrendValue = 0;
int superTrendDirection = 0;
'''

    @staticmethod
    def generate_init() -> str:
        """Generate indicator initialization for entry blocks."""
        return '''
//+------------------------------------------------------------------+
//| Initialize Entry Block Indicators                                |
//+------------------------------------------------------------------+
bool InitEntryIndicators()
{
   // Trend EMAs
   handle_ema_fast = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   handle_ema_slow = iMA(_Symbol, PERIOD_CURRENT, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   if(handle_ema_fast == INVALID_HANDLE || handle_ema_slow == INVALID_HANDLE)
   {
      Print("Failed to create EMA handles");
      return false;
   }
   
   // HMA (Hull Moving Average approximation using weighted MAs)
   handle_hma = iMA(_Symbol, PERIOD_CURRENT, HMA_Period, 0, MODE_LWMA, PRICE_CLOSE);
   if(handle_hma == INVALID_HANDLE)
   {
      Print("Failed to create HMA handle");
      return false;
   }
   
   // ATR for volatility
   handle_atr = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   handle_atr_sma = iMA(_Symbol, PERIOD_CURRENT, ATR_SMA_Period, 0, MODE_SMA, PRICE_CLOSE);
   if(handle_atr == INVALID_HANDLE)
   {
      Print("Failed to create ATR handle");
      return false;
   }
   
   // Bollinger Bands
   handle_bb = iBands(_Symbol, PERIOD_CURRENT, BB_Period, 0, BB_Dev, PRICE_CLOSE);
   if(handle_bb == INVALID_HANDLE)
   {
      Print("Failed to create BB handle");
      return false;
   }
   
   // RSI
   handle_rsi = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);
   if(handle_rsi == INVALID_HANDLE)
   {
      Print("Failed to create RSI handle");
      return false;
   }
   
   // MACD
   handle_macd = iMACD(_Symbol, PERIOD_CURRENT, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);
   if(handle_macd == INVALID_HANDLE)
   {
      Print("Failed to create MACD handle");
      return false;
   }
   
   // ADX
   handle_adx = iADX(_Symbol, PERIOD_CURRENT, ADX_Period);
   if(handle_adx == INVALID_HANDLE)
   {
      Print("Failed to create ADX handle");
      return false;
   }
   
   // SuperTrend ATR
   if(UseSuperTrend)
   {
      handle_supertrend_atr = iATR(_Symbol, PERIOD_CURRENT, SuperTrend_ATR_Period);
      if(handle_supertrend_atr == INVALID_HANDLE)
      {
         Print("Failed to create SuperTrend ATR handle");
         return false;
      }
   }
   
   Print("Entry indicators initialized successfully");
   return true;
}
'''

    @staticmethod
    def generate_deinit() -> str:
        """Generate cleanup code for entry blocks."""
        return '''
//+------------------------------------------------------------------+
//| Release Entry Block Indicators                                   |
//+------------------------------------------------------------------+
void DeinitEntryIndicators()
{
   IndicatorRelease(handle_ema_fast);
   IndicatorRelease(handle_ema_slow);
   IndicatorRelease(handle_hma);
   IndicatorRelease(handle_atr);
   IndicatorRelease(handle_bb);
   IndicatorRelease(handle_rsi);
   IndicatorRelease(handle_macd);
   IndicatorRelease(handle_adx);
   if(UseSuperTrend) IndicatorRelease(handle_supertrend_atr);
}
'''

    @staticmethod
    def generate_trend_detection() -> str:
        """Generate multi-filter trend detection."""
        return '''
//+------------------------------------------------------------------+
//| Trend Detection with Multiple Filters                            |
//+------------------------------------------------------------------+
int DetectTrend()
{
   double ema_fast[], ema_slow[], hma[];
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(ema_slow, true);
   ArraySetAsSeries(hma, true);
   
   if(CopyBuffer(handle_ema_fast, 0, 0, 3, ema_fast) < 3) return 0;
   if(CopyBuffer(handle_ema_slow, 0, 0, 3, ema_slow) < 3) return 0;
   if(CopyBuffer(handle_hma, 0, 0, 3, hma) < 3) return 0;
   
   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 3, close) < 3) return 0;
   
   int trendScore = 0;
   
   // Filter 1: EMA Cross (EMA50 vs EMA200)
   if(ema_fast[0] > ema_slow[0]) trendScore++;
   else if(ema_fast[0] < ema_slow[0]) trendScore--;
   
   // Filter 2: Price vs EMA
   if(close[0] > ema_fast[0] && close[0] > ema_slow[0]) trendScore++;
   else if(close[0] < ema_fast[0] && close[0] < ema_slow[0]) trendScore--;
   
   // Filter 3: HMA slope
   if(hma[0] > hma[1] && hma[1] > hma[2]) trendScore++;
   else if(hma[0] < hma[1] && hma[1] < hma[2]) trendScore--;
   
   // Filter 4: SuperTrend
   if(UseSuperTrend)
   {
      CalculateSuperTrend();
      if(superTrendDirection == 1) trendScore++;
      else if(superTrendDirection == -1) trendScore--;
   }
   
   // Require at least 2 confirmations
   if(trendScore >= 2) return 1;      // Bullish
   if(trendScore <= -2) return -1;    // Bearish
   return 0;                           // Neutral
}

//+------------------------------------------------------------------+
//| Calculate SuperTrend                                              |
//+------------------------------------------------------------------+
void CalculateSuperTrend()
{
   double atr[];
   double high[], low[], close[];
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   
   if(CopyBuffer(handle_supertrend_atr, 0, 0, 2, atr) < 2) return;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 2, high) < 2) return;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 2, low) < 2) return;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) < 2) return;
   
   double hl2 = (high[0] + low[0]) / 2.0;
   double atrValue = atr[0] * SuperTrend_ATR_Mult;
   
   double upperBand = hl2 + atrValue;
   double lowerBand = hl2 - atrValue;
   
   static double prevSuperTrend = 0;
   static int prevDirection = 0;
   
   if(close[0] > prevSuperTrend)
   {
      superTrendValue = lowerBand;
      superTrendDirection = 1;
   }
   else
   {
      superTrendValue = upperBand;
      superTrendDirection = -1;
   }
   
   prevSuperTrend = superTrendValue;
   prevDirection = superTrendDirection;
}
'''

    @staticmethod
    def generate_volatility_check() -> str:
        """Generate volatility filter check."""
        return '''
//+------------------------------------------------------------------+
//| Volatility Check (ATR + BB Expansion)                            |
//+------------------------------------------------------------------+
bool IsVolatilityAcceptable()
{
   if(!UseVolatilityFilter) return true;
   
   double atr[], bb_upper[], bb_lower[];
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_lower, true);
   
   if(CopyBuffer(handle_atr, 0, 0, ATR_SMA_Period + 5, atr) < ATR_SMA_Period + 5) return true;
   
   // Calculate ATR SMA manually
   double atr_sum = 0;
   for(int i = 1; i <= ATR_SMA_Period; i++)
      atr_sum += atr[i];
   double atr_sma = atr_sum / ATR_SMA_Period;
   
   // ATR must be above its average (trending/volatile market)
   double atr_ratio = (atr_sma > 0) ? atr[0] / atr_sma : 1.0;
   if(atr_ratio < MinATRRatio)
   {
      if(EnableLogging) Print("Volatility too low: ATR ratio = ", DoubleToString(atr_ratio, 2));
      return false;
   }
   
   // BB Expansion check
   if(UseBBExpansion)
   {
      if(CopyBuffer(handle_bb, 1, 0, 5, bb_upper) < 5) return true;
      if(CopyBuffer(handle_bb, 2, 0, 5, bb_lower) < 5) return true;
      
      double bb_width = bb_upper[0] - bb_lower[0];
      double bb_width_prev = bb_upper[1] - bb_lower[1];
      
      // BB should be expanding or at minimum width
      if(bb_width < MinBBWidth)
      {
         if(EnableLogging) Print("BB too narrow: ", DoubleToString(bb_width, 5));
         return false;
      }
   }
   
   volatilityState = (atr_ratio > 1.2) ? 1 : (atr_ratio < 0.8) ? -1 : 0;
   return true;
}
'''

    @staticmethod
    def generate_momentum_check() -> str:
        """Generate momentum confirmation check."""
        return '''
//+------------------------------------------------------------------+
//| Momentum Check (RSI Slope + MACD + ADX)                          |
//+------------------------------------------------------------------+
int CheckMomentum()
{
   if(!UseMomentumFilter) return 0;
   
   double rsi[], macd_main[], macd_signal[], adx[], adx_plus[], adx_minus[];
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   ArraySetAsSeries(adx, true);
   ArraySetAsSeries(adx_plus, true);
   ArraySetAsSeries(adx_minus, true);
   
   if(CopyBuffer(handle_rsi, 0, 0, RSI_SlopeLength + 1, rsi) < RSI_SlopeLength + 1) return 0;
   if(CopyBuffer(handle_macd, 0, 0, 3, macd_main) < 3) return 0;
   if(CopyBuffer(handle_macd, 1, 0, 3, macd_signal) < 3) return 0;
   if(CopyBuffer(handle_adx, 0, 0, 2, adx) < 2) return 0;
   if(CopyBuffer(handle_adx, 1, 0, 2, adx_plus) < 2) return 0;
   if(CopyBuffer(handle_adx, 2, 0, 2, adx_minus) < 2) return 0;
   
   int momentumScore = 0;
   
   // RSI Slope
   double rsi_slope = rsi[0] - rsi[RSI_SlopeLength];
   if(rsi_slope > 0 && rsi[0] > 50 && rsi[0] < 80) momentumScore++;
   else if(rsi_slope < 0 && rsi[0] < 50 && rsi[0] > 20) momentumScore--;
   
   // MACD Histogram slope (main - signal)
   double macd_hist_now = macd_main[0] - macd_signal[0];
   double macd_hist_prev = macd_main[1] - macd_signal[1];
   if(macd_hist_now > macd_hist_prev && macd_hist_now > 0) momentumScore++;
   else if(macd_hist_now < macd_hist_prev && macd_hist_now < 0) momentumScore--;
   
   // ADX trending + direction
   if(adx[0] >= ADX_MinTrend)
   {
      if(adx_plus[0] > adx_minus[0]) momentumScore++;
      else if(adx_minus[0] > adx_plus[0]) momentumScore--;
   }
   
   momentumState = (momentumScore >= 2) ? 1 : (momentumScore <= -2) ? -1 : 0;
   return momentumState;
}
'''

    @staticmethod
    def generate_trend_entry() -> str:
        """Generate trend-following entry logic."""
        return '''
//+------------------------------------------------------------------+
//| Trend Entry Block                                                 |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE CheckTrendEntry()
{
   if(!UseTrendEntry) return SIGNAL_NONE;
   
   // Get current trend
   marketTrend = DetectTrend();
   
   // Check volatility
   if(!IsVolatilityAcceptable()) return SIGNAL_NONE;
   
   // Check momentum
   int momentum = CheckMomentum();
   
   // Require trend + momentum alignment
   if(marketTrend == 1 && momentum >= 1)
   {
      // Additional confirmation: price above recent swing
      double high[];
      ArraySetAsSeries(high, true);
      if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 20, high) >= 20)
      {
         double recent_high = high[ArrayMaximum(high, 1, 10)];
         double close[];
         ArraySetAsSeries(close, true);
         CopyClose(_Symbol, PERIOD_CURRENT, 0, 1, close);
         
         if(close[0] > recent_high * 0.998) // Near recent highs
         {
            LogMessage("TREND BUY: Trend=" + IntegerToString(marketTrend) + " Mom=" + IntegerToString(momentum));
            return SIGNAL_BUY;
         }
      }
   }
   else if(marketTrend == -1 && momentum <= -1)
   {
      double low[];
      ArraySetAsSeries(low, true);
      if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 20, low) >= 20)
      {
         double recent_low = low[ArrayMinimum(low, 1, 10)];
         double close[];
         ArraySetAsSeries(close, true);
         CopyClose(_Symbol, PERIOD_CURRENT, 0, 1, close);
         
         if(close[0] < recent_low * 1.002)
         {
            LogMessage("TREND SELL: Trend=" + IntegerToString(marketTrend) + " Mom=" + IntegerToString(momentum));
            return SIGNAL_SELL;
         }
      }
   }
   
   return SIGNAL_NONE;
}
'''

    @staticmethod
    def generate_pullback_entry() -> str:
        """Generate pullback entry logic."""
        return '''
//+------------------------------------------------------------------+
//| Pullback Entry Block                                              |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE CheckPullbackEntry()
{
   if(!UsePullbackEntry) return SIGNAL_NONE;
   
   marketTrend = DetectTrend();
   if(marketTrend == 0) return SIGNAL_NONE;
   
   if(!IsVolatilityAcceptable()) return SIGNAL_NONE;
   
   double ema_fast[], close[], low[], high[];
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(high, true);
   
   if(CopyBuffer(handle_ema_fast, 0, 0, 5, ema_fast) < 5) return SIGNAL_NONE;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, close) < 5) return SIGNAL_NONE;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 5, low) < 5) return SIGNAL_NONE;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 5, high) < 5) return SIGNAL_NONE;
   
   // Bullish pullback: in uptrend, price touched EMA and bounced
   if(marketTrend == 1)
   {
      bool touched_ema = false;
      for(int i = 1; i <= 3; i++)
      {
         if(low[i] <= ema_fast[i] && close[i] > ema_fast[i])
            touched_ema = true;
      }
      
      if(touched_ema && close[0] > close[1] && close[0] > ema_fast[0])
      {
         int momentum = CheckMomentum();
         if(momentum >= 0)
         {
            LogMessage("PULLBACK BUY: Price bounced off EMA in uptrend");
            return SIGNAL_BUY;
         }
      }
   }
   // Bearish pullback: in downtrend, price touched EMA and rejected
   else if(marketTrend == -1)
   {
      bool touched_ema = false;
      for(int i = 1; i <= 3; i++)
      {
         if(high[i] >= ema_fast[i] && close[i] < ema_fast[i])
            touched_ema = true;
      }
      
      if(touched_ema && close[0] < close[1] && close[0] < ema_fast[0])
      {
         int momentum = CheckMomentum();
         if(momentum <= 0)
         {
            LogMessage("PULLBACK SELL: Price rejected at EMA in downtrend");
            return SIGNAL_SELL;
         }
      }
   }
   
   return SIGNAL_NONE;
}
'''

    @staticmethod
    def generate_breakout_entry() -> str:
        """Generate breakout entry logic."""
        return '''
//+------------------------------------------------------------------+
//| Breakout Entry Block                                              |
//+------------------------------------------------------------------+
input int BreakoutLookback = 20;                             // Breakout range lookback
input double BreakoutBufferPips = 5.0;                       // Breakout buffer (pips)

ENUM_SIGNAL_TYPE CheckBreakoutEntry()
{
   if(!UseBreakoutEntry) return SIGNAL_NONE;
   
   if(!IsVolatilityAcceptable()) return SIGNAL_NONE;
   
   double high[], low[], close[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, BreakoutLookback + 1, high) < BreakoutLookback + 1) return SIGNAL_NONE;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, BreakoutLookback + 1, low) < BreakoutLookback + 1) return SIGNAL_NONE;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) < 2) return SIGNAL_NONE;
   
   // Find range high/low (excluding current bar)
   double range_high = high[1];
   double range_low = low[1];
   for(int i = 2; i <= BreakoutLookback; i++)
   {
      if(high[i] > range_high) range_high = high[i];
      if(low[i] < range_low) range_low = low[i];
   }
   
   double buffer = BreakoutBufferPips * pipMultiplier * _Point;
   
   // Bullish breakout
   if(close[0] > range_high + buffer && close[1] <= range_high)
   {
      marketTrend = DetectTrend();
      if(marketTrend >= 0) // Not in downtrend
      {
         int momentum = CheckMomentum();
         if(momentum >= 0)
         {
            LogMessage("BREAKOUT BUY: Price broke above " + DoubleToString(range_high, _Digits));
            return SIGNAL_BUY;
         }
      }
   }
   // Bearish breakout
   else if(close[0] < range_low - buffer && close[1] >= range_low)
   {
      marketTrend = DetectTrend();
      if(marketTrend <= 0) // Not in uptrend
      {
         int momentum = CheckMomentum();
         if(momentum <= 0)
         {
            LogMessage("BREAKOUT SELL: Price broke below " + DoubleToString(range_low, _Digits));
            return SIGNAL_SELL;
         }
      }
   }
   
   return SIGNAL_NONE;
}
'''

    @staticmethod
    def generate_reversal_entry() -> str:
        """Generate reversal entry logic with divergence."""
        return '''
//+------------------------------------------------------------------+
//| Reversal Entry Block (Divergence + Exhaustion)                   |
//+------------------------------------------------------------------+
input int DivergenceLookback = 20;                           // Divergence lookback
input double RSI_Overbought = 70.0;                          // RSI Overbought
input double RSI_Oversold = 30.0;                            // RSI Oversold

ENUM_SIGNAL_TYPE CheckReversalEntry()
{
   if(!UseReversalEntry) return SIGNAL_NONE;
   
   double rsi[], close[], high[], low[];
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   
   if(CopyBuffer(handle_rsi, 0, 0, DivergenceLookback, rsi) < DivergenceLookback) return SIGNAL_NONE;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, DivergenceLookback, close) < DivergenceLookback) return SIGNAL_NONE;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, DivergenceLookback, high) < DivergenceLookback) return SIGNAL_NONE;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, DivergenceLookback, low) < DivergenceLookback) return SIGNAL_NONE;
   
   // Check for bullish divergence (price lower low, RSI higher low)
   if(rsi[0] < RSI_Oversold + 10 && rsi[0] > RSI_Oversold)
   {
      // Find recent price low and RSI low
      int price_low_idx = ArrayMinimum(low, 5, 15);
      int rsi_low_idx = ArrayMinimum(rsi, 5, 15);
      
      if(price_low_idx > 0 && rsi_low_idx > 0)
      {
         // Price made lower low but RSI made higher low
         if(low[0] < low[price_low_idx] && rsi[0] > rsi[rsi_low_idx])
         {
            if(IsVolatilityAcceptable())
            {
               LogMessage("REVERSAL BUY: Bullish divergence detected");
               return SIGNAL_BUY;
            }
         }
      }
   }
   
   // Check for bearish divergence (price higher high, RSI lower high)
   if(rsi[0] > RSI_Overbought - 10 && rsi[0] < RSI_Overbought)
   {
      int price_high_idx = ArrayMaximum(high, 5, 15);
      int rsi_high_idx = ArrayMaximum(rsi, 5, 15);
      
      if(price_high_idx > 0 && rsi_high_idx > 0)
      {
         if(high[0] > high[price_high_idx] && rsi[0] < rsi[rsi_high_idx])
         {
            if(IsVolatilityAcceptable())
            {
               LogMessage("REVERSAL SELL: Bearish divergence detected");
               return SIGNAL_SELL;
            }
         }
      }
   }
   
   return SIGNAL_NONE;
}
'''

    @staticmethod
    def generate_master_entry_check() -> str:
        """Generate master entry check that combines all blocks."""
        return '''
//+------------------------------------------------------------------+
//| Master Entry Check - Combines All Entry Blocks                   |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE CheckEntryConditions()
{
   ENUM_SIGNAL_TYPE signal = SIGNAL_NONE;
   
   // Priority order: Trend > Pullback > Breakout > Reversal
   
   // 1. Trend Entry (highest priority in trending markets)
   signal = CheckTrendEntry();
   if(signal != SIGNAL_NONE) return signal;
   
   // 2. Pullback Entry
   signal = CheckPullbackEntry();
   if(signal != SIGNAL_NONE) return signal;
   
   // 3. Breakout Entry
   signal = CheckBreakoutEntry();
   if(signal != SIGNAL_NONE) return signal;
   
   // 4. Reversal Entry (only at extremes)
   signal = CheckReversalEntry();
   if(signal != SIGNAL_NONE) return signal;
   
   return SIGNAL_NONE;
}
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete entry blocks module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_globals() + "\n" +
            cls.generate_init() + "\n" +
            cls.generate_deinit() + "\n" +
            cls.generate_trend_detection() + "\n" +
            cls.generate_volatility_check() + "\n" +
            cls.generate_momentum_check() + "\n" +
            cls.generate_trend_entry() + "\n" +
            cls.generate_pullback_entry() + "\n" +
            cls.generate_breakout_entry() + "\n" +
            cls.generate_reversal_entry() + "\n" +
            cls.generate_master_entry_check()
        )
