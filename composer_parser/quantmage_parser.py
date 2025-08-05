# quantmage_parser.py
"""
This module provides a Quantmage parser to convert Quantmage's JSON-based strategy format
into the JSON format expected by the ComposerStrategy class.
"""
import json
from typing import Dict, List, Any, Union, Optional
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class QuantmageParser:
    """
    Parses Quantmage's JSON-based strategy format into Composer symphony format.
    
    Quantmage uses a nested structure with "incantations" and "conditions" that need
    to be converted to Composer's LISP-style format.
    """
    
    def __init__(self):
        self.symbol_mapping = {
            # Add any symbol mappings if needed (e.g., crypto symbols)
        }
    
    def parse_quantmage_file(self, file_path: str) -> List:
        """
        Parse a Quantmage strategy file and convert it to Composer format.
        
        Args:
            file_path (str): Path to the Quantmage JSON file
            
        Returns:
            List: Composer symphony format
        """
        with open(file_path, 'r') as f:
            quantmage_data = json.load(f)
        
        return self.convert_quantmage_to_composer(quantmage_data)
    
    def parse_quantmage_json(self, quantmage_json: Dict) -> List:
        """
        Parse Quantmage JSON data and convert it to Composer format.
        
        Args:
            quantmage_json (Dict): Quantmage strategy data
            
        Returns:
            List: Composer symphony format
        """
        return self.convert_quantmage_to_composer(quantmage_json)
    
    def convert_quantmage_to_composer(self, quantmage_data: Dict) -> List:
        """
        Convert Quantmage strategy format to Composer symphony format.
        
        Args:
            quantmage_data (Dict): Quantmage strategy data
            
        Returns:
            List: Composer symphony format
        """
        # Extract basic strategy info
        name = quantmage_data.get('name', 'Quantmage Strategy')
        description = quantmage_data.get('description', '')
        benchmark_ticker = quantmage_data.get('benchmark_ticker', 'SPY')
        
        # Convert the main incantation to Composer format
        root_incantation = quantmage_data.get('incantation', {})
        composer_expression = self._convert_incantation_to_composer(root_incantation)
        
        # Create Composer symphony structure
        symphony = [
            "symphony",
            [":name", name],
            [":description", description],
            [":rebalance", "daily"],  # Default to daily rebalancing
            [":rebalance-corridor-width", 0.05],  # 5% corridor
            composer_expression
        ]
        
        return symphony
    
    def _convert_incantation_to_composer(self, incantation: Dict) -> List:
        """
        Convert a Quantmage incantation to Composer format.
        
        Args:
            incantation (Dict): Quantmage incantation
            
        Returns:
            List: Composer expression
        """
        incantation_type = incantation.get('incantation_type', '')
        
        if incantation_type == 'Weighted':
            return self._convert_weighted_incantation(incantation)
        elif incantation_type == 'IfElse':
            return self._convert_ifelse_incantation(incantation)
        elif incantation_type == 'Filtered':
            return self._convert_filtered_incantation(incantation)
        elif incantation_type == 'Ticker':
            return self._convert_ticker_incantation(incantation)
        else:
            logging.warning(f"Unknown incantation type: {incantation_type}")
            return ["empty"]
    
    def _convert_weighted_incantation(self, incantation: Dict) -> List:
        """
        Convert a Weighted incantation to Composer wt-cash-equal format.
        """
        sub_incantations = incantation.get('incantations', [])
        
        if len(sub_incantations) == 1:
            # Single incantation - convert directly
            return self._convert_incantation_to_composer(sub_incantations[0])
        else:
            # Multiple incantations - use wt-cash-equal
            children = [self._convert_incantation_to_composer(sub) for sub in sub_incantations]
            return ["wt-cash-equal", children]
    
    def _convert_ifelse_incantation(self, incantation: Dict) -> List:
        """
        Convert an IfElse incantation to Composer if format.
        """
        condition = incantation.get('condition', {})
        then_incantation = incantation.get('then_incantation', {})
        else_incantation = incantation.get('else_incantation', {})
        
        # Convert condition
        composer_condition = self._convert_condition_to_composer(condition)
        
        # Convert then and else branches
        then_branch = self._convert_incantation_to_composer(then_incantation)
        else_branch = self._convert_incantation_to_composer(else_incantation)
        
        return ["if", composer_condition, then_branch, else_branch]
    
    def _convert_filtered_incantation(self, incantation: Dict) -> List:
        """
        Convert a Filtered incantation to Composer filter format.
        """
        sub_incantations = incantation.get('incantations', [])
        sort_indicator = incantation.get('sort_indicator', {})
        count = incantation.get('count', 1)
        bottom = incantation.get('bottom', False)
        
        # Convert ticker symbols to assets
        assets = []
        for sub_inc in sub_incantations:
            if sub_inc.get('incantation_type') == 'Ticker':
                symbol = sub_inc.get('symbol', '')
                name = sub_inc.get('name', symbol)
                assets.append(self._create_asset(symbol, name))
        
        # Convert sort indicator
        sort_fn, sort_params = self._convert_indicator_to_composer(sort_indicator)
        
        # Create filter expression
        filter_expr = ["filter"]
        filter_expr.append([":sort-by-fn", sort_fn])
        filter_expr.append([":sort-by-fn-params", sort_params])
        filter_expr.append([":select-n", count])
        filter_expr.append([":select-fn", "bottom" if bottom else "top"])
        filter_expr.append([":sort-by-window-days", sort_indicator.get('window', 10)])
        filter_expr.extend(assets)
        
        return filter_expr
    
    def _convert_ticker_incantation(self, incantation: Dict) -> List:
        """
        Convert a Ticker incantation to Composer asset format.
        """
        symbol = incantation.get('symbol', '')
        name = incantation.get('name', symbol)
        
        return self._create_asset(symbol, name)
    
    def _convert_condition_to_composer(self, condition: Dict) -> List:
        """
        Convert a Quantmage condition to Composer condition format.
        """
        condition_type = condition.get('condition_type', '')
        
        if condition_type == 'SingleCondition':
            return self._convert_single_condition(condition)
        else:
            logging.warning(f"Unknown condition type: {condition_type}")
            return ["true"]
    
    def _convert_single_condition(self, condition: Dict) -> List:
        """
        Convert a SingleCondition to Composer condition format.
        """
        lh_indicator = condition.get('lh_indicator', {})
        rh_indicator = condition.get('rh_indicator', {})
        rh_value = condition.get('rh_value', 0)
        greater_than = condition.get('greater_than', True)
        lh_ticker_symbol = condition.get('lh_ticker_symbol', '')
        
        # Convert left-hand indicator
        lh_fn, lh_params = self._convert_indicator_to_composer(lh_indicator)
        
        # Determine comparison type
        if rh_indicator.get('type'):
            # Comparing two indicators
            rh_fn, rh_params = self._convert_indicator_to_composer(rh_indicator)
            comparator = "gt" if greater_than else "lt"
            
            return [
                "if-child",
                [":comparator", comparator],
                [":lhs-fn", lh_fn],
                [":lhs-val", lh_ticker_symbol],
                [":lhs-fn-params", lh_params],
                [":rhs-fn", rh_fn],
                [":rhs-fn-params", rh_params]
            ]
        else:
            # Comparing indicator to fixed value
            comparator = "gt" if greater_than else "lt"
            
            return [
                "if-child",
                [":comparator", comparator],
                [":lhs-fn", lh_fn],
                [":lhs-val", lh_ticker_symbol],
                [":lhs-fn-params", lh_params],
                [":rhs-val", rh_value],
                [":rhs-fixed-value?", True]
            ]
    
    def _convert_indicator_to_composer(self, indicator: Dict) -> tuple:
        """
        Convert a Quantmage indicator to Composer indicator format.
        
        Returns:
            tuple: (indicator_name, parameters_dict)
        """
        indicator_type = indicator.get('type', '')
        window = indicator.get('window', 10)
        
        # Map Quantmage indicators to Composer indicators
        indicator_mapping = {
            'RelativeStrengthIndex': 'relative-strength-index',
            'CumulativeReturn': 'cumulative-return',
            'Volatility': 'standard-deviation-return',
            'MovingAverage': 'moving-average-price',
            'ExponentialMovingAverage': 'exponential-moving-average-price'
        }
        
        composer_indicator = indicator_mapping.get(indicator_type, 'relative-strength-index')
        
        return composer_indicator, {"window": window}
    
    def _create_asset(self, symbol: str, name: str) -> List:
        """
        Create a Composer asset expression.
        """
        # Handle crypto symbols
        if symbol.startswith('CRYPTO::'):
            return ["asset", [":ticker", symbol], [":name", name]]
        else:
            return ["asset", [":ticker", symbol], [":name", name], [":exchange", "XNAS"]]


def parse_quantmage_file(file_path: str) -> List:
    """
    Parse a Quantmage strategy file and convert it to Composer format.
    
    Args:
        file_path (str): Path to the Quantmage JSON file
        
    Returns:
        List: Composer symphony format
    """
    parser = QuantmageParser()
    return parser.parse_quantmage_file(file_path)


def parse_quantmage_json(quantmage_json: Dict) -> List:
    """
    Parse Quantmage JSON data and convert it to Composer format.
    
    Args:
        quantmage_json (Dict): Quantmage strategy data
        
    Returns:
        List: Composer symphony format
    """
    parser = QuantmageParser()
    return parser.parse_quantmage_json(quantmage_json) 