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
  { label: "EUR/USD", value: "EURUSD", category: "Forex" },
  { label: "GBP/USD", value: "GBPUSD", category: "Forex" },
  { label: "USD/JPY", value: "USDJPY", category: "Forex" },
  { label: "NASDAQ 100", value: "NAS100", category: "Indices" },
  { label: "Dow Jones", value: "US30", category: "Indices" },
  { label: "Volatility 75", value: "VOL75", category: "Synthetic" },
  { label: "Volatility 100", value: "VOL100", category: "Synthetic" },
  { label: "Boom 1000", value: "BOOM1000", category: "Synthetic" },
  { label: "Crash 500", value: "CRASH500", category: "Synthetic" },
];

const sessions = [
  { label: "London Session", value: "london", time: "08:00-16:00 GMT" },
  { label: "New York Session", value: "newyork", time: "13:00-21:00 GMT" },
  { label: "London/NY Overlap", value: "overlap", time: "13:00-16:00 GMT" },
  { label: "Asian Session", value: "asian", time: "23:00-08:00 GMT" },
];

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
            <div key={category} className="space-y-2">
              <Badge variant="outline" className="mb-2">
                {category}
              </Badge>
              {instruments
                .filter((i) => i.category === category)
                .map((instrument) => (
                  <div key={instrument.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={instrument.value}
                      checked={config.instruments.includes(instrument.value)}
                      onCheckedChange={() => toggleInstrument(instrument.value)}
                    />
                    <label
                      htmlFor={instrument.value}
                      className="text-sm cursor-pointer hover:text-primary transition-colors"
                    >
                      {instrument.label}
                    </label>
                  </div>
                ))}
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
