import { StrategyConfig } from "@/types/strategy";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Download, Code2 } from "lucide-react";
import { toast } from "sonner";

interface Props {
  config: StrategyConfig;
}

export const CodeGeneratorStep = ({ config }: Props) => {
  const getTimeframePeriod = () => {
    switch (config.timeframe) {
      case "1m": return "PERIOD_M1";
      case "5m": return "PERIOD_M5";
      case "15m": return "PERIOD_M15";
      default: return "PERIOD_M1";
    }
  };

  const getIndicatorHandleName = (type: string, idx: number) => {
    const typeMap: Record<string, string> = {
      "EMA": "ma",
      "SMA": "ma",
      "RSI": "rsi",
      "MACD": "macd",
      "ATR": "atr",
      "BB": "bb",
      "Stochastic": "stoch"
    };
    return `handle_${typeMap[type] || type.toLowerCase()}_${idx}`;
  };

  const generateIndicatorHandles = () => {
    return config.indicators.map((ind, idx) => {
      if (ind.type === "VWAP") return "// VWAP calculated manually";
      return `int ${getIndicatorHandleName(ind.type, idx)};`;
    }).filter(Boolean).join("\n");
  };

  const generateIndicatorInit = () => {
    return config.indicators.map((ind, idx) => {
      const handleName = getIndicatorHandleName(ind.type, idx);
      switch (ind.type) {
        case "EMA":
          return `   ${handleName} = iMA(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, 0, MODE_EMA, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "SMA":
          return `   ${handleName} = iMA(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, 0, MODE_SMA, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "RSI":
          return `   ${handleName} = iRSI(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "MACD":
          return `   ${handleName} = iMACD(_Symbol, ${getTimeframePeriod()}, ${ind.params.fast || 12}, ${ind.params.slow || 26}, ${ind.params.signal || 9}, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "ATR":
          return `   ${handleName} = iATR(_Symbol, ${getTimeframePeriod()}, ${ind.params.period || 14});
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "BB":
          return `   ${handleName} = iBands(_Symbol, ${getTimeframePeriod()}, ${ind.params.period || 20}, 0, ${ind.params.deviation || 2}, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "Stochastic":
          return `   ${handleName} = iStochastic(_Symbol, ${getTimeframePeriod()}, ${ind.params.kPeriod || 5}, ${ind.params.dPeriod || 3}, ${ind.params.slowing || 3}, MODE_SMA, STO_LOWHIGH);
   if(${handleName} == INVALID_HANDLE) return(INIT_FAILED);`;
        default:
          return "";
      }
    }).filter(Boolean).join("\n");
  };

  const generateSessionCheck = () => {
    if (config.sessions.length === 0) return "   return true; // No session filter";
    
    const sessionChecks = config.sessions.map((s) => {
      switch (s) {
        case "london":
          return "   if(hour >= 8 && hour < 16) return true; // London session";
        case "newyork":
          return "   if(hour >= 13 && hour < 21) return true; // New York session";
        case "overlap":
          return "   if(hour >= 13 && hour < 16) return true; // London-NY overlap";
        case "asian":
          return "   if(hour >= 0 && hour < 8) return true; // Asian session";
        default:
          return "";
      }
    }).filter(Boolean).join("\n");
    
    return `${sessionChecks}
   
   Print("Session filter: Current hour ", hour, " does not match configured sessions");
   return false;`;
  };

  const generateEntryLogic = () => {
    if (config.entries.length === 0) {
      return `   // No entry conditions configured
   return false;`;
    }

    // Generate actual indicator value arrays
    const indicatorArrays: string[] = [];
    const indicatorCopies: string[] = [];
    
    config.indicators.forEach((ind, idx) => {
      const handleName = getIndicatorHandleName(ind.type, idx);
      
      switch (ind.type) {
        case "EMA":
        case "SMA":
          indicatorArrays.push(`   double ${ind.id}_val[];`);
          indicatorArrays.push(`   ArraySetAsSeries(${ind.id}_val, true);`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 0, 0, 3, ${ind.id}_val) < 3) return false;`);
          break;
        case "RSI":
          indicatorArrays.push(`   double rsi_val[];`);
          indicatorArrays.push(`   ArraySetAsSeries(rsi_val, true);`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 0, 0, 3, rsi_val) < 3) return false;`);
          break;
        case "BB":
          indicatorArrays.push(`   double bb_upper[], bb_middle[], bb_lower[];`);
          indicatorArrays.push(`   ArraySetAsSeries(bb_upper, true);`);
          indicatorArrays.push(`   ArraySetAsSeries(bb_middle, true);`);
          indicatorArrays.push(`   ArraySetAsSeries(bb_lower, true);`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 0, 0, 3, bb_upper) < 3) return false;  // Upper band`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 1, 0, 3, bb_middle) < 3) return false; // Middle band`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 2, 0, 3, bb_lower) < 3) return false;  // Lower band`);
          break;
        case "MACD":
          indicatorArrays.push(`   double macd_main[], macd_signal[];`);
          indicatorArrays.push(`   ArraySetAsSeries(macd_main, true);`);
          indicatorArrays.push(`   ArraySetAsSeries(macd_signal, true);`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 0, 0, 3, macd_main) < 3) return false;`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 1, 0, 3, macd_signal) < 3) return false;`);
          break;
        case "ATR":
          indicatorArrays.push(`   double atr_val[];`);
          indicatorArrays.push(`   ArraySetAsSeries(atr_val, true);`);
          indicatorCopies.push(`   if(CopyBuffer(${handleName}, 0, 0, 3, atr_val) < 3) return false;`);
          break;
      }
    });

    // Get current price data
    const priceData = `   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, ${getTimeframePeriod()}, 0, 3, close) < 3) return false;`;

    // Generate actual entry conditions based on strategy type
    let entryConditions = "";
    
    // Check if this is a BB + EMA strategy (like Volatility Breakout)
    const hasBB = config.indicators.some(ind => ind.type === "BB");
    const hasEMA = config.indicators.some(ind => ind.type === "EMA");
    const hasRSI = config.indicators.some(ind => ind.type === "RSI");
    
    if (hasBB && hasEMA) {
      // Volatility breakout or BB squeeze strategy
      const emaInd = config.indicators.find(ind => ind.type === "EMA");
      entryConditions = `   
   // Volatility Breakout Strategy
   Print("Checking BB+EMA: Close=", close[0], " EMA=", ${emaInd?.id}_val[0], " BB_U=", bb_upper[0], " BB_L=", bb_lower[0]);
   
   // LONG Signal 1: Price breaks above lower BB with bullish EMA trend
   if(close[0] > ${emaInd?.id}_val[0] && close[0] > bb_lower[0] && close[1] <= bb_lower[1])
   {
      Print("*** LONG SIGNAL: Breakout above lower BB with EMA support ***");
      lastSignal = 1;
      return true;
   }
   
   // LONG Signal 2: Price bounces from lower BB zone in uptrend
   if(close[1] <= bb_lower[1] && close[0] > bb_lower[0] && close[0] > ${emaInd?.id}_val[0])
   {
      Print("*** LONG SIGNAL: Bounce from lower BB zone (uptrend) ***");
      lastSignal = 1;
      return true;
   }
   
   // SHORT Signal 1: Price breaks below upper BB with bearish EMA trend
   if(close[0] < ${emaInd?.id}_val[0] && close[0] < bb_upper[0] && close[1] >= bb_upper[1])
   {
      Print("*** SHORT SIGNAL: Breakout below upper BB with EMA resistance ***");
      lastSignal = -1;
      return true;
   }
   
   // SHORT Signal 2: Price rejects from upper BB zone in downtrend
   if(close[1] >= bb_upper[1] && close[0] < bb_upper[0] && close[0] < ${emaInd?.id}_val[0])
   {
      Print("*** SHORT SIGNAL: Rejection from upper BB zone (downtrend) ***");
      lastSignal = -1;
      return true;
   }`;
    } else if (hasEMA && hasRSI) {
      // EMA + RSI scalping or mean reversion
      const emaInd = config.indicators.find(ind => ind.type === "EMA");
      entryConditions = `   
   // EMA + RSI Strategy
   Print("Checking EMA+RSI: Close=", close[0], " EMA=", ${emaInd?.id}_val[0], " RSI=", rsi_val[0]);
   
   // Long: Price above EMA with RSI momentum
   if(close[0] > ${emaInd?.id}_val[0] && rsi_val[0] > 50 && rsi_val[0] < 70 && close[1] < ${emaInd?.id}_val[1])
   {
      Print("*** LONG SIGNAL: EMA pullback with bullish RSI ***");
      lastSignal = 1;
      return true;
   }
   
   // Short: Price below EMA with RSI momentum
   if(close[0] < ${emaInd?.id}_val[0] && rsi_val[0] < 50 && rsi_val[0] > 30 && close[1] > ${emaInd?.id}_val[1])
   {
      Print("*** SHORT SIGNAL: EMA pullback with bearish RSI ***");
      lastSignal = -1;
      return true;
   }`;
    } else if (config.indicators.some(ind => ind.type === "EMA" && ind.id.includes("fast"))) {
      // EMA crossover strategy
      entryConditions = `   
   // EMA Crossover Strategy
   Print("Checking EMA Cross: Fast=", ema_fast_val[0], " Slow=", ema_slow_val[0]);
   
   // Long: Fast EMA crosses above Slow EMA
   if(ema_fast_val[0] > ema_slow_val[0] && ema_fast_val[1] <= ema_slow_val[1])
   {
      Print("*** LONG SIGNAL: Fast EMA crossed above Slow EMA ***");
      lastSignal = 1;
      return true;
   }
   
   // Short: Fast EMA crosses below Slow EMA
   if(ema_fast_val[0] < ema_slow_val[0] && ema_fast_val[1] >= ema_slow_val[1])
   {
      Print("*** SHORT SIGNAL: Fast EMA crossed below Slow EMA ***");
      lastSignal = -1;
      return true;
   }`;
    } else {
      // Generic fallback
      entryConditions = `   
   // Entry conditions: ${config.entries.map(e => e.description).join(", ")}
   Print("WARNING: No specific entry logic implemented for this indicator combination");
   return false;`;
    }

    return `${indicatorArrays.join("\n")}
   
${priceData}
   
${indicatorCopies.join("\n")}
${entryConditions}
   
   return false;`;
  };

  const generateStopLossCalculation = () => {
    switch (config.stopLoss.type) {
      case "atr":
        const atrHandle = config.indicators.findIndex(ind => ind.type === "ATR");
        const handleName = atrHandle >= 0 ? getIndicatorHandleName("ATR", atrHandle) : "handle_atr_0";
        return `   // ATR-based stop loss
   double atrValue[];
   ArraySetAsSeries(atrValue, true);
   if(CopyBuffer(${handleName}, 0, 0, 1, atrValue) > 0)
   {
      stopLossPips = atrValue[0] * ${config.stopLoss.atrMultiplier || 2} / _Point;
   }
   else
   {
      stopLossPips = StopLossPips; // Fallback to default
   }`;
      case "structure":
        return `   // Market structure stop loss
   // Implement swing high/low logic for structure-based SL
   stopLossPips = StopLossPips;`;
      default:
        return `   stopLossPips = StopLossPips;`;
    }
  };

  const generateTakeProfitCalculation = () => {
    switch (config.takeProfit.type) {
      case "rr":
        return `   takeProfitPips = stopLossPips * TakeProfitRatio;`;
      case "trailing":
        return `   takeProfitPips = stopLossPips * 3.0; // Initial TP, will trail`;
      default:
        return `   takeProfitPips = ${config.takeProfit.pips || 20};`;
    }
  };

  const generateMQL5 = () => {
    return `//+------------------------------------------------------------------+
//|                                    ${config.instruments.join("_")}_Strategy.mq5 |
//|                                    Generated by Strategy Builder |
//+------------------------------------------------------------------+
#property copyright "Quantum Strategy Builder"
#property version   "1.00"
#property description "Mechanical trading strategy - ${config.instruments.join(", ")}"

//--- Input Parameters
input group "=== Risk Management ==="
input double RiskPercent = ${config.positionSizePercent || 1.0};      // Risk per trade (%)
input double StopLossPips = ${config.stopLoss.pips || 10.0};          // Stop Loss (pips)
input double TakeProfitRatio = ${config.takeProfit.ratio || 2.0};     // Take Profit Ratio

input group "=== Trailing Stop ==="
input bool UseTrailingStop = true;                                     // Enable Trailing Stop
input double TrailingStopDistance = 10.0;                              // Trailing Stop Distance (pips)
input double TrailingStopActivation = 15.0;                            // Activate after profit (pips)

input group "=== Daily Limits ==="
input int MaxDailyLoss = ${config.maxDailyLoss || 100};                // Max Daily Loss ($)
input double DailyTarget = ${config.dailyTarget || 200.0};             // Daily Target ($)

input group "=== General Settings ==="
input int MagicNumber = 12345;                                         // Magic Number

//--- Indicator Handles
${generateIndicatorHandles()}

//--- Global Variables
double dailyPnL = 0.0;
datetime lastTradeDate;
bool dailyTargetReached = false;
int lastSignal = 0; // 1 = buy, -1 = sell, 0 = none
int dailyTradeCount = 0;
double currentTrailingStopDistance = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("Initializing ${config.instruments.join("/")} Strategy EA...");
   
   // Initialize date tracking
   lastTradeDate = TimeCurrent();
   
   // Initialize indicators
${generateIndicatorInit()}
   
   Print("All indicators initialized successfully");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Release indicator handles
${config.indicators.map((ind, idx) => {
  if (ind.type === "VWAP") return "";
  return `   IndicatorRelease(${getIndicatorHandleName(ind.type, idx)});`;
}).filter(Boolean).join("\n")}
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, ${getTimeframePeriod()}, 0);
   
   // Only check for new trades on new bar
   if(currentBarTime == lastBarTime)
      return;
   lastBarTime = currentBarTime;
   
   // Reset daily statistics at start of new day
   MqlDateTime currentTime, lastTradeTime;
   TimeToStruct(TimeCurrent(), currentTime);
   TimeToStruct(lastTradeDate, lastTradeTime);
   
   if(currentTime.day != lastTradeTime.day || currentTime.mon != lastTradeTime.mon || currentTime.year != lastTradeTime.year)
   {
      dailyPnL = 0.0;
      dailyTradeCount = 0;
      dailyTargetReached = false;
      lastTradeDate = TimeCurrent();
      Print("========== NEW TRADING DAY STARTED ==========");
   }
   
   // Update daily PnL and trade count
   UpdateDailyPnL();
   
   // Draw dashboard
   DrawDashboard();
   
   // Check daily target reached
   if(dailyTargetReached)
   {
      Print("Daily target of $", DailyTarget, " reached. No more trades today.");
      return;
   }
   
   // Check max daily loss
   if(dailyPnL <= -MaxDailyLoss)
   {
      Print("Max daily loss of $", MaxDailyLoss, " reached. Stopping trading for today.");
      return;
   }
   
   // Session filter
   if(!IsValidSession())
      return;
   
    // Check if we already have an open position
    if(PositionSelect(_Symbol))
    {
       // Manage trailing stop for open position
       if(UseTrailingStop)
          ManageTrailingStop();
       return;
    }
   
   Print("No position open. Checking entry conditions...");
   
   // Entry logic
   if(CheckEntryConditions())
   {
      Print("===== ENTRY CONDITIONS MET! Opening trade... =====");
      OpenTrade();
   }
   else
   {
      Print("No entry signal on this bar.");
   }
}

//+------------------------------------------------------------------+
//| Update daily PnL and trade count                                 |
//+------------------------------------------------------------------+
void UpdateDailyPnL()
{
   double todayProfit = 0.0;
   int todayTrades = 0;
   datetime todayStart = iTime(_Symbol, PERIOD_D1, 0);
   
   HistorySelect(todayStart, TimeCurrent());
   int totalDeals = HistoryDealsTotal();
   
   for(int i = 0; i < totalDeals; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == MagicNumber)
      {
         if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN)
         {
            todayTrades++;
         }
         todayProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      }
   }
   
   dailyPnL = todayProfit;
   dailyTradeCount = todayTrades;
   
   // Check if daily target reached
   if(dailyPnL >= DailyTarget)
   {
      dailyTargetReached = true;
   }
}

//+------------------------------------------------------------------+
//| Check if current time is in valid trading session               |
//+------------------------------------------------------------------+
bool IsValidSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   
${generateSessionCheck()}
   
   return false;
}

//+------------------------------------------------------------------+
//| Check entry conditions                                           |
//+------------------------------------------------------------------+
bool CheckEntryConditions()
{
${generateEntryLogic()}
}

//+------------------------------------------------------------------+
//| Open trade with risk management                                  |
//+------------------------------------------------------------------+
void OpenTrade()
{
   // Calculate lot size
   double lotSize = CalculateLotSize();
   
   // Declare stop loss and take profit pips
   double stopLossPips;
   double takeProfitPips;
   
   // Calculate stop loss
${generateStopLossCalculation()}
   
   // Calculate take profit
${generateTakeProfitCalculation()}
   
    // Determine trade direction based on lastSignal
    ENUM_ORDER_TYPE orderType = (lastSignal == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   // Get current price
   double price = (orderType == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Calculate SL and TP prices
   double slPrice = (orderType == ORDER_TYPE_BUY) ? price - (stopLossPips * _Point) : price + (stopLossPips * _Point);
   double tpPrice = (orderType == ORDER_TYPE_BUY) ? price + (takeProfitPips * _Point) : price - (takeProfitPips * _Point);
   
   // Prepare trade request
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lotSize;
   request.type = orderType;
   request.price = price;
   request.sl = slPrice;
   request.tp = tpPrice;
   request.deviation = 10;
   request.magic = MagicNumber;
   request.comment = "Quantum Strategy";
   
   // Send order
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         Print("Order placed successfully. Ticket: ", result.order);
      }
      else
      {
         Print("Order failed. Error code: ", result.retcode);
      }
   }
   else
   {
      Print("OrderSend failed. Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Calculate position size based on risk                           |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (RiskPercent / 100.0);
   double stopLossPips = StopLossPips;
   
   // Get tick value for current symbol
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   
   // Calculate lot size
   double lotSize = riskAmount / (stopLossPips * point / tickSize * tickValue);
   
   // Normalize to allowed lot sizes
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathMax(minLot, MathMin(maxLot, lotSize));
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   
    return NormalizeDouble(lotSize, 2);
}

//+------------------------------------------------------------------+
//| Manage trailing stop for open positions                         |
//+------------------------------------------------------------------+
void ManageTrailingStop()
{
   if(!PositionSelect(_Symbol))
      return;
   
   // Get position details
   double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL = PositionGetDouble(POSITION_SL);
   long positionType = PositionGetInteger(POSITION_TYPE);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   
   // Get current price
   double currentPrice = (positionType == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   // Calculate profit in pips
   double profitPips = 0.0;
   if(positionType == POSITION_TYPE_BUY)
      profitPips = (currentPrice - positionOpenPrice) / point;
   else
      profitPips = (positionOpenPrice - currentPrice) / point;
   
   // Check if profit exceeds activation level
   if(profitPips < TrailingStopActivation)
      return; // Not enough profit to activate trailing stop
   
   // Calculate new stop loss
   double newSL = 0.0;
   bool shouldModify = false;
   
   if(positionType == POSITION_TYPE_BUY)
   {
      // For buy positions, trail below current price
      newSL = currentPrice - (TrailingStopDistance * point);
      
      // Only move SL up, never down
      if(currentSL == 0.0 || newSL > currentSL)
         shouldModify = true;
   }
   else // POSITION_TYPE_SELL
   {
      // For sell positions, trail above current price
      newSL = currentPrice + (TrailingStopDistance * point);
      
      // Only move SL down, never up
      if(currentSL == 0.0 || newSL < currentSL)
         shouldModify = true;
   }
   
   // Modify position if needed
   if(shouldModify)
   {
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_SLTP;
      request.symbol = _Symbol;
      request.sl = NormalizeDouble(newSL, _Digits);
      request.tp = PositionGetDouble(POSITION_TP); // Keep existing TP
      
      if(OrderSend(request, result))
      {
         if(result.retcode == TRADE_RETCODE_DONE)
         {
            currentTrailingStopDistance = TrailingStopDistance;
            Print("Trailing stop updated: New SL = ", newSL, " | Profit = ", profitPips, " pips");
         }
         else
         {
            Print("Failed to update trailing stop. Error: ", result.retcode);
         }
       }
   }
}

//+------------------------------------------------------------------+
//| Draw on-chart dashboard with real-time statistics               |
//+------------------------------------------------------------------+
void DrawDashboard()
{
   string prefix = "Dashboard_";
   int xOffset = 20;
   int yOffset = 30;
   int lineHeight = 18;
   color textColor = clrWhite;
   color bgColor = C'30,30,40';
   int fontSize = 9;
   
   // Calculate statistics
   double distanceToTarget = DailyTarget - dailyPnL;
   double distanceToMaxLoss = MaxDailyLoss + dailyPnL;
   string trailingStatus = "Inactive";
   
   // Check trailing stop status
   if(PositionSelect(_Symbol) && UseTrailingStop)
   {
      double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                            SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                            SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double profitPips = 0.0;
      
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
         profitPips = (currentPrice - positionOpenPrice) / point;
      else
         profitPips = (positionOpenPrice - currentPrice) / point;
      
      if(profitPips >= TrailingStopActivation)
         trailingStatus = "ACTIVE (" + DoubleToString(TrailingStopDistance, 1) + " pips)";
      else
         trailingStatus = "Waiting (" + DoubleToString(TrailingStopActivation - profitPips, 1) + " pips left)";
   }
   
   // Background rectangle
   CreateLabel(prefix + "BG", xOffset-5, yOffset-5, "", bgColor, fontSize, 400, 120);
   
   // Title
   CreateLabel(prefix + "Title", xOffset, yOffset, "═══ TRADING DASHBOARD ═══", clrGold, fontSize+1);
   
   // Daily P&L
   color plColor = (dailyPnL >= 0) ? clrLime : clrRed;
   string plText = "Daily P&L: $" + DoubleToString(dailyPnL, 2);
   CreateLabel(prefix + "PL", xOffset, yOffset + lineHeight * 1, plText, plColor, fontSize);
   
   // Trades count
   CreateLabel(prefix + "Trades", xOffset, yOffset + lineHeight * 2, 
               "Trades Today: " + IntegerToString(dailyTradeCount), textColor, fontSize);
   
   // Distance to target
   color targetColor = (distanceToTarget <= DailyTarget * 0.2) ? clrLime : clrYellow;
   CreateLabel(prefix + "Target", xOffset, yOffset + lineHeight * 3, 
               "To Target: $" + DoubleToString(distanceToTarget, 2), targetColor, fontSize);
   
   // Distance to max loss
   color lossColor = (distanceToMaxLoss <= MaxDailyLoss * 0.2) ? clrRed : clrOrange;
   CreateLabel(prefix + "MaxLoss", xOffset, yOffset + lineHeight * 4, 
               "To Max Loss: $" + DoubleToString(distanceToMaxLoss, 2), lossColor, fontSize);
   
   // Trailing stop status
   color tsColor = (trailingStatus == "Inactive") ? clrGray : clrAqua;
   CreateLabel(prefix + "Trailing", xOffset, yOffset + lineHeight * 5, 
               "Trailing Stop: " + trailingStatus, tsColor, fontSize);
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Create or update text label on chart                            |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int size, int width=0, int height=0)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
   }
   
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
   
   if(width > 0 && height > 0)
   {
      ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
      ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
   }
}
//+------------------------------------------------------------------+`;
  };

  const copyToClipboard = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success("Code copied to clipboard!");
  };

  const downloadCode = (code: string, filename: string) => {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Code downloaded!");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Code2 className="w-5 h-5 text-primary" />
        <h3 className="text-xl font-semibold">Export Strategy Code</h3>
      </div>

      <Card className="bg-secondary/30 border-border">
        <Tabs defaultValue="mql5" className="w-full">
          <TabsList className="w-full grid grid-cols-2 bg-background">
            <TabsTrigger value="mql5">MQL5 (MT5)</TabsTrigger>
            <TabsTrigger value="pine">Pine Script (TradingView)</TabsTrigger>
          </TabsList>

          <TabsContent value="mql5" className="p-0">
            <div className="relative">
              <div className="absolute top-4 right-4 flex gap-2 z-10">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => copyToClipboard(generateMQL5())}
                  className="profit-glow"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => downloadCode(generateMQL5(), `${config.instruments[0] || "Strategy"}_${config.timeframe}_EA.mq5`)}
                >
                  <Download className="w-4 h-4 mr-1" />
                  Download
                </Button>
              </div>
              <pre className="p-6 bg-background/50 rounded-lg overflow-x-auto text-xs font-mono max-h-[600px]">
                <code className="text-foreground">{generateMQL5()}</code>
              </pre>
            </div>
          </TabsContent>

          <TabsContent value="pine" className="p-6">
            <div className="bg-accent/10 border border-accent/30 rounded-lg p-4">
              <p className="text-accent text-sm">
                Pine Script export coming soon. The MQL5 version above contains the complete
                strategy logic that can be manually adapted to Pine Script for TradingView.
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </Card>

      <Card className="p-6 bg-primary/5 border-primary/20">
        <h4 className="font-semibold mb-3 text-primary">Installation Instructions (MT5)</h4>
        <ol className="space-y-2 text-sm text-muted-foreground">
          <li>1. Copy the generated MQL5 code above</li>
          <li>2. Open MetaEditor (press F4 in MT5)</li>
          <li>3. File → New → Expert Advisor</li>
          <li>4. Paste the code and save as "QuantumStrategy.mq5"</li>
          <li>5. Click Compile (F7) - ensure no errors</li>
          <li>6. Drag the EA onto your chart</li>
          <li>7. Enable AutoTrading and configure inputs</li>
        </ol>
      </Card>
    </div>
  );
};
