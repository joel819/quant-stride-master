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
    id: "ema-crossover",
    name: "EMA Crossover",
    description: "Fast EMA crosses above/below slow EMA for trend entries. Classic trend-following strategy with high win rate in trending markets.",
    category: "Trend Following",
    recommendedPairs: "EURUSD, GBPUSD, USDJPY (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "USDJPY"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "newyork", "overlap"],
      indicators: [
        {
          id: "ema_fast",
          name: "EMA Fast",
          type: "EMA",
          params: { period: 9 },
          condition: "Fast EMA crosses Slow EMA"
        },
        {
          id: "ema_slow",
          name: "EMA Slow",
          type: "EMA",
          params: { period: 21 },
          condition: "Trend confirmation"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Dynamic stop loss"
        }
      ],
      entries: [
        {
          id: "long_entry",
          description: "Buy when fast EMA crosses above slow EMA",
          logic: "EMA9 > EMA21 && EMA9[1] <= EMA21[1]"
        },
        {
          id: "short_entry",
          description: "Sell when fast EMA crosses below slow EMA",
          logic: "EMA9 < EMA21 && EMA9[1] >= EMA21[1]"
        }
      ],
      exits: [
        {
          id: "exit_opposite",
          description: "Exit on opposite crossover",
          logic: "Opposite EMA crossover signal"
        }
      ],
      stopLoss: { type: "fixed", pips: 15 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "rsi-mean-reversion",
    name: "RSI Mean Reversion",
    description: "Buy oversold conditions (RSI < 30), sell overbought (RSI > 70). Works best in ranging markets with clear support/resistance.",
    category: "Mean Reversion",
    recommendedPairs: "EURUSD, GBPUSD, AUDUSD (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "AUDUSD"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "overlap"],
      indicators: [
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Oversold/Overbought levels"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend filter"
        }
      ],
      entries: [
        {
          id: "long_oversold",
          description: "Buy when RSI crosses above 30 (oversold bounce)",
          logic: "RSI > 30 && RSI[1] <= 30"
        },
        {
          id: "short_overbought",
          description: "Sell when RSI crosses below 70 (overbought rejection)",
          logic: "RSI < 70 && RSI[1] >= 70"
        }
      ],
      exits: [
        {
          id: "exit_midline",
          description: "Exit when RSI returns to 50 midline",
          logic: "RSI crosses 50 level"
        }
      ],
      stopLoss: { type: "fixed", pips: 12 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "bollinger-squeeze",
    name: "Bollinger Band Squeeze",
    description: "Breakout strategy that trades when volatility contracts and then expands. High probability trades after consolidation periods.",
    category: "Breakout",
    recommendedPairs: "NAS100, EURUSD, GBPUSD (Forex & Indices)",
    config: {
      instruments: ["NAS100", "EURUSD", "GBPUSD"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["newyork", "overlap"],
      indicators: [
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Volatility squeeze and breakout"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility filter"
        }
      ],
      entries: [
        {
          id: "long_breakout",
          description: "Buy when price breaks above upper band",
          logic: "Close > UpperBand && Close[1] <= UpperBand[1]"
        },
        {
          id: "short_breakout",
          description: "Sell when price breaks below lower band",
          logic: "Close < LowerBand && Close[1] >= LowerBand[1]"
        }
      ],
      exits: [
        {
          id: "exit_opposite_band",
          description: "Exit at middle or opposite Bollinger Band",
          logic: "Price reaches middle band"
        }
      ],
      stopLoss: { type: "fixed", pips: 20 },
      takeProfit: { type: "rr", ratio: 3 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "macd-momentum",
    name: "MACD Momentum",
    description: "Trade MACD signal line crossovers with histogram confirmation. Clean momentum signals for trend entries.",
    category: "Trend Following",
    recommendedPairs: "EURUSD, USDJPY, GBPUSD (Forex pairs)",
    config: {
      instruments: ["EURUSD", "USDJPY", "GBPUSD"],
      timeframe: "15m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "newyork"],
      indicators: [
        {
          id: "macd",
          name: "MACD",
          type: "MACD",
          params: { fast: 12, slow: 26, signal: 9 },
          condition: "Signal crossover"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend filter"
        }
      ],
      entries: [
        {
          id: "bullish_cross",
          description: "Buy when MACD crosses above signal line",
          logic: "MACD > Signal && MACD[1] <= Signal[1]"
        },
        {
          id: "bearish_cross",
          description: "Sell when MACD crosses below signal line",
          logic: "MACD < Signal && MACD[1] >= Signal[1]"
        }
      ],
      exits: [
        {
          id: "macd_cross",
          description: "Exit when MACD crosses signal line in opposite direction",
          logic: "MACD crosses signal line"
        }
      ],
      stopLoss: { type: "fixed", pips: 20 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "scalping-ema-rsi",
    name: "1-Minute Scalper",
    description: "Fast-paced scalping combining EMA trend and RSI momentum. Targets quick 5-10 pip moves in high-liquidity sessions.",
    category: "Scalping",
    recommendedPairs: "EURUSD, GBPUSD, USDJPY (Forex only)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "USDJPY"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["overlap"],
      indicators: [
        {
          id: "ema_20",
          name: "EMA 20",
          type: "EMA",
          params: { period: 20 },
          condition: "Trend direction"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 7 },
          condition: "Momentum confirmation"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility-based SL"
        }
      ],
      entries: [
        {
          id: "long_scalp",
          description: "Buy when price above EMA and RSI bullish",
          logic: "Close > EMA20 && RSI > 50 && RSI < 70"
        },
        {
          id: "short_scalp",
          description: "Sell when price below EMA and RSI bearish",
          logic: "Close < EMA20 && RSI < 50 && RSI > 30"
        }
      ],
      exits: [
        {
          id: "quick_profit",
          description: "Quick profit target at 10 pips or opposite signal",
          logic: "Target reached or opposite EMA cross"
        }
      ],
      stopLoss: { type: "fixed", pips: 8 },
      takeProfit: { type: "fixed", pips: 15 },
      maxDailyLoss: 15,
      positionSizePercent: 2,
    }
  },
  {
    id: "volatility-breakout",
    name: "Volatility Index Breakout",
    description: "Specialized for synthetic volatility indices. Trades spike patterns and volatility breakouts with tight risk management.",
    category: "Breakout",
    recommendedPairs: "Volatility 75, Volatility 100, Volatility 50 (Synthetics only)",
    config: {
      instruments: ["VOL75", "VOL100", "VOL50"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["london", "newyork", "overlap", "asian"],
      indicators: [
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Volatility spikes"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend bias"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum filter"
        }
      ],
      entries: [
        {
          id: "spike_long",
          description: "Buy when price bounces from lower BB with bullish RSI",
          logic: "Close <= LowerBand && RSI < 40 && RSI > 20"
        },
        {
          id: "spike_short",
          description: "Sell when price bounces from upper BB with bearish RSI",
          logic: "Close >= UpperBand && RSI > 60 && RSI < 80"
        }
      ],
      exits: [
        {
          id: "mean_reversion",
          description: "Exit at middle BB or opposite spike",
          logic: "Price returns to BB middle"
        }
      ],
      stopLoss: { type: "fixed", pips: 50 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "stochastic-reversal",
    name: "Stochastic Reversal",
    description: "Captures trend reversals using Stochastic oscillator crossovers in oversold/overbought zones. High win rate in ranging conditions.",
    category: "Mean Reversion",
    recommendedPairs: "EURUSD, GBPUSD, AUDUSD (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "AUDUSD"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "newyork"],
      indicators: [
        {
          id: "stoch",
          name: "Stochastic",
          type: "Stochastic",
          params: { kPeriod: 14, dPeriod: 3, slowing: 3 },
          condition: "K/D crossover in extreme zones"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend filter"
        }
      ],
      entries: [
        {
          id: "long_stoch",
          description: "Buy when %K crosses above %D below 30",
          logic: "StochK > StochD && StochK[1] <= StochD[1] && StochK < 35"
        },
        {
          id: "short_stoch",
          description: "Sell when %K crosses below %D above 70",
          logic: "StochK < StochD && StochK[1] >= StochD[1] && StochK > 65"
        }
      ],
      exits: [
        {
          id: "opposite_zone",
          description: "Exit when Stochastic reaches opposite extreme",
          logic: "Stochastic reaches opposite zone"
        }
      ],
      stopLoss: { type: "fixed", pips: 15 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "nasdaq-momentum",
    name: "NASDAQ Momentum",
    description: "Trend-following strategy optimized for US indices. Trades with momentum during high-volume US sessions.",
    category: "Trend Following",
    recommendedPairs: "NAS100, US30, SPX500 (Stock Indices only)",
    config: {
      instruments: ["NAS100", "US30", "SPX500"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 250,
      sessions: ["newyork", "overlap"],
      indicators: [
        {
          id: "ema_9",
          name: "EMA 9",
          type: "EMA",
          params: { period: 9 },
          condition: "Fast momentum"
        },
        {
          id: "ema_21",
          name: "EMA 21",
          type: "EMA",
          params: { period: 21 },
          condition: "Medium trend"
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
          id: "long_momentum",
          description: "Buy when EMAs aligned bullish with RSI momentum",
          logic: "EMA9 > EMA21 && RSI > 50 && RSI < 75"
        },
        {
          id: "short_momentum",
          description: "Sell when EMAs aligned bearish with RSI weakness",
          logic: "EMA9 < EMA21 && RSI < 50 && RSI > 25"
        }
      ],
      exits: [
        {
          id: "ema_reversal",
          description: "Exit on EMA crossover reversal",
          logic: "EMA crossover in opposite direction"
        }
      ],
      stopLoss: { type: "fixed", pips: 30 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 30,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "boom-crash-spike",
    name: "Boom & Crash Spike Catcher",
    description: "Specialized strategy for Boom/Crash indices. Catches spikes using Bollinger Band extremes and momentum confirmation.",
    category: "Scalping",
    recommendedPairs: "Boom 1000, Crash 1000, Boom 500, Crash 500 (Synthetics only)",
    config: {
      instruments: ["BOOM1000", "CRASH1000", "BOOM500", "CRASH500"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["london", "newyork", "overlap", "asian"],
      indicators: [
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2.5 },
          condition: "Spike detection"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 7 },
          condition: "Momentum filter"
        },
        {
          id: "ema_20",
          name: "EMA 20",
          type: "EMA",
          params: { period: 20 },
          condition: "Trend reference"
        }
      ],
      entries: [
        {
          id: "boom_entry",
          description: "Buy on Boom when RSI oversold at lower BB",
          logic: "Close <= LowerBand && RSI < 40"
        },
        {
          id: "crash_entry",
          description: "Sell on Crash when RSI overbought at upper BB",
          logic: "Close >= UpperBand && RSI > 60"
        }
      ],
      exits: [
        {
          id: "spike_exit",
          description: "Quick exit after spike captured",
          logic: "Fixed pip target or middle BB"
        }
      ],
      stopLoss: { type: "fixed", pips: 100 },
      takeProfit: { type: "fixed", pips: 150 },
      maxDailyLoss: 30,
      positionSizePercent: 1,
    }
  },
  {
    id: "london-breakout",
    name: "London Session Breakout",
    description: "Trades the breakout of Asian session range during London open. High probability due to increased liquidity.",
    category: "Breakout",
    recommendedPairs: "EURUSD, GBPUSD, EURGBP (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "EURGBP"],
      timeframe: "15m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london"],
      indicators: [
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Range calculation"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Bias filter"
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
          id: "breakout_long",
          description: "Buy when price breaks above EMA with momentum",
          logic: "Close > EMA50 && RSI > 55"
        },
        {
          id: "breakout_short",
          description: "Sell when price breaks below EMA with momentum",
          logic: "Close < EMA50 && RSI < 45"
        }
      ],
      exits: [
        {
          id: "session_end",
          description: "Exit before US session or at target",
          logic: "Fixed target or end of London session"
        }
      ],
      stopLoss: { type: "fixed", pips: 18 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "triple-ema-trend",
    name: "Triple EMA Trend",
    description: "Strong trend filter using three EMAs aligned in order. Only trades when all EMAs confirm direction.",
    category: "Trend Following",
    recommendedPairs: "EURUSD, GBPUSD, USDJPY, AUDUSD (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 150,
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
        }
      ],
      entries: [
        {
          id: "bullish_stack",
          description: "Buy when EMA8 > EMA21 > EMA55 (bullish stack)",
          logic: "EMA8 > EMA21 && EMA21 > EMA55 && Close > EMA8"
        },
        {
          id: "bearish_stack",
          description: "Sell when EMA8 < EMA21 < EMA55 (bearish stack)",
          logic: "EMA8 < EMA21 && EMA21 < EMA55 && Close < EMA8"
        }
      ],
      exits: [
        {
          id: "ema_break",
          description: "Exit when price closes beyond EMA21",
          logic: "Price closes on wrong side of EMA21"
        }
      ],
      stopLoss: { type: "fixed", pips: 15 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "rsi-bb-combo",
    name: "RSI + Bollinger Combo",
    description: "Multi-indicator confirmation strategy. Requires both RSI and BB signals to align before entry.",
    category: "Mean Reversion",
    recommendedPairs: "EURUSD, GBPUSD, AUDUSD (Forex pairs)",
    config: {
      instruments: ["EURUSD", "GBPUSD", "AUDUSD"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "newyork", "overlap"],
      indicators: [
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Oversold/Overbought"
        },
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Price extremes"
        }
      ],
      entries: [
        {
          id: "double_confirm_long",
          description: "Buy when RSI oversold AND price at lower BB",
          logic: "RSI < 35 && Close <= LowerBand"
        },
        {
          id: "double_confirm_short",
          description: "Sell when RSI overbought AND price at upper BB",
          logic: "RSI > 65 && Close >= UpperBand"
        }
      ],
      exits: [
        {
          id: "middle_reversion",
          description: "Exit at BB middle line or RSI 50",
          logic: "Price reaches middle BB or RSI crosses 50"
        }
      ],
      stopLoss: { type: "fixed", pips: 18 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "asian-range-breakout",
    name: "Asian Range Breakout",
    description: "Trades the breakout of the tight Asian session range. Best for JPY pairs with clear range definition.",
    category: "Breakout",
    recommendedPairs: "USDJPY, EURJPY, GBPJPY (JPY pairs)",
    config: {
      instruments: ["USDJPY", "EURJPY", "GBPJPY"],
      timeframe: "15m",
      accountSize: 100,
      dailyTarget: 150,
      sessions: ["london", "overlap"],
      indicators: [
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility measure"
        },
        {
          id: "ema_50",
          name: "EMA 50",
          type: "EMA",
          params: { period: 50 },
          condition: "Trend bias"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum"
        }
      ],
      entries: [
        {
          id: "range_break_long",
          description: "Buy when price breaks with bullish momentum",
          logic: "Close > EMA50 && RSI > 55 && RSI < 75"
        },
        {
          id: "range_break_short",
          description: "Sell when price breaks with bearish momentum",
          logic: "Close < EMA50 && RSI < 45 && RSI > 25"
        }
      ],
      exits: [
        {
          id: "range_target",
          description: "Target equal to Asian range size",
          logic: "Fixed target or reversal signal"
        }
      ],
      stopLoss: { type: "fixed", pips: 20 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "synthetic-scalper",
    name: "Synthetic Index Scalper",
    description: "Optimized for Deriv synthetic indices. Fast entries on volatility spikes with tight risk management.",
    category: "Scalping",
    recommendedPairs: "Volatility 75, Volatility 100, Volatility 50, Volatility 25 (Synthetics only)",
    config: {
      instruments: ["VOL75", "VOL100", "VOL50", "VOL25"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["london", "newyork", "overlap", "asian"],
      indicators: [
        {
          id: "ema_5",
          name: "EMA 5",
          type: "EMA",
          params: { period: 5 },
          condition: "Ultra-fast trend"
        },
        {
          id: "ema_13",
          name: "EMA 13",
          type: "EMA",
          params: { period: 13 },
          condition: "Quick trend"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 5 },
          condition: "Fast momentum"
        }
      ],
      entries: [
        {
          id: "quick_long",
          description: "Buy on EMA cross with RSI momentum",
          logic: "EMA5 > EMA13 && RSI > 45 && RSI < 75"
        },
        {
          id: "quick_short",
          description: "Sell on EMA cross with RSI momentum",
          logic: "EMA5 < EMA13 && RSI < 55 && RSI > 25"
        }
      ],
      exits: [
        {
          id: "quick_exit",
          description: "Fast exit on opposite cross or target",
          logic: "EMA cross or fixed pip target"
        }
      ],
      stopLoss: { type: "fixed", pips: 40 },
      takeProfit: { type: "fixed", pips: 60 },
      maxDailyLoss: 20,
      positionSizePercent: 2,
    }
  },
  {
    id: "index-momentum",
    name: "Index Momentum Rider",
    description: "Rides strong momentum moves on indices. Uses ATR for volatility-adjusted entries and exits.",
    category: "Trend Following",
    recommendedPairs: "NAS100, GER40, US30 (Stock Indices only)",
    config: {
      instruments: ["NAS100", "GER40", "US30"],
      timeframe: "5m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["london", "newyork", "overlap"],
      indicators: [
        {
          id: "ema_20",
          name: "EMA 20",
          type: "EMA",
          params: { period: 20 },
          condition: "Dynamic support/resistance"
        },
        {
          id: "atr",
          name: "ATR",
          type: "ATR",
          params: { period: 14 },
          condition: "Volatility filter"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Momentum strength"
        }
      ],
      entries: [
        {
          id: "momentum_long",
          description: "Buy on pullback with strong momentum",
          logic: "Close > EMA20 && RSI > 50 && RSI < 72"
        },
        {
          id: "momentum_short",
          description: "Sell on pullback with weak momentum",
          logic: "Close < EMA20 && RSI < 50 && RSI > 28"
        }
      ],
      exits: [
        {
          id: "atr_exit",
          description: "Exit at 2x ATR distance or momentum loss",
          logic: "2x ATR target or RSI divergence"
        }
      ],
      stopLoss: { type: "fixed", pips: 25 },
      takeProfit: { type: "rr", ratio: 2.5 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "jump-index-trader",
    name: "Jump Index Trader",
    description: "Specialized for Jump indices with sudden price movements. Uses quick entries after jump detection.",
    category: "Breakout",
    recommendedPairs: "Jump 10, Jump 25, Jump 50, Jump 75, Jump 100 (Synthetics only)",
    config: {
      instruments: ["JUMP10", "JUMP25", "JUMP50", "JUMP75", "JUMP100"],
      timeframe: "1m",
      accountSize: 100,
      dailyTarget: 200,
      sessions: ["london", "newyork", "overlap", "asian"],
      indicators: [
        {
          id: "bb",
          name: "Bollinger Bands",
          type: "BB",
          params: { period: 20, deviation: 2 },
          condition: "Jump detection"
        },
        {
          id: "ema_10",
          name: "EMA 10",
          type: "EMA",
          params: { period: 10 },
          condition: "Quick trend"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 7 },
          condition: "Momentum"
        }
      ],
      entries: [
        {
          id: "jump_long",
          description: "Buy when price above EMA with bullish momentum",
          logic: "Close > EMA10 && RSI > 45 && RSI < 72"
        },
        {
          id: "jump_short",
          description: "Sell when price below EMA with bearish momentum",
          logic: "Close < EMA10 && RSI < 55 && RSI > 28"
        }
      ],
      exits: [
        {
          id: "jump_exit",
          description: "Quick exit before next jump or at target",
          logic: "Fixed target or next jump detected"
        }
      ],
      stopLoss: { type: "fixed", pips: 80 },
      takeProfit: { type: "fixed", pips: 120 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  }
];
