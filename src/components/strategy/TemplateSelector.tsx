import { StrategyConfig } from "@/types/strategy";
import { strategyTemplates, StrategyTemplate } from "@/data/strategyTemplates";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, RefreshCw, Zap, BarChart3, Download } from "lucide-react";
import { toast } from "sonner";

interface Props {
  onSelectTemplate: (config: StrategyConfig) => void;
}

const categoryIcons = {
  "Trend Following": TrendingUp,
  "Mean Reversion": RefreshCw,
  "Breakout": Zap,
  "Scalping": BarChart3,
};

const categoryColors = {
  "Trend Following": "bg-blue-500/20 text-blue-400 border-blue-500/30",
  "Mean Reversion": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "Breakout": "bg-orange-500/20 text-orange-400 border-orange-500/30",
  "Scalping": "bg-green-500/20 text-green-400 border-green-500/30",
};

export const TemplateSelector = ({ onSelectTemplate }: Props) => {
  const handleLoadTemplate = (template: StrategyTemplate) => {
    onSelectTemplate(template.config);
    toast.success(`Loaded: ${template.name}`, {
      description: "Template configuration applied successfully",
    });
  };

  const categories = Array.from(new Set(strategyTemplates.map(t => t.category)));

  const renderTemplateCard = (template: StrategyTemplate) => {
    const Icon = categoryIcons[template.category];
    
    return (
      <Card
        key={template.id}
        className="p-4 bg-secondary/30 border-border hover:border-primary/50 transition-all hover:shadow-lg group"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg ${categoryColors[template.category]}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-foreground mb-1 group-hover:text-primary transition-colors">
                {template.name}
              </h4>
              <Badge variant="outline" className={`text-xs ${categoryColors[template.category]}`}>
                {template.category}
              </Badge>
            </div>
          </div>
        </div>

        <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
          {template.description}
        </p>

        <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
          <div className="bg-background/50 rounded p-2">
            <div className="text-muted-foreground mb-1">Timeframe</div>
            <div className="font-semibold text-foreground">{template.config.timeframe}</div>
          </div>
          <div className="bg-background/50 rounded p-2">
            <div className="text-muted-foreground mb-1">Indicators</div>
            <div className="font-semibold text-foreground">{template.config.indicators.length}</div>
          </div>
          <div className="bg-background/50 rounded p-2">
            <div className="text-muted-foreground mb-1">Risk</div>
            <div className="font-semibold text-foreground">{template.config.positionSizePercent}%</div>
          </div>
          <div className="bg-background/50 rounded p-2">
            <div className="text-muted-foreground mb-1">Daily Target</div>
            <div className="font-semibold text-foreground">${template.config.dailyTarget}</div>
          </div>
        </div>

        <Button
          onClick={() => handleLoadTemplate(template)}
          className="w-full profit-glow"
          size="sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Load Template
        </Button>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Strategy Templates
        </h3>
        <p className="text-muted-foreground">
          Pre-configured institutional-grade strategies ready to deploy
        </p>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList className="w-full grid grid-cols-5 bg-secondary/50">
          <TabsTrigger value="all">All</TabsTrigger>
          {categories.map((category) => (
            <TabsTrigger key={category} value={category}>
              {category.split(" ")[0]}
            </TabsTrigger>
          ))}
        </TabsList>

        <ScrollArea className="h-[600px] mt-6">
          <TabsContent value="all" className="mt-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
              {strategyTemplates.map(renderTemplateCard)}
            </div>
          </TabsContent>

          {categories.map((category) => (
            <TabsContent key={category} value={category} className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
                {strategyTemplates
                  .filter(t => t.category === category)
                  .map(renderTemplateCard)}
              </div>
            </TabsContent>
          ))}
        </ScrollArea>
      </Tabs>
    </div>
  );
};
