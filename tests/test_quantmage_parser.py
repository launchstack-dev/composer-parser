#!/usr/bin/env python3
"""
Tests for the Quantmage parser functionality.
"""

import unittest
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from composer_parser import parse_quantmage_json, parse_quantmage_file


class TestQuantmageParser(unittest.TestCase):
    """Test cases for Quantmage parser functionality."""
    
    def test_simple_ticker_incantation(self):
        """Test parsing a simple ticker incantation."""
        quantmage_strategy = {
            "name": "Simple Ticker Strategy",
            "description": "A simple strategy with one ticker",
            "incantation": {
                "incantation_type": "Ticker",
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust"
            }
        }
        
        result = parse_quantmage_json(quantmage_strategy)
        
        self.assertEqual(result[0], "symphony")
        self.assertEqual(result[1][1], "Simple Ticker Strategy")
        self.assertEqual(result[2][1], "A simple strategy with one ticker")
        self.assertEqual(result[3][1], "daily")
        self.assertEqual(result[4][1], 0.05)
        
        # Check the asset structure
        asset_expr = result[5]
        self.assertEqual(asset_expr[0], "asset")
        self.assertEqual(asset_expr[1][1], "SPY")
        self.assertEqual(asset_expr[2][1], "SPDR S&P 500 ETF Trust")
        self.assertEqual(asset_expr[3][1], "XNAS")
    
    def test_ifelse_incantation(self):
        """Test parsing an IfElse incantation."""
        quantmage_strategy = {
            "name": "IfElse Strategy",
            "description": "A strategy with conditional logic",
            "incantation": {
                "incantation_type": "IfElse",
                "condition": {
                    "condition_type": "SingleCondition",
                    "greater_than": True,
                    "lh_indicator": {
                        "type": "RelativeStrengthIndex",
                        "window": 14
                    },
                    "lh_ticker_symbol": "SPY",
                    "rh_value": 70.0,
                    "type": "IndicatorAndNumber"
                },
                "then_incantation": {
                    "incantation_type": "Ticker",
                    "symbol": "QQQ",
                    "name": "Invesco QQQ Trust"
                },
                "else_incantation": {
                    "incantation_type": "Ticker",
                    "symbol": "BIL",
                    "name": "SPDR Bloomberg 1-3 Month T-Bill ETF"
                }
            }
        }
        
        result = parse_quantmage_json(quantmage_strategy)
        
        # Check the if structure
        if_expr = result[5]
        self.assertEqual(if_expr[0], "if")
        
        # Check condition
        condition = if_expr[1]
        self.assertEqual(condition[0], "if-child")
        self.assertEqual(condition[1][1], "gt")
        self.assertEqual(condition[2][1], "relative-strength-index")
        self.assertEqual(condition[3][1], "SPY")
        self.assertEqual(condition[4][1], {"window": 14})
        self.assertEqual(condition[5][1], 70.0)
        self.assertEqual(condition[6][1], True)
        
        # Check then branch
        then_branch = if_expr[2]
        self.assertEqual(then_branch[0], "asset")
        self.assertEqual(then_branch[1][1], "QQQ")
        
        # Check else branch
        else_branch = if_expr[3]
        self.assertEqual(else_branch[0], "asset")
        self.assertEqual(else_branch[1][1], "BIL")
    
    def test_weighted_incantation(self):
        """Test parsing a Weighted incantation."""
        quantmage_strategy = {
            "name": "Weighted Strategy",
            "description": "A strategy with multiple weighted assets",
            "incantation": {
                "incantation_type": "Weighted",
                "incantations": [
                    {
                        "incantation_type": "Ticker",
                        "symbol": "SPY",
                        "name": "SPDR S&P 500 ETF Trust"
                    },
                    {
                        "incantation_type": "Ticker",
                        "symbol": "QQQ",
                        "name": "Invesco QQQ Trust"
                    }
                ]
            }
        }
        
        result = parse_quantmage_json(quantmage_strategy)
        
        # Check the weighted structure
        weighted_expr = result[5]
        self.assertEqual(weighted_expr[0], "wt-cash-equal")
        self.assertEqual(len(weighted_expr[1]), 2)
        
        # Check first asset
        asset1 = weighted_expr[1][0]
        self.assertEqual(asset1[0], "asset")
        self.assertEqual(asset1[1][1], "SPY")
        
        # Check second asset
        asset2 = weighted_expr[1][1]
        self.assertEqual(asset2[0], "asset")
        self.assertEqual(asset2[1][1], "QQQ")
    
    def test_filtered_incantation(self):
        """Test parsing a Filtered incantation."""
        quantmage_strategy = {
            "name": "Filtered Strategy",
            "description": "A strategy with filtering",
            "incantation": {
                "incantation_type": "Filtered",
                "incantations": [
                    {
                        "incantation_type": "Ticker",
                        "symbol": "SPY",
                        "name": "SPDR S&P 500 ETF Trust"
                    },
                    {
                        "incantation_type": "Ticker",
                        "symbol": "QQQ",
                        "name": "Invesco QQQ Trust"
                    }
                ],
                "sort_indicator": {
                    "type": "RelativeStrengthIndex",
                    "window": 14
                },
                "count": 1,
                "bottom": False
            }
        }
        
        result = parse_quantmage_json(quantmage_strategy)
        
        # Check the filter structure
        filter_expr = result[5]
        self.assertEqual(filter_expr[0], "filter")
        self.assertEqual(filter_expr[1][1], "relative-strength-index")
        self.assertEqual(filter_expr[2][1], {"window": 14})
        self.assertEqual(filter_expr[3][1], 1)
        self.assertEqual(filter_expr[4][1], "top")
        self.assertEqual(filter_expr[5][1], 14)
        
        # Check assets
        self.assertEqual(len(filter_expr[6:]), 2)
        self.assertEqual(filter_expr[6][0], "asset")
        self.assertEqual(filter_expr[6][1][1], "SPY")
        self.assertEqual(filter_expr[7][0], "asset")
        self.assertEqual(filter_expr[7][1][1], "QQQ")
    
    def test_indicator_mapping(self):
        """Test that Quantmage indicators are correctly mapped to Composer indicators."""
        indicator_tests = [
            ("RelativeStrengthIndex", "relative-strength-index"),
            ("CumulativeReturn", "cumulative-return"),
            ("Volatility", "standard-deviation-return"),
            ("MovingAverage", "moving-average-price"),
            ("ExponentialMovingAverage", "exponential-moving-average-price")
        ]
        
        for quantmage_indicator, expected_composer_indicator in indicator_tests:
            with self.subTest(quantmage_indicator=quantmage_indicator):
                quantmage_strategy = {
                    "name": f"Test {quantmage_indicator}",
                    "description": "Test indicator mapping",
                    "incantation": {
                        "incantation_type": "IfElse",
                        "condition": {
                            "condition_type": "SingleCondition",
                            "greater_than": True,
                            "lh_indicator": {
                                "type": quantmage_indicator,
                                "window": 14
                            },
                            "lh_ticker_symbol": "SPY",
                            "rh_value": 70.0,
                            "type": "IndicatorAndNumber"
                        },
                        "then_incantation": {
                            "incantation_type": "Ticker",
                            "symbol": "SPY",
                            "name": "SPDR S&P 500 ETF Trust"
                        },
                        "else_incantation": {
                            "incantation_type": "Ticker",
                            "symbol": "BIL",
                            "name": "SPDR Bloomberg 1-3 Month T-Bill ETF"
                        }
                    }
                }
                
                result = parse_quantmage_json(quantmage_strategy)
                condition = result[5][1]  # Get the condition from the if expression
                self.assertEqual(condition[2][1], expected_composer_indicator)


if __name__ == "__main__":
    unittest.main() 