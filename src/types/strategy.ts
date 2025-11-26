export type Instrument = "EURUSD" | "GBPUSD" | "USDJPY" | "NAS100" | "US30" | "VOL75" | "VOL100" | "BOOM1000" | "CRASH500";

export type Timeframe = "1m" | "5m" | "15m";

export type Session = "london" | "newyork" | "overlap" | "asian";

export interface Indicator {
  id: string;
  name: string;
  type: "EMA" | "SMA" | "RSI" | "MACD" | "VWAP" | "BB" | "ATR" | "Stochastic";
  params: Record<string, number>;
  condition?: string;
}

export interface EntryCondition {
  id: string;
  description: string;
  logic: string;
}

export interface ExitCondition {
  id: string;
  description: string;
  logic: string;
}

export interface StopLoss {
  type: "fixed" | "atr" | "structure";
  pips?: number;
  atrMultiplier?: number;
}

export interface TakeProfit {
  type: "fixed" | "rr" | "trailing";
  pips?: number;
  ratio?: number;
  trailDistance?: number;
}

export interface StrategyConfig {
  instruments: string[];
  timeframe: Timeframe;
  accountSize: number;
  dailyTarget: number;
  sessions: Session[];
  indicators: Indicator[];
  entries: EntryCondition[];
  exits: ExitCondition[];
  stopLoss: StopLoss;
  takeProfit: TakeProfit;
  maxDailyLoss: number;
  positionSizePercent: number;
}
