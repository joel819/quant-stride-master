"""
Order Management Templates
MQL5 template blocks for safe order execution.
"""


class OrderManagementTemplates:
    """
    Generates MQL5 code blocks for order management.
    
    Includes:
    - Safe order placement with retries
    - Duplicate order prevention
    - Position modification (SL/TP)
    - Partial close functionality
    - Trailing stop management
    - Breakeven management
    """
    
    @staticmethod
    def generate_safe_order_open() -> str:
        """Generate safe order opening with retries."""
        return '''
//+------------------------------------------------------------------+
//| Safe Order Opening with Retries                                   |
//+------------------------------------------------------------------+
bool OpenBuyOrder(double lots, double sl_pips, double tp_pips, string comment = "")
{
   if(!PreTradeChecks())
      return false;
   
   symbolInfo.RefreshRates();
   double ask = symbolInfo.Ask();
   double spread = symbolInfo.Spread();
   
   // Check spread
   if(UseSpreadFilter && spread > MaxSpreadPoints)
   {
      if(EnableLogging) Print("Spread too high: ", spread, " > ", MaxSpreadPoints);
      return false;
   }
   
   // Calculate SL/TP prices
   double sl_price = 0.0;
   double tp_price = 0.0;
   
   if(sl_pips > 0)
      sl_price = ask - sl_pips * pipMultiplier * _Point;
   if(tp_pips > 0)
      tp_price = ask + tp_pips * pipMultiplier * _Point;
   
   // Normalize prices
   sl_price = NormalizeDouble(sl_price, _Digits);
   tp_price = NormalizeDouble(tp_price, _Digits);
   
   // Verify stops are valid
   if(!ValidateStopLevels(ask, sl_price, tp_price, ORDER_TYPE_BUY))
   {
      if(EnableLogging) Print("Invalid stop levels for BUY");
      return false;
   }
   
   // Try to open order with retries
   for(int attempt = 0; attempt < MaxOrderRetries; attempt++)
   {
      if(trade.Buy(lots, _Symbol, ask, sl_price, tp_price, comment))
      {
         dailyTradeCount++;
         if(EnableLogging) 
            Print("BUY order opened: Lots=", lots, " SL=", sl_price, " TP=", tp_price);
         return true;
      }
      
      uint error = GetLastError();
      if(EnableLogging) Print("Buy failed. Attempt ", attempt + 1, " Error: ", error);
      
      // Don't retry on certain errors
      if(error == TRADE_RETCODE_INVALID_VOLUME || 
         error == TRADE_RETCODE_NO_MONEY ||
         error == TRADE_RETCODE_MARKET_CLOSED)
         break;
      
      Sleep(RetryDelayMs);
      symbolInfo.RefreshRates();
      ask = symbolInfo.Ask();
   }
   
   return false;
}

bool OpenSellOrder(double lots, double sl_pips, double tp_pips, string comment = "")
{
   if(!PreTradeChecks())
      return false;
   
   symbolInfo.RefreshRates();
   double bid = symbolInfo.Bid();
   double spread = symbolInfo.Spread();
   
   // Check spread
   if(UseSpreadFilter && spread > MaxSpreadPoints)
   {
      if(EnableLogging) Print("Spread too high: ", spread, " > ", MaxSpreadPoints);
      return false;
   }
   
   // Calculate SL/TP prices
   double sl_price = 0.0;
   double tp_price = 0.0;
   
   if(sl_pips > 0)
      sl_price = bid + sl_pips * pipMultiplier * _Point;
   if(tp_pips > 0)
      tp_price = bid - tp_pips * pipMultiplier * _Point;
   
   // Normalize prices
   sl_price = NormalizeDouble(sl_price, _Digits);
   tp_price = NormalizeDouble(tp_price, _Digits);
   
   // Verify stops are valid
   if(!ValidateStopLevels(bid, sl_price, tp_price, ORDER_TYPE_SELL))
   {
      if(EnableLogging) Print("Invalid stop levels for SELL");
      return false;
   }
   
   // Try to open order with retries
   for(int attempt = 0; attempt < MaxOrderRetries; attempt++)
   {
      if(trade.Sell(lots, _Symbol, bid, sl_price, tp_price, comment))
      {
         dailyTradeCount++;
         if(EnableLogging)
            Print("SELL order opened: Lots=", lots, " SL=", sl_price, " TP=", tp_price);
         return true;
      }
      
      uint error = GetLastError();
      if(EnableLogging) Print("Sell failed. Attempt ", attempt + 1, " Error: ", error);
      
      if(error == TRADE_RETCODE_INVALID_VOLUME || 
         error == TRADE_RETCODE_NO_MONEY ||
         error == TRADE_RETCODE_MARKET_CLOSED)
         break;
      
      Sleep(RetryDelayMs);
      symbolInfo.RefreshRates();
      bid = symbolInfo.Bid();
   }
   
   return false;
}
'''

    @staticmethod
    def generate_duplicate_prevention() -> str:
        """Generate duplicate order prevention code."""
        return '''
//+------------------------------------------------------------------+
//| Duplicate Order Prevention                                        |
//+------------------------------------------------------------------+
input int MinSecondsBetweenTrades = 60;                      // Min seconds between trades
datetime lastTradeTime = 0;

bool CanOpenNewTrade()
{
   // Check if enough time has passed since last trade
   if(TimeCurrent() - lastTradeTime < MinSecondsBetweenTrades)
   {
      if(EnableLogging) Print("Too soon since last trade. Wait ", 
         MinSecondsBetweenTrades - (TimeCurrent() - lastTradeTime), " seconds");
      return false;
   }
   
   // Check for existing position
   if(HasOpenPosition())
   {
      if(EnableLogging) Print("Already have an open position");
      return false;
   }
   
   // Check for pending orders
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket > 0)
      {
         if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
            OrderGetInteger(ORDER_MAGIC) == MagicNumber)
         {
            if(EnableLogging) Print("Pending order exists");
            return false;
         }
      }
   }
   
   return true;
}

bool PreTradeChecks()
{
   if(!CanOpenNewTrade())
      return false;
   
   if(!CheckDailyLimits())
      return false;
   
   if(!IsDrawdownSafe())
      return false;
   
   lastTradeTime = TimeCurrent();
   return true;
}
'''

    @staticmethod
    def generate_position_modification() -> str:
        """Generate position modification code."""
        return '''
//+------------------------------------------------------------------+
//| Position Modification (SL/TP)                                     |
//+------------------------------------------------------------------+
bool ModifyPosition(ulong ticket, double new_sl, double new_tp)
{
   if(!positionInfo.SelectByTicket(ticket))
   {
      Print("Cannot select position ", ticket);
      return false;
   }
   
   double current_sl = positionInfo.StopLoss();
   double current_tp = positionInfo.TakeProfit();
   
   // Normalize
   new_sl = NormalizeDouble(new_sl, _Digits);
   new_tp = NormalizeDouble(new_tp, _Digits);
   
   // Check if modification is needed
   if(MathAbs(new_sl - current_sl) < _Point && MathAbs(new_tp - current_tp) < _Point)
   {
      return true; // No change needed
   }
   
   // Modify position
   for(int attempt = 0; attempt < MaxOrderRetries; attempt++)
   {
      if(trade.PositionModify(ticket, new_sl, new_tp))
      {
         if(EnableLogging) Print("Position modified: SL=", new_sl, " TP=", new_tp);
         return true;
      }
      
      uint error = GetLastError();
      if(EnableLogging) Print("Modify failed. Attempt ", attempt + 1, " Error: ", error);
      
      if(error == TRADE_RETCODE_INVALID_STOPS)
         break;
      
      Sleep(RetryDelayMs);
   }
   
   return false;
}

//--- Validate stop levels against broker requirements
bool ValidateStopLevels(double price, double sl, double tp, ENUM_ORDER_TYPE order_type)
{
   long min_stop = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_stop_price = min_stop * _Point;
   
   if(order_type == ORDER_TYPE_BUY)
   {
      if(sl > 0 && price - sl < min_stop_price)
      {
         if(EnableLogging) Print("SL too close. Min: ", min_stop, " points");
         return false;
      }
      if(tp > 0 && tp - price < min_stop_price)
      {
         if(EnableLogging) Print("TP too close. Min: ", min_stop, " points");
         return false;
      }
   }
   else if(order_type == ORDER_TYPE_SELL)
   {
      if(sl > 0 && sl - price < min_stop_price)
      {
         if(EnableLogging) Print("SL too close. Min: ", min_stop, " points");
         return false;
      }
      if(tp > 0 && price - tp < min_stop_price)
      {
         if(EnableLogging) Print("TP too close. Min: ", min_stop, " points");
         return false;
      }
   }
   
   return true;
}
'''

    @staticmethod
    def generate_partial_close() -> str:
        """Generate partial position close code."""
        return '''
//+------------------------------------------------------------------+
//| Partial Position Close                                            |
//+------------------------------------------------------------------+
input bool UsePartialTP = true;                              // Enable Partial Take Profit
input double PartialClosePercent = 50.0;                     // Close % at TP1
input double PartialTPPips = 10.0;                           // TP1 distance (pips)

bool partialTPTaken = false;
double originalLots = 0.0;

bool PartialClosePosition(ulong ticket, double percent)
{
   if(!positionInfo.SelectByTicket(ticket))
      return false;
   
   double current_lots = positionInfo.Volume();
   double close_lots = current_lots * (percent / 100.0);
   
   // Normalize to lot step
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   
   close_lots = MathFloor(close_lots / lot_step) * lot_step;
   
   if(close_lots < min_lot)
   {
      if(EnableLogging) Print("Partial close lot too small: ", close_lots);
      return false;
   }
   
   // Partial close
   if(trade.PositionClosePartial(ticket, close_lots))
   {
      if(EnableLogging) Print("Partial close: ", close_lots, " lots of ", current_lots);
      return true;
   }
   
   return false;
}

void ManagePartialTP()
{
   if(!UsePartialTP || partialTPTaken)
      return;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current = positionInfo.PriceCurrent();
         double profit_pips = 0.0;
         
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
            profit_pips = (current - entry) / (pipMultiplier * _Point);
         else
            profit_pips = (entry - current) / (pipMultiplier * _Point);
         
         if(profit_pips >= PartialTPPips)
         {
            if(PartialClosePosition(positionInfo.Ticket(), PartialClosePercent))
            {
               partialTPTaken = true;
               
               // Move SL to breakeven after partial
               if(MoveToBreakevenAfterPartial)
               {
                  double be_price = entry;
                  be_price += (positionInfo.PositionType() == POSITION_TYPE_BUY ? 1 : -1) 
                              * BreakevenBuffer * pipMultiplier * _Point;
                  ModifyPosition(positionInfo.Ticket(), NormalizeDouble(be_price, _Digits), positionInfo.TakeProfit());
               }
            }
         }
      }
   }
}
'''

    @staticmethod
    def generate_trailing_stop() -> str:
        """Generate trailing stop management code."""
        return '''
//+------------------------------------------------------------------+
//| Trailing Stop Management                                          |
//+------------------------------------------------------------------+
input bool UseTrailingStop = true;                           // Enable Trailing Stop
input double TrailingDistance = 15.0;                        // Trailing distance (pips)
input double TrailingActivation = 20.0;                      // Activation profit (pips)
input double TrailingStep = 5.0;                             // Trailing step (pips)

void ManageTrailingStop()
{
   if(!UseTrailingStop)
      return;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current = positionInfo.PriceCurrent();
         double current_sl = positionInfo.StopLoss();
         double profit_pips = 0.0;
         double new_sl = 0.0;
         
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
         {
            profit_pips = (current - entry) / (pipMultiplier * _Point);
            
            if(profit_pips < TrailingActivation)
               continue;
            
            new_sl = current - TrailingDistance * pipMultiplier * _Point;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            // Only move if better than current and step threshold met
            if(new_sl > current_sl + TrailingStep * pipMultiplier * _Point)
            {
               ModifyPosition(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit());
            }
         }
         else // SELL
         {
            profit_pips = (entry - current) / (pipMultiplier * _Point);
            
            if(profit_pips < TrailingActivation)
               continue;
            
            new_sl = current + TrailingDistance * pipMultiplier * _Point;
            new_sl = NormalizeDouble(new_sl, _Digits);
            
            // Only move if better than current
            if(current_sl == 0 || new_sl < current_sl - TrailingStep * pipMultiplier * _Point)
            {
               ModifyPosition(positionInfo.Ticket(), new_sl, positionInfo.TakeProfit());
            }
         }
      }
   }
}
'''

    @staticmethod
    def generate_breakeven() -> str:
        """Generate breakeven management code."""
        return '''
//+------------------------------------------------------------------+
//| Breakeven Management                                              |
//+------------------------------------------------------------------+
input bool UseBreakeven = true;                              // Enable Breakeven
input double BreakevenPips = 10.0;                           // Activation (pips)
input double BreakevenBuffer = 2.0;                          // Buffer above entry (pips)
input bool MoveToBreakevenAfterPartial = true;               // Move to BE after partial

bool breakevenApplied = false;

void ManageBreakeven()
{
   if(!UseBreakeven || breakevenApplied)
      return;
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() != _Symbol || positionInfo.Magic() != MagicNumber)
            continue;
         
         double entry = positionInfo.PriceOpen();
         double current = positionInfo.PriceCurrent();
         double current_sl = positionInfo.StopLoss();
         double profit_pips = 0.0;
         double be_price = 0.0;
         
         if(positionInfo.PositionType() == POSITION_TYPE_BUY)
         {
            profit_pips = (current - entry) / (pipMultiplier * _Point);
            be_price = entry + BreakevenBuffer * pipMultiplier * _Point;
            
            if(profit_pips >= BreakevenPips && current_sl < be_price)
            {
               if(ModifyPosition(positionInfo.Ticket(), NormalizeDouble(be_price, _Digits), positionInfo.TakeProfit()))
               {
                  breakevenApplied = true;
                  if(EnableLogging) Print("Breakeven applied at ", be_price);
               }
            }
         }
         else // SELL
         {
            profit_pips = (entry - current) / (pipMultiplier * _Point);
            be_price = entry - BreakevenBuffer * pipMultiplier * _Point;
            
            if(profit_pips >= BreakevenPips && (current_sl == 0 || current_sl > be_price))
            {
               if(ModifyPosition(positionInfo.Ticket(), NormalizeDouble(be_price, _Digits), positionInfo.TakeProfit()))
               {
                  breakevenApplied = true;
                  if(EnableLogging) Print("Breakeven applied at ", be_price);
               }
            }
         }
      }
   }
}
'''

    @staticmethod
    def generate_inputs() -> str:
        """Generate input parameters for order management."""
        return '''
input group "=== Order Management ==="
input int MaxOrderRetries = 3;                               // Max order retries
input int RetryDelayMs = 500;                                // Retry delay (ms)
input int MaxSlippage = 3;                                   // Max slippage (points)
'''

    @classmethod
    def generate_full_module(cls) -> str:
        """Generate complete order management module."""
        return (
            cls.generate_inputs() + "\n" +
            cls.generate_safe_order_open() +
            cls.generate_duplicate_prevention() +
            cls.generate_position_modification() +
            cls.generate_partial_close() +
            cls.generate_trailing_stop() +
            cls.generate_breakeven()
        )
