#!/usr/bin/env python3
"""
ResearchAgent - Specialized agent for news scanning and web research

This agent handles all research-related tasks including news scanning,
web search, information gathering, and content analysis.
"""

import asyncio
import logging
import aiohttp
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Load DATA_PATH from environment
DATA_PATH = os.getenv("DATA_PATH", "app/data")

try:
    from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from jarvis.agents.agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """Specialized agent for research operations."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="ResearchAgent",
            capabilities=[AgentCapability.RESEARCH],
            version="1.0.0",
            **kwargs
        )
        
        # Research-specific configuration
        self.research_config = {
            "max_search_results": 10,
            "news_sources": [
                "https://newsapi.org",
                "https://api.nytimes.com",
                "https://api.guardianapis.com"
            ],
            "search_engines": [
                "https://www.googleapis.com/customsearch/v1",
                "https://api.bing.microsoft.com/v7.0/search"
            ],
            "cache_duration": 300,  # 5 minutes
            "rate_limit_delay": 1.0  # seconds between requests
        }
        
        # Research state
        self.news_cache = {}
        self.search_cache = {}
        self.research_history = []
        self.active_searches = {}
        
        # HTTP session for web requests
        self.http_session = None
        
        self.logger = logging.getLogger("agent.research")
    
    async def start(self, redis_comm=None, agent_manager=None):
        """Start the agent with startup logging."""
        # Log startup information
        print(f"[ResearchAgent] CWD: {os.getcwd()}")
        print(f"[ResearchAgent] DATA_PATH: {DATA_PATH}")
        
        # Call parent start method
        await super().start(redis_comm, agent_manager)
    
    def _register_task_handlers(self):
        """Register research task handlers."""
        self.register_task_handler("scan_news", self._handle_scan_news)
        self.register_task_handler("web_search", self._handle_web_search)
        self.register_task_handler("search_topic", self._handle_search_topic)
        self.register_task_handler("get_news_article", self._handle_get_news_article)
        self.register_task_handler("analyze_content", self._handle_analyze_content)
        self.register_task_handler("summarize_article", self._handle_summarize_article)
        self.register_task_handler("get_trending_topics", self._handle_get_trending_topics)
        self.register_task_handler("research_company", self._handle_research_company)
        self.register_task_handler("get_market_news", self._handle_get_market_news)
        self.register_task_handler("get_tech_news", self._handle_get_tech_news)
        self.register_task_handler("get_crypto_news", self._handle_get_crypto_news)
        self.register_task_handler("fact_check", self._handle_fact_check)
        self.register_task_handler("get_research_history", self._handle_get_research_history)
        self.register_task_handler("save_research", self._handle_save_research)
        self.register_task_handler("get_saved_research", self._handle_get_saved_research)
    
    async def _initialize(self):
        """Initialize research-specific resources."""
        try:
            # Initialize HTTP session
            await self._initialize_http_session()
            
            # Load research configuration
            await self._load_research_config()
            
            # Initialize research cache
            await self._initialize_research_cache()
            
            self.logger.info("✅ ResearchAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize ResearchAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup research resources."""
        try:
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
            
            # Save research cache
            await self._save_research_cache()
            
            self.logger.info("✅ ResearchAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during ResearchAgent cleanup: {e}")
    
    async def _initialize_http_session(self):
        """Initialize HTTP session for web requests."""
        self.logger.info("🌐 Initializing HTTP session...")
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("✅ HTTP session initialized")
    
    async def _load_research_config(self):
        """Load research configuration."""
        self.logger.info("📋 Loading research configuration...")
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info("✅ Research configuration loaded")
    
    async def _initialize_research_cache(self):
        """Initialize research cache."""
        self.logger.info("💾 Initializing research cache...")
        
        # Sample cached data
        self.news_cache = {
            "last_updated": datetime.now().isoformat(),
            "articles": []
        }
        
        self.search_cache = {}
        
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("✅ Research cache initialized")
    
    async def _save_research_cache(self):
        """Save research cache to persistent storage."""
        self.logger.info("💾 Saving research cache...")
        await asyncio.sleep(0.1)  # Simulate saving time
        self.logger.info("✅ Research cache saved")
    
    async def _make_web_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a web request with error handling."""
        try:
            async with self.http_session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Error making request to {url}: {e}")
            return {"error": str(e)}
    
    async def _call_mcp_server(self, tool_name: str, args: dict = None, server: str = "search") -> dict:
        """Helper method to call MCP server tools."""
        if args is None:
            args = {}
        
        self.logger.info(f"🌐 Making HTTP request to MCP server: {tool_name} on {server}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:3012/run-tool",
                json={"tool": tool_name, "args": args, "server": server},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                self.logger.info(f"📡 HTTP response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"📦 Response data: {data}")
                    if data.get('ok'):
                        result = data.get('result', {})
                        self.logger.info(f"✅ MCP server returned: {result}")
                        return result
                    else:
                        error_msg = f"MCP server error: {data.get('detail', 'Unknown error')}"
                        self.logger.error(f"❌ {error_msg}")
                        raise Exception(error_msg)
                else:
                    error_msg = f"HTTP error: {response.status}"
                    self.logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)

    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle research tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown research task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling research task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_scan_news(self, task: TaskRequest) -> TaskResponse:
        """Handle news scanning request."""
        try:
            category = task.parameters.get("category", "general")
            limit = task.parameters.get("limit", 10)
            sources = task.parameters.get("sources", [])
            
            self.logger.info(f"🔍 Calling MCP server for web.search...")
            # Call the real MCP server for news scanning
            args = {
                "query": category
            }
            result = await self._call_mcp_server("web.search", args, "search")
            self.logger.info(f"📊 Received news data: {result}")
            
            # Add to research history
            self.research_history.append({
                "task_type": "scan_news",
                "query": category,
                "results_count": len(result.get("articles", [])),
                "timestamp": datetime.now().isoformat()
            })
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_web_search(self, task: TaskRequest) -> TaskResponse:
        """Handle web search request."""
        try:
            query = task.parameters.get("query", "")
            limit = task.parameters.get("limit", 10)
            search_engine = task.parameters.get("search_engine", "google")
            
            if not query:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Search query is required"
                )
            
            # Check cache first
            cache_key = f"search_{query}_{limit}_{search_engine}"
            if cache_key in self.search_cache:
                cached_data = self.search_cache[cache_key]
                if datetime.fromisoformat(cached_data["timestamp"]) > datetime.now() - timedelta(seconds=self.research_config["cache_duration"]):
                    return TaskResponse(
                        task_id=task.task_id,
                        agent_id=self.agent_id,
                        success=True,
                        result=cached_data["data"]
                    )
            
            # Simulate web search (in reality, this would call search APIs)
            search_results = [
                {
                    "title": f"Search Result 1 for '{query}'",
                    "url": "https://example.com/result1",
                    "snippet": f"This is a relevant result about {query} with detailed information.",
                    "rank": 1,
                    "source": "Example.com"
                },
                {
                    "title": f"Search Result 2 for '{query}'",
                    "url": "https://example.com/result2",
                    "snippet": f"Another comprehensive resource about {query} with expert insights.",
                    "rank": 2,
                    "source": "ExpertSite.com"
                },
                {
                    "title": f"Search Result 3 for '{query}'",
                    "url": "https://example.com/result3",
                    "snippet": f"Latest developments and news about {query} from reliable sources.",
                    "rank": 3,
                    "source": "NewsSite.com"
                }
            ]
            
            # Limit results
            search_results = search_results[:limit]
            
            result = {
                "query": query,
                "results": search_results,
                "total_results": len(search_results),
                "search_engine": search_engine,
                "searched_at": datetime.now().isoformat()
            }
            
            # Cache the result
            self.search_cache[cache_key] = {
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
            
            # Add to research history
            self.research_history.append({
                "task_type": "web_search",
                "query": query,
                "results_count": len(search_results),
                "timestamp": datetime.now().isoformat()
            })
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_search_topic(self, task: TaskRequest) -> TaskResponse:
        """Handle comprehensive topic search request."""
        try:
            topic = task.parameters.get("topic", "")
            depth = task.parameters.get("depth", "basic")  # basic, intermediate, deep
            
            if not topic:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Topic is required"
                )
            
            # Perform comprehensive search
            search_results = []
            
            # News search
            news_task = TaskRequest(
                task_id=f"news_{task.task_id}",
                agent_id=self.agent_id,
                capability=AgentCapability.RESEARCH,
                task_type="scan_news",
                parameters={"category": "general", "limit": 5}
            )
            news_response = await self._handle_scan_news(news_task)
            if news_response.success:
                search_results.extend(news_response.result.get("articles", []))
            
            # Web search
            web_task = TaskRequest(
                task_id=f"web_{task.task_id}",
                agent_id=self.agent_id,
                capability=AgentCapability.RESEARCH,
                task_type="web_search",
                parameters={"query": topic, "limit": 5}
            )
            web_response = await self._handle_web_search(web_task)
            if web_response.success:
                search_results.extend(web_response.result.get("results", []))
            
            # Analyze and summarize
            analysis = {
                "topic": topic,
                "search_depth": depth,
                "total_sources": len(search_results),
                "key_findings": [
                    f"Multiple sources discuss {topic}",
                    f"Recent developments in {topic} field",
                    f"Expert opinions on {topic} trends"
                ],
                "confidence_score": 0.85,
                "last_updated": datetime.now().isoformat()
            }
            
            result = {
                "topic": topic,
                "analysis": analysis,
                "sources": search_results,
                "search_completed_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_news_article(self, task: TaskRequest) -> TaskResponse:
        """Handle get news article request."""
        try:
            article_url = task.parameters.get("url")
            article_id = task.parameters.get("article_id")
            
            if not article_url and not article_id:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Article URL or ID is required"
                )
            
            # Simulate article retrieval (in reality, this would fetch the actual article)
            article_data = {
                "id": article_id or "article_001",
                "url": article_url or "https://example.com/article",
                "title": "Sample News Article",
                "content": "This is the full content of the news article with detailed information about the topic. It includes multiple paragraphs with comprehensive coverage of the subject matter.",
                "author": "John Doe",
                "published_at": datetime.now().isoformat(),
                "word_count": 500,
                "reading_time": "2 minutes",
                "tags": ["news", "technology", "analysis"],
                "sentiment": "neutral",
                "summary": "Brief summary of the article content"
            }
            
            result = {
                "article": article_data,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_analyze_content(self, task: TaskRequest) -> TaskResponse:
        """Handle content analysis request."""
        try:
            content = task.parameters.get("content", "")
            analysis_type = task.parameters.get("analysis_type", "general")
            
            if not content:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Content is required for analysis"
                )
            
            # Simulate content analysis
            analysis = {
                "content_length": len(content),
                "word_count": len(content.split()),
                "sentiment": "positive" if "good" in content.lower() else "neutral",
                "key_topics": ["technology", "innovation", "development"],
                "language": "english",
                "readability_score": 75,
                "analysis_type": analysis_type,
                "confidence": 0.8,
                "analyzed_at": datetime.now().isoformat()
            }
            
            result = {
                "analysis": analysis,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_summarize_article(self, task: TaskRequest) -> TaskResponse:
        """Handle article summarization request."""
        try:
            article_content = task.parameters.get("content", "")
            summary_length = task.parameters.get("length", "medium")  # short, medium, long
            
            if not article_content:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Article content is required for summarization"
                )
            
            # Simulate article summarization
            summary_lengths = {
                "short": 50,
                "medium": 150,
                "long": 300
            }
            
            target_length = summary_lengths.get(summary_length, 150)
            
            summary = f"This is a {summary_length} summary of the article content. It covers the main points and key findings discussed in the original text. The summary provides a concise overview while maintaining the essential information."
            
            result = {
                "summary": summary,
                "original_length": len(article_content),
                "summary_length": len(summary),
                "compression_ratio": round(len(summary) / len(article_content), 2),
                "summary_type": summary_length,
                "summarized_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_trending_topics(self, task: TaskRequest) -> TaskResponse:
        """Handle get trending topics request."""
        try:
            category = task.parameters.get("category", "general")
            time_period = task.parameters.get("time_period", "24h")  # 1h, 24h, 7d, 30d
            
            # Simulate trending topics
            trending_topics = [
                {
                    "topic": "Artificial Intelligence",
                    "trend_score": 95,
                    "mentions": 15000,
                    "growth_rate": 25.5,
                    "category": "technology"
                },
                {
                    "topic": "Cryptocurrency",
                    "trend_score": 88,
                    "mentions": 12000,
                    "growth_rate": 18.2,
                    "category": "finance"
                },
                {
                    "topic": "Climate Change",
                    "trend_score": 82,
                    "mentions": 9500,
                    "growth_rate": 12.8,
                    "category": "environment"
                },
                {
                    "topic": "Space Exploration",
                    "trend_score": 75,
                    "mentions": 7800,
                    "growth_rate": 8.5,
                    "category": "science"
                }
            ]
            
            # Filter by category if specified
            if category != "general":
                trending_topics = [topic for topic in trending_topics if topic["category"] == category]
            
            result = {
                "trending_topics": trending_topics,
                "category": category,
                "time_period": time_period,
                "total_topics": len(trending_topics),
                "generated_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_research_company(self, task: TaskRequest) -> TaskResponse:
        """Handle company research request."""
        try:
            company_name = task.parameters.get("company_name", "")
            research_depth = task.parameters.get("depth", "basic")
            
            if not company_name:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Company name is required"
                )
            
            # Simulate company research
            company_data = {
                "name": company_name,
                "industry": "Technology",
                "founded": "2010",
                "headquarters": "San Francisco, CA",
                "employees": "10,000+",
                "revenue": "$1B+",
                "description": f"{company_name} is a leading technology company specializing in innovative solutions.",
                "key_products": ["Product A", "Product B", "Product C"],
                "recent_news": [
                    f"{company_name} announces new product launch",
                    f"{company_name} reports strong quarterly earnings",
                    f"{company_name} expands international operations"
                ],
                "stock_info": {
                    "symbol": "COMP",
                    "price": 150.25,
                    "change": 2.5,
                    "change_percent": 1.69
                },
                "research_depth": research_depth,
                "last_updated": datetime.now().isoformat()
            }
            
            result = {
                "company": company_data,
                "research_completed_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_market_news(self, task: TaskRequest) -> TaskResponse:
        """Handle market news request."""
        try:
            market = task.parameters.get("market", "general")  # stocks, crypto, forex, commodities
            limit = task.parameters.get("limit", 10)
            
            # Simulate market news
            market_news = [
                {
                    "title": "Stock Market Shows Strong Performance",
                    "summary": "Major indices reach new highs amid positive economic indicators",
                    "market": "stocks",
                    "impact": "positive",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Cryptocurrency Market Volatility Continues",
                    "summary": "Bitcoin and Ethereum show mixed signals as market adjusts",
                    "market": "crypto",
                    "impact": "neutral",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Oil Prices Rise on Supply Concerns",
                    "summary": "Crude oil futures increase due to geopolitical tensions",
                    "market": "commodities",
                    "impact": "positive",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            # Filter by market if specified
            if market != "general":
                market_news = [news for news in market_news if news["market"] == market]
            
            result = {
                "market_news": market_news[:limit],
                "market": market,
                "total_articles": len(market_news),
                "scanned_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_tech_news(self, task: TaskRequest) -> TaskResponse:
        """Handle tech news request."""
        try:
            limit = task.parameters.get("limit", 10)
            
            # Simulate tech news
            tech_news = [
                {
                    "title": "New AI Model Breaks Language Understanding Records",
                    "summary": "Latest AI breakthrough achieves human-level performance in language tasks",
                    "category": "artificial_intelligence",
                    "impact": "high",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Quantum Computing Milestone Reached",
                    "summary": "Researchers achieve quantum advantage in practical applications",
                    "category": "quantum_computing",
                    "impact": "high",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "5G Network Expansion Accelerates",
                    "summary": "Telecommunications companies roll out 5G infrastructure globally",
                    "category": "telecommunications",
                    "impact": "medium",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            result = {
                "tech_news": tech_news[:limit],
                "total_articles": len(tech_news),
                "scanned_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_crypto_news(self, task: TaskRequest) -> TaskResponse:
        """Handle crypto news request."""
        try:
            limit = task.parameters.get("limit", 10)
            
            # Simulate crypto news
            crypto_news = [
                {
                    "title": "Bitcoin Reaches New All-Time High",
                    "summary": "BTC breaks previous records amid institutional adoption",
                    "cryptocurrency": "bitcoin",
                    "sentiment": "positive",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Ethereum 2.0 Upgrade Progresses",
                    "summary": "Network upgrade shows promising results in testing",
                    "cryptocurrency": "ethereum",
                    "sentiment": "positive",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "title": "Regulatory Clarity Improves Market Confidence",
                    "summary": "New regulations provide framework for crypto adoption",
                    "cryptocurrency": "general",
                    "sentiment": "positive",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            result = {
                "crypto_news": crypto_news[:limit],
                "total_articles": len(crypto_news),
                "scanned_at": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_fact_check(self, task: TaskRequest) -> TaskResponse:
        """Handle fact checking request."""
        try:
            claim = task.parameters.get("claim", "")
            
            if not claim:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Claim is required for fact checking"
                )
            
            # Simulate fact checking
            fact_check_result = {
                "claim": claim,
                "verdict": "mostly_true",
                "confidence": 0.85,
                "explanation": "This claim is supported by multiple reliable sources and recent data.",
                "sources": [
                    "Reliable Source 1",
                    "Expert Analysis 2",
                    "Official Report 3"
                ],
                "related_facts": [
                    "Supporting fact 1",
                    "Supporting fact 2"
                ],
                "checked_at": datetime.now().isoformat()
            }
            
            result = {
                "fact_check": fact_check_result
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_research_history(self, task: TaskRequest) -> TaskResponse:
        """Handle get research history request."""
        try:
            limit = task.parameters.get("limit", 50)
            
            # Sort by timestamp (newest first)
            sorted_history = sorted(
                self.research_history,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            result = {
                "research_history": sorted_history[:limit],
                "total_searches": len(self.research_history),
                "showing": min(limit, len(sorted_history))
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_save_research(self, task: TaskRequest) -> TaskResponse:
        """Handle save research request."""
        try:
            research_data = task.parameters.get("research_data", {})
            title = task.parameters.get("title", "Untitled Research")
            tags = task.parameters.get("tags", [])
            
            if not research_data:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Research data is required"
                )
            
            # Save research (in reality, this would save to database)
            saved_research = {
                "id": f"research_{len(self.research_history) + 1:03d}",
                "title": title,
                "data": research_data,
                "tags": tags,
                "saved_at": datetime.now().isoformat()
            }
            
            result = {
                "message": f"Research '{title}' saved successfully",
                "research": saved_research
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_saved_research(self, task: TaskRequest) -> TaskResponse:
        """Handle get saved research request."""
        try:
            tags = task.parameters.get("tags", [])
            limit = task.parameters.get("limit", 20)
            
            # Simulate saved research
            saved_research = [
                {
                    "id": "research_001",
                    "title": "AI Market Analysis",
                    "tags": ["ai", "market", "analysis"],
                    "saved_at": datetime.now().isoformat()
                },
                {
                    "id": "research_002",
                    "title": "Cryptocurrency Trends",
                    "tags": ["crypto", "trends", "finance"],
                    "saved_at": datetime.now().isoformat()
                }
            ]
            
            # Filter by tags if specified
            if tags:
                saved_research = [
                    r for r in saved_research 
                    if any(tag in r["tags"] for tag in tags)
                ]
            
            result = {
                "saved_research": saved_research[:limit],
                "total_saved": len(saved_research),
                "showing": min(limit, len(saved_research))
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    # Test the ResearchAgent
    async def test_research_agent():
        agent = ResearchAgent()
        
        try:
            await agent.start()
            print(f"✅ ResearchAgent started: {agent.get_info()}")
            
            # Test a task
            task = TaskRequest(
                task_id="test_001",
                agent_id=agent.agent_id,
                capability=AgentCapability.RESEARCH,
                task_type="scan_news",
                parameters={"category": "technology", "limit": 5}
            )
            
            response = await agent._handle_task(task)
            print(f"🔍 News response: {response.result}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
        finally:
            await agent.stop()
            print("✅ ResearchAgent stopped")
    
    asyncio.run(test_research_agent())
