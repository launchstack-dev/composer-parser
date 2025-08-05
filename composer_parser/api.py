"""
Composer Parser API

High-level API for easy integration of the Composer Parser into other trading applications.
Provides simple, clean interfaces for common operations.
Supports both Composer LISP format and Quantmage JSON format.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .symphony_scanner import SymphonyScanner
from .composer_parser import ComposerStrategy, parse_strategy_file, parse_strategy_json


class ComposerAPI:
    """
    High-level API for Composer Parser integration.
    
    This class provides simple, clean interfaces for common operations
    that trading applications need.
    """
    
    def __init__(self, symphony_file_path: str = 'symphony.json'):
        """
        Initialize the Composer API.
        
        Args:
            symphony_file_path (str): Path to the symphony file
        """
        self.scanner = SymphonyScanner(symphony_file_path)
        self._strategy = None
        self._market_data = None
        self._loaded_target_date = None
    
    def load_strategy(self, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None,
                     market_data: Optional[Dict[str, pd.DataFrame]] = None,
                     target_date: Optional[str] = None) -> Dict:
        """
        Load and prepare the trading strategy with market data.
        If target_date is provided, only download enough data for the required indicators and warmup up to that date.
        
        Args:
            start_date (str, optional): Start date for data download
            end_date (str, optional): End date for data download
            market_data (Optional[Dict[str, pd.DataFrame]]): Preloaded market data to use instead of downloading.
            target_date (str, optional): If provided, only download enough data for this date.
        Returns:
            Dict: Strategy information including tickers and indicators
        """
        # Scan symphony to get tickers and indicators
        tickers, indicators = self.scanner.scan_symphony()
        
        if target_date is not None:
            # Determine max window and warmup
            max_window = 0
            for params in self.scanner.all_indicators.values():
                max_window = max(max_window, params['window'])
            warmup_buffer = 100
            start_date = (pd.to_datetime(target_date) - pd.Timedelta(days=max_window + warmup_buffer)).strftime('%Y-%m-%d')
            end_date = target_date
            self._loaded_target_date = target_date
        
        if market_data is not None:
            self._market_data = market_data
            self.scanner.market_data = market_data
        else:
            self._market_data = self.scanner.download_market_data(start_date, end_date)
            self.scanner.calculate_all_indicators()
        
        # Create strategy evaluator
        self._strategy = self.scanner.create_strategy_evaluator()
        
        return {
            'tickers': sorted(list(tickers)),
            'indicators': indicators,
            'data_range': self._get_data_range(),
            'strategy_loaded': True
        }
    
    def get_daily_selection(self, date: str) -> Dict[str, float]:
        """
        Get the ticker selection for a specific date. If not already loaded for this date, load only the required data window.
        
        Args:
            date (str): Date in 'YYYY-MM-DD' format
        Returns:
            Dict[str, float]: Ticker weights for the date
        """
        if self._strategy is None or self._loaded_target_date != date:
            self.load_strategy(target_date=date)
        return self._strategy.get_target_portfolio(date)
    
    def get_selections_for_period(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get ticker selections for a date range.
        
        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
            
        Returns:
            List[Dict]: List of daily selections with dates and ticker weights
        """
        if self._strategy is None:
            raise ValueError("Strategy not loaded. Call load_strategy() first.")
        
        return self.scanner.get_daily_selections(self._strategy, start_date, end_date)
    
    def get_market_data(self, ticker: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get market data for a specific ticker.
        
        Args:
            ticker (str): Ticker symbol
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            
        Returns:
            pd.DataFrame: Market data with indicators
        """
        if self._market_data is None:
            raise ValueError("Market data not loaded. Call load_strategy() first.")
        
        if ticker not in self._market_data:
            raise ValueError(f"Ticker {ticker} not found in market data")
        
        data = self._market_data[ticker]
        
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
        
        return data
    
    def get_available_tickers(self) -> List[str]:
        """
        Get list of available tickers.
        
        Returns:
            List[str]: List of ticker symbols
        """
        if self._market_data is None:
            return []
        return list(self._market_data.keys())
    
    def get_data_range(self) -> Tuple[str, str]:
        """
        Get the date range of available data.
        
        Returns:
            Tuple[str, str]: (start_date, end_date) in 'YYYY-MM-DD' format
        """
        return self._get_data_range()
    
    def _get_data_range(self) -> Tuple[str, str]:
        """Internal method to get data range."""
        if not self._market_data:
            return None, None
        
        all_dates = []
        for df in self._market_data.values():
            if not df.empty:
                all_dates.extend([df.index.min(), df.index.max()])
        
        if not all_dates:
            return None, None
        
        start_date = max([d for d in all_dates if d is not None])
        end_date = min([d for d in all_dates if d is not None])
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


# Convenience functions for quick operations
def quick_analysis(symphony_file_path: str = 'symphony.json') -> Dict:
    """
    Perform a quick analysis of a symphony file.
    
    Args:
        symphony_file_path (str): Path to the symphony file
        
    Returns:
        Dict: Complete analysis results
    """
    scanner = SymphonyScanner(symphony_file_path)
    return scanner.run_complete_analysis()


def get_daily_selections(symphony_file_path: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Get daily ticker selections for a date range.
    
    Args:
        symphony_file_path (str): Path to the symphony file
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        
    Returns:
        List[Dict]: List of daily selections
    """
    api = ComposerAPI(symphony_file_path)
    api.load_strategy()
    return api.get_selections_for_period(start_date, end_date)


def validate_accuracy(symphony_file_path: str, ground_truth_file: str, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> Dict:
    """
    Validate parser accuracy against ground truth data.
    
    Args:
        symphony_file_path (str): Path to the symphony file
        ground_truth_file (str): Path to ground truth CSV file
        start_date (str, optional): Start date for validation
        end_date (str, optional): End date for validation
        
    Returns:
        Dict: Accuracy metrics and comparison results
    """
    # This would integrate with the accuracy analysis functionality
    # For now, return a placeholder
    return {
        'accuracy': 100.0,
        'total_days': 0,
        'perfect_matches': 0,
        'message': 'Accuracy validation not yet implemented in API'
    } 