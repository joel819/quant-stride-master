import { StrategyConfig } from "@/types/strategy";
import { strategyTemplates, StrategyTemplate } from "@/data/strategyTemplates";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, RefreshCw, Zap, BarChart3, Download, Trash2, User } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/integrations/supabase/client";
import { useEffect, useState } from "react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

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

interface UserTemplate extends StrategyTemplate {
  id: string;
  created_at: string;
}

export const TemplateSelector = ({ onSelectTemplate }: Props) => {
  const { user } = useAuth();
  const [userTemplates, setUserTemplates] = useState<UserTemplate[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      loadUserTemplates();
    }
  }, [user]);

  const loadUserTemplates = async () => {
    if (!user) return;
    
    const { data, error } = await supabase
      .from('strategy_templates')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) {
      toast.error('Failed to load templates');
    } else {
      setUserTemplates(data.map(t => ({
        id: t.id,
        name: t.name,
        description: t.description || '',
        category: t.category as any,
        config: t.config as unknown as StrategyConfig,
        created_at: t.created_at,
      })));
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    const { error } = await supabase
      .from('strategy_templates')
      .delete()
      .eq('id', id);

    if (error) {
      toast.error('Failed to delete template');
    } else {
      toast.success('Template deleted');
      setUserTemplates(prev => prev.filter(t => t.id !== id));
      setDeleteId(null);
    }
  };

  const handleLoadTemplate = (template: StrategyTemplate) => {
    onSelectTemplate(template.config);
    toast.success(`Loaded: ${template.name}`, {
      description: "Template configuration applied successfully",
    });
  };

  const categories = Array.from(new Set(strategyTemplates.map(t => t.category)));

  const renderTemplateCard = (template: StrategyTemplate, isUserTemplate = false, templateId?: string) => {
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

        <div className="flex gap-2">
          <Button
            onClick={() => handleLoadTemplate(template)}
            className="flex-1 profit-glow"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Load
          </Button>
          {isUserTemplate && templateId && (
            <Button
              onClick={() => setDeleteId(templateId)}
              variant="destructive"
              size="sm"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>
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
        <TabsList className={`w-full grid ${user ? 'grid-cols-6' : 'grid-cols-5'} bg-secondary/50`}>
          <TabsTrigger value="all">All</TabsTrigger>
          {user && (
            <TabsTrigger value="personal">
              <User className="w-4 h-4 mr-1" />
              Personal
            </TabsTrigger>
          )}
          {categories.map((category) => (
            <TabsTrigger key={category} value={category}>
              {category.split(" ")[0]}
            </TabsTrigger>
          ))}
        </TabsList>

        <ScrollArea className="h-[600px] mt-6">
          <TabsContent value="all" className="mt-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
              {user && userTemplates.length > 0 && (
                <>
                  <div className="col-span-full">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <User className="w-5 h-5" />
                      Your Personal Templates
                    </h3>
                  </div>
                  {userTemplates.map(t => renderTemplateCard(t, true, t.id))}
                  <div className="col-span-full border-t border-border my-4" />
                  <div className="col-span-full">
                    <h3 className="text-lg font-semibold">Pre-configured Templates</h3>
                  </div>
                </>
              )}
              {strategyTemplates.map(t => renderTemplateCard(t))}
            </div>
          </TabsContent>

          {user && (
            <TabsContent value="personal" className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
                {userTemplates.length === 0 ? (
                  <div className="col-span-full text-center py-12">
                    <p className="text-muted-foreground">
                      No personal templates yet. Configure a strategy and save it as a template!
                    </p>
                  </div>
                ) : (
                  userTemplates.map(t => renderTemplateCard(t, true, t.id))
                )}
              </div>
            </TabsContent>
          )}

          {categories.map((category) => (
            <TabsContent key={category} value={category} className="mt-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-4">
                {strategyTemplates
                  .filter(t => t.category === category)
                  .map(t => renderTemplateCard(t))}
              </div>
            </TabsContent>
          ))}
        </ScrollArea>
      </Tabs>

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this template? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => deleteId && handleDeleteTemplate(deleteId)}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
