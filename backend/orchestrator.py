"""
QuantStride Orchestrator
Main pipeline orchestration for EA generation.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
import json

from core import (
    StrategyValidator,
    MQLValidator,
    Backtester,
    Optimizer,
    AutoImprover,
)
from templates import (
    BaseEATemplate,
    IndicatorTemplates,
    RiskManagementTemplates,
    TrendFilterTemplates,
    OrderManagementTemplates,
    FilterTemplates,
)
from config import settings


@dataclass
class PipelineResult:
    """Result from the full EA generation pipeline."""
    success: bool
    ea_name: str = ""
    mql5_code: str = ""
    validation_passed: bool = False
    compilation_passed: bool = False
    backtest_passed: bool = False
    
    validation_issues: list = field(default_factory=list)
    compilation_errors: list = field(default_factory=list)
    backtest_metrics: Optional[dict] = None
    
    profitability_score: int = 0
    risk_score: int = 0
    
    backtest_instructions: dict = field(default_factory=dict)
    error_message: str = ""


class Orchestrator:
    """
    Main pipeline orchestrator for EA generation.
    
    Pipeline stages:
    1. Strategy Validation
    2. Code Generation
    3. MQL5 Compilation
    4. Backtesting (optional)
    5. Optimization (optional)
    6. Output Generation
    """
    
    def __init__(self):
        self.validator = StrategyValidator()
        self.compiler = MQLValidator()
        self.backtester = Backtester()
        self.optimizer = Optimizer()
        self.auto_improver = AutoImprover()
    
    def generate_ea(
        self,
        strategy: dict,
        ea_name: str = "QuantStrideEA",
        run_backtest: bool = False,
        auto_improve: bool = False,
    ) -> PipelineResult:
        """
        Run the full EA generation pipeline.
        
        Args:
            strategy: Strategy configuration dictionary
            ea_name: Name for the generated EA
            run_backtest: Whether to run backtesting
            auto_improve: Whether to run auto-improvement
            
        Returns:
            PipelineResult with all outputs
        """
        result = PipelineResult(success=False, ea_name=ea_name)
        
        # Stage 1: Validate strategy
        print(f"[1/5] Validating strategy...")
        validation = self.validator.validate(strategy)
        result.validation_passed = validation.is_valid
        result.validation_issues = [
            {"severity": i.severity.value, "message": i.message}
            for i in validation.issues
        ]
        result.profitability_score = validation.profitability_score
        result.risk_score = validation.risk_score
        
        if not validation.is_valid:
            result.error_message = validation.summary
            return result
        
        # Stage 2: Generate MQL5 code
        print(f"[2/5] Generating MQL5 code...")
        mql5_code = self._generate_code(strategy, ea_name)
        result.mql5_code = mql5_code
        
        # Stage 3: Compile and validate
        print(f"[3/5] Compiling MQL5...")
        compilation = self.compiler.validate(mql5_code, f"{ea_name}.mq5")
        result.compilation_passed = compilation.success
        result.compilation_errors = [
            {"line": e.line, "message": e.message}
            for e in compilation.errors
        ]
        
        if compilation.fixed_code:
            result.mql5_code = compilation.fixed_code
        
        # Stage 4: Backtest (optional)
        if run_backtest and compilation.success:
            print(f"[4/5] Running backtest...")
            result.backtest_metrics, result.backtest_passed = self._run_backtest(
                mql5_code, strategy
            )
        else:
            print(f"[4/5] Skipping backtest...")
        
        # Stage 5: Auto-improve (optional)
        if auto_improve and not result.backtest_passed:
            print(f"[5/5] Running auto-improvement...")
            improvement = self.auto_improver.improve(strategy)
            if improvement.success and improvement.final_mql5_code:
                result.mql5_code = improvement.final_mql5_code
                result.backtest_metrics = improvement.final_metrics
                result.backtest_passed = True
        else:
            print(f"[5/5] Skipping auto-improvement...")
        
        # Generate backtest instructions
        result.backtest_instructions = self._generate_backtest_instructions(strategy)
        
        result.success = result.validation_passed and result.compilation_passed
        
        return result
    
    def _generate_code(self, strategy: dict, ea_name: str) -> str:
        """Generate MQL5 code from strategy configuration."""
        # Build indicator initialization
        indicator_init = self._build_indicator_init(strategy)
        
        # Build indicator cleanup
        cleanup_code = self._build_indicator_cleanup(strategy)
        
        # Build tick logic
        tick_logic = self._build_tick_logic(strategy)
        
        # Generate full EA
        code = BaseEATemplate.generate_full_skeleton(
            ea_name=ea_name,
            indicator_init=indicator_init,
            cleanup_code=cleanup_code,
            tick_logic=tick_logic
        )
        
        return code
    
    def _build_indicator_init(self, strategy: dict) -> str:
        """Build indicator initialization code."""
        init_code = []
        
        indicators = strategy.get("indicators", [])
        for i, ind in enumerate(indicators):
            ind_type = ind.get("type", "")
            params = ind.get("params", {})
            handle_name = f"handle_{ind_type.lower()}_{i}"
            
            template_result = IndicatorTemplates.generate_for_indicator(
                ind_type, handle_name, params
            )
            
            if template_result["init"]:
                init_code.append(template_result["init"])
        
        return "\n".join(init_code)
    
    def _build_indicator_cleanup(self, strategy: dict) -> str:
        """Build indicator release code."""
        cleanup_code = []
        
        indicators = strategy.get("indicators", [])
        for i, ind in enumerate(indicators):
            ind_type = ind.get("type", "")
            handle_name = f"handle_{ind_type.lower()}_{i}"
            cleanup_code.append(f"   IndicatorRelease({handle_name});")
        
        return "\n".join(cleanup_code)
    
    def _build_tick_logic(self, strategy: dict) -> str:
        """Build OnTick logic from entry/exit conditions."""
        tick_code = []
        
        # Add price data arrays
        tick_code.append(IndicatorTemplates.generate_price_arrays())
        tick_code.append("")
        
        # Add indicator buffer reads
        indicators = strategy.get("indicators", [])
        for i, ind in enumerate(indicators):
            ind_type = ind.get("type", "")
            params = ind.get("params", {})
            handle_name = f"handle_{ind_type.lower()}_{i}"
            
            template_result = IndicatorTemplates.generate_for_indicator(
                ind_type, handle_name, params
            )
            
            if template_result["read"]:
                tick_code.append(template_result["read"])
                tick_code.append("")
        
        # Add signal checking
        tick_code.append("   // Check filters")
        tick_code.append("   if(!PassesAllFilters()) return;")
        tick_code.append("")
        tick_code.append("   // Check entry signals")
        tick_code.append("   ENUM_SIGNAL_TYPE signal = CheckEntryConditions();")
        tick_code.append("   ")
        tick_code.append("   if(signal == SIGNAL_BUY)")
        tick_code.append("   {")
        tick_code.append("      LogMessage(\"BUY signal detected\");")
        tick_code.append(f"      OpenBuyOrder(CalculateLotSize(StopLossPips), StopLossPips, StopLossPips * TakeProfitRatio);")
        tick_code.append("   }")
        tick_code.append("   else if(signal == SIGNAL_SELL)")
        tick_code.append("   {")
        tick_code.append("      LogMessage(\"SELL signal detected\");")
        tick_code.append(f"      OpenSellOrder(CalculateLotSize(StopLossPips), StopLossPips, StopLossPips * TakeProfitRatio);")
        tick_code.append("   }")
        
        return "\n".join(tick_code)
    
    def _run_backtest(
        self,
        mql5_code: str,
        strategy: dict
    ) -> tuple[Optional[dict], bool]:
        """Run backtest and return metrics."""
        import tempfile
        import os
        
        # Save EA to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.mq5', delete=False
        ) as f:
            f.write(mql5_code)
            ea_path = f.name
        
        try:
            # Get symbol and timeframe from strategy
            symbols = strategy.get("instruments", ["EURUSD"])
            symbol = symbols[0] if symbols else "EURUSD"
            timeframe = strategy.get("timeframe", "5m")
            
            # Run backtest
            result = self.backtester.run_backtest(
                ea_path=ea_path,
                symbol=symbol,
                timeframe=timeframe
            )
            
            if result.success:
                metrics = {
                    "profit_factor": result.metrics.profit_factor,
                    "win_rate": result.metrics.win_rate,
                    "net_profit": result.metrics.total_net_profit,
                    "max_drawdown": result.metrics.max_drawdown_percent,
                    "total_trades": result.metrics.total_trades,
                    "sharpe_ratio": result.metrics.sharpe_ratio,
                }
                return metrics, result.passed_criteria
            
            return None, False
            
        finally:
            try:
                os.unlink(ea_path)
            except:
                pass
    
    def _generate_backtest_instructions(self, strategy: dict) -> dict:
        """Generate recommended backtest settings."""
        symbols = strategy.get("instruments", ["EURUSD"])
        timeframe = strategy.get("timeframe", "5m")
        
        return {
            "symbol": symbols[0] if symbols else "EURUSD",
            "timeframe": timeframe,
            "period": {
                "start": settings.BACKTEST_START_DATE,
                "end": settings.BACKTEST_END_DATE
            },
            "settings": {
                "spread": settings.DEFAULT_SPREAD,
                "modeling": "Every tick",
                "deposit": 10000,
                "leverage": 100
            },
            "optimization_params": [
                {"name": "RiskPercent", "start": 0.5, "end": 3.0, "step": 0.5},
                {"name": "StopLossPips", "start": 10, "end": 50, "step": 5},
                {"name": "TakeProfitRatio", "start": 1.5, "end": 3.0, "step": 0.5},
            ],
            "criteria": {
                "min_profit_factor": settings.MIN_PROFIT_FACTOR,
                "max_drawdown": settings.MAX_DRAWDOWN_PERCENT,
                "min_trades": settings.MIN_TOTAL_TRADES
            }
        }
    
    def save_ea(self, result: PipelineResult, output_dir: Path = None) -> str:
        """Save generated EA to file."""
        output_dir = output_dir or settings.EA_OUTPUT_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save MQL5 file
        ea_path = output_dir / f"{result.ea_name}.mq5"
        ea_path.write_text(result.mql5_code, encoding="utf-8")
        
        # Save metadata
        meta_path = output_dir / f"{result.ea_name}_meta.json"
        meta = {
            "ea_name": result.ea_name,
            "validation_passed": result.validation_passed,
            "compilation_passed": result.compilation_passed,
            "backtest_passed": result.backtest_passed,
            "profitability_score": result.profitability_score,
            "risk_score": result.risk_score,
            "backtest_metrics": result.backtest_metrics,
            "backtest_instructions": result.backtest_instructions
        }
        meta_path.write_text(json.dumps(meta, indent=2))
        
        return str(ea_path)


# CLI interface
if __name__ == "__main__":
    import sys
    
    # Example usage
    sample_strategy = {
        "instruments": ["EURUSD"],
        "timeframe": "5m",
        "accountSize": 10000,
        "dailyTarget": 100,
        "sessions": ["london", "newyork"],
        "indicators": [
            {"id": "ema_8", "name": "EMA 8", "type": "EMA", "params": {"period": 8}},
            {"id": "ema_21", "name": "EMA 21", "type": "EMA", "params": {"period": 21}},
            {"id": "rsi", "name": "RSI", "type": "RSI", "params": {"period": 14}},
        ],
        "entries": [
            {"id": "buy", "description": "Buy signal", "logic": "EMA8 > EMA21 && RSI > 50"},
            {"id": "sell", "description": "Sell signal", "logic": "EMA8 < EMA21 && RSI < 50"},
        ],
        "exits": [
            {"id": "ema_cross", "description": "Exit on EMA cross", "logic": "EMA cross against position"}
        ],
        "stopLoss": {"type": "fixed", "pips": 20},
        "takeProfit": {"type": "rr", "ratio": 2},
        "maxDailyLoss": 100,
        "positionSizePercent": 1
    }
    
    orchestrator = Orchestrator()
    result = orchestrator.generate_ea(
        strategy=sample_strategy,
        ea_name="SampleEA",
        run_backtest=False
    )
    
    print(f"\n{'='*50}")
    print(f"EA Generation Result")
    print(f"{'='*50}")
    print(f"Success: {result.success}")
    print(f"Validation: {'✓' if result.validation_passed else '✗'}")
    print(f"Compilation: {'✓' if result.compilation_passed else '✗'}")
    print(f"Profitability Score: {result.profitability_score}/100")
    print(f"Risk Score: {result.risk_score}/100")
    
    if result.success:
        print(f"\nMQL5 Code Length: {len(result.mql5_code)} characters")
        print(f"\nFirst 500 chars of generated code:")
        print(result.mql5_code[:500])
