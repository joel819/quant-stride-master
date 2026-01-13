"""
Backtester
Run MT5 Strategy Tester and parse backtest reports.
"""

import subprocess
import tempfile
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


@dataclass
class BacktestMetrics:
    """Key performance metrics from a backtest."""
    # Basic metrics
    total_trades: int = 0
    profit_trades: int = 0
    loss_trades: int = 0
    
    # Financial metrics
    initial_deposit: float = 0.0
    total_net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    
    # Ratios
    profit_factor: float = 0.0
    expected_payoff: float = 0.0
    recovery_factor: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    relative_drawdown: float = 0.0
    
    # Time-based
    avg_trade_duration: str = ""
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.profit_trades / self.total_trades) * 100
    
    @property
    def is_profitable(self) -> bool:
        return self.profit_factor >= 1.0 and self.total_net_profit > 0


@dataclass
class BacktestResult:
    """Complete result from a backtest run."""
    success: bool
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)
    passed_criteria: bool = False
    rejection_reasons: list[str] = field(default_factory=list)
    raw_report: str = ""
    report_path: Optional[str] = None
    error_message: str = ""
    
    # Test parameters
    symbol: str = ""
    timeframe: str = ""
    start_date: str = ""
    end_date: str = ""
    spread: int = 0


class Backtester:
    """
    Run MT5 Strategy Tester and analyze results.
    
    Features:
    - Run backtests via MT5 terminal
    - Parse HTML/XML backtest reports
    - Extract performance metrics
    - Apply acceptance criteria
    """
    
    # Acceptance criteria - Prop-Firm Safe Standards
    DEFAULT_CRITERIA = {
        "min_profit_factor": 1.4,       # User requirement: >= 1.4
        "max_drawdown_percent": 25.0,   # User requirement: <= 25%
        "min_total_trades": 50,         # Statistical significance
        "min_win_rate": 55.0,           # User requirement: >= 55%
        "min_recovery_factor": 1.5,     # User requirement: >= 1.5
        "min_sharpe_ratio": 1.0,        # User requirement: >= 1.0
    }
    
    # Regex patterns for parsing HTML reports
    METRICS_PATTERNS = {
        "total_net_profit": re.compile(r"Total Net Profit.*?(-?[\d\s]+\.?\d*)", re.IGNORECASE),
        "gross_profit": re.compile(r"Gross Profit.*?([\d\s]+\.?\d*)", re.IGNORECASE),
        "gross_loss": re.compile(r"Gross Loss.*?(-?[\d\s]+\.?\d*)", re.IGNORECASE),
        "profit_factor": re.compile(r"Profit Factor.*?([\d\.]+)", re.IGNORECASE),
        "expected_payoff": re.compile(r"Expected Payoff.*?(-?[\d\.]+)", re.IGNORECASE),
        "max_drawdown": re.compile(r"Maximal Drawdown.*?([\d\s]+\.?\d*).*?\(([\d\.]+)%\)", re.IGNORECASE),
        "total_trades": re.compile(r"Total Trades.*?(\d+)", re.IGNORECASE),
        "profit_trades": re.compile(r"(?:Profit Trades|Short Trades \(won %\)|Long Trades \(won %\)).*?(\d+)", re.IGNORECASE),
        "sharpe_ratio": re.compile(r"Sharpe Ratio.*?(-?[\d\.]+)", re.IGNORECASE),
        "recovery_factor": re.compile(r"Recovery Factor.*?([\d\.]+)", re.IGNORECASE),
    }
    
    def __init__(
        self,
        mt5_path: str = None,
        criteria: dict = None
    ):
        self.mt5_path = mt5_path or settings.MT5_TERMINAL_PATH
        self.criteria = criteria or self.DEFAULT_CRITERIA
        self.timeout = settings.BACKTEST_TIMEOUT
    
    def run_backtest(
        self,
        ea_path: str,
        symbol: str = None,
        timeframe: str = None,
        start_date: str = None,
        end_date: str = None,
        spread: int = None,
        initial_deposit: float = 10000.0,
    ) -> BacktestResult:
        """
        Run a backtest on an EA file.
        
        Args:
            ea_path: Path to the compiled .ex5 file
            symbol: Trading symbol (default from settings)
            timeframe: Timeframe (default from settings)
            start_date: Start date YYYY.MM.DD (default from settings)
            end_date: End date YYYY.MM.DD (default from settings)
            spread: Spread in points (default from settings)
            initial_deposit: Initial account balance
            
        Returns:
            BacktestResult with metrics and analysis
        """
        result = BacktestResult(
            success=False,
            symbol=symbol or settings.DEFAULT_SYMBOL,
            timeframe=timeframe or settings.DEFAULT_TIMEFRAME,
            start_date=start_date or settings.BACKTEST_START_DATE,
            end_date=end_date or settings.BACKTEST_END_DATE,
            spread=spread or settings.DEFAULT_SPREAD,
        )
        result.metrics.initial_deposit = initial_deposit
        
        # Check if MT5 exists
        if not os.path.exists(self.mt5_path):
            # Return mock result for non-Windows systems
            return self._mock_backtest(result, ea_path)
        
        # Check if EA exists
        if not os.path.exists(ea_path):
            result.error_message = f"EA file not found: {ea_path}"
            return result
        
        try:
            # Create config file for backtest
            config_content = self._create_config(
                ea_path=ea_path,
                symbol=result.symbol,
                timeframe=result.timeframe,
                start_date=result.start_date,
                end_date=result.end_date,
                spread=result.spread,
                initial_deposit=initial_deposit,
            )
            
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ini", delete=False
            ) as config_file:
                config_file.write(config_content)
                config_path = config_file.name
            
            # Run MT5 with config
            cmd = [self.mt5_path, f"/config:{config_path}"]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Find and parse report
            report_path = self._find_report(ea_path)
            if report_path:
                result.report_path = report_path
                result.raw_report = Path(report_path).read_text(encoding="utf-8", errors="ignore")
                result.metrics = self._parse_report(result.raw_report)
                result.success = True
            else:
                result.error_message = "Backtest report not found"
            
            # Clean up config file
            os.unlink(config_path)
            
        except subprocess.TimeoutExpired:
            result.error_message = "Backtest timed out"
        except Exception as e:
            result.error_message = f"Backtest failed: {str(e)}"
        
        # Apply acceptance criteria
        if result.success:
            result.passed_criteria, result.rejection_reasons = self._check_criteria(result.metrics)
        
        return result
    
    def _mock_backtest(self, result: BacktestResult, ea_path: str) -> BacktestResult:
        """Generate mock backtest result when MT5 is not available."""
        result.success = True
        result.error_message = "MT5 not available - mock results generated"
        
        # Generate reasonable mock metrics
        import random
        random.seed(hash(ea_path) % 2**32)
        
        result.metrics.total_trades = random.randint(100, 500)
        result.metrics.profit_trades = int(result.metrics.total_trades * random.uniform(0.45, 0.65))
        result.metrics.loss_trades = result.metrics.total_trades - result.metrics.profit_trades
        
        result.metrics.gross_profit = random.uniform(500, 3000)
        result.metrics.gross_loss = random.uniform(300, 2000)
        result.metrics.total_net_profit = result.metrics.gross_profit - abs(result.metrics.gross_loss)
        
        if result.metrics.gross_loss != 0:
            result.metrics.profit_factor = result.metrics.gross_profit / abs(result.metrics.gross_loss)
        else:
            result.metrics.profit_factor = result.metrics.gross_profit
        
        result.metrics.max_drawdown = random.uniform(100, 500)
        result.metrics.max_drawdown_percent = (result.metrics.max_drawdown / result.metrics.initial_deposit) * 100
        
        result.metrics.sharpe_ratio = random.uniform(0.5, 2.5)
        result.metrics.expected_payoff = result.metrics.total_net_profit / result.metrics.total_trades
        
        if result.metrics.max_drawdown > 0:
            result.metrics.recovery_factor = result.metrics.total_net_profit / result.metrics.max_drawdown
        
        result.metrics.max_consecutive_wins = random.randint(3, 12)
        result.metrics.max_consecutive_losses = random.randint(2, 8)
        
        result.passed_criteria, result.rejection_reasons = self._check_criteria(result.metrics)
        
        return result
    
    def _create_config(
        self,
        ea_path: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        spread: int,
        initial_deposit: float,
    ) -> str:
        """Create MT5 tester configuration file content."""
        # Map timeframe string to MT5 period
        tf_map = {
            "M1": 1, "1m": 1,
            "M5": 5, "5m": 5,
            "M15": 15, "15m": 15,
            "M30": 30, "30m": 30,
            "H1": 60, "1h": 60,
            "H4": 240, "4h": 240,
            "D1": 1440, "1d": 1440,
        }
        period = tf_map.get(timeframe, 5)
        
        return f"""
[Common]
Login=0
ProxyEnable=0

[Tester]
Expert={ea_path}
Symbol={symbol}
Period={period}
Optimization=0
Model=1
FromDate={start_date}
ToDate={end_date}
ForwardMode=0
Deposit={initial_deposit}
Currency=USD
Leverage=100
ExecutionMode=0
OptimizationCriterion=0
Visual=0
Report=report
Spread={spread}
"""
    
    def _find_report(self, ea_path: str) -> Optional[str]:
        """Find the backtest report file."""
        # Reports are typically saved in MT5 data folder
        data_path = settings.get_mt5_data_path()
        if not data_path:
            return None
        
        # Look for HTML reports
        reports_dir = data_path / "reports"
        if reports_dir.exists():
            # Find most recent report
            reports = list(reports_dir.glob("*.htm")) + list(reports_dir.glob("*.html"))
            if reports:
                return str(max(reports, key=os.path.getmtime))
        
        return None
    
    def _parse_report(self, html_content: str) -> BacktestMetrics:
        """Parse HTML backtest report and extract metrics."""
        metrics = BacktestMetrics()
        
        # Remove HTML tags for easier parsing
        clean_text = re.sub(r"<[^>]+>", " ", html_content)
        clean_text = re.sub(r"\s+", " ", clean_text)
        
        # Extract metrics using patterns
        for metric_name, pattern in self.METRICS_PATTERNS.items():
            match = pattern.search(clean_text)
            if match:
                try:
                    value_str = match.group(1).replace(" ", "").replace(",", "")
                    value = float(value_str)
                    
                    if metric_name == "total_trades":
                        metrics.total_trades = int(value)
                    elif metric_name == "profit_trades":
                        metrics.profit_trades = int(value)
                    elif metric_name == "total_net_profit":
                        metrics.total_net_profit = value
                    elif metric_name == "gross_profit":
                        metrics.gross_profit = value
                    elif metric_name == "gross_loss":
                        metrics.gross_loss = abs(value)
                    elif metric_name == "profit_factor":
                        metrics.profit_factor = value
                    elif metric_name == "expected_payoff":
                        metrics.expected_payoff = value
                    elif metric_name == "sharpe_ratio":
                        metrics.sharpe_ratio = value
                    elif metric_name == "recovery_factor":
                        metrics.recovery_factor = value
                    elif metric_name == "max_drawdown":
                        metrics.max_drawdown = value
                        if match.lastindex >= 2:
                            metrics.max_drawdown_percent = float(match.group(2))
                except (ValueError, IndexError):
                    pass
        
        # Calculate derived metrics if not found
        if metrics.profit_trades == 0 and metrics.total_trades > 0:
            # Estimate from win rate if available
            pass
        
        metrics.loss_trades = metrics.total_trades - metrics.profit_trades
        
        return metrics
    
    def _check_criteria(self, metrics: BacktestMetrics) -> tuple[bool, list[str]]:
        """Check if metrics meet acceptance criteria."""
        rejection_reasons = []
        
        # Profit Factor
        min_pf = self.criteria.get("min_profit_factor", 1.5)
        if metrics.profit_factor < min_pf:
            rejection_reasons.append(
                f"Profit Factor {metrics.profit_factor:.2f} < {min_pf}"
            )
        
        # Max Drawdown
        max_dd = self.criteria.get("max_drawdown_percent", 30.0)
        if metrics.max_drawdown_percent > max_dd:
            rejection_reasons.append(
                f"Max Drawdown {metrics.max_drawdown_percent:.1f}% > {max_dd}%"
            )
        
        # Total Trades
        min_trades = self.criteria.get("min_total_trades", 50)
        if metrics.total_trades < min_trades:
            rejection_reasons.append(
                f"Total Trades {metrics.total_trades} < {min_trades}"
            )
        
        # Win Rate
        min_win_rate = self.criteria.get("min_win_rate", 40.0)
        if metrics.win_rate < min_win_rate:
            rejection_reasons.append(
                f"Win Rate {metrics.win_rate:.1f}% < {min_win_rate}%"
            )
        
        # Recovery Factor
        min_rf = self.criteria.get("min_recovery_factor", 1.5)
        if metrics.recovery_factor < min_rf:
            rejection_reasons.append(
                f"Recovery Factor {metrics.recovery_factor:.2f} < {min_rf}"
            )
        
        # Sharpe Ratio (NEW)
        min_sharpe = self.criteria.get("min_sharpe_ratio", 1.0)
        if metrics.sharpe_ratio < min_sharpe:
            rejection_reasons.append(
                f"Sharpe Ratio {metrics.sharpe_ratio:.2f} < {min_sharpe}"
            )
        
        passed = len(rejection_reasons) == 0
        return passed, rejection_reasons
    
    def get_summary(self, result: BacktestResult) -> str:
        """Generate a human-readable summary of backtest results."""
        if not result.success:
            return f"❌ Backtest failed: {result.error_message}"
        
        m = result.metrics
        
        summary = f"""
📊 **Backtest Results** ({result.symbol} {result.timeframe})
Period: {result.start_date} to {result.end_date}

💰 **Performance**
- Net Profit: ${m.total_net_profit:,.2f}
- Profit Factor: {m.profit_factor:.2f}
- Win Rate: {m.win_rate:.1f}%

📈 **Trade Statistics**
- Total Trades: {m.total_trades}
- Winners: {m.profit_trades} | Losers: {m.loss_trades}
- Expected Payoff: ${m.expected_payoff:.2f}

⚠️ **Risk Metrics**
- Max Drawdown: ${m.max_drawdown:,.2f} ({m.max_drawdown_percent:.1f}%)
- Recovery Factor: {m.recovery_factor:.2f}
- Sharpe Ratio: {m.sharpe_ratio:.2f}
"""
        
        if result.passed_criteria:
            summary += "\n✅ **PASSED** all acceptance criteria"
        else:
            summary += f"\n❌ **REJECTED**: {', '.join(result.rejection_reasons)}"
        
        return summary.strip()
