import { StrategyConfig } from "@/types/strategy";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, AlertTriangle, Target, Percent } from "lucide-react";

interface Props {
  config: StrategyConfig;
  setConfig: (config: StrategyConfig) => void;
}

export const RiskManagementStep = ({ config, setConfig }: Props) => {
  const calculatePositionSize = () => {
    const riskAmount = (config.accountSize * config.positionSizePercent) / 100;
    const lotSize = riskAmount / (config.stopLoss.pips || 10);
    return lotSize.toFixed(2);
  };

  const calculateWinRate = () => {
    const rr = config.takeProfit.ratio || 2;
    const minWinRate = (1 / (1 + rr)) * 100;
    return minWinRate.toFixed(1);
  };

  const dailyTradesNeeded = () => {
    const avgWin = (config.stopLoss.pips || 10) * (config.takeProfit.ratio || 2);
    const trades = Math.ceil(config.dailyTarget / avgWin);
    return trades;
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 bg-secondary/30 border-border">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-destructive" />
            <h3 className="text-lg font-semibold">Stop Loss</h3>
          </div>

          <div className="space-y-4">
            <div>
              <Label>Type</Label>
              <select
                value={config.stopLoss.type}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    stopLoss: { ...config.stopLoss, type: e.target.value as any },
                  })
                }
                className="w-full bg-background border-border text-foreground rounded-md p-2 mt-1"
              >
                <option value="fixed">Fixed Pips</option>
                <option value="atr">ATR Multiple</option>
                <option value="structure">Market Structure</option>
              </select>
            </div>

            {config.stopLoss.type === "fixed" && (
              <div>
                <Label>Stop Loss (Pips)</Label>
                <Input
                  type="number"
                  value={config.stopLoss.pips || 0}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      stopLoss: { ...config.stopLoss, pips: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            )}

            {config.stopLoss.type === "atr" && (
              <div>
                <Label>ATR Multiplier</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={config.stopLoss.atrMultiplier || 1.5}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      stopLoss: {
                        ...config.stopLoss,
                        atrMultiplier: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6 bg-secondary/30 border-border">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-success" />
            <h3 className="text-lg font-semibold">Take Profit</h3>
          </div>

          <div className="space-y-4">
            <div>
              <Label>Type</Label>
              <select
                value={config.takeProfit.type}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    takeProfit: { ...config.takeProfit, type: e.target.value as any },
                  })
                }
                className="w-full bg-background border-border text-foreground rounded-md p-2 mt-1"
              >
                <option value="fixed">Fixed Pips</option>
                <option value="rr">Risk:Reward Ratio</option>
                <option value="trailing">Trailing Stop</option>
              </select>
            </div>

            {config.takeProfit.type === "fixed" && (
              <div>
                <Label>Take Profit (Pips)</Label>
                <Input
                  type="number"
                  value={config.takeProfit.pips || 0}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      takeProfit: { ...config.takeProfit, pips: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            )}

            {config.takeProfit.type === "rr" && (
              <div>
                <Label>Risk:Reward Ratio</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={config.takeProfit.ratio || 2}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      takeProfit: { ...config.takeProfit, ratio: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            )}

            {config.takeProfit.type === "trailing" && (
              <div>
                <Label>Trail Distance (Pips)</Label>
                <Input
                  type="number"
                  value={config.takeProfit.trailDistance || 10}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      takeProfit: {
                        ...config.takeProfit,
                        trailDistance: parseFloat(e.target.value),
                      },
                    })
                  }
                  className="bg-background border-border mt-1"
                />
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card className="p-6 bg-secondary/30 border-border">
        <div className="flex items-center gap-2 mb-4">
          <Percent className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Position Sizing</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Risk Per Trade (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={config.positionSizePercent}
              onChange={(e) =>
                setConfig({ ...config, positionSizePercent: parseFloat(e.target.value) })
              }
              className="bg-background border-border mt-1"
            />
          </div>
          <div>
            <Label>Max Daily Loss ($)</Label>
            <Input
              type="number"
              value={config.maxDailyLoss}
              onChange={(e) =>
                setConfig({ ...config, maxDailyLoss: parseFloat(e.target.value) })
              }
              className="bg-background border-border mt-1"
            />
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-accent/10 border-accent/30">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-semibold">Strategy Statistics</h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-primary">
              {calculatePositionSize()}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Lot Size</div>
          </div>

          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-accent">{calculateWinRate()}%</div>
            <div className="text-xs text-muted-foreground mt-1">Min Win Rate</div>
          </div>

          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-success">
              {dailyTradesNeeded()}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Trades/Day</div>
          </div>

          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-foreground">
              ${config.dailyTarget}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Daily Target</div>
          </div>
        </div>
      </Card>
    </div>
  );
};
