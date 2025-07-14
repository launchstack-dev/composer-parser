# Composer Parser

A Python backtesting application for Composer.trade strategies that parses symphony JSON files, downloads historical market data, calculates technical indicators, and validates parser accuracy against ground truth data.

## Overview

This application allows you to:
- Load Composer.trade strategy definitions from JSON files
- Download historical market data for all required tickers
- Calculate technical indicators dynamically based on strategy requirements
- Run backtests with realistic trading simulation
- Validate parser accuracy against ground truth CSV data
- Compare parser selections with actual Composer.trade selections

## Features

### ✅ Currently Implemented

#### Core Parser Operators
- **`if`** - Conditional logic with then/else branches
- **`weight-equal`** - Distributes weights equally across all branches
- **`weight-specified`** - Assigns specific weights to assets
- **`asset`** - Individual asset selection
- **`group`** - Groups multiple assets together
- **`filter`** - Selects top/bottom N assets based on indicator ranking

#### Technical Indicators
- **RSI** (Relative Strength Index) - with configurable window
- **Moving Average** - Simple Moving Average with configurable window
- **Current Price** - Real-time price data

#### Data Management
- **Automatic ticker extraction** from symphony JSON
- **Dynamic indicator calculation** based on strategy requirements
- **Historical data download** via yfinance
- **Ground truth validation** against CSV files

#### Backtesting
- **Realistic trading simulation** with buy/sell orders
- **Portfolio tracking** with value history
- **Performance metrics** (total return, Sharpe ratio, max drawdown)
- **Accuracy validation** against ground truth data

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd composer-parser
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Backtest

1. **Prepare your symphony JSON file** (see `symphony.json` for example)
2. **Prepare ground truth CSV** (optional, for validation)
3. **Run the backtest:**
   ```bash
   python3 backtester.py
   ```

### Configuration

Edit the configuration section in `backtester.py`:

```python
# --- Configuration ---
SYMPHONY_FILE_PATH = 'symphony.json'
GROUND_TRUTH_FILE_PATH = 'composer-tickers.csv'
START_DATE = '2022-01-01'
END_DATE = '2024-01-01'
INITIAL_CAPITAL = 100000.0
```

## File Structure

