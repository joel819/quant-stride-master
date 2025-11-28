import { StrategyConfig } from "@/types/strategy";

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: "Trend Following" | "Mean Reversion" | "Breakout" | "Scalping";
  config: StrategyConfig;
}

export const strategyTemplates: StrategyTemplate[] = [
  {
    id: "ema-crossover",
    name: "EMA Crossover",
    description: "Fast EMA crosses above/below slow EMA for trend entries. Classic trend-following strategy with high win rate in trending markets.",
    category: "Trend Following",
    config: {
      instruments: ["EURUSD", "GBPUSD"],
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
          logic: "FastEMA[0] > SlowEMA[0] && FastEMA[1] <= SlowEMA[1]"
        },
        {
          id: "short_entry",
          description: "Sell when fast EMA crosses below slow EMA",
          logic: "FastEMA[0] < SlowEMA[0] && FastEMA[1] >= SlowEMA[1]"
        }
      ],
      exits: [
        {
          id: "exit_opposite",
          description: "Exit on opposite crossover",
          logic: "Opposite EMA crossover signal"
        }
      ],
      stopLoss: { type: "atr", atrMultiplier: 1.5 },
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
    config: {
      instruments: ["EURUSD", "GBPUSD", "VOL75"],
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
          id: "ema_200",
          name: "EMA 200",
          type: "EMA",
          params: { period: 200 },
          condition: "Trend filter"
        }
      ],
      entries: [
        {
          id: "long_oversold",
          description: "Buy when RSI crosses above 30 (oversold bounce)",
          logic: "RSI[0] > 30 && RSI[1] <= 30 && Close > EMA200"
        },
        {
          id: "short_overbought",
          description: "Sell when RSI crosses below 70 (overbought rejection)",
          logic: "RSI[0] < 70 && RSI[1] >= 70 && Close < EMA200"
        }
      ],
      exits: [
        {
          id: "exit_midline",
          description: "Exit when RSI returns to 50 midline",
          logic: "RSI crosses 50 level"
        }
      ],
      stopLoss: { type: "fixed", pips: 10 },
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
    config: {
      instruments: ["NAS100", "BOOM1000", "CRASH1000"],
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
          description: "Buy when price breaks above upper band after squeeze",
          logic: "Close > UpperBand && ATR[0] > ATR[10] && BandWidth < AvgBandWidth"
        },
        {
          id: "short_breakout",
          description: "Sell when price breaks below lower band after squeeze",
          logic: "Close < LowerBand && ATR[0] > ATR[10] && BandWidth < AvgBandWidth"
        }
      ],
      exits: [
        {
          id: "exit_opposite_band",
          description: "Exit at opposite Bollinger Band",
          logic: "Price reaches opposite band"
        }
      ],
      stopLoss: { type: "atr", atrMultiplier: 2 },
      takeProfit: { type: "rr", ratio: 3 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  },
  {
    id: "macd-divergence",
    name: "MACD Divergence",
    description: "Identifies trend reversals by spotting divergence between price action and MACD indicator. Advanced pattern recognition strategy.",
    category: "Mean Reversion",
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
          condition: "Divergence detection"
        },
        {
          id: "rsi",
          name: "RSI",
          type: "RSI",
          params: { period: 14 },
          condition: "Confirmation filter"
        }
      ],
      entries: [
        {
          id: "bullish_divergence",
          description: "Buy on bullish divergence: lower price lows, higher MACD lows",
          logic: "Price makes lower low && MACD makes higher low && RSI > 30"
        },
        {
          id: "bearish_divergence",
          description: "Sell on bearish divergence: higher price highs, lower MACD highs",
          logic: "Price makes higher high && MACD makes lower high && RSI < 70"
        }
      ],
      exits: [
        {
          id: "macd_cross",
          description: "Exit when MACD crosses signal line in opposite direction",
          logic: "MACD crosses signal line"
        }
      ],
      stopLoss: { type: "structure", pips: 15 },
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
          description: "Buy when price above EMA and RSI shows bullish momentum",
          logic: "Close > EMA20 && RSI > 50 && RSI < 70 && Price pullback to EMA"
        },
        {
          id: "short_scalp",
          description: "Sell when price below EMA and RSI shows bearish momentum",
          logic: "Close < EMA20 && RSI < 50 && RSI > 30 && Price pullback to EMA"
        }
      ],
      exits: [
        {
          id: "quick_profit",
          description: "Quick profit target at 10 pips or opposite signal",
          logic: "Target reached or opposite EMA cross"
        }
      ],
      stopLoss: { type: "fixed", pips: 5 },
      takeProfit: { type: "fixed", pips: 10 },
      maxDailyLoss: 15,
      positionSizePercent: 2,
    }
  },
  {
    id: "volatility-breakout",
    name: "Volatility Index Breakout",
    description: "Specialized for synthetic volatility indices. Trades spike patterns and volatility breakouts with tight risk management.",
    category: "Breakout",
    config: {
      instruments: ["VOL75", "VOL100", "BOOM1000"],
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
        }
      ],
      entries: [
        {
          id: "spike_long",
          description: "Buy after volatility spike with trend confirmation",
          logic: "Price touches lower BB && Close > EMA50 && Previous spike down"
        },
        {
          id: "spike_short",
          description: "Sell after volatility spike with trend confirmation",
          logic: "Price touches upper BB && Close < EMA50 && Previous spike up"
        }
      ],
      exits: [
        {
          id: "mean_reversion",
          description: "Exit at middle BB or opposite spike",
          logic: "Price returns to BB middle or opposite signal"
        }
      ],
      stopLoss: { type: "fixed", pips: 15 },
      takeProfit: { type: "rr", ratio: 2 },
      maxDailyLoss: 25,
      positionSizePercent: 1.5,
    }
  }
];
