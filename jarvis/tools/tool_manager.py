"""
Tool manager for Jarvis.
This module manages the available tools and their execution.
"""
import re
import logging
from typing import Dict, Any, List, Optional

from .web_search import WebSearch
from .calculator import Calculator
from .file_operations import FileOperations
from .system_info import SystemInfo
from .debug import DebugTool
from ..config import AVAILABLE_TOOLS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolManager:
    """Manager for handling Jarvis's tools."""
    
    def __init__(self):
        """Initialize the tool manager with available tools."""
        self.tools = {}
        
        # Initialize web search tool if enabled
        if "web_search" in AVAILABLE_TOOLS:
            self.tools["web_search"] = WebSearch()
            logger.info("Web search tool initialized")
            
        # Initialize calculator tool if enabled
        if "calculator" in AVAILABLE_TOOLS:
            self.tools["calculator"] = Calculator()
            logger.info("Calculator tool initialized")
            
        # Initialize file operations tool if enabled
        if "file_operations" in AVAILABLE_TOOLS:
            self.tools["file_operations"] = FileOperations()
            logger.info("File operations tool initialized")
            
        # Initialize system info tool if enabled
        if "system_info" in AVAILABLE_TOOLS:
            self.tools["system_info"] = SystemInfo()
            logger.info("System info tool initialized")
            
        # Always initialize debug tool (but not exposed to user)
        self.debug_tool = DebugTool()
        logger.info("Debug tool initialized")
            
        logger.info(f"Available tools: {', '.join(self.get_available_tools())}")
    
    def get_available_tools(self) -> List[str]:
        """Get the list of available tools.
        
        Returns:
            List of available tool names
        """
        return list(self.tools.keys())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions for all available tools.
        
        Returns:
            Dict of tool names and descriptions
        """
        descriptions = {
            "web_search": "Search the web for information using DuckDuckGo",
            "calculator": "Perform mathematical calculations and unit conversions",
            "file_operations": "Read, write, and list files and directories",
            "system_info": "Get information about system resources like CPU and memory",
        }
        
        return {name: descriptions.get(name, "No description available") 
                for name in self.get_available_tools()}
    
    def detect_tool_calls(self, query: str) -> List[Dict[str, Any]]:
        """Detect potential tool calls in a user query.
        
        This uses simple regex patterns to detect if a query
        is asking to use a specific tool.
        
        Args:
            query: User's input text
            
        Returns:
            List of detected tool calls
        """
        tool_calls = []
        query = query.lower()
        
        # Weather related patterns should use web search
        weather_patterns = [
            r"(weather|forecast|temperature|rain|snow|precipitation|humidity|climate).*?(in|for|at|today|tomorrow|this week|this weekend)",
            r"(is it|will it).*(rain|snow|sunny|cloudy|warm|cold|hot)",
            r"(what's|what is|how's|how is).*(weather|temperature).*(in|at|for)",
        ]
        
        # News related patterns
        news_patterns = [
            r"(news|headlines|latest).*(about|on|regarding)",
            r"(what happened|what's happening|what is happening).*(today|now|recently)",
        ]
        
        # Information seeking patterns
        info_patterns = [
            r"(who is|what is|where is|when is|why is|how is|how to|what are|where are|when are)",
            r"(tell me about|information about|details about|facts about|give me.*?about)",
            r"(search|look up|find|google|search for|find information about)",
        ]
        
        # Calculator patterns
        calc_patterns = [
            r"(calculate|compute|evaluate|solve|what is)\s+([0-9+\-*/().%\s]+)",
            r"(convert|change)\s+(\d+\.?\d*)\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)",
            r"(solve|what is the solution to)\s+([^=]+=.+)",
        ]
        
        # File operation patterns
        file_patterns = [
            r"(read|open|show|display)\s+(the\s+)?(file|contents\s+of)\s+([^\s]+)",
            r"(write|save|create)\s+(to\s+)?(a\s+)?(file|document)\s+([^\s]+)",
            r"(list|show)\s+(the\s+)?(contents\s+of|files\s+in|directory)\s+([^\s]+)",
        ]
        
        # System info patterns
        system_patterns = [
            r"(cpu|processor|memory|ram|disk|storage|system)\s+(usage|utilization|info|information|status)",
            r"(how much|what is|show|display|tell me about)\s+(cpu|memory|ram|disk|storage)\s+(usage|utilization)",
            r"(system|computer|machine|device)\s+(status|health|performance|specs|specifications)",
        ]
        
        # Check if the query matches any web search patterns
        if "web_search" in self.tools:
            all_patterns = weather_patterns + news_patterns + info_patterns
            
            for pattern in all_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    logger.info(f"Detected web search intent in query: {query}")
                    tool_calls.append({
                        "tool": "web_search",
                        "params": {"query": query.strip()},
                        "confidence": 0.8  # Confidence score
                    })
                    break
        
        # Check if the query matches any calculator patterns
        if "calculator" in self.tools and not tool_calls:
            # Check for expressions to evaluate
            for pattern in calc_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    if match.group(1) in ["calculate", "compute", "evaluate", "what is"]:
                        # Extract the expression
                        expression = match.group(2).strip()
                        if expression:
                            logger.info(f"Detected calculator intent in query: {query}")
                            tool_calls.append({
                                "tool": "calculator",
                                "params": {"expression": expression},
                                "confidence": 0.9
                            })
                            break
                    elif match.group(1) in ["convert", "change"]:
                        # Extract unit conversion parameters
                        value = float(match.group(2))
                        from_unit = match.group(3)
                        to_unit = match.group(4)
                        logger.info(f"Detected unit conversion intent in query: {query}")
                        tool_calls.append({
                            "tool": "calculator",
                            "params": {
                                "value": value,
                                "from_unit": from_unit,
                                "to_unit": to_unit,
                                "conversion": True
                            },
                            "confidence": 0.9
                        })
                        break
                    elif match.group(1) in ["solve", "what is the solution to"]:
                        # Extract the equation
                        equation = match.group(2).strip()
                        if equation:
                            logger.info(f"Detected equation solving intent in query: {query}")
                            tool_calls.append({
                                "tool": "calculator",
                                "params": {"equation": equation},
                                "confidence": 0.9
                            })
                            break
                        
        # Check if the query matches any file operation patterns
        if "file_operations" in self.tools and not tool_calls:
            for pattern in file_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    action = match.group(1).lower()
                    target = match.group(4) if len(match.groups()) >= 4 else ""
                    
                    if action in ["read", "open", "show", "display"]:
                        logger.info(f"Detected file read intent in query: {query}")
                        tool_calls.append({
                            "tool": "file_operations",
                            "params": {"operation": "read", "file_path": target},
                            "confidence": 0.8
                        })
                        break
                    elif action in ["write", "save", "create"]:
                        # Note: content will need to be provided separately
                        logger.info(f"Detected file write intent in query: {query}")
                        tool_calls.append({
                            "tool": "file_operations",
                            "params": {"operation": "write", "file_path": target, "content": ""},
                            "confidence": 0.7  # Lower confidence as we need content
                        })
                        break
                    elif action in ["list", "show"]:
                        logger.info(f"Detected directory list intent in query: {query}")
                        tool_calls.append({
                            "tool": "file_operations",
                            "params": {"operation": "list", "directory_path": target},
                            "confidence": 0.8
                        })
                        break
                        
        # Check if the query matches any system info patterns
        if "system_info" in self.tools and not tool_calls:
            for pattern in system_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    # Determine which system info to get
                    if "cpu" in query:
                        info_type = "cpu"
                    elif "memory" in query or "ram" in query:
                        info_type = "memory"
                    elif "disk" in query or "storage" in query:
                        info_type = "disk"
                    else:
                        info_type = "all"  # Default to all
                        
                    logger.info(f"Detected system info intent in query: {query}")
                    tool_calls.append({
                        "tool": "system_info",
                        "params": {"info_type": info_type},
                        "confidence": 0.8
                    })
                    break
        
        logger.info(f"Detected {len(tool_calls)} tool calls")
        return tool_calls
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        """Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution result or None if tool not found
        """
        start_time = None
        result = None
        
        try:
            if tool_name not in self.tools:
                logger.warning(f"Tool {tool_name} not found")
                return None
                
            tool = self.tools[tool_name]
            
            if tool_name == "web_search":
                query = params.get("query", "")
                if not query:
                    logger.warning("No search query provided")
                    return "Error: No search query provided."
                
                logger.info(f"Executing web search with query: {query}")
                results = tool.search(query)
                result = tool.summarize_results(results)
                
            elif tool_name == "calculator":
                if "expression" in params:
                    expression = params["expression"]
                    logger.info(f"Evaluating expression: {expression}")
                    calc_result = tool.evaluate(expression)
                    result = tool.summarize_results(calc_result)
                elif "equation" in params:
                    equation = params["equation"]
                    logger.info(f"Solving equation: {equation}")
                    calc_result = tool.solve_equation(equation)
                    result = tool.summarize_results(calc_result)
                elif "conversion" in params and params["conversion"]:
                    value = params["value"]
                    from_unit = params["from_unit"]
                    to_unit = params["to_unit"]
                    logger.info(f"Converting {value} {from_unit} to {to_unit}")
                    calc_result = tool.convert_units(value, from_unit, to_unit)
                    result = tool.summarize_results(calc_result)
                else:
                    logger.warning("Invalid calculator parameters")
                    return "Error: Missing required calculator parameters."
                    
            elif tool_name == "file_operations":
                operation = params.get("operation")
                if operation == "read":
                    file_path = params.get("file_path")
                    if not file_path:
                        logger.warning("No file path provided for read operation")
                        return "Error: No file path provided for read operation."
                        
                    logger.info(f"Reading file: {file_path}")
                    op_result = tool.read_file(file_path)
                    result = tool.summarize_results(op_result)
                    
                elif operation == "write":
                    file_path = params.get("file_path")
                    content = params.get("content", "")
                    append = params.get("append", False)
                    
                    if not file_path:
                        logger.warning("No file path provided for write operation")
                        return "Error: No file path provided for write operation."
                        
                    logger.info(f"Writing to file: {file_path}")
                    op_result = tool.write_file(file_path, content, append)
                    result = tool.summarize_results(op_result)
                    
                elif operation == "list":
                    directory_path = params.get("directory_path", ".")
                    logger.info(f"Listing directory: {directory_path}")
                    op_result = tool.list_directory(directory_path)
                    result = tool.summarize_results(op_result)
                    
                else:
                    logger.warning(f"Invalid file operation: {operation}")
                    return f"Error: Invalid file operation {operation}."
                    
            elif tool_name == "system_info":
                info_type = params.get("info_type", "all")
                logger.info(f"Getting system info: {info_type}")
                
                if info_type == "cpu":
                    sys_result = tool.get_cpu_info()
                elif info_type == "memory":
                    sys_result = tool.get_memory_info()
                elif info_type == "disk":
                    sys_result = tool.get_disk_info()
                elif info_type == "network":
                    sys_result = tool.get_network_info()
                else:
                    sys_result = tool.get_all_info()
                    
                result = tool.summarize_results(sys_result, info_type)
                    
            # Add handling for other tools as they are implemented
            
            # Log the tool call
            if hasattr(self, 'debug_tool'):
                self.debug_tool.log_call(tool_name, params, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            
            # Log the error
            if hasattr(self, 'debug_tool'):
                self.debug_tool.log_call(tool_name, params, f"ERROR: {str(e)}")
                
            return f"Error executing {tool_name}: {str(e)}"
    
    def debug_tool_call(self, tool_name: str, method_name: str, **params) -> str:
        """Debug a tool call.
        
        Args:
            tool_name: Name of the tool to debug
            method_name: Name of the method to call
            params: Parameters for the method
            
        Returns:
            Debug result as a string
        """
        if tool_name not in self.tools:
            return f"Error: Tool {tool_name} not found"
            
        tool = self.tools[tool_name]
        
        # Test the tool call
        test_result = self.debug_tool.test_tool(tool, method_name, **params)
        
        # Return the formatted result
        return self.debug_tool.summarize_results(test_result) 