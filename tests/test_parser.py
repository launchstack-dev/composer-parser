"""
Tests for the ComposerStrategy parser functionality.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from composer_parser.composer_parser import ComposerStrategy


class TestComposerStrategy:
    """Test cases for ComposerStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample market data
        self.sample_data = {
            'SPY': pd.DataFrame({
                'Close': [100, 101, 102, 103, 104],
                'RSI': [50, 51, 52, 53, 54],
                'MA200': [98, 99, 100, 101, 102],
                'current_price': [100, 101, 102, 103, 104]
            }, index=pd.date_range('2024-01-01', periods=5, freq='D')),
            'TQQQ': pd.DataFrame({
                'Close': [50, 51, 52, 53, 54],
                'RSI': [45, 46, 47, 48, 49],
                'MA20': [49, 50, 51, 52, 53],
                'current_price': [50, 51, 52, 53, 54]
            }, index=pd.date_range('2024-01-01', periods=5, freq='D'))
        }

        # Create sample symphony JSON
        self.sample_symphony = [
            "defsymphony",
            "Test Strategy",
            [
                "if",
                [">", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 200}]],
                [["asset", "TQQQ", "Test Asset"]],
                [["asset", "SPY", "Test Asset 2"]]
            ]
        ]

    def test_strategy_initialization(self):
        """Test that ComposerStrategy initializes correctly."""
        strategy = ComposerStrategy(self.sample_symphony, self.sample_data)
        assert strategy is not None
        assert hasattr(strategy, 'symphony')
        assert hasattr(strategy, 'market_data')

    def test_get_target_portfolio_basic(self):
        """Test basic portfolio calculation."""
        strategy = ComposerStrategy(self.sample_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        portfolio = strategy.get_target_portfolio(date)
        
        assert isinstance(portfolio, dict)
        assert len(portfolio) > 0
        assert all(isinstance(k, str) for k in portfolio.keys())
        assert all(isinstance(v, (int, float)) for v in portfolio.values())

    def test_get_target_portfolio_weights_sum_to_one(self):
        """Test that portfolio weights sum to approximately 1.0."""
        strategy = ComposerStrategy(self.sample_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        portfolio = strategy.get_target_portfolio(date)
        total_weight = sum(portfolio.values())
        
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected 1.0"

    def test_get_target_portfolio_with_missing_data(self):
        """Test handling of missing market data."""
        strategy = ComposerStrategy(self.sample_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        # This should not raise an exception
        portfolio = strategy.get_target_portfolio(date)
        assert isinstance(portfolio, dict)

    def test_strategy_with_complex_conditions(self):
        """Test strategy with more complex conditional logic."""
        complex_symphony = [
            "defsymphony",
            "Complex Test Strategy",
            [
                "if",
                [">", ["rsi", "TQQQ", {":window": 10}], 70],
                [["asset", "SPY", "Conservative"]],
                [
                    "if",
                    ["<", ["rsi", "TQQQ", {":window": 10}], 30],
                    [["asset", "TQQQ", "Aggressive"]],
                    [["asset", "SPY", "Neutral"]]
                ]
            ]
        ]
        
        strategy = ComposerStrategy(complex_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        portfolio = strategy.get_target_portfolio(date)
        assert isinstance(portfolio, dict)
        assert len(portfolio) > 0

    def test_weight_equal_operator(self):
        """Test weight-equal operator functionality."""
        weight_equal_symphony = [
            "defsymphony",
            "Weight Equal Test",
            [
                "weight-equal",
                [
                    ["asset", "SPY", "Asset 1"],
                    ["asset", "TQQQ", "Asset 2"]
                ]
            ]
        ]
        
        strategy = ComposerStrategy(weight_equal_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        portfolio = strategy.get_target_portfolio(date)
        
        # Should have equal weights
        weights = list(portfolio.values())
        assert len(weights) == 2
        assert abs(weights[0] - weights[1]) < 0.01

    def test_filter_operator(self):
        """Test filter operator functionality."""
        filter_symphony = [
            "defsymphony",
            "Filter Test",
            [
                "filter",
                ["rsi", {":window": 10}],
                ["select-top", 1],
                [
                    ["asset", "SPY", "Asset 1"],
                    ["asset", "TQQQ", "Asset 2"]
                ]
            ]
        ]
        
        strategy = ComposerStrategy(filter_symphony, self.sample_data)
        date = pd.Timestamp('2024-01-03')
        
        portfolio = strategy.get_target_portfolio(date)
        assert isinstance(portfolio, dict)
        assert len(portfolio) > 0

    def test_invalid_symphony_format(self):
        """Test handling of invalid symphony format."""
        invalid_symphony = ["invalid", "format"]
        
        with pytest.raises(ValueError):
            ComposerStrategy(invalid_symphony, self.sample_data)

    def test_missing_market_data(self):
        """Test handling of missing market data."""
        strategy = ComposerStrategy(self.sample_symphony, {})
        date = pd.Timestamp('2024-01-03')
        
        with pytest.raises(ValueError):
            strategy.get_target_portfolio(date)

    def test_date_out_of_range(self):
        """Test handling of dates outside available data range."""
        strategy = ComposerStrategy(self.sample_symphony, self.sample_data)
        date = pd.Timestamp('2020-01-01')  # Date before available data
        
        with pytest.raises(ValueError):
            strategy.get_target_portfolio(date)


class TestParserEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_symphony(self):
        """Test handling of empty symphony."""
        with pytest.raises(ValueError):
            ComposerStrategy([], {})

    def test_none_symphony(self):
        """Test handling of None symphony."""
        with pytest.raises(ValueError):
            ComposerStrategy(None, {})

    def test_malformed_asset_definition(self):
        """Test handling of malformed asset definitions."""
        malformed_symphony = [
            "defsymphony",
            "Malformed Test",
            [["asset", "SPY"]]  # Missing description
        ]
        
        # This should not raise an exception but handle gracefully
        strategy = ComposerStrategy(malformed_symphony, {})
        assert strategy is not None


if __name__ == "__main__":
    pytest.main([__file__]) 