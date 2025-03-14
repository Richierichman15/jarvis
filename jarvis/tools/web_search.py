"""
Web search tool for Jarvis.
This tool allows Jarvis to search the web for information.
"""
import logging
import time
import re
from typing import List, Dict, Any, Optional, Union
from duckduckgo_search import DDGS
import requests
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSearch:
    """Enhanced web search tool using multiple search engines and types."""
    
    def __init__(self, max_results: int = 5, timeout: int = 10, retries: int = 2):
        """Initialize the web search tool.
        
        Args:
            max_results: Maximum number of results to return
            timeout: Timeout in seconds for search requests
            retries: Number of retry attempts if a search fails
        """
        self.max_results = max_results
        self.timeout = timeout
        self.retries = retries
        self.search_engine = DDGS()
        self.last_search_time = None
        
        # Respect rate limits (1 second between searches)
        self.min_search_interval = 1.0
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limiting."""
        if self.last_search_time is not None:
            elapsed = time.time() - self.last_search_time
            if elapsed < self.min_search_interval:
                time.sleep(self.min_search_interval - elapsed)
        
        self.last_search_time = time.time()
    
    def search(self, query: str, search_type: str = "text") -> List[Dict[str, Any]]:
        """Search the web for the given query.
        
        Args:
            query: Search query
            search_type: Type of search to perform (text, news, images)
            
        Returns:
            List of search results
        """
        logger.info(f"Performing {search_type} search for: {query}")
        
        # Try multiple times in case of failure
        for attempt in range(self.retries + 1):
            try:
                self._wait_for_rate_limit()
                
                if search_type == "text":
                    results = list(self.search_engine.text(
                        query, 
                        max_results=self.max_results, 
                        timelimit=str(self.timeout)
                    ))
                elif search_type == "news":
                    results = list(self.search_engine.news(
                        query, 
                        max_results=self.max_results, 
                        timelimit=str(self.timeout)
                    ))
                elif search_type == "images":
                    results = list(self.search_engine.images(
                        query, 
                        max_results=self.max_results, 
                        timelimit=str(self.timeout)
                    ))
                else:
                    logger.warning(f"Unknown search type: {search_type}, falling back to text search")
                    results = list(self.search_engine.text(
                        query, 
                        max_results=self.max_results, 
                        timelimit=str(self.timeout)
                    ))
                
                if results:
                    logger.info(f"Found {len(results)} results for {search_type} search")
                    results = self._filter_results(results, search_type)
                    return results
                else:
                    logger.warning(f"No results found for {search_type} search on attempt {attempt+1}")
                    
                    # If we have no results but have more retries, try again after a short delay
                    if attempt < self.retries:
                        time.sleep(1)
                    else:
                        # If all attempts failed, try a more generic search as a last resort
                        if search_type != "text":
                            logger.info(f"Falling back to text search for: {query}")
                            return self.search(query, "text")
                            
            except Exception as e:
                logger.error(f"Search failed on attempt {attempt+1}: {str(e)}")
                
                # If we have retries left, wait and try again
                if attempt < self.retries:
                    time.sleep(1)
                else:
                    # All retries failed
                    return [{"title": "Error", "body": f"Failed to search: {str(e)}", "href": ""}]
                    
        # If we get here, all attempts failed
        return [{"title": "No Results", "body": "No search results found.", "href": ""}]
    
    def _filter_results(self, results: List[Dict[str, Any]], search_type: str) -> List[Dict[str, Any]]:
        """Filter results to remove low-quality or duplicate information.
        
        Args:
            results: Search results to filter
            search_type: Type of search performed
            
        Returns:
            Filtered search results
        """
        filtered_results = []
        seen_urls = set()
        seen_titles = set()
        
        for result in results:
            # Skip empty results
            if not result.get("title") or not result.get("body", ""):
                continue
                
            # Skip duplicate URLs or very similar titles
            url = result.get("href", "").lower()
            title = result.get("title", "").lower()
            
            # Skip if we've seen this URL already
            if url in seen_urls:
                continue
                
            # Skip if we've seen a very similar title
            if any(self._is_similar_text(title, seen) for seen in seen_titles):
                continue
                
            # For news, check if it has a recent date
            if search_type == "news" and "published" in result:
                try:
                    # Skip old news
                    published = result.get("published")
                    if self._is_too_old(published):
                        continue
                except:
                    # If we can't parse the date, keep the result
                    pass
            
            # Add to filtered results
            filtered_results.append(result)
            seen_urls.add(url)
            seen_titles.add(title)
            
            # Stop once we have enough filtered results
            if len(filtered_results) >= self.max_results:
                break
                
        return filtered_results
    
    def _is_similar_text(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two text strings are very similar.
        
        Args:
            text1: First text string
            text2: Second text string
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if texts are similar, False otherwise
        """
        # Simple character-based similarity
        if not text1 or not text2:
            return False
            
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
            
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity > threshold
    
    def _is_too_old(self, date_str: str, max_days: int = 30) -> bool:
        """Check if a date is too old.
        
        Args:
            date_str: Date string from search result
            max_days: Maximum age in days
            
        Returns:
            True if date is too old, False otherwise
        """
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d %b %Y", "%B %d, %Y", "%Y/%m/%d"]:
                try:
                    date = datetime.strptime(date_str, fmt)
                    cutoff_date = datetime.now() - timedelta(days=max_days)
                    return date < cutoff_date
                except ValueError:
                    continue
                    
            # If we couldn't parse the date, assume it's recent
            return False
        except:
            return False
    
    def multi_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Perform multiple types of searches for comprehensive results.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with results from different search types
        """
        results = {}
        
        # Check if it's a news query
        news_keywords = ["news", "latest", "recent", "today", "update", "breaking"]
        is_news_query = any(keyword in query.lower() for keyword in news_keywords)
        
        # Check if it's an image query
        image_keywords = ["image", "picture", "photo", "how does it look", "what does it look like"]
        is_image_query = any(keyword in query.lower() for keyword in image_keywords)
        
        # Prioritize search types based on query
        if is_news_query:
            # For news queries, try news search first, then text search
            results["news"] = self.search(query, "news")
            if not self._has_good_results(results["news"]):
                results["text"] = self.search(query, "text")
        elif is_image_query:
            # For image queries, try image search first
            results["images"] = self.search(query, "images")
            results["text"] = self.search(query, "text")
        else:
            # Default: just do text search
            results["text"] = self.search(query, "text")
            
        return results
    
    def _has_good_results(self, results: List[Dict[str, Any]]) -> bool:
        """Check if search results are good quality.
        
        Args:
            results: Search results to check
            
        Returns:
            True if results are good quality, False otherwise
        """
        # Minimum threshold for "good" results
        if not results:
            return False
            
        # Check for error results
        if len(results) == 1 and ("Error" in results[0].get("title", "") or "No Results" in results[0].get("title", "")):
            return False
            
        return len(results) >= 2  # At least 2 results
    
    def summarize_results(self, results: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]) -> str:
        """Summarize search results into a readable format.
        
        Args:
            results: Search results to summarize (list or dict with search types)
            
        Returns:
            Formatted summary string
        """
        # Handle both direct results list and multi-search results dict
        if isinstance(results, dict):
            # Multi-search results
            if not any(self._has_good_results(r) for r in results.values()):
                return "No relevant results found."
                
            summary = "Web Search Results:\n\n"
            
            # Add news results first if available
            if "news" in results and self._has_good_results(results["news"]):
                summary += "NEWS RESULTS:\n"
                summary += self._format_results(results["news"], "news")
                summary += "\n"
                
            # Add text results
            if "text" in results and self._has_good_results(results["text"]):
                if "news" in results and self._has_good_results(results["news"]):
                    summary += "ADDITIONAL INFORMATION:\n"
                summary += self._format_results(results["text"], "text")
                
            # Add image results as textual descriptions
            if "images" in results and self._has_good_results(results["images"]):
                summary += "\nIMAGE DESCRIPTIONS:\n"
                summary += self._format_results(results["images"], "images")
                
            return summary
        else:
            # Direct results list
            if not results:
                return "No results found."
                
            return self._format_results(results, "text")
    
    def _format_results(self, results: List[Dict[str, Any]], result_type: str) -> str:
        """Format specific result types.
        
        Args:
            results: List of search results
            result_type: Type of results (text, news, images)
            
        Returns:
            Formatted text
        """
        formatted = ""
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            
            if result_type == "news":
                body = result.get("body", "No description")
                link = result.get("href", "")
                published = result.get("published", "")
                source = result.get("source", "")
                
                formatted += f"{i}. {title}\n"
                if published:
                    formatted += f"   Published: {published}"
                    if source:
                        formatted += f" - Source: {source}"
                    formatted += "\n"
                formatted += f"   {body}\n"
                formatted += f"   URL: {link}\n\n"
                
            elif result_type == "images":
                image_url = result.get("image", "")
                source = result.get("source", "")
                description = result.get("title", "No description")
                
                formatted += f"{i}. {description}\n"
                if source:
                    formatted += f"   Source: {source}\n"
                formatted += f"   Image URL: {image_url}\n\n"
                
            else:  # text results
                body = result.get("body", "No description")
                link = result.get("href", "")
                
                formatted += f"{i}. {title}\n"
                formatted += f"   {body}\n"
                formatted += f"   URL: {link}\n\n"
                
        return formatted
        
    def detect_search_type(self, query: str) -> str:
        """Detect the appropriate search type based on the query.
        
        Args:
            query: User's search query
            
        Returns:
            Recommended search type
        """
        query_lower = query.lower()
        
        # Check for news-related queries
        news_patterns = [
            r"(news|headlines|latest|recent|update|breaking)\s+(about|on|regarding|of)",
            r"(what happened|what's happening|what is happening)",
            r"(today|yesterday|this week)'s (news|updates|events)",
        ]
        
        for pattern in news_patterns:
            if re.search(pattern, query_lower):
                return "news"
                
        # Check for image-related queries
        image_patterns = [
            r"(image|images|picture|pictures|photo|photos|photograph|photographs)\s+of",
            r"(what does|how does).+(look like)",
            r"(show|display).+(image|picture|photo)",
        ]
        
        for pattern in image_patterns:
            if re.search(pattern, query_lower):
                return "images"
                
        # Default to text search
        return "text" 