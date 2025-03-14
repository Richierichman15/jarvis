"""
Debug tool for Jarvis.
This tool provides debugging capabilities for Jarvis components.
"""
import os
import sys
import time
import logging
import inspect
import traceback
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DebugTool:
    """Debug tool for debugging Jarvis components and tools."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize the debug tool.
        
        Args:
            log_dir: Directory to store debug logs, defaults to 'jarvis/debug_logs'
        """
        if log_dir is None:
            # Default to jarvis/debug_logs relative to the Jarvis installation
            jarvis_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(jarvis_root, "debug_logs")
            
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_dir = log_dir
        self.log_level = logging.DEBUG
        self.start_time = time.time()
        
        # Set up file handler for debug logs
        log_file = os.path.join(log_dir, f"jarvis_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to root logger
        logging.getLogger().addHandler(file_handler)
        
        logger.info(f"Debug tool initialized, logging to {log_file}")
        self.log_file = log_file
    
    def function_timer(self, func: Callable) -> Callable:
        """Decorator to time a function's execution.
        
        Args:
            func: Function to time
            
        Returns:
            Wrapped function
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"Completed {func.__name__} in {elapsed:.4f} seconds")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Error in {func.__name__} after {elapsed:.4f} seconds: {str(e)}")
                raise
                
        return wrapper
    
    def log_call(self, tool_name: str, params: Dict[str, Any], result: Any) -> None:
        """Log a tool call for debugging.
        
        Args:
            tool_name: Name of the tool called
            params: Parameters passed to the tool
            result: Result of the tool call
        """
        timestamp = datetime.now().isoformat()
        
        logger.debug(f"Tool Call: {tool_name}")
        logger.debug(f"Parameters: {params}")
        
        # Truncate result if it's too large
        result_str = str(result)
        if len(result_str) > 1000:
            result_str = result_str[:1000] + "... [truncated]"
            
        logger.debug(f"Result: {result_str}")
        
        # Log to a specific tool call log
        tool_log_file = os.path.join(self.log_dir, f"tool_calls.log")
        with open(tool_log_file, 'a', encoding='utf-8') as f:
            f.write(f"--- {timestamp} - {tool_name} ---\n")
            f.write(f"Parameters: {params}\n")
            f.write(f"Result: {result_str}\n\n")
    
    def test_tool(self, tool_instance: Any, method_name: str, **params) -> Dict[str, Any]:
        """Test a tool's method with the given parameters.
        
        Args:
            tool_instance: Tool instance to test
            method_name: Method name to call
            **params: Parameters to pass to the method
            
        Returns:
            Dictionary with test results
        """
        if not hasattr(tool_instance, method_name):
            error_msg = f"Method {method_name} not found in tool {tool_instance.__class__.__name__}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        method = getattr(tool_instance, method_name)
        if not callable(method):
            error_msg = f"{method_name} is not a callable method"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        logger.info(f"Testing {tool_instance.__class__.__name__}.{method_name} with params: {params}")
        
        try:
            # Time the method call
            start_time = time.time()
            result = method(**params)
            elapsed = time.time() - start_time
            
            # Log the result
            logger.info(f"Tool test completed in {elapsed:.4f} seconds")
            
            return {
                "success": True,
                "result": result,
                "execution_time": elapsed,
                "tool": tool_instance.__class__.__name__,
                "method": method_name,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"Error testing tool: {str(e)}"
            logger.error(error_msg)
            logger.debug(tb)
            
            return {
                "success": False,
                "error": error_msg,
                "traceback": tb,
                "tool": tool_instance.__class__.__name__,
                "method": method_name,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_tool_info(self, tool_instance: Any) -> Dict[str, Any]:
        """Get information about a tool.
        
        Args:
            tool_instance: Tool instance to get information about
            
        Returns:
            Dictionary with tool information
        """
        if tool_instance is None:
            error_msg = "No tool instance provided"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            # Get tool class name
            class_name = tool_instance.__class__.__name__
            
            # Get tool methods
            methods = []
            for name, member in inspect.getmembers(tool_instance):
                if not name.startswith('_') and callable(member):
                    # Get method signature
                    signature = str(inspect.signature(member))
                    
                    # Get method docstring
                    docstring = inspect.getdoc(member) or "No documentation available"
                    
                    methods.append({
                        "name": name,
                        "signature": signature,
                        "docstring": docstring
                    })
                    
            logger.info(f"Retrieved information for tool {class_name}")
            
            return {
                "success": True,
                "tool": class_name,
                "methods": methods,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error getting tool information: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_debug_logs(self, num_lines: int = 50) -> Dict[str, Any]:
        """Get recent debug logs.
        
        Args:
            num_lines: Number of recent log lines to return
            
        Returns:
            Dictionary with log lines
        """
        try:
            # Read the log file
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # Get the last num_lines lines
                lines = f.readlines()
                last_lines = lines[-num_lines:] if len(lines) > num_lines else lines
                
            logger.info(f"Retrieved {len(last_lines)} log lines")
            
            return {
                "success": True,
                "log_file": self.log_file,
                "lines": last_lines,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error getting debug logs: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    def summarize_results(self, result: Dict[str, Any]) -> str:
        """Summarize debug results into a readable format.
        
        Args:
            result: Debug result dictionary
            
        Returns:
            Formatted summary string
        """
        if not result.get("success", False):
            return f"Debug Error: {result.get('error', 'Unknown error')}"
            
        summary = "Debug Information:\n\n"
        
        if "result" in result:
            # Tool test result
            summary += f"Tool Test: {result.get('tool', 'Unknown')}.{result.get('method', 'Unknown')}\n"
            summary += f"Execution Time: {result.get('execution_time', 'N/A'):.4f} seconds\n"
            summary += f"Parameters: {result.get('params', {})}\n\n"
            
            # Format the result
            result_data = result["result"]
            if isinstance(result_data, dict):
                summary += "Result:\n"
                for key, value in result_data.items():
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "... [truncated]"
                    summary += f"- {key}: {value_str}\n"
            else:
                result_str = str(result_data)
                if len(result_str) > 500:
                    result_str = result_str[:500] + "... [truncated]"
                summary += f"Result: {result_str}\n"
                
        elif "methods" in result:
            # Tool information
            summary += f"Tool Information: {result.get('tool', 'Unknown')}\n\n"
            summary += "Available Methods:\n"
            
            for method in result["methods"]:
                summary += f"- {method['name']}{method['signature']}\n"
                
                # Add simplified docstring (first line only)
                docstring = method['docstring'].split('\n')[0]
                summary += f"  {docstring}\n"
                
        elif "lines" in result:
            # Debug logs
            summary += f"Debug Logs from {result.get('log_file', 'Unknown')}\n"
            summary += f"Recent {len(result['lines'])} lines:\n\n"
            
            for line in result["lines"]:
                summary += line
                
        return summary 