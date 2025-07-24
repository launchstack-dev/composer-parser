# composer_parser.py
"""
This module provides the ComposerStrategy class, which is responsible for
parsing and evaluating trading strategies defined in a Composer.trade-style
JSON format. It translates the LISP-like DSL into an executable trading logic.
"""
import pandas as pd
from typing import Dict, List, Any, Union
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class ComposerStrategy:
    """
    Parses and evaluates a Composer.trade symphony JSON.
    
    This class takes a symphony definition (as a dictionary) and the necessary
    market data. It then recursively evaluates the nested expressions to
    determine the target portfolio allocation for a given date.
    """

    def __init__(self, symphony_json: List, market_data: Dict[str, pd.DataFrame]):
        """
        Initializes the ComposerStrategy evaluator.

        Args:
            symphony_json (List): The complete Composer symphony, loaded from JSON.
            market_data (Dict[str, pd.DataFrame]): A dictionary where keys are ticker
                symbols and values are pandas DataFrames containing OHLCV data and
                pre-calculated technical indicators (e.g., 'RSI', 'MA200').
        """
        if not isinstance(symphony_json, list) or len(symphony_json) < 3:
            raise ValueError("Invalid symphony JSON structure.")
        self.symphony = symphony_json
        self.market_data = market_data
        self.evaluation_date = None

    def _get_data_for_date(self, symbol: str, date: pd.Timestamp) -> pd.Series:
        """
        Safely retrieves the row of data for a specific symbol and date.
        Uses direct indexing to get data for the exact date.
        """
        if symbol not in self.market_data or self.market_data[symbol].empty:
            raise ValueError(f"Market data not available for symbol: {symbol}")
        
        # Try to get data for the exact date first
        if date in self.market_data[symbol].index:
            data_for_date = self.market_data[symbol].loc[date]
            return data_for_date
        
        # If exact date not found, use asof to get the most recent data on or before the date
        data_for_date = self.market_data[symbol].asof(date)
        
        # Check if we got any valid data (ignore NaN indicators)
        if pd.isna(data_for_date).all():
            raise ValueError(f"No data available for {symbol} on or before {date.strftime('%Y-%m-%d')}")
            
        return data_for_date

    def _get_indicator_value(self, symbol: str, indicator_type: str, indicator_params: dict) -> float:
        """
        Gets the indicator value for a specific symbol and indicator type.

        Args:
            symbol (str): The ticker symbol.
            indicator_type (str): The type of indicator (e.g., 'rsi', 'moving-average-price').
            indicator_params (dict): Parameters for the indicator (e.g., window size).
        Returns:
            float: The indicator value, or None if not available.
        """
        try:
            data = self._get_data_for_date(symbol, self.evaluation_date)
            
            if indicator_type == 'rsi':
                window = int(indicator_params.get(':window', 10))  # default to 10
                rsi_col = f'RSI_{window}'
                if rsi_col in data:
                    return data[rsi_col]
                else:
                    return None
            elif indicator_type == 'moving-average-price':
                window = int(indicator_params.get(':window', 20))  # default to 20
                ma_col = f'MA_{window}'
                if ma_col in data:
                    return data[ma_col]
                else:
                    return None
            elif indicator_type == 'current-price':
                if 'current_price' in data:
                    return data['current_price']
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def _resolve_value(self, value_expression: Union[List, str, int, float]) -> float:
        """
        Resolves an expression to a numeric value (e.g., gets RSI or a price).

        Args:
            value_expression (Union[List, str, int, float]): The value expression to resolve.
        Returns:
            float: The resolved numeric value.
        """
        if not isinstance(value_expression, list):
            return float(value_expression)

        operator = value_expression[0]
        
        try:
            if operator == 'current-price':
                symbol = value_expression[1]
                return self._get_data_for_date(symbol, self.evaluation_date)['Close']
            
            elif operator == 'moving-average-price':
                symbol = value_expression[1]
                params = value_expression[2]
                if isinstance(params, dict):
                    window = int(params.get(':window', 20))  # default to 20
                elif isinstance(params, list):
                    window = 20  # default
                    for i in range(len(params) - 1):
                        if params[i] == ':window':
                            window = int(params[i + 1])
                            break
                else:
                    window = 20  # default
                ma_column = f'MA_{window}'
                if ma_column not in self.market_data[symbol].columns:
                     raise ValueError(f"Indicator '{ma_column}' not found for {symbol}. Please calculate it first.")
                return self._get_data_for_date(symbol, self.evaluation_date)[ma_column]

            elif operator == 'rsi':
                symbol = value_expression[1]
                params = value_expression[2]
                if isinstance(params, dict):
                    window = int(params.get(':window', 10))  # default to 10
                elif isinstance(params, list):
                    window = 10  # default
                    for i in range(len(params) - 1):
                        if params[i] == ':window':
                            window = int(params[i + 1])
                            break
                else:
                    window = 10  # default
                rsi_column = f'RSI_{window}'
                if rsi_column not in self.market_data[symbol].columns:
                    raise ValueError(f"Indicator '{rsi_column}' not found for {symbol}. Please calculate it first.")
                return self._get_data_for_date(symbol, self.evaluation_date)[rsi_column]
            
            else:
                raise ValueError(f"Unknown value operator: {operator}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Malformed value expression '{value_expression}': {e}")


    def _evaluate_condition(self, condition: List) -> bool:
        """Evaluates a conditional expression like (> (current-price "SPY") ...)."""
        if not isinstance(condition, list) or len(condition) != 3:
            raise ValueError(f"Malformed condition expression: {condition}")

        operator, operand1_expr, operand2_expr = condition
        
        operand1 = self._resolve_value(operand1_expr)
        operand2 = self._resolve_value(operand2_expr)

        if operator == '>':
            return operand1 > operand2
        elif operator == '<':
            return operand1 < operand2
        elif operator == '>=':
            return operand1 >= operand2
        elif operator == '<=':
            return operand1 <= operand2
        elif operator == '=':
            return operand1 == operand2
        else:
            raise ValueError(f"Unknown comparison operator: {operator}")

    def _evaluate_expression(self, expression: List) -> Dict[str, float]:
        """
        Recursively evaluates a Composer expression and returns a portfolio dictionary.
        This is the core of the recursive descent parser.
        """
        if not expression:
            return {}
            
        operator = expression[0]
        
        if operator == 'if':
            # Structure: (if condition then_branch else_branch)
            _, condition, then_branch, else_branch = expression
            if self._evaluate_condition(condition):
                return self._evaluate_expression(then_branch)
            else:
                return self._evaluate_expression(else_branch)

        elif operator == 'weight-equal':
            # Structure: (weight-equal [branch1] [branch2] ...)
            # Each branch should be evaluated independently
            branches = expression[1:]
            if not branches:
                return {}
            
            # Evaluate each branch and collect results
            all_results = []
            for branch in branches:
                branch_result = self._evaluate_expression(branch)
                if branch_result:  # Only add non-empty results
                    all_results.append(branch_result)
            
            # If no valid results, return empty
            if not all_results:
                return {}
            
            # Combine all results and distribute weights equally
            combined_assets = {}
            for result in all_results:
                for asset, weight in result.items():
                    if asset in combined_assets:
                        combined_assets[asset] += weight
                    else:
                        combined_assets[asset] = weight
            
            # Normalize weights to sum to 1.0
            total_weight = sum(combined_assets.values())
            if total_weight > 0:
                return {asset: weight / total_weight for asset, weight in combined_assets.items()}
            
            return {}

        elif operator == 'weight-specified':
            # Structure: (weight-specified weight1 asset1 weight2 asset2 ...)
            portfolio = {}
            total_weight = 0
            
            for i in range(1, len(expression), 2):
                if i + 1 < len(expression):
                    weight = float(expression[i])
                    asset_expr = expression[i + 1]
                    asset_portfolio = self._evaluate_expression(asset_expr)
                    
                    for asset, _ in asset_portfolio.items():
                        portfolio[asset] = weight
                        total_weight += weight
            
            # Normalize weights
            if total_weight > 0:
                return {asset: weight / total_weight for asset, weight in portfolio.items()}
            
            return portfolio

        elif operator == 'asset':
            # Base case: returns the asset itself with weight 1.0
            return {expression[1]: 1.0}
        
        elif operator == 'group':
            # A group contains a sub-expression that defines the assets within it
            return self._evaluate_expression(expression[2])

        elif operator == 'filter':
            # Structure: (filter indicator_criteria selection_method asset_list)
            indicator_criteria = expression[1]
            selection_method = expression[2]
            asset_list = expression[3]
            
            if not asset_list:
                return {}
            
            # Extract indicator parameters
            if isinstance(indicator_criteria, list) and len(indicator_criteria) >= 2:
                indicator_type = indicator_criteria[0]
                indicator_params = indicator_criteria[2] if len(indicator_criteria) > 2 else {}
            else:
                return {}
            
            # Evaluate indicator for each asset
            asset_scores = []
            for asset_expr in asset_list:
                asset_portfolio = self._evaluate_expression(asset_expr)
                for asset, _ in asset_portfolio.items():
                    indicator_value = self._get_indicator_value(asset, indicator_type, indicator_params)
                    if indicator_value is not None:
                        asset_scores.append((asset, indicator_value))
            
            if not asset_scores:
                return {}
            
            # Sort and select
            if isinstance(selection_method, list) and len(selection_method) >= 2:
                method = selection_method[0]
                count = selection_method[1] if len(selection_method) > 1 else 1
            else:
                method = 'select-top'
                count = 1
            
            if method == 'select-top':
                asset_scores.sort(key=lambda x: x[1], reverse=True)
            else:
                asset_scores.sort(key=lambda x: x[1], reverse=False)
            
            # Return equal weights for selected assets
            selected_assets = asset_scores[:count]
            if selected_assets:
                equal_weight = 1.0 / len(selected_assets)
                return {asset: equal_weight for asset, _ in selected_assets}
            
            return {}

        else:
            # Handle lists of expressions
            if isinstance(expression, list):
                # Check if this is a list of asset expressions
                asset_expressions = [item for item in expression if isinstance(item, list) and len(item) >= 2 and item[0] == 'asset']
                
                if len(asset_expressions) > 1:
                    # Multiple assets - equal weight
                    equal_weight = 1.0 / len(asset_expressions)
                    portfolio = {}
                    for asset_expr in asset_expressions:
                        asset_portfolio = self._evaluate_expression(asset_expr)
                        for asset, _ in asset_portfolio.items():
                            portfolio[asset] = equal_weight
                    return portfolio
                elif len(expression) == 1 and isinstance(expression[0], list):
                    # Single sub-expression
                    return self._evaluate_expression(expression[0])
            
            raise ValueError(f"Unknown expression operator: {operator}")

    def get_target_portfolio(self, date: Union[str, pd.Timestamp]) -> Dict[str, float]:
        """
        The main entry point to start the evaluation for a specific date.

        Args:
            date (Union[str, pd.Timestamp]): The date for which to evaluate the strategy.

        Returns:
            Dict[str, float]: A dictionary representing the target portfolio,
                              with symbols as keys and weights as values.
        """
        self.evaluation_date = pd.to_datetime(date)
        
        # The top-level trading logic is the third element of the initial JSON list
        root_expression = self.symphony[2]
        
        portfolio = self._evaluate_expression(root_expression)
        
        # Normalize weights to sum to 1, as a safeguard.
        total_weight = sum(portfolio.values())
        if total_weight > 0:
            return {asset: weight / total_weight for asset, weight in portfolio.items()}
        
        return portfolio
