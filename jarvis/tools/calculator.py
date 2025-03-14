"""
Calculator tool for Jarvis.
This tool provides simple and advanced mathematical operations.
"""
import math
import logging
from typing import Dict, Any, Union, List
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Calculator:
    """Calculator tool for mathematical operations."""
    
    def __init__(self):
        """Initialize the calculator tool."""
        logger.info("Calculator tool initialized")
    
    def evaluate(self, expression: str) -> Dict[str, Any]:
        """Evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Dictionary with evaluation result or error
        """
        if not expression or not isinstance(expression, str):
            error_msg = f"Invalid expression: {expression}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            # Clean the expression to make it safer
            clean_expression = self._sanitize_expression(expression)
            
            # Create a safe dictionary of allowed functions and constants
            safe_dict = {
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'len': len,
                'int': int,
                'float': float,
                'pow': pow,
                'sqrt': math.sqrt,
                'ceil': math.ceil,
                'floor': math.floor,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'pi': math.pi,
                'e': math.e,
                'radians': math.radians,
                'degrees': math.degrees
            }
            
            # Evaluate the expression in the safe environment
            result = eval(clean_expression, {"__builtins__": {}}, safe_dict)
            
            logger.info(f"Successfully evaluated expression: {expression} = {result}")
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
                
        except Exception as e:
            error_msg = f"Error evaluating expression '{expression}': {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _sanitize_expression(self, expression: str) -> str:
        """Sanitize a mathematical expression to make it safer.
        
        Args:
            expression: Mathematical expression to sanitize
            
        Returns:
            Sanitized expression
        """
        # Remove any potential dangerous characters
        sanitized = re.sub(r'[^0-9+\-*/().,%\s\[\]a-zA-Z]', '', expression)
        
        # Check for potential function or method access
        if re.search(r'(__[\w]+)|(\b(import|exec|eval|compile|open|file|os|sys)\b)', sanitized):
            raise ValueError("Potential security risk detected in expression")
            
        return sanitized
    
    def solve_equation(self, equation: str) -> Dict[str, Any]:
        """Attempt to solve a simple equation.
        
        This is a basic implementation that can solve simple linear equations
        in the form of ax + b = c.
        
        Args:
            equation: Equation to solve in the form "ax + b = c"
            
        Returns:
            Dictionary with solution or error
        """
        if not equation or not isinstance(equation, str):
            error_msg = f"Invalid equation: {equation}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            # Check if we have a valid equation (containing =)
            if "=" not in equation:
                error_msg = f"Not a valid equation (missing =): {equation}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            # Very simple equation solver - only works for basic linear equations
            # Format: ax + b = c
            left, right = equation.split("=")
            
            # Move all terms with x to the left and all constants to the right
            left = left.strip()
            right = right.strip()
            
            # Check if x is on the right side and rearrange if needed
            if "x" in right:
                # Swap sides if x is on the right
                left, right = right, left
                
            # Try to extract the coefficient of x
            x_term = None
            constant = 0
            
            # Find the x term
            match = re.search(r'([+-]?\s*\d*\.?\d*)\s*x', left)
            if match:
                coef = match.group(1).strip()
                if coef == "+" or coef == "":
                    coef = "1"
                elif coef == "-":
                    coef = "-1"
                x_term = float(coef)
                
            # Remove the x term from the left side
            left = re.sub(r'([+-]?\s*\d*\.?\d*)\s*x', '', left)
            
            # Extract any remaining constants on the left
            left_constants = re.findall(r'([+-]?\s*\d+\.?\d*)', left)
            for const in left_constants:
                constant -= float(const)
                
            # Extract constants on the right
            right_constants = re.findall(r'([+-]?\s*\d+\.?\d*)', right)
            for const in right_constants:
                constant += float(const)
                
            # Solve for x
            if x_term is None or x_term == 0:
                if constant == 0:
                    solution = "All real numbers (infinite solutions)"
                else:
                    solution = "No solution"
            else:
                solution = constant / x_term
                
            logger.info(f"Successfully solved equation: {equation}, x = {solution}")
            return {
                "success": True,
                "equation": equation,
                "variable": "x",
                "solution": solution
            }
                
        except Exception as e:
            error_msg = f"Error solving equation '{equation}': {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert between different units.
        
        Supports:
        - Length: meters, feet, inches, centimeters, kilometers, miles
        - Weight: kilograms, pounds, grams, ounces
        - Temperature: celsius, fahrenheit, kelvin
        
        Args:
            value: Value to convert
            from_unit: Unit to convert from
            to_unit: Unit to convert to
            
        Returns:
            Dictionary with conversion result or error
        """
        if not isinstance(value, (int, float)):
            error_msg = f"Invalid value: {value}. Must be a number."
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        # Normalize units to lowercase
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # Define conversion factors to SI units
        length_units = {
            "meters": 1,
            "meter": 1,
            "m": 1,
            "centimeters": 0.01,
            "centimeter": 0.01,
            "cm": 0.01,
            "kilometers": 1000,
            "kilometer": 1000,
            "km": 1000,
            "inches": 0.0254,
            "inch": 0.0254,
            "in": 0.0254,
            "feet": 0.3048,
            "foot": 0.3048,
            "ft": 0.3048,
            "miles": 1609.34,
            "mile": 1609.34,
            "mi": 1609.34
        }
        
        weight_units = {
            "kilograms": 1,
            "kilogram": 1,
            "kg": 1,
            "grams": 0.001,
            "gram": 0.001,
            "g": 0.001,
            "pounds": 0.453592,
            "pound": 0.453592,
            "lb": 0.453592,
            "ounces": 0.0283495,
            "ounce": 0.0283495,
            "oz": 0.0283495
        }
        
        # Temperature requires special handling
        temp_units = ["celsius", "fahrenheit", "kelvin", "c", "f", "k"]
        
        try:
            # Check if both units are of the same type
            if from_unit in length_units and to_unit in length_units:
                # Convert to SI then to target unit
                si_value = value * length_units[from_unit]
                result = si_value / length_units[to_unit]
                unit_type = "length"
            elif from_unit in weight_units and to_unit in weight_units:
                # Convert to SI then to target unit
                si_value = value * weight_units[from_unit]
                result = si_value / weight_units[to_unit]
                unit_type = "weight"
            elif from_unit in temp_units and to_unit in temp_units:
                # Normalize temperature unit names
                if from_unit == "c":
                    from_unit = "celsius"
                elif from_unit == "f":
                    from_unit = "fahrenheit"
                elif from_unit == "k":
                    from_unit = "kelvin"
                    
                if to_unit == "c":
                    to_unit = "celsius"
                elif to_unit == "f":
                    to_unit = "fahrenheit"
                elif to_unit == "k":
                    to_unit = "kelvin"
                
                # Convert to Celsius first
                if from_unit == "celsius":
                    celsius = value
                elif from_unit == "fahrenheit":
                    celsius = (value - 32) * 5/9
                elif from_unit == "kelvin":
                    celsius = value - 273.15
                
                # Convert from Celsius to target
                if to_unit == "celsius":
                    result = celsius
                elif to_unit == "fahrenheit":
                    result = celsius * 9/5 + 32
                elif to_unit == "kelvin":
                    result = celsius + 273.15
                    
                unit_type = "temperature"
            else:
                error_msg = f"Cannot convert between {from_unit} and {to_unit}. Units are not compatible."
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            logger.info(f"Successfully converted {value} {from_unit} to {result} {to_unit}")
            return {
                "success": True,
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": result,
                "converted_unit": to_unit,
                "unit_type": unit_type
            }
                
        except Exception as e:
            error_msg = f"Error converting {value} {from_unit} to {to_unit}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def summarize_results(self, result: Dict[str, Any]) -> str:
        """Summarize calculation results into a readable format.
        
        Args:
            result: Calculation result dictionary
            
        Returns:
            Formatted summary string
        """
        if not result.get("success", False):
            return f"Calculation Error: {result.get('error', 'Unknown error')}"
            
        if "expression" in result:
            # Expression evaluation result
            summary = f"Expression: {result['expression']}\n"
            summary += f"Result: {result['result']}"
            
        elif "equation" in result:
            # Equation solving result
            summary = f"Equation: {result['equation']}\n"
            
            if isinstance(result['solution'], str):
                summary += f"Solution: {result['solution']}"
            else:
                summary += f"Solution: {result['variable']} = {result['solution']}"
                
        elif "converted_value" in result:
            # Unit conversion result
            summary = f"Unit Conversion:\n"
            summary += f"{result['original_value']} {result['original_unit']} = {result['converted_value']} {result['converted_unit']}"
            
        else:
            summary = f"Calculation Result: {result}"
            
        logger.info("Summarized calculation results")
        return summary 