```
composer-parser/
├── backtester.py          # Main backtesting application
├── composer_parser.py     # Symphony JSON parser
├── symphony.json          # Example strategy definition
├── composer-tickers.csv   # Ground truth data (optional)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Symphony JSON Format

The symphony JSON follows Composer.trade's Lisp-like syntax converted to JSON:

```json
[
  "defsymphony",
  "Strategy Name",
  [
    "if",
    [">", ["current-price", "SPY"], ["moving-average-price", "SPY", {":window": 200}]],
    [["asset", "TQQQ", "Description"]],
    [["asset", "BIL", "Description"]]
  ]
]
```

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `if` | Conditional logic | `["if", condition, then_branch, else_branch]` |
| `weight-equal` | Equal weight distribution | `["weight-equal", [branch1, branch2]]` |
| `weight-specified` | Specific weights | `["weight-specified", 0.6, asset1, 0.4, asset2]` |
| `asset` | Individual asset | `["asset", "TQQQ", "Description"]` |
| `group` | Asset grouping | `["group", "TQQQ+SPY", [sub_expression]]` |
| `filter` | Asset filtering | `["filter", ["rsi", {":window": 10}], ["select-top", 1], [assets]]` |

### Supported Indicators

| Indicator | Syntax | Description |
|-----------|--------|-------------|
| RSI | `["rsi", "TICKER", {":window": 10}]` | Relative Strength Index |
| Moving Average | `["moving-average-price", "TICKER", {":window": 200}]` | Simple Moving Average |
| Current Price | `["current-price", "TICKER"]` | Current market price |

## Current Performance

- **Parser Accuracy:** 100% against ground truth data
- **Supported Indicators:** RSI, Moving Average, Current Price
- **Supported Operators:** if, weight-equal, weight-specified, asset, group, filter
- **Data Sources:** yfinance for historical data
- **Validation:** CSV-based ground truth comparison

## Future Improvements Needed

### 🔴 High Priority

#### Additional Technical Indicators
- **MACD** (Moving Average Convergence Divergence)
  - Signal line, histogram, fast/slow periods
  - Example: `["macd", "TICKER", {":fast": 12, ":slow": 26, ":signal": 9}]`
- **Bollinger Bands**
  - Upper/lower bands, standard deviation
  - Example: `["bollinger-bands", "TICKER", {":window": 20, ":std": 2}]`
- **Stochastic Oscillator**
  - %K and %D lines
  - Example: `["stochastic", "TICKER", {":k_period": 14, ":d_period": 3}]`
- **Volume Indicators**
  - Volume-weighted average price (VWAP)
  - On-balance volume (OBV)
  - Example: `["vwap", "TICKER"]`

#### Enhanced Parser Operators
- **`weight-specified` improvements**
  - Support for dynamic weight calculations
  - Weight validation and normalization
- **`filter` enhancements**
  - Support for multiple selection criteria
  - Custom ranking functions
  - Example: `["filter", [["rsi", "TICKER"], ["macd", "TICKER"]], ["select-top", 2], [assets]]`
- **`group` improvements**
  - Dynamic group membership
  - Group-based indicators

#### Data Quality & Reliability
- **Multiple data sources**
  - Alpha Vantage API integration
  - Polygon.io integration
  - Data source fallback mechanisms
- **Data validation**
  - Missing data detection and handling
  - Outlier detection and cleaning
  - Data consistency checks

### 🟡 Medium Priority

#### Advanced Strategy Features
- **Risk Management**
  - Position sizing based on volatility
  - Stop-loss and take-profit logic
  - Maximum position limits
- **Portfolio Constraints**
  - Sector allocation limits
  - Maximum single position size
  - Rebalancing frequency controls
- **Market Regime Detection**
  - Volatility regime identification
  - Trend detection algorithms
  - Market stress indicators

#### Performance Optimization
- **Caching mechanisms**
  - Indicator calculation caching
  - Data download caching
  - Parser result caching
- **Parallel processing**
  - Multi-threaded data downloads
  - Parallel indicator calculations
- **Memory optimization**
  - Efficient data structures
  - Garbage collection optimization

#### Enhanced Validation
- **Multi-timeframe validation**
  - Daily, weekly, monthly comparisons
  - Intraday validation (if data available)
- **Statistical validation**
  - Correlation analysis
  - Performance attribution
  - Risk-adjusted metrics
- **Visual validation**
  - Chart generation with selections
  - Performance comparison plots

### 🟢 Low Priority

#### User Interface
- **Web interface**
  - Strategy builder UI
  - Real-time backtesting
  - Performance dashboard
- **Configuration management**
  - Strategy templates
  - Parameter optimization
  - A/B testing framework

#### Advanced Analytics
- **Machine learning integration**
  - Feature engineering for ML models
  - Model performance tracking
  - Automated strategy generation
- **Risk analytics**
  - Value at Risk (VaR) calculations
  - Expected shortfall
  - Stress testing scenarios

#### Integration & Deployment
- **API endpoints**
  - RESTful API for strategy evaluation
  - Webhook support for real-time updates
- **Cloud deployment**
  - Docker containerization
  - Kubernetes orchestration
  - Auto-scaling capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## Testing

Run the backtest to validate functionality:
```bash
python3 backtester.py
```

Expected output should show:
- 100% parser accuracy
- Successful indicator calculations
- Realistic trading simulation

## Dependencies

- **pandas** - Data manipulation and analysis
- **yfinance** - Yahoo Finance data download
- **pandas-ta** - Technical analysis indicators
- **numpy** - Numerical computations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Composer.trade for the strategy format
- Yahoo Finance for market data
- pandas-ta for technical indicators 