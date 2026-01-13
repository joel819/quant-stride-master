"""
API Routes
Endpoints for EA generation, validation, and optimization.
"""

from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .models import (
    StrategyRequest,
    BacktestRequest,
    OptimizationRequest,
    ImprovementRequest,
    GenerateResponse,
    ValidationResponse,
    ValidationIssue,
    BacktestResponse,
    BacktestMetrics,
    OptimizationResponse,
    ParameterSetResult,
    ImprovementResponse,
    ImprovementAttemptResult,
    HealthResponse,
)
from core import (
    StrategyValidator,
    MQLValidator,
    Backtester,
    Optimizer,
    AutoImprover,
)
from templates import BaseEATemplate

router = APIRouter()


def strategy_to_dict(strategy) -> dict:
    """Convert Pydantic strategy model to dict."""
    return strategy.model_dump()


# ============= Validation Endpoint =============

@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy(request: StrategyRequest):
    """
    Validate a trading strategy.
    
    Checks for:
    - Required fields
    - Valid indicator parameters
    - Logical consistency
    - Profitability potential
    """
    validator = StrategyValidator()
    result = validator.validate(strategy_to_dict(request.strategy))
    
    issues = [
        ValidationIssue(
            severity=issue.severity.value,
            category=issue.category,
            message=issue.message,
            field=issue.field,
            suggestion=issue.suggestion
        )
        for issue in result.issues
    ]
    
    return ValidationResponse(
        status="success" if result.is_valid else "error",
        is_valid=result.is_valid,
        issues=issues,
        profitability_score=result.profitability_score,
        risk_score=result.risk_score,
        summary=result.summary
    )


# ============= Generate Endpoint =============

@router.post("/generate", response_model=GenerateResponse)
async def generate_ea(request: StrategyRequest):
    """
    Generate an MQL5 Expert Advisor from a strategy.
    
    Steps:
    1. Validate strategy
    2. Generate MQL5 code
    3. Optionally validate compilation
    4. Return code and instructions
    """
    strategy_dict = strategy_to_dict(request.strategy)
    
    # Step 1: Validate
    validator = StrategyValidator()
    validation = validator.validate(strategy_dict)
    
    validation_response = ValidationResponse(
        status="success" if validation.is_valid else "error",
        is_valid=validation.is_valid,
        issues=[
            ValidationIssue(
                severity=i.severity.value,
                category=i.category,
                message=i.message,
                field=i.field,
                suggestion=i.suggestion
            )
            for i in validation.issues
        ],
        profitability_score=validation.profitability_score,
        risk_score=validation.risk_score,
        summary=validation.summary
    )
    
    if not validation.is_valid:
        return GenerateResponse(
            status="error",
            ea_name=request.ea_name,
            mql5_code="",
            validation=validation_response,
            errors=[e.message for e in validation.errors]
        )
    
    # Step 2: Generate MQL5 code
    # Using the base template (full implementation would use strategy config)
    mql5_code = BaseEATemplate.generate_full_skeleton(
        ea_name=request.ea_name or "QuantStrideEA"
    )
    
    # Step 3: Generate backtest instructions
    backtest_instruction = {
        "symbol": request.strategy.instruments[0] if request.strategy.instruments else "EURUSD",
        "timeframe": request.strategy.timeframe.value,
        "recommended_period": "2023.01.01 - 2024.01.01",
        "spread": 10,
        "modeling": "Every tick",
        "optimization_params": [
            "RiskPercent: 0.5 - 3.0 (step 0.5)",
            "StopLossPips: 10 - 50 (step 5)",
            "TakeProfitRatio: 1.5 - 3.0 (step 0.5)"
        ]
    }
    
    return GenerateResponse(
        status="success",
        ea_name=request.ea_name,
        mql5_code=mql5_code,
        validation=validation_response,
        backtest_instruction=backtest_instruction
    )


# ============= Compile Endpoint =============

@router.post("/compile")
async def compile_ea(request: StrategyRequest):
    """
    Compile MQL5 code and validate.
    
    Uses MetaEditor CLI if available, otherwise performs
    structural validation.
    """
    # Generate code first
    mql5_code = BaseEATemplate.generate_full_skeleton(
        ea_name=request.ea_name or "QuantStrideEA"
    )
    
    # Compile
    compiler = MQLValidator()
    result = compiler.validate(mql5_code)
    
    return {
        "status": "success" if result.success else "error",
        "success": result.success,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "compile_attempts": result.compile_attempts,
        "summary": compiler.get_error_summary(result),
        "fixed_code": result.fixed_code
    }


