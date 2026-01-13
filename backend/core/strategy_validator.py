"""
Strategy Validator
Validates trading strategy logic before EA generation.
Ensures all required components exist and no logical contradictions.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result for a strategy."""
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    profitability_score: int = 0  # 0-100
    risk_score: int = 0  # 0-100 (higher = riskier)
    summary: str = ""
    
    def add_error(self, category: str, message: str, field: str = None, suggestion: str = None):
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category=category,
            message=message,
            field=field,
            suggestion=suggestion
        ))
        self.is_valid = False
    
    def add_warning(self, category: str, message: str, field: str = None, suggestion: str = None):
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category=category,
            message=message,
            field=field,
            suggestion=suggestion
        ))
    
    def add_info(self, category: str, message: str):
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            category=category,
            message=message
        ))
    
    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


class StrategyValidator:
    """
    Validates trading strategy configurations.
    
    Checks:
    - All required fields are present
    - Indicators have valid parameters
    - Entry/exit logic is complete
    - SL/TP settings are valid
    - No logical contradictions
    - Profitability potential scoring
    """
    
    # Valid indicator types
    VALID_INDICATORS = {"EMA", "SMA", "RSI", "MACD", "ATR", "BB", "Stochastic", "ADX", "VWAP"}
    
    # Required parameters per indicator type
    INDICATOR_PARAMS = {
        "EMA": {"period": (1, 500)},
        "SMA": {"period": (1, 500)},
        "RSI": {"period": (2, 100)},
        "MACD": {"fast": (2, 100), "slow": (5, 200), "signal": (1, 50)},
        "ATR": {"period": (1, 100)},
        "BB": {"period": (2, 100), "deviation": (0.5, 5.0)},
        "Stochastic": {"kPeriod": (1, 100), "dPeriod": (1, 100), "slowing": (1, 50)},
        "ADX": {"period": (2, 100)},
        "VWAP": {}
    }
    
    # Valid timeframes
    VALID_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
    
    # Valid sessions
    VALID_SESSIONS = {"london", "newyork", "overlap", "asian"}
    
    def __init__(self):
        self.result = ValidationResult(is_valid=True)
    
    def validate(self, strategy: dict) -> ValidationResult:
        """
        Validate a complete strategy configuration.
        
        Args:
            strategy: Strategy configuration dictionary
            
        Returns:
            ValidationResult with all issues and scores
        """
        self.result = ValidationResult(is_valid=True)
        
        # Run all validation checks
        self._validate_required_fields(strategy)
        self._validate_instruments(strategy)
        self._validate_timeframe(strategy)
        self._validate_sessions(strategy)
        self._validate_indicators(strategy)
        self._validate_entries(strategy)
        self._validate_exits(strategy)
        self._validate_stop_loss(strategy)
        self._validate_take_profit(strategy)
        self._validate_risk_settings(strategy)
        self._validate_logical_consistency(strategy)
        
        # Calculate scores
        self._calculate_profitability_score(strategy)
        self._calculate_risk_score(strategy)
        
        # Generate summary
        self._generate_summary(strategy)
        
        return self.result
    
    def _validate_required_fields(self, strategy: dict):
        """Check all required top-level fields exist."""
        required = ["instruments", "timeframe", "indicators", "entries", "exits", "stopLoss", "takeProfit"]
        
        for field in required:
            if field not in strategy:
                self.result.add_error(
                    "required_field",
                    f"Missing required field: {field}",
                    field=field,
                    suggestion=f"Add '{field}' to your strategy configuration"
                )
            elif strategy[field] is None:
                self.result.add_error(
                    "required_field",
                    f"Field '{field}' cannot be null",
                    field=field
                )
    
    def _validate_instruments(self, strategy: dict):
        """Validate trading instruments."""
        instruments = strategy.get("instruments", [])
        
        if not instruments:
            self.result.add_error(
                "instruments",
                "No trading instruments specified",
                field="instruments",
                suggestion="Add at least one instrument (e.g., 'EURUSD')"
            )
            return
        
        if not isinstance(instruments, list):
            self.result.add_error(
                "instruments",
                "Instruments must be a list",
                field="instruments"
            )
            return
        
        # Check for duplicates
        if len(instruments) != len(set(instruments)):
            self.result.add_warning(
                "instruments",
                "Duplicate instruments detected",
                field="instruments"
            )
    
    def _validate_timeframe(self, strategy: dict):
        """Validate timeframe setting."""
        timeframe = strategy.get("timeframe")
        
        if not timeframe:
            self.result.add_error(
                "timeframe",
                "No timeframe specified",
                field="timeframe",
                suggestion=f"Choose from: {', '.join(self.VALID_TIMEFRAMES)}"
            )
            return
        
        if timeframe not in self.VALID_TIMEFRAMES:
            self.result.add_warning(
                "timeframe",
                f"Unusual timeframe: {timeframe}",
                field="timeframe",
                suggestion=f"Standard timeframes: {', '.join(self.VALID_TIMEFRAMES)}"
            )
    
    def _validate_sessions(self, strategy: dict):
        """Validate trading sessions."""
        sessions = strategy.get("sessions", [])
        
        if not sessions:
            self.result.add_info(
                "sessions",
                "No session filter - EA will trade 24/7"
            )
            return
        
        for session in sessions:
            if session not in self.VALID_SESSIONS:
                self.result.add_warning(
                    "sessions",
                    f"Unknown session: {session}",
                    field="sessions",
                    suggestion=f"Valid sessions: {', '.join(self.VALID_SESSIONS)}"
                )
    
    def _validate_indicators(self, strategy: dict):
        """Validate all indicators have valid types and parameters."""
        indicators = strategy.get("indicators", [])
        
        if not indicators:
            self.result.add_error(
                "indicators",
                "No indicators defined",
                field="indicators",
                suggestion="Add at least one indicator for signal generation"
            )
            return
        
        indicator_ids = set()
        
        for idx, ind in enumerate(indicators):
            # Check required fields
            if "id" not in ind:
                self.result.add_error(
                    "indicator",
                    f"Indicator {idx} missing 'id' field",
                    field=f"indicators[{idx}]"
                )
            else:
                if ind["id"] in indicator_ids:
                    self.result.add_error(
                        "indicator",
                        f"Duplicate indicator ID: {ind['id']}",
                        field=f"indicators[{idx}].id"
                    )
                indicator_ids.add(ind["id"])
            
            if "type" not in ind:
                self.result.add_error(
                    "indicator",
                    f"Indicator {idx} missing 'type' field",
                    field=f"indicators[{idx}]"
                )
                continue
            
            ind_type = ind["type"]
            
            # Check valid type
            if ind_type not in self.VALID_INDICATORS:
                self.result.add_error(
                    "indicator",
                    f"Unknown indicator type: {ind_type}",
                    field=f"indicators[{idx}].type",
                    suggestion=f"Valid types: {', '.join(self.VALID_INDICATORS)}"
                )
                continue
            
            # Check parameters
            params = ind.get("params", {})
            required_params = self.INDICATOR_PARAMS.get(ind_type, {})
            
            for param_name, (min_val, max_val) in required_params.items():
                if param_name not in params:
                    self.result.add_error(
                        "indicator_param",
                        f"Indicator '{ind.get('id', idx)}' missing required param: {param_name}",
                        field=f"indicators[{idx}].params.{param_name}",
                        suggestion=f"Add {param_name} (range: {min_val}-{max_val})"
                    )
                else:
                    value = params[param_name]
                    if not isinstance(value, (int, float)):
                        self.result.add_error(
                            "indicator_param",
                            f"Parameter '{param_name}' must be a number",
                            field=f"indicators[{idx}].params.{param_name}"
                        )
                    elif value < min_val or value > max_val:
                        self.result.add_warning(
                            "indicator_param",
                            f"Parameter '{param_name}' value {value} outside typical range ({min_val}-{max_val})",
                            field=f"indicators[{idx}].params.{param_name}"
                        )
    
    def _validate_entries(self, strategy: dict):
        """Validate entry conditions."""
        entries = strategy.get("entries", [])
        
        if not entries:
            self.result.add_error(
                "entries",
                "No entry conditions defined",
                field="entries",
                suggestion="Define at least one entry condition with logic"
            )
            return
        
        has_long = False
        has_short = False
        
        for idx, entry in enumerate(entries):
            if "id" not in entry:
                self.result.add_error(
                    "entry",
                    f"Entry {idx} missing 'id' field",
                    field=f"entries[{idx}]"
                )
            
            if "logic" not in entry or not entry["logic"]:
                self.result.add_error(
                    "entry",
                    f"Entry '{entry.get('id', idx)}' missing logic expression",
                    field=f"entries[{idx}].logic",
                    suggestion="Add logic expression (e.g., 'RSI > 50 && Close > EMA')"
                )
            else:
                # Check for buy/sell indication in ID or description
                entry_id = entry.get("id", "").lower()
                entry_desc = entry.get("description", "").lower()
                
                if any(x in entry_id or x in entry_desc for x in ["long", "buy", "bullish"]):
                    has_long = True
                if any(x in entry_id or x in entry_desc for x in ["short", "sell", "bearish"]):
                    has_short = True
        
        if not has_long and not has_short:
            self.result.add_warning(
                "entries",
                "Entry conditions don't clearly indicate buy/sell direction",
                field="entries",
                suggestion="Name entries with 'long'/'short' or 'buy'/'sell' for clarity"
            )
        elif not has_long:
            self.result.add_info("entries", "Strategy appears to be short-only")
        elif not has_short:
            self.result.add_info("entries", "Strategy appears to be long-only")
    
    def _validate_exits(self, strategy: dict):
        """Validate exit conditions."""
        exits = strategy.get("exits", [])
        
        if not exits:
            self.result.add_warning(
                "exits",
                "No custom exit conditions - will rely on SL/TP only",
                field="exits",
                suggestion="Consider adding signal-based exit conditions"
            )
            return
        
        for idx, exit_cond in enumerate(exits):
            if "id" not in exit_cond:
                self.result.add_error(
                    "exit",
                    f"Exit {idx} missing 'id' field",
                    field=f"exits[{idx}]"
                )
            
            if "logic" not in exit_cond or not exit_cond["logic"]:
                self.result.add_warning(
                    "exit",
                    f"Exit '{exit_cond.get('id', idx)}' missing logic expression",
                    field=f"exits[{idx}].logic"
                )
    
    def _validate_stop_loss(self, strategy: dict):
        """Validate stop loss settings."""
        sl = strategy.get("stopLoss", {})
        
        if not sl:
            self.result.add_error(
                "stopLoss",
                "No stop loss configured",
                field="stopLoss",
                suggestion="Every strategy must have a stop loss for risk management"
            )
            return
        
        sl_type = sl.get("type")
        if sl_type not in ["fixed", "atr", "structure"]:
            self.result.add_error(
                "stopLoss",
                f"Invalid stop loss type: {sl_type}",
                field="stopLoss.type",
                suggestion="Use 'fixed', 'atr', or 'structure'"
            )
        
        if sl_type == "fixed":
            pips = sl.get("pips")
            if pips is None:
                self.result.add_error(
                    "stopLoss",
                    "Fixed SL requires 'pips' value",
                    field="stopLoss.pips"
                )
            elif pips <= 0:
                self.result.add_error(
                    "stopLoss",
                    "Stop loss pips must be positive",
                    field="stopLoss.pips"
                )
            elif pips < 5:
                self.result.add_warning(
                    "stopLoss",
                    f"Very tight stop loss ({pips} pips) - may cause premature exits",
                    field="stopLoss.pips"
                )
        
        if sl_type == "atr":
            multiplier = sl.get("atrMultiplier")
            if multiplier is None:
                self.result.add_error(
                    "stopLoss",
                    "ATR SL requires 'atrMultiplier' value",
                    field="stopLoss.atrMultiplier"
                )
            elif multiplier <= 0:
                self.result.add_error(
                    "stopLoss",
                    "ATR multiplier must be positive",
                    field="stopLoss.atrMultiplier"
                )
    
    def _validate_take_profit(self, strategy: dict):
        """Validate take profit settings."""
        tp = strategy.get("takeProfit", {})
        
        if not tp:
            self.result.add_error(
                "takeProfit",
                "No take profit configured",
                field="takeProfit"
            )
            return
        
        tp_type = tp.get("type")
        if tp_type not in ["fixed", "rr", "trailing"]:
            self.result.add_error(
                "takeProfit",
                f"Invalid take profit type: {tp_type}",
                field="takeProfit.type",
                suggestion="Use 'fixed', 'rr', or 'trailing'"
            )
        
        if tp_type == "fixed":
            pips = tp.get("pips")
            if pips is None:
                self.result.add_error(
                    "takeProfit",
                    "Fixed TP requires 'pips' value",
                    field="takeProfit.pips"
                )
        
        if tp_type == "rr":
            ratio = tp.get("ratio")
            if ratio is None:
                self.result.add_error(
                    "takeProfit",
                    "R:R TP requires 'ratio' value",
                    field="takeProfit.ratio"
                )
            elif ratio < 1:
                self.result.add_warning(
                    "takeProfit",
                    f"Low R:R ratio ({ratio}) - requires high win rate",
                    field="takeProfit.ratio",
                    suggestion="Consider ratio >= 1.5 for better risk-adjusted returns"
                )
    
    def _validate_risk_settings(self, strategy: dict):
        """Validate risk management settings."""
        position_size = strategy.get("positionSizePercent")
        if position_size is not None:
            if position_size <= 0:
                self.result.add_error(
                    "risk",
                    "Position size percent must be positive",
                    field="positionSizePercent"
                )
            elif position_size > 5:
                self.result.add_warning(
                    "risk",
                    f"High position size ({position_size}%) - significant risk per trade",
                    field="positionSizePercent",
                    suggestion="Consider 1-2% for conservative risk management"
                )
        
        max_daily_loss = strategy.get("maxDailyLoss")
        if max_daily_loss is not None and max_daily_loss <= 0:
            self.result.add_error(
                "risk",
                "Max daily loss must be positive",
                field="maxDailyLoss"
            )
    
    def _validate_logical_consistency(self, strategy: dict):
        """Check for logical contradictions in strategy rules."""
        entries = strategy.get("entries", [])
        indicators = strategy.get("indicators", [])
        
        # Get indicator types used
        indicator_types = {ind["type"] for ind in indicators if "type" in ind}
        
        for entry in entries:
            logic = entry.get("logic", "").upper()
            
            # Check RSI contradictions
            if "RSI" in indicator_types:
                # RSI > X AND RSI < Y where X > Y
                if "RSI >" in logic and "RSI <" in logic:
                    # Simple pattern check - could be more sophisticated
                    self.result.add_info(
                        "logic",
                        f"Entry '{entry.get('id')}' has RSI upper and lower bounds - verify they're not contradictory"
                    )
            
            # Check for common logical issues
            if "&&" in logic and "||" in logic:
                self.result.add_info(
                    "logic",
                    f"Entry '{entry.get('id')}' mixes AND/OR - ensure parentheses define correct precedence"
                )
        
        # Check for indicator alignment
        ema_count = len([i for i in indicators if i.get("type") == "EMA"])
        if ema_count >= 3:
            self.result.add_info(
                "indicators",
                f"Triple EMA setup detected ({ema_count} EMAs) - good for trend filtering"
            )
    
    def _calculate_profitability_score(self, strategy: dict):
        """
        Calculate estimated profitability score (0-100).
        
        Scoring criteria:
        - Entry conditions clarity: 0-20
        - Indicator synergy: 0-20
        - Risk:Reward ratio: 0-20
        - Risk management: 0-20
        - Strategy completeness: 0-20
        """
        score = 0
        
        # Entry conditions
        entries = strategy.get("entries", [])
        if entries:
            if len(entries) >= 2:  # Both long and short
                score += 15
            else:
                score += 10
            
            # Logic complexity (more conditions = potentially better filtering)
            avg_logic_len = sum(len(e.get("logic", "")) for e in entries) / len(entries)
            if avg_logic_len > 30:
                score += 5
        
        # Indicator synergy
        indicators = strategy.get("indicators", [])
        indicator_types = {i.get("type") for i in indicators}
        
        # Trend + Momentum + Volatility = good combo
        has_trend = bool(indicator_types & {"EMA", "SMA", "ADX"})
        has_momentum = bool(indicator_types & {"RSI", "MACD", "Stochastic"})
        has_volatility = bool(indicator_types & {"ATR", "BB"})
        
        if has_trend:
            score += 8
        if has_momentum:
            score += 7
        if has_volatility:
            score += 5
        
        # Risk:Reward
        tp = strategy.get("takeProfit", {})
        if tp.get("type") == "rr":
            ratio = tp.get("ratio", 1)
            if ratio >= 2:
                score += 20
            elif ratio >= 1.5:
                score += 15
            elif ratio >= 1:
                score += 10
        elif tp.get("type") == "fixed":
            score += 10
        
        # Risk management
        sl = strategy.get("stopLoss", {})
        if sl:
            score += 10
            if sl.get("type") == "atr":
                score += 5  # Dynamic SL is better
        
        if strategy.get("maxDailyLoss"):
            score += 5
        
        self.result.profitability_score = min(100, score)
    
    def _calculate_risk_score(self, strategy: dict):
        """
        Calculate risk score (0-100, higher = riskier).
        """
        score = 0
        
        # Position sizing risk
        pos_size = strategy.get("positionSizePercent", 1)
        if pos_size > 5:
            score += 30
        elif pos_size > 3:
            score += 20
        elif pos_size > 2:
            score += 10
        
        # Stop loss risk
        sl = strategy.get("stopLoss", {})
        if not sl:
            score += 40
        elif sl.get("type") == "fixed":
            pips = sl.get("pips", 10)
            if pips < 5:
                score += 15  # Too tight
            elif pips > 50:
                score += 20  # Too wide
        
        # No exits defined
        if not strategy.get("exits"):
            score += 15
        
        # No daily loss limit
        if not strategy.get("maxDailyLoss"):
            score += 10
        
        self.result.risk_score = min(100, score)
    
    def _generate_summary(self, strategy: dict):
        """Generate a human-readable summary."""
        errors = len(self.result.errors)
        warnings = len(self.result.warnings)
        
        if errors > 0:
            self.result.summary = f"❌ Validation failed with {errors} error(s) and {warnings} warning(s)"
        elif warnings > 0:
            self.result.summary = f"⚠️ Validation passed with {warnings} warning(s)"
        else:
            self.result.summary = "✅ Strategy validation passed"
        
        self.result.summary += f" | Profitability: {self.result.profitability_score}/100"
        self.result.summary += f" | Risk: {self.result.risk_score}/100"
