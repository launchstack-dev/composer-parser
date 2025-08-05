#!/usr/bin/env python3
"""
Simple Usage Example

This example demonstrates how to use the Composer Parser API
for easy integration into trading applications.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import date
import pandas as pd
from composer_parser import ComposerAPI, quick_analysis, get_daily_selections


def example_basic_usage():
    """Example of basic usage with the ComposerAPI class."""
    print("=== Basic Usage Example ===")
    
    # Initialize the API
    api = ComposerAPI('symphony.json')
    
    # Load the strategy with market data
    strategy_info = api.load_strategy()
    print(f"Loaded strategy with {len(strategy_info['tickers'])} tickers")
    print(f"Available tickers: {strategy_info['tickers']}")
    print(f"Data range: {strategy_info['data_range']}")
    
    # Get a specific day's selection
    selection = api.get_daily_selection('2024-01-02')
    print(f"Selection for 2024-01-02: {selection}")
    
    # Get selections for a period
    selections = api.get_selections_for_period('2024-01-01', '2024-01-05')
    print(f"Got {len(selections)} selections for the period")
    
    # Get market data for a ticker
    spy_data = api.get_market_data('SPY', '2024-01-01', '2024-01-05')
    print(f"SPY data shape: {spy_data.shape}")
    print(f"SPY columns: {list(spy_data.columns)}")


def example_quick_functions():
    """Example using the quick convenience functions."""
    print("\n=== Quick Functions Example ===")
    
    # Quick analysis
    results = quick_analysis('symphony.json')
    print(f"Quick analysis completed: {results['total_days_analyzed']} days analyzed")
    
    # Get daily selections
    selections = get_daily_selections('symphony.json', '2024-01-01', '2024-01-10')
    print(f"Got {len(selections)} daily selections")
    
    # Show first few selections
    for i, selection in enumerate(selections[:3]):
        print(f"  {selection['date']}: {selection['selected_tickers']}")


def example_integration():
    """Example of how to integrate into a trading application."""
    print("\n=== Integration Example ===")
    
    # Initialize API
    api = ComposerAPI('symphony.json')
    api.load_strategy()
    
    # Simulate a trading loop
    dates = ['2024-01-02', '2024-01-03', '2024-01-04']
    
    for date in dates:
        # Get strategy selection for the day
        selection = api.get_daily_selection(date)
        
        # In a real trading app, you would:
        # 1. Check current positions
        # 2. Compare with target selection
        # 3. Generate orders to rebalance
        # 4. Execute trades
        
        print(f"Date: {date}")
        print(f"  Target allocation: {selection}")
        print(f"  Actions needed: Rebalance to match target")
        print()


def debug_today_decision():
    """Debug and print the decision path for today's selection."""
    logging.info("\n=== Debug Today's Decision ===")
    today = date.today().strftime('%Y-%m-%d')
    api = ComposerAPI('symphony.json')
    api.load_strategy()
    selection = api.get_daily_selection(today)
    logging.info(f"Today's date: {today}")
    logging.info(f"Today's selection: {selection}")

    # Print last available date in SPY DataFrame
    try:
        spy_df = api.get_market_data('SPY')
        last_date = spy_df.index[-1]
        logging.info(f"SPY last available date in DataFrame: {last_date}")
        logging.info(f"SPY DataFrame index dtype: {spy_df.index.dtype}")
    except Exception as e:
        logging.info(f"Could not get SPY DataFrame: {e}")

    # Print regime and indicator data for key tickers
    tickers = ['SPY', 'TQQQ', 'SQQQ', 'XLK', 'TECL', 'BIL', 'UPRO', 'TLT']
    for ticker in tickers:
        try:
            df = api.get_market_data(ticker)
            row = df.loc[pd.to_datetime(today)]
            logging.info(f"\n{ticker}:")
            for col in row.index:
                if 'MA_' in col or 'RSI_' in col or col in ['Close', 'current_price']:
                    logging.info(f"  {col}: {row[col]}")
        except Exception as e:
            logging.info(f"  {ticker}: No data for today ({e})")

    # Print regime logic (SPY > MA_200, etc.)
    try:
        spy = api.get_market_data('SPY').loc[pd.to_datetime(today)]
        spy_close = spy['Close']
        spy_ma200 = spy.get('MA_200', float('nan'))
        spy_rsi10 = spy.get('RSI_10', float('nan'))
        logging.info(f"\nRegime checks:")
        logging.info(f"  SPY Close: {spy_close}")
        logging.info(f"  SPY MA_200: {spy_ma200}")
        logging.info(f"  SPY > MA_200: {spy_close > spy_ma200 if not pd.isna(spy_ma200) else 'N/A'}")
        logging.info(f"  SPY RSI_10: {spy_rsi10}")
    except Exception as e:
        logging.info(f"  Regime data unavailable: {e}")


if __name__ == "__main__":
    print("Composer Parser API Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_quick_functions()
        example_integration()
        debug_today_decision()
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure you have a valid symphony.json file in the current directory.") 