# ============= Backtest Endpoint =============

@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on a strategy.
    
    Returns performance metrics and acceptance criteria results.
    """
    # Generate EA first
    mql5_code = BaseEATemplate.generate_full_skeleton(ea_name="BacktestEA")
    
    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mq5', delete=False) as f:
        f.write(mql5_code)
        ea_path = f.name
    
    # Run backtest
    backtester = Backtester()
    result = backtester.run_backtest(
        ea_path=ea_path,
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        spread=request.spread,
        initial_deposit=request.initial_deposit
    )
    
    # Clean up
    import os
    try:
        os.unlink(ea_path)
    except:
        pass
    
    metrics = BacktestMetrics(
        total_trades=result.metrics.total_trades,
        profit_trades=result.metrics.profit_trades,
        loss_trades=result.metrics.loss_trades,
        win_rate=result.metrics.win_rate,
        total_net_profit=result.metrics.total_net_profit,
        gross_profit=result.metrics.gross_profit,
        gross_loss=result.metrics.gross_loss,
        profit_factor=result.metrics.profit_factor,
        expected_payoff=result.metrics.expected_payoff,
        max_drawdown=result.metrics.max_drawdown,
        max_drawdown_percent=result.metrics.max_drawdown_percent,
        sharpe_ratio=result.metrics.sharpe_ratio,
        recovery_factor=result.metrics.recovery_factor
    )
    
    return BacktestResponse(
        status="success" if result.success else "error",
        success=result.success,
        metrics=metrics,
        passed_criteria=result.passed_criteria,
        rejection_reasons=result.rejection_reasons,
        symbol=result.symbol,
        timeframe=result.timeframe,
        summary=backtester.get_summary(result)
    )


# ============= Optimize Endpoint =============

@router.post("/optimize", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """
    Run parameter optimization on a strategy.
    """
    # Generate EA
    mql5_code = BaseEATemplate.generate_full_skeleton(ea_name="OptimizeEA")
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mq5', delete=False) as f:
        f.write(mql5_code)
        ea_path = f.name
    
    # Run optimization
    optimizer = Optimizer()
    result = optimizer.optimize_grid(
        ea_path=ea_path,
        parameter_ranges=request.parameter_ranges,
        symbol=request.symbol,
        timeframe=request.timeframe,
        max_combinations=request.max_combinations
    )
    
    # Clean up
    import os
    try:
        os.unlink(ea_path)
    except:
        pass
    
    best_params = None
    if result.best_parameters:
        best_metrics = None
        if result.best_parameters.metrics:
            best_metrics = BacktestMetrics(
                total_trades=result.best_parameters.metrics.total_trades,
                profit_trades=result.best_parameters.metrics.profit_trades,
                loss_trades=result.best_parameters.metrics.loss_trades,
                win_rate=result.best_parameters.metrics.win_rate,
                total_net_profit=result.best_parameters.metrics.total_net_profit,
                profit_factor=result.best_parameters.metrics.profit_factor,
                max_drawdown_percent=result.best_parameters.metrics.max_drawdown_percent,
            )
        
        best_params = ParameterSetResult(
            name=result.best_parameters.name,
            values=result.best_parameters.values,
            score=result.best_parameters.score,
            metrics=best_metrics
        )
    
    return OptimizationResponse(
        status="success" if result.success else "error",
        success=result.success,
        best_parameters=best_params,
        total_combinations=result.total_combinations,
        tested_combinations=result.tested_combinations,
        improvement_percent=result.improvement_percent,
        optimization_time=result.optimization_time,
        summary=optimizer.get_summary(result)
    )


# ============= Auto-Improve Endpoint =============

@router.post("/auto-improve", response_model=ImprovementResponse)
async def auto_improve(request: ImprovementRequest):
    """
    Run the auto-improvement loop on a strategy.
    
    Iteratively:
    1. Validate
    2. Compile
    3. Backtest
    4. Improve if weak
    5. Repeat until criteria met or max iterations
    """
    strategy_dict = strategy_to_dict(request.strategy)
    
    improver = AutoImprover(
        max_iterations=request.max_iterations
    )
    
    result = improver.improve(
        strategy=strategy_dict,
        symbol=request.symbol,
        timeframe=request.timeframe
    )
    
    attempts = [
        ImprovementAttemptResult(
            iteration=a.iteration,
            action=a.action.value,
            changes_made=a.changes_made,
            score=a.improvement_score,
            success=a.success
        )
        for a in result.attempts
    ]
    
    return ImprovementResponse(
        status="success" if result.success else "error",
        success=result.success,
        iterations=result.iterations,
        improvement_percent=result.improvement_percent,
        original_strategy=result.original_strategy,
        improved_strategy=result.improved_strategy,
        final_mql5_code=result.final_mql5_code,
        final_metrics=result.final_metrics,
        attempts=attempts,
        summary=result.improvement_summary
    )


# ============= Health Check =============

@router.get("/health", response_model=HealthResponse)
async def api_health():
    """API health check with feature availability."""
    import os
    from config import settings
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        mt5_available=os.path.exists(settings.MT5_TERMINAL_PATH),
        features={
            "validation": True,
            "compilation": os.path.exists(settings.METAEDITOR_PATH),
            "backtesting": os.path.exists(settings.MT5_TERMINAL_PATH),
            "optimization": os.path.exists(settings.MT5_TERMINAL_PATH),
            "auto_improvement": True,
            "custom_ea_generation": True,
        }
    )


# ============= Custom EA Generation Endpoint =============

from pydantic import BaseModel
from typing import Optional

class CustomEARequest(BaseModel):
    """Request for custom EA generation."""
    ea_name: str = "CustomEA"
    symbol: str = "EURUSD"
    
    # Trend settings
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    use_trend_filter: bool = True
    
    # Entry settings
    rsi_period: int = 14
    rsi_buy_min: float = 30.0
    rsi_buy_max: float = 40.0
    rsi_sell_min: float = 60.0
    rsi_sell_max: float = 70.0
    use_macd_confirmation: bool = True
    pullback_distance_pips: float = 30.0
    
    # Risk settings
    risk_percent: float = 1.0
    risk_reward_ratio: float = 2.0
    min_sl_pips: float = 20.0
    max_sl_pips: float = 100.0
    use_breakeven: bool = True
    breakeven_trigger_pips: float = 20.0
    breakeven_offset_pips: float = 5.0
    use_trailing_stop: bool = False
    
    # Advanced Trailing Stop
    trailing_stop_type: str = "fixed"  # fixed, atr, step
    trailing_start_pips: float = 30.0
    trailing_distance_pips: float = 20.0  # for fixed
    atr_period: int = 14
    atr_multiplier: float = 1.5
    step_size_pips: float = 10.0
    step_distance_pips: float = 10.0
    
    # Partial Close
    use_partial_close: bool = False
    partial_close_percent: float = 50.0
    partial_close_tp1_rr: float = 1.0
    partial_close_tp2_rr: float = 2.0
    move_sl_after_partial: bool = True
    
    # Filters
    max_spread_points: float = 20.0
    use_trading_hours: bool = True
    trading_hour_start: int = 8
    trading_hour_end: int = 18
    use_news_filter: bool = True


class CustomEAResponse(BaseModel):
    """Response from custom EA generation."""
    status: str
    ea_name: str
    symbol: str
    mql5_code: str
    file_path: Optional[str] = None
    code_length: int = 0
    backtest_instructions: dict = {}


@router.post("/generate-custom-ea", response_model=CustomEAResponse)
async def generate_custom_ea(request: CustomEARequest):
    """
    Generate a custom MQL5 Expert Advisor with specified settings.
    """
    from templates.custom_ea_generator import CustomEAGenerator, EASettings
    from config import settings as app_settings
    
    # Create settings from request
    ea_settings = EASettings(
        ea_name=request.ea_name,
        symbol=request.symbol,
        ema_fast_period=request.ema_fast_period,
        ema_slow_period=request.ema_slow_period,
        use_trend_filter=request.use_trend_filter,
        rsi_period=request.rsi_period,
        rsi_buy_min=request.rsi_buy_min,
        rsi_buy_max=request.rsi_buy_max,
        rsi_sell_min=request.rsi_sell_min,
        rsi_sell_max=request.rsi_sell_max,
        use_macd_confirmation=request.use_macd_confirmation,
        pullback_distance_pips=request.pullback_distance_pips,
        risk_percent=request.risk_percent,
        risk_reward_ratio=request.risk_reward_ratio,
        min_sl_pips=request.min_sl_pips,
        max_sl_pips=request.max_sl_pips,
        use_breakeven=request.use_breakeven,
        breakeven_trigger_pips=request.breakeven_trigger_pips,
        breakeven_buffer_pips=request.breakeven_offset_pips,
        
        # New Trailing Stop mappings
        use_trailing_stop=request.use_trailing_stop,
        trailing_stop_type=request.trailing_stop_type,
        trailing_start_pips=request.trailing_start_pips,
        trailing_distance_pips=request.trailing_distance_pips,
        atr_period=request.atr_period,
        atr_multiplier=request.atr_multiplier,
        step_size_pips=request.step_size_pips,
        step_distance_pips=request.step_distance_pips,
        
        # Partial Close
        use_partial_close=request.use_partial_close,
        partial_close_percent=request.partial_close_percent,
        partial_close_tp1_rr=request.partial_close_tp1_rr,
        partial_close_tp2_rr=request.partial_close_tp2_rr,
        move_sl_after_partial=request.move_sl_after_partial,
        
        max_spread_points=request.max_spread_points,
        use_trading_hours=request.use_trading_hours,
        trading_hour_start=request.trading_hour_start,
        trading_hour_end=request.trading_hour_end,
        use_news_filter=request.use_news_filter,
    )
    
    # Generate EA
    generator = CustomEAGenerator(ea_settings)
    mql5_code = generator.generate()
    
    # Save to file
    output_dir = str(app_settings.EA_OUTPUT_DIR)
    file_path = generator.save(output_dir)
    
    # Backtest instructions
    backtest_instructions = {
        "symbol": request.symbol,
        "timeframe": "M5",
        "period": "2023.01.01 - 2024.01.01",
        "spread": int(request.max_spread_points),
        "modeling": "Every tick",
        "optimization_params": {
            "RSI_Buy_Min": f"{request.rsi_buy_min - 10} - {request.rsi_buy_min + 10} (step 5)",
            "RiskRewardRatio": "1.5 - 3.0 (step 0.5)",
            "EMA_Fast_Period": f"{max(10, request.ema_fast_period - 20)} - {request.ema_fast_period + 20} (step 10)",
        }
    }
    
    return CustomEAResponse(
        status="success",
        ea_name=request.ea_name,
        symbol=request.symbol,
        mql5_code=mql5_code,
        file_path=file_path,
        code_length=len(mql5_code),
        backtest_instructions=backtest_instructions
    )


@router.get("/presets")
async def get_ea_presets():
    """
    Get available EA preset configurations.
    
    Returns preset configurations for popular symbols.
    """
    return {
        "presets": [
            {
                "name": "XAUUSD_Scalper",
                "symbol": "XAUUSD",
                "description": "Gold scalping EA with pullback entries",
                "settings": {
                    "ema_fast_period": 50,
                    "ema_slow_period": 200,
                    "rsi_buy_min": 20,
                    "rsi_buy_max": 35,
                    "rsi_sell_min": 65,
                    "rsi_sell_max": 80,
                    "risk_percent": 1.0,
                    "risk_reward_ratio": 2.0,
                    "max_spread_points": 25,
                    "trading_hour_start": 8,
                    "trading_hour_end": 18
                }
            },
            {
                "name": "EURUSD_Scalper",
                "symbol": "EURUSD", 
                "description": "Euro scalping EA for London/NY sessions",
                "settings": {
                    "ema_fast_period": 21,
                    "ema_slow_period": 55,
                    "rsi_buy_min": 30,
                    "rsi_buy_max": 45,
                    "rsi_sell_min": 55,
                    "rsi_sell_max": 70,
                    "risk_percent": 1.0,
                    "risk_reward_ratio": 1.5,
                    "max_spread_points": 15,
                    "trading_hour_start": 8,
                    "trading_hour_end": 17
                }
            },
            {
                "name": "US30_Trader",
                "symbol": "US30",
                "description": "Dow Jones index trader for US session",
                "settings": {
                    "ema_fast_period": 20,
                    "ema_slow_period": 50,
                    "rsi_buy_min": 35,
                    "rsi_buy_max": 50,
                    "risk_percent": 0.5,
                    "risk_reward_ratio": 2.0,
                    "max_spread_points": 50,
                    "trading_hour_start": 14,
                    "trading_hour_end": 21
                }
            },
            {
                "name": "V75_Trader",
                "symbol": "Volatility 75 Index",
                "description": "Volatility 75 Index trader (24/7)",
                "settings": {
                    "ema_fast_period": 10,
                    "ema_slow_period": 21,
                    "rsi_buy_min": 25,
                    "rsi_buy_max": 40,
                    "risk_percent": 0.5,
                    "risk_reward_ratio": 1.5,
                    "use_trading_hours": False,
                    "use_news_filter": False
                }
            }
        ]
    }
