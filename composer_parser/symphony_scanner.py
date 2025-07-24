"""
Symphony Scanner Module

This module provides functionality to scan, parse, and analyze Lisp-style symphony files
for trading strategies. It handles data downloading, indicator calculation, and strategy evaluation.
"""

import pandas as pd
import yfinance as yf
import pandas_ta as ta
from typing import Dict, List, Set, Tuple, Union
from .lisp_parser import parse_symphony_file
from .composer_parser import ComposerStrategy


class SymphonyScanner:
    """
    A comprehensive scanner for Lisp-style symphony trading strategy files.
    
    This class provides functionality to:
    - Parse Lisp-style symphony files
    - Extract tickers and indicators
    - Download historical market data
    - Calculate technical indicators
    - Evaluate trading strategies
    """
    
    def __init__(self, symphony_file_path: str = 'symphony.json'):
        """
        Initialize the SymphonyScanner.
        
        Args:
            symphony_file_path (str): Path to the symphony file
        """
        self.symphony_file_path = symphony_file_path
        self.all_tickers: Set[str] = set()
        self.all_indicators: Dict = {}
        self.market_data: Dict[str, pd.DataFrame] = {}
    
    def scan_symphony(self) -> Tuple[Set[str], Dict]:
        """
        Scan the symphony file to extract tickers and indicators.
        
        Returns:
            Tuple[Set[str], Dict]: (tickers, indicators)
        """
        print("🔍 Scanning symphony.json...")
        
        try:
            symphony = parse_symphony_file(self.symphony_file_path)
            print("✅ Symphony parsed successfully")
            
            # Extract tickers and indicators
            self.all_tickers = self._extract_all_tickers(symphony)
            self.all_indicators = self._extract_all_indicators(symphony)
            
            print(f"📊 Found {len(self.all_tickers)} tickers: {sorted(self.all_tickers)}")
            print(f"📈 Found {len(self.all_indicators)} indicator types:")
            for key, params in self.all_indicators.items():
                print(f"   - {key}: {params}")
            
            return self.all_tickers, self.all_indicators
            
        except Exception as e:
            print(f"❌ Error scanning symphony: {e}")
            raise
    
    def _extract_all_tickers(self, symphony: List) -> Set[str]:
        """Extract all ticker symbols from the symphony."""
        tickers = set()
        
        def extract_from_expression(expr):
            if isinstance(expr, list):
                if len(expr) > 0 and expr[0] in ['current-price', 'moving-average-price', 'rsi']:
                    if len(expr) > 1 and isinstance(expr[1], str):
                        tickers.add(expr[1])
                elif len(expr) > 0 and expr[0] == 'asset':
                    if len(expr) > 1 and isinstance(expr[1], str):
                        tickers.add(expr[1])
                elif len(expr) > 0 and expr[0] == 'group':
                    if len(expr) > 1 and isinstance(expr[1], str):
                        # Parse group string like "UVXY+VIXM+BIL+BTAL"
                        group_tickers = expr[1].split('+')
                        tickers.update(group_tickers)
                
                # Recursively process all elements
                for item in expr:
                    extract_from_expression(item)
        
        extract_from_expression(symphony)
        return tickers
    
    def _extract_all_indicators(self, symphony: List) -> Dict:
        """Extract all indicator types and their parameters from the symphony."""
        indicators = {}
        
        def extract_from_expression(expr):
            if isinstance(expr, list):
                if len(expr) > 0 and expr[0] == 'rsi':
                    if len(expr) > 2:
                        params = expr[2]
                        window = 10  # default
                        if isinstance(params, dict) and ':window' in params:
                            window = int(params[':window'])
                        elif isinstance(params, list):
                            for i in range(len(params) - 1):
                                if params[i] == ':window':
                                    window = int(params[i + 1])
                                    break
                        indicators[('rsi', window)] = {'type': 'rsi', 'window': window}
                
                elif len(expr) > 0 and expr[0] == 'moving-average-price':
                    if len(expr) > 2:
                        params = expr[2]
                        window = 20  # default
                        if isinstance(params, dict) and ':window' in params:
                            window = int(params[':window'])
                        elif isinstance(params, list):
                            for i in range(len(params) - 1):
                                if params[i] == ':window':
                                    window = int(params[i + 1])
                                    break
                        indicators[('ma', window)] = {'type': 'ma', 'window': window}
                
                # Recursively process all elements
                for item in expr:
                    extract_from_expression(item)
        
        extract_from_expression(symphony)
        return indicators
    
    def download_market_data(self, start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        Download maximum available historical market data for all tickers.
        
        Args:
            start_date (str, optional): Start date for data download. If None, downloads from earliest available.
            end_date (str, optional): End date for data download. If None, downloads to latest available.
            
        Returns:
            Dict[str, pd.DataFrame]: Market data for each ticker
        """
        if not self.all_tickers:
            print("⚠️  No tickers found to download")
            return {}
        
        # Set default dates to get maximum available data
        if start_date is None:
            start_date = '1990-01-01'  # Very early date to get all available data
        if end_date is None:
            end_date = '2024-12-31'    # Current date
        
        print(f"📥 Downloading maximum available market data for {len(self.all_tickers)} tickers...")
        print(f"   Download period: {start_date} to {end_date}")
        
        # Download maximum available data using yfinance
        tickers_list = list(self.all_tickers)
        data = yf.download(tickers_list, start=start_date, end=end_date, group_by='ticker')
        
        # Convert to the expected format
        market_data = {}
        for ticker in self.all_tickers:
            if len(self.all_tickers) == 1:
                ticker_data = data
            else:
                if ticker in data.columns.get_level_values(0):
                    ticker_data = data[ticker]
                else:
                    print(f"⚠️  Warning: No data found for {ticker}")
                    ticker_data = pd.DataFrame()
            
            # Keep all data for indicator calculation, but mark the analysis period
            market_data[ticker] = ticker_data
        
        self.market_data = market_data
        print(f"✅ Downloaded data for {len(market_data)} tickers")
        
        # Print data summary
        for ticker, df in market_data.items():
            if not df.empty:
                print(f"   {ticker}: {df.shape[0]} days, {df.shape[1]} columns")
            else:
                print(f"   {ticker}: No data")
                
        return market_data
    
    def determine_max_analysis_length(self) -> Tuple[str, str]:
        """
        Determine the maximum possible analysis period based on available data and indicator requirements.
        
        Returns:
            Tuple[str, str]: (start_date, end_date) for maximum analysis period
        """
        if not self.market_data:
            print("⚠️  No market data available. Run download_market_data first.")
            return None, None
        
        # Find the earliest and latest dates across all tickers
        earliest_dates = []
        latest_dates = []
        
        for ticker, df in self.market_data.items():
            if not df.empty:
                earliest_dates.append(df.index.min())
                latest_dates.append(df.index.max())
        
        if not earliest_dates or not latest_dates:
            print("⚠️  No valid data found in market_data")
            return None, None
        
        # Get the latest earliest date and earliest latest date (intersection)
        global_earliest = max(earliest_dates)  # Latest of earliest dates
        global_latest = min(latest_dates)      # Earliest of latest dates
        
        # Calculate required warmup based on indicators
        max_window = 0
        for indicator_key, params in self.all_indicators.items():
            if params['type'] == 'rsi':
                max_window = max(max_window, params['window'])
            elif params['type'] == 'ma':
                max_window = max(max_window, params['window'])
        
        # Add buffer for warmup (extra days beyond the max window)
        warmup_buffer = 100  # Extra days for safety
        required_warmup = max_window + warmup_buffer
        
        # Calculate the actual start date for analysis
        analysis_start = global_earliest + pd.Timedelta(days=required_warmup)
        analysis_end = global_latest
        
        # Ensure we have enough data
        if analysis_start >= analysis_end:
            print(f"⚠️  Insufficient data for analysis. Need at least {required_warmup} days of warmup.")
            return None, None
        
        start_date_str = analysis_start.strftime('%Y-%m-%d')
        end_date_str = analysis_end.strftime('%Y-%m-%d')
        
        print(f"📊 Maximum analysis period determined:")
        print(f"   Data available: {global_earliest.strftime('%Y-%m-%d')} to {global_latest.strftime('%Y-%m-%d')}")
        print(f"   Max indicator window: {max_window} days")
        print(f"   Required warmup: {required_warmup} days")
        print(f"   Analysis period: {start_date_str} to {end_date_str}")
        print(f"   Total analysis days: {(analysis_end - analysis_start).days} days")
        
        return start_date_str, end_date_str
    
    def calculate_all_indicators(self) -> Dict[str, pd.DataFrame]:
        """
        Calculate all technical indicators for ALL tickers.
        
        Returns:
            Dict[str, pd.DataFrame]: Market data with indicators added
        """
        print("🧮 Calculating technical indicators for ALL tickers...")
        
        # Get all unique indicator parameters
        all_rsi_windows = set()
        all_ma_windows = set()
        
        for indicator_key, params in self.all_indicators.items():
            if params['type'] == 'rsi':
                all_rsi_windows.add(params['window'])
            elif params['type'] == 'ma':
                all_ma_windows.add(params['window'])
        
        print(f"   RSI windows: {sorted(all_rsi_windows)}")
        print(f"   MA windows: {sorted(all_ma_windows)}")
        
        # Calculate indicators for each ticker
        for ticker, df in self.market_data.items():
            if df.empty:
                continue
                
            print(f"   Calculating indicators for {ticker}...")
            
            # Calculate RSI for all windows
            for window in all_rsi_windows:
                rsi_col = f'RSI_{window}'
                df[rsi_col] = ta.rsi(df['Close'], length=window)
            
            # Calculate moving averages for all windows
            for window in all_ma_windows:
                ma_col = f'MA_{window}'
                df[ma_col] = ta.sma(df['Close'], length=window)
            
            # Add current price column
            df['current_price'] = df['Close']
            
            # Forward fill NaN values
            df = df.ffill()
            
            self.market_data[ticker] = df
            
        print("✅ All indicators calculated")
        return self.market_data
    
    def create_strategy_evaluator(self) -> ComposerStrategy:
        """
        Create a strategy evaluator from the parsed symphony.
        
        Returns:
            ComposerStrategy: Strategy evaluator
        """
        print("🎯 Creating strategy evaluator...")
        
        # Parse the symphony file
        symphony = parse_symphony_file(self.symphony_file_path)
        
        # Find the main strategy logic (weight-equal expression)
        strategy_logic = None
        for i, item in enumerate(symphony):
            if isinstance(item, list) and len(item) > 0 and item[0] == 'weight-equal':
                strategy_logic = item
                break
        
        if strategy_logic is None:
            raise ValueError("No weight-equal expression found in symphony")
        
        # Create the symphony_json structure expected by ComposerStrategy
        symphony_json = [
            "TQQQ FTLT Strategy",  # name
            "Strategy description",  # description
            strategy_logic  # strategy logic
        ]
        
        print("DEBUG: Symphony structure type:", type(symphony_json))
        print("DEBUG: Symphony length:", len(symphony_json))
        print("DEBUG: First element:", symphony_json[0])
        print("DEBUG: Second element:", symphony_json[1])
        print("DEBUG: Third element type:", type(symphony_json[2]))
        print("DEBUG: Found strategy logic at index 10:", symphony_json[2][0])
        print("DEBUG: Fixed symphony structure:", [type(item) for item in symphony_json])
        
        # Create the strategy evaluator
        strategy = ComposerStrategy(symphony_json, self.market_data)
        print("✅ Strategy evaluator created")
        
        return strategy
    
    def get_daily_selections(self, strategy: ComposerStrategy, start_date: str, end_date: str) -> List[Dict]:
        """
        Get ticker selections for each day in the date range.
        
        Args:
            strategy (ComposerStrategy): Strategy evaluator
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            List[Dict]: Daily ticker selections
        """
        print(f"📅 Getting daily ticker selections from {start_date} to {end_date}...")
        
        # Get common dates across all tickers
        common_dates = None
        for ticker, df in self.market_data.items():
            if not df.empty:
                if common_dates is None:
                    common_dates = df.index
                else:
                    common_dates = common_dates.intersection(df.index)
        
        if common_dates is None or len(common_dates) == 0:
            print("⚠️  No common dates found across tickers")
            return []
        
        # Filter to the requested date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        date_range = common_dates[(common_dates >= start_dt) & (common_dates <= end_dt)]
        
        print(f"   Evaluating {len(date_range)} trading days...")
        
        daily_selections = []
        for i, date in enumerate(date_range):
            try:
                target_portfolio = strategy.get_target_portfolio(date)
                selected_tickers = {ticker: weight for ticker, weight in target_portfolio.items() if weight > 0}
                
                daily_selections.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'selected_tickers': selected_tickers,
                    'total_weight': sum(selected_tickers.values())
                })
                
                if i < 5:  # Show first 5 days for debugging
                    print(f"   {date.strftime('%Y-%m-%d')}: {selected_tickers}")
                    
            except Exception as e:
                print(f"   ⚠️  Error on {date.strftime('%Y-%m-%d')}: {e}")
                daily_selections.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'selected_tickers': {},
                    'total_weight': 0,
                    'error': str(e)
                })
        
        print(f"✅ Generated {len(daily_selections)} daily selections")
        return daily_selections
    
    def run_complete_analysis(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Run the complete symphony analysis pipeline with maximum available data.
        
        Args:
            start_date (str, optional): Start date for analysis. If None, uses maximum available period.
            end_date (str, optional): End date for analysis. If None, uses maximum available period.
            
        Returns:
            Dict: Complete analysis results
        """
        print("🚀 Starting complete symphony analysis with maximum data...")
        
        # Step 1: Scan symphony
        tickers, indicators = self.scan_symphony()
        
        # Step 2: Download maximum available market data
        self.download_market_data()
        
        # Step 3: Calculate indicators
        self.calculate_all_indicators()
        
        # Step 4: Determine maximum analysis period
        if start_date is None or end_date is None:
            start_date, end_date = self.determine_max_analysis_length()
            if start_date is None or end_date is None:
                print("❌ Failed to determine analysis period")
                return {}
        
        # Step 5: Create strategy evaluator
        strategy = self.create_strategy_evaluator()
        
        # Step 6: Get daily selections
        daily_selections = self.get_daily_selections(strategy, start_date, end_date)
        
        # Compile results
        results = {
            'symphony_file': self.symphony_file_path,
            'analysis_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'tickers_found': sorted(list(tickers)),
            'indicators_found': indicators,
            'market_data_summary': {
                ticker: {
                    'shape': df.shape,
                    'date_range': f"{df.index.min()} to {df.index.max()}" if not df.empty else "No data"
                } for ticker, df in self.market_data.items()
            },
            'daily_selections': daily_selections,
            'total_days_analyzed': len(daily_selections)
        }
        
        print("✅ Complete analysis finished!")
        return results 