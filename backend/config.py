"""
QuantStride Backend Configuration
Centralized configuration for MT5, MetaEditor, and application settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "QuantStride EA Generator"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]
    
    # MT5 Paths (Windows)
    MT5_TERMINAL_PATH: str = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    METAEDITOR_PATH: str = r"C:\Program Files\MetaTrader 5\metaeditor64.exe"
    MT5_DATA_PATH: str = r"C:\Users\{username}\AppData\Roaming\MetaQuotes\Terminal"
    
    # Compilation Settings
    COMPILE_TIMEOUT: int = 30  # seconds
    MAX_COMPILE_RETRIES: int = 3
    AUTO_FIX_ENABLED: bool = True
    
    # Backtest Settings
    BACKTEST_TIMEOUT: int = 300  # 5 minutes
    DEFAULT_SYMBOL: str = "EURUSD"
    DEFAULT_TIMEFRAME: str = "M5"
    DEFAULT_SPREAD: int = 10
    BACKTEST_START_DATE: str = "2023.01.01"
    BACKTEST_END_DATE: str = "2024.01.01"
    
    # Strategy Validation - Prop-Firm Safe Defaults
    MIN_PROFIT_FACTOR: float = 1.4
    MAX_DRAWDOWN_PERCENT: float = 25.0
    MIN_TOTAL_TRADES: int = 50
    MIN_WIN_RATE: float = 55.0
    MIN_SHARPE_RATIO: float = 1.0
    MIN_RECOVERY_FACTOR: float = 1.5
    
    # Optimization Settings
    OPTIMIZATION_TIMEOUT: int = 3600  # 1 hour
    MAX_OPTIMIZATION_PASSES: int = 1000
    OPTIMIZATION_CRITERIA: str = "Balance"  # Balance, Profit Factor, Custom
    
    # Auto-Improvement Loop
    MAX_IMPROVEMENT_ITERATIONS: int = 10
    IMPROVEMENT_THRESHOLD_PF: float = 1.4
    IMPROVEMENT_THRESHOLD_DD: float = 25.0
    IMPROVEMENT_THRESHOLD_WR: float = 55.0
    IMPROVEMENT_THRESHOLD_SHARPE: float = 1.0
    IMPROVEMENT_THRESHOLD_RF: float = 1.5
    
    # Output Paths
    OUTPUT_DIR: Path = Path("./output")
    EA_OUTPUT_DIR: Path = Path("./output/experts")
    BACKTEST_REPORTS_DIR: Path = Path("./output/reports")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_mt5_data_path() -> Optional[Path]:
    """Get the MT5 data path for the current user."""
    username = os.getenv("USERNAME", os.getenv("USER", ""))
    if username:
        path = Path(settings.MT5_DATA_PATH.format(username=username))
        if path.exists():
            return path
    return None


def ensure_output_dirs():
    """Create output directories if they don't exist."""
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.EA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKTEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# Initialize on import
ensure_output_dirs()
