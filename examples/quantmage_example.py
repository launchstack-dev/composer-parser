#!/usr/bin/env python3
"""
Quantmage Strategy Parser Example

This example demonstrates how to use the composer-parser with Quantmage strategy files.
It shows how to parse a Quantmage JSON strategy and convert it to Composer format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from composer_parser import parse_strategy_file, parse_strategy_json
import json

def main():
    """Demonstrate Quantmage strategy parsing."""
    
    # Example 1: Parse from file
    print("=== Example 1: Parsing Quantmage Strategy from File ===")
    
    # Check if quantmage-source file exists
    quantmage_file = "quantmage-source"
    if os.path.exists(quantmage_file):
        try:
            # Parse the Quantmage strategy file
            composer_symphony = parse_strategy_file(quantmage_file)
            
            print(f"Successfully parsed Quantmage strategy!")
            print(f"Strategy name: {composer_symphony[1][1] if len(composer_symphony) > 1 else 'Unknown'}")
            print(f"Strategy description: {composer_symphony[2][1] if len(composer_symphony) > 2 else 'No description'}")
            print(f"Rebalance frequency: {composer_symphony[3][1] if len(composer_symphony) > 3 else 'Unknown'}")
            
            print("\nConverted to Composer format:")
            print(json.dumps(composer_symphony, indent=2))
            
        except Exception as e:
            print(f"Error parsing Quantmage file: {e}")
    else:
        print(f"Quantmage source file '{quantmage_file}' not found.")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Parse from JSON data
    print("=== Example 2: Parsing Quantmage Strategy from JSON Data ===")
    
    # Sample Quantmage strategy data
    sample_quantmage_strategy = {
        "name": "Sample Quantmage Strategy",
        "description": "A simple example strategy",
        "benchmark_ticker": "SPY",
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
    
    try:
        # Parse the Quantmage JSON data
        composer_symphony = parse_strategy_json(sample_quantmage_strategy)
        
        print(f"Successfully parsed sample Quantmage strategy!")
        print(f"Strategy name: {composer_symphony[1][1] if len(composer_symphony) > 1 else 'Unknown'}")
        print(f"Strategy description: {composer_symphony[2][1] if len(composer_symphony) > 2 else 'No description'}")
        
        print("\nConverted to Composer format:")
        print(json.dumps(composer_symphony, indent=2))
        
    except Exception as e:
        print(f"Error parsing sample Quantmage data: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Show format detection
    print("=== Example 3: Format Detection ===")
    
    # Test with different file types
    test_files = [
        ("symphony.json", "Composer LISP format"),
        ("quantmage-source", "Quantmage JSON format")
    ]
    
    for filename, expected_format in test_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                
                if content.startswith('{'):
                    detected_format = "Quantmage JSON"
                else:
                    detected_format = "Composer LISP"
                
                print(f"File: {filename}")
                print(f"Expected: {expected_format}")
                print(f"Detected: {detected_format}")
                print(f"Match: {'✓' if expected_format in detected_format else '✗'}")
                print()
                
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        else:
            print(f"File {filename} not found")

if __name__ == "__main__":
    main() 