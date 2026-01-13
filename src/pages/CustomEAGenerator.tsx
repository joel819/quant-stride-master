import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Download, Copy, Sparkles, TrendingUp, Shield, Clock, BrainCircuit } from 'lucide-react';

interface EASettings {
    ea_name: string;
    symbol: string;
    ema_fast_period: number;
    ema_slow_period: number;
    use_trend_filter: boolean;
    rsi_period: number;
    rsi_buy_min: number;
    rsi_buy_max: number;
    rsi_sell_min: number;
    rsi_sell_max: number;
    use_macd_confirmation: boolean;
    pullback_distance_pips: number;
    risk_percent: number;
    risk_reward_ratio: number;
    min_sl_pips: number;
    max_sl_pips: number;
    use_breakeven: boolean;
    breakeven_trigger_pips: number;
    breakeven_offset_pips: number;
    use_trailing_stop: boolean;
    trailing_stop_type: 'fixed' | 'atr' | 'step';
    trailing_start_pips: number;
    trailing_distance_pips: number;
    atr_period: number;
    atr_multiplier: number;
    step_size_pips: number;
    step_distance_pips: number;
    max_spread_points: number;
    use_trading_hours: boolean;
    trading_hour_start: number;
    trading_hour_end: number;
    use_news_filter: boolean;
    use_partial_close: boolean;
    partial_close_percent: number;
    partial_close_tp1_rr: number;
    partial_close_tp2_rr: number;
    move_sl_after_partial: boolean;
}

interface Preset {
    name: string;
    symbol: string;
    description: string;
    settings: Partial<EASettings>;
}

const API_BASE = 'http://localhost:8000/api';

const defaultSettings: EASettings = {
    ea_name: 'MyCustomEA',
    symbol: 'EURUSD',
    ema_fast_period: 50,
    ema_slow_period: 200,
    use_trend_filter: true,
    rsi_period: 14,
    rsi_buy_min: 30,
    rsi_buy_max: 45,
    rsi_sell_min: 55,
    rsi_sell_max: 70,
    use_macd_confirmation: true,
    pullback_distance_pips: 30,
    risk_percent: 1.0,
    risk_reward_ratio: 2.0,
    min_sl_pips: 20,
    max_sl_pips: 100,
    use_breakeven: true,
    breakeven_trigger_pips: 20,
    breakeven_offset_pips: 2,
    use_trailing_stop: false,
    trailing_stop_type: 'fixed',
    trailing_start_pips: 30,
    trailing_distance_pips: 20,
    atr_period: 14,
    atr_multiplier: 1.5,
    step_size_pips: 10,
    step_distance_pips: 10,
    max_spread_points: 20,
    use_trading_hours: true,
    trading_hour_start: 8,
    trading_hour_end: 18,
    use_news_filter: true,
    use_partial_close: false,
    partial_close_percent: 50,
    partial_close_tp1_rr: 1.0,
    partial_close_tp2_rr: 2.0,
    move_sl_after_partial: true,
};

interface Props {
    isEmbedded?: boolean;
}

