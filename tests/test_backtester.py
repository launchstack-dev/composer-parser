"""
Tests for the backtester functionality.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from backtester import (
    get_all_tickers,
    extract_indicator_params,
    calculate_indicators,
    download_market_data,
    load_ground_truth_data
)


class TestTickerExtraction:
    """Test cases for ticker extraction functionality."""

    def test_get_all_tickers_basic(self):
        """Test basic ticker extraction from symphony."""
        symphony = [
            "defsymphony",
            "Test Strategy",
            [
                "if",
                [">", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 200}]],
                [["asset", "TQQQ", "Test Asset"]],
                [["asset", "SPY", "Test Asset 2"]]
            ]
        ]
        
        tickers = get_all_tickers(symphony)
        expected = {'SPY', 'TQQQ'}
        assert tickers == expected

    def test_get_all_tickers_with_group(self):
        """Test ticker extraction with group operator."""
        symphony = [
            "defsymphony",
            "Group Test",
            [
                "group",
                "SPY+TQQQ+TLT",
                [["asset", "UVXY", "Test Asset"]]
            ]
        ]
        
        tickers = get_all_tickers(symphony)
        expected = {'SPY', 'TQQQ', 'TLT', 'UVXY'}
        assert tickers == expected

    def test_get_all_tickers_with_indicators(self):
        """Test ticker extraction with indicator references."""
        symphony = [
            "defsymphony",
            "Indicator Test",
            [
                "if",
                [">", ["rsi", "TQQQ", {":window": 10}], 70],
                [["asset", "SPY", "Test Asset"]],
                [["asset", "TQQQ", "Test Asset 2"]]
            ]
        ]
        
        tickers = get_all_tickers(symphony)
        expected = {'TQQQ', 'SPY'}
        assert tickers == expected

    def test_get_all_tickers_empty(self):
        """Test ticker extraction with empty symphony."""
        symphony = ["defsymphony", "Empty Strategy", []]
        
        tickers = get_all_tickers(symphony)
        assert tickers == set()

    def test_get_all_tickers_nested(self):
        """Test ticker extraction with deeply nested structure."""
        symphony = [
            "defsymphony",
            "Nested Test",
            [
                "if",
                [">", ["current-price", "SPY"], 100],
                [
                    "weight-equal",
                    [
                        ["asset", "TQQQ", "Asset 1"],
                        ["asset", "TLT", "Asset 2"]
                    ]
                ],
                [
                    "filter",
                    ["rsi", {":window": 10}],
                    ["select-top", 1],
                    [
                        ["asset", "SQQQ", "Asset 3"],
                        ["asset", "UVXY", "Asset 4"]
                    ]
                ]
            ]
        ]
        
        tickers = get_all_tickers(symphony)
        expected = {'SPY', 'TQQQ', 'TLT', 'SQQQ', 'UVXY'}
        assert tickers == expected


class TestIndicatorExtraction:
    """Test cases for indicator parameter extraction."""

    def test_extract_indicator_params_rsi(self):
        """Test RSI indicator parameter extraction."""
        symphony = [
            "defsymphony",
            "RSI Test",
            [
                "if",
                [">", ["rsi", "TQQQ", {":window": 14}], 70],
                [["asset", "SPY", "Test Asset"]],
                [["asset", "TQQQ", "Test Asset 2"]]
            ]
        ]
        
        params = extract_indicator_params(symphony)
        expected_key = ('rsi', 14)
        assert expected_key in params
        assert 'TQQQ' in params[expected_key]

    def test_extract_indicator_params_ma(self):
        """Test moving average indicator parameter extraction."""
        symphony = [
            "defsymphony",
            "MA Test",
            [
                "if",
                [">", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 50}]],
                [["asset", "TQQQ", "Test Asset"]],
                [["asset", "SPY", "Test Asset 2"]]
            ]
        ]
        
        params = extract_indicator_params(symphony)
        expected_key = ('ma', 50)
        assert expected_key in params
        assert 'SPY' in params[expected_key]

    def test_extract_indicator_params_filter(self):
        """Test indicator parameter extraction with filter operator."""
        symphony = [
            "defsymphony",
            "Filter Test",
            [
                "filter",
                ["rsi", {":window": 10}],
                ["select-top", 1],
                [
                    ["asset", "SQQQ", "Asset 1"],
                    ["asset", "TLT", "Asset 2"]
                ]
            ]
        ]
        
        params = extract_indicator_params(symphony)
        expected_key = ('rsi', 10)
        assert expected_key in params
        # Should include common filter tickers
        assert 'SQQQ' in params[expected_key]
        assert 'TLT' in params[expected_key]

    def test_extract_indicator_params_multiple(self):
        """Test extraction of multiple indicator types."""
        symphony = [
            "defsymphony",
            "Multiple Indicators",
            [
                "if",
                [
                    "and",
                    [">", ["rsi", "TQQQ", {":window": 14}], 70],
                    ["<", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 200}]]
                ],
                [["asset", "TLT", "Test Asset"]],
                [["asset", "TQQQ", "Test Asset 2"]]
            ]
        ]
        
        params = extract_indicator_params(symphony)
        
        # Check RSI
        rsi_key = ('rsi', 14)
        assert rsi_key in params
        assert 'TQQQ' in params[rsi_key]
        
        # Check MA
        ma_key = ('ma', 200)
        assert ma_key in params
        assert 'SPY' in params[ma_key]


class TestIndicatorCalculation:
    """Test cases for indicator calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample market data
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        self.market_data = {
            'SPY': pd.DataFrame({
                'Close': np.linspace(100, 110, 10),
                'Open': np.linspace(99, 109, 10),
                'High': np.linspace(101, 111, 10),
                'Low': np.linspace(98, 108, 10),
                'Volume': np.random.randint(1000000, 5000000, 10)
            }, index=dates),
            'TQQQ': pd.DataFrame({
                'Close': np.linspace(50, 55, 10),
                'Open': np.linspace(49, 54, 10),
                'High': np.linspace(51, 56, 10),
                'Low': np.linspace(48, 53, 10),
                'Volume': np.random.randint(500000, 2000000, 10)
            }, index=dates)
        }

    def test_calculate_indicators_rsi(self):
        """Test RSI calculation."""
        indicator_params = {('rsi', 10): {'SPY', 'TQQQ'}}
        
        result = calculate_indicators(self.market_data, indicator_params)
        
        # Check that RSI columns were added
        assert 'RSI' in result['SPY'].columns
        assert 'RSI' in result['TQQQ'].columns
        
        # Check that RSI values are reasonable (0-100)
        assert result['SPY']['RSI'].min() >= 0
        assert result['SPY']['RSI'].max() <= 100
        assert result['TQQQ']['RSI'].min() >= 0
        assert result['TQQQ']['RSI'].max() <= 100

    def test_calculate_indicators_ma(self):
        """Test moving average calculation."""
        indicator_params = {('ma', 5): {'SPY'}}
        
        result = calculate_indicators(self.market_data, indicator_params)
        
        # Check that MA column was added
        assert 'MA5' in result['SPY'].columns
        
        # Check that MA values are reasonable
        assert not result['SPY']['MA5'].isna().all()
        assert result['SPY']['MA5'].iloc[-1] > 0

    def test_calculate_indicators_current_price(self):
        """Test current price calculation."""
        indicator_params = {}
        
        result = calculate_indicators(self.market_data, indicator_params)
        
        # Check that current_price column was added
        assert 'current_price' in result['SPY'].columns
        assert 'current_price' in result['TQQQ'].columns
        
        # Check that current_price equals Close
        pd.testing.assert_series_equal(
            result['SPY']['current_price'],
            result['SPY']['Close']
        )

    def test_calculate_indicators_multiple(self):
        """Test calculation of multiple indicators."""
        indicator_params = {
            ('rsi', 10): {'SPY'},
            ('ma', 5): {'SPY', 'TQQQ'},
            ('ma', 10): {'TQQQ'}
        }
        
        result = calculate_indicators(self.market_data, indicator_params)
        
        # Check all indicators were calculated
        assert 'RSI' in result['SPY'].columns
        assert 'MA5' in result['SPY'].columns
        assert 'MA5' in result['TQQQ'].columns
        assert 'MA10' in result['TQQQ'].columns

    def test_calculate_indicators_missing_ticker(self):
        """Test handling of missing tickers in indicator params."""
        indicator_params = {('rsi', 10): {'MISSING_TICKER'}}
        
        # Should not raise an exception
        result = calculate_indicators(self.market_data, indicator_params)
        assert result == self.market_data


