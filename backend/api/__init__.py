"""
QuantStride API Layer
FastAPI routes for EA generation, validation, and optimization.
"""

from .main import app
from .routes import router
from .models import (
    StrategyRequest,
    GenerateResponse,
    ValidationResponse,
    BacktestResponse,
    OptimizationResponse,
    ImprovementResponse,
)

__all__ = [
    "app",
    "router",
    "StrategyRequest",
    "GenerateResponse",
    "ValidationResponse",
    "BacktestResponse",
    "OptimizationResponse",
    "ImprovementResponse",
]
