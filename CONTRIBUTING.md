# Contributing to Composer Parser

Thank you for your interest in contributing to Composer Parser! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker
- Include detailed steps to reproduce the bug
- Provide sample data if applicable
- Include your Python version and OS

### Suggesting Enhancements

- Use the GitHub issue tracker with the "enhancement" label
- Describe the feature and its benefits
- Include use cases and examples

### Pull Requests

- Fork the repository
- Create a feature branch
- Make your changes
- Add tests if applicable
- Update documentation
- Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Installation

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/composer-parser.git
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

4. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov black flake8 mypy
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=composer_parser --cov=backtester

# Run specific test file
pytest tests/test_parser.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Testing

### Running the Backtest

```bash
python3 backtester.py
```

Expected output:
- 100% parser accuracy
- Successful indicator calculations
- Realistic trading simulation

### Test Data

- Use the provided `symphony.json` for testing
- Create your own test strategies
- Validate against ground truth data if available

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation

3. **Test your changes:**
   ```bash
   python3 backtester.py
   pytest
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request:**
   - Use a descriptive title
   - Include a detailed description
   - Reference any related issues

### Pull Request Guidelines

- **Title:** Use a clear, descriptive title
- **Description:** Explain what the PR does and why
- **Tests:** Include tests for new functionality
- **Documentation:** Update README or add docstrings
- **Breaking Changes:** Clearly mark any breaking changes

## Code Style

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Maximum line length of 88 characters (Black default)
- Use descriptive variable and function names

### Documentation

- Add docstrings to all functions and classes
- Use Google-style docstrings
- Update README.md for new features
- Include examples in documentation

### Example Docstring

```python
def calculate_indicators(market_data: Dict[str, pd.DataFrame], indicator_params: dict) -> Dict[str, pd.DataFrame]:
    """
    Calculates technical indicators for market data.
    
    Args:
        market_data: Dictionary mapping ticker symbols to DataFrames
        indicator_params: Dictionary of indicator parameters
        
    Returns:
        Dictionary with calculated indicators added to DataFrames
        
    Example:
        >>> params = {('rsi', 10): {'SPY', 'TQQQ'}}
        >>> result = calculate_indicators(data, params)
    """
```

## Reporting Bugs

### Bug Report Template

```markdown
**Bug Description:**
Brief description of the bug

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- Python version: X.X.X
- OS: Windows/macOS/Linux
- Package versions: (run `pip freeze`)

**Additional Information:**
Any other relevant information
```

## Feature Requests

### Feature Request Template

```markdown
**Feature Description:**
Brief description of the feature

**Use Case:**
Why this feature would be useful

**Proposed Implementation:**
How you think it should work

**Alternatives Considered:**
Other approaches you've considered
```

## Getting Help

- **Issues:** Use the GitHub issue tracker
- **Discussions:** Use GitHub Discussions
- **Documentation:** Check the README and code comments

## Recognition

Contributors will be recognized in:
- The README.md file
- Release notes
- GitHub contributors page

Thank you for contributing to Composer Parser! 