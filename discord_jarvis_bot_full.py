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

# Create Discord client
client = discord.Client(intents=intents)

# Global aiohttp session for connection reuse
session: Optional[aiohttp.ClientSession] = None


class JarvisClientMCPClient:
    """Client for communicating with Jarvis Client HTTP Server."""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=60)  # Increased to 60 seconds for news scanning
        self.available_tools: Dict[str, Any] = {}
    
    async def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools from all connected servers."""
        try:
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
        Call a tool on the Jarvis Client HTTP Server.
        
        Args:
            tool_name: The name of the tool to call
            arguments: The arguments for the tool
            server: Optional server name (if not specified, uses default)
            
        Returns:
            Response from the tool or error message
        """
        try:
            if arguments is None:
                arguments = {}
                
            payload = {
                "tool": tool_name,
                "args": arguments
            }
            
            if server:
                payload["server"] = server
            
            logger.info(f"Calling tool: {tool_name} on server: {server or 'default'} with args: {arguments}")
            
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
                    return f"Error: HTTP {response.status} - {error_msg}"
                    
        except asyncio.TimeoutError:
            error_msg = "Request timed out"
            logger.error(error_msg)
            return error_msg
        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
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
        
        # Search Commands
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


# Global instances
jarvis_client: Optional[JarvisClientMCPClient] = None
command_router: Optional[DiscordCommandRouter] = None
model_manager: Optional['ModelManager'] = None  # For AI-powered response formatting
conversation_context: Optional[ConversationContext] = None  # For tracking conversation history


@client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global session, jarvis_client, command_router, model_manager, conversation_context
    
    logger.info(f'{client.user} has connected to Discord!')
    logger.info(f'Bot is in {len(client.guilds)} guilds')
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize Jarvis client and command router
    jarvis_client = JarvisClientMCPClient(JARVIS_CLIENT_URL, session)
    command_router = DiscordCommandRouter(jarvis_client)
    
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
    """Event handler for incoming Discord messages."""
    global command_router, model_manager, conversation_context
    
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
            
            # Step 1: Get raw response from Jarvis tools (with retry, validation, auto-followup)
            raw_response = await command_router.handle_message(message)
            
            # Step 2: Format the response using AI (if available)
            if model_manager and MODEL_AVAILABLE:
                try:
                    # Get context about what command was run
                    context = f"User asked: {message.content[:100]}"
                    if user_context:
                        context += f"\nPrevious context: {user_context[:100]}"
                    
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
            elif len(response) > 2000:  # Discord message limit
                response = response[:1900] + "...\n\n*Response truncated due to length*"
            
            # Send response
            await message.reply(response)
            
            # Store in conversation context
            if conversation_context:
                conversation_context.add_message(
                    user_id=message.author.id,
                    query=message.content,
                    response=response,
                    metadata={"timestamp": datetime.now().isoformat()}
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
    global session
    
    if session:
        await session.close()
        logger.info("Closed aiohttp session")


@client.event
async def on_disconnect():
    """Event handler for bot disconnection."""
    logger.info("Bot disconnected from Discord")
    await cleanup()


async def main():
    """Main entry point."""
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
    
    try:
        # Start the bot
        await client.start(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token")
        logger.error("Please check your DISCORD_BOT_TOKEN in the .env file")
    except discord.PrivilegedIntentsRequired as e:
        logger.error("Privileged intents not enabled!")
        logger.error("Go to https://discord.com/developers/applications/")
        logger.error("Select your bot -> Bot -> Privileged Gateway Intents")
        logger.error("Enable 'Message Content Intent'")
        logger.error("Then restart the bot")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
