#!/usr/bin/env python3
"""
Full-Featured Discord Bot for Jarvis MCP Integration

This bot connects to the Jarvis Client HTTP Server which provides access to ALL
connected MCP servers (trading, system, search, jarvis) through a single interface.

Usage:
    python discord_jarvis_bot_full.py

Environment Variables:
    DISCORD_BOT_TOKEN - Discord bot token
    DISCORD_CLIENT_ID - Discord client ID
    DISCORD_CLIENT_SERVER - Discord server ID
    DISCORD_WEBHOOK_URL - Discord webhook URL (optional)
    JARVIS_CLIENT_URL - Jarvis Client HTTP Server URL (default: http://localhost:3011)
"""

import asyncio
import aiohttp
import discord
import logging
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Import Jarvis AI model and formatter
try:
    from jarvis.models.model_manager import ModelManager
    from formatter import format_response
    MODEL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import Jarvis model or formatter: {e}")
    MODEL_AVAILABLE = False

# Import event listener
try:
    from jarvis_event_listener import TradingEventListener
    EVENT_LISTENER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import event listener: {e}")
    EVENT_LISTENER_AVAILABLE = False

# Import intelligence core
try:
    from jarvis.intelligence import IntentRouter, IntentResult, IntentType
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import intelligence core: {e}")
    INTELLIGENCE_AVAILABLE = False

# Import server manager
try:
    from server_manager import ServerManager
    SERVER_MANAGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import server manager: {e}")
    SERVER_MANAGER_AVAILABLE = False

# Import music player
try:
    from jarvis_music_player import MusicPlayer
    MUSIC_PLAYER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import music player: {e}")
    MUSIC_PLAYER_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_jarvis_bot_full.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
JARVIS_CLIENT_URL = os.getenv('JARVIS_CLIENT_URL', 'http://localhost:3012')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN_HERE')
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', 'YOUR_DISCORD_CLIENT_ID_HERE')
DISCORD_CLIENT_SERVER = os.getenv('DISCORD_CLIENT_SERVER', 'YOUR_DISCORD_SERVER_ID_HERE')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# Discord bot intents
intents = discord.Intents.default()
intents.message_content = True  # This requires privileged intent
intents.guilds = True

# Create Discord client with enhanced connection settings
client = discord.Client(
    intents=intents,
    heartbeat_timeout=60.0,  # Increased heartbeat timeout
    max_messages=1000,  # Limit message cache
    chunk_guilds_at_startup=False,  # Don't chunk all guilds at startup
    member_cache_flags=discord.MemberCacheFlags.none()  # Disable member caching to save memory
)

# Global aiohttp session for connection reuse
session: Optional[aiohttp.ClientSession] = None

# Global server manager instance
server_manager: Optional[ServerManager] = None


