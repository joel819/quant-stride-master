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

  const generateIndicatorHandles = () => {
    return config.indicators.map((ind, idx) => {
      switch (ind.type) {
        case "EMA":
        case "SMA":
          return `int handle_ma_${idx};`;
        case "RSI":
          return `int handle_rsi_${idx};`;
        case "MACD":
          return `int handle_macd_${idx};`;
        case "ATR":
          return `int handle_atr_${idx};`;
        case "BB":
          return `int handle_bb_${idx};`;
        case "Stochastic":
          return `int handle_stoch_${idx};`;
        case "VWAP":
          return `// VWAP calculated manually`;
        default:
          return "";
      }
    }).filter(Boolean).join("\n");
  };

  const generateIndicatorInit = () => {
    return config.indicators.map((ind, idx) => {
      switch (ind.type) {
        case "EMA":
          return `   handle_ma_${idx} = iMA(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, 0, MODE_EMA, PRICE_CLOSE);
   if(handle_ma_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "SMA":
          return `   handle_ma_${idx} = iMA(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, 0, MODE_SMA, PRICE_CLOSE);
   if(handle_ma_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "RSI":
          return `   handle_rsi_${idx} = iRSI(_Symbol, ${getTimeframePeriod()}, ${ind.params.period}, PRICE_CLOSE);
   if(handle_rsi_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "MACD":
          return `   handle_macd_${idx} = iMACD(_Symbol, ${getTimeframePeriod()}, ${ind.params.fast || 12}, ${ind.params.slow || 26}, ${ind.params.signal || 9}, PRICE_CLOSE);
   if(handle_macd_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "ATR":
          return `   handle_atr_${idx} = iATR(_Symbol, ${getTimeframePeriod()}, ${ind.params.period || 14});
   if(handle_atr_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "BB":
          return `   handle_bb_${idx} = iBands(_Symbol, ${getTimeframePeriod()}, ${ind.params.period || 20}, 0, ${ind.params.deviation || 2}, PRICE_CLOSE);
   if(handle_bb_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        case "Stochastic":
          return `   handle_stoch_${idx} = iStochastic(_Symbol, ${getTimeframePeriod()}, ${ind.params.kPeriod || 5}, ${ind.params.dPeriod || 3}, ${ind.params.slowing || 3}, MODE_SMA, STO_LOWHIGH);
   if(handle_stoch_${idx} == INVALID_HANDLE) return(INIT_FAILED);`;
        default:
          return "";
      }
    }).filter(Boolean).join("\n");
  };

  const generateSessionCheck = () => {
    if (config.sessions.length === 0) return "   return true; // No session filter";
    
    return config.sessions.map((s) => {
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
  };

  const generateEntryLogic = () => {
    if (config.entries.length === 0) {
      return `   // No entry conditions configured
   // Please add entry conditions in the Strategy Builder
   return false;`;
    }

    return `   // Entry conditions: ${config.entries.map(e => e.description).join(", ")}
   // Implement based on your configured indicators and conditions
   
   ${config.entries.map((entry, idx) => `   // Entry ${idx + 1}: ${entry.description}
   // Logic: ${entry.logic}`).join("\n   ")}
   
   return false; // Set to true when conditions met`;
  };

  const generateStopLossCalculation = () => {
    switch (config.stopLoss.type) {
      case "atr":
        return `   // ATR-based stop loss
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(handle_atr_0, 0, 0, 1, atr) <= 0) return;
   double stopLossPips = atr[0] * ${config.stopLoss.atrMultiplier || 2} / _Point;`;
      case "structure":
        return `   // Market structure stop loss
   // Implement swing high/low logic for structure-based SL
   double stopLossPips = StopLossPips;`;
      default:
        return `   double stopLossPips = StopLossPips;`;
    }
  };

  const generateTakeProfitCalculation = () => {
    switch (config.takeProfit.type) {
      case "rr":
        return `   double takeProfit = stopLoss * TakeProfitRatio;`;
      case "trailing":
        return `   double takeProfit = stopLoss * 3; // Initial TP, will trail`;
      default:
        return `   double takeProfit = ${config.takeProfit.pips || 20} * _Point * 10;`;
    }
  };

  const generateMQL5 = () => {
    return `//+------------------------------------------------------------------+
//|                                    ${config.instruments.join("_")}_Strategy.mq5 |
//|                                    Generated by Strategy Builder |
//+------------------------------------------------------------------+
#property copyright "Quantum Strategy Builder"
#property version   "1.00"
#property strict

//--- Input Parameters
input double RiskPercent = ${config.positionSizePercent};
input double StopLossPips = ${config.stopLoss.pips || 10};
input double TakeProfitRatio = ${config.takeProfit.ratio || 2};
input int MaxDailyLoss = ${config.maxDailyLoss};
input double DailyTarget = ${config.dailyTarget};
input int MagicNumber = 12345;

//--- Indicator Handles
${generateIndicatorHandles()}

//--- Global Variables
double dailyPnL = 0.0;
datetime lastTradeDate = 0;
bool dailyTargetReached = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("Initializing ${config.instruments.join("/")} Strategy EA...");
   
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
  return `   IndicatorRelease(handle_${ind.type.toLowerCase()}_${idx});`;
}).filter(Boolean).join("\n")}
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Reset daily statistics
   datetime currentDate = TimeCurrent();
   if(TimeDay(currentDate) != TimeDay(lastTradeDate))
   {
      dailyPnL = 0.0;
      dailyTargetReached = false;
      lastTradeDate = currentDate;
      Print("New trading day started. Daily stats reset.");
   }
   
   // Check daily target reached
   if(dailyTargetReached)
   {
      Print("Daily target of ", DailyTarget, " reached. No more trades today.");
      return;
   }
   
   // Check max daily loss
   if(dailyPnL <= -MaxDailyLoss)
   {
      Print("Max daily loss of ", MaxDailyLoss, " reached. Stopping trading for today.");
      return;
   }
   
   // Update daily PnL
   UpdateDailyPnL();
   
   // Session filter
   if(!IsValidSession())
      return;
   
   // Check if we already have an open position
   if(PositionSelect(_Symbol))
      return;
   
   // Entry logic
   if(CheckEntryConditions())
   {
      OpenTrade();
   }
}

//+------------------------------------------------------------------+
//| Update daily PnL                                                 |
//+------------------------------------------------------------------+
void UpdateDailyPnL()
{
   double todayProfit = 0.0;
   datetime todayStart = iTime(_Symbol, PERIOD_D1, 0);
   
   HistorySelect(todayStart, TimeCurrent());
   int totalDeals = HistoryDealsTotal();
   
   for(int i = 0; i < totalDeals; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == MagicNumber)
      {
         todayProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
      }
   }
   
   dailyPnL = todayProfit;
   
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
   TimeCurrent(dt);
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
   
   // Calculate stop loss
${generateStopLossCalculation()}
   
   // Calculate take profit
${generateTakeProfitCalculation()}
   
   // Determine trade direction (implement your signal logic)
   ENUM_ORDER_TYPE orderType = ORDER_TYPE_BUY; // Change based on your signal
   
   // Get current price
   double price = (orderType == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Calculate SL and TP prices
   double slPrice = (orderType == ORDER_TYPE_BUY) ? price - stopLossPips * _Point : price + stopLossPips * _Point;
   double tpPrice = (orderType == ORDER_TYPE_BUY) ? price + takeProfit : price - takeProfit;
   
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
