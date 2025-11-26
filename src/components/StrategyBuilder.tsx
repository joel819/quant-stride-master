import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ConfigurationStep } from "./strategy/ConfigurationStep";
import { IndicatorsStep } from "./strategy/IndicatorsStep";
import { RiskManagementStep } from "./strategy/RiskManagementStep";
import { PerformanceAnalyzerStep } from "./strategy/PerformanceAnalyzerStep";
import { CodeGeneratorStep } from "./strategy/CodeGeneratorStep";
import { BacktestGuideStep } from "./strategy/BacktestGuideStep";
import { StrategyConfig } from "@/types/strategy";

export const StrategyBuilder = () => {
  const [config, setConfig] = useState<StrategyConfig>({
    instruments: ["EURUSD", "GBPUSD"],
    timeframe: "1m",
    accountSize: 100,
    dailyTarget: 150,
    sessions: ["london", "newyork", "overlap"],
    indicators: [],
    entries: [],
    exits: [],
    stopLoss: { type: "fixed", pips: 5 },
    takeProfit: { type: "rr", ratio: 2 },
    maxDailyLoss: 20,
    positionSizePercent: 2,
  });

  return (
    <div className="min-h-screen bg-background grid-pattern">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Quantum Strategy Builder
          </h1>
          <p className="text-muted-foreground">
            Build institutional-grade mechanical trading strategies
          </p>
        </div>

        <Card className="card-elevated bg-card/50 backdrop-blur-sm border-border">
          <Tabs defaultValue="config" className="w-full">
            <TabsList className="w-full grid grid-cols-6 bg-secondary/50">
              <TabsTrigger value="config">Configuration</TabsTrigger>
              <TabsTrigger value="indicators">Indicators</TabsTrigger>
              <TabsTrigger value="risk">Risk Management</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="code">Code Export</TabsTrigger>
              <TabsTrigger value="backtest">Backtest</TabsTrigger>
            </TabsList>

            <div className="p-6">
              <TabsContent value="config">
                <ConfigurationStep config={config} setConfig={setConfig} />
              </TabsContent>

              <TabsContent value="indicators">
                <IndicatorsStep config={config} setConfig={setConfig} />
              </TabsContent>

              <TabsContent value="risk">
                <RiskManagementStep config={config} setConfig={setConfig} />
              </TabsContent>

              <TabsContent value="performance">
                <PerformanceAnalyzerStep config={config} />
              </TabsContent>

              <TabsContent value="code">
                <CodeGeneratorStep config={config} />
              </TabsContent>

              <TabsContent value="backtest">
                <BacktestGuideStep />
              </TabsContent>
            </div>
          </Tabs>
        </Card>
      </div>
    </div>
  );
};
