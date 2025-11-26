import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle2, TrendingUp, Calendar, Target } from "lucide-react";
import { useState } from "react";

const backtestSteps = [
  {
    category: "Setup",
    icon: Calendar,
    steps: [
      "Open TradingView or MT5 with your target instrument",
      "Set timeframe to match strategy (1m/5m/15m)",
      "Add all configured indicators to the chart",
      "Set chart to replay mode or historical data",
    ],
  },
  {
    category: "Execution",
    icon: TrendingUp,
    steps: [
      "Start from at least 3 months of historical data",
      "Progress candle-by-candle through the data",
      "Mark every entry signal according to your rules",
      "Record entry price, stop-loss, and take-profit",
      "Track actual exit based on price movement",
      "Log trade outcome (win/loss) and pips gained/lost",
    ],
  },
  {
    category: "Analysis",
    icon: Target,
    steps: [
      "Calculate total winning trades vs losing trades",
      "Compute win rate percentage",
      "Calculate average win vs average loss",
      "Determine actual risk:reward achieved",
      "Calculate maximum drawdown encountered",
      "Verify if strategy meets profit targets",
    ],
  },
  {
    category: "Validation",
    icon: CheckCircle2,
    steps: [
      "Test across different market conditions (trending/ranging)",
      "Verify performance in different sessions",
      "Check if edge degrades during news events",
      "Ensure at least 100+ trades for statistical significance",
      "Compare results against different instruments",
      "Document any strategy modifications needed",
    ],
  },
];

export const BacktestGuideStep = () => {
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  const toggleStep = (step: string) => {
    const newCompleted = new Set(completed);
    if (newCompleted.has(step)) {
      newCompleted.delete(step);
    } else {
      newCompleted.add(step);
    }
    setCompleted(newCompleted);
  };

  const totalSteps = backtestSteps.reduce((sum, cat) => sum + cat.steps.length, 0);
  const completedSteps = completed.size;
  const progress = Math.round((completedSteps / totalSteps) * 100);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold mb-2">Manual Backtest Checklist</h3>
        <p className="text-muted-foreground text-sm mb-4">
          Follow this systematic process to validate your strategy with historical data.
        </p>

        <Card className="p-4 bg-primary/10 border-primary/30 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-muted-foreground">Overall Progress</div>
              <div className="text-2xl font-bold font-mono text-primary">
                {completedSteps}/{totalSteps} Steps
              </div>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold font-mono text-primary">{progress}%</div>
              <div className="text-xs text-muted-foreground">Complete</div>
            </div>
          </div>
          <div className="mt-3 w-full bg-secondary rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500 profit-glow"
              style={{ width: `${progress}%` }}
            />
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        {backtestSteps.map((category, catIdx) => (
          <Card key={catIdx} className="p-6 bg-secondary/30 border-border">
            <div className="flex items-center gap-2 mb-4">
              <category.icon className="w-5 h-5 text-primary" />
              <h4 className="text-lg font-semibold">{category.category}</h4>
            </div>

            <div className="space-y-3">
              {category.steps.map((step, stepIdx) => {
                const stepId = `${catIdx}-${stepIdx}`;
                const isCompleted = completed.has(stepId);

                return (
                  <div
                    key={stepIdx}
                    className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
                      isCompleted
                        ? "bg-primary/10 border-primary/30"
                        : "bg-background/50 border-border hover:border-primary/20"
                    }`}
                  >
                    <Checkbox
                      id={stepId}
                      checked={isCompleted}
                      onCheckedChange={() => toggleStep(stepId)}
                      className="mt-0.5"
                    />
                    <label
                      htmlFor={stepId}
                      className={`flex-1 text-sm cursor-pointer ${
                        isCompleted ? "text-primary font-medium" : "text-foreground"
                      }`}
                    >
                      {step}
                    </label>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-6 bg-accent/10 border-accent/30">
        <h4 className="font-semibold mb-3 text-accent flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" />
          Pro Tips for Accurate Backtesting
        </h4>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>• Use tick data or at least M1 data for scalping strategies</li>
          <li>• Account for spread and commissions in every trade</li>
          <li>• Be brutally honest - only count signals that match ALL criteria</li>
          <li>• Test during high volatility AND low volatility periods</li>
          <li>• Skip trades during major news events unless strategy accounts for them</li>
          <li>• Document why trades failed to improve strategy</li>
          <li>• Aim for minimum 60% win rate with 1:2 RR for consistent profitability</li>
        </ul>
      </Card>
    </div>
  );
};
