"""
Trend Filter Templates
MQL5 template blocks for trend confirmation filters.
"""


class TrendFilterTemplates:
    """
    Generates MQL5 code blocks for trend filtering.
    
    Includes:
    - EMA stack filter (8/21/55)
    - ADX trend strength filter
    - Higher timeframe alignment
    - Multiple MA confirmation
    """
    
    @staticmethod
    def generate_ema_stack_filter() -> str:
        """Generate triple EMA stack trend filter."""
        return '''
//+------------------------------------------------------------------+
//| EMA Stack Filter - Triple EMA Trend Confirmation                  |
//+------------------------------------------------------------------+
int GetEMAStackTrend(double ema_fast, double ema_mid, double ema_slow)
{
   // Bullish: EMA8 > EMA21 > EMA55
   if(ema_fast > ema_mid && ema_mid > ema_slow)
      return 1;
   
   // Bearish: EMA8 < EMA21 < EMA55
   if(ema_fast < ema_mid && ema_mid < ema_slow)
      return -1;
   
   // Mixed/Neutral
   return 0;
}

//--- Check if price respects EMA structure
bool IsPriceInTrend(double price, double ema_fast, double ema_mid, double ema_slow, int direction)
{
   if(direction == 1) // Bullish
   {
      return (price > ema_fast && ema_fast > ema_mid && ema_mid > ema_slow);
   }
   else if(direction == -1) // Bearish
   {
      return (price < ema_fast && ema_fast < ema_mid && ema_mid < ema_slow);
   }
   return false;
}

//--- Check for pullback to EMA
bool IsPullbackToEMA(double low, double high, double ema, int direction)
{
   if(direction == 1) // Bullish pullback
   {
      return (low <= ema && low > ema * 0.99); // Touched but not broken
   }
   else if(direction == -1) // Bearish pullback
   {
      return (high >= ema && high < ema * 1.01);
   }
   return false;
}
'''

    @staticmethod
    def generate_adx_filter() -> str:
        """Generate ADX trend strength filter."""
        return '''
//+------------------------------------------------------------------+
//| ADX Trend Strength Filter                                         |
//+------------------------------------------------------------------+
input double ADXTrendThreshold = 25.0;                       // Min ADX for trend
input double ADXStrongTrend = 40.0;                          // ADX for strong trend
input double ADXWeakThreshold = 20.0;                        // ADX for weak/ranging

bool IsStrongTrend(double adx_value)
{
   return adx_value >= ADXStrongTrend;
}

bool IsTrending(double adx_value)
{
   return adx_value >= ADXTrendThreshold;
}

bool IsRanging(double adx_value)
{
   return adx_value < ADXWeakThreshold;
}

//--- Get trend direction from DI lines
int GetADXDirection(double plus_di, double minus_di)
{
   if(plus_di > minus_di)
      return 1;  // Bullish
   else if(minus_di > plus_di)
      return -1; // Bearish
   return 0;     // Neutral
}

//--- Check if ADX confirms the signal direction
bool ADXConfirmsSignal(double adx, double plus_di, double minus_di, int signal_direction)
{
   if(!IsTrending(adx))
      return false;
   
   int adx_direction = GetADXDirection(plus_di, minus_di);
   return (adx_direction == signal_direction);
}
'''

    @staticmethod
    def generate_htf_alignment() -> str:
        """Generate higher timeframe alignment filter."""
        return '''
//+------------------------------------------------------------------+
//| Higher Timeframe Alignment Filter                                 |
//+------------------------------------------------------------------+
input bool UseHTFFilter = true;                              // Use HTF trend filter
input bool RequireHTFAlignment = true;                       // Require HTF alignment

int htfTrend = 0; // 1 = bullish, -1 = bearish, 0 = neutral

//--- Get higher timeframe based on current TF
ENUM_TIMEFRAMES GetHTFPeriod()
{
   ENUM_TIMEFRAMES currentTF = Period();
   
   switch(currentTF)
   {
      case PERIOD_M1:  return PERIOD_M5;
      case PERIOD_M5:  return PERIOD_M15;
      case PERIOD_M15: return PERIOD_H1;
      case PERIOD_M30: return PERIOD_H1;
      case PERIOD_H1:  return PERIOD_H4;
      case PERIOD_H4:  return PERIOD_D1;
      default:         return PERIOD_H1;
   }
}

//--- Update HTF trend from EMA
void UpdateHTFTrend(int htf_ema_handle)
{
   if(!UseHTFFilter)
   {
      htfTrend = 0;
      return;
   }
   
   double htf_ema[];
   ArraySetAsSeries(htf_ema, true);
   
   if(CopyBuffer(htf_ema_handle, 0, 0, 3, htf_ema) < 3)
   {
      htfTrend = 0;
      return;
   }
   
   // Get HTF close price
   double htf_close[];
   ArraySetAsSeries(htf_close, true);
   if(CopyClose(_Symbol, GetHTFPeriod(), 0, 2, htf_close) < 2)
   {
      htfTrend = 0;
      return;
   }
   
   // Determine HTF trend
   if(htf_close[0] > htf_ema[0] && htf_ema[0] > htf_ema[1])
      htfTrend = 1;  // Bullish
   else if(htf_close[0] < htf_ema[0] && htf_ema[0] < htf_ema[1])
      htfTrend = -1; // Bearish
   else
      htfTrend = 0;  // Neutral
}

//--- Check if signal aligns with HTF trend
bool IsHTFAligned(int signal_direction)
{
   if(!UseHTFFilter)
      return true;
   
   if(!RequireHTFAlignment)
      return true;
   
   // Allow if HTF is neutral
   if(htfTrend == 0)
      return true;
   
   // Require alignment
   return (htfTrend == signal_direction);
}
'''

    @staticmethod
    def generate_multi_ma_confirmation() -> str:
        """Generate multiple moving average confirmation."""
        return '''
//+------------------------------------------------------------------+
//| Multi-MA Confirmation Filter                                      |
//+------------------------------------------------------------------+

//--- Count how many MAs confirm the direction
int CountMAConfirmations(double price, double ma1, double ma2, double ma3, int direction)
{
   int confirmations = 0;
   
   if(direction == 1) // Bullish
   {
      if(price > ma1) confirmations++;
      if(price > ma2) confirmations++;
      if(price > ma3) confirmations++;
      if(ma1 > ma2) confirmations++;
      if(ma2 > ma3) confirmations++;
   }
   else if(direction == -1) // Bearish
   {
      if(price < ma1) confirmations++;
      if(price < ma2) confirmations++;
      if(price < ma3) confirmations++;
      if(ma1 < ma2) confirmations++;
      if(ma2 < ma3) confirmations++;
   }
   
   return confirmations;
}

//--- Check if MAs are fanning (trend gaining momentum)
bool AreMAsFanning(double ma_fast_now, double ma_mid_now, double ma_slow_now,
                   double ma_fast_prev, double ma_mid_prev, double ma_slow_prev,
                   int direction)
{
   if(direction == 1) // Bullish fanning
   {
      double spread_now = ma_fast_now - ma_slow_now;
      double spread_prev = ma_fast_prev - ma_slow_prev;
      return (spread_now > spread_prev && spread_now > 0);
   }
   else if(direction == -1) // Bearish fanning
   {
      double spread_now = ma_slow_now - ma_fast_now;
      double spread_prev = ma_slow_prev - ma_fast_prev;
      return (spread_now > spread_prev && spread_now > 0);
   }
   return false;
}

//--- Check if MAs are compressing (potential reversal)
bool AreMAsCompressing(double ma_fast_now, double ma_slow_now,
                       double ma_fast_prev, double ma_slow_prev)
{
   double spread_now = MathAbs(ma_fast_now - ma_slow_now);
   double spread_prev = MathAbs(ma_fast_prev - ma_slow_prev);
   
   return (spread_now < spread_prev);
}

//--- Calculate MA slope
double CalculateMASlope(double ma_now, double ma_prev, int bars_back)
{
   return (ma_now - ma_prev) / bars_back;
}

//--- Check if trend is accelerating
bool IsTrendAccelerating(double slope_now, double slope_prev, int direction)
{
   if(direction == 1)
      return (slope_now > slope_prev && slope_now > 0);
   else if(direction == -1)
      return (slope_now < slope_prev && slope_now < 0);
   return false;
}
'''

    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for trend filters."""
        return '''
input group "=== Trend Filters ==="
input bool UseEMAStackFilter = true;                         // Use EMA Stack Filter
input int EMAFastPeriod = 8;                                 // Fast EMA Period
input int EMAMidPeriod = 21;                                 // Mid EMA Period
input int EMASlowPeriod = 55;                                // Slow EMA Period

input bool UseADXFilter = true;                              // Use ADX Filter
input int ADXPeriod = 14;                                    // ADX Period
input double ADXMinTrend = 25.0;                             // Min ADX for trend

input bool UseHTFFilter = true;                              // Use HTF Alignment
input bool RequireHTFAlignment = true;                       // Require HTF Alignment
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete trend filter module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_ema_stack_filter() +
            cls.generate_adx_filter() +
            cls.generate_htf_alignment() +
            cls.generate_multi_ma_confirmation()
        )
