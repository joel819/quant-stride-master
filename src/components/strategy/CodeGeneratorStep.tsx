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
  const getTimeframePeriod = (tf?: string) => {
    const timeframe = tf || config.timeframe;
    switch (timeframe) {
      case "1m": return "PERIOD_M1";
      case "5m": return "PERIOD_M5";
      case "15m": return "PERIOD_M15";
      default: return "PERIOD_M1";
    }
  };

  const getHTFPeriod = () => {
    // Higher timeframe for multi-timeframe analysis
    switch (config.timeframe) {
      case "1m": return "PERIOD_M5";   // 1m uses 5m as HTF
      case "5m": return "PERIOD_M15";  // 5m uses 15m as HTF
      case "15m": return "PERIOD_H1";  // 15m uses 1H as HTF
      default: return "PERIOD_M5";
    }
  };

  const getIndicatorHandleName = (type: string, idx: number, htf = false) => {
    const typeMap: Record<string, string> = {
      "EMA": "ma",
      "SMA": "ma",
      "RSI": "rsi",
      "MACD": "macd",
      "ATR": "atr",
      "BB": "bb",
      "Stochastic": "stoch"
    };
    const suffix = htf ? "_htf" : "";
    return `handle_${typeMap[type] || type.toLowerCase()}_${idx}${suffix}`;
  };

  const generateIndicatorHandles = () => {
    const handles = config.indicators.map((ind, idx) => {
      if (ind.type === "VWAP") return "// VWAP calculated manually";
      return `int ${getIndicatorHandleName(ind.type, idx)};`;
    }).filter(Boolean);
    
    // Add HTF handles for multi-timeframe
    const htfHandles = config.indicators.map((ind, idx) => {
      if (ind.type === "VWAP") return "";
      return `int ${getIndicatorHandleName(ind.type, idx, true)};`;
    }).filter(Boolean);
    
    return [...handles, "// HTF Indicator Handles", ...htfHandles].join("\n");
  };

  const generateIndicatorInit = () => {
    const inits = config.indicators.map((ind, idx) => {
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
    }).filter(Boolean);

    // Add HTF indicator initialization
    const htfInits = config.indicators.map((ind, idx) => {
      const handleName = getIndicatorHandleName(ind.type, idx, true);
      switch (ind.type) {
        case "EMA":
          return `   ${handleName} = iMA(_Symbol, ${getHTFPeriod()}, ${ind.params.period}, 0, MODE_EMA, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) Print("Warning: HTF EMA failed to initialize");`;
        case "SMA":
          return `   ${handleName} = iMA(_Symbol, ${getHTFPeriod()}, ${ind.params.period}, 0, MODE_SMA, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) Print("Warning: HTF SMA failed to initialize");`;
        case "RSI":
          return `   ${handleName} = iRSI(_Symbol, ${getHTFPeriod()}, ${ind.params.period}, PRICE_CLOSE);
   if(${handleName} == INVALID_HANDLE) Print("Warning: HTF RSI failed to initialize");`;
        default:
          return "";
      }
    }).filter(Boolean);

    return [...inits, "\n   // Initialize HTF indicators for multi-timeframe analysis", ...htfInits].join("\n");
  };

  const generateSessionCheck = () => {
    if (config.sessions.length === 0) return "   return true; // No session filter - trade 24/7";
    
    const sessionChecks = config.sessions.map((s) => {
      switch (s) {
        case "london":
          return "      if(hour >= 8 && hour < 16) { Print(\"Session OK: London\"); return true; }";
        case "newyork":
          return "      if(hour >= 13 && hour < 21) { Print(\"Session OK: New York\"); return true; }";
        case "overlap":
          return "      if(hour >= 13 && hour < 16) { Print(\"Session OK: London-NY Overlap\"); return true; }";
        case "asian":
          return "      if(hour >= 0 && hour < 8) { Print(\"Session OK: Asian\"); return true; }";
        default:
          return "";
      }
    }).filter(Boolean).join("\n");
    
    return `   // Check configured sessions
${sessionChecks}
   
   // No matching session found
   return false;`;
  };

  const generateMQL5 = () => {
    const hasEMA = config.indicators.some(ind => ind.type === "EMA");
    const hasBB = config.indicators.some(ind => ind.type === "BB");
    const hasRSI = config.indicators.some(ind => ind.type === "RSI");
    const hasMACD = config.indicators.some(ind => ind.type === "MACD");
    const hasATR = config.indicators.some(ind => ind.type === "ATR");
    
    const emaInd = config.indicators.find(ind => ind.type === "EMA");

    return `//+------------------------------------------------------------------+
//|                              ${config.instruments.join("_")}_AdvancedEA.mq5 |
//|                              Generated by Advanced Strategy Builder |
//|                              Features: MTF + News + Money Mgmt     |
//+------------------------------------------------------------------+
#property copyright "Quantum Strategy Builder Pro"
#property version   "2.00"
#property description "Advanced mechanical trading strategy"
#property description "Features: Multi-TF, News Filter, Money Mgmt, Multiple Entry Types"

//+------------------------------------------------------------------+
//|                         ENUMERATIONS                              |
//+------------------------------------------------------------------+
// NOTE: Enums MUST be declared before input parameters in MQL5
enum ENUM_MM_TYPE
{
   MM_FIXED = 0,           // Fixed lot size
   MM_MARTINGALE = 1,      // Martingale (double after loss)
   MM_ANTI_MARTINGALE = 2, // Anti-Martingale (double after win)
   MM_RECOVERY = 3         // Recovery (increase after loss streak)
};

enum ENUM_SIGNAL_TYPE
{
   SIGNAL_NONE = 0,
   SIGNAL_SCALP_LONG = 1,
   SIGNAL_SCALP_SHORT = -1,
   SIGNAL_BREAKOUT_LONG = 2,
   SIGNAL_BREAKOUT_SHORT = -2,
   SIGNAL_REVERSAL_LONG = 3,
   SIGNAL_REVERSAL_SHORT = -3
};

//+------------------------------------------------------------------+
//|                         INPUT PARAMETERS                          |
//+------------------------------------------------------------------+

input group "=== Risk Management ==="
input double RiskPercent = ${config.positionSizePercent || 1.0};      // Risk per trade (%)
input double StopLossPips = ${config.stopLoss.pips || 10.0};          // Base Stop Loss (pips)
input double TakeProfitRatio = ${config.takeProfit.ratio || 2.0};     // Take Profit Ratio

input group "=== Multi-Timeframe Settings ==="
input bool UseMTF = true;                                              // Enable Multi-Timeframe Analysis
input bool RequireHTFAlignment = true;                                 // Require HTF trend alignment

input group "=== News Filter ==="
input bool UseNewsFilter = true;                                       // Enable News Filter
input int NewsMinutesBefore = 30;                                      // Stop trading X mins before news
input int NewsMinutesAfter = 30;                                       // Resume trading X mins after news
input ENUM_DAY_OF_WEEK NFPDay = FRIDAY;                                // NFP Day (usually Friday)
input int NFPWeek = 1;                                                 // NFP Week of month (1 = first)

input group "=== Entry Types ==="
input bool UseScalping = true;                                         // Enable Scalping Entries
input bool UseBreakout = true;                                         // Enable Breakout Entries
input bool UseReversal = true;                                         // Enable Reversal Entries
input double BreakoutPips = 5.0;                                       // Breakout threshold (pips)

input group "=== Advanced Money Management ==="
input ENUM_MM_TYPE MoneyManagement = MM_FIXED;                         // Money Management Type
input double MartingaleMultiplier = 2.0;                               // Martingale/Anti multiplier
input int MaxMartingaleTrades = 3;                                     // Max consecutive scaling
input bool UseGridTrading = false;                                     // Enable Grid Mode
input double GridSpacing = 10.0;                                       // Grid spacing (pips)
input int MaxGridLevels = 5;                                           // Max grid levels

input group "=== Breakeven ==="
input bool UseBreakeven = true;                                        // Enable Breakeven
input double BreakevenActivation = 10.0;                               // Activate after profit (pips)
input double BreakevenBuffer = 2.0;                                    // Buffer above/below entry (pips)

input group "=== Trailing Stop ==="
input bool UseTrailingStop = true;                                     // Enable Trailing Stop
input double TrailingStopDistance = 10.0;                              // Trailing Stop Distance (pips)
input double TrailingStopActivation = 15.0;                            // Activate after profit (pips)

input group "=== Partial Profit Taking ==="
input bool UsePartialTP = true;                                        // Enable Partial Take Profit
input double PartialTPPercent = 50.0;                                  // Close % at TP1 (0-100)
input double PartialTPPips = 10.0;                                     // TP1 distance (pips)
input bool MoveToBreakevenAfterPartial = true;                         // Move SL to BE after partial

input group "=== Daily Limits ==="
input int MaxDailyLoss = ${config.maxDailyLoss || 100};                // Max Daily Loss ($)
input double DailyTarget = ${config.dailyTarget || 200.0};             // Daily Target ($)
input int MaxDailyTrades = 10;                                         // Max trades per day

input group "=== General Settings ==="
input int MagicNumber = 12345;                                         // Magic Number
input bool EnableDebugMode = true;                                     // Enable detailed logging

//+------------------------------------------------------------------+
//|                       INDICATOR HANDLES                           |
//+------------------------------------------------------------------+
${generateIndicatorHandles()}

//+------------------------------------------------------------------+
//|                       GLOBAL VARIABLES                            |
//+------------------------------------------------------------------+
double dailyPnL = 0.0;
datetime lastTradeDate;
bool dailyTargetReached = false;
ENUM_SIGNAL_TYPE lastSignal = SIGNAL_NONE;
int dailyTradeCount = 0;
double currentTrailingStopDistance = 0.0;
bool breakevenApplied = false;
double pipMultiplier = 1.0;

// Money management tracking
int consecutiveLosses = 0;
int consecutiveWins = 0;
double lastLotSize = 0.0;
int martingaleLevel = 0;

// Grid trading
int gridLevel = 0;
double gridBaseLot = 0.0;
double gridBasePrice = 0.0;

// News time tracking
datetime nextNewsTime = 0;
bool isNewsTime = false;

// HTF trend tracking
int htfTrend = 0; // 1 = bullish, -1 = bearish, 0 = neutral

// Partial profit tracking
bool partialTPTaken = false;
double originalPositionSize = 0.0;

// Structure tracking for breakouts
double recentHigh = 0.0;
double recentLow = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("=========================================");
   Print("Initializing Advanced ${config.instruments.join("/")} Strategy EA...");
   Print("Features: MTF=", UseMTF, " | News=", UseNewsFilter, " | MM=", EnumToString(MoneyManagement));
   Print("Entry Types: Scalp=", UseScalping, " | Breakout=", UseBreakout, " | Reversal=", UseReversal);
   Print("=========================================");
   
   // Initialize date tracking
   lastTradeDate = TimeCurrent();
   
   // Determine pip multiplier based on symbol type and digits
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string symbolName = _Symbol;
   
   // Check if this is a synthetic index (Volatility, Boom, Crash, Jump, Step, Range)
   bool isSynthetic = (StringFind(symbolName, "Volatility") >= 0 ||
                       StringFind(symbolName, "Vol") >= 0 ||
                       StringFind(symbolName, "Boom") >= 0 ||
                       StringFind(symbolName, "Crash") >= 0 ||
                       StringFind(symbolName, "Jump") >= 0 ||
                       StringFind(symbolName, "Step") >= 0 ||
                       StringFind(symbolName, "Range") >= 0 ||
                       StringFind(symbolName, "1 Index") >= 0 ||
                       StringFind(symbolName, "10 Index") >= 0 ||
                       StringFind(symbolName, "25 Index") >= 0 ||
                       StringFind(symbolName, "50 Index") >= 0 ||
                       StringFind(symbolName, "75 Index") >= 0 ||
                       StringFind(symbolName, "100 Index") >= 0 ||
                       StringFind(symbolName, "200 Index") >= 0 ||
                       StringFind(symbolName, "300 Index") >= 0);
   
   // Check if this is a stock index (NAS100, US30, etc.)
   bool isStockIndex = (StringFind(symbolName, "NAS") >= 0 ||
                        StringFind(symbolName, "US30") >= 0 ||
                        StringFind(symbolName, "US500") >= 0 ||
                        StringFind(symbolName, "SPX") >= 0 ||
                        StringFind(symbolName, "GER") >= 0 ||
                        StringFind(symbolName, "UK100") >= 0 ||
                        StringFind(symbolName, "JP225") >= 0);
   
   // Get minimum stop level from broker FIRST
   long minStopPoints = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minStopLevel = minStopPoints * _Point;
   double currentSpread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double spreadPrice = currentSpread * _Point;
   
   Print("=== STOP LEVEL ANALYSIS ===");
   Print("Symbol: ", _Symbol, " | Digits: ", digits);
   Print("Min stop level (points): ", minStopPoints, " | Min stop level (price): ", minStopLevel);
   Print("Current spread (points): ", currentSpread, " | Spread (price): ", spreadPrice);
   
   // CRITICAL FIX: For synthetic indices, calculate MINIMUM safe stop first
   // V75 and similar synthetics require 200-1000+ point stops depending on broker
   double absoluteMinStopPrice = 0;
   
   if(isSynthetic)
   {
      Print("Detected SYNTHETIC INDEX");
      
      // For synthetics, we need to ensure stops are FAR enough
      // Minimum should be at least: max(broker_min_stop, 200 points) + spread * 5
      double minRequired = MathMax((double)minStopPoints, 200.0);
      absoluteMinStopPrice = (minRequired + currentSpread * 5) * _Point;
      
      // pipMultiplier for synthetics: 1 pip = 1 point
      pipMultiplier = 1.0;
      
      // Now ensure StopLossPips * pipMultiplier * _Point >= absoluteMinStopPrice
      double calculatedDistance = StopLossPips * pipMultiplier * _Point;
      
      if(calculatedDistance < absoluteMinStopPrice)
      {
         // Increase multiplier to make stops safe
         double requiredMultiplier = absoluteMinStopPrice / (StopLossPips * _Point);
         pipMultiplier = MathCeil(requiredMultiplier * 1.5); // 50% safety buffer
         Print("SYNTHETIC: Increased pipMultiplier to ", pipMultiplier, " for safe stops");
      }
      
      Print("Absolute min stop price: ", absoluteMinStopPrice, " | Current calculated: ", StopLossPips * pipMultiplier * _Point);
   }
   else if(isStockIndex)
   {
      pipMultiplier = 1.0;
      absoluteMinStopPrice = (MathMax((double)minStopPoints, 50.0) + currentSpread * 3) * _Point;
      
      double calculatedDistance = StopLossPips * pipMultiplier * _Point;
      if(calculatedDistance < absoluteMinStopPrice)
      {
         double requiredMultiplier = absoluteMinStopPrice / (StopLossPips * _Point);
         pipMultiplier = MathCeil(requiredMultiplier * 1.5);
         Print("STOCK INDEX: Increased pipMultiplier to ", pipMultiplier, " for safe stops");
      }
      
      Print("Detected STOCK INDEX - using pipMultiplier: ", pipMultiplier);
   }
   else if(digits == 3 || digits == 5)
   {
      pipMultiplier = 10.0;
   }
   else if(digits == 2)
   {
      pipMultiplier = 1.0;
   }
   else
   {
      pipMultiplier = 1.0;
   }
   
   // FINAL SAFETY CHECK: Always verify against broker minimum
   double testDistance = StopLossPips * _Point * pipMultiplier;
   double safeMinStop = minStopLevel + spreadPrice * 5; // Add generous spread buffer
   
   if(testDistance < safeMinStop && safeMinStop > 0)
   {
      double requiredMultiplier = (safeMinStop / (_Point * StopLossPips)) * 2.0; // Double buffer
      if(requiredMultiplier > pipMultiplier)
      {
         pipMultiplier = MathCeil(requiredMultiplier);
         Print("*** FINAL ADJUSTMENT - pipMultiplier increased to: ", pipMultiplier);
      }
   }
   
   Print("Final pip multiplier: ", pipMultiplier);
   Print("Final SL distance: ", StopLossPips * _Point * pipMultiplier, " | Safe min: ", safeMinStop);
   Print("=== END STOP LEVEL ANALYSIS ===");
   
   // Initialize indicators
${generateIndicatorInit()}
   
   // Initialize structure tracking
   UpdateMarketStructure();
   
   // Initialize news calendar check
   if(UseNewsFilter)
      CheckNewsCalendar();
   
   Print("All indicators initialized successfully");
   Print("=========================================");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "Dashboard_");
   
${config.indicators.map((ind, idx) => {
  if (ind.type === "VWAP") return "";
  return `   IndicatorRelease(${getIndicatorHandleName(ind.type, idx)});
   IndicatorRelease(${getIndicatorHandleName(ind.type, idx, true)});`;
}).filter(Boolean).join("\n")}
   
   Print("EA deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Update dashboard on every tick
   DrawDashboard();
   
   // Manage open positions on EVERY tick
   if(HasOpenPosition())
   {
      // Partial profit taking - check first
      if(UsePartialTP && !partialTPTaken)
         ManagePartialTP();
      
      if(UseBreakeven && !breakevenApplied)
         ManageBreakeven();
      
      if(UseTrailingStop)
         ManageTrailingStop();
      
      // Grid management
      if(UseGridTrading)
         ManageGrid();
   }
   else
   {
      breakevenApplied = false;
      partialTPTaken = false;
      originalPositionSize = 0.0;
      gridLevel = 0;
   }
   
   // Only check for new trades on new bar
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, ${getTimeframePeriod()}, 0);
   
   if(currentBarTime == lastBarTime)
      return;
   lastBarTime = currentBarTime;
   
   // Reset daily statistics
   MqlDateTime currentTime, lastTradeTime;
   TimeToStruct(TimeCurrent(), currentTime);
   TimeToStruct(lastTradeDate, lastTradeTime);
   
   if(currentTime.day != lastTradeTime.day || currentTime.mon != lastTradeTime.mon || currentTime.year != lastTradeTime.year)
   {
      dailyPnL = 0.0;
      dailyTradeCount = 0;
      dailyTargetReached = false;
      lastTradeDate = TimeCurrent();
      consecutiveLosses = 0;
      consecutiveWins = 0;
      martingaleLevel = 0;
      Print("========== NEW TRADING DAY STARTED ==========");
   }
   
   // Update daily PnL
   UpdateDailyPnL();
   
   // Update market structure
   UpdateMarketStructure();
   
   // Update HTF trend
   if(UseMTF)
      UpdateHTFTrend();
   
   // Update news status
   if(UseNewsFilter)
      CheckNewsCalendar();
   
   // === TRADING FILTERS ===
   
   // Daily target check
   if(dailyTargetReached)
   {
      if(EnableDebugMode) Print("Daily target reached. No new trades.");
      return;
   }
   
   // Max daily loss check
   if(dailyPnL <= -MaxDailyLoss)
   {
      if(EnableDebugMode) Print("Max daily loss hit. No new trades.");
      return;
   }
   
   // Max daily trades check
   if(dailyTradeCount >= MaxDailyTrades)
   {
      if(EnableDebugMode) Print("Max daily trades reached. No new trades.");
      return;
   }
   
   // News filter check
   if(UseNewsFilter && isNewsTime)
   {
      if(EnableDebugMode) Print("News time active. No new trades.");
      return;
   }
   
   // Session filter
   if(!IsValidSession())
      return;
   
   // Skip if position already open (unless grid trading)
   if(HasOpenPosition() && !UseGridTrading)
      return;
   
   if(EnableDebugMode) Print("Checking entry conditions...");
   
   // Check entry conditions
   ENUM_SIGNAL_TYPE signal = CheckAllEntryConditions();
   
   if(signal != SIGNAL_NONE)
   {
      lastSignal = signal;
      Print("===== SIGNAL DETECTED: ", EnumToString(signal), " =====");
      OpenTrade(signal);
   }
}

//+------------------------------------------------------------------+
//| Check all entry condition types                                  |
//+------------------------------------------------------------------+
ENUM_SIGNAL_TYPE CheckAllEntryConditions()
{
   // Get price data
   double close[], open[], high[], low[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   if(CopyClose(_Symbol, ${getTimeframePeriod()}, 0, 10, close) < 10) return SIGNAL_NONE;
   if(CopyOpen(_Symbol, ${getTimeframePeriod()}, 0, 10, open) < 10) return SIGNAL_NONE;
   if(CopyHigh(_Symbol, ${getTimeframePeriod()}, 0, 10, high) < 10) return SIGNAL_NONE;
   if(CopyLow(_Symbol, ${getTimeframePeriod()}, 0, 10, low) < 10) return SIGNAL_NONE;
   
   bool isBullishCandle = close[1] > open[1];
   bool isBearishCandle = close[1] < open[1];
   double candleBody = MathAbs(close[1] - open[1]);
   double candleRange = high[1] - low[1];
   
   // Get indicator values
${hasEMA ? `   double ema_val[];
   ArraySetAsSeries(ema_val, true);
   if(CopyBuffer(${getIndicatorHandleName("EMA", config.indicators.findIndex(ind => ind.type === "EMA"))}, 0, 0, 5, ema_val) < 5) return SIGNAL_NONE;
   
   double ema_htf[];
   ArraySetAsSeries(ema_htf, true);
   CopyBuffer(${getIndicatorHandleName("EMA", config.indicators.findIndex(ind => ind.type === "EMA"), true)}, 0, 0, 3, ema_htf);` : ''}

${hasBB ? `   double bb_upper[], bb_middle[], bb_lower[];
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_middle, true);
   ArraySetAsSeries(bb_lower, true);
   if(CopyBuffer(${getIndicatorHandleName("BB", config.indicators.findIndex(ind => ind.type === "BB"))}, 1, 0, 5, bb_upper) < 5) return SIGNAL_NONE;
   if(CopyBuffer(${getIndicatorHandleName("BB", config.indicators.findIndex(ind => ind.type === "BB"))}, 0, 0, 5, bb_middle) < 5) return SIGNAL_NONE;
   if(CopyBuffer(${getIndicatorHandleName("BB", config.indicators.findIndex(ind => ind.type === "BB"))}, 2, 0, 5, bb_lower) < 5) return SIGNAL_NONE;` : ''}

${hasRSI ? `   double rsi_val[];
   ArraySetAsSeries(rsi_val, true);
   if(CopyBuffer(${getIndicatorHandleName("RSI", config.indicators.findIndex(ind => ind.type === "RSI"))}, 0, 0, 5, rsi_val) < 5) return SIGNAL_NONE;
   
   double rsi_htf[];
   ArraySetAsSeries(rsi_htf, true);
   CopyBuffer(${getIndicatorHandleName("RSI", config.indicators.findIndex(ind => ind.type === "RSI"), true)}, 0, 0, 3, rsi_htf);` : ''}

${hasMACD ? `   double macd_main[], macd_signal[];
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   if(CopyBuffer(${getIndicatorHandleName("MACD", config.indicators.findIndex(ind => ind.type === "MACD"))}, 0, 0, 5, macd_main) < 5) return SIGNAL_NONE;
   if(CopyBuffer(${getIndicatorHandleName("MACD", config.indicators.findIndex(ind => ind.type === "MACD"))}, 1, 0, 5, macd_signal) < 5) return SIGNAL_NONE;` : ''}

   // MTF Filter
   bool htfBullish = !UseMTF || !RequireHTFAlignment || htfTrend >= 0;
   bool htfBearish = !UseMTF || !RequireHTFAlignment || htfTrend <= 0;
   
   double pipValue = _Point * pipMultiplier;
   
   // ============= SCALPING ENTRIES =============
   if(UseScalping)
   {
${hasEMA && hasBB ? `      // BB bounce with EMA filter
      bool scalpLong = (low[1] <= bb_lower[1] && close[1] > bb_lower[1] && close[1] > ema_val[1] && isBullishCandle);
      bool scalpShort = (high[1] >= bb_upper[1] && close[1] < bb_upper[1] && close[1] < ema_val[1] && isBearishCandle);
      
      if(scalpLong && htfBullish)
      {
         Print("SCALP LONG: BB lower bounce + EMA support");
         return SIGNAL_SCALP_LONG;
      }
      if(scalpShort && htfBearish)
      {
         Print("SCALP SHORT: BB upper bounce + EMA resistance");
         return SIGNAL_SCALP_SHORT;
      }` : hasEMA ? `      // EMA pullback scalp
      bool scalpLong = (close[2] < ema_val[2] && close[1] > ema_val[1] && isBullishCandle);
      bool scalpShort = (close[2] > ema_val[2] && close[1] < ema_val[1] && isBearishCandle);
      
      if(scalpLong && htfBullish)
      {
         Print("SCALP LONG: Price crossed above EMA");
         return SIGNAL_SCALP_LONG;
      }
      if(scalpShort && htfBearish)
      {
         Print("SCALP SHORT: Price crossed below EMA");
         return SIGNAL_SCALP_SHORT;
      }` : `      // Price action scalp
      bool scalpLong = (isBullishCandle && candleBody > candleRange * 0.6);
      bool scalpShort = (isBearishCandle && candleBody > candleRange * 0.6);
      
      if(scalpLong && htfBullish)
      {
         Print("SCALP LONG: Strong bullish candle");
         return SIGNAL_SCALP_LONG;
      }
      if(scalpShort && htfBearish)
      {
         Print("SCALP SHORT: Strong bearish candle");
         return SIGNAL_SCALP_SHORT;
      }`}
   }
   
   // ============= BREAKOUT ENTRIES =============
   if(UseBreakout)
   {
      double breakoutDistance = BreakoutPips * pipValue;
      
      // Check for structure breakout
      bool breakoutLong = (close[1] > recentHigh + breakoutDistance) && isBullishCandle;
      bool breakoutShort = (close[1] < recentLow - breakoutDistance) && isBearishCandle;
      
${hasBB ? `      // BB breakout confirmation
      double bbWidth = (bb_upper[1] - bb_lower[1]) / bb_middle[1] * 100;
      bool validBBBreakout = bbWidth > 1.0; // Minimum volatility
      breakoutLong = breakoutLong && validBBBreakout;
      breakoutShort = breakoutShort && validBBBreakout;` : ''}
      
      if(breakoutLong && htfBullish)
      {
         Print("BREAKOUT LONG: Price broke above structure high ", recentHigh);
         return SIGNAL_BREAKOUT_LONG;
      }
      if(breakoutShort && htfBearish)
      {
         Print("BREAKOUT SHORT: Price broke below structure low ", recentLow);
         return SIGNAL_BREAKOUT_SHORT;
      }
   }
   
   // ============= REVERSAL ENTRIES =============
   if(UseReversal)
   {
${hasRSI ? `      // RSI extreme reversal
      bool rsiOversold = rsi_val[2] < 25 && rsi_val[1] > 25 && rsi_val[1] > rsi_val[2];
      bool rsiOverbought = rsi_val[2] > 75 && rsi_val[1] < 75 && rsi_val[1] < rsi_val[2];
      
      if(rsiOversold && isBullishCandle && htfBullish)
      {
         Print("REVERSAL LONG: RSI oversold bounce from ", rsi_val[2]);
         return SIGNAL_REVERSAL_LONG;
      }
      if(rsiOverbought && isBearishCandle && htfBearish)
      {
         Print("REVERSAL SHORT: RSI overbought rejection from ", rsi_val[2]);
         return SIGNAL_REVERSAL_SHORT;
      }` : ''}

${hasBB ? `      // Double BB touch reversal
      bool doubleBBLong = (low[2] < bb_lower[2] && low[1] < bb_lower[1] && close[1] > bb_lower[1] && isBullishCandle);
      bool doubleBBShort = (high[2] > bb_upper[2] && high[1] > bb_upper[1] && close[1] < bb_upper[1] && isBearishCandle);
      
      if(doubleBBLong && htfBullish)
      {
         Print("REVERSAL LONG: Double BB lower touch");
         return SIGNAL_REVERSAL_LONG;
      }
      if(doubleBBShort && htfBearish)
      {
         Print("REVERSAL SHORT: Double BB upper touch");
         return SIGNAL_REVERSAL_SHORT;
      }` : ''}

      // Engulfing pattern reversal
      bool bullishEngulf = (open[1] < close[2] && close[1] > open[2] && candleBody > MathAbs(open[2] - close[2]) * 1.5);
      bool bearishEngulf = (open[1] > close[2] && close[1] < open[2] && candleBody > MathAbs(open[2] - close[2]) * 1.5);
      
      if(bullishEngulf && htfBullish)
      {
         Print("REVERSAL LONG: Bullish engulfing pattern");
         return SIGNAL_REVERSAL_LONG;
      }
      if(bearishEngulf && htfBearish)
      {
         Print("REVERSAL SHORT: Bearish engulfing pattern");
         return SIGNAL_REVERSAL_SHORT;
      }
   }
   
   return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| Update market structure (recent highs/lows)                      |
//+------------------------------------------------------------------+
void UpdateMarketStructure()
{
   double high[], low[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   
   if(CopyHigh(_Symbol, ${getTimeframePeriod()}, 0, 20, high) < 20) return;
   if(CopyLow(_Symbol, ${getTimeframePeriod()}, 0, 20, low) < 20) return;
   
   // Find recent swing high (highest of last 20 bars, excluding current)
   recentHigh = high[1];
   recentLow = low[1];
   
   for(int i = 1; i < 20; i++)
   {
      if(high[i] > recentHigh) recentHigh = high[i];
      if(low[i] < recentLow) recentLow = low[i];
   }
}

//+------------------------------------------------------------------+
//| Update HTF trend direction                                       |
//+------------------------------------------------------------------+
void UpdateHTFTrend()
{
${hasEMA ? `   double ema_htf[];
   ArraySetAsSeries(ema_htf, true);
   if(CopyBuffer(${getIndicatorHandleName("EMA", config.indicators.findIndex(ind => ind.type === "EMA"), true)}, 0, 0, 5, ema_htf) < 5)
   {
      htfTrend = 0;
      return;
   }
   
   double htfClose[];
   ArraySetAsSeries(htfClose, true);
   if(CopyClose(_Symbol, ${getHTFPeriod()}, 0, 5, htfClose) < 5)
   {
      htfTrend = 0;
      return;
   }
   
   // Determine HTF trend
   if(htfClose[1] > ema_htf[1] && ema_htf[1] > ema_htf[2])
      htfTrend = 1;  // Bullish
   else if(htfClose[1] < ema_htf[1] && ema_htf[1] < ema_htf[2])
      htfTrend = -1; // Bearish
   else
      htfTrend = 0;  // Neutral
   
   if(EnableDebugMode) Print("HTF Trend: ", (htfTrend == 1 ? "BULLISH" : htfTrend == -1 ? "BEARISH" : "NEUTRAL"));` : `   htfTrend = 0; // No EMA for HTF analysis`}
}

