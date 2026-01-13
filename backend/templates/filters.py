"""
Filter Templates
MQL5 template blocks for trade filtering.
"""


class FilterTemplates:
    """
    Generates MQL5 code blocks for various trade filters.
    
    Includes:
    - Spread filter
    - Slippage filter
    - News time filter
    - Session filters
    - Volatility filter
    """
    
    @staticmethod
    def generate_spread_filter() -> str:
        """Generate spread filter code."""
        return '''
//+------------------------------------------------------------------+
//| Spread Filter                                                     |
//+------------------------------------------------------------------+
input bool UseSpreadFilter = true;                           // Enable Spread Filter
input int MaxSpreadPoints = 30;                              // Max spread (points)
input bool DynamicSpreadCheck = true;                        // Check spread on every tick

bool IsSpreadAcceptable()
{
   if(!UseSpreadFilter)
      return true;
   
   long current_spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   
   if(current_spread > MaxSpreadPoints)
   {
      if(EnableLogging) Print("Spread too high: ", current_spread, " > ", MaxSpreadPoints);
      return false;
   }
   
   return true;
}

//--- Get average spread over last N ticks
double GetAverageSpread(int ticks = 10)
{
   static double spread_history[];
   static int spread_index = 0;
   static bool initialized = false;
   
   if(!initialized)
   {
      ArrayResize(spread_history, ticks);
      ArrayInitialize(spread_history, 0);
      initialized = true;
   }
   
   // Add current spread to history
   spread_history[spread_index] = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   spread_index = (spread_index + 1) % ticks;
   
   // Calculate average
   double sum = 0;
   for(int i = 0; i < ticks; i++)
      sum += spread_history[i];
   
   return sum / ticks;
}
'''

    @staticmethod
    def generate_slippage_filter() -> str:
        """Generate slippage control code."""
        return '''
//+------------------------------------------------------------------+
//| Slippage Filter                                                   |
//+------------------------------------------------------------------+
input int MaxSlippagePoints = 5;                             // Max slippage (points)
input bool TrackSlippage = true;                             // Track slippage history

double totalSlippage = 0.0;
int slippageCount = 0;

double CalculateSlippage(double requested_price, double filled_price)
{
   double slippage = MathAbs(filled_price - requested_price) / _Point;
   
   if(TrackSlippage)
   {
      totalSlippage += slippage;
      slippageCount++;
      
      if(EnableLogging && slippage > 0)
         Print("Slippage: ", slippage, " points");
   }
   
   return slippage;
}

double GetAverageSlippage()
{
   if(slippageCount == 0)
      return 0.0;
   return totalSlippage / slippageCount;
}
'''

    @staticmethod
    def generate_news_filter() -> str:
        """Generate news time filter code."""
        return '''
//+------------------------------------------------------------------+
//| News Time Filter                                                  |
//+------------------------------------------------------------------+
input bool UseNewsFilter = true;                             // Enable News Filter
input int NewsMinutesBefore = 30;                            // Stop trading X mins before
input int NewsMinutesAfter = 15;                             // Resume trading X mins after
input bool AvoidNFP = true;                                  // Avoid NFP day
input ENUM_DAY_OF_WEEK NFPDay = FRIDAY;                      // NFP day

datetime nextNewsTime = 0;
bool isNewsTime = false;

//--- Check if current time is near news
void UpdateNewsFilter()
{
   if(!UseNewsFilter)
   {
      isNewsTime = false;
      return;
   }
   
   // Check for NFP
   if(AvoidNFP)
   {
      MqlDateTime current;
      TimeToStruct(TimeCurrent(), current);
      
      // NFP is typically first Friday of the month
      if(current.day_of_week == NFPDay && current.day <= 7)
      {
         // First Friday - avoid high-impact hours (usually 8:30 AM ET = 12:30 PM GMT)
         if(current.hour >= 12 && current.hour <= 16)
         {
            isNewsTime = true;
            if(EnableLogging) Print("NFP period - trading paused");
            return;
         }
      }
   }
   
   // Check if we're within news blackout period
   if(nextNewsTime > 0)
   {
      datetime now = TimeCurrent();
      datetime news_start = nextNewsTime - NewsMinutesBefore * 60;
      datetime news_end = nextNewsTime + NewsMinutesAfter * 60;
      
      if(now >= news_start && now <= news_end)
      {
         isNewsTime = true;
         return;
      }
   }
   
   isNewsTime = false;
}

bool IsNewsTimeSafe()
{
   UpdateNewsFilter();
   return !isNewsTime;
}

//--- Set next expected news time (can be updated externally)
void SetNextNewsTime(datetime news_time)
{
   nextNewsTime = news_time;
}
'''

    @staticmethod
    def generate_session_filter() -> str:
        """Generate trading session filter code."""
        return '''
//+------------------------------------------------------------------+
//| Session Filter                                                    |
//+------------------------------------------------------------------+
input bool UseSessionFilter = true;                          // Enable Session Filter
input bool TradeLondon = true;                               // Trade London Session
input bool TradeNewYork = true;                              // Trade New York Session
input bool TradeAsian = false;                               // Trade Asian Session
input bool TradeLondonNYOverlap = true;                      // Trade London-NY Overlap
input bool AvoidMarketOpen = true;                           // Avoid first 15 min
input bool AvoidMarketClose = true;                          // Avoid last 15 min
input bool AvoidSundayOpen = true;                           // Avoid Sunday open
input bool AvoidFridayClose = true;                          // Avoid Friday close
input int FridayCloseHour = 20;                              // Friday stop hour (server)

bool IsValidSession()
{
   if(!UseSessionFilter)
      return true;
   
   MqlDateTime server_time;
   TimeToStruct(TimeCurrent(), server_time);
   int hour = server_time.hour;
   int minute = server_time.min;
   ENUM_DAY_OF_WEEK day = (ENUM_DAY_OF_WEEK)server_time.day_of_week;
   
   // Sunday/Monday filters
   if(AvoidSundayOpen)
   {
      if(day == SUNDAY)
         return false;
      if(day == MONDAY && hour < 2)
         return false;
   }
   
   // Friday close filter
   if(AvoidFridayClose && day == FRIDAY && hour >= FridayCloseHour)
   {
      if(EnableLogging) Print("Friday close period - no new trades");
      return false;
   }
   
   // Market open/close filters
   if(AvoidMarketOpen && minute < 15 && (hour == 0 || hour == 8 || hour == 13))
      return false;
   
   if(AvoidMarketClose && minute > 45 && (hour == 7 || hour == 12 || hour == 21))
      return false;
   
   // Session checks (assuming server time is close to GMT)
   bool in_session = false;
   
   // London: 08:00 - 16:00 GMT
   if(TradeLondon && hour >= 8 && hour < 16)
   {
      in_session = true;
      if(EnableLogging) Print("Session: London");
   }
   
   // New York: 13:00 - 21:00 GMT
   if(TradeNewYork && hour >= 13 && hour < 21)
   {
      in_session = true;
      if(EnableLogging) Print("Session: New York");
   }
   
   // London-NY Overlap: 13:00 - 16:00 GMT
   if(TradeLondonNYOverlap && hour >= 13 && hour < 16)
   {
      in_session = true;
      if(EnableLogging) Print("Session: London-NY Overlap");
   }
   
   // Asian: 00:00 - 08:00 GMT
   if(TradeAsian && hour >= 0 && hour < 8)
   {
      in_session = true;
      if(EnableLogging) Print("Session: Asian");
   }
   
   return in_session;
}
'''

    @staticmethod
    def generate_volatility_filter() -> str:
        """Generate volatility filter code."""
        return '''
//+------------------------------------------------------------------+
//| Volatility Filter (ATR-based)                                     |
//+------------------------------------------------------------------+
input bool UseVolatilityFilter = true;                       // Enable Volatility Filter
input double MinATRMultiplier = 0.5;                         // Min ATR (vs average)
input double MaxATRMultiplier = 3.0;                         // Max ATR (vs average)
input int VolatilityATRPeriod = 14;                          // ATR period

int handle_volatility_atr = INVALID_HANDLE;
double averageATR = 0.0;

bool InitVolatilityFilter()
{
   if(!UseVolatilityFilter)
      return true;
   
   handle_volatility_atr = iATR(_Symbol, PERIOD_CURRENT, VolatilityATRPeriod);
   return (handle_volatility_atr != INVALID_HANDLE);
}

void UpdateAverageATR()
{
   if(!UseVolatilityFilter || handle_volatility_atr == INVALID_HANDLE)
      return;
   
   double atr_values[];
   ArraySetAsSeries(atr_values, true);
   
   if(CopyBuffer(handle_volatility_atr, 0, 0, 50, atr_values) >= 50)
   {
      double sum = 0;
      for(int i = 0; i < 50; i++)
         sum += atr_values[i];
      averageATR = sum / 50.0;
   }
}

bool IsVolatilityAcceptable()
{
   if(!UseVolatilityFilter || handle_volatility_atr == INVALID_HANDLE)
      return true;
   
   double current_atr[];
   ArraySetAsSeries(current_atr, true);
   
   if(CopyBuffer(handle_volatility_atr, 0, 0, 1, current_atr) < 1)
      return true;
   
   if(averageATR == 0)
   {
      UpdateAverageATR();
      return true; // Allow trading while calibrating
   }
   
   double atr_ratio = current_atr[0] / averageATR;
   
   // Too low volatility - skip
   if(atr_ratio < MinATRMultiplier)
   {
      if(EnableLogging) Print("Volatility too low: ", DoubleToString(atr_ratio, 2), "x average");
      return false;
   }
   
   // Too high volatility - skip
   if(atr_ratio > MaxATRMultiplier)
   {
      if(EnableLogging) Print("Volatility too high: ", DoubleToString(atr_ratio, 2), "x average");
      return false;
   }
   
   return true;
}
'''

    @staticmethod
    def generate_combined_filter() -> str:
        """Generate combined filter check function."""
        return '''
//+------------------------------------------------------------------+
//| Combined Filter Check                                             |
//+------------------------------------------------------------------+
bool PassesAllFilters()
{
   // Spread filter
   if(!IsSpreadAcceptable())
      return false;
   
   // News filter
   if(!IsNewsTimeSafe())
      return false;
   
   // Session filter
   if(!IsValidSession())
      return false;
   
   // Volatility filter
   if(!IsVolatilityAcceptable())
      return false;
   
   // Daily limits
   if(!CheckDailyLimits())
      return false;
   
   // Drawdown protection
   if(!IsDrawdownSafe())
      return false;
   
   return true;
}
'''

    @staticmethod
    def generate_inputs() -> str:
        """Generate all filter input parameters."""
        return '''
input group "=== Filters ==="
input bool UseSpreadFilter = true;                           // Enable Spread Filter
input int MaxSpreadPoints = 30;                              // Max spread (points)
input bool UseNewsFilter = true;                             // Enable News Filter
input int NewsMinutesBefore = 30;                            // Mins before news
input int NewsMinutesAfter = 15;                             // Mins after news
input bool UseSessionFilter = true;                          // Enable Session Filter
input bool UseVolatilityFilter = true;                       // Enable Volatility Filter
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete filter module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_spread_filter() +
            cls.generate_slippage_filter() +
            cls.generate_news_filter() +
            cls.generate_session_filter() +
            cls.generate_volatility_filter() +
            cls.generate_combined_filter()
        )
