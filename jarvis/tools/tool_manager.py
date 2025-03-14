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
from .code_editor import CodeEditorTool
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
            
        # Initialize code editor tool if enabled
        if "code_editor" in AVAILABLE_TOOLS:
            self.tools["code_editor"] = CodeEditorTool()
            logger.info("Code editor tool initialized")
            
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
            "code_editor": "Edit, highlight, and execute code in various programming languages"
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
        
        # Code editor patterns
        code_patterns = [
            r"(edit|create|modify|update)\s+(the\s+)?(code|file|program|script)\s+([^\s]+)",
            r"(run|execute|test)\s+(the\s+)?(code|program|script|function)\s+([^\s]+)?",
            r"(highlight|format|indent|beautify|pretty print|analyze)\s+(the\s+)?(code|program|script)",
            r"(diff|compare|find differences)\s+(?:between\s+)?([^\s]+)\s+(?:and\s+)?([^\s]+)",
            r"(undo|revert|rollback)\s+(the\s+)?(changes|edits|modifications)",
        ]
        
        # Check if the query matches any web search patterns
        if "web_search" in self.tools:
            all_patterns = weather_patterns + news_patterns + info_patterns
            
            for pattern in all_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    logger.info(f"Detected web search intent in query: {query}")
                    
                    # Detect the best search type for this query
                    web_search_tool = self.tools["web_search"]
                    search_type = web_search_tool.detect_search_type(query)
                    
                    tool_calls.append({
                        "tool": "web_search",
                        "params": {
                            "query": query.strip(),
                            "search_type": search_type,
                            "multi_search": True
                        },
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
                    
        # Check if the query matches any code editor patterns
        if "code_editor" in self.tools and not tool_calls:
            for pattern in code_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    action = match.group(1).lower()
                    
                    if action in ["edit", "create", "modify", "update"]:
                        # Extract the file path
                        target = match.group(4) if len(match.groups()) >= 4 else ""
                        logger.info(f"Detected code edit intent in query: {query}")
                        tool_calls.append({
                            "tool": "code_editor",
                            "params": {"operation": "edit", "file_path": target},
                            "confidence": 0.9
                        })
                        break
                    elif action in ["run", "execute", "test"]:
                        # Extract the file path or directly execute code
                        target = match.group(4) if len(match.groups()) >= 4 else ""
                        logger.info(f"Detected code execution intent in query: {query}")
                        tool_calls.append({
                            "tool": "code_editor",
                            "params": {"operation": "execute", "file_path": target},
                            "confidence": 0.9
                        })
                        break
                    elif action in ["highlight", "format", "indent", "beautify", "pretty print", "analyze"]:
                        logger.info(f"Detected code highlight intent in query: {query}")
                        tool_calls.append({
                            "tool": "code_editor",
                            "params": {"operation": "highlight"},
                            "confidence": 0.8
                        })
                        break
                    elif action in ["diff", "compare", "find differences"]:
                        # Extract the two files to compare
                        file1 = match.group(2) if len(match.groups()) >= 2 else ""
                        file2 = match.group(3) if len(match.groups()) >= 3 else ""
                        logger.info(f"Detected diff intent in query: {query}")
                        tool_calls.append({
                            "tool": "code_editor",
                            "params": {"operation": "diff", "file1": file1, "file2": file2},
                            "confidence": 0.9
                        })
                        break
                    elif action in ["undo", "revert", "rollback"]:
                        logger.info(f"Detected undo intent in query: {query}")
                        tool_calls.append({
                            "tool": "code_editor",
                            "params": {"operation": "undo"},
                            "confidence": 0.9
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
                
                # Check if we should do a multi-search
                multi_search = params.get("multi_search", False)
                search_type = params.get("search_type", "text")
                
                web_tool = self.tools["web_search"]
                logger.info(f"Executing web search with query: {query}")
                
                if multi_search:
                    # Perform multiple search types based on query
                    results = web_tool.multi_search(query)
                else:
                    # Perform a single search type
                    results = web_tool.search(query, search_type)
                    
                result = web_tool.summarize_results(results)
                
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
                
            elif tool_name == "code_editor":
                operation = params.get("operation")
                
                if operation == "edit":
                    file_path = params.get("file_path")
                    content = params.get("content")
                    
                    if not file_path:
                        logger.warning("No file path provided for code edit operation")
                        return "Error: No file path provided for code edit operation."
                    
                    if content:
                        # Write the file with new content
                        logger.info(f"Editing code in file: {file_path}")
                        op_result = tool.write_file(file_path, content)
                    else:
                        # Just read the file for editing
                        logger.info(f"Opening file for editing: {file_path}")
                        op_result = tool.read_file(file_path)
                        
                    result = tool.summarize_results(op_result)
                
                elif operation == "execute":
                    code = params.get("code")
                    language = params.get("language", "python")
                    file_path = params.get("file_path")
                    
                    if file_path and not code:
                        # Read code from file
                        file_result = tool.read_file(file_path)
                        if file_result["success"]:
                            code = file_result["content"]
                            # Try to detect language from file extension
                            if "." in file_path:
                                ext = file_path.split(".")[-1].lower()
                                if ext in ["py", "pyw"]:
                                    language = "python"
                                elif ext in ["js"]:
                                    language = "javascript"
                                elif ext in ["sh", "bash"]:
                                    language = "bash"
                                # Add more languages as needed
                    
                    if not code:
                        logger.warning("No code provided for execution")
                        return "Error: No code provided for execution."
                        
                    logger.info(f"Executing {language} code")
                    op_result = tool.execute_code(code, language)
                    result = tool.summarize_results(op_result)
                
                elif operation == "highlight":
                    code = params.get("code")
                    language = params.get("language")
                    file_path = params.get("file_path")
                    
                    if file_path and not code:
                        # Read code from file
                        file_result = tool.read_file(file_path)
                        if file_result["success"]:
                            # Already highlighted in read_file
                            return tool.summarize_results(file_result)
                    
                    if not code:
                        logger.warning("No code provided for highlighting")
                        return "Error: No code provided for highlighting."
                        
                    logger.info("Highlighting code")
                    highlighted = tool._highlight_code(code, file_path)
                    result = tool.summarize_results({
                        "success": True,
                        "content": code,
                        "highlighted": highlighted,
                        "file_path": file_path
                    })
                
                elif operation == "diff":
                    file1 = params.get("file1")
                    file2 = params.get("file2")
                    content1 = params.get("content1")
                    content2 = params.get("content2")
                    
                    if file1 and not content1:
                        # Read content from file1
                        file_result = tool.read_file(file1)
                        if file_result["success"]:
                            content1 = file_result["content"]
                    
                    if file2 and not content2:
                        # Read content from file2
                        file_result = tool.read_file(file2)
                        if file_result["success"]:
                            content2 = file_result["content"]
                    
                    if not content1 or not content2:
                        logger.warning("Missing content for diff operation")
                        return "Error: Missing content for diff operation."
                        
                    logger.info(f"Comparing files: {file1} and {file2}")
                    diff_result = tool.diff(content1, content2)
                    result = f"Diff between {file1 or 'first content'} and {file2 or 'second content'}:\n\n```diff\n{diff_result}\n```"
                
                elif operation == "undo":
                    logger.info("Undoing last change")
                    op_result = tool.undo()
                    result = tool.summarize_results(op_result)
                
                else:
                    logger.warning(f"Invalid code editor operation: {operation}")
                    return f"Error: Invalid code editor operation {operation}."
            
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