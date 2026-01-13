"""
Auto-Improver
Automatic improvement loop: generate → validate → compile → backtest → improve.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import copy
import random

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from .strategy_validator import StrategyValidator, ValidationResult
from .mql_validator import MQLValidator, CompilationResult
from .backtester import Backtester, BacktestResult
from .optimizer import Optimizer


class ImprovementAction(str, Enum):
    """Types of improvements applied."""
    ADJUST_PARAMETERS = "adjust_parameters"
    ADD_FILTER = "add_filter"
    MODIFY_RISK = "modify_risk"
    CHANGE_TIMEFRAME = "change_timeframe"
    ADD_INDICATOR = "add_indicator"
    TIGHTEN_ENTRIES = "tighten_entries"
    ADJUST_SL_TP = "adjust_sl_tp"


@dataclass
class ImprovementAttempt:
    """Record of a single improvement attempt."""
    iteration: int
    action: ImprovementAction
    changes_made: dict
    validation_result: Optional[ValidationResult] = None
    compilation_result: Optional[CompilationResult] = None
    backtest_result: Optional[BacktestResult] = None
    improvement_score: float = 0.0
    success: bool = False


@dataclass
class ImprovementResult:
    """Final result from auto-improvement loop."""
    success: bool
    original_strategy: dict = field(default_factory=dict)
    improved_strategy: Optional[dict] = None
    final_mql5_code: str = ""
    iterations: int = 0
    attempts: list[ImprovementAttempt] = field(default_factory=list)
    final_metrics: Optional[dict] = None
    improvement_summary: str = ""
    error_message: str = ""
    
    @property
    def improvement_percent(self) -> float:
        """Percent improvement from original."""
        if len(self.attempts) < 2:
            return 0.0
        
        first_score = self.attempts[0].improvement_score
        last_score = self.attempts[-1].improvement_score
        
        if first_score <= 0:
            return 0.0
        
        return ((last_score - first_score) / first_score) * 100


class AutoImprover:
    """
    Automatic strategy improvement engine.
    
    Pipeline:
    1. Generate EA from strategy
    2. Validate strategy logic
    3. Compile MQL5 code
    4. Run backtest
    5. If weak → apply improvements → retry
    6. Return best configuration
    """
    
    # Improvement thresholds
    WEAK_PROFIT_FACTOR = 1.5
    WEAK_WIN_RATE = 45.0
    WEAK_DRAWDOWN = 30.0
    
    def __init__(
        self,
        code_generator: Callable[[dict], str] = None,
        max_iterations: int = None,
    ):
        """
        Initialize auto-improver.
        
        Args:
            code_generator: Function that generates MQL5 code from strategy dict
            max_iterations: Maximum improvement iterations
        """
        self.code_generator = code_generator
        self.max_iterations = max_iterations or settings.MAX_IMPROVEMENT_ITERATIONS
        
        # Initialize components
        self.strategy_validator = StrategyValidator()
        self.mql_validator = MQLValidator()
        self.backtester = Backtester()
        self.optimizer = Optimizer()
    
    def improve(
        self,
        strategy: dict,
        symbol: str = None,
        timeframe: str = None,
    ) -> ImprovementResult:
        """
        Run the full improvement loop on a strategy.
        
        Args:
            strategy: Strategy configuration dictionary
            symbol: Override symbol for backtesting
            timeframe: Override timeframe for backtesting
            
        Returns:
            ImprovementResult with the best strategy found
        """
        result = ImprovementResult(
            success=False,
            original_strategy=copy.deepcopy(strategy)
        )
        
        current_strategy = copy.deepcopy(strategy)
        best_strategy = None
        best_score = 0.0
        
        for iteration in range(self.max_iterations):
            attempt = ImprovementAttempt(
                iteration=iteration + 1,
                action=ImprovementAction.ADJUST_PARAMETERS,
                changes_made={}
            )
            
            # Step 1: Validate strategy logic
            validation = self.strategy_validator.validate(current_strategy)
            attempt.validation_result = validation
            
            if not validation.is_valid:
                # Try to fix validation errors
                fixed_strategy = self._fix_validation_errors(current_strategy, validation)
                if fixed_strategy:
                    current_strategy = fixed_strategy
                    attempt.changes_made["validation_fixes"] = [
                        e.message for e in validation.errors
                    ]
                else:
                    result.error_message = f"Cannot fix validation errors: {validation.summary}"
                    result.attempts.append(attempt)
                    break
            
            # Step 2: Generate MQL5 code
            if self.code_generator:
                mql5_code = self.code_generator(current_strategy)
            else:
                # Use built-in template generation
                mql5_code = self._generate_basic_ea(current_strategy)
            
            # Step 3: Compile and validate MQL5
            compilation = self.mql_validator.validate(mql5_code)
            attempt.compilation_result = compilation
            
            if not compilation.success:
                # Check if there are auto-fixes available
                if compilation.fixed_code:
                    mql5_code = compilation.fixed_code
                    attempt.changes_made["compilation_fixes"] = [
                        e.message for e in compilation.errors if e.auto_fixable
                    ]
                else:
                    result.error_message = f"Compilation failed: {self.mql_validator.get_error_summary(compilation)}"
                    result.attempts.append(attempt)
                    break
            
            # Step 4: Run backtest
            # Save temporary EA file for backtesting
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mq5", delete=False
            ) as ea_file:
                ea_file.write(mql5_code)
                ea_path = ea_file.name
            
            backtest = self.backtester.run_backtest(
                ea_path=ea_path,
                symbol=symbol or current_strategy.get("instruments", ["EURUSD"])[0],
                timeframe=timeframe or current_strategy.get("timeframe", "5m"),
            )
            attempt.backtest_result = backtest
            
            # Clean up temp file
            import os
            try:
                os.unlink(ea_path)
            except:
                pass
            
            if not backtest.success:
                result.error_message = f"Backtest failed: {backtest.error_message}"
                result.attempts.append(attempt)
                continue
            
            # Step 5: Evaluate performance
            attempt.improvement_score = self._calculate_strategy_score(backtest)
            
            # Track best result
            if attempt.improvement_score > best_score:
                best_score = attempt.improvement_score
                best_strategy = copy.deepcopy(current_strategy)
                result.final_mql5_code = mql5_code
            
            # Check if strategy passes criteria
            if backtest.passed_criteria:
                attempt.success = True
                result.success = True
                result.improved_strategy = current_strategy
                result.final_metrics = {
                    "profit_factor": backtest.metrics.profit_factor,
                    "win_rate": backtest.metrics.win_rate,
                    "net_profit": backtest.metrics.total_net_profit,
                    "max_drawdown": backtest.metrics.max_drawdown_percent,
                }
                result.attempts.append(attempt)
                break
            
            # Step 6: Apply improvements
            improved_strategy = self._apply_improvements(
                current_strategy, backtest, attempt
            )
            
            if improved_strategy:
                current_strategy = improved_strategy
            else:
                # No more improvements possible
                result.attempts.append(attempt)
                break
            
            result.attempts.append(attempt)
        
        # Use best result found
        result.iterations = len(result.attempts)
        
        if best_strategy and not result.improved_strategy:
            result.improved_strategy = best_strategy
            result.success = best_score > 0
        
        result.improvement_summary = self._generate_summary(result)
        
        return result
    
    def _fix_validation_errors(
        self,
        strategy: dict,
        validation: ValidationResult
    ) -> Optional[dict]:
        """Attempt to fix validation errors automatically."""
        fixed = copy.deepcopy(strategy)
        
        for error in validation.errors:
            if error.category == "indicator_param":
                # Try to add missing parameters with defaults
                if "missing required param" in error.message.lower():
                    # Extract param name and add default
                    pass
            
            elif error.category == "required_field":
                # Add missing required fields with sensible defaults
                field = error.field
                if field == "indicators" and not fixed.get("indicators"):
                    fixed["indicators"] = []
                elif field == "entries" and not fixed.get("entries"):
                    fixed["entries"] = []
                elif field == "exits" and not fixed.get("exits"):
                    fixed["exits"] = []
                elif field == "stopLoss" and not fixed.get("stopLoss"):
                    fixed["stopLoss"] = {"type": "fixed", "pips": 20}
                elif field == "takeProfit" and not fixed.get("takeProfit"):
                    fixed["takeProfit"] = {"type": "rr", "ratio": 2}
        
        # Re-validate
        revalidation = self.strategy_validator.validate(fixed)
        if revalidation.is_valid:
            return fixed
        
        return None
    
    def _apply_improvements(
        self,
        strategy: dict,
        backtest: BacktestResult,
        attempt: ImprovementAttempt
    ) -> Optional[dict]:
        """Apply improvements based on backtest results."""
        improved = copy.deepcopy(strategy)
        m = backtest.metrics
        changes = {}
        
        # Determine what to improve based on metrics
        if m.profit_factor < self.WEAK_PROFIT_FACTOR:
            # Improve profit factor
            action = self._improve_profit_factor(improved, m)
            if action:
                changes.update(action)
                attempt.action = ImprovementAction.TIGHTEN_ENTRIES
        
        if m.max_drawdown_percent > self.WEAK_DRAWDOWN:
            # Reduce drawdown
            action = self._reduce_drawdown(improved, m)
            if action:
                changes.update(action)
                attempt.action = ImprovementAction.MODIFY_RISK
        
        if m.win_rate < self.WEAK_WIN_RATE:
            # Improve win rate
            action = self._improve_win_rate(improved, m)
            if action:
                changes.update(action)
                attempt.action = ImprovementAction.ADD_FILTER
        
        if not changes:
            # Try random tweaks
            action = self._apply_random_tweaks(improved)
            if action:
                changes.update(action)
                attempt.action = ImprovementAction.ADJUST_PARAMETERS
        
        if changes:
            attempt.changes_made.update(changes)
            return improved
        
        return None
    
    def _improve_profit_factor(self, strategy: dict, metrics) -> Optional[dict]:
        """Improvements to increase profit factor."""
        changes = {}
        
        # Increase R:R ratio
        tp = strategy.get("takeProfit", {})
        if tp.get("type") == "rr":
            current_ratio = tp.get("ratio", 2)
            new_ratio = min(current_ratio + 0.5, 4)
            tp["ratio"] = new_ratio
            changes["take_profit_ratio"] = f"{current_ratio} -> {new_ratio}"
        
        # Reduce position size to limit losses
        pos_size = strategy.get("positionSizePercent", 2)
        if pos_size > 1:
            new_size = max(pos_size - 0.5, 0.5)
            strategy["positionSizePercent"] = new_size
            changes["position_size"] = f"{pos_size}% -> {new_size}%"
        
        return changes if changes else None
    
    def _reduce_drawdown(self, strategy: dict, metrics) -> Optional[dict]:
        """Improvements to reduce max drawdown."""
        changes = {}
        
        # Reduce position size
        pos_size = strategy.get("positionSizePercent", 2)
        new_size = max(pos_size * 0.7, 0.5)
        strategy["positionSizePercent"] = new_size
        changes["position_size"] = f"{pos_size}% -> {new_size:.1f}%"
        
        # Decrease daily loss limit
        max_loss = strategy.get("maxDailyLoss", 100)
        new_max_loss = max(max_loss * 0.8, 10)
        strategy["maxDailyLoss"] = new_max_loss
        changes["max_daily_loss"] = f"${max_loss} -> ${new_max_loss:.0f}"
        
        # Tighten stop loss
        sl = strategy.get("stopLoss", {})
        if sl.get("type") == "fixed":
            current_pips = sl.get("pips", 20)
            new_pips = max(current_pips * 0.85, 5)
            sl["pips"] = new_pips
            changes["stop_loss"] = f"{current_pips} -> {new_pips:.0f} pips"
        
        return changes if changes else None
    
    def _improve_win_rate(self, strategy: dict, metrics) -> Optional[dict]:
        """Improvements to increase win rate."""
        changes = {}
        
        indicators = strategy.get("indicators", [])
        
        # Add RSI filter if not present
        has_rsi = any(i.get("type") == "RSI" for i in indicators)
        if not has_rsi:
            indicators.append({
                "id": f"rsi_{len(indicators)}",
                "name": "RSI Filter",
                "type": "RSI",
                "params": {"period": 14},
                "condition": "Momentum filter"
            })
            changes["added_indicator"] = "RSI 14"
        
        # Add trend filter (EMA) if not present
        has_ema = any(i.get("type") == "EMA" for i in indicators)
        if not has_ema:
            indicators.append({
                "id": f"ema_{len(indicators)}",
                "name": "EMA Trend",
                "type": "EMA",
                "params": {"period": 50},
                "condition": "Trend filter"
            })
            changes["added_indicator"] = "EMA 50"
        
        return changes if changes else None
    
    def _apply_random_tweaks(self, strategy: dict) -> Optional[dict]:
        """Apply small random parameter tweaks."""
        changes = {}
        
        # Tweak indicator periods
        indicators = strategy.get("indicators", [])
        for ind in indicators:
            if "period" in ind.get("params", {}):
                current = ind["params"]["period"]
                # Random adjustment ±20%
                adjustment = random.uniform(0.8, 1.2)
                new_period = max(2, int(current * adjustment))
                if new_period != current:
                    ind["params"]["period"] = new_period
                    changes[f"{ind.get('id', 'unknown')}_period"] = f"{current} -> {new_period}"
                    break  # Only tweak one at a time
        
        return changes if changes else None
    
    def _calculate_strategy_score(self, backtest: BacktestResult) -> float:
        """Calculate overall strategy score from backtest results."""
        if not backtest.success:
            return 0.0
        
        m = backtest.metrics
        
        # Weighted scoring similar to optimizer
        score = 0.0
        
        # Profit Factor (0-30 points)
        score += min(m.profit_factor * 10, 30)
        
        # Win Rate (0-25 points)
        score += min(m.win_rate / 4, 25)
        
        # Drawdown penalty (0-20 points, lower DD = higher score)
        dd_score = max(0, 20 - m.max_drawdown_percent * 0.5)
        score += dd_score
        
        # Recovery Factor (0-15 points)
        score += min(m.recovery_factor * 3, 15)
        
        # Sharpe Ratio (0-10 points)
        score += min(max(m.sharpe_ratio, 0) * 4, 10)
        
        return score
    
    def _generate_basic_ea(self, strategy: dict) -> str:
        """Generate a basic EA template from strategy config."""
        # This is a simplified version - the real implementation
        # would use the existing CodeGeneratorStep logic
        
        instruments = strategy.get("instruments", ["EURUSD"])
        timeframe = strategy.get("timeframe", "5m")
        
        return f'''//+------------------------------------------------------------------+
//|                                Auto-Generated EA                 |
//|                              QuantStride Generator               |
//+------------------------------------------------------------------+
#property copyright "QuantStride Auto-Improver"
#property version   "1.00"

input double RiskPercent = {strategy.get("positionSizePercent", 1.0)};
input double StopLossPips = {strategy.get("stopLoss", {}).get("pips", 20)};
input double TakeProfitRatio = {strategy.get("takeProfit", {}).get("ratio", 2.0)};
input int MagicNumber = 12345;

int OnInit()
{{
   Print("EA Initialized for {", ".join(instruments)}");
   return(INIT_SUCCEEDED);
}}

void OnDeinit(const int reason)
{{
   Print("EA Deinitialized");
}}

void OnTick()
{{
   // Basic tick handler
   // Full implementation would include all indicators and logic
}}
'''
    
    def _generate_summary(self, result: ImprovementResult) -> str:
        """Generate a human-readable summary."""
        if not result.success and not result.improved_strategy:
            return f"❌ Improvement failed after {result.iterations} iterations: {result.error_message}"
        
        summary = f"""
🔄 **Auto-Improvement Results**
- Iterations: {result.iterations}/{self.max_iterations}
- Improvement: {result.improvement_percent:+.1f}%
"""
        
        if result.final_metrics:
            summary += f"""
📊 **Final Metrics**
- Profit Factor: {result.final_metrics.get('profit_factor', 0):.2f}
- Win Rate: {result.final_metrics.get('win_rate', 0):.1f}%
- Net Profit: ${result.final_metrics.get('net_profit', 0):,.2f}
- Max Drawdown: {result.final_metrics.get('max_drawdown', 0):.1f}%
"""
        
        # List changes made
        all_changes = {}
        for attempt in result.attempts:
            all_changes.update(attempt.changes_made)
        
        if all_changes:
            summary += "\n🔧 **Changes Applied**\n"
            for key, value in list(all_changes.items())[:10]:
                summary += f"- {key}: {value}\n"
        
        if result.success:
            summary += "\n✅ Strategy passed all acceptance criteria!"
        else:
            summary += "\n⚠️ Strategy improved but may need manual review."
        
        return summary.strip()
