# backtester.py
"""
A standalone backtesting application for Composer.trade strategies.

This script performs the following steps:
1. Loads a strategy defined in a JSON file.
2. Downloads historical market data for all required tickers using yfinance.
3. Pre-calculates all necessary technical indicators.
4. Iterates through a specified date range, day by day.
5. On each day, it uses the ComposerStrategy parser to determine the target portfolio.
6. Simulates trades (buy/sell) to align the current portfolio with the target.
7. Tracks portfolio value over time and prints a summary.
8. Validates parser accuracy against ground truth CSV data.
"""
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
from composer_parser import ComposerStrategy
from typing import Dict, List, Set

# --- Configuration ---
SYMPHONY_FILE_PATH = 'symphony.json'
GROUND_TRUTH_FILE_PATH = 'composer-tickers.csv'
START_DATE = '2011-01-01'  # Extended to earliest available data
END_DATE = '2024-12-31'    # Extended to latest available data
INITIAL_CAPITAL = 100000.0

def get_all_tickers(symphony: List) -> Set[str]:
    """Recursively finds all unique ticker symbols mentioned in the symphony."""
    tickers = set()
    
    # Use a stack for iterative traversal to avoid recursion depth limits
    stack = [symphony]
    
    while stack:
        current = stack.pop()
        if isinstance(current, list):
            # Only apply extraction logic if the list is long enough
            if len(current) >= 2:
                if current[0] == 'asset':
                    tickers.add(current[1])
                    print(f"Found asset ticker: {current[1]}")
                elif current[0] in ['current-price', 'moving-average-price', 'rsi']:
                    if isinstance(current[1], str):
                        tickers.add(current[1])
                        print(f"Found indicator ticker: {current[1]} (from {current[0]})")
                elif current[0] == 'group':
                    if isinstance(current[1], str):
                        group_tickers = current[1].split('+')
                        tickers.update(group_tickers)
                        print(f"Found group tickers: {group_tickers}")
            # Always recurse into all list elements
            for item in current:
                stack.append(item)
    print(f"Total tickers found: {tickers}")
    return tickers

def map_composer_indicators_to_pandas_ta():
    """
    Maps Composer.trade indicator names to pandas-ta equivalents.
    Returns a dictionary mapping Composer indicator names to pandas-ta function names.
    """
    return {
        'rsi': 'rsi',
        'moving-average-price': 'sma',  # Simple Moving Average
        'current-price': 'close',  # Current price is just the Close column
        # Add more mappings as needed
    }

def extract_indicator_params(symphony: List) -> dict:
    """
    Recursively extract all indicator usages and their parameters from the symphony JSON.
    Returns a dict: { (indicator, param): set([tickers]) }
    Example: { ('rsi', 10): set(['TQQQ', 'SPY']) }
    """
    indicator_params = {}
    stack = [symphony]
    while stack:
        current = stack.pop()
        if isinstance(current, list):
            if len(current) >= 2:
                if current[0] == 'rsi':
                    ticker = current[1]
                    window = 10  # default
                    if len(current) > 2 and isinstance(current[2], dict) and ':window' in current[2]:
                        window = int(current[2][':window'])
                    key = ('rsi', window)
                    if key not in indicator_params:
                        indicator_params[key] = set()
                    
                    if isinstance(ticker, str):
                        indicator_params[key].add(ticker)
                        print(f"[extract_indicator_params] Added RSI ticker: {ticker}")
                    elif isinstance(ticker, dict):
                        # This is a filter case like (rsi {:window 10}) - no specific ticker
                        # We need to find the tickers in the parent filter expression
                        print(f"[extract_indicator_params] Found filter RSI expression: {current}")
                        # For now, we'll add common tickers that might be used in filters
                        # This is a temporary fix - ideally we'd traverse up to find the filter's asset list
                        common_filter_tickers = ['SQQQ', 'TLT', 'TQQQ', 'SPY']
                        for common_ticker in common_filter_tickers:
                            indicator_params[key].add(common_ticker)
                        print(f"[extract_indicator_params] Added common filter tickers: {common_filter_tickers}")
                    else:
                        print(f"[extract_indicator_params] Skipping non-string ticker in rsi: {ticker}")
                elif current[0] == 'moving-average-price':
                    ticker = current[1]
                    window = 20  # default
                    if len(current) > 2 and isinstance(current[2], dict) and ':window' in current[2]:
                        window = int(current[2][':window'])
                    key = ('ma', window)
                    if key not in indicator_params:
                        indicator_params[key] = set()
                    if isinstance(ticker, str):
                        indicator_params[key].add(ticker)
                        print(f"[extract_indicator_params] Added MA ticker: {ticker}")
                    else:
                        print(f"[extract_indicator_params] Skipping non-string ticker in moving-average-price: {ticker}")
            for item in current:
                stack.append(item)
    
    print(f"[extract_indicator_params] Final indicator_params: {indicator_params}")
    return indicator_params

