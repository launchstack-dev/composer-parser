"""
Composer Parser Package

A comprehensive package for parsing and analyzing Lisp-style symphony trading strategy files.
Provides functionality for data downloading, indicator calculation, and strategy evaluation.

Main Components:
- SymphonyScanner: Main class for scanning and analyzing symphony files
- ComposerStrategy: Strategy evaluator for making ticker selections
- LispParser: Parser for Lisp-style syntax in symphony files
"""

from .symphony_scanner import SymphonyScanner
from .composer_parser import ComposerStrategy
from .lisp_parser import parse_symphony_file
from .api import ComposerAPI, quick_analysis, get_daily_selections, validate_accuracy
from .version import __version__

__all__ = [
    'SymphonyScanner',
    'ComposerStrategy', 
    'parse_symphony_file',
    'ComposerAPI',
    'quick_analysis',
    'get_daily_selections', 
    'validate_accuracy',
    '__version__'
]

# Convenience function for quick analysis
def analyze_symphony(symphony_file_path: str = 'symphony.json', 
                    start_date: str = None, 
                    end_date: str = None,
                    market_data: dict = None) -> dict:
    """
    Quick function to analyze a symphony file and return results.
    
    Args:
        symphony_file_path (str): Path to the symphony file
        start_date (str, optional): Start date for analysis
        end_date (str, optional): End date for analysis
        market_data (dict, optional): Preloaded market data to use instead of downloading.
    Returns:
        dict: Analysis results
    """
    from .api import ComposerAPI
    api = ComposerAPI(symphony_file_path)
    api.load_strategy(start_date, end_date, market_data=market_data)
    return api.scanner.run_complete_analysis(start_date, end_date) 