"""
Tests for Strategy Validator
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.strategy_validator import StrategyValidator, ValidationResult


class TestStrategyValidator:
    """Tests for the StrategyValidator class."""
    
    @pytest.fixture
    def validator(self):
        return StrategyValidator()
    
    @pytest.fixture
    def valid_strategy(self):
        return {
            "instruments": ["EURUSD"],
            "timeframe": "5m",
            "accountSize": 10000,
            "dailyTarget": 100,
            "sessions": ["london", "newyork"],
            "indicators": [
                {"id": "ema_8", "name": "EMA 8", "type": "EMA", "params": {"period": 8}},
                {"id": "rsi", "name": "RSI", "type": "RSI", "params": {"period": 14}},
            ],
            "entries": [
                {"id": "buy", "description": "Buy signal", "logic": "EMA > price && RSI > 50"},
            ],
            "exits": [
                {"id": "exit", "description": "Exit signal", "logic": "RSI < 30"}
            ],
            "stopLoss": {"type": "fixed", "pips": 20},
            "takeProfit": {"type": "rr", "ratio": 2},
            "maxDailyLoss": 100,
            "positionSizePercent": 1
        }
    
    def test_valid_strategy_passes(self, validator, valid_strategy):
        """Test that a valid strategy passes validation."""
        result = validator.validate(valid_strategy)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_missing_instruments_fails(self, validator, valid_strategy):
        """Test that missing instruments causes validation failure."""
        del valid_strategy["instruments"]
        result = validator.validate(valid_strategy)
        assert not result.is_valid
        assert any("instruments" in str(i.message).lower() for i in result.errors)
    
    def test_empty_instruments_fails(self, validator, valid_strategy):
        """Test that empty instruments list fails."""
        valid_strategy["instruments"] = []
        result = validator.validate(valid_strategy)
        assert not result.is_valid
    
    def test_invalid_indicator_type_warns(self, validator, valid_strategy):
        """Test that invalid indicator type generates warning."""
        valid_strategy["indicators"].append({
            "id": "unknown",
            "name": "Unknown",
            "type": "INVALID_TYPE",
            "params": {}
        })
        result = validator.validate(valid_strategy)
        # Should still be valid but with warning
        assert any("INVALID_TYPE" in str(i.message) for i in result.issues)
    
    def test_invalid_ema_period_fails(self, validator, valid_strategy):
        """Test that invalid EMA period fails validation."""
        valid_strategy["indicators"][0]["params"]["period"] = 0
        result = validator.validate(valid_strategy)
        assert any("period" in str(i.message).lower() for i in result.issues)
    
    def test_negative_stop_loss_fails(self, validator, valid_strategy):
        """Test that negative stop loss fails."""
        valid_strategy["stopLoss"]["pips"] = -10
        result = validator.validate(valid_strategy)
        assert not result.is_valid
    
    def test_extreme_rr_ratio_warns(self, validator, valid_strategy):
        """Test that extreme R:R ratio generates warning."""
        valid_strategy["takeProfit"]["ratio"] = 10
        result = validator.validate(valid_strategy)
        assert any("ratio" in str(i.message).lower() for i in result.warnings)
    
    def test_profitability_score_calculated(self, validator, valid_strategy):
        """Test that profitability score is calculated."""
        result = validator.validate(valid_strategy)
        assert 0 <= result.profitability_score <= 100
    
    def test_risk_score_calculated(self, validator, valid_strategy):
        """Test that risk score is calculated."""
        result = validator.validate(valid_strategy)
        assert 0 <= result.risk_score <= 100
    
    def test_summary_generated(self, validator, valid_strategy):
        """Test that summary is generated."""
        result = validator.validate(valid_strategy)
        assert result.summary
        assert len(result.summary) > 0


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_errors_property(self):
        """Test that errors property filters correctly."""
        from core.strategy_validator import ValidationIssue, Severity
        
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(Severity.ERROR, "error", "Error message"),
                ValidationIssue(Severity.WARNING, "warning", "Warning message"),
            ]
        )
        
        assert len(result.errors) == 1
        assert result.errors[0].severity == Severity.ERROR
    
    def test_warnings_property(self):
        """Test that warnings property filters correctly."""
        from core.strategy_validator import ValidationIssue, Severity
        
        result = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(Severity.ERROR, "error", "Error message"),
                ValidationIssue(Severity.WARNING, "warning", "Warning message"),
            ]
        )
        
        assert len(result.warnings) == 1
        assert result.warnings[0].severity == Severity.WARNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