//+------------------------------------------------------------------+
//| Check news calendar (simplified time-based)                      |
//+------------------------------------------------------------------+
void CheckNewsCalendar()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // High impact news times (simplified - major economic releases)
   // NFP: First Friday of month, 8:30 AM EST (13:30 GMT)
   // FOMC: Usually 2:00 PM EST (19:00 GMT)
   // ECB: Usually 7:45 AM EST (12:45 GMT)
   
   isNewsTime = false;
   
   // NFP Check (First Friday of month)
   if(dt.day_of_week == NFPDay && dt.day <= 7)
   {
      // NFP is usually at 13:30 GMT
      int nfpHour = 13;
      int nfpMinute = 30;
      
      int currentMinutes = dt.hour * 60 + dt.min;
      int nfpMinutes = nfpHour * 60 + nfpMinute;
      
      if(currentMinutes >= (nfpMinutes - NewsMinutesBefore) && currentMinutes <= (nfpMinutes + NewsMinutesAfter))
      {
         isNewsTime = true;
         if(EnableDebugMode) Print("NEWS FILTER: NFP time window active");
      }
   }
   
   // FOMC Check (Every 6 weeks, Wednesdays at 19:00 GMT)
   if(dt.day_of_week == WEDNESDAY)
   {
      int fomcHour = 19;
      if(dt.hour >= (fomcHour - 1) && dt.hour <= (fomcHour + 1))
      {
         // Could be FOMC day - be cautious
         // In real implementation, would check calendar API
      }
   }
   
   // Daily high-impact times (8:30, 10:00, 14:00, 14:30 GMT)
   int highImpactHours[] = {8, 10, 14};
   for(int i = 0; i < ArraySize(highImpactHours); i++)
   {
      if(dt.hour == highImpactHours[i] && dt.min <= 35 && dt.min >= 25)
      {
         // Potential news release time
         if(EnableDebugMode) Print("NEWS FILTER: Potential high-impact time");
      }
   }
}

