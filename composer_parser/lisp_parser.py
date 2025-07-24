# lisp_parser.py
"""
This module provides a Lisp parser to convert Composer.trade Lisp-style symphony files
into the JSON format expected by the ComposerStrategy class.
"""
import re
from typing import List, Union, Dict, Any

class LispParser:
    """
    Parses Lisp-style Composer.trade symphony files into JSON format.
    """
    
    def __init__(self):
        self.tokens = []
        self.current_token = 0
    
    def tokenize(self, lisp_string: str) -> List[str]:
        """
        Tokenizes a Lisp string into individual tokens.
        """
        # Remove comments and extra whitespace
        lisp_string = re.sub(r';.*$', '', lisp_string, flags=re.MULTILINE)
        
        # Add spaces around parentheses and brackets for easier tokenization
        lisp_string = re.sub(r'\(', ' ( ', lisp_string)
        lisp_string = re.sub(r'\)', ' ) ', lisp_string)
        lisp_string = re.sub(r'\[', ' [ ', lisp_string)
        lisp_string = re.sub(r'\]', ' ] ', lisp_string)
        lisp_string = re.sub(r'\{', ' { ', lisp_string)
        lisp_string = re.sub(r'\}', ' } ', lisp_string)
        
        # Split on whitespace and filter out empty tokens
        tokens = [token.strip() for token in lisp_string.split() if token.strip()]
        return tokens
    
    def parse_atom(self, token: str) -> Union[str, int, float, bool]:
        """
        Parses an atom (string, number, boolean, etc.) from a token.
        """
        # Try to parse as number
        try:
            if '.' in token:
                return float(token)
            else:
                return int(token)
        except ValueError:
            pass
        
        # Check for boolean
        if token.lower() == 'true':
            return True
        if token.lower() == 'false':
            return False
        
        # Check for keyword (starts with :)
        if token.startswith(':'):
            return token
        
        # Check for string (remove quotes if present)
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        
        # Handle special case where token ends with comma (remove it)
        if token.endswith(','):
            token = token[:-1]
            # Try to parse the cleaned token
            try:
                if '.' in token:
                    return float(token)
                else:
                    return int(token)
            except ValueError:
                pass
        
        # Default to symbol
        return token
    
    def parse_expression(self) -> Union[List, str, int, float, bool]:
        """
        Parses a Lisp expression recursively.
        """
        if self.current_token >= len(self.tokens):
            raise ValueError("Unexpected end of input")
        
        token = self.tokens[self.current_token]
        
        if token == '(' or token == '[' or token == '{':
            # Start of a list/array/object
            opening_token = token
            closing_token = ')' if token == '(' else ']' if token == '[' else '}'
            
            self.current_token += 1
            result = []
            
            while (self.current_token < len(self.tokens) and 
                   self.tokens[self.current_token] != closing_token):
                result.append(self.parse_expression())
            
            if self.current_token >= len(self.tokens):
                raise ValueError(f"Unmatched opening {opening_token}")
            
            self.current_token += 1  # consume closing token
            return result
        
        elif token in [')', ']', '}']:
            raise ValueError(f"Unexpected closing {token}")
        
        else:
            # Atom
            self.current_token += 1
            return self.parse_atom(token)
    
    def parse(self, lisp_string: str) -> List:
        """
        Parses a complete Lisp string into a JSON-compatible structure.
        """
        self.tokens = self.tokenize(lisp_string)
        self.current_token = 0
        
        result = self.parse_expression()
        
        if self.current_token < len(self.tokens):
            raise ValueError(f"Unexpected tokens after parsing: {self.tokens[self.current_token:]}")
        
        return result

def parse_symphony_file(file_path: str) -> List:
    """
    Parses a symphony file and returns the parsed structure.
    
    Args:
        file_path (str): Path to the symphony file
        
    Returns:
        List: The parsed symphony structure
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    parser = LispParser()
    return parser.parse(content) 