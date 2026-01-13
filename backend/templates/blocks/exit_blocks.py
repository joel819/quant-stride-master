"""
Exit Blocks
Smart exit logic with dual exit system.
"""


class ExitBlocks:
    """
    Modular exit blocks for EA assembly.
    
    Dual exit system:
    - Hard exits: Fixed SL/TP
    - Soft exits: Momentum reversal, trailing stop, time-based
    """
    
    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for exit blocks."""
        return '''
//+------------------------------------------------------------------+
//|                     EXIT BLOCK PARAMETERS                        |
//+------------------------------------------------------------------+
input group "=== Hard Exit Settings ==="
input double FixedSL_Pips = 30.0;                            // Fixed Stop Loss (pips)
input double FixedTP_Pips = 60.0;                            // Fixed Take Profit (pips)
input bool UseATRBasedSL = true;                             // Use ATR-based SL
input double ATR_SL_Multiplier = 2.0;                        // ATR Multiplier for SL
input double ATR_TP_Multiplier = 3.0;                        // ATR Multiplier for TP
input double MinSL_Pips = 10.0;                              // Minimum SL (pips)
input double MaxSL_Pips = 100.0;                             // Maximum SL (pips)

input group "=== Momentum Exit ==="
input bool UseMomentumExit = true;                           // Enable Momentum Exit
input int MomentumExit_RSI_Period = 14;                      // RSI Period for exit
input double MomentumExit_RSI_BuyExit = 75.0;                // RSI level to exit buys
input double MomentumExit_RSI_SellExit = 25.0;               // RSI level to exit sells
input bool UseMACD_Exit = true;                              // Use MACD cross for exit

input group "=== ATR Trailing Stop ==="
input bool UseATRTrailing = true;                            // Enable ATR Trailing
input double ATRTrail_Multiplier = 2.5;                      // ATR Multiplier for trail
input double ATRTrail_Activation_Pips = 20.0;                // Activation profit (pips)
input double ATRTrail_Step_Pips = 5.0;                       // Min step to update (pips)

input group "=== MA Trailing Stop ==="
input bool UseMATrailing = false;                            // Enable MA Trailing
input int MATrail_Period = 21;                               // MA Period for trail
input ENUM_MA_METHOD MATrail_Method = MODE_EMA;              // MA Method
input double MATrail_Buffer_Pips = 5.0;                      // Buffer from MA (pips)

input group "=== Time-Based Exit ==="
input bool UseTimeExit = true;                               // Enable Time Exit
input int MaxTradeBars = 50;                                 // Max bars to hold trade
input int MaxTradeHours = 24;                                // Max hours to hold trade
input bool CloseBeforeWeekend = true;                        // Close before weekend
input int FridayCloseHour = 20;                              // Friday close hour (server)
'''

    @staticmethod
    def generate_globals() -> str:
        """Generate global variables for exit blocks."""
        return '''
//+------------------------------------------------------------------+
//|                      EXIT BLOCK GLOBALS                          |
//+------------------------------------------------------------------+
int handle_exit_atr;
int handle_exit_rsi;
int handle_exit_macd;
int handle_ma_trail;

datetime tradeOpenTime[];      // Track when each trade was opened
int tradeOpenBar[];            // Track which bar trade was opened
'''

    @staticmethod
    def generate_init() -> str:
        """Generate indicator initialization for exit blocks."""
        return '''
//+------------------------------------------------------------------+
//| Initialize Exit Block Indicators                                 |
//+------------------------------------------------------------------+
bool InitExitIndicators()
{
   handle_exit_atr = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   if(handle_exit_atr == INVALID_HANDLE)
   {
      Print("Failed to create exit ATR handle");
      return false;
   }
   
   if(UseMomentumExit)
   {
      handle_exit_rsi = iRSI(_Symbol, PERIOD_CURRENT, MomentumExit_RSI_Period, PRICE_CLOSE);
      if(handle_exit_rsi == INVALID_HANDLE)
      {
         Print("Failed to create exit RSI handle");
         return false;
      }
      
      handle_exit_macd = iMACD(_Symbol, PERIOD_CURRENT, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);
      if(handle_exit_macd == INVALID_HANDLE)
      {
         Print("Failed to create exit MACD handle");
         return false;
      }
   }
   
   if(UseMATrailing)
   {
      handle_ma_trail = iMA(_Symbol, PERIOD_CURRENT, MATrail_Period, 0, MATrail_Method, PRICE_CLOSE);
      if(handle_ma_trail == INVALID_HANDLE)
      {
         Print("Failed to create MA trail handle");
         return false;
      }
   }
   
   Print("Exit indicators initialized successfully");
   return true;
}
'''

    @staticmethod
    def generate_deinit() -> str:
        """Generate cleanup code for exit blocks."""
        return '''
//+------------------------------------------------------------------+
//| Release Exit Block Indicators                                    |
//+------------------------------------------------------------------+
void DeinitExitIndicators()
{
   IndicatorRelease(handle_exit_atr);
   if(UseMomentumExit)
   {
      IndicatorRelease(handle_exit_rsi);
      IndicatorRelease(handle_exit_macd);
   }
   if(UseMATrailing) IndicatorRelease(handle_ma_trail);
}
'''

    @staticmethod
    def generate_calculate_sl_tp() -> str:
        """Generate SL/TP calculation functions."""
        return '''
//+------------------------------------------------------------------+
//| Calculate Stop Loss (ATR-based or Fixed)                         |
//+------------------------------------------------------------------+
double CalculateStopLoss(ENUM_ORDER_TYPE orderType)
{
   double sl_pips = FixedSL_Pips;
   
   if(UseATRBasedSL)
   {
      double atr[];
      ArraySetAsSeries(atr, true);
      if(CopyBuffer(handle_exit_atr, 0, 0, 1, atr) >= 1)
      {
         double atr_pips = atr[0] / (pipMultiplier * _Point);
         sl_pips = atr_pips * ATR_SL_Multiplier;
         
         // Clamp to min/max
         sl_pips = MathMax(MinSL_Pips, MathMin(MaxSL_Pips, sl_pips));
      }
   }
   
   double sl_points = sl_pips * pipMultiplier * _Point;
   
   if(orderType == ORDER_TYPE_BUY)
      return NormalizeDouble(symbolInfo.Ask() - sl_points, _Digits);
   else
      return NormalizeDouble(symbolInfo.Bid() + sl_points, _Digits);
}

//+------------------------------------------------------------------+
//| Calculate Take Profit (ATR-based or Fixed)                       |
//+------------------------------------------------------------------+
double CalculateTakeProfit(ENUM_ORDER_TYPE orderType, double sl_pips)
{
   double tp_pips = FixedTP_Pips;
   
   if(UseATRBasedSL)
   {
      double atr[];
      ArraySetAsSeries(atr, true);
      if(CopyBuffer(handle_exit_atr, 0, 0, 1, atr) >= 1)
      {
         double atr_pips = atr[0] / (pipMultiplier * _Point);
         tp_pips = atr_pips * ATR_TP_Multiplier;
      }
   }
   
   // Ensure minimum R:R of 1.5
   tp_pips = MathMax(tp_pips, sl_pips * 1.5);
   
   double tp_points = tp_pips * pipMultiplier * _Point;
   
   if(orderType == ORDER_TYPE_BUY)
      return NormalizeDouble(symbolInfo.Ask() + tp_points, _Digits);
   else
      return NormalizeDouble(symbolInfo.Bid() - tp_points, _Digits);
}
'''

    @staticmethod
    def generate_momentum_exit() -> str:
        """Generate momentum-based exit logic."""
        return '''
//+------------------------------------------------------------------+
//| Momentum Exit Block                                               |
//+------------------------------------------------------------------+
bool CheckMomentumExit(ENUM_POSITION_TYPE posType)
{
   if(!UseMomentumExit) return false;
   
   double rsi[], macd_main[], macd_signal[];
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   
   if(CopyBuffer(handle_exit_rsi, 0, 0, 3, rsi) < 3) return false;
   if(UseMACD_Exit)
   {
      if(CopyBuffer(handle_exit_macd, 0, 0, 3, macd_main) < 3) return false;
      if(CopyBuffer(handle_exit_macd, 1, 0, 3, macd_signal) < 3) return false;
   }
   
   // RSI exit conditions
   if(posType == POSITION_TYPE_BUY)
   {
      // Exit buy if RSI goes overbought
      if(rsi[0] >= MomentumExit_RSI_BuyExit)
      {
         LogMessage("MOMENTUM EXIT: RSI overbought at " + DoubleToString(rsi[0], 1));
         return true;
      }
      
      // MACD bearish cross while in profit
      if(UseMACD_Exit)
      {
         if(macd_main[0] < macd_signal[0] && macd_main[1] >= macd_signal[1])
         {
            LogMessage("MOMENTUM EXIT: MACD bearish cross");
            return true;
         }
      }
   }
   else if(posType == POSITION_TYPE_SELL)
   {
      // Exit sell if RSI goes oversold
      if(rsi[0] <= MomentumExit_RSI_SellExit)
      {
         LogMessage("MOMENTUM EXIT: RSI oversold at " + DoubleToString(rsi[0], 1));
         return true;
      }
      
      // MACD bullish cross while in profit
      if(UseMACD_Exit)
      {
         if(macd_main[0] > macd_signal[0] && macd_main[1] <= macd_signal[1])
         {
            LogMessage("MOMENTUM EXIT: MACD bullish cross");
            return true;
         }
      }
   }
   
   return false;
}
'''

    @staticmethod
    def generate_atr_trailing() -> str:
        """Generate ATR-based trailing stop."""
        return '''
//+------------------------------------------------------------------+
//| ATR Trailing Stop Exit                                            |
//+------------------------------------------------------------------+
void ManageATRTrailingStop()
{
   if(!UseATRTrailing) return;
   
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(handle_exit_atr, 0, 0, 1, atr) < 1) return;
   
   double trail_distance = atr[0] * ATRTrail_Multiplier;
   double activation_points = ATRTrail_Activation_Pips * pipMultiplier * _Point;
   double step_points = ATRTrail_Step_Pips * pipMultiplier * _Point;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current = positionInfo.PriceCurrent();
         double current_sl = positionInfo.StopLoss();
         double profit_points = 0;
         double new_sl = 0;
         
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
         {
            profit_points = current - entry;
            
            // Only trail if in profit beyond activation
            if(profit_points < activation_points) continue;
            
            new_sl = current - trail_distance;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            // Only move if better and step met
            if(new_sl > current_sl + step_points && new_sl > entry)
            {
               if(trade.PositionModify(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit()))
               {
                  LogMessage("ATR TRAILING: SL moved to " + DoubleToString(new_sl, _Digits));
               }
            }
         }
         else if(positionInfo.PositionType() == POSITION_TYPE_SELL)
         {
            profit_points = entry - current;
            
            if(profit_points < activation_points) continue;
            
            new_sl = current + trail_distance;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            if(current_sl == 0 || new_sl < current_sl - step_points)
            {
               if(new_sl < entry)
               {
                  if(trade.PositionModify(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit()))
                  {
                     LogMessage("ATR TRAILING: SL moved to " + DoubleToString(new_sl, _Digits));
                  }
               }
            }
         }
      }
   }
}
'''

    @staticmethod
    def generate_ma_trailing() -> str:
        """Generate MA-based trailing stop."""
        return '''
//+------------------------------------------------------------------+
//| MA Trailing Stop Exit                                             |
//+------------------------------------------------------------------+
void ManageMATrailingStop()
{
   if(!UseMATrailing) return;
   
   double ma[];
   ArraySetAsSeries(ma, true);
   if(CopyBuffer(handle_ma_trail, 0, 0, 2, ma) < 2) return;
   
   double buffer_points = MATrail_Buffer_Pips * pipMultiplier * _Point;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current_sl = positionInfo.StopLoss();
         double new_sl = 0;
         
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
         {
            // Trail SL below MA
            new_sl = ma[0] - buffer_points;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            // Only move if better and above entry
            if(new_sl > current_sl && new_sl > entry)
            {
               if(trade.PositionModify(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit()))
               {
                  LogMessage("MA TRAILING: SL moved to " + DoubleToString(new_sl, _Digits) + " (MA=" + DoubleToString(ma[0], _Digits) + ")");
               }
            }
         }
         else if(positionInfo.PositionType() == POSITION_TYPE_SELL)
         {
            // Trail SL above MA
            new_sl = ma[0] + buffer_points;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            if(current_sl == 0 || (new_sl < current_sl && new_sl < entry))
            {
               if(trade.PositionModify(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit()))
               {
                  LogMessage("MA TRAILING: SL moved to " + DoubleToString(new_sl, _Digits) + " (MA=" + DoubleToString(ma[0], _Digits) + ")");
               }
            }
         }
      }
   }
}
'''

    @staticmethod
    def generate_time_exit() -> str:
        """Generate time-based exit logic."""
        return '''
//+------------------------------------------------------------------+
//| Time-Based Exit Block                                             |
//+------------------------------------------------------------------+
bool CheckTimeExit(ulong ticket, datetime openTime, int openBar)
{
   if(!UseTimeExit) return false;
   
   datetime currentTime = TimeCurrent();
   int currentBar = Bars(_Symbol, PERIOD_CURRENT);
   
   // Check max bars
   int barsHeld = currentBar - openBar;
   if(barsHeld >= MaxTradeBars)
   {
      LogMessage("TIME EXIT: Trade held for " + IntegerToString(barsHeld) + " bars");
      return true;
   }
   
   // Check max hours
   int hoursHeld = (int)((currentTime - openTime) / 3600);
   if(hoursHeld >= MaxTradeHours)
   {
      LogMessage("TIME EXIT: Trade held for " + IntegerToString(hoursHeld) + " hours");
      return true;
   }
   
   // Check weekend close
   if(CloseBeforeWeekend)
   {
      MqlDateTime dt;
      TimeToStruct(currentTime, dt);
      
      if(dt.day_of_week == FRIDAY && dt.hour >= FridayCloseHour)
      {
         LogMessage("TIME EXIT: Closing before weekend");
         return true;
      }
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Track Trade Open Time                                             |
//+------------------------------------------------------------------+
void RecordTradeOpen(ulong ticket)
{
   int size = ArraySize(tradeOpenTime);
   ArrayResize(tradeOpenTime, size + 1);
   ArrayResize(tradeOpenBar, size + 1);
   tradeOpenTime[size] = TimeCurrent();
   tradeOpenBar[size] = Bars(_Symbol, PERIOD_CURRENT);
}
'''

    @staticmethod
    def generate_manage_exits() -> str:
        """Generate master exit management function."""
        return '''
//+------------------------------------------------------------------+
//| Manage All Exits - Called every tick                              |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   // Apply trailing stops
   ManageATRTrailingStop();
   ManageMATrailingStop();
   
   // Check soft exit conditions
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         ulong ticket = positionInfo.Ticket();
         ENUM_POSITION_TYPE posType = positionInfo.PositionType();
         double profit = positionInfo.Profit();
         
         // Only use soft exits when in profit (protect gains)
         if(profit > 0)
         {
            // Momentum exit
            if(CheckMomentumExit(posType))
            {
               trade.PositionClose(ticket);
               LogMessage("Position " + IntegerToString(ticket) + " closed by MOMENTUM EXIT");
               continue;
            }
         }
         
         // Time-based exit (regardless of profit)
         // Note: Need to track open time per position
         datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);
         int openBar = 0; // Would need to track this
         
         if(CheckTimeExit(ticket, openTime, openBar))
         {
            trade.PositionClose(ticket);
            LogMessage("Position " + IntegerToString(ticket) + " closed by TIME EXIT");
            continue;
         }
      }
   }
}
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete exit blocks module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_globals() + "\n" +
            cls.generate_init() + "\n" +
            cls.generate_deinit() + "\n" +
            cls.generate_calculate_sl_tp() + "\n" +
            cls.generate_momentum_exit() + "\n" +
            cls.generate_atr_trailing() + "\n" +
            cls.generate_ma_trailing() + "\n" +
            cls.generate_time_exit() + "\n" +
            cls.generate_manage_exits()
        )
