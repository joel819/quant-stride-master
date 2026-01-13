"""
Pydantic Models
Request and response schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


# ============= Enums =============

class IndicatorType(str, Enum):
    EMA = "EMA"
    SMA = "SMA"
    RSI = "RSI"
    MACD = "MACD"
    ATR = "ATR"
    BB = "BB"
    STOCHASTIC = "Stochastic"
    ADX = "ADX"
    VWAP = "VWAP"


class StopLossType(str, Enum):
    FIXED = "fixed"
    ATR = "atr"
    STRUCTURE = "structure"


class TakeProfitType(str, Enum):
    FIXED = "fixed"
    RR = "rr"
    TRAILING = "trailing"


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class Session(str, Enum):
    LONDON = "london"
    NEWYORK = "newyork"
    OVERLAP = "overlap"
    ASIAN = "asian"


# ============= Strategy Components =============

class IndicatorConfig(BaseModel):
    """Configuration for a single indicator."""
    id: str
    name: str
    type: IndicatorType
    params: dict[str, float] = Field(default_factory=dict)
    condition: Optional[str] = None


class EntryCondition(BaseModel):
    """Entry condition definition."""
    id: str
    description: str
    logic: str


class ExitCondition(BaseModel):
    """Exit condition definition."""
    id: str
    description: str
    logic: str


class StopLossConfig(BaseModel):
    """Stop loss configuration."""
    type: StopLossType
    pips: Optional[float] = None
    atrMultiplier: Optional[float] = None


class TakeProfitConfig(BaseModel):
    """Take profit configuration."""
    type: TakeProfitType
    pips: Optional[float] = None
    ratio: Optional[float] = None
    trailDistance: Optional[float] = None


# ============= Main Strategy Config =============

class StrategyConfig(BaseModel):
    """Complete trading strategy configuration."""
    instruments: list[str] = Field(min_length=1)
    timeframe: Timeframe
    accountSize: float = 10000.0
    dailyTarget: float = 100.0
    sessions: list[Session] = Field(default_factory=list)
    indicators: list[IndicatorConfig] = Field(default_factory=list)
    entries: list[EntryCondition] = Field(default_factory=list)
    exits: list[ExitCondition] = Field(default_factory=list)
    stopLoss: StopLossConfig
    takeProfit: TakeProfitConfig
    maxDailyLoss: float = 100.0
    positionSizePercent: float = 1.0


# ============= Request Models =============

class StrategyRequest(BaseModel):
    """Request to process a trading strategy."""
    strategy: StrategyConfig
    ea_name: Optional[str] = "GeneratedEA"


class BacktestRequest(BaseModel):
    """Request to run a backtest."""
    strategy: StrategyConfig
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    spread: Optional[int] = None
    initial_deposit: float = 10000.0


class OptimizationRequest(BaseModel):
    """Request to run optimization."""
    strategy: StrategyConfig
    parameter_ranges: dict[str, list[float]]
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    max_combinations: int = 100


class ImprovementRequest(BaseModel):
    """Request to run auto-improvement."""
    strategy: StrategyConfig
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    max_iterations: Optional[int] = None


# ============= Response Models =============

class ValidationIssue(BaseModel):
    """A single validation issue."""
    severity: str
    category: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response from strategy validation."""
    status: str  # "success" or "error"
    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    profitability_score: int = 0
    risk_score: int = 0
    summary: str = ""


class CompilationError(BaseModel):
    """A compilation error."""
    line: int
    column: int
    error_type: str
    message: str
    auto_fixable: bool = False


class CompilationResponse(BaseModel):
    """Response from MQL5 compilation."""
    status: str
    success: bool
    errors: list[CompilationError] = Field(default_factory=list)
    warnings: list[CompilationError] = Field(default_factory=list)
    compile_attempts: int = 0


class GenerateResponse(BaseModel):
    """Response from EA generation."""
    status: str  # "success" or "error"
    ea_name: str = ""
    mql5_code: str = ""
    validation: ValidationResponse
    compilation: Optional[CompilationResponse] = None
    backtest_instruction: Optional[dict] = None
    errors: list[str] = Field(default_factory=list)


class BacktestMetrics(BaseModel):
    """Backtest performance metrics."""
    total_trades: int = 0
    profit_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    total_net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    expected_payoff: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    recovery_factor: float = 0.0


class BacktestResponse(BaseModel):
    """Response from backtest run."""
    status: str
    success: bool
    metrics: BacktestMetrics
    passed_criteria: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)
    symbol: str = ""
    timeframe: str = ""
    summary: str = ""


class ParameterSetResult(BaseModel):
    """Result for a single parameter set."""
    name: str
    values: dict[str, float]
    score: float = 0.0
    metrics: Optional[BacktestMetrics] = None


class OptimizationResponse(BaseModel):
    """Response from optimization run."""
    status: str
    success: bool
    best_parameters: Optional[ParameterSetResult] = None
    total_combinations: int = 0
    tested_combinations: int = 0
    improvement_percent: float = 0.0
    optimization_time: float = 0.0
    summary: str = ""


class ImprovementAttemptResult(BaseModel):
    """Result of a single improvement attempt."""
    iteration: int
    action: str
    changes_made: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    success: bool = False


class ImprovementResponse(BaseModel):
    """Response from auto-improvement run."""
    status: str
    success: bool
    iterations: int = 0
    improvement_percent: float = 0.0
    original_strategy: dict = Field(default_factory=dict)
    improved_strategy: Optional[dict] = None
    final_mql5_code: str = ""
    final_metrics: Optional[dict] = None
    attempts: list[ImprovementAttemptResult] = Field(default_factory=list)
    summary: str = ""


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    mt5_available: bool
    features: dict[str, bool]
