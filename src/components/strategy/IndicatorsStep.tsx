import { StrategyConfig, Indicator } from "@/types/strategy";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, TrendingUp, Activity } from "lucide-react";
import { useState } from "react";

interface Props {
  config: StrategyConfig;
  setConfig: (config: StrategyConfig) => void;
}

const indicatorTemplates = [
  { name: "EMA", params: { period: 20 } },
  { name: "RSI", params: { period: 14, overbought: 70, oversold: 30 } },
  { name: "MACD", params: { fast: 12, slow: 26, signal: 9 } },
  { name: "VWAP", params: {} },
  { name: "BB", params: { period: 20, deviation: 2 } },
  { name: "ATR", params: { period: 14 } },
  { name: "Stochastic", params: { kPeriod: 14, dPeriod: 3, slowing: 3 } },
];

export const IndicatorsStep = ({ config, setConfig }: Props) => {
  const [selectedType, setSelectedType] = useState<string>("EMA");

  const addIndicator = () => {
    const template = indicatorTemplates.find((t) => t.name === selectedType);
    if (!template) return;

    const newIndicator: Indicator = {
      id: `${template.name}-${Date.now()}`,
      name: template.name,
      type: template.name as any,
      params: { ...template.params },
      condition: "",
    };

    setConfig({
      ...config,
      indicators: [...config.indicators, newIndicator],
    });
  };

  const updateIndicator = (id: string, updates: Partial<Indicator>) => {
    setConfig({
      ...config,
      indicators: config.indicators.map((ind) =>
        ind.id === id ? { ...ind, ...updates } : ind
      ),
    });
  };

  const removeIndicator = (id: string) => {
    setConfig({
      ...config,
      indicators: config.indicators.filter((ind) => ind.id !== id),
    });
  };

  const addEntry = () => {
    setConfig({
      ...config,
      entries: [
        ...config.entries,
        {
          id: `entry-${Date.now()}`,
          description: "",
          logic: "",
        },
      ],
    });
  };

  const addExit = () => {
    setConfig({
      ...config,
      exits: [
        ...config.exits,
        {
          id: `exit-${Date.now()}`,
          description: "",
          logic: "",
        },
      ],
    });
  };

  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="text-xl font-semibold">Technical Indicators</h3>
          </div>
          <div className="flex gap-2">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-secondary border-border text-foreground rounded-md px-3 py-2"
            >
              {indicatorTemplates.map((template) => (
                <option key={template.name} value={template.name}>
                  {template.name}
                </option>
              ))}
            </select>
            <Button onClick={addIndicator} size="sm" className="profit-glow">
              <Plus className="w-4 h-4 mr-1" />
              Add Indicator
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          {config.indicators.map((indicator) => (
            <Card key={indicator.id} className="p-4 bg-secondary/30 border-border">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Badge className="font-mono bg-primary/20 text-primary border-primary/30">
                    {indicator.type}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeIndicator(indicator.id)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                {Object.entries(indicator.params).map(([key, value]) => (
                  <div key={key}>
                    <Label className="text-xs text-muted-foreground capitalize">
                      {key}
                    </Label>
                    <Input
                      type="number"
                      value={value}
                      onChange={(e) =>
                        updateIndicator(indicator.id, {
                          params: {
                            ...indicator.params,
                            [key]: parseFloat(e.target.value),
                          },
                        })
                      }
                      className="bg-background border-border mt-1"
                    />
                  </div>
                ))}
              </div>

              <div>
                <Label className="text-xs text-muted-foreground">Signal Condition</Label>
                <Input
                  placeholder="e.g., RSI crosses above 30 on candle close"
                  value={indicator.condition || ""}
                  onChange={(e) =>
                    updateIndicator(indicator.id, { condition: e.target.value })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-success" />
            <h3 className="text-xl font-semibold">Entry Conditions</h3>
          </div>
          <Button onClick={addEntry} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add Entry Rule
          </Button>
        </div>

        <div className="space-y-3">
          {config.entries.map((entry, idx) => (
            <Card key={entry.id} className="p-4 bg-success/5 border-success/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-mono text-success">Entry Rule #{idx + 1}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setConfig({
                      ...config,
                      entries: config.entries.filter((e) => e.id !== entry.id),
                    })
                  }
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              <Textarea
                placeholder="Describe exact entry condition (e.g., Price breaks above EMA 20 AND RSI > 50 AND MACD histogram turns positive)"
                value={entry.description}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    entries: config.entries.map((en) =>
                      en.id === entry.id ? { ...en, description: e.target.value } : en
                    ),
                  })
                }
                className="bg-background border-border min-h-[80px]"
              />
            </Card>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-destructive rotate-180" />
            <h3 className="text-xl font-semibold">Exit Conditions</h3>
          </div>
          <Button onClick={addExit} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add Exit Rule
          </Button>
        </div>

        <div className="space-y-3">
          {config.exits.map((exit, idx) => (
            <Card key={exit.id} className="p-4 bg-destructive/5 border-destructive/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-mono text-destructive">Exit Rule #{idx + 1}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setConfig({
                      ...config,
                      exits: config.exits.filter((e) => e.id !== exit.id),
                    })
                  }
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              <Textarea
                placeholder="Describe exact exit condition (e.g., Price touches opposite Bollinger Band OR trailing stop hit)"
                value={exit.description}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    exits: config.exits.map((ex) =>
                      ex.id === exit.id ? { ...ex, description: e.target.value } : ex
                    ),
                  })
                }
                className="bg-background border-border min-h-[80px]"
              />
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

const Badge = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded ${className}`}>
    {children}
  </span>
);
