# composer_parser.py
"""
This module provides the ComposerStrategy class, which is responsible for
parsing and evaluating trading strategies defined in a Composer.trade-style
JSON format. It translates the LISP-like DSL into an executable trading logic.
"""
import pandas as pd
from typing import Dict, List, Any, Union

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
        Uses `asof` to find the most recent data available on or before the given date.
        """
        if symbol not in self.market_data or self.market_data[symbol].empty:
            raise ValueError(f"Market data not available for symbol: {symbol}")
        
        # Use asof to get the latest data on or before the evaluation date
        data_for_date = self.market_data[symbol].asof(date)

        if pd.isna(data_for_date).all():
            raise ValueError(f"No data available for {symbol} on or before {date.strftime('%Y-%m-%d')}")
            
        return data_for_date

    def _get_indicator_value(self, symbol: str, indicator_type: str, indicator_params: dict) -> float:
        """
        Gets the indicator value for a specific symbol and indicator type.
        """
        try:
            data = self._get_data_for_date(symbol, self.evaluation_date)
            
            if indicator_type == 'rsi':
                # RSI is stored as 'RSI' in the DataFrame
                if 'RSI' in data:
                    return data['RSI']
                else:
                    return None
            elif indicator_type == 'moving-average-price':
                # Moving average is stored as 'MA{window}' in the DataFrame
                window = indicator_params.get(':window', 20)  # default to 20
                ma_col = f'MA{window}'
                if ma_col in data:
                    return data[ma_col]
                else:
                    return None
            elif indicator_type == 'current-price':
                # Current price is stored as 'current_price' in the DataFrame
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
        This is a key part of evaluating conditions.
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
                window = params.get(':window')
                ma_column = f'MA{window}'
                if ma_column not in self.market_data[symbol].columns:
                     raise ValueError(f"Indicator '{ma_column}' not found for {symbol}. Please calculate it first.")
                return self._get_data_for_date(symbol, self.evaluation_date)[ma_column]

            elif operator == 'rsi':
                symbol = value_expression[1]
                params = value_expression[2]
                # Assuming RSI is pre-calculated and stored in a column named 'RSI'
                if 'RSI' not in self.market_data[symbol].columns:
                    raise ValueError(f"Indicator 'RSI' not found for {symbol}. Please calculate it first.")
                return self._get_data_for_date(symbol, self.evaluation_date)['RSI']
            
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
                return self._evaluate_expression(then_branch) # Pass the entire branch list
            else:
                return self._evaluate_expression(else_branch) # Pass the entire branch list

        elif operator == 'weight-equal':
            # Structure: (weight-equal [branch1] [branch2] ...)
            # This should distribute weights equally across all branches
            branches = expression[1:]
            if not branches:
                return {}
            
            # Evaluate all branches and collect all assets
            all_assets = {}
            for branch in branches:
                branch_portfolio = self._evaluate_expression(branch[0])
                for asset, weight in branch_portfolio.items():
                    if asset in all_assets:
                        all_assets[asset] += weight
                    else:
                        all_assets[asset] = weight
            
            # Distribute weights equally among all assets
            if all_assets:
                equal_weight = 1.0 / len(all_assets)
                return {asset: equal_weight for asset in all_assets}
            
            return {}


        elif operator == 'weight-specified':
            # Structure: (weight-specified weight1 asset1 weight2 asset2 ...)
            portfolio = {}
            for i in range(1, len(expression), 2):
                weight = expression[i]
                asset_expr = expression[i+1]
                asset_portfolio = self._evaluate_expression(asset_expr)
                for asset, _ in asset_portfolio.items():
                    portfolio[asset] = float(weight)
            return portfolio

        elif operator == 'asset':
            # Base case: returns the asset itself with a nominal weight of 1.0
            # The parent expression (e.g., weight-specified) will assign the true weight.
            return {expression[1]: 1.0}
        
        elif operator == 'group':
            # A group contains a sub-expression that defines the assets within it.
            # We evaluate the sub-expression.
            return self._evaluate_expression(expression[2][0])

        elif operator == 'filter':
            # Structure: (filter indicator_criteria selection_method asset_list)
            # Example: (filter (rsi {:window 10}) (select-top 1) [asset1 asset2 ...])
            indicator_criteria = expression[1]
            selection_method = expression[2]
            asset_list = expression[3]
            
            if not asset_list:
                return {}
            
            # Extract the indicator type and parameters
            if isinstance(indicator_criteria, list) and len(indicator_criteria) >= 2:
                indicator_type = indicator_criteria[0]  # e.g., 'rsi'
                # Handle indicator parameters properly
                if len(indicator_criteria) > 2 and isinstance(indicator_criteria[2], dict):
                    indicator_params = indicator_criteria[2]  # e.g., {:window 10}
                else:
                    indicator_params = {}
            else:
                # Fallback to first asset if indicator criteria is malformed
                return self._evaluate_expression(asset_list[0])
            
            # Evaluate the indicator for each asset and collect scores
            asset_scores = []
            for asset_expr in asset_list:
                try:
                    asset_portfolio = self._evaluate_expression(asset_expr)
                    for asset, weight in asset_portfolio.items():
                        if weight > 0:  # Only consider assets with positive weight
                            # Get the indicator value for this asset using the helper method
                            indicator_value = self._get_indicator_value(asset, indicator_type, indicator_params)
                            if indicator_value is not None:
                                asset_scores.append((asset, indicator_value))
                except Exception as e:
                    # Skip assets that can't be evaluated
                    continue
            
            if not asset_scores:
                return {}
            
            # Sort by indicator value (descending for select-top, ascending for select-bottom)
            if isinstance(selection_method, list) and len(selection_method) >= 2:
                method = selection_method[0]  # e.g., 'select-top'
                count = selection_method[1] if len(selection_method) > 1 else 1
            else:
                method = 'select-top'
                count = 1
            
            if method == 'select-top':
                asset_scores.sort(key=lambda x: x[1], reverse=True)
            elif method == 'select-bottom':
                asset_scores.sort(key=lambda x: x[1], reverse=False)
            else:
                # Default to select-top
                asset_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select the top/bottom assets
            selected_assets = asset_scores[:count]
            
            # Return equal weights for selected assets
            if selected_assets:
                equal_weight = 1.0 / len(selected_assets)
                return {asset: equal_weight for asset, _ in selected_assets}
            
            return {}

        else:
            # This handles cases where an expression is a list containing multiple sub-expressions
            # or a single sub-expression, a common pattern in the Composer JSON.
            if isinstance(expression, list):
                # Check if this is a list of asset expressions (equal-weighted assets)
                asset_expressions = []
                for item in expression:
                    if isinstance(item, list) and len(item) >= 2 and item[0] == 'asset':
                        asset_expressions.append(item)
                
                if len(asset_expressions) > 1:
                    # Multiple asset expressions - treat as equal-weighted
                    equal_weight = 1.0 / len(asset_expressions)
                    portfolio = {}
                    for asset_expr in asset_expressions:
                        asset_portfolio = self._evaluate_expression(asset_expr)
                        for asset, _ in asset_portfolio.items():
                            portfolio[asset] = equal_weight
                    return portfolio
                elif len(expression) == 1 and isinstance(expression[0], list):
                    # Single sub-expression - recurse into it
                    return self._evaluate_expression(expression[0])
                else:
                    raise ValueError(f"Unknown expression structure: {expression}")
            else:
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
