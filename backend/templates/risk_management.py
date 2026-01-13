"""
Risk Management Templates
MQL5 template blocks for position sizing and risk control.
"""


class RiskManagementTemplates:
    """
    Generates MQL5 code blocks for risk management.
    
    Includes:
    - Position sizing (fixed, percent, Kelly)
    - Max drawdown protection
    - Daily loss limits
    - Equity-based stops
    - Consecutive loss handling
    """
    
    @staticmethod
    def generate_lot_size_calculator() -> str:
        """Generate lot size calculation function."""
        return '''
//+------------------------------------------------------------------+
//| Calculate lot size based on risk management rules                |
//+------------------------------------------------------------------+
double CalculateLotSize(double slPips)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = balance * (RiskPercent / 100.0);
   
   // Apply dynamic risk reduction after losses
   if(UseDynamicRiskReduction && consecutiveLosses > 0)
   {
      double reduction = MathPow(RiskReductionFactor, consecutiveLosses);
      riskAmount *= reduction;
      if(EnableLogging) Print("Risk reduced to: $", DoubleToString(riskAmount, 2), " after ", consecutiveLosses, " losses");
   }
   
   // Get tick and lot info
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   
   // Calculate point value
   double pointValue = (tickValue / tickSize) * _Point;
   
   // Calculate lot size
   double lots = 0.0;
   if(pointValue > 0 && slPips > 0)
   {
      double slPoints = slPips * pipMultiplier;
      lots = riskAmount / (slPoints * pointValue);
   }
   
   // Apply money management type
   switch(MoneyManagement)
   {
      case MM_FIXED:
         lots = MathMin(lots, FixedLotSize);
         break;
         
      case MM_MARTINGALE:
         if(consecutiveLosses > 0)
         {
            double multiplier = MathPow(MartingaleMultiplier, MathMin(consecutiveLosses, MaxMartingaleTrades));
            lots *= multiplier;
         }
         break;
         
      case MM_ANTI_MARTINGALE:
         if(consecutiveWins > 0)
         {
            double multiplier = MathPow(MartingaleMultiplier, MathMin(consecutiveWins, MaxMartingaleTrades));
            lots *= multiplier;
         }
         break;
         
      case MM_RECOVERY:
         if(isInRecoveryMode)
         {
            lots *= (1.0 + RecoveryRiskStep * recoveryWinStreak);
         }
         break;
   }
   
   // Normalize and clamp lot size
   lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));
   
   // Final safety check: don't risk more than max risk amount
   double maxRiskLots = (equity * MaxRiskPercent / 100.0) / (slPips * pipMultiplier * pointValue);
   lots = MathMin(lots, maxRiskLots);
   
   lastLotSize = lots;
   return lots;
}
'''

    @staticmethod
    def generate_drawdown_protection() -> str:
        """Generate drawdown protection code."""
        return '''
//+------------------------------------------------------------------+
//| Drawdown Protection Management                                    |
//+------------------------------------------------------------------+
void UpdateDrawdownProtection()
{
   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   // Update peak balance
   if(currentBalance > peakBalance)
   {
      peakBalance = currentBalance;
      
      // Check if we've recovered from recovery mode
      if(isInRecoveryMode && currentBalance >= recoveryTargetBalance)
      {
         isInRecoveryMode = false;
         recoveryStatus = "RECOVERED";
         if(ResetRiskOnRecovery) dynamicRiskMultiplier = 1.0;
         Print("RECOVERY COMPLETE: Balance restored to $", DoubleToString(currentBalance, 2));
      }
   }
   
   // Calculate current drawdown
   currentDrawdownPercent = ((peakBalance - currentBalance) / peakBalance) * 100.0;
   
   // Check if max drawdown exceeded
   if(currentDrawdownPercent >= MaxTotalDrawdownPercent)
   {
      if(!drawdownHaltActive)
      {
         drawdownHaltActive = true;
         Print("*** CIRCUIT BREAKER: Max drawdown of ", DoubleToString(MaxTotalDrawdownPercent, 1), "% exceeded ***");
         Print("Current drawdown: ", DoubleToString(currentDrawdownPercent, 2), "%");
         
         // Enter recovery mode
         if(UseRecoveryMode)
         {
            isInRecoveryMode = true;
            recoveryStartBalance = currentBalance;
            recoveryTargetBalance = peakBalance * (RecoveryThresholdPercent / 100.0);
            recoveryStatus = "RECOVERY_MODE";
            Print("Entering RECOVERY MODE. Target: $", DoubleToString(recoveryTargetBalance, 2));
         }
      }
   }
   
   // Check consecutive losses
   if(consecutiveLosses >= MaxConsecutiveLosses)
   {
      if(coolingOffEndTime == 0)
      {
         coolingOffEndTime = TimeCurrent() + CoolingOffMinutes * 60;
         Print("COOLING OFF initiated after ", consecutiveLosses, " consecutive losses");
         Print("Trading will resume at: ", TimeToString(coolingOffEndTime));
      }
   }
}

//--- Check if trading is allowed based on drawdown rules
bool IsDrawdownSafe()
{
   if(!UseDrawdownProtection)
      return true;
   
   // Circuit breaker active
   if(drawdownHaltActive)
   {
      if(EnableLogging) Print("Trading blocked: Circuit breaker active");
      return false;
   }
   
   // Cooling off period
   if(coolingOffEndTime > 0 && TimeCurrent() < coolingOffEndTime)
   {
      if(EnableLogging) Print("Trading blocked: Cooling off period until ", TimeToString(coolingOffEndTime));
      return false;
   }
   
   // Equity stop check
   double equityDrop = ((startingBalance - AccountInfoDouble(ACCOUNT_EQUITY)) / startingBalance) * 100.0;
   if(equityDrop >= EquityStopPercent)
   {
      if(EnableLogging) Print("Trading blocked: Equity stop triggered at ", DoubleToString(equityDrop, 1), "%");
      return false;
   }
   
   return true;
}
'''

    @staticmethod
    def generate_daily_limits() -> str:
        """Generate daily loss/profit limit code."""
        return '''
//+------------------------------------------------------------------+
//| Daily Limits Management                                           |
//+------------------------------------------------------------------+
bool CheckDailyLimits()
{
   // Check daily loss limit
   if(dailyPnL <= -MaxDailyLoss)
   {
      if(!dailyLimitReached)
      {
         dailyLimitReached = true;
         Print("DAILY LOSS LIMIT reached: $", DoubleToString(dailyPnL, 2));
      }
      return false;
   }
   
   // Check daily profit target
   if(dailyPnL >= DailyTarget)
   {
      if(!dailyTargetReached)
      {
         dailyTargetReached = true;
         Print("DAILY TARGET reached: $", DoubleToString(dailyPnL, 2));
      }
      return false;
   }
   
   // Check trade count
   if(dailyTradeCount >= MaxDailyTrades)
   {
      if(EnableLogging) Print("Max daily trades reached: ", dailyTradeCount);
      return false;
   }
   
   return true;
}

//--- Update daily PnL on trade close
void UpdateDailyStats(double profit)
{
   dailyPnL += profit;
   dailyTradeCount++;
   
   // Update win/loss streaks
   if(profit > 0)
   {
      consecutiveWins++;
      consecutiveLosses = 0;
      if(isInRecoveryMode) recoveryWinStreak++;
   }
   else if(profit < 0)
   {
      consecutiveLosses++;
      consecutiveWins = 0;
      todayLossStreak++;
      recoveryWinStreak = 0;
      
      // Start cooling off if needed
      if(consecutiveLosses >= MaxConsecutiveLosses && coolingOffEndTime == 0)
      {
         coolingOffEndTime = TimeCurrent() + CoolingOffMinutes * 60;
      }
   }
   
   if(EnableLogging)
   {
      Print("Trade closed. Profit: $", DoubleToString(profit, 2), 
            " | Daily PnL: $", DoubleToString(dailyPnL, 2),
            " | Trades: ", dailyTradeCount);
   }
}
'''

    @staticmethod
    def generate_equity_stop() -> str:
        """Generate equity-based stop out code."""
        return '''
//+------------------------------------------------------------------+
//| Equity Stop - Close all if equity drops below threshold          |
//+------------------------------------------------------------------+
void CheckEquityStop()
{
   if(!UseEquityStop)
      return;
   
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double equityThreshold = startingBalance * (1.0 - EquityStopPercent / 100.0);
   
   if(equity <= equityThreshold)
   {
      Print("*** EQUITY STOP TRIGGERED ***");
      Print("Equity: $", DoubleToString(equity, 2), " <= Threshold: $", DoubleToString(equityThreshold, 2));
      
      // Close all positions
      CloseAllPositions("Equity Stop");
      
      // Halt trading for the day
      dailyLimitReached = true;
   }
}

//--- Close all open positions
void CloseAllPositions(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == _Symbol && positionInfo.Magic() == MagicNumber)
         {
            trade.PositionClose(positionInfo.Ticket());
            Print("Closed position #", positionInfo.Ticket(), " | Reason: ", reason);
         }
      }
   }
}
'''

    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for risk management."""
        return '''
input group "=== Risk Management ==="
input double RiskPercent = 1.0;                              // Risk per trade (%)
input double MaxRiskPercent = 5.0;                           // Max risk per trade (%)
input ENUM_MM_TYPE MoneyManagement = MM_PERCENT;             // Money Management Type
input double FixedLotSize = 0.01;                            // Fixed lot size (if MM_FIXED)

input group "=== Martingale Settings ==="
input double MartingaleMultiplier = 2.0;                     // Martingale multiplier
input int MaxMartingaleTrades = 3;                           // Max martingale levels

input group "=== Daily Limits ==="
input double MaxDailyLoss = 100.0;                           // Max daily loss ($)
input double DailyTarget = 200.0;                            // Daily profit target ($)
input int MaxDailyTrades = 10;                               // Max trades per day

input group "=== Drawdown Protection ==="
input bool UseDrawdownProtection = true;                     // Enable Drawdown Protection
input double MaxTotalDrawdownPercent = 20.0;                 // Max total drawdown (%)
input double EquityStopPercent = 15.0;                       // Equity stop level (%)
input int MaxConsecutiveLosses = 4;                          // Max consecutive losses
input int CoolingOffMinutes = 60;                            // Cooling off period (min)
input bool UseDynamicRiskReduction = true;                   // Reduce risk after losses
input double RiskReductionFactor = 0.5;                      // Risk reduction per loss

input group "=== Recovery Mode ==="
input bool UseRecoveryMode = true;                           // Enable recovery mode
input double RecoveryThresholdPercent = 80.0;                // Recovery target (% of peak)
input bool ResetRiskOnRecovery = true;                       // Reset risk on recovery
input double RecoveryRiskStep = 0.25;                        // Risk increase per win
'''

    @staticmethod
    def generate_globals() -> str:
        """Generate global variables for risk management."""
        return '''
// Risk management tracking
double startingBalance = 0.0;
double peakBalance = 0.0;
double currentDrawdownPercent = 0.0;
bool drawdownHaltActive = false;
datetime coolingOffEndTime = 0;
int todayLossStreak = 0;
double dynamicRiskMultiplier = 1.0;

// Recovery mode
bool isInRecoveryMode = false;
double recoveryStartBalance = 0.0;
double recoveryTargetBalance = 0.0;
int recoveryWinStreak = 0;
string recoveryStatus = "NORMAL";

// Trade tracking
int consecutiveLosses = 0;
int consecutiveWins = 0;
double lastLotSize = 0.0;
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete risk management module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_globals() + "\n" +
            cls.generate_lot_size_calculator() +
            cls.generate_drawdown_protection() +
            cls.generate_daily_limits() +
            cls.generate_equity_stop()
        )