//+------------------------------------------------------------------+
//| Open trade with advanced money management                        |
//+------------------------------------------------------------------+
void OpenTrade(ENUM_SIGNAL_TYPE signal)
{
   // Calculate lot size with money management
   double lotSize = CalculateLotSize();
   
   // Declare stop loss and take profit
   double stopLossPips = StopLossPips;
   double takeProfitPips = stopLossPips * TakeProfitRatio;
   
   // Adjust SL/TP based on signal type
   if(signal == SIGNAL_BREAKOUT_LONG || signal == SIGNAL_BREAKOUT_SHORT)
   {
      stopLossPips *= 1.5;  // Wider stops for breakouts
      takeProfitPips = stopLossPips * TakeProfitRatio * 1.2; // Better RR for breakouts
   }
   else if(signal == SIGNAL_REVERSAL_LONG || signal == SIGNAL_REVERSAL_SHORT)
   {
      takeProfitPips = stopLossPips * TakeProfitRatio * 1.5; // Better RR for reversals
   }
   
   // Determine direction
   bool isLong = (signal > 0);
   ENUM_ORDER_TYPE orderType = isLong ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   
   // Get current price
   double price = isLong ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Convert pips to price distance
   double pipValue = _Point * pipMultiplier;
   double slDistance = stopLossPips * pipValue;
   double tpDistance = takeProfitPips * pipValue;
   
   // Calculate SL and TP prices
   double slPrice = isLong ? price - slDistance : price + slDistance;
   double tpPrice = isLong ? price + tpDistance : price - tpDistance;
   
   // CRITICAL: Validate stops against broker minimum BEFORE sending order
   long minStopPoints = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double currentSpread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double minStopDistance = minStopPoints * _Point;
   double spreadPrice = currentSpread * _Point;
   
   // Synthetic indices and volatile instruments need extra buffer
   string symbolName = _Symbol;
   bool isSynthetic = (StringFind(symbolName, "Volatility") >= 0 ||
                       StringFind(symbolName, "Vol") >= 0 ||
                       StringFind(symbolName, "Boom") >= 0 ||
                       StringFind(symbolName, "Crash") >= 0 ||
                       StringFind(symbolName, "Jump") >= 0 ||
                       StringFind(symbolName, "Step") >= 0 ||
                       StringFind(symbolName, "Range") >= 0);
   
   // Calculate safe minimum distance with generous buffers
   double spreadMultiplier = isSynthetic ? 10.0 : 5.0;
   double safeMinDistance = MathMax(minStopDistance, 100 * _Point) + spreadPrice * spreadMultiplier;
   
   if(isSynthetic)
   {
      // For synthetics, enforce absolute minimum of 300 points
      safeMinDistance = MathMax(safeMinDistance, 300 * _Point);
   }
   
   // Check and adjust SL distance if too close
   double actualSLDistance = MathAbs(price - slPrice);
   if(actualSLDistance < safeMinDistance)
   {
      Print("WARNING: SL too close! Current: ", actualSLDistance, " | Min required: ", safeMinDistance);
      // Increase SL distance to safe minimum with extra buffer
      slDistance = safeMinDistance * 2.0;
      slPrice = isLong ? price - slDistance : price + slDistance;
      // Recalculate TP to maintain RR
      tpDistance = slDistance * TakeProfitRatio;
      tpPrice = isLong ? price + tpDistance : price - tpDistance;
      Print("ADJUSTED: New SL distance: ", slDistance, " | New TP distance: ", tpDistance);
   }
   
   // Check and adjust TP distance if too close
   double actualTPDistance = MathAbs(price - tpPrice);
   if(actualTPDistance < safeMinDistance)
   {
      Print("WARNING: TP too close! Current: ", actualTPDistance, " | Min required: ", safeMinDistance);
      tpDistance = safeMinDistance * 2.5;
      tpPrice = isLong ? price + tpDistance : price - tpDistance;
      Print("ADJUSTED: New TP distance: ", tpDistance);
   }
   
   // Normalize prices
   slPrice = NormalizeDouble(slPrice, _Digits);
   tpPrice = NormalizeDouble(tpPrice, _Digits);
   
   Print("Opening ", (isLong ? "BUY" : "SELL"), " | Signal: ", EnumToString(signal));
   Print("Price: ", price, " | SL: ", slPrice, " (dist: ", actualSLDistance, " -> ", MathAbs(price - slPrice), ") | TP: ", tpPrice, " | Lot: ", lotSize);
   Print("Min stop level: ", minStopDistance, " | Safe min: ", safeMinDistance, " | Spread: ", spreadPrice);
   
   // Get filling mode
   ENUM_ORDER_TYPE_FILLING fillType = GetAllowedFillingMode();
   
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
   request.deviation = 30;
   request.magic = MagicNumber;
   request.comment = "QSB_" + EnumToString(signal);
   request.type_filling = fillType;
   
   // Send order
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
      {
         Print("*** ORDER PLACED SUCCESSFULLY *** Ticket: ", result.order);
         dailyTradeCount++;
         lastLotSize = lotSize;
         
         // Track original position size for partial TP
         originalPositionSize = lotSize;
         partialTPTaken = false;
         
         // Grid base setup
         if(UseGridTrading)
         {
            gridBaseLot = lotSize;
            gridBasePrice = price;
            gridLevel = 1;
         }
      }
      else
      {
         Print("Order failed. Error: ", result.retcode, " - ", GetRetcodeDescription(result.retcode));
      }
   }
   else
   {
      Print("OrderSend failed. Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Calculate lot size with money management                         |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (RiskPercent / 100.0);
   
   // Get tick value
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   
   // Calculate pip value
   double pipValue = _Point * pipMultiplier;
   double pipsValue = (pipValue / tickSize) * tickValue;
   
   // Base lot size
   double baseLotSize = 0.0;
   if(pipsValue > 0)
      baseLotSize = riskAmount / (StopLossPips * pipsValue);
   
   // Apply money management
   double lotSize = baseLotSize;
   
   switch(MoneyManagement)
   {
      case MM_FIXED:
         // Use base lot size
         lotSize = baseLotSize;
         break;
         
      case MM_MARTINGALE:
         // Double after each loss
         if(consecutiveLosses > 0 && martingaleLevel < MaxMartingaleTrades)
         {
            double multiplier = MathPow(MartingaleMultiplier, MathMin(consecutiveLosses, MaxMartingaleTrades));
            lotSize = baseLotSize * multiplier;
            martingaleLevel++;
            Print("MARTINGALE: Level ", martingaleLevel, " | Multiplier: ", multiplier);
         }
         else if(consecutiveLosses == 0)
         {
            martingaleLevel = 0;
         }
         break;
         
      case MM_ANTI_MARTINGALE:
         // Increase after wins
         if(consecutiveWins > 0)
         {
            double multiplier = 1.0 + (MartingaleMultiplier - 1.0) * MathMin(consecutiveWins, MaxMartingaleTrades) / MaxMartingaleTrades;
            lotSize = baseLotSize * multiplier;
            Print("ANTI-MARTINGALE: Wins=", consecutiveWins, " | Multiplier: ", multiplier);
         }
         break;
         
      case MM_RECOVERY:
         // Gradually increase after loss streak
         if(consecutiveLosses >= 2)
         {
            double recoveryMultiplier = 1.0 + (consecutiveLosses * 0.25);
            lotSize = baseLotSize * MathMin(recoveryMultiplier, MartingaleMultiplier);
            Print("RECOVERY: Losses=", consecutiveLosses, " | Multiplier: ", recoveryMultiplier);
         }
         break;
   }
   
   // Normalize to allowed lot sizes
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathMax(minLot, MathMin(maxLot, lotSize));
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   
   return NormalizeDouble(lotSize, 2);
}

//+------------------------------------------------------------------+
//| Manage grid trading                                              |
//+------------------------------------------------------------------+
void ManageGrid()
{
   if(!SelectOurPosition())
      return;
   
   if(gridLevel >= MaxGridLevels)
      return;
   
   double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double pipValue = _Point * pipMultiplier;
   long positionType = PositionGetInteger(POSITION_TYPE);
   
   double distance = 0.0;
   bool shouldAddLevel = false;
   
   if(positionType == POSITION_TYPE_BUY)
   {
      distance = (gridBasePrice - currentPrice) / pipValue;
      shouldAddLevel = (distance >= GridSpacing * gridLevel);
   }
   else
   {
      distance = (currentPrice - gridBasePrice) / pipValue;
      shouldAddLevel = (distance >= GridSpacing * gridLevel);
   }
   
   if(shouldAddLevel)
   {
      // Add grid level
      double gridLot = gridBaseLot * (1.0 + gridLevel * 0.5);
      ENUM_ORDER_TYPE orderType = (positionType == POSITION_TYPE_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      
      Print("GRID: Adding level ", gridLevel + 1, " at distance ", DoubleToString(distance, 1), " pips");
      
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = NormalizeDouble(gridLot, 2);
      request.type = orderType;
      request.price = currentPrice;
      request.deviation = 30;
      request.magic = MagicNumber;
      request.comment = "QSB_GRID_" + IntegerToString(gridLevel + 1);
      request.type_filling = GetAllowedFillingMode();
      
      if(OrderSend(request, result))
      {
         if(result.retcode == TRADE_RETCODE_DONE)
         {
            gridLevel++;
            Print("Grid level ", gridLevel, " added successfully");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check if we have an open position                                |
//+------------------------------------------------------------------+
bool HasOpenPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0)
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && 
            PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            return true;
         }
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Select our position                                              |
//+------------------------------------------------------------------+
bool SelectOurPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0)
      {
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && 
            PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            return true;
         }
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Update daily PnL and track wins/losses                           |
//+------------------------------------------------------------------+
void UpdateDailyPnL()
{
   double todayProfit = 0.0;
   int todayTrades = 0;
   datetime todayStart = iTime(_Symbol, PERIOD_D1, 0);
   
   HistorySelect(todayStart, TimeCurrent());
   int totalDeals = HistoryDealsTotal();
   
   static int lastDealCount = 0;
   
   for(int i = 0; i < totalDeals; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == MagicNumber)
      {
         if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN)
         {
            todayTrades++;
         }
         
         double dealProfit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
         todayProfit += dealProfit;
         
         // Track consecutive wins/losses (only for closed trades)
         if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT && i >= lastDealCount)
         {
            if(dealProfit > 0)
            {
               consecutiveWins++;
               consecutiveLosses = 0;
            }
            else if(dealProfit < 0)
            {
               consecutiveLosses++;
               consecutiveWins = 0;
            }
         }
      }
   }
   
   lastDealCount = totalDeals;
   dailyPnL = todayProfit;
   dailyTradeCount = todayTrades;
   
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
   
${config.sessions.length === 0 ? '   return true; // No session filter' : generateSessionCheck()}
}

