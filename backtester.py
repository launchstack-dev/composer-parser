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
from composer_parser.composer_parser import ComposerStrategy
from typing import Dict, List, Set

# --- Configuration ---
SYMPHONY_FILE_PATH = 'symphony.json'
GROUND_TRUTH_FILE_PATH = 'composer-tickers.csv'
#START_DATE = '2011-01-01'  # Extended to earliest available data
#END_DATE = '2024-12-31'    # Extended to latest available data
# Backtest period (the actual period we want to test)
BACKTEST_START = '2024-01-01'
BACKTEST_END = '2024-12-31'

# Data download period (includes warm-up buffer for indicators)
# Calculate how much earlier we need to start to have enough data for the largest indicator window
MAX_INDICATOR_WINDOW = 200  # 200-day MA is the largest window
WARM_UP_BUFFER = 50  # Extra buffer days
START_DATE = '2023-01-01'  # Start early enough to have warm-up data for 2024 backtest
END_DATE = '2024-12-31'


INITIAL_CAPITAL = 100000.0

# Trading constraints for more realistic backtesting
TRANSACTION_COST_PCT = 0.001  # 0.1% per trade (typical for ETFs)
MIN_TRADE_SIZE = 100.0  # Minimum trade size in dollars
REBALANCE_FREQUENCY = 1  # Rebalance every N days (1 = daily, 5 = weekly, 21 = monthly)
SLIPPAGE_PCT = 0.0005  # 0.05% slippage per trade

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
    
    # Track ticker selection frequency
    ticker_selection_count = {}
    total_trading_days = 0

    # NEW: Track daily ticker selection and weights
    daily_selection_log = []

    # Get the intersection of available dates across all tickers
    common_dates = None
    for symbol in all_tickers:
        if common_dates is None:
            common_dates = market_data[symbol].index
        else:
            common_dates = common_dates.intersection(market_data[symbol].index)

    print(f"\nRunning backtest from {common_dates.min().strftime('%Y-%m-%d')} to {common_dates.max().strftime('%Y-%m-%d')}...")
    print(f"Total trading days available: {len(common_dates)}")
    
    # Calculate warm-up period needed for indicators
    max_window = 0
    for (indicator, window), tickers in indicator_params.items():
        max_window = max(max_window, window)
    
    print(f"Max indicator window: {max_window} days")
    
    # Use the actual backtest period, but ensure we have enough warm-up data for indicators
    print(f"Data available: {common_dates.min().strftime('%Y-%m-%d')} to {common_dates.max().strftime('%Y-%m-%d')}")
    
    # Filter to the actual backtest period
    backtest_start = pd.Timestamp(BACKTEST_START)
    backtest_end = pd.Timestamp(BACKTEST_END)
    
    # Get the backtest dates (the period we actually want to test)
    backtest_dates = common_dates[(common_dates >= backtest_start) & (common_dates <= backtest_end)]
    
    print(f"✅ Backtest period: {backtest_start.strftime('%Y-%m-%d')} to {backtest_end.strftime('%Y-%m-%d')}")
    print(f"Total backtest days: {len(backtest_dates)}")
    
    # Verify we have enough warm-up data before the backtest period
    warm_up_start = backtest_start - pd.Timedelta(days=max_window + WARM_UP_BUFFER)
    warm_up_data_available = common_dates[common_dates < backtest_start]
    
    if len(warm_up_data_available) >= max_window:
        print(f"✅ Sufficient warm-up data available ({len(warm_up_data_available)} days before backtest)")
    else:
        print(f"⚠️  Warning: Limited warm-up data. Only {len(warm_up_data_available)} days available, need {max_window}")
        print(f"   Consider downloading data from an earlier date")

    # 5. Backtesting Loop
    rebalance_counter = 0
    initial_backtest_value = None
    for i, date in enumerate(backtest_dates):
        # 1. Calculate the current value of the portfolio BEFORE any trades for the day.
        # This reflects the value at market close, based on holdings from the previous day.
        current_value = portfolio['cash']
        for symbol, shares in holdings.items():
            # Use the current date's closing price to value existing holdings
            try:
                current_value += shares * market_data[symbol].asof(date)['Close']
            except (KeyError, TypeError):
                # Handle cases where a stock might not have data on a specific day
                # For simplicity, we'll skip this holding for the day
                print(f"⚠️  No data for {symbol} on {date.strftime('%Y-%m-%d')}, skipping from portfolio value")
                pass

        # 2. Record this pre-trade value for performance tracking.
        portfolio_history.append({'Date': date, 'Value': current_value})

        # Record initial value at the start of the backtest period
        if i == 0:
            initial_backtest_value = current_value

        # Only rebalance based on frequency
        rebalance_counter += 1
        if rebalance_counter < REBALANCE_FREQUENCY:
            continue

        rebalance_counter = 0

        # 3. Determine the target allocation based on today's closing data.
        try:
            target_portfolio = strategy.get_target_portfolio(date)
        except ValueError as e:
            print(f"SKIP {date.strftime('%Y-%m-%d')}: Could not evaluate strategy. Reason: {e}")
            continue
        except Exception as e:
            print(f"ERROR {date.strftime('%Y-%m-%d')}: Unexpected error: {e}")
            continue

        # Debug: Print target portfolio for first few days and track coverage
        if len(portfolio_history) < 5:
            print(f"DEBUG {date.strftime('%Y-%m-%d')}: Target portfolio = {target_portfolio}")
        
        # Track ticker selection coverage
        if target_portfolio:
            selected_tickers = list(target_portfolio.keys())
            # NEW: Log the daily selection
            daily_selection_log.append({
                'Date': date.strftime('%Y-%m-%d'),
                **{ticker: target_portfolio[ticker] for ticker in selected_tickers}
            })
            print(f"\U0001F4CA {date.strftime('%Y-%m-%d')}: Selected tickers = {selected_tickers} (weights: {[f'{w:.2f}' for w in target_portfolio.values()]})")
            
            # Debug indicator values for key tickers on first few days
            if total_trading_days < 5:
                print(f"   📈 Indicator values on {date.strftime('%Y-%m-%d')}:")
                for ticker in ['SPY', 'TQQQ', 'SQQQ']:
                    if ticker in market_data:
                        try:
                            rsi = market_data[ticker].loc[date, 'RSI'] if 'RSI' in market_data[ticker].columns else 'N/A'
                            current_price = market_data[ticker].loc[date, 'current_price']
                            if ticker == 'SPY' and 'MA200' in market_data[ticker].columns:
                                ma200 = market_data[ticker].loc[date, 'MA200']
                                print(f"      {ticker}: Price=${current_price:.2f}, RSI={rsi:.1f}, MA200=${ma200:.2f}")
                            elif ticker == 'TQQQ' and 'MA20' in market_data[ticker].columns:
                                ma20 = market_data[ticker].loc[date, 'MA20']
                                print(f"      {ticker}: Price=${current_price:.2f}, RSI={rsi:.1f}, MA20=${ma20:.2f}")
                            else:
                                print(f"      {ticker}: Price=${current_price:.2f}, RSI={rsi:.1f}")
                        except (KeyError, IndexError):
                            print(f"      {ticker}: Data not available")
                print()
            
            # Count ticker selections
            total_trading_days += 1
            for ticker in selected_tickers:
                ticker_selection_count[ticker] = ticker_selection_count.get(ticker, 0) + 1

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

        # 4. Execute trades to rebalance the portfolio.
        # Note: All calculations for trades use the 'current_value' from Step 1.

        # First, sell positions that are no longer in the target portfolio
        assets_to_sell = set(holdings.keys()) - set(target_portfolio.keys())
        for symbol in list(assets_to_sell):
            price = market_data[symbol].asof(date)['Close']
            # Apply slippage to sell price
            sell_price = price * (1 - SLIPPAGE_PCT)
            trade_value = holdings[symbol] * sell_price
            
            if trade_value >= MIN_TRADE_SIZE or i == 0:
                # Apply transaction costs
                transaction_cost = trade_value * TRANSACTION_COST_PCT
                net_proceeds = trade_value - transaction_cost
                portfolio['cash'] += net_proceeds
                print(f"{date.strftime('%Y-%m-%d')} - SELL: {holdings[symbol]:.2f} shares of {symbol} at ${sell_price:.2f} (net: ${net_proceeds:.2f})")
            del holdings[symbol]

        # Second, adjust weights for all target assets
        # KEY CHANGE: Target value is based on the pre-trade portfolio value
        for symbol, target_weight in target_portfolio.items():
            target_value = current_value * target_weight
            price = market_data[symbol].asof(date)['Close']
            target_shares = target_value / price
            
            current_shares = holdings.get(symbol, 0)
            shares_to_trade = target_shares - current_shares

            # Debug first day trading
            if i == 0:
                print(f"[DEBUG] Trading logic for {symbol}:")
                print(f"  Target weight: {target_weight}")
                print(f"  Pre-trade current value: ${current_value:.2f}")
                print(f"  Target value: ${target_value:.2f}")
                print(f"  Price: ${price:.2f}")
                print(f"  Target shares: {target_shares:.2f}")
                print(f"  Current shares: {current_shares}")
                print(f"  Shares to trade: {shares_to_trade:.2f}")
                print(f"  Trade value: ${abs(shares_to_trade * price):.2f}")
                print(f"  MIN_TRADE_SIZE: ${MIN_TRADE_SIZE:.2f}")
                print(f"  Cash available: ${portfolio['cash']:.2f}")

            # Always allow trades on the first rebalance, regardless of MIN_TRADE_SIZE
            if abs(shares_to_trade * price) < MIN_TRADE_SIZE and i != 0:
                continue  # Skip trades below minimum size

            if shares_to_trade > 0: # Buy
                # Apply slippage to buy price
                buy_price = price * (1 + SLIPPAGE_PCT)
                # Calculate max shares affordable given slippage and transaction cost
                max_affordable_shares = portfolio['cash'] / (buy_price * (1 + TRANSACTION_COST_PCT))
                shares_to_buy = min(shares_to_trade, max_affordable_shares)
                gross_cost = shares_to_buy * buy_price
                transaction_cost = gross_cost * TRANSACTION_COST_PCT
                total_cost = gross_cost + transaction_cost
                
                # Debug buy logic
                if i == 0:
                    print(f"[DEBUG] Buy logic for {symbol}:")
                    print(f"  shares_to_trade: {shares_to_trade:.2f}")
                    print(f"  buy_price: ${buy_price:.2f}")
                    print(f"  max_affordable_shares: {max_affordable_shares:.2f}")
                    print(f"  shares_to_buy: {shares_to_buy:.2f}")
                    print(f"  gross_cost: ${gross_cost:.2f}")
                    print(f"  transaction_cost: ${transaction_cost:.2f}")
                    print(f"  total_cost: ${total_cost:.2f}")
                    print(f"  portfolio['cash']: ${portfolio['cash']:.2f}")
                    print(f"  shares_to_buy > 0: {shares_to_buy > 0}")
                    print(f"  portfolio['cash'] >= total_cost: {portfolio['cash'] >= total_cost}")
                    print(f"  Buy condition: {shares_to_buy > 0 and portfolio['cash'] >= total_cost}")
                
                if shares_to_buy > 0 and portfolio['cash'] >= total_cost:
                    portfolio['cash'] -= total_cost
                    holdings[symbol] = holdings.get(symbol, 0) + shares_to_buy
                    print(f"{date.strftime('%Y-%m-%d')} - BUY: {shares_to_buy:.2f} shares of {symbol} at ${buy_price:.2f} (total: ${total_cost:.2f})")
                elif i == 0:
                    print(f"[DEBUG] Buy failed for {symbol} on first day!")
            elif shares_to_trade < 0: # Sell
                shares_to_sell = abs(shares_to_trade)
                # Apply slippage to sell price
                sell_price = price * (1 - SLIPPAGE_PCT)
                gross_proceeds = shares_to_sell * sell_price
                transaction_cost = gross_proceeds * TRANSACTION_COST_PCT
                net_proceeds = gross_proceeds - transaction_cost
                
                portfolio['cash'] += net_proceeds
                holdings[symbol] -= shares_to_sell
                print(f"{date.strftime('%Y-%m-%d')} - SELL: {shares_to_sell:.2f} shares of {symbol} at ${sell_price:.2f} (net: ${net_proceeds:.2f})")

        # Debug: Print holdings and cash after the first day
        if i == 0:
            print(f"[DEBUG] Holdings after first rebalance: {holdings}")
            print(f"[DEBUG] Cash after first rebalance: {portfolio['cash']}")

    # Calculate final portfolio value at the end of the backtest
    # The last recorded value in portfolio_history will be for the second-to-last day
    # To get the true final value, perform one last calculation for the final day
    final_date = backtest_dates[-1]
    final_value = portfolio['cash']
    for symbol, shares in holdings.items():
        final_value += shares * market_data[symbol].asof(final_date)['Close']
    
    print(f"\n[DEBUG] Final portfolio calculation:")
    print(f"  Final date: {final_date.strftime('%Y-%m-%d')}")
    print(f"  Cash: ${portfolio['cash']:.2f}")
    print(f"  Holdings: {holdings}")
    for symbol, shares in holdings.items():
        final_price = market_data[symbol].asof(final_date)['Close']
        holding_value = shares * final_price
        print(f"    {symbol}: {shares:.2f} shares @ ${final_price:.2f} = ${holding_value:.2f}")
    print(f"  Final portfolio value: ${final_value:.2f}")
    print(f"  Initial backtest value: ${initial_backtest_value:.2f}")

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
    
    print("\n--- Backtest Results (with Realistic Constraints) ---")
    print(f"Trading Constraints Applied:")
    print(f"  - Transaction Costs: {TRANSACTION_COST_PCT*100:.1f}% per trade")
    print(f"  - Slippage: {SLIPPAGE_PCT*100:.3f}% per trade")
    print(f"  - Minimum Trade Size: ${MIN_TRADE_SIZE:.0f}")
    print(f"  - Rebalance Frequency: Every {REBALANCE_FREQUENCY} days")
    print()
    print(f"Initial Portfolio Value: ${initial_backtest_value:,.2f}")
    print(f"Final Portfolio Value:   ${final_value:,.2f}")
    
    total_return = (final_value / initial_backtest_value - 1) * 100
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
    
    # Print ticker selection coverage
    print(f"\n--- Ticker Selection Coverage ---")
    print(f"Total Trading Days: {total_trading_days}")
    print(f"Ticker Selection Frequency:")
    for ticker, count in sorted(ticker_selection_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_trading_days) * 100
        print(f"  {ticker}: {count} days ({percentage:.1f}%)")

    # NEW: Print daily ticker selection log (first 10 days for brevity)
    print("\n--- Daily Ticker Selection (first 10 days) ---")
    for row in daily_selection_log[:10]:
        print(row)
    if len(daily_selection_log) > 10:
        print(f"... ({len(daily_selection_log)-10} more days not shown)")

    # Optionally, save to CSV for full analysis
    try:
        import csv
        with open('daily_ticker_selection.csv', 'w', newline='') as csvfile:
            fieldnames = ['Date'] + sorted({k for d in daily_selection_log for k in d if k != 'Date'})
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in daily_selection_log:
                writer.writerow(row)
        print("\nDaily ticker selection log saved to daily_ticker_selection.csv")
    except Exception as e:
        print(f"Could not save daily ticker selection log: {e}")

    # --- TQQQ Buy-and-Hold Diagnostic ---
    print("\n--- TQQQ Buy-and-Hold Diagnostic (2024) ---")
    tqqq_df = market_data.get('TQQQ')
    if tqqq_df is not None:
        tqqq_2024 = tqqq_df[(tqqq_df.index >= pd.Timestamp('2024-01-01')) & (tqqq_df.index <= pd.Timestamp('2024-12-31'))]
        if not tqqq_2024.empty:
            first_date = tqqq_2024.index[0]
            last_date = tqqq_2024.index[-1]
            first_close = tqqq_2024.iloc[0]['Close']
            last_close = tqqq_2024.iloc[-1]['Close']
            tqqq_return = (last_close / first_close - 1) * 100
            print(f"First trading day: {first_date.strftime('%Y-%m-%d')}, Close: ${first_close:.2f}")
            print(f"Last trading day:  {last_date.strftime('%Y-%m-%d')}, Close: ${last_close:.2f}")
            print(f"TQQQ Buy-and-Hold Return (2024): {tqqq_return:.2f}%")
        else:
            print("No TQQQ data for 2024.")
    else:
        print("No TQQQ data available in market_data.")


if __name__ == '__main__':
    run_backtest()
