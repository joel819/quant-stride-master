"""
Protection Blocks
Safety and failure protection for prop-firm safe trading.
"""


class ProtectionBlocks:
    """
    Protection blocks for EA safety.
    
    Includes:
    - Drawdown guard (circuit breaker)
    - Max open trades limiter
    - Volatility kill switch
    - News kill switch
    """
    
    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for protection blocks."""
        return '''
//+------------------------------------------------------------------+
//|                  PROTECTION BLOCK PARAMETERS                     |
//+------------------------------------------------------------------+
input group "=== Drawdown Protection ==="
input bool UseDrawdownGuard = true;                          // Enable Drawdown Guard
input double MaxDrawdownPercent = 5.0;                       // Max Daily Drawdown (%)
input double MaxTotalDrawdownPercent = 10.0;                 // Max Total Drawdown (%)
input bool CloseAllOnDrawdown = true;                        // Close all on DD breach
input bool HaltEAOnDrawdown = true;                          // Halt EA on DD breach

input group "=== Position Limits ==="
input int MaxOpenTrades = 1;                                 // Max Concurrent Trades
input int MaxDailyTrades = 5;                                // Max Trades per Day
input bool OneDirectionPerSession = false;                   // One direction per session

input group "=== Volatility Kill Switch ==="
input bool UseVolatilityKillSwitch = true;                   // Enable Volatility Kill
input double VolatilityKill_ATR_Mult = 3.0;                  // ATR spike multiplier
input int VolatilityKill_Cooldown_Mins = 30;                 // Cooldown after spike

input group "=== News Kill Switch ==="
input bool UseNewsKillSwitch = true;                         // Enable News Kill
input int News_MinutesBefore = 30;                           // Stop X mins before
input int News_MinutesAfter = 15;                            // Resume X mins after
input bool Block_NFP = true;                                 // Block during NFP
input bool Block_FOMC = true;                                // Block during FOMC
input bool Block_ECB = true;                                 // Block during ECB

input group "=== Equity Protection ==="
input bool UseEquityProtection = true;                       // Enable Equity Protection
input double EquityStopPercent = 8.0;                        // Equity stop (% of start)
input double EquityTargetPercent = 10.0;                     // Daily equity target (%)
'''

    @staticmethod
    def generate_globals() -> str:
        """Generate global variables for protection blocks."""
        return '''
//+------------------------------------------------------------------+
//|                   PROTECTION BLOCK GLOBALS                       |
//+------------------------------------------------------------------+
// Drawdown tracking
double startingBalance = 0;
double peakBalance = 0;
double dailyStartBalance = 0;
double currentDrawdownPercent = 0;
double dailyDrawdownPercent = 0;
bool drawdownHalt = false;

// Trade counting
int dailyTradeCount = 0;
datetime lastTradeDate = 0;
int sessionDirection = 0; // 1=Long, -1=Short, 0=None

// Kill switch states
bool volatilityKillActive = false;
datetime volatilityKillEndTime = 0;
bool newsKillActive = false;
datetime nextNewsTime = 0;

// Daily tracking
double dailyPnL = 0;
bool dailyTargetReached = false;
bool dailyLossLimitReached = false;
'''

    @staticmethod
    def generate_init() -> str:
        """Generate initialization for protection blocks."""
        return '''
//+------------------------------------------------------------------+
//| Initialize Protection Systems                                     |
//+------------------------------------------------------------------+
bool InitProtection()
{
   startingBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   peakBalance = startingBalance;
   dailyStartBalance = startingBalance;
   lastTradeDate = TimeCurrent();
   
   Print("Protection initialized. Starting balance: $", DoubleToString(startingBalance, 2));
   Print("Max DD: ", DoubleToString(MaxDrawdownPercent, 1), "% daily / ", 
         DoubleToString(MaxTotalDrawdownPercent, 1), "% total");
   
   return true;
}
'''

    @staticmethod
    def generate_drawdown_guard() -> str:
        """Generate drawdown protection logic."""
        return '''
//+------------------------------------------------------------------+
//| Drawdown Guard - Circuit Breaker                                  |
//+------------------------------------------------------------------+
void UpdateDrawdownStatus()
{
   if(!UseDrawdownGuard) return;
   
   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   // Update peak balance
   if(currentBalance > peakBalance)
   {
      peakBalance = currentBalance;
   }
   
   // Calculate total drawdown from peak
   currentDrawdownPercent = ((peakBalance - currentEquity) / peakBalance) * 100.0;
   
   // Calculate daily drawdown
   dailyDrawdownPercent = ((dailyStartBalance - currentEquity) / dailyStartBalance) * 100.0;
   
   // Check daily drawdown limit
   if(dailyDrawdownPercent >= MaxDrawdownPercent)
   {
      if(!dailyLossLimitReached)
      {
         dailyLossLimitReached = true;
         Print("*** DAILY DRAWDOWN LIMIT REACHED: ", DoubleToString(dailyDrawdownPercent, 2), "% ***");
         
         if(CloseAllOnDrawdown)
         {
            CloseAllPositions("Daily DD Limit");
         }
         
         if(HaltEAOnDrawdown)
         {
            drawdownHalt = true;
            Print("*** EA HALTED UNTIL TOMORROW ***");
         }
      }
   }
   
   // Check total drawdown limit
   if(currentDrawdownPercent >= MaxTotalDrawdownPercent)
   {
      if(!drawdownHalt)
      {
         drawdownHalt = true;
         Print("*** TOTAL DRAWDOWN LIMIT REACHED: ", DoubleToString(currentDrawdownPercent, 2), "% ***");
         
         if(CloseAllOnDrawdown)
         {
            CloseAllPositions("Total DD Limit");
         }
         Print("*** EA HALTED - MANUAL INTERVENTION REQUIRED ***");
      }
   }
}

//+------------------------------------------------------------------+
//| Close All Positions                                               |
//+------------------------------------------------------------------+
void CloseAllPositions(string reason)
{
   Print("CLOSING ALL POSITIONS: ", reason);
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == _Symbol && positionInfo.Magic() == MagicNumber)
         {
            trade.PositionClose(positionInfo.Ticket());
            Print("Closed position #", positionInfo.Ticket());
         }
      }
   }
}

bool IsDrawdownSafe()
{
   UpdateDrawdownStatus();
   return !drawdownHalt && !dailyLossLimitReached;
}
'''

    @staticmethod
    def generate_position_limits() -> str:
        """Generate position limit checks."""
        return '''
//+------------------------------------------------------------------+
//| Position Limit Checks                                             |
//+------------------------------------------------------------------+
bool CanOpenNewTrade(int direction)
{
   // Check drawdown first
   if(!IsDrawdownSafe()) return false;
   
   // Check max open trades
   int openCount = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == _Symbol && positionInfo.Magic() == MagicNumber)
            openCount++;
      }
   }
   
   if(openCount >= MaxOpenTrades)
   {
      if(EnableLogging) Print("Max open trades reached: ", openCount);
      return false;
   }
   
   // Check daily trade limit
   CheckNewDay();
   if(dailyTradeCount >= MaxDailyTrades)
   {
      if(EnableLogging) Print("Max daily trades reached: ", dailyTradeCount);
      return false;
   }
   
   // Check daily target
   if(dailyTargetReached)
   {
      if(EnableLogging) Print("Daily target already reached");
      return false;
   }
   
   // Check one direction per session
   if(OneDirectionPerSession && sessionDirection != 0)
   {
      if(direction != sessionDirection)
      {
         if(EnableLogging) Print("Session direction locked to ", (sessionDirection == 1 ? "LONG" : "SHORT"));
         return false;
      }
   }
   
   // Check kill switches
   if(!IsKillSwitchClear()) return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| Check for New Trading Day                                         |
//+------------------------------------------------------------------+
void CheckNewDay()
{
   MqlDateTime current, last;
   TimeToStruct(TimeCurrent(), current);
   TimeToStruct(lastTradeDate, last);
   
   if(current.day != last.day || current.mon != last.mon || current.year != last.year)
   {
      // New day - reset counters
      dailyTradeCount = 0;
      dailyPnL = 0;
      dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      dailyTargetReached = false;
      dailyLossLimitReached = false;
      sessionDirection = 0;
      drawdownHalt = false; // Reset daily halt
      lastTradeDate = TimeCurrent();
      
      Print("=== NEW TRADING DAY ===");
      Print("Daily start balance: $", DoubleToString(dailyStartBalance, 2));
   }
}

//+------------------------------------------------------------------+
//| Record Trade Opened                                               |
//+------------------------------------------------------------------+
void OnTradeOpened(int direction)
{
   dailyTradeCount++;
   
   if(OneDirectionPerSession && sessionDirection == 0)
   {
      sessionDirection = direction;
      Print("Session direction locked to ", (direction == 1 ? "LONG" : "SHORT"));
   }
   
   lastTradeTime = TimeCurrent();
}
'''

    @staticmethod
    def generate_volatility_kill_switch() -> str:
        """Generate volatility-based kill switch."""
        return '''
//+------------------------------------------------------------------+
//| Volatility Kill Switch                                            |
//+------------------------------------------------------------------+
void UpdateVolatilityKillSwitch()
{
   if(!UseVolatilityKillSwitch) return;
   
   // Check if cooldown is over
   if(volatilityKillActive && TimeCurrent() >= volatilityKillEndTime)
   {
      volatilityKillActive = false;
      Print("Volatility kill switch deactivated");
   }
   
   if(volatilityKillActive) return;
   
   // Check for ATR spike
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(handle_atr, 0, 0, 30, atr) < 30) return;
   
   // Calculate average ATR
   double atr_sum = 0;
   for(int i = 1; i < 30; i++)
      atr_sum += atr[i];
   double atr_avg = atr_sum / 29.0;
   
   // Check for spike
   if(atr[0] > atr_avg * VolatilityKill_ATR_Mult)
   {
      volatilityKillActive = true;
      volatilityKillEndTime = TimeCurrent() + VolatilityKill_Cooldown_Mins * 60;
      Print("*** VOLATILITY KILL SWITCH ACTIVATED ***");
      Print("ATR: ", DoubleToString(atr[0], _Digits), " > ", DoubleToString(atr_avg * VolatilityKill_ATR_Mult, _Digits));
      Print("Will resume at: ", TimeToString(volatilityKillEndTime));
   }
}

bool IsVolatilityKillClear()
{
   UpdateVolatilityKillSwitch();
   return !volatilityKillActive;
}
'''

    @staticmethod
    def generate_news_kill_switch() -> str:
        """Generate news-based kill switch."""
        return '''
//+------------------------------------------------------------------+
//| News Kill Switch                                                  |
//+------------------------------------------------------------------+
void UpdateNewsKillSwitch()
{
   if(!UseNewsKillSwitch) return;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Check NFP (First Friday of month, usually 8:30 AM ET = 13:30 GMT)
   if(Block_NFP)
   {
      if(dt.day_of_week == FRIDAY && dt.day <= 7) // First Friday
      {
         if(dt.hour >= 12 && dt.hour <= 15) // NFP window
         {
            if(!newsKillActive)
            {
               newsKillActive = true;
               Print("*** NEWS KILL: NFP Window ***");
            }
            return;
         }
      }
   }
   
   // Check FOMC (Usually Wednesday, 2:00 PM ET = 19:00 GMT)
   if(Block_FOMC)
   {
      if(dt.day_of_week == WEDNESDAY && dt.hour >= 18 && dt.hour <= 21)
      {
         if(!newsKillActive)
         {
            newsKillActive = true;
            Print("*** NEWS KILL: FOMC Window ***");
         }
         return;
      }
   }
   
   // Check ECB (Usually Thursday, varies)
   if(Block_ECB)
   {
      if(dt.day_of_week == THURSDAY && dt.hour >= 12 && dt.hour <= 15)
      {
         if(!newsKillActive)
         {
            newsKillActive = true;
            Print("*** NEWS KILL: ECB Window ***");
         }
         return;
      }
   }
   
   // Clear kill if no active news
   if(newsKillActive)
   {
      newsKillActive = false;
      Print("News kill switch cleared");
   }
}

bool IsNewsKillClear()
{
   UpdateNewsKillSwitch();
   return !newsKillActive;
}
'''

    @staticmethod
    def generate_equity_protection() -> str:
        """Generate equity-based protection."""
        return '''
//+------------------------------------------------------------------+
//| Equity Protection                                                 |
//+------------------------------------------------------------------+
void CheckEquityProtection()
{
   if(!UseEquityProtection) return;
   
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double equityThreshold = dailyStartBalance * (1.0 - EquityStopPercent / 100.0);
   double equityTarget = dailyStartBalance * (1.0 + EquityTargetPercent / 100.0);
   
   // Equity stop
   if(equity <= equityThreshold)
   {
      if(!dailyLossLimitReached)
      {
         dailyLossLimitReached = true;
         Print("*** EQUITY STOP: $", DoubleToString(equity, 2), " <= $", DoubleToString(equityThreshold, 2), " ***");
         CloseAllPositions("Equity Stop");
      }
   }
   
   // Equity target reached
   if(equity >= equityTarget)
   {
      if(!dailyTargetReached)
      {
         dailyTargetReached = true;
         Print("*** DAILY TARGET REACHED: $", DoubleToString(equity, 2), " ***");
         // Optionally close all and stop
      }
   }
}
'''

    @staticmethod
    def generate_master_kill_check() -> str:
        """Generate master kill switch check."""
        return '''
//+------------------------------------------------------------------+
//| Master Kill Switch Check                                          |
//+------------------------------------------------------------------+
bool IsKillSwitchClear()
{
   // Check volatility
   if(!IsVolatilityKillClear())
   {
      if(EnableLogging) Print("Blocked by volatility kill switch");
      return false;
   }
   
   // Check news
   if(!IsNewsKillClear())
   {
      if(EnableLogging) Print("Blocked by news kill switch");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Run All Protection Checks (Call at start of OnTick)              |
//+------------------------------------------------------------------+
void RunProtectionChecks()
{
   CheckNewDay();
   UpdateDrawdownStatus();
   CheckEquityProtection();
}
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete protection blocks module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_globals() + "\n" +
            cls.generate_init() + "\n" +
            cls.generate_drawdown_guard() + "\n" +
            cls.generate_position_limits() + "\n" +
            cls.generate_volatility_kill_switch() + "\n" +
            cls.generate_news_kill_switch() + "\n" +
            cls.generate_equity_protection() + "\n" +
            cls.generate_master_kill_check()
        )