export default function CustomEAGenerator({ isEmbedded = false }: Props) {
    const [settings, setSettings] = useState<EASettings>(defaultSettings);
    const [presets, setPresets] = useState<Preset[]>([]);
    const [generatedCode, setGeneratedCode] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [filePath, setFilePath] = useState<string>('');
    const [aiPrompt, setAiPrompt] = useState('');
    const [isAiLoading, setIsAiLoading] = useState(false);
    const [isAiOpen, setIsAiOpen] = useState(false);
    const { toast } = useToast();

    // Fetch presets on mount
    useState(() => {
        fetch(`${API_BASE}/presets`)
            .then(res => res.json())
            .then(data => setPresets(data.presets || []))
            .catch(err => console.error('Failed to load presets:', err));
    });

    const handlePresetSelect = (presetName: string) => {
        const preset = presets.find(p => p.name === presetName);
        if (preset) {
            setSettings({
                ...defaultSettings,
                ...preset.settings,
                ea_name: preset.name,
                symbol: preset.symbol,
            });
            toast({
                title: 'Preset Loaded',
                description: `${preset.name} settings applied`,
            });
        }
    };

    const generateEA = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE}/generate-custom-ea`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            });

            const data = await response.json();

            if (data.status === 'success') {
                setGeneratedCode(data.mql5_code);
                setFilePath(data.file_path);
                toast({
                    title: '✅ EA Generated Successfully!',
                    description: `${data.ea_name}.mq5 (${data.code_length.toLocaleString()} chars)`,
                });
            } else {
                throw new Error(data.message || 'Generation failed');
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: error instanceof Error ? error.message : 'Failed to generate EA',
                variant: 'destructive',
            });
        } finally {
            setIsLoading(false);
        }
    };




    const handleAiAssist = async () => {
        if (!aiPrompt.trim()) return;
        setIsAiLoading(true);
        try {
            const response = await fetch(`${API_BASE}/ai-assist`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: aiPrompt }),
            });

            const newSettings = await response.json();

            if (newSettings && typeof newSettings === 'object') {
                setSettings({ ...defaultSettings, ...newSettings });
                toast({
                    title: '🤖 Strategy Generated!',
                    description: 'AI has configured your EA settings.',
                });
                setIsAiOpen(false);
            } else {
                throw new Error('Invalid response from AI');
            }
        } catch (error) {
            toast({
                title: 'AI Error',
                description: 'Failed to generate strategy. Check API Key.',
                variant: 'destructive',
            });
        } finally {
            setIsAiLoading(false);
        }
    };

    const copyCode = () => {
        navigator.clipboard.writeText(generatedCode);
        toast({ title: 'Copied!', description: 'Code copied to clipboard' });
    };

    const downloadCode = () => {
        const blob = new Blob([generatedCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${settings.ea_name}.mq5`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const content = (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header - Only show if not embedded */}
            {!isEmbedded && (
                <div className="text-center space-y-2">
                    <h1 className="text-4xl font-bold text-white flex items-center justify-center gap-3">
                        <Sparkles className="h-10 w-10 text-yellow-400" />
                        Custom EA Generator
                    </h1>
                    <p className="text-slate-300">
                        Generate production-quality Expert Advisors for any symbol
                    </p>
                </div>
            )}

            {/* Presets */}
            <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-400" />
                        Quick Presets
                    </CardTitle>
                    <Dialog open={isAiOpen} onOpenChange={setIsAiOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="bg-purple-900/50 border-purple-500/50 hover:bg-purple-900 text-purple-200">
                                <BrainCircuit className="w-4 h-4 mr-2 text-purple-400" />
                                AI Assistant
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-slate-900 border-slate-700 text-slate-100">
                            <DialogHeader>
                                <DialogTitle className="flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-purple-400" />
                                    AI Strategy Designer
                                </DialogTitle>
                                <DialogDescription className="text-slate-400">
                                    Describe your strategy in plain English. The AI will configure all technical indicators, risk settings, and logic for you.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <Textarea
                                    placeholder="Example: Create a conservative Gold scalper that trades M5 pullbacks. Use EMA 50/200 for trend, RSI for entry, and a trailing stop of 20 pips. Risk 1% per trade."
                                    value={aiPrompt}
                                    onChange={(e) => setAiPrompt(e.target.value)}
                                    className="h-32 bg-slate-800 border-slate-600 text-slate-100 placeholder:text-slate-500"
                                />
                                <div className="text-xs text-slate-500">
                                    💡 Tip: Be specific about indicators (RSI, MACD), risk (%), and trading style.
                                </div>
                            </div>
                            <DialogFooter>
                                <Button
                                    onClick={handleAiAssist}
                                    disabled={isAiLoading || !aiPrompt.trim()}
                                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600"
                                >
                                    {isAiLoading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Designing Strategy...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4 mr-2" />
                                            Generate Settings
                                        </>
                                    )}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-3">
                        {presets.map(preset => (
                            <Button
                                key={preset.name}
                                variant="outline"
                                className="border-slate-600 hover:bg-slate-700"
                                onClick={() => handlePresetSelect(preset.name)}
                            >
                                <Badge variant="secondary" className="mr-2">{preset.symbol}</Badge>
                                {preset.name.replace('_', ' ')}
                            </Button>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Settings Panel */}
                <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                        <CardTitle className="text-white">EA Configuration</CardTitle>
                        <CardDescription>Customize your Expert Advisor settings</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Tabs defaultValue="general" className="space-y-4">
                            <TabsList className="grid grid-cols-4 bg-slate-700">
                                <TabsTrigger value="general">General</TabsTrigger>
                                <TabsTrigger value="entry">Entry</TabsTrigger>
                                <TabsTrigger value="risk">Risk</TabsTrigger>
                                <TabsTrigger value="filters">Filters</TabsTrigger>
                            </TabsList>

                            {/* General Tab */}
                            <TabsContent value="general" className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-slate-300">EA Name</Label>
                                        <Input
                                            value={settings.ea_name}
                                            onChange={e => setSettings({ ...settings, ea_name: e.target.value })}
                                            className="bg-slate-700 border-slate-600"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-slate-300">Symbol</Label>
                                        <Select
                                            value={settings.symbol}
                                            onValueChange={val => setSettings({ ...settings, symbol: val })}
                                        >
                                            <SelectTrigger className="bg-slate-700 border-slate-600">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="XAUUSD">XAUUSD (Gold)</SelectItem>
                                                <SelectItem value="EURUSD">EURUSD</SelectItem>
                                                <SelectItem value="GBPUSD">GBPUSD</SelectItem>
                                                <SelectItem value="USDJPY">USDJPY</SelectItem>
                                                <SelectItem value="BTCUSD">BTCUSD</SelectItem>
                                                <SelectItem value="US30">US30 (Dow Jones)</SelectItem>
                                                <SelectItem value="NAS100">NAS100</SelectItem>
                                                <SelectItem value="Volatility 75 Index">V75 Index</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-slate-300">Fast EMA Period: {settings.ema_fast_period}</Label>
                                    <Slider
                                        value={[settings.ema_fast_period]}
                                        onValueChange={([val]) => setSettings({ ...settings, ema_fast_period: val })}
                                        min={5} max={100} step={1}
                                        className="py-2"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-slate-300">Slow EMA Period: {settings.ema_slow_period}</Label>
                                    <Slider
                                        value={[settings.ema_slow_period]}
                                        onValueChange={([val]) => setSettings({ ...settings, ema_slow_period: val })}
                                        min={20} max={500} step={5}
                                        className="py-2"
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <Label className="text-slate-300">Use Trend Filter (EMA)</Label>
                                    <Switch
                                        checked={settings.use_trend_filter}
                                        onCheckedChange={val => setSettings({ ...settings, use_trend_filter: val })}
                                    />
                                </div>
                            </TabsContent>

                            {/* Entry Tab */}
                            <TabsContent value="entry" className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="text-slate-300">RSI Buy Zone: {settings.rsi_buy_min} - {settings.rsi_buy_max}</Label>
                                    <div className="flex gap-4">
                                        <Slider
                                            value={[settings.rsi_buy_min]}
                                            onValueChange={([val]) => setSettings({ ...settings, rsi_buy_min: val })}
                                            min={10} max={50} step={1}
                                        />
                                        <Slider
                                            value={[settings.rsi_buy_max]}
                                            onValueChange={([val]) => setSettings({ ...settings, rsi_buy_max: val })}
                                            min={20} max={60} step={1}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-slate-300">RSI Sell Zone: {settings.rsi_sell_min} - {settings.rsi_sell_max}</Label>
                                    <div className="flex gap-4">
                                        <Slider
                                            value={[settings.rsi_sell_min]}
                                            onValueChange={([val]) => setSettings({ ...settings, rsi_sell_min: val })}
                                            min={40} max={80} step={1}
                                        />
                                        <Slider
                                            value={[settings.rsi_sell_max]}
                                            onValueChange={([val]) => setSettings({ ...settings, rsi_sell_max: val })}
                                            min={50} max={90} step={1}
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center justify-between">
                                    <Label className="text-slate-300">Use MACD Confirmation</Label>
                                    <Switch
                                        checked={settings.use_macd_confirmation}
                                        onCheckedChange={val => setSettings({ ...settings, use_macd_confirmation: val })}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-slate-300">Pullback Distance: {settings.pullback_distance_pips} pips</Label>
                                    <Slider
                                        value={[settings.pullback_distance_pips]}
                                        onValueChange={([val]) => setSettings({ ...settings, pullback_distance_pips: val })}
                                        min={5} max={200} step={5}
                                    />
                                </div>
                            </TabsContent>

                            {/* Risk Tab */}
                            <TabsContent value="risk" className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Risk per Trade: {settings.risk_percent}%</Label>
                                    <Slider
                                        value={[settings.risk_percent]}
                                        onValueChange={([val]) => setSettings({ ...settings, risk_percent: val })}
                                        min={0.1} max={5} step={0.1}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-slate-300">Risk:Reward Ratio: 1:{settings.risk_reward_ratio}</Label>
                                    <Slider
                                        value={[settings.risk_reward_ratio]}
                                        onValueChange={([val]) => setSettings({ ...settings, risk_reward_ratio: val })}
                                        min={1} max={5} step={0.1}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-slate-300">Min SL (pips)</Label>
                                        <Input
                                            type="number"
                                            value={settings.min_sl_pips}
                                            onChange={e => setSettings({ ...settings, min_sl_pips: Number(e.target.value) })}
                                            className="bg-slate-700 border-slate-600"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-slate-300">Max SL (pips)</Label>
                                        <Input
                                            type="number"
                                            value={settings.max_sl_pips}
                                            onChange={e => setSettings({ ...settings, max_sl_pips: Number(e.target.value) })}
                                            className="bg-slate-700 border-slate-600"
                                        />
                                    </div>
                                </div>

                                {/* Breakeven Settings */}
                                <div className="space-y-3 p-3 bg-slate-700/50 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-slate-300 font-medium">Auto Breakeven</Label>
                                        <Switch
                                            checked={settings.use_breakeven}
                                            onCheckedChange={val => setSettings({ ...settings, use_breakeven: val })}
                                        />
                                    </div>

                                    {settings.use_breakeven && (
                                        <div className="grid grid-cols-2 gap-3 pt-2">
                                            <div className="space-y-2">
                                                <Label className="text-slate-400 text-sm">Trigger (pips)</Label>
                                                <Input
                                                    type="number"
                                                    value={settings.breakeven_trigger_pips}
                                                    onChange={e => setSettings({ ...settings, breakeven_trigger_pips: Number(e.target.value) })}
                                                    className="bg-slate-700 border-slate-600"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label className="text-slate-400 text-sm">Offset (pips)</Label>
                                                <Input
                                                    type="number"
                                                    value={settings.breakeven_offset_pips}
                                                    onChange={e => setSettings({ ...settings, breakeven_offset_pips: Number(e.target.value) })}
                                                    className="bg-slate-700 border-slate-600"
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Advanced Trailing Stop Settings */}
                                <div className="space-y-3 p-3 bg-slate-700/50 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-slate-300 font-medium">Advanced Trailing Stop</Label>
                                        <Switch
                                            checked={settings.use_trailing_stop}
                                            onCheckedChange={val => setSettings({ ...settings, use_trailing_stop: val })}
                                        />
                                    </div>

                                    {settings.use_trailing_stop && (
                                        <div className="space-y-4 pt-2">
                                            <div className="space-y-2">
                                                <Label className="text-slate-400 text-sm">Trailing Type</Label>
                                                <Select
                                                    value={settings.trailing_stop_type}
                                                    onValueChange={(val: 'fixed' | 'atr' | 'step') => setSettings({ ...settings, trailing_stop_type: val })}
                                                >
                                                    <SelectTrigger className="bg-slate-700 border-slate-600">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="fixed">Fixed Distance</SelectItem>
                                                        <SelectItem value="atr">ATR-Based (Dynamic)</SelectItem>
                                                        <SelectItem value="step">Step-Wise</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>

                                            <div className="space-y-2">
                                                <Label className="text-slate-400 text-sm">Start After (pips): {settings.trailing_start_pips}</Label>
                                                <Slider
                                                    value={[settings.trailing_start_pips]}
                                                    onValueChange={([val]) => setSettings({ ...settings, trailing_start_pips: val })}
                                                    min={5} max={100} step={5}
                                                />
                                            </div>

                                            {settings.trailing_stop_type === 'fixed' && (
                                                <div className="space-y-2">
                                                    <Label className="text-slate-400 text-sm">Trail Distance (pips): {settings.trailing_distance_pips}</Label>
                                                    <Slider
                                                        value={[settings.trailing_distance_pips]}
                                                        onValueChange={([val]) => setSettings({ ...settings, trailing_distance_pips: val })}
                                                        min={5} max={100} step={5}
                                                    />
                                                </div>
                                            )}

                                            {settings.trailing_stop_type === 'atr' && (
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div className="space-y-2">
                                                        <Label className="text-slate-400 text-sm">ATR Period</Label>
                                                        <Input
                                                            type="number"
                                                            value={settings.atr_period}
                                                            onChange={e => setSettings({ ...settings, atr_period: Number(e.target.value) })}
                                                            className="bg-slate-700 border-slate-600"
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <Label className="text-slate-400 text-sm">ATR Multiplier</Label>
                                                        <Input
                                                            type="number"
                                                            step="0.1"
                                                            value={settings.atr_multiplier}
                                                            onChange={e => setSettings({ ...settings, atr_multiplier: Number(e.target.value) })}
                                                            className="bg-slate-700 border-slate-600"
                                                        />
                                                    </div>
                                                </div>
                                            )}

                                            {settings.trailing_stop_type === 'step' && (
                                                <div className="grid grid-cols-2 gap-3">
                                                    <div className="space-y-2">
                                                        <Label className="text-slate-400 text-sm">Step Size (pips)</Label>
                                                        <Input
                                                            type="number"
                                                            value={settings.step_size_pips}
                                                            onChange={e => setSettings({ ...settings, step_size_pips: Number(e.target.value) })}
                                                            className="bg-slate-700 border-slate-600"
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <Label className="text-slate-400 text-sm">Step Distance (pips)</Label>
                                                        <Input
                                                            type="number"
                                                            value={settings.step_distance_pips}
                                                            onChange={e => setSettings({ ...settings, step_distance_pips: Number(e.target.value) })}
                                                            className="bg-slate-700 border-slate-600"
                                                        />
                                                    </div>
                                                </div>
                                            )}

                                            <div className="text-xs text-slate-400 bg-slate-800 p-2 rounded">
                                                {settings.trailing_stop_type === 'fixed' && (
                                                    <span>Fixed: Trail stop follows price at a constant distance</span>
                                                )}
                                                {settings.trailing_stop_type === 'atr' && (
                                                    <span>ATR: Trail distance adapts to market volatility (ATR × Multiplier)</span>
                                                )}
                                                {settings.trailing_stop_type === 'step' && (
                                                    <span>Step: Stop moves in discrete steps as price advances by step size</span>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Partial Close Settings */}
                                <div className="space-y-3 p-3 bg-slate-700/50 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-slate-300 font-medium">Partial Close (Scale Out)</Label>
                                        <Switch
                                            checked={settings.use_partial_close}
                                            onCheckedChange={val => setSettings({ ...settings, use_partial_close: val })}
                                        />
                                    </div>

                                    {settings.use_partial_close && (
                                        <div className="space-y-4 pt-2">
                                            <div className="space-y-2">
                                                <Label className="text-slate-400 text-sm">Close % at TP1: {settings.partial_close_percent}%</Label>
                                                <Slider
                                                    value={[settings.partial_close_percent]}
                                                    onValueChange={([val]) => setSettings({ ...settings, partial_close_percent: val })}
                                                    min={25} max={75} step={5}
                                                />
                                            </div>

                                            <div className="grid grid-cols-2 gap-3">
                                                <div className="space-y-2">
                                                    <Label className="text-slate-400 text-sm">TP1 (R:R)</Label>
                                                    <Input
                                                        type="number"
                                                        step="0.1"
                                                        value={settings.partial_close_tp1_rr}
                                                        onChange={e => setSettings({ ...settings, partial_close_tp1_rr: Number(e.target.value) })}
                                                        className="bg-slate-700 border-slate-600"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label className="text-slate-400 text-sm">TP2 (R:R)</Label>
                                                    <Input
                                                        type="number"
                                                        step="0.1"
                                                        value={settings.partial_close_tp2_rr}
                                                        onChange={e => setSettings({ ...settings, partial_close_tp2_rr: Number(e.target.value) })}
                                                        className="bg-slate-700 border-slate-600"
                                                    />
                                                </div>
                                            </div>

                                            <div className="flex items-center justify-between">
                                                <Label className="text-slate-400 text-sm">Move SL to Entry After TP1</Label>
                                                <Switch
                                                    checked={settings.move_sl_after_partial}
                                                    onCheckedChange={val => setSettings({ ...settings, move_sl_after_partial: val })}
                                                />
                                            </div>

                                            <div className="text-xs text-slate-400 bg-slate-800 p-2 rounded">
                                                <span>
                                                    Example: Close {settings.partial_close_percent}% at {settings.partial_close_tp1_rr}R,
                                                    let remaining {100 - settings.partial_close_percent}% run to {settings.partial_close_tp2_rr}R
                                                    {settings.move_sl_after_partial && " (SL moves to breakeven after TP1)"}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </TabsContent>

                            {/* Filters Tab */}
                            <TabsContent value="filters" className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Max Spread: {settings.max_spread_points} points</Label>
                                    <Slider
                                        value={[settings.max_spread_points]}
                                        onValueChange={([val]) => setSettings({ ...settings, max_spread_points: val })}
                                        min={5} max={100} step={5}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-blue-400" />
                                        <Label className="text-slate-300">Trading Hours Filter</Label>
                                    </div>
                                    <Switch
                                        checked={settings.use_trading_hours}
                                        onCheckedChange={val => setSettings({ ...settings, use_trading_hours: val })}
                                    />
                                </div>

                                {settings.use_trading_hours && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label className="text-slate-300">Start Hour (UTC)</Label>
                                            <Input
                                                type="number"
                                                value={settings.trading_hour_start}
                                                onChange={e => setSettings({ ...settings, trading_hour_start: Number(e.target.value) })}
                                                className="bg-slate-700 border-slate-600"
                                                min={0} max={23}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-slate-300">End Hour (UTC)</Label>
                                            <Input
                                                type="number"
                                                value={settings.trading_hour_end}
                                                onChange={e => setSettings({ ...settings, trading_hour_end: Number(e.target.value) })}
                                                className="bg-slate-700 border-slate-600"
                                                min={0} max={23}
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Shield className="h-4 w-4 text-yellow-400" />
                                        <Label className="text-slate-300">News Filter (NFP, FOMC)</Label>
                                    </div>
                                    <Switch
                                        checked={settings.use_news_filter}
                                        onCheckedChange={val => setSettings({ ...settings, use_news_filter: val })}
                                    />
                                </div>
                            </TabsContent>
                        </Tabs>

                        <Button
                            onClick={generateEA}
                            disabled={isLoading}
                            className="w-full mt-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                            size="lg"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="mr-2 h-5 w-5" />
                                    Generate EA
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* Code Preview */}
                <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <CardTitle className="text-white">Generated Code</CardTitle>
                            {generatedCode && (
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" onClick={copyCode}>
                                        <Copy className="h-4 w-4 mr-1" /> Copy
                                    </Button>
                                    <Button variant="outline" size="sm" onClick={downloadCode}>
                                        <Download className="h-4 w-4 mr-1" /> Download
                                    </Button>
                                </div>
                            )}
                        </div>
                        {filePath && (
                            <CardDescription className="text-green-400">
                                ✓ Saved to: {filePath}
                            </CardDescription>
                        )}
                    </CardHeader>
                    <CardContent>
                        <div className="bg-slate-900 rounded-lg p-4 h-[600px] overflow-auto">
                            {generatedCode ? (
                                <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                                    {generatedCode.substring(0, 5000)}
                                    {generatedCode.length > 5000 && '\n\n... (truncated for preview)'}
                                </pre>
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-500">
                                    <div className="text-center">
                                        <Sparkles className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                        <p>Configure your EA and click Generate</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );

    if (isEmbedded) {
        return content;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
            {content}
        </div>
    );
}
