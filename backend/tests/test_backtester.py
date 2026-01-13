"""
Tests for Backtester
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.backtester import Backtester, BacktestResult, BacktestMetrics


class TestBacktester:
    """Tests for the Backtester class."""
    
    @pytest.fixture
    def backtester(self):
        return Backtester()
    
    def test_mock_backtest_generates_results(self, backtester):
        """Test that mock backtest generates valid results."""
        result = backtester.run_backtest(
            ea_path="/fake/path/test_ea.mq5",
            symbol="EURUSD",
            timeframe="5m"
        )
        
        # Should use mock since MT5 not available
        assert result.success
        assert result.metrics.total_trades > 0
    
    def test_metrics_have_correct_types(self, backtester):
        """Test that metrics have correct types."""
        result = backtester.run_backtest("/fake/path.mq5")
        
        assert isinstance(result.metrics.total_trades, int)
        assert isinstance(result.metrics.profit_factor, float)
        assert isinstance(result.metrics.win_rate, float)
    
    def test_win_rate_calculation(self):
        """Test win rate property calculation."""
        metrics = BacktestMetrics(
            total_trades=100,
            profit_trades=60,
            loss_trades=40
        )
        
        assert metrics.win_rate == 60.0
    
    def test_win_rate_zero_trades(self):
        """Test win rate with zero trades."""
        metrics = BacktestMetrics(total_trades=0)
        assert metrics.win_rate == 0.0
    
    def test_is_profitable_property(self):
        """Test is_profitable property."""
        profitable = BacktestMetrics(
            profit_factor=1.5,
            total_net_profit=1000
        )
        assert profitable.is_profitable
        
        unprofitable = BacktestMetrics(
            profit_factor=0.8,
            total_net_profit=-500
        )
        assert not unprofitable.is_profitable
    
    def test_criteria_check(self, backtester):
        """Test that criteria checking works."""
        result = backtester.run_backtest("/fake/path.mq5")
        
        # passed_criteria should be boolean
        assert isinstance(result.passed_criteria, bool)
        assert isinstance(result.rejection_reasons, list)
    
    def test_summary_generation(self, backtester):
        """Test summary generation."""
        result = backtester.run_backtest("/fake/path.mq5")
        summary = backtester.get_summary(result)
        
        assert "Backtest Results" in summary
        assert result.symbol in summary


class TestBacktestCriteria:
    """Tests for backtest acceptance criteria."""
    
    def test_profit_factor_check(self):
        """Test profit factor criterion."""
        backtester = Backtester(criteria={"min_profit_factor": 1.5})
        metrics = BacktestMetrics(profit_factor=1.2)
        
        passed, reasons = backtester._check_criteria(metrics)
        assert not passed
        assert any("Profit Factor" in r for r in reasons)
    
    def test_drawdown_check(self):
        """Test max drawdown criterion."""
        backtester = Backtester(criteria={"max_drawdown_percent": 20.0})
        metrics = BacktestMetrics(max_drawdown_percent=25.0)
        
        passed, reasons = backtester._check_criteria(metrics)
        assert not passed
        assert any("Drawdown" in r for r in reasons)
    
    def test_min_trades_check(self):
        """Test minimum trades criterion."""
        backtester = Backtester(criteria={"min_total_trades": 100})
        metrics = BacktestMetrics(total_trades=50)
        
        passed, reasons = backtester._check_criteria(metrics)
        assert not passed
        assert any("Trades" in r for r in reasons)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