def calculate_indicators(market_data: Dict[str, pd.DataFrame], indicator_params: dict) -> Dict[str, pd.DataFrame]:
    """
    Calculates all required technical indicators for each ticker's DataFrame using the extracted parameters.
    """
    print("Calculating technical indicators...")
    for (indicator, window), tickers in indicator_params.items():
        for symbol in tickers:
            if symbol not in market_data:
                continue
            df = market_data[symbol]
            if indicator == 'rsi':
                # RSI is expected to be named 'RSI' without window suffix
                if 'RSI' not in df:
                    df['RSI'] = df.ta.rsi(length=window)
                    print(f"   Calculated RSI for {symbol}")
            elif indicator == 'ma':
                # Moving average is expected to be named 'MA{window}' (e.g., 'MA200')
                col = f'MA{window}'
                if col not in df:
                    df[col] = df['Close'].rolling(window=window).mean()
                    print(f"   Calculated {col} for {symbol}")
    
    # Always add current price for all tickers
    for symbol, df in market_data.items():
        df['current_price'] = df['Close']
        df.dropna(inplace=True)
        print(f"   {symbol}: {len(df)} rows after final dropna")
    
    print("✅ Indicator calculation complete.")
    return market_data

def download_market_data(tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    """
    Downloads historical stock data for a list of tickers from yfinance.
    """
    print(f"Downloading data for: {', '.join(tickers)}")
    data = yf.download(tickers, start=start, end=end, group_by='ticker')
    
    processed_data = {}
    for ticker in tickers:
        if len(tickers) > 1:
            df = data[ticker].copy()
        else:
            df = data.copy()
            
        print(f"   {ticker}: {len(df)} rows before dropna")
        df.dropna(inplace=True)
        print(f"   {ticker}: {len(df)} rows after dropna")
        if not df.empty:
            processed_data[ticker] = df
        else:
            print(f"   ⚠️  {ticker}: No data after processing")
            
    print("✅ Data download complete.")
    return processed_data

def load_ground_truth_data(file_path: str) -> pd.DataFrame:
    """
    Loads ground truth data from CSV file and processes it for validation.
    """
    print(f"Loading ground truth data from {file_path}...")
    try:
        # Load CSV with date parsing
        df = pd.read_csv(file_path, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
        
        print(f"✅ Ground truth data loaded successfully.")
        print(f"   - Date range: {df.index.min()} to {df.index.max()}")
        print(f"   - Total dates: {len(df)}")
        print(f"   - Columns: {list(df.columns)}")
        return df
        
    except FileNotFoundError:
        print(f"⚠️  Ground truth file not found at '{file_path}'. Validation will be skipped.")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️  Error loading ground truth data: {e}. Validation will be skipped.")
        return pd.DataFrame()

def get_parser_primary_ticker(target_portfolio: Dict[str, float]) -> str:
    """
    Extracts the primary ticker (highest weight) from the parser's target portfolio.
    """
    if not target_portfolio:
        return None
    
    # Find the ticker with the highest weight
    primary_ticker = max(target_portfolio.items(), key=lambda x: x[1])[0]
    return primary_ticker

def run_backtest():
    """
    Main function to orchestrate the backtest.
    """
    # 1. Load Symphony
    try:
        with open(SYMPHONY_FILE_PATH, 'r') as f:
            symphony_json = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Symphony file not found at '{SYMPHONY_FILE_PATH}'")
        print("Please create this file with the JSON content from Composer.trade.")
        # Create a placeholder file with the provided structure
        placeholder_symphony = [
            "defsymphony",
            "TQQQ For The Long Term | reddit version",
            [
                "if",
                [">", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 200}]],
                [
                    [
                        "weight-equal",
                        [
                            [
                                "if",
                                [">", ["rsi", "TQQQ", {":window": 10}], 79],
                                [
                                    [
                                        "group",
                                        "UVXY+VIXM+BIL+BTAL",
                                        [
                                            [
                                                "weight-specified",
                                                0.25, ["asset", "UVXY", "ProShares Ultra VIX Short-Term Futures ETF"],
                                                0.25, ["asset", "VIXM", "ProShares VIX Mid-Term Futures ETF"],
                                                0.25, ["asset", "BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF"],
                                                0.25, ["asset", "BTAL", "AGF U.S. Market Neutral Anti-Beta Fund"]
                                            ]
                                        ]
                                    ]
                                ],
                                [
                                    [
                                        "weight-equal",
                                        [
                                            [
                                                "if",
                                                [">", ["rsi", "SPY", {":window": 10}], 80],
                                                [
                                                    [
                                                        "group",
                                                        "VIXY+VIXM+BIL+BTAL",
                                                        [
                                                            [
                                                                "weight-specified",
                                                                0.25, ["asset", "UVXY", "ProShares Ultra VIX Short-Term Futures ETF"],
                                                                0.25, ["asset", "VIXM", "ProShares VIX Mid-Term Futures ETF"],
                                                                0.25, ["asset", "BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF"],
                                                                0.25, ["asset", "BTAL", "AGF U.S. Market Neutral Anti-Beta Fund"]
                                                            ]
                                                        ]
                                                    ]
                                                ],
                                                [
                                                    [
                                                        "weight-equal",
                                                        [
                                                            [
                                                                "if",
                                                                ["<", ["rsi", "XLK", {":window": 10}], 31],
                                                                [["asset", "TECL", "Direxion Daily Technology Bull 3x Shares"]],
                                                                [
                                                                    [
                                                                        "weight-equal",
                                                                        [
                                                                            [
                                                                                "if",
                                                                                ["<", ["rsi", "SPY", {":window": 10}], 30],
                                                                                [["asset", "UPRO", "ProShares UltraPro S&P500"]],
                                                                                [["asset", "TQQQ", "ProShares Trust - ProShares UltraPro QQQ 3x Shares"]]
                                                                            ]
                                                                        ]
                                                                    ]
                                                                ]
                                                            ]
                                                        ]
                                                    ]
                                                ]
                                            ]
                                        ]
                                    ]
                                ]
                            ]
                        ]
                    ]
                ],
                [
                    [
                        "weight-equal",
                        [
                            [
                                "if",
                                ["<", ["rsi", "TQQQ", {":window": 10}], 31],
                                [
                                    ["asset", "TECL", "Direxion Daily Technology Bull 3x Shares"],
                                    ["asset", "BIL", "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF"]
                                ],
                                [
                                    [
                                        "weight-equal",
                                        [
                                            [
                                                "if",
                                                ["<", ["rsi", "SPY", {":window": 10}], 30],
                                                [
                                                    ["asset", "UPRO", "ProShares UltraPro S&P500"],
                                                    ["asset", "BIL", "SPDR Series Trust - SPDR Bloomberg 1-3 Month T-Bill ETF"]
                                                ],
                                                [
                                                    [
                                                        "weight-equal",
                                                        [
                                                            [
                                                                "if",
                                                                ["<", ["current-price", "TQQQ"], ["moving-average-price", "TQQQ", {":window": 20}]],
                                                                [
                                                                    [
                                                                        "weight-equal",
                                                                        [
                                                                            [
                                                                                "filter",
                                                                                ["rsi", {":window": 10}],
                                                                                ["select-top", 1],
                                                                                [
                                                                                    ["asset", "SQQQ", "ProShares UltraPro Short QQQ"],
                                                                                    ["asset", "TLT", "iShares 20+ Year Treasury Bond ETF"]
                                                                                ]
                                                                            ]
                                                                        ]
                                                                    ]
                                                                ],
                                                                [
                                                                    [
                                                                        "weight-equal",
                                                                        [
                                                                            [
                                                                                "if",
                                                                                ["<", ["rsi", "SQQQ", {":window": 10}], 31],
                                                                                [["asset", "SQQQ", "ProShares UltraPro Short QQQ"]],
                                                                                [["asset", "TQQQ", "ProShares UltraPro QQQ"]]
                                                                            ]
                                                                        ]
                                                                    ]
                                                                ]
                                                            ]
                                                        ]
                                                    ]
                                                ]
                                            ]
                                        ]
                                    ]
                                ]
                            ]
                        ]
                    ]
                ]
            ]
        ]
        with open(SYMPHONY_FILE_PATH, 'w') as f:
            json.dump(placeholder_symphony, f, indent=2)
        print(f"A placeholder '{SYMPHONY_FILE_PATH}' has been created. Please verify its content.")
        return

    # 2. Load Ground Truth Data
    ground_truth_df = load_ground_truth_data(GROUND_TRUTH_FILE_PATH)

    # 3. Get tickers, download data, and calculate indicators
    all_tickers = list(get_all_tickers(symphony_json))
    indicator_params = extract_indicator_params(symphony_json)
    market_data = download_market_data(all_tickers, START_DATE, END_DATE)
    market_data = calculate_indicators(market_data, indicator_params)

    # 4. Initialize Strategy and Backtest Environment
    strategy = ComposerStrategy(symphony_json, market_data)
    
    portfolio = {'cash': INITIAL_CAPITAL}
    holdings = {} # { 'TICKER': num_shares }
    portfolio_history = []

    # Initialize validation counters
    validation_matches = 0
    validation_mismatches = 0
    days_validated = 0
    mismatch_details = []  # <-- Add this to store mismatch info

    # Get the intersection of available dates across all tickers
    common_dates = None
    for symbol in all_tickers:
        if common_dates is None:
            common_dates = market_data[symbol].index
        else:
            common_dates = common_dates.intersection(market_data[symbol].index)

    print(f"\nRunning backtest from {common_dates.min().strftime('%Y-%m-%d')} to {common_dates.max().strftime('%Y-%m-%d')}...")

    # 5. Backtesting Loop
    for date in common_dates:
        # Calculate current portfolio value
        current_value = portfolio['cash']
        for symbol, shares in holdings.items():
            current_value += shares * market_data[symbol].asof(date)['Close']
        
        portfolio_history.append({'Date': date, 'Value': current_value})

        # Get target portfolio for the day
        try:
            target_portfolio = strategy.get_target_portfolio(date)
        except ValueError as e:
            print(f"SKIP {date.strftime('%Y-%m-%d')}: Could not evaluate strategy. Reason: {e}")
            continue
        except Exception as e:
            print(f"ERROR {date.strftime('%Y-%m-%d')}: Unexpected error: {e}")
            continue

        # Debug: Print target portfolio for first few days
        if len(portfolio_history) < 5:
            print(f"DEBUG {date.strftime('%Y-%m-%d')}: Target portfolio = {target_portfolio}")

        # Validation Block
        if not ground_truth_df.empty:
            # Get parser's selected tickers (all with weight > 0)
            parser_tickers = set([t for t, w in target_portfolio.items() if w > 0])

            # Get ground truth tickers (all with nonzero allocation)
            ground_truth_tickers = set()
            if date in ground_truth_df.index:
                # The CSV has multiple ticker columns with percentage allocations
                # Skip the first two columns (Date, Day Traded) and check each ticker column
                ticker_columns = [col for col in ground_truth_df.columns if col not in ['Date', 'Day Traded']]
                
                for col in ticker_columns:
                    val = ground_truth_df.loc[date, col]
                    if isinstance(val, str) and val != '-' and val.strip() != '':
                        try:
                            # Remove '%' and convert to float
                            allocation = float(val.replace('%', ''))
                            if allocation > 0:
                                ground_truth_tickers.add(col)
                        except (ValueError, AttributeError):
                            continue

                days_validated += 1
                if parser_tickers == ground_truth_tickers:
                    validation_matches += 1
                else:
                    validation_mismatches += 1
                    mismatch_details.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'parser': sorted(parser_tickers),
                        'ground_truth': sorted(ground_truth_tickers)
                    })
                    print(f"❌ SET MISMATCH on {date.strftime('%Y-%m-%d')}: Parser {sorted(parser_tickers)}, Ground Truth {sorted(ground_truth_tickers)}")
                    
                    # Debug: Show RSI values for relevant tickers on mismatch dates
                    print(f"   📊 RSI Values on {date.strftime('%Y-%m-%d')}:")
                    for ticker in ['SQQQ', 'TLT', 'TQQQ', 'SPY']:
                        if ticker in market_data:
                            try:
                                rsi_value = market_data[ticker].loc[date, 'RSI']
                                print(f"      {ticker}: RSI = {rsi_value:.2f}")
                            except (KeyError, IndexError):
                                print(f"      {ticker}: RSI = N/A")
                    print()
            else:
                if days_validated < 5:
                    print(f"⚠️  Date {date.strftime('%Y-%m-%d')} not found in ground truth data")
        else:
            print("⚠️  Ground truth DataFrame is empty")

        # Rebalance portfolio
        # First, sell positions that are no longer in the target portfolio
        assets_to_sell = set(holdings.keys()) - set(target_portfolio.keys())
        for symbol in list(assets_to_sell):
            price = market_data[symbol].asof(date)['Close']
            portfolio['cash'] += holdings[symbol] * price
            print(f"{date.strftime('%Y-%m-%d')} - SELL: {holdings[symbol]} shares of {symbol} at ${price:.2f}")
            del holdings[symbol]

        # Second, adjust weights for all target assets
        for symbol, target_weight in target_portfolio.items():
            target_value = current_value * target_weight
            price = market_data[symbol].asof(date)['Close']
            target_shares = target_value / price
            
            current_shares = holdings.get(symbol, 0)
            shares_to_trade = target_shares - current_shares

            if shares_to_trade > 0: # Buy
                cost = shares_to_trade * price
                if portfolio['cash'] >= cost:
                    portfolio['cash'] -= cost
                    holdings[symbol] = holdings.get(symbol, 0) + shares_to_trade
                    print(f"{date.strftime('%Y-%m-%d')} - BUY: {shares_to_trade:.2f} shares of {symbol} at ${price:.2f}")
            elif shares_to_trade < 0: # Sell
                shares_to_sell = abs(shares_to_trade)
                proceeds = shares_to_sell * price
                portfolio['cash'] += proceeds
                holdings[symbol] -= shares_to_sell
                print(f"{date.strftime('%Y-%m-%d')} - SELL: {shares_to_sell:.2f} shares of {symbol} at ${price:.2f}")

    # 6. Generate Validation Report
    if not ground_truth_df.empty and days_validated > 0:
        accuracy = (validation_matches / days_validated) * 100
        print("\n--- Parser Accuracy Report (Set Comparison) ---")
        print("Comparison against composer-tickers.csv:")
        print(f"- Total Days Validated: {days_validated}")
        print(f"- Set Matches:          {validation_matches}")
        print(f"- Set Mismatches:       {validation_mismatches}")
        print(f"- Accuracy:             {accuracy:.2f}%")
        print("--------------------------")
        if mismatch_details:
            print("\n--- Mismatch Details ---")
            print(f"{'Date':<12} | {'Parser Tickers':<30} | {'Ground Truth Tickers':<30}")
            print("-"*80)
            for m in mismatch_details:
                print(f"{m['date']:<12} | {', '.join(m['parser']):<30} | {', '.join(m['ground_truth']):<30}")
            print("-"*80)

    # 7. Print Results
    history_df = pd.DataFrame(portfolio_history)
    history_df.set_index('Date', inplace=True)
    
    print("\n--- Backtest Results ---")
    print(f"Initial Portfolio Value: ${INITIAL_CAPITAL:,.2f}")
    print(f"Final Portfolio Value:   ${history_df['Value'].iloc[-1]:,.2f}")
    
    total_return = (history_df['Value'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
    print(f"Total Return:            {total_return:.2f}%")

    # Simple Sharpe Ratio (assuming risk-free rate is 0)
    daily_returns = history_df['Value'].pct_change().dropna()
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * (252**0.5) # Annualized
        print(f"Annualized Sharpe Ratio: {sharpe_ratio:.2f}")
    else:
        print("Annualized Sharpe Ratio: N/A (insufficient data)")

    # Max Drawdown
    peak = history_df['Value'].cummax()
    drawdown = (history_df['Value'] - peak) / peak
    max_drawdown = drawdown.min() * 100
    print(f"Maximum Drawdown:        {max_drawdown:.2f}%")


if __name__ == '__main__':
    run_backtest()
