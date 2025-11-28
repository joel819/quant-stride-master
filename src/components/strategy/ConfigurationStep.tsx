import { StrategyConfig } from "@/types/strategy";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Clock, DollarSign, Globe } from "lucide-react";

interface Props {
  config: StrategyConfig;
  setConfig: (config: StrategyConfig) => void;
}

const instruments = [
  // Major Forex Pairs
  { label: "EUR/USD", value: "EURUSD", category: "Forex", bestSessions: ["london", "overlap", "newyork"] },
  { label: "GBP/USD", value: "GBPUSD", category: "Forex", bestSessions: ["london", "overlap", "newyork"] },
  { label: "USD/JPY", value: "USDJPY", category: "Forex", bestSessions: ["asian", "london", "newyork"] },
  { label: "AUD/USD", value: "AUDUSD", category: "Forex", bestSessions: ["asian", "london"] },
  { label: "USD/CAD", value: "USDCAD", category: "Forex", bestSessions: ["newyork", "overlap"] },
  { label: "NZD/USD", value: "NZDUSD", category: "Forex", bestSessions: ["asian", "london"] },
  { label: "USD/CHF", value: "USDCHF", category: "Forex", bestSessions: ["london", "overlap"] },
  // Cross Pairs
  { label: "EUR/JPY", value: "EURJPY", category: "Forex", bestSessions: ["london", "overlap"] },
  { label: "GBP/JPY", value: "GBPJPY", category: "Forex", bestSessions: ["london", "overlap"] },
  { label: "AUD/JPY", value: "AUDJPY", category: "Forex", bestSessions: ["asian", "london"] },
  { label: "EUR/GBP", value: "EURGBP", category: "Forex", bestSessions: ["london", "overlap"] },
  { label: "EUR/CHF", value: "EURCHF", category: "Forex", bestSessions: ["london"] },
  { label: "GBP/AUD", value: "GBPAUD", category: "Forex", bestSessions: ["london", "asian"] },
  // Indices
  { label: "NASDAQ 100", value: "NAS100", category: "Indices", bestSessions: ["newyork", "overlap"] },
  { label: "Dow Jones 30", value: "US30", category: "Indices", bestSessions: ["newyork", "overlap"] },
  { label: "S&P 500", value: "SPX500", category: "Indices", bestSessions: ["newyork", "overlap"] },
  { label: "Germany 40", value: "GER40", category: "Indices", bestSessions: ["london"] },
  // Volatility Indices - 24/7 Trading
  { label: "Volatility 10", value: "VOL10", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Volatility 25", value: "VOL25", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Volatility 50", value: "VOL50", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Volatility 75", value: "VOL75", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Volatility 100", value: "VOL100", category: "Synthetic", bestSessions: ["24/7"] },
  // Boom & Crash Indices - 24/7 Trading
  { label: "Boom 500", value: "BOOM500", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Boom 1000", value: "BOOM1000", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Crash 500", value: "CRASH500", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Crash 1000", value: "CRASH1000", category: "Synthetic", bestSessions: ["24/7"] },
  // Jump Indices - 24/7 Trading
  { label: "Jump 10", value: "JUMP10", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Jump 25", value: "JUMP25", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Jump 50", value: "JUMP50", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Jump 75", value: "JUMP75", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Jump 100", value: "JUMP100", category: "Synthetic", bestSessions: ["24/7"] },
  // Other Synthetic Indices - 24/7 Trading
  { label: "Step Index", value: "STEP", category: "Synthetic", bestSessions: ["24/7"] },
  { label: "Range Break", value: "RANGEBREAK", category: "Synthetic", bestSessions: ["24/7"] },
];

const sessions = [
  { label: "London Session", value: "london", time: "08:00-16:00 GMT", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  { label: "New York Session", value: "newyork", time: "13:00-21:00 GMT", color: "bg-green-500/20 text-green-400 border-green-500/30" },
  { label: "London/NY Overlap", value: "overlap", time: "13:00-16:00 GMT", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  { label: "Asian Session", value: "asian", time: "23:00-08:00 GMT", color: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
];

const getSessionBadge = (sessionValue: string) => {
  const session = sessions.find(s => s.value === sessionValue);
  return session ? { label: session.label.split(" ")[0], color: session.color } : null;
};

export const ConfigurationStep = ({ config, setConfig }: Props) => {
  const toggleInstrument = (value: string) => {
    const updated = config.instruments.includes(value)
      ? config.instruments.filter((i) => i !== value)
      : [...config.instruments, value];
    setConfig({ ...config, instruments: updated });
  };

  const toggleSession = (value: string) => {
    const updated = config.sessions.includes(value as any)
      ? config.sessions.filter((s) => s !== value)
      : [...config.sessions, value as any];
    setConfig({ ...config, sessions: updated });
  };

  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-primary" />
          <h3 className="text-xl font-semibold">Instruments</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {["Forex", "Indices", "Synthetic"].map((category) => (
            <div key={category} className="space-y-2 bg-secondary/20 p-4 rounded-lg border border-border">
              <Badge variant="outline" className="mb-3">
                {category} ({instruments.filter((i) => i.category === category).length})
              </Badge>
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                {instruments
                  .filter((i) => i.category === category)
                  .map((instrument) => (
                    <div key={instrument.value} className="flex items-start space-x-2 group">
                      <Checkbox
                        id={instrument.value}
                        checked={config.instruments.includes(instrument.value)}
                        onCheckedChange={() => toggleInstrument(instrument.value)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <label
                          htmlFor={instrument.value}
                          className="text-sm cursor-pointer hover:text-primary transition-colors block"
                        >
                          {instrument.label}
                        </label>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {instrument.bestSessions[0] === "24/7" ? (
                            <Badge variant="outline" className="text-xs px-1.5 py-0 bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                              24/7
                            </Badge>
                          ) : (
                            instrument.bestSessions.map((session) => {
                              const badge = getSessionBadge(session);
                              return badge ? (
                                <Badge 
                                  key={session} 
                                  variant="outline" 
                                  className={`text-xs px-1.5 py-0 ${badge.color}`}
                                >
                                  {badge.label}
                                </Badge>
                              ) : null;
                            })
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-primary" />
            <Label>Timeframe</Label>
          </div>
          <select
            value={config.timeframe}
            onChange={(e) => setConfig({ ...config, timeframe: e.target.value as any })}
            className="w-full bg-secondary border-border text-foreground rounded-md p-2"
          >
            <option value="1m">1 Minute (Scalping)</option>
            <option value="5m">5 Minutes (Day Trading)</option>
            <option value="15m">15 Minutes (Swing Intraday)</option>
          </select>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-primary" />
            <Label>Account Parameters</Label>
          </div>
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  type="number"
                  placeholder="Account Size"
                  value={config.accountSize}
                  onChange={(e) =>
                    setConfig({ ...config, accountSize: parseFloat(e.target.value) })
                  }
                  className="bg-secondary border-border"
                />
              </div>
              <div className="flex-1">
                <Input
                  type="number"
                  placeholder="Daily Target"
                  value={config.dailyTarget}
                  onChange={(e) =>
                    setConfig({ ...config, dailyTarget: parseFloat(e.target.value) })
                  }
                  className="bg-secondary border-border"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-primary" />
          <h3 className="text-xl font-semibold">Trading Sessions</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {sessions.map((session) => (
            <div
              key={session.value}
              className="flex items-start space-x-3 p-3 rounded-lg bg-secondary/50 border border-border hover:border-primary/50 transition-colors"
            >
              <Checkbox
                id={session.value}
                checked={config.sessions.includes(session.value as any)}
                onCheckedChange={() => toggleSession(session.value)}
                className="mt-1"
              />
              <div className="flex-1">
                <label
                  htmlFor={session.value}
                  className="text-sm font-medium cursor-pointer block"
                >
                  {session.label}
                </label>
                <p className="text-xs text-muted-foreground font-mono">{session.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
