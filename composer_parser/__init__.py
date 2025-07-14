"""
Composer Parser - A Python library for parsing and backtesting Composer.trade strategies.

This library provides tools to:
- Parse Composer.trade symphony JSON strategies
- Download and process market data
- Calculate technical indicators
- Run backtests with realistic trading simulation
- Validate parser accuracy against ground truth data
"""

__version__ = "1.0.0"
__author__ = "Jensen Carlsen"
__email__ = "jensen@example.com"
__description__ = "A Python library for parsing and backtesting Composer.trade strategies"

from .composer_parser import ComposerStrategy

__all__ = ["ComposerStrategy"] 