//+------------------------------------------------------------------+
//| Manage trailing stop                                             |
//+------------------------------------------------------------------+
void ManageTrailingStop()
{
   if(!SelectOurPosition())
      return;
   
   ulong positionTicket = PositionGetInteger(POSITION_TICKET);
   double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL = PositionGetDouble(POSITION_SL);
   long positionType = PositionGetInteger(POSITION_TYPE);
   
   double currentPrice = (positionType == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   double pipValue = _Point * pipMultiplier;
   double profitPips = 0.0;
   if(positionType == POSITION_TYPE_BUY)
      profitPips = (currentPrice - positionOpenPrice) / pipValue;
   else
      profitPips = (positionOpenPrice - currentPrice) / pipValue;
   
   if(profitPips < TrailingStopActivation)
      return;
   
   double trailDistance = TrailingStopDistance * pipValue;
   double newSL = 0.0;
   bool shouldModify = false;
   
   if(positionType == POSITION_TYPE_BUY)
   {
      newSL = currentPrice - trailDistance;
      if(currentSL == 0.0 || newSL > currentSL + _Point)
         shouldModify = true;
   }
   else
   {
      newSL = currentPrice + trailDistance;
      if(currentSL == 0.0 || newSL < currentSL - _Point)
         shouldModify = true;
   }
   
   if(shouldModify)
   {
      newSL = NormalizeDouble(newSL, _Digits);
      
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_SLTP;
      request.position = positionTicket;
      request.symbol = _Symbol;
      request.sl = newSL;
      request.tp = PositionGetDouble(POSITION_TP);
      
      if(OrderSend(request, result))
      {
         if(result.retcode == TRADE_RETCODE_DONE)
         {
            Print("Trailing stop updated: SL = ", newSL, " | Profit = ", DoubleToString(profitPips, 1), " pips");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage breakeven                                                 |
//+------------------------------------------------------------------+
void ManageBreakeven()
{
   if(!SelectOurPosition())
      return;
   
   ulong positionTicket = PositionGetInteger(POSITION_TICKET);
   double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL = PositionGetDouble(POSITION_SL);
   long positionType = PositionGetInteger(POSITION_TYPE);
   
   double currentPrice = (positionType == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   double pipValue = _Point * pipMultiplier;
   double profitPips = 0.0;
   if(positionType == POSITION_TYPE_BUY)
      profitPips = (currentPrice - positionOpenPrice) / pipValue;
   else
      profitPips = (positionOpenPrice - currentPrice) / pipValue;
   
   if(profitPips < BreakevenActivation)
      return;
   
   double bufferDistance = BreakevenBuffer * pipValue;
   double breakevenSL = 0.0;
   bool shouldModify = false;
   
   if(positionType == POSITION_TYPE_BUY)
   {
      breakevenSL = positionOpenPrice + bufferDistance;
      if(currentSL < breakevenSL - _Point)
         shouldModify = true;
   }
   else
   {
      breakevenSL = positionOpenPrice - bufferDistance;
      if(currentSL == 0.0 || currentSL > breakevenSL + _Point)
         shouldModify = true;
   }
   
   if(shouldModify)
   {
      breakevenSL = NormalizeDouble(breakevenSL, _Digits);
      
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_SLTP;
      request.position = positionTicket;
      request.symbol = _Symbol;
      request.sl = breakevenSL;
      request.tp = PositionGetDouble(POSITION_TP);
      
      if(OrderSend(request, result))
      {
         if(result.retcode == TRADE_RETCODE_DONE)
         {
            breakevenApplied = true;
             Print("*** BREAKEVEN APPLIED *** SL = ", breakevenSL);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage partial profit taking                                     |
//+------------------------------------------------------------------+
void ManagePartialTP()
{
   if(!SelectOurPosition())
      return;
   
   ulong positionTicket = PositionGetInteger(POSITION_TICKET);
   double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentVolume = PositionGetDouble(POSITION_VOLUME);
   long positionType = PositionGetInteger(POSITION_TYPE);
   
   double currentPrice = (positionType == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   double pipValue = _Point * pipMultiplier;
   double profitPips = 0.0;
   
   if(positionType == POSITION_TYPE_BUY)
      profitPips = (currentPrice - positionOpenPrice) / pipValue;
   else
      profitPips = (positionOpenPrice - currentPrice) / pipValue;
   
   // Check if reached partial TP level
   if(profitPips < PartialTPPips)
      return;
   
   // Calculate volume to close (percentage of original or current)
   double volumeToClose = currentVolume * (PartialTPPercent / 100.0);
   
   // Normalize volume
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   volumeToClose = MathFloor(volumeToClose / lotStep) * lotStep;
   volumeToClose = MathMax(minLot, volumeToClose);
   
   // Ensure we don't close more than current volume
   if(volumeToClose >= currentVolume)
   {
      Print("Partial TP: Volume to close >= current volume, skipping partial close");
      partialTPTaken = true;
      return;
   }
   
   // Partial close order
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = volumeToClose;
   request.type = (positionType == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = currentPrice;
   request.deviation = 30;
   request.position = positionTicket;
   request.magic = MagicNumber;
   request.comment = "QSB_PARTIAL_TP";
   request.type_filling = GetAllowedFillingMode();
   
   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         partialTPTaken = true;
         Print("*** PARTIAL TP TAKEN *** Closed: ", volumeToClose, " lots at ", DoubleToString(profitPips, 1), " pips profit");
         Print("Remaining position: ", currentVolume - volumeToClose, " lots");
         
         // Move to breakeven after partial close if enabled
         if(MoveToBreakevenAfterPartial)
         {
            double bufferDistance = BreakevenBuffer * pipValue;
            double breakevenSL = 0.0;
            
            if(positionType == POSITION_TYPE_BUY)
               breakevenSL = positionOpenPrice + bufferDistance;
            else
               breakevenSL = positionOpenPrice - bufferDistance;
            
            breakevenSL = NormalizeDouble(breakevenSL, _Digits);
            
            MqlTradeRequest slRequest = {};
            MqlTradeResult slResult = {};
            
            slRequest.action = TRADE_ACTION_SLTP;
            slRequest.position = positionTicket;
            slRequest.symbol = _Symbol;
            slRequest.sl = breakevenSL;
            slRequest.tp = 0.0; // Remove TP, let trailing stop handle it
            
            if(OrderSend(slRequest, slResult))
            {
               if(slResult.retcode == TRADE_RETCODE_DONE)
               {
                  breakevenApplied = true;
                  Print("*** SL moved to breakeven after partial TP *** SL = ", breakevenSL);
               }
            }
         }
      }
      else
      {
         Print("Partial TP failed. Error: ", result.retcode, " - ", GetRetcodeDescription(result.retcode));
      }
   }
   else
   {
      Print("Partial TP OrderSend failed. Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Get allowed filling mode                                         |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetAllowedFillingMode()
{
   uint filling = (uint)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   
   return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
//| Get retcode description                                          |
//+------------------------------------------------------------------+
string GetRetcodeDescription(uint retcode)
{
   switch(retcode)
   {
      case TRADE_RETCODE_REQUOTE: return "Requote";
      case TRADE_RETCODE_REJECT: return "Rejected";
      case TRADE_RETCODE_CANCEL: return "Canceled";
      case TRADE_RETCODE_PLACED: return "Placed";
      case TRADE_RETCODE_DONE: return "Done";
      case TRADE_RETCODE_DONE_PARTIAL: return "Done partial";
      case TRADE_RETCODE_ERROR: return "Error";
      case TRADE_RETCODE_TIMEOUT: return "Timeout";
      case TRADE_RETCODE_INVALID: return "Invalid request";
      case TRADE_RETCODE_INVALID_VOLUME: return "Invalid volume";
      case TRADE_RETCODE_INVALID_PRICE: return "Invalid price";
      case TRADE_RETCODE_INVALID_STOPS: return "Invalid stops";
      case TRADE_RETCODE_TRADE_DISABLED: return "Trade disabled";
      case TRADE_RETCODE_MARKET_CLOSED: return "Market closed";
      case TRADE_RETCODE_NO_MONEY: return "No money";
      case TRADE_RETCODE_PRICE_CHANGED: return "Price changed";
      case TRADE_RETCODE_PRICE_OFF: return "Price off";
      default: return "Unknown error";
   }
}

//+------------------------------------------------------------------+
//| Draw advanced dashboard                                          |
//+------------------------------------------------------------------+
void DrawDashboard()
{
   string prefix = "Dashboard_";
   int xOffset = 20;
   int yOffset = 30;
   int lineHeight = 18;
   color textColor = clrWhite;
   int fontSize = 8;
   
   // Statistics
   double distanceToTarget = DailyTarget - dailyPnL;
   double distanceToMaxLoss = MaxDailyLoss + dailyPnL;
   string trailingStatus = "OFF";
   string breakevenStatus = "OFF";
   string newsStatus = UseNewsFilter ? (isNewsTime ? "BLOCKED" : "CLEAR") : "DISABLED";
   string htfStatus = UseMTF ? (htfTrend == 1 ? "BULL" : htfTrend == -1 ? "BEAR" : "NEUTRAL") : "OFF";
   string mmStatus = EnumToString(MoneyManagement);
   double currentProfitPips = 0.0;
   
   if(SelectOurPosition())
   {
      double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                            SymbolInfoDouble(_Symbol, SYMBOL_BID) : 
                            SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double positionOpenPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double pipValue = _Point * pipMultiplier;
      
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
         currentProfitPips = (currentPrice - positionOpenPrice) / pipValue;
      else
         currentProfitPips = (positionOpenPrice - currentPrice) / pipValue;
      
      if(UseBreakeven)
         breakevenStatus = breakevenApplied ? "LOCKED" : DoubleToString(BreakevenActivation - currentProfitPips, 0) + " pips";
      
      if(UseTrailingStop)
         trailingStatus = (currentProfitPips >= TrailingStopActivation) ? "ACTIVE" : DoubleToString(TrailingStopActivation - currentProfitPips, 0) + " pips";
   }
   
   // Background
   string bgName = prefix + "BG";
   if(ObjectFind(0, bgName) < 0)
   {
      ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, bgName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, xOffset - 10);
      ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, yOffset - 10);
      ObjectSetInteger(0, bgName, OBJPROP_XSIZE, 260);
      ObjectSetInteger(0, bgName, OBJPROP_YSIZE, 250);
      ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, C'15,15,25');
      ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, bgName, OBJPROP_COLOR, clrDodgerBlue);
      ObjectSetInteger(0, bgName, OBJPROP_WIDTH, 1);
   }
   
   int line = 0;
   
   // Title
   CreateLabel(prefix + "Title", xOffset, yOffset + lineHeight * line++, "═══ ADVANCED EA v2.0 ═══", clrDodgerBlue, fontSize + 1);
   
   // Daily PnL
   color plColor = (dailyPnL >= 0) ? clrLime : clrRed;
   string plSign = (dailyPnL >= 0) ? "+" : "";
   CreateLabel(prefix + "PL", xOffset, yOffset + lineHeight * line++, "P&L: " + plSign + "$" + DoubleToString(MathAbs(dailyPnL), 2), plColor, fontSize);
   
   // Trades
   CreateLabel(prefix + "Trades", xOffset, yOffset + lineHeight * line++, "Trades: " + IntegerToString(dailyTradeCount) + "/" + IntegerToString(MaxDailyTrades), textColor, fontSize);
   
   // Target/Loss
   CreateLabel(prefix + "Target", xOffset, yOffset + lineHeight * line++, "To Target: $" + DoubleToString(distanceToTarget, 2), clrYellow, fontSize);
   CreateLabel(prefix + "MaxLoss", xOffset, yOffset + lineHeight * line++, "To Max Loss: $" + DoubleToString(distanceToMaxLoss, 2), clrOrange, fontSize);
   
   // Advanced features
   line++;
   CreateLabel(prefix + "Sep1", xOffset, yOffset + lineHeight * line++, "─── ADVANCED FEATURES ───", clrGray, fontSize);
   
   color htfColor = (htfTrend == 1) ? clrLime : (htfTrend == -1) ? clrRed : clrYellow;
   CreateLabel(prefix + "HTF", xOffset, yOffset + lineHeight * line++, "HTF Trend: " + htfStatus, htfColor, fontSize);
   
   color newsColor = (isNewsTime) ? clrRed : clrLime;
   CreateLabel(prefix + "News", xOffset, yOffset + lineHeight * line++, "News: " + newsStatus, newsColor, fontSize);
   
   CreateLabel(prefix + "MM", xOffset, yOffset + lineHeight * line++, "MM: " + mmStatus + " (W:" + IntegerToString(consecutiveWins) + "/L:" + IntegerToString(consecutiveLosses) + ")", clrAqua, fontSize);
   
   // Protection
   line++;
   CreateLabel(prefix + "Sep2", xOffset, yOffset + lineHeight * line++, "─── PROTECTION ───", clrGray, fontSize);
   
   color beColor = (breakevenStatus == "LOCKED") ? clrLime : clrYellow;
   CreateLabel(prefix + "BE", xOffset, yOffset + lineHeight * line++, "Breakeven: " + breakevenStatus, beColor, fontSize);
   
   color tsColor = (trailingStatus == "ACTIVE") ? clrLime : clrYellow;
   CreateLabel(prefix + "Trail", xOffset, yOffset + lineHeight * line++, "Trailing: " + trailingStatus, tsColor, fontSize);
   
   // Partial TP status
   string partialStatus = UsePartialTP ? (partialTPTaken ? "TAKEN" : "WAITING") : "OFF";
   color partialColor = partialTPTaken ? clrLime : (UsePartialTP ? clrYellow : clrGray);
   CreateLabel(prefix + "Partial", xOffset, yOffset + lineHeight * line++, "Partial TP: " + partialStatus, partialColor, fontSize);
   
   // Position
   if(SelectOurPosition())
   {
      color profitColor = (currentProfitPips >= 0) ? clrLime : clrRed;
      string profitSign = (currentProfitPips >= 0) ? "+" : "";
      CreateLabel(prefix + "Pos", xOffset, yOffset + lineHeight * line++, "Position: " + profitSign + DoubleToString(currentProfitPips, 1) + " pips", profitColor, fontSize);
   }
   else
   {
      CreateLabel(prefix + "Pos", xOffset, yOffset + lineHeight * line++, "Position: None", clrGray, fontSize);
   }
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Create label helper                                              |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int size)
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
   ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
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
        <h3 className="text-xl font-semibold">Export Advanced Strategy Code</h3>
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
                  onClick={() => downloadCode(generateMQL5(), `${config.instruments[0] || "Strategy"}_${config.timeframe}_AdvancedEA.mq5`)}
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
                advanced strategy logic.
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </Card>

      <Card className="p-6 bg-primary/5 border-primary/20">
        <h4 className="font-semibold mb-3 text-primary">Advanced EA Features</h4>
        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
          <div>
            <h5 className="font-medium text-foreground mb-2">Entry Types</h5>
            <ul className="space-y-1">
              <li>• Scalping (BB bounce, EMA pullback)</li>
              <li>• Breakout (structure breaks)</li>
              <li>• Reversal (RSI extremes, engulfing)</li>
            </ul>
          </div>
          <div>
            <h5 className="font-medium text-foreground mb-2">Money Management</h5>
            <ul className="space-y-1">
              <li>• Fixed lot sizing</li>
              <li>• Martingale (double after loss)</li>
              <li>• Anti-Martingale (scale up wins)</li>
              <li>• Recovery mode</li>
            </ul>
          </div>
          <div>
            <h5 className="font-medium text-foreground mb-2">Filters</h5>
            <ul className="space-y-1">
              <li>• Multi-timeframe trend alignment</li>
              <li>• News event filter (NFP, FOMC)</li>
              <li>• Session time restrictions</li>
            </ul>
          </div>
          <div>
            <h5 className="font-medium text-foreground mb-2">Protection</h5>
            <ul className="space-y-1">
              <li>• Breakeven protection</li>
              <li>• Trailing stop</li>
              <li>• Daily loss limit</li>
              <li>• Grid trading option</li>
            </ul>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-secondary/30 border-border">
        <h4 className="font-semibold mb-3">Installation Instructions (MT5)</h4>
        <ol className="space-y-2 text-sm text-muted-foreground">
          <li>1. Download the generated MQL5 code</li>
          <li>2. Open MetaEditor (press F4 in MT5)</li>
          <li>3. File → New → Expert Advisor</li>
          <li>4. Paste the code and save as "AdvancedEA.mq5"</li>
          <li>5. Click Compile (F7) - ensure no errors</li>
          <li>6. Drag the EA onto your chart</li>
          <li>7. Configure inputs in the Properties dialog</li>
          <li>8. Enable AutoTrading</li>
        </ol>
      </Card>
    </div>
  );
};
