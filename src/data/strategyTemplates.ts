import { StrategyConfig } from "@/types/strategy";

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: "Trend Following" | "Mean Reversion" | "Breakout" | "Scalping";
  recommendedPairs: string;
  config: StrategyConfig;
}

export const strategyTemplates: StrategyTemplate[] = [
  {
    id: "triple-ema-trend",
    name: "Triple EMA Trend Filter",
    description: "High-probability trend-following with triple EMA alignment. Only enters when all 3 EMAs stack in order, confirming strong trend momentum.",
    category: "Trend Following",
    recommendedPairs: "EURUSD, GBPUSD, USDJPY (Forex majors)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "USDJPY"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 100,
      sessions: ["london", "newyork", "overlap"],
      indicators: [
        {
          id: "ema_8",
          name: "EMA 8",
          type: "EMA",
          params: { period: 8 },
          condition: "Fast trend"
        },
        {
          id: "ema_21",
          name: "EMA 21",
          type: "EMA",
          params: { period: 21 },
          condition: "Medium trend"
        },
        {
          id: "ema_55",
          name: "EMA 55",
          type: "EMA",
          params: { period: 55 },
          condition: "Slow trend"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum filter (40-60 neutral zone avoided)"
        }
      ],
      entries: [
        {
          id: "bullish_stack",
          description: "Buy only when EMA8 > EMA21 > EMA55 AND RSI confirms momentum",
          logic: "EMA8 > EMA21 && EMA21 > EMA55 && Close > EMA8 && RSI > 55 && RSI < 75"
        },
        {
          id: "bearish_stack",
          description: "Sell only when EMA8 < EMA21 < EMA55 AND RSI confirms weakness",
          logic: "EMA8 < EMA21 && EMA21 < EMA55 && Close < EMA8 && RSI < 45 && RSI > 25"
        }
      ],
      exits: [
        {
          id: "ema_break",
          description: "Exit when price closes beyond EMA21 against position",
          logic: "Price closes on wrong side of EMA21"
        }
      ],
      stopLoss: { type: "fixed", pips: 18 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 15,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "rsi-extreme-reversal",
    name: "RSI Extreme Reversal",
    description: "Mean reversion at extreme RSI levels (< 25 or > 75). Waits for RSI to exit extreme zone before entry, confirming reversal.",
    category: "Mean Reversion",
    recommendedPairs: "EURUSD, GBPUSD, AUDUSD (Forex ranges)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "AUDUSD"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 100,
      sessions: ["london", "overlap"],
      indicators: [
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Extreme levels (< 25 oversold, > 75 overbought)"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend context filter"
        },
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Price extreme confirmation"
        }
      ],
      entries: [
        {
          id: "long_extreme",
          description: "Buy when RSI exits oversold (was < 25, now crosses above 30) at lower BB",
          logic: "RSI > 30 && RSI[1] <= 30 && RSI[2] < 25 && Close <= LowerBand"
        },
        {
          id: "short_extreme",
          description: "Sell when RSI exits overbought (was > 75, now crosses below 70) at upper BB",
          logic: "RSI < 70 && RSI[1] >= 70 && RSI[2] > 75 && Close >= UpperBand"
        }
      ],
      exits: [
        {
          id: "midline_exit",
          description: "Exit at RSI 50 midline or middle BB",
          logic: "RSI crosses 50 or price reaches middle BB"
        }
      ],
      stopLoss: { type: "fixed", pips: 15 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 12,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "london-killzone",
    name: "London Killzone Breakout",
    description: "Trades London session open (7-10 AM GMT) breakouts only. High probability due to institutional order flow.",
    category: "Breakout",
    recommendedPairs: "EURUSD, GBPUSD, EURGBP (EUR/GBP pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "EURGBP"],
      timeframe: "15m",
      accountSize: 100,
      dailyTarget: 80,
      sessions: ["london"],
      indicators: [
        {
          id: "ema_20",
          name: "EMA 20",
          type: "EMA",
          params: { period: 20 },
          condition: "Short-term trend"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Medium trend bias"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility expansion confirmation"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum confirmation"
        }
      ],
      entries: [
        {
          id: "london_long",
          description: "Buy when both EMAs aligned bullish with RSI momentum above 55",
          logic: "EMA20 > EMA50 && Close > EMA20 && RSI > 55 && RSI < 72"
        },
        {
          id: "london_short",
          description: "Sell when both EMAs aligned bearish with RSI momentum below 45",
          logic: "EMA20 < EMA50 && Close < EMA20 && RSI < 45 && RSI > 28"
        }
      ],
      exits: [
        {
          id: "session_end",
          description: "Exit before US session overlap or at 2:1 target",
          logic: "Fixed RR target or 11 AM GMT"
        }
      ],
      stopLoss: { type: "fixed", pips: 20 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 15,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "macd-zero-cross",
    name: "MACD Zero Line Cross",
    description: "Trades MACD crossing zero line (not just signal line). Stronger trend confirmation with fewer false signals.",
    category: "Trend Following",
    recommendedPairs: "NAS100, US30, EURUSD (Indices & Forex)",
    config: {
      instruments: ["NAS100", "US30", "EURUSD"],
      timeframe: "15m",
      accountSize: 100,
      dailyTarget: 120,
      sessions: ["newyork", "overlap"],
      indicators: [
        {
          id: "macd",
          name: "MACD",
          type: "MACD",
          params: { fast: 12, slow: 26, signal: 9 },
          condition: "Zero line crossover"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend alignment filter"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Not overbought/oversold"
        }
      ],
      entries: [
        {
          id: "zero_cross_long",
          description: "Buy when MACD crosses above zero with EMA and RSI confirmation",
          logic: "MACD > 0 && MACD[1] <= 0 && Close > EMA50 && RSI > 45 && RSI < 70"
        },
        {
          id: "zero_cross_short",
          description: "Sell when MACD crosses below zero with EMA and RSI confirmation",
          logic: "MACD < 0 && MACD[1] >= 0 && Close < EMA50 && RSI < 55 && RSI > 30"
        }
      ],
      exits: [
        {
          id: "macd_reversal",
          description: "Exit when MACD crosses zero in opposite direction",
          logic: "MACD zero line cross against position"
        }
      ],
      stopLoss: { type: "fixed", pips: 25 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 20,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "volatility-75-scalper",
    name: "Volatility 75 Pro Scalper",
    description: "High-probability V75 strategy with triple confirmation: EMA stack + RSI momentum + ATR volatility filter. Only trades during optimal volatility conditions.",
    category: "Scalping",
    recommendedPairs: "Volatility 75 Index (Synthetics only)",
    config: {
      instruments: ["VOL75"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 100,
      sessions: ["london", "newyork", "overlap", "asian"],
      indicators: [
        {
          id: "ema_8",
          name: "EMA 8",
          type: "EMA",
          params: { period: 8 },
          condition: "Fast trend - must align with EMA21"
        },
        {
          id: "ema_21",
          name: "EMA 21",
          type: "EMA",
          params: { period: 21 },
          condition: "Medium trend confirmation"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Slow trend filter - overall bias"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum filter (55-70 for longs, 30-45 for shorts)"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility filter - skip low volatility periods"
        },
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Price extreme detection - avoid chasing"
        }
      ],
      entries: [
        {
          id: "v75_long",
          description: "Buy ONLY when: Triple EMA bullish stack (8>21>50) + RSI 55-68 + Price NOT at upper BB + Pullback to EMA8",
          logic: "EMA8 > EMA21 && EMA21 > EMA50 && Close > EMA8 && Low <= EMA8 && RSI > 55 && RSI < 68 && Close < UpperBand"
        },
        {
          id: "v75_short",
          description: "Sell ONLY when: Triple EMA bearish stack (8<21<50) + RSI 32-45 + Price NOT at lower BB + Pullback to EMA8",
          logic: "EMA8 < EMA21 && EMA21 < EMA50 && Close < EMA8 && High >= EMA8 && RSI > 32 && RSI < 45 && Close > LowerBand"
        }
      ],
      exits: [
        {
          id: "trailing_exit",
          description: "Trailing stop protects profits after 80 pips, breakeven at 50 pips",
          logic: "Breakeven at 50 pips, trail at 40 pips distance after 80 pips profit"
        }
      ],
      stopLoss: { type: "fixed", pips: 80 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 15,
      positionSizePercent: 0.5,
    }
  },
  {
    id: "nasdaq-momentum",
    name: "NASDAQ NY Session Momentum",
    description: "Trades NASDAQ during US session only with strict EMA and RSI alignment. Avoids choppy pre-market.",
    category: "Trend Following",
    recommendedPairs: "NAS100, US30, SPX500 (Stock Indices)",
    config: {
      instruments: ["NAS100", "US30", "SPX500"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["newyork"],
      indicators: [
        {
          id: "ema_9",
          name: "EMA 9",
          type: "EMA",
          params: { period: 9 },
          condition: "Fast trend"
        },
        {
          id: "ema_21",
          name: "EMA 21",
          type: "EMA",
          params: { period: 21 },
          condition: "Medium trend"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Slow trend filter"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum confirmation"
        }
      ],
      entries: [
        {
          id: "nas_long",
          description: "Buy when all 3 EMAs aligned bullish with RSI > 55",
          logic: "EMA9 > EMA21 && EMA21 > EMA50 && Close > EMA9 && RSI > 55 && RSI < 72"
        },
        {
          id: "nas_short",
          description: "Sell when all 3 EMAs aligned bearish with RSI < 45",
          logic: "EMA9 < EMA21 && EMA21 < EMA50 && Close < EMA9 && RSI < 45 && RSI > 28"
        }
      ],
      exits: [
        {
          id: "ema_reversal",
          description: "Exit on EMA9 cross against position",
          logic: "EMA9 crosses EMA21 against position"
        }
      ],
      stopLoss: { type: "fixed", pips: 35 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 25,
      positionSizePercent: 1,
    }
  }
];
