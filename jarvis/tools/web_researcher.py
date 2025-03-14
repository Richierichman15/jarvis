"""
Web Researcher tool for Jarvis.
This tool provides advanced web research capabilities including web scraping,
API-based data retrieval, and intelligent research planning.
"""

import logging
import time
import re
import json
import requests
from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .web_search import WebSearch  # Import the existing web search tool
import regex as re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebResearcher:
    """Advanced web research tool with specialized data gathering capabilities."""
    
    def __init__(self, max_results: int = 8, timeout: int = 15, retries: int = 3):
        """Initialize the web researcher tool.
        
        Args:
            max_results: Maximum number of results to return
            timeout: Timeout in seconds for requests
            retries: Number of retry attempts if a request fails
        """
        self.max_results = max_results
        self.timeout = timeout
        self.retries = retries
        self.web_search = WebSearch(max_results=max_results, timeout=timeout, retries=retries)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.headers = {"User-Agent": self.user_agent}
        
        # List of supported APIs and their endpoints
        self.apis = {
            "crypto": {
                "coinbase": "https://api.coinbase.com/v2/prices/{currency}-USD/spot",
                "coingecko": "https://api.coingecko.com/api/v3/simple/price?ids={currency}&vs_currencies=usd",
            },
            "weather": {
                "openweathermap": "https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric",
            },
            "news": {
                "newsapi": "https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}",
            }
        }
        
        # Cache for API responses with TTL
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default TTL
        
    def research(self, query: str, research_type: str = "general") -> Dict[str, Any]:
        """Conduct web research based on the query and research type.
        
        Args:
            query: Research query or topic
            research_type: Type of research (general, crypto, news, products, jobs)
            
        Returns:
            Dictionary with research results
        """
        logger.info(f"Conducting {research_type} research for: {query}")
        
        # Determine the best research strategy
        if research_type == "crypto":
            return self.get_crypto_info(query)
        elif research_type == "news":
            return self.get_news(query)
        elif research_type == "products":
            return self.compare_products(query)
        elif research_type == "jobs":
            return self.search_jobs(query)
        else:
            # For general research, use enhanced web search
            return self.enhanced_search(query)
    
    def get_crypto_info(self, currency: str) -> Dict[str, Any]:
        """Get real-time cryptocurrency information.
        
        Args:
            currency: Name of the cryptocurrency (e.g., bitcoin, ethereum)
            
        Returns:
            Dictionary with cryptocurrency information
        """
        logger.info(f"Getting cryptocurrency info for: {currency}")
        
        # Normalize the currency name
        currency = currency.lower().strip()
        if currency == "btc":
            currency = "bitcoin"
        elif currency == "eth":
            currency = "ethereum"
        
        # Check cache first - reduced TTL to 30 seconds for more accuracy
        cache_key = f"crypto_{currency}"
        if cache_key in self.cache and (time.time() - self.cache[cache_key]["timestamp"]) < 30:
            logger.info(f"Using cached crypto data for {currency} (less than 30 seconds old)")
            return self.cache[cache_key]["data"]
        
        results = {
            "currency": currency,
            "prices": {},
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Enhanced browser-like headers to avoid being blocked
        enhanced_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # IMPROVEMENT 1: Direct scraping of Coindesk with improved selectors
        if currency == "bitcoin":
            try:
                logger.info("Attempting to directly scrape CoinDesk for real-time Bitcoin price")
                response = requests.get(
                    "https://www.coindesk.com/price/bitcoin/", 
                    headers=enhanced_headers, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Multiple selector attempts to handle website changes
                    price_selectors = [
                        "span[data-currency-price-usd]",  # Original selector
                        "div[class*='price-large']",      # Common price class pattern
                        "div.price-large",                # Alternative class
                        "span.currency-price",            # Another possible class
                        "div[class*='priceValue']",       # Common price value class
                        "div.priceValue"                  # Alternative price value class
                    ]
                    
                    price_element = None
                    
                    # Try each selector until we find one that works
                    for selector in price_selectors:
                        price_element = soup.select_one(selector)
                        if price_element:
                            logger.info(f"Found price element using selector: {selector}")
                            break
                    
                    if price_element:
                        try:
                            price_text = price_element.get_text().strip()
                            # Handle various price formats
                            price_text = price_text.replace('$', '').replace(',', '')
                            # Find first occurrence of a number
                            number_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
                            if number_match:
                                price = float(number_match.group(1))
                                results["prices"]["coindesk"] = price
                                results["sources"].append({
                                    "name": "CoinDesk",
                                    "url": "https://www.coindesk.com/price/bitcoin/",
                                    "timestamp": datetime.now().strftime("%H:%M:%S")
                                })
                                logger.info(f"Successfully scraped Bitcoin price from CoinDesk: ${price:,.2f}")
                            else:
                                logger.warning(f"Could not extract number from price text: {price_text}")
                        except (ValueError, AttributeError, re.error) as e:
                            logger.warning(f"Error parsing CoinDesk price: {str(e)}")
                    else:
                        # If all selectors fail, try a more brute-force approach
                        logger.info("All selectors failed, attempting pattern-based search")
                        # Look for text containing USD price patterns
                        price_pattern = re.compile(r'\$(\d{1,3},\d{3}(?:,\d{3})*(?:\.\d+)?)')
                        matches = price_pattern.findall(response.text)
                        if matches:
                            try:
                                price = float(matches[0].replace('$', '').replace(',', ''))
                                results["prices"]["coindesk"] = price
                                results["sources"].append({
                                    "name": "CoinDesk",
                                    "url": "https://www.coindesk.com/price/bitcoin/",
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "method": "pattern-match"
                                })
                                logger.info(f"Found Bitcoin price via pattern matching: ${price:,.2f}")
                            except (ValueError, IndexError, re.error) as e:
                                logger.warning(f"Error parsing pattern-matched price: {str(e)}")
                else:
                    logger.warning(f"Failed to fetch CoinDesk page: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Error scraping CoinDesk: {str(e)}")
        
        # IMPROVEMENT 2: Add CoinMarketCap as an additional source
        try:
            cmc_url = f"https://coinmarketcap.com/currencies/{currency}/"
            logger.info(f"Fetching price from CoinMarketCap at {cmc_url}")
            
            response = requests.get(cmc_url, headers=enhanced_headers, timeout=self.timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try multiple selectors for CoinMarketCap
                price_selectors = [
                    "div.priceValue span",
                    "span.sc-f70bb44c-0",
                    "div[class*='priceValue']",
                    "span.price"
                ]
                
                price_element = None
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        break
                
                if price_element:
                    try:
                        price_text = price_element.get_text().strip()
                        price_text = price_text.replace('$', '').replace(',', '')
                        price = float(price_text)
                        results["prices"]["coinmarketcap"] = price
                        results["sources"].append({
                            "name": "CoinMarketCap",
                            "url": cmc_url,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        logger.info(f"Successfully scraped {currency} price from CoinMarketCap: ${price:,.2f}")
                    except (ValueError, AttributeError, re.error) as e:
                        logger.warning(f"Error parsing CoinMarketCap price: {str(e)}")
                else:
                    # Pattern-based approach
                    price_pattern = re.compile(r'\$(\d{1,3},\d{3}(?:,\d{3})*(?:\.\d+)?)')
                    matches = price_pattern.findall(response.text)
                    if matches:
                        try:
                            price = float(matches[0].replace('$', '').replace(',', ''))
                            results["prices"]["coinmarketcap"] = price
                            results["sources"].append({
                                "name": "CoinMarketCap",
                                "url": cmc_url,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "method": "pattern-match"
                            })
                            logger.info(f"Found {currency} price via pattern matching on CMC: ${price:,.2f}")
                        except (ValueError, IndexError, re.error) as e:
                            logger.warning(f"Error parsing pattern-matched CMC price: {str(e)}")
        except Exception as e:
            logger.warning(f"Error scraping CoinMarketCap: {str(e)}")
        
        # Try CoinGecko API first (doesn't require API key)
        try:
            url = self.apis["crypto"]["coingecko"].format(currency=currency)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if currency in data and "usd" in data[currency]:
                    price = data[currency]["usd"]
                    results["prices"]["coingecko"] = price
                    results["sources"].append({
                        "name": "CoinGecko",
                        "url": f"https://www.coingecko.com/en/coins/{currency}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    logger.info(f"Successfully fetched {currency} price from CoinGecko API: ${price:,.2f}")
        except Exception as e:
            logger.warning(f"Error fetching from CoinGecko: {str(e)}")
        
        # Try Coinbase API as backup
        try:
            url = self.apis["crypto"]["coinbase"].format(currency=currency)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "amount" in data["data"]:
                    price = float(data["data"]["amount"])
                    results["prices"]["coinbase"] = price
                    results["sources"].append({
                        "name": "Coinbase",
                        "url": f"https://www.coinbase.com/price/{currency}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    logger.info(f"Successfully fetched {currency} price from Coinbase API: ${price:,.2f}")
        except Exception as e:
            logger.warning(f"Error fetching from Coinbase: {str(e)}")
        
        # Calculate average price if we have any results
        if results["prices"]:
            total = sum(results["prices"].values())
            count = len(results["prices"])
            results["average_price"] = round(total / count, 2)
            
            # New: Add min and max values
            results["min_price"] = min(results["prices"].values())
            results["max_price"] = max(results["prices"].values())
            results["price_range"] = f"${results['min_price']:,.2f} - ${results['max_price']:,.2f}"
            
            # Store in cache
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": results
            }
            
            logger.info(f"Found cryptocurrency prices from {count} sources. Average: ${results['average_price']:,.2f}")
            return results
        else:
            # Fallback to web search if APIs fail
            logger.info("API and scraping requests failed, falling back to web search")
            search_results = self.web_search.search(f"{currency} price usd current", "text")
            
            # Format search results
            results["fallback"] = True
            results["search_results"] = search_results
            
            # Try to extract price from search results
            for result in search_results:
                # Look for price patterns in the result text
                body = result.get("body", "")
                title = result.get("title", "")
                full_text = title + " " + body
                
                # Match price patterns like $82,000 or $82,000.00
                price_matches = re.findall(r'\$(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+,\d+(?:\.\d+)?|\d+(?:\.\d+)?)', full_text)
                
                if price_matches:
                    try:
                        # Use the first match
                        price_text = price_matches[0].replace(',', '')
                        price = float(price_text)
                        
                        # Only add reasonable prices (filter out very low values that might be wrong)
                        if currency == "bitcoin" and 10000 <= price <= 200000:
                            results["extracted_price"] = price
                            results["price_source"] = result.get("title", "Search Result")
                            results["source_url"] = result.get("href", "")
                            break
                        elif price > 0:  # For other currencies
                            results["extracted_price"] = price
                            results["price_source"] = result.get("title", "Search Result")
                            results["source_url"] = result.get("href", "")
                            break
                    except (ValueError, IndexError):
                        continue
            
            return results
    
    def get_news(self, query: str, days: int = 1) -> Dict[str, Any]:
        """Get latest news on a topic.
        
        Args:
            query: News topic or search query
            days: How many days back to search
            
        Returns:
            Dictionary with news articles
        """
        logger.info(f"Getting news for: {query} (last {days} days)")
        
        # Check cache first
        cache_key = f"news_{query}_{days}"
        if cache_key in self.cache and (time.time() - self.cache[cache_key]["timestamp"]) < 1800:  # 30 minutes TTL for news
            logger.info(f"Using cached news data for {query}")
            return self.cache[cache_key]["data"]
        
        # Use the news search from WebSearch
        search_results = self.web_search.search(query, "news")
        
        # Format the results
        results = {
            "topic": query,
            "articles": search_results,
            "sources": self._extract_news_sources(search_results),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in cache
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": results
        }
        
        return results
    
    def _extract_news_sources(self, news_results: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from news results.
        
        Args:
            news_results: List of news article results
            
        Returns:
            List of unique sources
        """
        sources = []
        for article in news_results:
            if "source" in article and article["source"] not in sources:
                sources.append(article["source"])
        return sources
    
    def compare_products(self, query: str) -> Dict[str, Any]:
        """Compare products across different retailers.
        
        Args:
            query: Product search query
            
        Returns:
            Dictionary with product comparison results
        """
        logger.info(f"Comparing products for: {query}")
        
        # This would ideally use shopping APIs, but for now we'll simulate with web search
        search_results = self.web_search.search(f"{query} price compare", "text")
        
        # Extract and format the results
        products = []
        for result in search_results:
            # Extract price using regex if possible
            price_match = re.search(r'\$(\d+(?:\.\d+)?)', result.get("body", ""))
            price = float(price_match.group(1)) if price_match else None
            
            product = {
                "title": result.get("title", "Unknown Product"),
                "description": result.get("body", ""),
                "price": price,
                "retailer": self._extract_domain(result.get("href", "")),
                "url": result.get("href", "")
            }
            products.append(product)
        
        # Sort by price if available
        products_with_price = [p for p in products if p["price"] is not None]
        if products_with_price:
            products_with_price.sort(key=lambda x: x["price"])
            
        return {
            "query": query,
            "products": products_with_price or products,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        if not url:
            return "Unknown"
        
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        return "Unknown"
    
    def search_jobs(self, query: str) -> Dict[str, Any]:
        """Search for job listings.
        
        Args:
            query: Job search query
            
        Returns:
            Dictionary with job listings
        """
        logger.info(f"Searching jobs for: {query}")
        
        # For now, we'll simulate this with web search
        search_results = self.web_search.search(f"{query} jobs", "text")
        
        # Format the results
        jobs = []
        for result in search_results:
            job = {
                "title": result.get("title", "Unknown Position"),
                "description": result.get("body", ""),
                "company": self._extract_domain(result.get("href", "")),
                "url": result.get("href", "")
            }
            jobs.append(job)
        
        return {
            "query": query,
            "listings": jobs,
            "timestamp": datetime.now().isoformat()
        }
    
    def enhanced_search(self, query: str) -> Dict[str, Any]:
        """Perform an enhanced web search with deeper result analysis.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with enhanced search results
        """
        logger.info(f"Enhanced search for: {query}")
        
        # Get regular search results
        search_results = self.web_search.search(query, "text")
        
        # Add domain credibility assessment
        for result in search_results:
            result["domain"] = self._extract_domain(result.get("href", ""))
            result["credibility"] = self._assess_domain_credibility(result["domain"])
        
        # Sort results by credibility
        search_results.sort(key=lambda x: x.get("credibility", 0), reverse=True)
        
        return {
            "query": query,
            "results": search_results,
            "key_insights": self._extract_key_insights(search_results),
            "timestamp": datetime.now().isoformat()
        }
    
    def _assess_domain_credibility(self, domain: str) -> int:
        """Assess the credibility of a domain on a scale of 1-10.
        
        Args:
            domain: Domain name to assess
            
        Returns:
            Credibility score (1-10)
        """
        # This is a simplified version - would be more sophisticated in reality
        high_credibility_domains = [
            "wikipedia.org", "github.com", "edu", "gov", 
            "nytimes.com", "bbc.com", "reuters.com", "bloomberg.com",
            "nature.com", "science.org", "ieee.org", "acm.org"
        ]
        
        medium_credibility_domains = [
            "medium.com", "forbes.com", "cnn.com", "techcrunch.com",
            "wired.com", "zdnet.com", "cnet.com", "theverge.com"
        ]
        
        # Check for high credibility domains
        for high_domain in high_credibility_domains:
            if high_domain in domain:
                return 10
        
        # Check for medium credibility domains
        for medium_domain in medium_credibility_domains:
            if medium_domain in domain:
                return 7
        
        # Default credibility for unknown domains
        return 5
    
    def _extract_key_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from search results.
        
        Args:
            results: List of search results
            
        Returns:
            List of key insights
        """
        insights = []
        
        # For now, just extract from the top 3 most credible results
        for result in results[:3]:
            body = result.get("body", "")
            if body:
                # Split into sentences and take the first one as a key insight
                sentences = re.split(r'[.!?]', body)
                for sentence in sentences:
                    # Clean the sentence
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 30 and clean_sentence not in insights:
                        insights.append(clean_sentence)
                        break
        
        return insights
    
    def format_research_results(self, results: Dict[str, Any], research_type: str) -> str:
        """Format research results for display.
        
        Args:
            results: Research results to format
            research_type: Type of research (general, crypto, news, products, jobs)
            
        Returns:
            Formatted results as a string
        """
        formatted = f"## {research_type.capitalize()} Research Results\n\n"
        
        if research_type == "crypto":
            formatted += f"### {results['currency'].upper()} Price Information\n\n"
            
            # Add fetch time for transparency
            if "fetch_time" in results:
                formatted += f"*Prices fetched at: {results['fetch_time']}*\n\n"
            
            if "average_price" in results:
                formatted += f"**Average Price:** ${results['average_price']:,.2f} USD\n\n"
                
                # Add price range if available
                if "price_range" in results:
                    formatted += f"**Price Range:** {results['price_range']} USD\n\n"
            
            formatted += "**Prices by Source:**\n\n"
            for source, price in results.get("prices", {}).items():
                formatted += f"- {source.capitalize()}: ${price:,.2f} USD\n"
            
            formatted += "\n**Sources:**\n\n"
            for source in results.get("sources", []):
                timestamp = source.get("timestamp", "")
                timestamp_str = f" (at {timestamp})" if timestamp else ""
                formatted += f"- [{source['name']}{timestamp_str}]({source['url']})\n"
                
            # Handle fallback case
            if results.get("fallback", False) and "extracted_price" in results:
                formatted += f"\n**Extracted Price:** ${results['extracted_price']:,.2f} USD\n"
                formatted += f"**Source:** {results['price_source']}\n"
                if "source_url" in results and results["source_url"]:
                    formatted += f"**URL:** {results['source_url']}\n"
                
        elif research_type == "news":
            formatted += f"### Latest News on {results['topic']}\n\n"
            
            for i, article in enumerate(results.get("articles", []), 1):
                title = article.get("title", "No title")
                source = article.get("source", "Unknown source")
                url = article.get("href", "")
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   Source: {source}\n"
                if url:
                    formatted += f"   [Read more]({url})\n"
                formatted += "\n"
                
        elif research_type == "products":
            formatted += f"### Product Comparison for '{results['query']}'\n\n"
            
            for i, product in enumerate(results.get("products", []), 1):
                title = product.get("title", "Unknown product")
                price = f"${product.get('price'):,.2f}" if product.get("price") else "Price not found"
                retailer = product.get("retailer", "Unknown retailer")
                url = product.get("url", "")
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   Price: {price}\n"
                formatted += f"   Retailer: {retailer}\n"
                if url:
                    formatted += f"   [View product]({url})\n"
                formatted += "\n"
                
        elif research_type == "jobs":
            formatted += f"### Job Listings for '{results['query']}'\n\n"
            
            for i, job in enumerate(results.get("listings", []), 1):
                title = job.get("title", "Unknown position")
                company = job.get("company", "Unknown company")
                url = job.get("url", "")
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   Company: {company}\n"
                if url:
                    formatted += f"   [View job listing]({url})\n"
                formatted += "\n"
                
        else:  # general research
            formatted += f"### Information on '{results['query']}'\n\n"
            
            if "key_insights" in results and results["key_insights"]:
                formatted += "**Key Insights:**\n\n"
                for insight in results["key_insights"]:
                    formatted += f"- {insight}\n"
                formatted += "\n"
            
            formatted += "**Sources:**\n\n"
            for i, result in enumerate(results.get("results", []), 1):
                title = result.get("title", "No title")
                url = result.get("href", "")
                credibility = result.get("credibility", 0)
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   Credibility: {credibility}/10\n"
                if url:
                    formatted += f"   [Read more]({url})\n"
                formatted += "\n"
                
        # Add timestamp
        if "timestamp" in results:
            formatted += f"\n*Research conducted at: {results['timestamp']}*"
            
        return formatted

# Create a singleton instance
web_researcher = WebResearcher() 