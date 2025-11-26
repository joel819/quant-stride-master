import { StrategyConfig } from "@/types/strategy";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, TrendingDown, Activity, DollarSign, Percent, AlertTriangle } from "lucide-react";
import { useState, useMemo } from "react";

interface Props {
  config: StrategyConfig;
}

interface PerformanceMetrics {
  expectedValuePerTrade: number;
  winRate: number;
  lossRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  expectedDailyProfit: number;
  expectedMonthlyProfit: number;
  maxDrawdown: number;
  sharpeRatio: number;
  recoveryFactor: number;
  consecutiveLossProbability: number;
}

export const PerformanceAnalyzerStep = ({ config }: Props) => {
  const [customWinRate, setCustomWinRate] = useState<number>(65);
  const [tradesPerDay, setTradesPerDay] = useState<number>(8);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(4);
  const [simulationRuns, setSimulationRuns] = useState<number>(1000);

  const metrics = useMemo((): PerformanceMetrics => {
    const rrRatio = config.takeProfit.ratio || 2;
    const stopLossPips = config.stopLoss.pips || 10;
    
    const winRate = customWinRate / 100;
    const lossRate = 1 - winRate;
    
    const avgWin = stopLossPips * rrRatio;
    const avgLoss = stopLossPips;
    
    // Expected Value per trade
    const ev = (winRate * avgWin) - (lossRate * avgLoss);
    
    // Profit Factor
    const grossProfit = winRate * avgWin;
    const grossLoss = lossRate * avgLoss;
    const profitFactor = grossProfit / grossLoss;
    
    // Daily & Monthly Projections
    const expectedDailyProfit = ev * tradesPerDay;
    const expectedMonthlyProfit = expectedDailyProfit * 20; // 20 trading days
    
    // Maximum Drawdown Estimation (based on consecutive losses)
    const consecutiveLosses = Math.ceil(Math.log(0.01) / Math.log(lossRate));
    const maxDrawdown = consecutiveLosses * avgLoss;
    
    // Sharpe Ratio Calculation
    const dailyReturn = expectedDailyProfit / config.accountSize;
    const stdDev = Math.sqrt(
      winRate * Math.pow(avgWin / config.accountSize - dailyReturn, 2) +
      lossRate * Math.pow(-avgLoss / config.accountSize - dailyReturn, 2)
    ) * Math.sqrt(tradesPerDay);
    
    const annualizedReturn = dailyReturn * 252; // 252 trading days
    const annualizedStdDev = stdDev * Math.sqrt(252);
    const sharpeRatio = (annualizedReturn - riskFreeRate / 100) / annualizedStdDev;
    
    // Recovery Factor
    const recoveryFactor = expectedMonthlyProfit / maxDrawdown;
    
    // Consecutive Loss Probability (5 losses in a row)
    const consecutiveLossProbability = Math.pow(lossRate, 5) * 100;
    
    return {
      expectedValuePerTrade: ev,
      winRate,
      lossRate,
      avgWin,
      avgLoss,
      profitFactor,
      expectedDailyProfit,
      expectedMonthlyProfit,
      maxDrawdown,
      sharpeRatio,
      recoveryFactor,
      consecutiveLossProbability,
    };
  }, [config, customWinRate, tradesPerDay, riskFreeRate]);

  const runMonteCarloSimulation = () => {
    const results: number[] = [];
    
    for (let sim = 0; sim < simulationRuns; sim++) {
      let balance = config.accountSize;
      
      for (let trade = 0; trade < tradesPerDay * 20; trade++) {
        const isWin = Math.random() < metrics.winRate;
        const pipsGained = isWin ? metrics.avgWin : -metrics.avgLoss;
        const dollarValue = (pipsGained / 10) * (balance * config.positionSizePercent / 100);
        balance += dollarValue;
        
        if (balance <= config.accountSize * 0.5) break; // 50% drawdown stop
      }
      
      results.push(balance);
    }
    
    const sortedResults = results.sort((a, b) => a - b);
    const median = sortedResults[Math.floor(sortedResults.length / 2)];
    const percentile95 = sortedResults[Math.floor(sortedResults.length * 0.95)];
    const percentile5 = sortedResults[Math.floor(sortedResults.length * 0.05)];
    
    return {
      median: median - config.accountSize,
      best: percentile95 - config.accountSize,
      worst: percentile5 - config.accountSize,
      profitable: results.filter(r => r > config.accountSize).length / results.length * 100,
    };
  };

  const [simResults, setSimResults] = useState(runMonteCarloSimulation());

  const getMetricColor = (value: number, threshold: { good: number; bad: number }) => {
    if (value >= threshold.good) return "text-success";
    if (value <= threshold.bad) return "text-destructive";
    return "text-accent";
  };

  const getRiskLevel = () => {
    if (metrics.sharpeRatio > 2 && metrics.profitFactor > 2) return { level: "Low Risk", color: "success" };
    if (metrics.sharpeRatio > 1 && metrics.profitFactor > 1.5) return { level: "Medium Risk", color: "accent" };
    return { level: "High Risk", color: "destructive" };
  };

  const riskLevel = getRiskLevel();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold mb-2">Strategy Performance Analyzer</h3>
        <p className="text-muted-foreground text-sm">
          Statistical analysis and Monte Carlo simulation of your strategy's expected performance
        </p>
      </div>

      <Card className="p-6 bg-secondary/30 border-border">
        <h4 className="font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Analysis Parameters
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Expected Win Rate (%)</Label>
            <Input
              type="number"
              min="50"
              max="100"
              value={customWinRate}
              onChange={(e) => setCustomWinRate(parseFloat(e.target.value))}
              className="bg-background border-border mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Based on backtest results or conservative estimate
            </p>
          </div>
          
          <div>
            <Label>Expected Trades Per Day</Label>
            <Input
              type="number"
              min="1"
              max="50"
              value={tradesPerDay}
              onChange={(e) => setTradesPerDay(parseFloat(e.target.value))}
              className="bg-background border-border mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Average number of setups per trading day
            </p>
          </div>
          
          <div>
            <Label>Risk-Free Rate (%)</Label>
            <Input
              type="number"
              step="0.1"
              value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(parseFloat(e.target.value))}
              className="bg-background border-border mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Annual benchmark rate (e.g., T-Bills)
            </p>
          </div>
          
          <div>
            <Label>Monte Carlo Runs</Label>
            <Input
              type="number"
              value={simulationRuns}
              onChange={(e) => setSimulationRuns(parseFloat(e.target.value))}
              className="bg-background border-border mt-1"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Number of simulation iterations
            </p>
          </div>
        </div>
        
        <Button 
          onClick={() => setSimResults(runMonteCarloSimulation())}
          className="mt-4 w-full profit-glow"
        >
          Run Simulation
        </Button>
      </Card>

      <Card className={`p-6 bg-${riskLevel.color}/10 border-${riskLevel.color}/30`}>
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold flex items-center gap-2">
            <AlertTriangle className={`w-5 h-5 text-${riskLevel.color}`} />
            Risk Assessment
          </h4>
          <span className={`text-lg font-bold text-${riskLevel.color}`}>{riskLevel.level}</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={`text-3xl font-bold font-mono ${getMetricColor(metrics.sharpeRatio, { good: 2, bad: 1 })}`}>
              {metrics.sharpeRatio.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Sharpe Ratio</div>
            <Progress 
              value={Math.min(metrics.sharpeRatio * 25, 100)} 
              className="mt-2 h-1"
            />
          </div>
          
          <div className="text-center">
            <div className={`text-3xl font-bold font-mono ${getMetricColor(metrics.profitFactor, { good: 2, bad: 1.5 })}`}>
              {metrics.profitFactor.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Profit Factor</div>
            <Progress 
              value={Math.min(metrics.profitFactor * 30, 100)} 
              className="mt-2 h-1"
            />
          </div>
          
          <div className="text-center">
            <div className={`text-3xl font-bold font-mono ${getMetricColor(metrics.recoveryFactor, { good: 3, bad: 1 })}`}>
              {metrics.recoveryFactor.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Recovery Factor</div>
            <Progress 
              value={Math.min(metrics.recoveryFactor * 20, 100)} 
              className="mt-2 h-1"
            />
          </div>
          
          <div className="text-center">
            <div className={`text-3xl font-bold font-mono ${getMetricColor(100 - metrics.consecutiveLossProbability, { good: 90, bad: 70 })}`}>
              {metrics.consecutiveLossProbability.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">5-Loss Streak Risk</div>
            <Progress 
              value={100 - metrics.consecutiveLossProbability} 
              className="mt-2 h-1"
            />
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 bg-success/5 border-success/20">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-success" />
            <h4 className="font-semibold">Profitability Metrics</h4>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Expected Value/Trade</span>
              <span className="text-lg font-bold font-mono text-success">
                +{metrics.expectedValuePerTrade.toFixed(2)} pips
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Expected Daily Profit</span>
              <span className="text-lg font-bold font-mono text-success">
                ${metrics.expectedDailyProfit.toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Expected Monthly Profit</span>
              <span className="text-lg font-bold font-mono text-success">
                ${metrics.expectedMonthlyProfit.toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Monthly ROI</span>
              <span className="text-lg font-bold font-mono text-success">
                {((metrics.expectedMonthlyProfit / config.accountSize) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-destructive/5 border-destructive/20">
          <div className="flex items-center gap-2 mb-4">
            <TrendingDown className="w-5 h-5 text-destructive" />
            <h4 className="font-semibold">Risk Metrics</h4>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Estimated Max Drawdown</span>
              <span className="text-lg font-bold font-mono text-destructive">
                ${metrics.maxDrawdown.toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Drawdown % of Account</span>
              <span className="text-lg font-bold font-mono text-destructive">
                {((metrics.maxDrawdown / config.accountSize) * 100).toFixed(1)}%
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Max Daily Loss Limit</span>
              <span className="text-lg font-bold font-mono text-destructive">
                ${config.maxDailyLoss}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-background/50 rounded-lg">
              <span className="text-sm text-muted-foreground">Risk Per Trade</span>
              <span className="text-lg font-bold font-mono text-destructive">
                {config.positionSizePercent}%
              </span>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6 bg-primary/5 border-primary/20">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-5 h-5 text-primary" />
          <h4 className="font-semibold">Monte Carlo Simulation Results</h4>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-primary">
              {simResults.profitable.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">Profitable Months</div>
          </div>
          
          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className={`text-2xl font-bold font-mono ${simResults.median > 0 ? 'text-success' : 'text-destructive'}`}>
              ${simResults.median.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Median Outcome</div>
          </div>
          
          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-success">
              ${simResults.best.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">95th Percentile</div>
          </div>
          
          <div className="text-center p-4 bg-background/50 rounded-lg">
            <div className="text-2xl font-bold font-mono text-destructive">
              ${simResults.worst.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">5th Percentile</div>
          </div>
        </div>
        
        <p className="text-xs text-muted-foreground mt-4 text-center">
          Simulation ran {simulationRuns.toLocaleString()} iterations over a 20-day trading period
        </p>
      </Card>

      <Card className="p-6 bg-accent/10 border-accent/30">
        <h4 className="font-semibold mb-3 text-accent flex items-center gap-2">
          <Percent className="w-5 h-5" />
          Performance Interpretation
        </h4>
        <div className="space-y-3 text-sm">
          <div className="flex gap-2">
            <span className="font-semibold min-w-[140px]">Sharpe Ratio:</span>
            <span className="text-muted-foreground">
              {metrics.sharpeRatio > 2 ? "Excellent" : metrics.sharpeRatio > 1 ? "Good" : "Poor"} - 
              {metrics.sharpeRatio > 2 
                ? " Superior risk-adjusted returns" 
                : metrics.sharpeRatio > 1 
                ? " Acceptable risk-adjusted returns" 
                : " Returns don't justify the risk"}
            </span>
          </div>
          
          <div className="flex gap-2">
            <span className="font-semibold min-w-[140px]">Profit Factor:</span>
            <span className="text-muted-foreground">
              {metrics.profitFactor > 2 ? "Strong" : metrics.profitFactor > 1.5 ? "Acceptable" : "Weak"} - 
              For every $1 lost, you make ${metrics.profitFactor.toFixed(2)}
            </span>
          </div>
          
          <div className="flex gap-2">
            <span className="font-semibold min-w-[140px]">Win Rate:</span>
            <span className="text-muted-foreground">
              {(metrics.winRate * 100).toFixed(1)}% - 
              {metrics.winRate > 0.6 ? " High consistency" : " Moderate consistency"}
            </span>
          </div>
          
          <div className="flex gap-2">
            <span className="font-semibold min-w-[140px]">Recovery Factor:</span>
            <span className="text-muted-foreground">
              {metrics.recoveryFactor > 3 ? "Excellent" : metrics.recoveryFactor > 2 ? "Good" : "Concerning"} - 
              Profits are {metrics.recoveryFactor.toFixed(1)}x larger than max drawdown
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
};