class JarvisClientMCPClient:
    """Client for communicating with Jarvis Client HTTP Server."""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=60)  # Increased to 60 seconds for news scanning
        self.available_tools: Dict[str, Any] = {}
        self.connection_retries = 0
        self.max_connection_retries = 5
        self.last_health_check = 0
        self.health_check_interval = 30  # Check every 30 seconds
    
    async def health_check(self) -> bool:
        """Check if the server is healthy and responsive."""
        try:
            import time
            current_time = time.time()
            if current_time - self.last_health_check < self.health_check_interval:
                return True  # Skip if checked recently
            
            async with self.session.get(
                f"{self.base_url}/servers",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                self.last_health_check = current_time
                if response.status == 200:
                    self.connection_retries = 0  # Reset retry counter on success
                    return True
                else:
                    logger.warning(f"Health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Health check error: {e}")
            return False

    async def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools from all connected servers."""
        try:
            # Perform health check first
            if not await self.health_check():
                logger.warning("Server health check failed, but continuing with tools request")
            
            async with self.session.get(
                f"{self.base_url}/tools",
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    # Organize tools by server
                    tools_by_server = {}
                    for tool in tools_data:
                        server = tool.get('server', 'unknown')
                        if server not in tools_by_server:
                            tools_by_server[server] = []
                        tools_by_server[server].append(tool)
                    
                    self.available_tools = tools_by_server
                    logger.info(f"Loaded {len(tools_data)} tools from {len(tools_by_server)} servers")
                    return tools_by_server
                else:
                    logger.error(f"Failed to get tools: HTTP {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
            return {}
    
    async def call_tool(self, tool_name: str, arguments: dict = None, server: str = None) -> str:
        """
        Call a tool on the Jarvis Client HTTP Server with enhanced error handling and retry logic.
        
        Args:
            tool_name: The name of the tool to call
            arguments: The arguments for the tool
            server: Optional server name (if not specified, uses default)
            
        Returns:
            Response from the tool or error message
        """
        if arguments is None:
            arguments = {}
            
        payload = {
            "tool": tool_name,
            "args": arguments
        }
        
        if server:
            payload["server"] = server
        
        logger.info(f"Calling tool: {tool_name} on server: {server or 'default'} with args: {arguments}")
        
        # Enhanced retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check server health before making request
                if attempt > 0:  # Only check health on retries
                    if not await self.health_check():
                        logger.warning(f"Server health check failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                
                # Use longer timeout for news scanning
                timeout = aiohttp.ClientTimeout(total=120) if tool_name == "jarvis_scan_news" else self.timeout
                
                async with self.session.post(
                    f"{self.base_url}/run-tool",
                    json=payload,
                    timeout=timeout,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            result = data.get('result', {})
                            
                            # Handle different result formats
                            if isinstance(result, dict):
                                if 'text' in result:
                                    return result['text']
                                elif 'items' in result:
                                    # Handle content list
                                    texts = []
                                    for item in result.get('items', []):
                                        if item.get('type') == 'text' and item.get('text'):
                                            texts.append(item['text'])
                                    return '\n'.join(texts) if texts else str(result)
                                else:
                                    return str(result)
                            else:
                                return str(result)
                        else:
                            error_msg = data.get('detail', 'Unknown error')
                            logger.error(f"Tool call failed: {error_msg}")
                            return f"Error: {error_msg}"
                    else:
                        error_msg = await response.text()
                        logger.error(f"HTTP {response.status}: {error_msg}")
                        
                        # Check if it's a recoverable error
                        if response.status in [502, 503, 504] and attempt < max_retries - 1:
                            logger.warning(f"Recoverable HTTP error {response.status}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        return f"Error: HTTP {response.status} - {error_msg}"
                        
            except asyncio.TimeoutError:
                error_msg = f"Request timed out (attempt {attempt + 1}/{max_retries})"
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
            except aiohttp.ClientError as e:
                error_msg = f"Network error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
            except Exception as e:
                error_msg = f"Unexpected error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
        
        return f"Error: Failed to call tool after {max_retries} attempts"
    
    async def natural_language_query(self, query: str) -> str:
        """
        Send a natural language query to the Jarvis Client.
        
        Args:
            query: The natural language query
            
        Returns:
            Response from Jarvis
        """
        try:
            payload = {"message": query}
            
            logger.info(f"Sending natural language query: {query}")
            
            async with self.session.post(
                f"{self.base_url}/nl",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data.get('text', 'No response received')
                else:
                    error_msg = await response.text()
                    logger.error(f"Natural language query failed: HTTP {response.status} - {error_msg}")
                    return f"Error: {error_msg}"
                    
        except Exception as e:
            error_msg = f"Natural language query error: {str(e)}"
            logger.error(error_msg)
            return error_msg


class ConversationContext:
    """Track conversation context for follow-up questions."""
    
    def __init__(self, max_history: int = 5):
        self.history: Dict[int, List[Dict]] = {}  # user_id -> messages
        self.max_history = max_history
    
    def add_message(self, user_id: int, query: str, response: str, metadata: dict = None):
        """Add a message to conversation history."""
        if user_id not in self.history:
            self.history[user_id] = []
        
        self.history[user_id].append({
            "query": query,
            "response": response,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        })
        
        # Trim to max history
        if len(self.history[user_id]) > self.max_history:
            self.history[user_id] = self.history[user_id][-self.max_history:]
    
    def get_context(self, user_id: int, last_n: int = 2) -> str:
        """Get recent conversation context."""
        if user_id not in self.history:
            return ""
        
        recent = self.history[user_id][-last_n:]
        context_parts = []
        
        for msg in recent:
            context_parts.append(f"Previous: {msg['query'][:100]}")
        
        return "\n".join(context_parts)
    
    def extract_relevant_data(self, user_id: int, keyword: str) -> Optional[str]:
        """Extract relevant data from previous responses."""
        if user_id not in self.history:
            return None
        
        # Search backwards through history
        for msg in reversed(self.history[user_id]):
            if keyword.lower() in msg['query'].lower():
                return msg.get('metadata', {})
        
        return None


class DiscordCommandRouter:
    """Routes Discord commands to appropriate Jarvis tools."""
    
    def __init__(self, jarvis_client: JarvisClientMCPClient):
        self.jarvis_client = jarvis_client
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """Detect the user's intent and extract key information."""
        import re
        query_lower = query.lower()
        
        intent_patterns = {
            "specific_list": {
                "pattern": r"list|top \d+|what are|show me|give me",
                "expects_detailed_response": True,
                "should_extract_items": True
            },
            "follow_up": {
                "pattern": r"more about|details on|tell me more|explain|elaborate|more information",
                "needs_context": True,
                "expects_detailed_response": True
            },
            "comparison": {
                "pattern": r"compare|versus|vs|difference between",
                "expects_detailed_response": True,
                "needs_multiple_sources": True
            },
            "current_events": {
                "pattern": r"latest|recent|new|today|this week|breaking",
                "prefers_news_source": True,
                "time_sensitive": True
            }
        }
        
        detected = {
            "intent_type": "general",
            "confidence": 0.5,
            "metadata": {}
        }
        
        for intent_name, intent_spec in intent_patterns.items():
            if re.search(intent_spec["pattern"], query_lower):
                detected["intent_type"] = intent_name
                detected["confidence"] = 0.8
                detected["metadata"] = {k: v for k, v in intent_spec.items() if k != "pattern"}
                break
        
        return detected
    
    def refine_search_query(self, query: str, intent: Dict[str, Any]) -> str:
        """Refine search query based on intent and content."""
        query_lower = query.lower()
        
        # For crypto/Web3 queries, filter out gambling sites
        if any(word in query_lower for word in ['crypto', 'coin', 'token', 'blockchain', 'web3']):
            # Add exclusion terms and specificity
            return f"{query} cryptocurrency blockchain -casino -gambling -betting site:coinmarketcap.com OR site:coingecko.com OR site:decrypt.co"
        
        # For tariff/policy queries, add specificity
        if any(word in query_lower for word in ['tariff', 'trade deal', 'policy', 'regulation']):
            return f"{query} official announcement 2025 government"
        
        # For "top" or "best" queries, add ranking terms
        if any(word in query_lower for word in ['top', 'best', 'leading']):
            return f"{query} ranked list 2025"
        
        # For news queries, add time restriction
        if intent.get("metadata", {}).get("time_sensitive"):
            return f"{query} 2025"
        
        return query
    
    def validate_response_quality(self, response: str, query: str) -> tuple[bool, Optional[str]]:
        """Check if response adequately answers the query."""
        import re
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Check 1: User asked for a list, did we provide one?
        if "list" in query_lower or "top" in query_lower or "what are" in query_lower:
            # Count bullet points, numbers, or line breaks
            has_list_formatting = bool(re.search(r'(\n-|\n\d+\.|\n•|^\d+\.)', response, re.MULTILINE))
            if not has_list_formatting and len(response) < 300:
                return False, "Response should include a formatted list with details"
        
        # Check 2: User asked for specific data, did we provide it?
        if any(word in query_lower for word in ['what are', 'which', 'details', 'explain']):
            # Response should be reasonably long
            if len(response) < 200:
                return False, "Response too brief for detail query"
        
        # Check 3: Check for common error patterns
        error_patterns = ['no results', 'session closed', 'error:', 'failed to']
        if any(pattern in response_lower for pattern in error_patterns):
            return False, "Response contains error indicators"
        
        # Check 4: Avoid vague responses
        vague_phrases = ['let me know', 'would you like', 'i can provide', 'here are some']
        if len(response) < 200 and any(phrase in response_lower for phrase in vague_phrases):
            return False, "Response is too vague"
        
        # Check 5: For search queries, check for irrelevant results (e.g., casino for crypto)
        if 'crypto' in query_lower or 'coin' in query_lower:
            if 'casino' in response_lower or 'gambling' in response_lower:
                return False, "Response contains irrelevant gambling/casino content"
        
        return True, None
    
    async def _handle_local_command(self, tool_name: str, arguments: Dict[str, Any], message: discord.Message) -> str:
        """Handle local commands (event management and music) that don't go through MCP."""
        global event_listener, music_player
        
        # Handle music commands
        if tool_name.startswith("music_"):
            if not music_player:
                return "❌ Music player is not initialized."
            
            return await self._handle_music_command(tool_name, arguments, message)
        
        # Handle event commands
        if not event_listener:
            return "❌ Event listener is not initialized. Set EVENT_NOTIFICATION_CHANNEL_ID in your .env file and restart the bot."
        
        try:
            if tool_name == "events_start_monitoring":
                success = await event_listener.start_monitoring()
                if success:
                    return "✅ Event monitoring started! You'll receive real-time trading notifications in this channel."
                else:
                    return "⚠️ Event monitoring is already running."
            
            elif tool_name == "events_stop_monitoring":
                success = await event_listener.stop_monitoring()
                if success:
                    return "🛑 Event monitoring stopped. No more notifications will be sent."
                else:
                    return "⚠️ Event monitoring is not currently running."
            
            elif tool_name == "events_get_statistics":
                stats = event_listener.get_statistics()
                total = stats["total_events"]
                by_type = stats["by_type"]
                is_monitoring = stats["is_monitoring"]
                
                status_emoji = "🟢" if is_monitoring else "🔴"
                response = f"📊 **Event Statistics**\n\n"
                response += f"Status: {status_emoji} {'Monitoring' if is_monitoring else 'Stopped'}\n"
                response += f"Total Events: **{total}**\n\n"
                response += "**By Type:**\n"
                
                for event_type, count in by_type.items():
                    if count > 0:
                        response += f"• {event_type}: {count}\n"
                
                return response
            
            elif tool_name == "events_get_history":
                limit = arguments.get("limit", 10)
                history = event_listener.get_history(limit)
                
                if not history:
                    return "📝 No events in history yet."
                
                response = f"📝 **Recent Events** (Last {len(history)})\n\n"
                
                for event in history:
                    event_type = event.get("type", "unknown")
                    symbol = event.get("symbol", "N/A")
                    timestamp = event.get("received_at", "N/A")
                    response += f"• **{event_type}** - {symbol} at {timestamp[:19]}\n"
                
                return response
            
            elif tool_name == "events_test_event":
                event_type = arguments.get("type", "market_alert")
                
                # Create a test event
                test_events = {
                    "market_alert": {
                        "type": "market_alert",
                        "symbol": "BTC/USDT",
                        "change_percent": 3.5,
                        "price": 45200.00,
                        "volume": 1200000,
                        "timeframe": "1h"
                    },
                    "trade_executed": {
                        "type": "trade_executed",
                        "side": "BUY",
                        "symbol": "ETH/USDT",
                        "size": 2.5,
                        "price": 2800.00,
                        "pnl_percent": 2.3,
                        "order_type": "MARKET"
                    },
                    "risk_limit_hit": {
                        "type": "risk_limit_hit",
                        "reason": "Daily loss limit reached",
                        "impact": "All trading halted",
                        "current_loss": 5.2,
                        "limit": 5.0
                    },
                    "daily_summary": {
                        "type": "daily_summary",
                        "total_trades": 15,
                        "win_rate": 66.7,
                        "total_pnl": 450.00,
                        "total_pnl_percent": 4.5,
                        "best_trade": {"symbol": "BTC/USDT", "pnl_percent": 5.2},
                        "worst_trade": {"symbol": "SOL/USDT", "pnl_percent": -1.8}
                    }
                }
                
                test_event = test_events.get(event_type)
                if not test_event:
                    return f"❌ Unknown test event type: {event_type}. Available: {', '.join(test_events.keys())}"
                
                # Send the test event
                await event_listener.handle_event(test_event)
                return f"✅ Test event sent: **{event_type}**\nCheck the notification channel for the message."
            
            elif tool_name == "events_check_markets":
                # This would call the MCP tool to check markets
                return "🔍 Manually triggering market price check... (This would call the MCP tool)"
            
            else:
                return f"❌ Unknown event command: {tool_name}"
        
        except Exception as e:
            logger.error(f"Error handling local command: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    async def _handle_music_command(self, tool_name: str, arguments: Dict[str, Any], message: discord.Message) -> str:
        """Handle music commands routed to the music player."""
        global music_player
        
        try:
            if tool_name == "music_play":
                song_name = arguments.get("song_name")
                return await music_player.play_song(message.author, message.channel, song_name)
            
            elif tool_name == "music_play_or_resume":
                # Check if paused, if so resume, otherwise play random
                guild_id = message.author.guild.id
                if guild_id in music_player.is_paused and music_player.is_paused[guild_id]:
                    return await music_player.resume(message.author, message.channel)
                else:
                    # Start playing with auto-queue
                    return await music_player.play_random(message.author, message.channel, count=5)
            
            elif tool_name == "music_pause":
                return await music_player.pause(message.author, message.channel)
            
            elif tool_name == "music_resume":
                return await music_player.resume(message.author, message.channel)
            
            elif tool_name == "music_stop":
                return await music_player.stop(message.author, message.channel)
            
            elif tool_name == "music_skip":
                return await music_player.skip(message.author, message.channel)
            
            elif tool_name == "music_queue_add":
                song_name = arguments.get("song_name")
                if not song_name:
                    return "❌ Please specify a song name to add to queue"
                return await music_player.add_to_queue(message.author, message.channel, song_name)
            
            elif tool_name == "music_queue_view":
                return await music_player.show_queue(message.author, message.channel)
            
            elif tool_name == "music_now_playing":
                return await music_player.now_playing(message.author, message.channel)
            
            elif tool_name == "music_leave":
                return await music_player.leave(message.author, message.channel)
            
            elif tool_name == "music_list_songs":
                return await music_player.list_available_songs()
            
            elif tool_name == "music_random":
                return await music_player.play_random(message.author, message.channel)
            
            elif tool_name == "music_search":
                keyword = arguments.get("keyword")
                if not keyword:
                    return "❌ Please specify a search keyword"
                return await music_player.search_songs(keyword)
            
            elif tool_name == "music_clear_queue":
                return await music_player.clear_queue(message.author, message.channel)
            
            elif tool_name == "music_remove_from_queue":
                position = arguments.get("position")
                if not position:
                    return "❌ Please specify a position to remove"
                return await music_player.remove_from_queue(message.author, message.channel, position)
            
            elif tool_name == "music_mcp_queue":
                return await music_player.get_mcp_queue()
            
            else:
                return f"❌ Unknown music command: {tool_name}"
        
        except Exception as e:
            logger.error(f"Error handling music command: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    async def auto_followup(self, initial_response: str, query: str) -> Optional[str]:
        """Execute intelligent follow-up search if initial response is poor."""
        query_lower = query.lower()
        
        # If asking about Web3 coins and response is poor
        if ('web3' in query_lower or 'crypto' in query_lower) and ('coin' in query_lower or 'token' in query_lower):
            if 'list' in query_lower or 'top' in query_lower or 'what are' in query_lower:
                # Try a more specific search
                refined_query = "top 10 web3 cryptocurrencies 2025 by market cap coinmarketcap"
                logger.info(f"Auto-followup: Searching for '{refined_query}'")
                try:
                    return await self.jarvis_client.call_tool(
                        "jarvis_web_search",
                        {"query": refined_query},
                        "jarvis"
                    )
                except Exception as e:
                    logger.warning(f"Auto-followup failed: {e}")
                    return None
        
        # If asking about tariffs and response is too brief
        if 'tariff' in query_lower and len(initial_response) < 300:
            refined_query = "new tariffs imposed 2025 Trump administration details list"
            logger.info(f"Auto-followup: Searching for '{refined_query}'")
            try:
                return await self.jarvis_client.call_tool(
                    "jarvis_web_search",
                    {"query": refined_query},
                    "jarvis"
                )
            except Exception as e:
                logger.warning(f"Auto-followup failed: {e}")
                return None
        
        return None
    
    def parse_command(self, message_content: str) -> tuple[str, dict, str]:
        """
        Parse Discord message and return appropriate tool, arguments, and server.
        
        Args:
            message_content: The Discord message content
            
        Returns:
            Tuple of (tool_name, arguments, server)
        """
        content = message_content.lower().strip()
        
        # Command routing - all tools are on the jarvis server
        if content.startswith('/news') or 'scan news' in content:
            return "jarvis_scan_news", {}, "jarvis"
        
        # Trading Commands - using ACTUAL tool names with double namespace prefix
        elif content.startswith('/balance') or 'get balance' in content:
            return "trading.trading.get_balance", {}, "jarvis"
        elif content.startswith('/price') or 'get price' in content:
            # Extract symbol from command
            symbol = message_content.replace('/price', '').replace('get price', '').strip().upper()
            if not symbol:
                return "jarvis_chat", {"message": "Please specify a symbol for price lookup. Example: /price BTC"}, "jarvis"
            
            # Auto-format symbol for Kraken (add /USD or /USDT if not present)
            if '/' not in symbol:
                # Try common quote currencies
                symbol = f"{symbol}/USD"
            
            return "trading.trading.get_price", {"symbol": symbol}, "jarvis"
        elif content.startswith('/ohlcv') or 'ohlcv data' in content:
            # Extract symbol from command
            symbol = message_content.replace('/ohlcv', '').replace('ohlcv data', '').strip().upper()
            if not symbol:
                return "jarvis_chat", {"message": "Please specify a symbol for OHLCV data. Example: /ohlcv BTC"}, "jarvis"
            
            # Auto-format symbol for Kraken (add /USD or /USDT if not present)
            if '/' not in symbol:
                symbol = f"{symbol}/USD"
            
            return "trading.trading.get_ohlcv", {"symbol": symbol}, "jarvis"
        elif content.startswith('/momentum') or 'momentum signals' in content:
            return "trading.trading.get_momentum_signals", {}, "jarvis"
        elif content.startswith('/doctor') or 'trading doctor' in content:
            return "trading.trading.doctor", {}, "jarvis"
        elif content.startswith('/history') or 'trade history' in content:
            return "trading.trading.get_trade_history", {}, "jarvis"
        elif content.startswith('/pnl') or 'profit loss' in content:
            return "trading.trading.get_pnl_summary", {}, "jarvis"
        
        # Portfolio Commands (Paper Trading) - using ACTUAL tool names with trading.portfolio prefix
        elif content.startswith('/portfolio') or 'get portfolio' in content:
            return "trading.portfolio.get_overview", {}, "jarvis"
        elif content.startswith('/positions') or 'get positions' in content:
            return "trading.portfolio.get_positions", {}, "jarvis"
        elif content.startswith('/trades') or 'get trades' in content or 'recent trades' in content:
            return "trading.trading.get_recent_executions", {"limit": 20}, "jarvis"
        elif content.startswith('/paper') or 'paper trading' in content:
            return "trading.portfolio.get_overview", {}, "jarvis"
        elif content.startswith('/performance') or 'get performance' in content:
            return "trading.portfolio.get_performance", {}, "jarvis"
        elif content.startswith('/exit') or 'exit engine' in content:
            return "trading.portfolio.get_exit_engine_status", {}, "jarvis"
        elif content.startswith('/state') or 'trading state' in content:
            return "trading.portfolio.get_trading_state", {}, "jarvis"
        elif content.startswith('/export') or 'export data' in content:
            return "trading.portfolio.get_export_data", {}, "jarvis"
        
        # System Commands
        elif content.startswith('/status') or 'get status' in content:
            return "jarvis_get_status", {}, "jarvis"
        elif content.startswith('/memory') or 'get memory' in content:
            return "jarvis_get_memory", {"limit": 10}, "jarvis"
        elif content.startswith('/tasks') or 'get tasks' in content:
            return "jarvis_get_tasks", {"status": "all"}, "jarvis"
        elif content.startswith('/quests') or 'get quests' in content:
            return "system.system.list_quests", {}, "jarvis"
        elif content.startswith('/system') or 'system status' in content:
            return "system.system.get_status", {}, "jarvis"
        
        # Event Monitoring Commands
        elif content.startswith('/events start') or content == '/events on':
            return "events_start_monitoring", {}, "local"
        elif content.startswith('/events stop') or content == '/events off':
            return "events_stop_monitoring", {}, "local"
        elif content.startswith('/events stats') or content == '/events statistics':
            return "events_get_statistics", {}, "local"
        elif content.startswith('/events history'):
            # Extract limit if provided
            import re
            match = re.search(r'history\s+(\d+)', content)
            limit = int(match.group(1)) if match else 10
            return "events_get_history", {"limit": limit}, "local"
        elif content.startswith('/events test'):
            # Extract event type if provided
            test_type = content.replace('/events test', '').strip()
            return "events_test_event", {"type": test_type if test_type else "market_alert"}, "local"
        elif content.startswith('/events check'):
            return "events_check_markets", {}, "local"
        
        # Music Commands
        elif content.startswith('/play'):
            # Extract song name if provided
            song_name = message_content.replace('/play', '').strip()
            # If no song name, check if we should resume instead
            if not song_name:
                return "music_play_or_resume", {}, "local"
            return "music_play", {"song_name": song_name}, "local"
        elif content.startswith('/pause'):
            return "music_pause", {}, "local"
        elif content.startswith('/resume'):
            return "music_resume", {}, "local"
        elif content.startswith('/stop'):
            return "music_stop", {}, "local"
        elif content.startswith('/skip'):
            return "music_skip", {}, "local"
        elif content.startswith('/queue clear'):
            return "music_clear_queue", {}, "local"
        elif content.startswith('/queue remove'):
            # Extract position
            import re
            match = re.search(r'remove\s+(\d+)', content)
            if match:
                position = int(match.group(1))
                return "music_remove_from_queue", {"position": position}, "local"
            else:
                return "music_queue_view", {}, "local"
        elif content.startswith('/queue'):
            # Check if adding to queue or viewing queue
            rest = message_content.replace('/queue', '').strip()
            if rest:
                return "music_queue_add", {"song_name": rest}, "local"
            else:
                return "music_queue_view", {}, "local"
        elif content.startswith('/nowplaying') or content.startswith('/np'):
            return "music_now_playing", {}, "local"
        elif content.startswith('/songs') or content.startswith('/list'):
            return "music_list_songs", {}, "local"
        elif content.startswith('/random') or content.startswith('/shuffle'):
            return "music_random", {}, "local"
        elif content.startswith('/findsong') or content.startswith('/find'):
            # Extract search keyword
            keyword = message_content.replace('/findsong', '').replace('/find', '').strip()
            if not keyword:
                return "music_list_songs", {}, "local"
            return "music_search", {"keyword": keyword}, "local"
        elif content.startswith('/mcpqueue'):
            return "music_mcp_queue", {}, "local"
        elif content.startswith('/leave') or content.startswith('/disconnect'):
            return "music_leave", {}, "local"
        elif content.startswith('/volume'):
            # Extract volume level
            import re
            match = re.search(r'volume\s+(\d+)', content)
            if match:
                volume = int(match.group(1))
                return "music_volume", {"volume": volume}, "local"
            else:
                return "music_volume", {}, "local"
        elif content.startswith('/join'):
            return "music_join", {}, "local"
        
        # Search Commands (web search)
        elif content.startswith('/search') or 'web search' in content:
            # Extract search query
            query = message_content.replace('/search', '').replace('web search', '').strip()
            if not query:
                query = "latest technology news"
            
            # Detect intent and refine query
            intent = self.detect_query_intent(query)
            refined_query = self.refine_search_query(query, intent)
            
            logger.info(f"Search query refined: '{query}' -> '{refined_query}'")
            return "jarvis_web_search", {"query": refined_query}, "jarvis"
        
        # Help and Chat
        elif content.startswith('/help') or 'help' in content:
            return "jarvis_chat", {"message": "show available commands and help"}, "jarvis"
        elif any(word in content for word in ['date', 'time', 'today', 'what day', 'what time']):
            # Handle date/time questions directly with jarvis_chat
            return "jarvis_chat", {"message": message_content}, "jarvis"
        else:
            # For any other message, use natural language processing
            return "natural_language", {"query": message_content}, None
    
    async def handle_message(self, message: discord.Message) -> str:
        """
        Handle a Discord message and return Jarvis response with retry logic and validation.
        
        Args:
            message: The Discord message object
            
        Returns:
            Response from Jarvis
        """
        tool_name, arguments, server = self.parse_command(message.content)
        
        # Handle local commands (event management)
        if server == "local":
            return await self._handle_local_command(tool_name, arguments, message)
        
        # Send progress message for long-running operations
        progress_msg = None
        if tool_name == "jarvis_scan_news":
            progress_msg = await message.reply("🔍 Scanning news sources... This may take up to 2 minutes.")
        
        # Retry logic with exponential backoff
        max_retries = 3
        result = None
        
        for attempt in range(max_retries):
            try:
                if tool_name == "natural_language":
                    # Use natural language processing
                    result = await self.jarvis_client.natural_language_query(arguments["query"])
                else:
                    # Call specific tool
                    result = await self.jarvis_client.call_tool(tool_name, arguments, server)
                
                # Successfully got a result, break the retry loop
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a recoverable error
                if any(keyword in error_msg for keyword in ['closed', 'session', 'connection', 'timeout']):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"Recoverable error on attempt {attempt + 1}/{max_retries}: {e}")
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        result = f"❌ Connection error after {max_retries} attempts. Please try again in a moment."
                        break
                else:
                    # Non-recoverable error
                    logger.error(f"Non-recoverable error: {e}")
                    result = f"❌ Error: {str(e)}"
                    break
        
        # Delete progress message if it was sent
        if progress_msg:
            try:
                await progress_msg.delete()
            except:
                pass  # Ignore if message can't be deleted
        
        # Validate response quality
        if result and not result.startswith("❌"):
            is_valid, reason = self.validate_response_quality(result, message.content)
            
            # If response is poor quality, try auto-followup
            if not is_valid:
                logger.info(f"Response validation failed: {reason}. Attempting auto-followup...")
                followup_result = await self.auto_followup(result, message.content)
                
                if followup_result:
                    # Append followup to original result
                    result = f"{result}\n\n**📊 Additional Information:**\n{followup_result}"
                    logger.info("Auto-followup successful")
                else:
                    # Just use the original result
                    logger.info("Auto-followup didn't improve result, using original")
        
        return result or "No response received from Jarvis."


async def execute_intelligent_tool(intent_result: 'IntentResult', message: discord.Message) -> str:
    """Execute a tool based on intelligent intent analysis."""
    global jarvis_client, command_router
    
    try:
        tool_name = intent_result.tool_name
        arguments = intent_result.arguments
        server = "jarvis"  # Default server
        
        # Determine server based on tool name
        if tool_name.startswith("music_"):
            server = "local"
        elif tool_name.startswith("events_"):
            server = "local"
        elif tool_name.startswith("trading."):
            server = "jarvis"
        elif tool_name.startswith("system."):
            server = "jarvis"
        elif tool_name.startswith("jarvis_"):
            server = "jarvis"
        elif tool_name.startswith("fitness."):
            server = "jarvis"
        
        logger.info(f"🔧 Executing intelligent tool: {tool_name} on server: {server}")
        logger.info(f"📝 Arguments: {arguments}")
        
        # Handle local commands (music, events)
        if server == "local":
            return await command_router._handle_local_command(tool_name, arguments, message)
        
        # Handle MCP tools
        else:
            if tool_name == "jarvis_chat":
                # Use natural language processing
                return await jarvis_client.natural_language_query(arguments.get("message", ""))
            else:
                # Call specific tool
                return await jarvis_client.call_tool(tool_name, arguments, server)
                
    except Exception as e:
        logger.error(f"Error executing intelligent tool: {e}")
        return f"❌ Error executing tool: {str(e)}"


# Global instances
jarvis_client: Optional[JarvisClientMCPClient] = None
command_router: Optional[DiscordCommandRouter] = None
model_manager: Optional['ModelManager'] = None  # For AI-powered response formatting
conversation_context: Optional[ConversationContext] = None  # For tracking conversation history
event_listener: Optional['TradingEventListener'] = None  # For trading event notifications
music_player: Optional['MusicPlayer'] = None  # For music playback in voice channels
intent_router: Optional[IntentRouter] = None  # For intelligent command routing

# Event notification channel ID (configure in .env or here)
EVENT_NOTIFICATION_CHANNEL_ID = os.getenv('EVENT_NOTIFICATION_CHANNEL_ID', None)


@client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global session, jarvis_client, command_router, model_manager, conversation_context, event_listener, music_player, intent_router, server_manager
    
    logger.info(f'{client.user} has connected to Discord!')
    logger.info(f'Bot is in {len(client.guilds)} guilds')
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize server manager and start missing servers
    if SERVER_MANAGER_AVAILABLE:
        try:
            server_manager = ServerManager(JARVIS_CLIENT_URL)
            logger.info("🔧 Server manager initialized")
            
            # Start missing servers
            logger.info("🚀 Checking for missing servers...")
            available = await server_manager.start_missing_servers()
            
            # Log server status
            for server, is_available in available.items():
                status = "✅" if is_available else "❌"
                logger.info(f"  {server}: {status}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize server manager: {e}")
    else:
        logger.warning("⚠️ Server manager not available - servers must be started manually")
    
    # Initialize Jarvis client and command router
    jarvis_client = JarvisClientMCPClient(JARVIS_CLIENT_URL, session)
    command_router = DiscordCommandRouter(jarvis_client)
    
    # Initialize intelligence core
    if INTELLIGENCE_AVAILABLE:
        try:
            intent_router = IntentRouter()
            logger.info("🧠 Intelligence core initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize intelligence core: {e}")
            intent_router = None
    else:
        logger.warning("⚠️ Intelligence core not available")
        intent_router = None
    
    # Initialize music player
    if MUSIC_PLAYER_AVAILABLE:
        music_player = MusicPlayer(jarvis_client)
        logger.info("✅ Music player initialized")
    else:
        logger.info("ℹ️ Music player not available (module not loaded)")
    
    # Initialize conversation context for tracking user queries
    conversation_context = ConversationContext(max_history=5)
    logger.info("✅ Conversation context initialized")
    
    # Initialize AI model for response formatting
    if MODEL_AVAILABLE:
        try:
            model_manager = ModelManager()
            logger.info("✅ AI model initialized for response formatting")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize AI model for formatting: {e}")
            logger.warning("Responses will be sent without AI formatting")
            model_manager = None
    else:
        logger.warning("⚠️ Model manager not available - responses will be sent raw")
        model_manager = None
    
    # Initialize event listener if channel is configured
    if EVENT_LISTENER_AVAILABLE and EVENT_NOTIFICATION_CHANNEL_ID:
        try:
            channel_id = int(EVENT_NOTIFICATION_CHANNEL_ID)
            notification_channel = client.get_channel(channel_id)
            
            if notification_channel:
                event_listener = TradingEventListener(JARVIS_CLIENT_URL, notification_channel)
                logger.info(f"✅ Event listener initialized for channel: {notification_channel.name}")
            else:
                logger.warning(f"⚠️ Could not find notification channel with ID: {channel_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize event listener: {e}")
    else:
        if not EVENT_LISTENER_AVAILABLE:
            logger.info("ℹ️ Event listener not available (module not loaded)")
        if not EVENT_NOTIFICATION_CHANNEL_ID:
            logger.info("ℹ️ Event notifications disabled (EVENT_NOTIFICATION_CHANNEL_ID not set)")
    
    # Get available tools
    try:
        tools = await jarvis_client.get_available_tools()
        if tools:
            logger.info("Available tools by server:")
            for server, server_tools in tools.items():
                logger.info(f"  {server}: {len(server_tools)} tools")
        else:
            logger.warning("No tools available - check if Jarvis Client HTTP Server is running")
    except Exception as e:
        logger.error(f"Failed to get available tools: {e}")


@client.event
async def on_message(message):
    """Event handler for incoming Discord messages with intelligent routing."""
    global command_router, model_manager, conversation_context, intent_router
    
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Only respond to messages in the configured server (if specified)
    if DISCORD_CLIENT_SERVER and DISCORD_CLIENT_SERVER != 'YOUR_DISCORD_SERVER_ID_HERE':
        if str(message.guild.id) != DISCORD_CLIENT_SERVER:
            return
    
    # Log incoming message
    logger.info(f"Received message from {message.author}: {message.content}")
    
    try:
        # Show typing indicator while processing
        async with message.channel.typing():
            # Check for follow-up context
            user_context = ""
            if conversation_context:
                user_context = conversation_context.get_context(message.author.id)
                if user_context:
                    logger.info(f"Using conversation context for {message.author.name}")
            
            # Step 1: Intelligent intent analysis (if available)
            raw_response = None
            intent_result = None
            
            if intent_router and INTELLIGENCE_AVAILABLE:
                try:
                    # Use intelligent routing
                    intent_result = await intent_router.analyze_intent(
                        message.content, 
                        str(message.author.id), 
                        str(message.channel.id)
                    )
                    
                    logger.info(f"🧠 Intent: {intent_result.intent_type.value} "
                              f"(confidence: {intent_result.confidence:.2f})")
                    logger.info(f"🔧 Tool: {intent_result.tool_name}")
                    logger.info(f"💭 Reasoning: {intent_result.reasoning}")
                    
                    # Execute the determined tool
                    raw_response = await execute_intelligent_tool(intent_result, message)
                    
                except Exception as e:
                    logger.warning(f"Intelligent routing failed, falling back to command router: {e}")
                    intent_result = None
            
            # Step 2: Fallback to traditional command router if intelligent routing failed
            if raw_response is None:
                raw_response = await command_router.handle_message(message)
            
            # Step 3: Format the response using AI (if available)
            if model_manager and MODEL_AVAILABLE:
                try:
                    # Get context about what command was run
                    context = f"User asked: {message.content[:100]}"
                    if user_context:
                        context += f"\nPrevious context: {user_context[:100]}"
                    
                    # Add intent information if available
                    if intent_result:
                        context += f"\nIntent: {intent_result.intent_type.value} "
                        context += f"(confidence: {intent_result.confidence:.2f})"
                        context += f"\nReasoning: {intent_result.reasoning}"
                    
                    # Detect intent for better formatting
                    intent = command_router.detect_query_intent(message.content)
                    if intent.get("metadata", {}).get("expects_detailed_response"):
                        context += "\nUser expects detailed response with specific data."
                    
                    # Format the response using Jarvis AI
                    formatted_response = await format_response(
                        raw_response=raw_response,
                        model_manager=model_manager,
                        context=context
                    )
                    response = formatted_response
                    logger.info("✨ Response formatted by AI")
                except Exception as format_error:
                    # If formatting fails, use raw response
                    logger.warning(f"Formatting failed, using raw response: {format_error}")
                    response = raw_response
            else:
                # No AI available, use raw response
                response = raw_response
            
            # Handle empty or error responses
            if not response or response.strip() == "":
                response = "No response received from Jarvis."
            
            # Send response (automatically handles long messages by splitting)
            await send_long_message(message, response)
            
            # Store in conversation context with intent information
            if conversation_context:
                metadata = {"timestamp": datetime.now().isoformat()}
                if intent_result:
                    metadata.update({
                        "intent_type": intent_result.intent_type.value,
                        "confidence": intent_result.confidence,
                        "tool_used": intent_result.tool_name,
                        "reasoning": intent_result.reasoning
                    })
                
                conversation_context.add_message(
                    user_id=message.author.id,
                    query=message.content,
                    response=response,
                    metadata=metadata
                )
            
            # Log response
            logger.info(f"Sent response to {message.author}: {response[:100]}...")
            
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        await message.reply("Sorry, I encountered an error processing your request.")
        
        # Send error to webhook if configured
        if DISCORD_WEBHOOK_URL:
            await send_error_webhook(error_msg, message.content)


def split_message_intelligently(text: str, max_length: int = 1950) -> List[str]:
    """
    Split a long message into multiple parts at natural boundaries.
    
    Args:
        text: The text to split
        max_length: Maximum length per message (default 1950 to leave room for indicators)
        
    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by double newlines (paragraphs) first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed limit
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            # If current chunk has content, save it
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > max_length:
                sentences = paragraph.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        
                        # If sentence itself is too long, split by character limit
                        if len(sentence) > max_length:
                            # Split at newlines within the long sentence
                            lines = sentence.split('\n')
                            for line in lines:
                                if len(current_chunk) + len(line) + 1 > max_length:
                                    if current_chunk:
                                        chunks.append(current_chunk.strip())
                                    current_chunk = line + '\n'
                                else:
                                    current_chunk += line + '\n'
                        else:
                            current_chunk = sentence + ' '
                    else:
                        current_chunk += sentence + ' '
            else:
                current_chunk = paragraph + '\n\n'
        else:
            current_chunk += paragraph + '\n\n'
    
    # Add any remaining content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


async def send_long_message(message: discord.Message, text: str) -> None:
    """
    Send a message that might be longer than Discord's 2000 character limit.
    Automatically splits into multiple messages with indicators.
    
    Args:
        message: The Discord message to reply to
        text: The text to send (can be any length)
    """
    chunks = split_message_intelligently(text, max_length=1950)
    
    if len(chunks) == 1:
        # Single message, send normally
        await message.reply(chunks[0])
        logger.info(f"Sent single message ({len(chunks[0])} chars)")
    else:
        # Multiple messages, add indicators
        logger.info(f"Splitting response into {len(chunks)} messages")
        
        for i, chunk in enumerate(chunks, 1):
            # Add message indicator
            indicator = f"📄 **Part {i}/{len(chunks)}**\n\n" if i > 1 else ""
            full_chunk = indicator + chunk
            
            # Send the chunk
            if i == 1:
                await message.reply(full_chunk)
            else:
                # For subsequent messages, send in the same channel
                await message.channel.send(full_chunk)
            
            # Small delay to ensure messages arrive in order
            if i < len(chunks):
                await asyncio.sleep(0.5)
        
        logger.info(f"Successfully sent {len(chunks)} message parts")


async def send_error_webhook(error_msg: str, original_message: str):
    """Send error notification to Discord webhook."""
    if not DISCORD_WEBHOOK_URL or not session:
        return
    
    try:
        webhook_data = {
            "content": f"🚨 **Jarvis Bot Error**\n\n**Error:** {error_msg}\n**Original Message:** {original_message}\n**Time:** {datetime.now().isoformat()}"
        }
        
        async with session.post(DISCORD_WEBHOOK_URL, json=webhook_data) as response:
            if response.status == 204:
                logger.info("Error notification sent to webhook")
            else:
                logger.error(f"Failed to send webhook: {response.status}")
                
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")


async def cleanup():
    """Cleanup resources on shutdown."""
    global session, event_listener, music_player
    
    # Stop event monitoring if running
    if event_listener:
        try:
            await event_listener.cleanup()
            logger.info("Event listener cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up event listener: {e}")
    
    # Cleanup music player
    if music_player:
        try:
            await music_player.cleanup()
            logger.info("Music player cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up music player: {e}")
    
    if session:
        await session.close()
        logger.info("Closed aiohttp session")


@client.event
async def on_disconnect():
    """Event handler for bot disconnection."""
    global server_manager
    logger.info("Bot disconnected from Discord")
    
    # Stop managed servers when bot disconnects
    if server_manager and SERVER_MANAGER_AVAILABLE:
        try:
            logger.info("🛑 Stopping managed servers due to bot disconnection...")
            await server_manager.stop_all_servers()
        except Exception as e:
            logger.error(f"Error stopping servers: {e}")
    
    # Don't cleanup immediately - let the bot try to reconnect
    # await cleanup()

@client.event
async def on_resumed():
    """Event handler for when the bot resumes connection."""
    logger.info("Bot connection resumed successfully")

@client.event
async def on_error(event, *args, **kwargs):
    """Event handler for Discord errors."""
    logger.error(f"Discord error in event {event}: {args}, {kwargs}")

@client.event
async def on_socket_raw_receive(msg):
    """Log raw socket messages for debugging."""
    # Only log important events to avoid spam
    if msg.get('t') in ['RESUMED', 'READY', 'GUILD_CREATE', 'GUILD_DELETE']:
        logger.debug(f"Discord event: {msg.get('t')}")


async def connection_monitor():
    """Monitor connection health and attempt reconnection if needed."""
    global jarvis_client, server_manager
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if jarvis_client:
                # Check if the bot is connected to Discord
                if client.is_ready():
                    # Perform health check on the Jarvis server
                    if not await jarvis_client.health_check():
                        logger.warning("Jarvis server health check failed")
                        
                        # Try to restart missing servers
                        if server_manager and SERVER_MANAGER_AVAILABLE:
                            logger.info("🔄 Attempting to restart missing servers...")
                            try:
                                available = await server_manager.start_missing_servers()
                                for server, is_available in available.items():
                                    if not is_available:
                                        logger.warning(f"⚠️ {server} server still unavailable")
                            except Exception as e:
                                logger.error(f"Error restarting servers: {e}")
                else:
                    logger.warning("Discord bot is not ready")
                    
        except Exception as e:
            logger.error(f"Error in connection monitor: {e}")
            await asyncio.sleep(30)  # Wait before retrying

async def main():
    """Main entry point with enhanced error handling and monitoring."""
    # Debug: Show loaded environment variables (without exposing tokens)
    logger.info("Environment variables loaded:")
    logger.info(f"DISCORD_BOT_TOKEN: {'SET' if DISCORD_BOT_TOKEN and DISCORD_BOT_TOKEN != 'YOUR_DISCORD_BOT_TOKEN_HERE' else 'NOT SET'}")
    logger.info(f"DISCORD_CLIENT_ID: {'SET' if DISCORD_CLIENT_ID and DISCORD_CLIENT_ID != 'YOUR_DISCORD_CLIENT_ID_HERE' else 'NOT SET'}")
    logger.info(f"DISCORD_CLIENT_SERVER: {'SET' if DISCORD_CLIENT_SERVER and DISCORD_CLIENT_SERVER != 'YOUR_DISCORD_SERVER_ID_HERE' else 'NOT SET'}")
    logger.info(f"DISCORD_WEBHOOK_URL: {'SET' if DISCORD_WEBHOOK_URL else 'NOT SET'}")
    logger.info(f"JARVIS_CLIENT_URL: {JARVIS_CLIENT_URL}")
    
    # Validate configuration
    if DISCORD_BOT_TOKEN == 'YOUR_DISCORD_BOT_TOKEN_HERE' or not DISCORD_BOT_TOKEN:
        logger.error("Please set DISCORD_BOT_TOKEN environment variable")
        logger.error("Create a .env file with: DISCORD_BOT_TOKEN=your_actual_token_here")
        return
    
    logger.info("Starting Full-Featured Discord Jarvis Bot...")
    logger.info(f"Connecting to Jarvis Client HTTP Server: {JARVIS_CLIENT_URL}")
    
    # Start connection monitor task
    monitor_task = None
    
    try:
        # Start the bot with retry logic
        max_startup_retries = 3
        for attempt in range(max_startup_retries):
            try:
                logger.info(f"Starting bot (attempt {attempt + 1}/{max_startup_retries})")
                
                # Start connection monitor
                monitor_task = asyncio.create_task(connection_monitor())
                
                # Start the bot
                await client.start(DISCORD_BOT_TOKEN)
                break  # If we get here, the bot started successfully
                
            except discord.LoginFailure:
                logger.error("Invalid Discord bot token")
                logger.error("Please check your DISCORD_BOT_TOKEN in the .env file")
                break
            except discord.PrivilegedIntentsRequired as e:
                logger.error("Privileged intents not enabled!")
                logger.error("Go to https://discord.com/developers/applications/")
                logger.error("Select your bot -> Bot -> Privileged Gateway Intents")
                logger.error("Enable 'Message Content Intent'")
                logger.error("Then restart the bot")
                break
            except Exception as e:
                logger.error(f"Error starting bot (attempt {attempt + 1}): {e}")
                if attempt < max_startup_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Failed to start bot after all retry attempts")
                    
    except KeyboardInterrupt:
        logger.info("Bot startup interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
    finally:
        # Cleanup
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
        await cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
