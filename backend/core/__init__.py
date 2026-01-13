"""
QuantStride Core Modules
Strategy validation, compilation, backtesting, optimization, and auto-improvement.
"""

from .strategy_validator import StrategyValidator, ValidationResult
from .mql_validator import MQLValidator, CompilationResult
from .backtester import Backtester, BacktestResult, BacktestMetrics
from .optimizer import Optimizer, OptimizationResult, ParameterSet
from .auto_improver import AutoImprover, ImprovementResult, ImprovementAction

__all__ = [
    "StrategyValidator",
    "ValidationResult",
    "MQLValidator",
    "CompilationResult",
    "Backtester",
    "BacktestResult",
    "Optimizer",
    "OptimizationResult",
    "AutoImprover",
    "ImprovementResult",
]