class TestDataDownload:
    """Test cases for market data download functionality."""

    @patch('backtester.yf.download')
    def test_download_market_data_single_ticker(self, mock_download):
        """Test downloading data for a single ticker."""
        # Mock the download response
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102],
            'Open': [99, 100, 101],
            'High': [101, 102, 103],
            'Low': [98, 99, 100],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        
        mock_download.return_value = mock_data
        
        tickers = ['SPY']
        start_date = '2024-01-01'
        end_date = '2024-01-03'
        
        result = download_market_data(tickers, start_date, end_date)
        
        assert 'SPY' in result
        assert len(result['SPY']) == 3
        assert 'Close' in result['SPY'].columns

    @patch('backtester.yf.download')
    def test_download_market_data_multiple_tickers(self, mock_download):
        """Test downloading data for multiple tickers."""
        # Mock the download response for multiple tickers
        mock_data = {
            'SPY': pd.DataFrame({
                'Close': [100, 101, 102],
                'Open': [99, 100, 101],
                'High': [101, 102, 103],
                'Low': [98, 99, 100],
                'Volume': [1000000, 1100000, 1200000]
            }, index=pd.date_range('2024-01-01', periods=3, freq='D')),
            'TQQQ': pd.DataFrame({
                'Close': [50, 51, 52],
                'Open': [49, 50, 51],
                'High': [51, 52, 53],
                'Low': [48, 49, 50],
                'Volume': [500000, 550000, 600000]
            }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        }
        
        mock_download.return_value = mock_data
        
        tickers = ['SPY', 'TQQQ']
        start_date = '2024-01-01'
        end_date = '2024-01-03'
        
        result = download_market_data(tickers, start_date, end_date)
        
        assert 'SPY' in result
        assert 'TQQQ' in result
        assert len(result['SPY']) == 3
        assert len(result['TQQQ']) == 3


class TestGroundTruthData:
    """Test cases for ground truth data loading."""

    def test_load_ground_truth_data_success(self, tmp_path):
        """Test successful loading of ground truth data."""
        # Create a temporary CSV file
        csv_content = """Date,Day Traded,SPY,TQQQ,TLT
2024-01-01,1,50.0,25.0,25.0
2024-01-02,1,60.0,20.0,20.0
2024-01-03,1,40.0,30.0,30.0"""
        
        csv_file = tmp_path / "test_ground_truth.csv"
        csv_file.write_text(csv_content)
        
        result = load_ground_truth_data(str(csv_file))
        
        assert not result.empty
        assert len(result) == 3
        assert 'SPY' in result.columns
        assert 'TQQQ' in result.columns
        assert 'TLT' in result.columns
        assert result.index.name == 'Date'

    def test_load_ground_truth_data_file_not_found(self):
        """Test handling of missing ground truth file."""
        result = load_ground_truth_data("nonexistent_file.csv")
        
        assert result.empty

    def test_load_ground_truth_data_invalid_format(self, tmp_path):
        """Test handling of invalid CSV format."""
        # Create a malformed CSV file
        csv_content = """Invalid,Format,File
This,is,not
a,proper,csv"""
        
        csv_file = tmp_path / "invalid_ground_truth.csv"
        csv_file.write_text(csv_content)
        
        # Should handle gracefully
        result = load_ground_truth_data(str(csv_file))
        assert result.empty


if __name__ == "__main__":
    pytest.main([__file__]) 