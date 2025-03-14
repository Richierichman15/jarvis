"""
Tool manager for Jarvis.
This module manages the available tools and their execution.
"""
import re
import logging
from typing import Dict, Any, List, Optional

from .web_search import WebSearch
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
            
        # Add more tools here as they are implemented
        
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
            # Add more tool descriptions as they are implemented
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
        
        # Check if the query matches any of these patterns
        all_patterns = []
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
            return tool.summarize_results(results)
            
        # Add handling for other tools as they are implemented
        
        return None 