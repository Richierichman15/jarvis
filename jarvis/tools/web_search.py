"""
Web search tool for Jarvis.
This tool allows Jarvis to search the web for information.
"""
import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSearch:
    """Web search tool using DuckDuckGo."""
    
    def __init__(self, max_results: int = 5):
        """Initialize the web search tool.
        
        Args:
            max_results: Maximum number of results to return
        """
        self.max_results = max_results
        self.search_engine = DDGS()
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the web for the given query.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        try:
            # Set a timeout to avoid hanging
            results = list(self.search_engine.text(query, max_results=self.max_results, timelimit='5'))
            logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return [{"title": "Error", "body": f"Failed to search: {str(e)}", "href": ""}]
    
    def summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """Summarize search results into a readable format.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted summary string
        """
        if not results:
            return "No results found."
            
        summary = "Web Search Results:\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            link = result.get("href", "")
            
            summary += f"{i}. {title}\n"
            summary += f"   {body}\n"
            summary += f"   URL: {link}\n\n"
            
        return summary 