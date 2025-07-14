# Composer Parser

**⚠️ WORK IN PROGRESS - EXPECT BUGS ⚠️**

A Python backtesting application for Composer.trade strategies that parses symphony JSON files, downloads historical market data, calculates technical indicators, and validates parser accuracy against ground truth data.

## ⚠️ Important Disclaimers

- **This is a work in progress** - Expect bugs, incomplete features, and breaking changes
- **Limited indicator support** - Only RSI, Moving Average, and Current Price are currently implemented
- **Experimental code** - Not suitable for production trading
- **No warranty** - Use at your own risk
- **Educational purposes** - Primarily for learning and research
- **Tested strategy only** - Currently validated against one specific symphony (see [symphony.json](symphony.json))
- **Original source** - Strategy sourced from [Composer.trade](https://app.composer.trade/symphony/tZA9DlWahdsFdA4ROkq6/details)

## 🚨 Legal Disclaimers & Liability

### No Warranty
**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.**

### No Liability
**IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

### User Responsibility
- **You are solely responsible** for any decisions made using this software
- **No financial advice** - This software does not provide investment advice
- **Test thoroughly** - Always test with small amounts before any real trading
- **Understand the risks** - Trading involves substantial risk of loss
- **Use at your own risk** - The authors accept no responsibility for financial losses
- **Code is experimental** - May contain bugs that could cause incorrect results
- **No guarantee of accuracy** - Results may be wrong or misleading
- **Not for production use** - This is research/educational software only

### Financial Disclaimer
**This software is for educational and research purposes only. It is not intended to provide financial advice or recommendations. Any trading decisions made using this software are made at your own risk. Past performance does not guarantee future results. You should consult with qualified financial professionals before making any investment decisions.**

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

#### Technical Indicators (Limited Support)
- **RSI** (Relative Strength Index) - with configurable window
- **Moving Average** - Simple Moving Average with configurable window
- **Current Price** - Real-time price data

**⚠️ Note:** Only these three indicators are currently implemented. Additional indicators (MACD, Bollinger Bands, Stochastic, etc.) are planned but not yet available.

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

**⚠️ By installing and using this software, you acknowledge that you understand the risks and accept full responsibility for any consequences.**

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

**⚠️ WARNING: Use this software at your own risk. The authors accept no liability for any financial losses or damages resulting from the use of this code.**

### Basic Backtest

1. **Prepare your symphony JSON file** (see `symphony.json` for example)
2. **Prepare ground truth CSV** (optional, for validation)
3. **Run the backtest:**
   ```bash
   python3 backtester.py
   ```

**⚠️ Important:** Always test with small amounts and understand that this experimental software may produce incorrect results. Never rely solely on this software for trading decisions.

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

## Current Performance (Experimental)

- **Parser Accuracy:** 100% against the tested symphony strategy
- **Supported Indicators:** RSI, Moving Average, Current Price (limited set)
- **Supported Operators:** if, weight-equal, weight-specified, asset, group, filter
- **Data Sources:** yfinance for historical data
- **Validation:** CSV-based ground truth comparison
- **Tested Strategy:** [symphony.json](symphony.json) - "TQQQ For The Long Term | reddit version" (sourced from [Composer.trade](https://app.composer.trade/symphony/tZA9DlWahdsFdA4ROkq6/details))

**⚠️ Important:** The 100% accuracy is achieved only for the specific symphony strategy provided. Other strategies may not work correctly due to limited indicator support and potential bugs.

## Known Limitations & Bugs

### 🐛 Current Issues
- **Limited indicator support** - Only 3 indicators implemented (RSI, MA, Current Price)
- **Single strategy tested** - Only validated against [symphony.json](symphony.json)
- **No error handling** - Many edge cases not handled gracefully
- **Memory usage** - Large datasets may cause memory issues
- **Data quality** - No validation of downloaded market data
- **Performance** - Not optimized for large-scale backtesting

### ⚠️ What Doesn't Work
- Strategies using unsupported indicators (MACD, Bollinger Bands, etc.)
- Complex nested filter operations
- Dynamic weight calculations
- Real-time data feeds
- Multi-timeframe analysis
- Risk management features

## Future Improvements Needed

### 🔴 High Priority

#### Additional Technical Indicators (CRITICAL)
**⚠️ This is the most important limitation - only 3 indicators are currently supported!**

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
- **Additional Price Indicators**
  - Exponential Moving Average (EMA)
  - Weighted Moving Average (WMA)
  - Price channels and envelopes

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

## Contributing

**⚠️ This is an experimental project - contributions are welcome but please understand this is a work in progress!**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to submit pull requests, report bugs, and suggest features.

### 🎯 Priority Areas for Contributors
1. **Expand indicator support** - This is the most critical need
2. **Add error handling** - Make the parser more robust
3. **Test with different strategies** - Validate against more symphony files
4. **Performance optimization** - Improve memory usage and speed
5. **Documentation** - Help improve docs and examples

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/composer-parser.git
   cd composer-parser
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```

3. **Run tests:**
   ```bash
   make test
   ```

4. **Check code quality:**
   ```bash
   make check
   ```

### Code Quality

This project uses several tools to maintain code quality:

- **Black** - Code formatting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pytest** - Testing
- **Pre-commit** - Git hooks

Run `make help` to see all available commands.

## Security

Please report security vulnerabilities to [INSERT SECURITY EMAIL]. See our [Security Policy](SECURITY.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Composer.trade** - For the innovative strategy platform and the [original symphony strategy](https://app.composer.trade/symphony/tZA9DlWahdsFdA4ROkq6/details)
- **yfinance** - For reliable market data
- **pandas-ta** - For technical indicators
- **The open source community** - For inspiration and tools

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

---

## 🚨 Final Disclaimer

**By using this software, you acknowledge and agree that:**

1. **This is experimental research software** - not production-ready
2. **You use it entirely at your own risk** - no liability accepted
3. **You are responsible for all consequences** - financial or otherwise
4. **No guarantees of accuracy** - results may be wrong
5. **Not financial advice** - consult professionals for investment decisions
6. **Test thoroughly** - never rely on untested software for real trading
7. **Understand the code** - don't use what you don't understand
8. **Use responsibly** - this is for education and research only

**The authors and contributors to this project accept no responsibility for any losses, damages, or consequences resulting from the use of this software. You are solely responsible for your own actions and decisions.** 