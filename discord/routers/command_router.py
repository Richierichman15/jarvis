"""Command router for Discord bot."""
import asyncio
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import discord

from discord.clients.http_client import JarvisClientMCPClient

logger = logging.getLogger(__name__)


class DiscordCommandRouter:
    """Routes Discord commands to appropriate Jarvis tools."""
    
    def __init__(self, jarvis_client: JarvisClientMCPClient, 
                 event_listener=None, music_player=None):
        self.jarvis_client = jarvis_client
        self.event_listener = event_listener
        self.music_player = music_player
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """Detect the user's intent and extract key information."""
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
    
    def validate_response_quality(self, response: str, query: str) -> Tuple[bool, Optional[str]]:
        """Check if response adequately answers the query."""
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Check 1: User asked for a list, did we provide one?
        if "list" in query_lower or "top" in query_lower or "what are" in query_lower:
            has_list_formatting = bool(re.search(r'(\n-|\n\d+\.|\n•|^\d+\.)', response, re.MULTILINE))
            if not has_list_formatting and len(response) < 300:
                return False, "Response should include a formatted list with details"
        
        # Check 2: User asked for specific data, did we provide it?
        if any(word in query_lower for word in ['what are', 'which', 'details', 'explain']):
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
        
        # Check 5: For search queries, check for irrelevant results
        if 'crypto' in query_lower or 'coin' in query_lower:
            if 'casino' in response_lower or 'gambling' in response_lower:
                return False, "Response contains irrelevant gambling/casino content"
        
        return True, None
    
    async def _handle_local_command(self, tool_name: str, arguments: Dict[str, Any], message: discord.Message) -> str:
        """Handle local commands (event management and music) that don't go through MCP."""
        # Handle music commands
        if tool_name.startswith("music_"):
            if not self.music_player:
                return "❌ Music player is not initialized."
            return await self._handle_music_command(tool_name, arguments, message)
        
        # Handle event commands
        if not self.event_listener:
            return "❌ Event listener is not initialized. Set EVENT_NOTIFICATION_CHANNEL_ID in your .env file and restart the bot."
        
        try:
            if tool_name == "events_start_monitoring":
                success = await self.event_listener.start_monitoring()
                return "✅ Event monitoring started! You'll receive real-time trading notifications in this channel." if success else "⚠️ Event monitoring is already running."
            
            elif tool_name == "events_stop_monitoring":
                success = await self.event_listener.stop_monitoring()
                return "🛑 Event monitoring stopped. No more notifications will be sent." if success else "⚠️ Event monitoring is not currently running."
            
            elif tool_name == "events_get_statistics":
                stats = self.event_listener.get_statistics()
                total = stats["total_events"]
                by_type = stats["by_type"]
                is_monitoring = stats["is_monitoring"]
                
                status_emoji = "🟢" if is_monitoring else "🔴"
                response = f"📊 **Event Statistics**\n\n"
                response += f"Status: {status_emoji} {'Monitoring' if is_monitoring else 'Stopped'}\n"
                response += f"Total Events: **{total}**\n\n**By Type:**\n"
                
                for event_type, count in by_type.items():
                    if count > 0:
                        response += f"• {event_type}: {count}\n"
                
                return response
            
            elif tool_name == "events_get_history":
                limit = arguments.get("limit", 10)
                history = self.event_listener.get_history(limit)
                
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
                
                await self.event_listener.handle_event(test_event)
                return f"✅ Test event sent: **{event_type}**\nCheck the notification channel for the message."
            
            elif tool_name == "events_check_markets":
                return "🔍 Manually triggering market price check... (This would call the MCP tool)"
            
            else:
                return f"❌ Unknown event command: {tool_name}"
        
        except Exception as e:
            logger.error(f"Error handling local command: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    async def _handle_music_command(self, tool_name: str, arguments: Dict[str, Any], message: discord.Message) -> str:
        """Handle music commands routed to the music player."""
        try:
            if tool_name == "music_play":
                song_name = arguments.get("song_name")
                return await self.music_player.play_song(message.author, message.channel, song_name)
            
            elif tool_name == "music_play_or_resume":
                guild_id = message.author.guild.id
                if guild_id in self.music_player.is_paused and self.music_player.is_paused[guild_id]:
                    return await self.music_player.resume(message.author, message.channel)
                else:
                    return await self.music_player.play_random(message.author, message.channel, count=5)
            
            elif tool_name == "music_pause":
                return await self.music_player.pause(message.author, message.channel)
            
            elif tool_name == "music_resume":
                return await self.music_player.resume(message.author, message.channel)
            
            elif tool_name == "music_stop":
                return await self.music_player.stop(message.author, message.channel)
            
            elif tool_name == "music_skip":
                return await self.music_player.skip(message.author, message.channel)
            
            elif tool_name == "music_queue_add":
                song_name = arguments.get("song_name")
                if not song_name:
                    return "❌ Please specify a song name to add to queue"
                return await self.music_player.add_to_queue(message.author, message.channel, song_name)
            
            elif tool_name == "music_queue_view":
                return await self.music_player.show_queue(message.author, message.channel)
            
            elif tool_name == "music_now_playing":
                return await self.music_player.now_playing(message.author, message.channel)
            
            elif tool_name == "music_leave":
                return await self.music_player.leave(message.author, message.channel)
            
            elif tool_name == "music_list_songs":
                return await self.music_player.list_available_songs()
            
            elif tool_name == "music_random":
                return await self.music_player.play_random(message.author, message.channel)
            
            elif tool_name == "music_search":
                keyword = arguments.get("keyword")
                if not keyword:
                    return "❌ Please specify a search keyword"
                return await self.music_player.search_songs(keyword)
            
            elif tool_name == "music_clear_queue":
                return await self.music_player.clear_queue(message.author, message.channel)
            
            elif tool_name == "music_remove_from_queue":
                position = arguments.get("position")
                if not position:
                    return "❌ Please specify a position to remove"
                return await self.music_player.remove_from_queue(message.author, message.channel, position)
            
            elif tool_name == "music_mcp_queue":
                return await self.music_player.get_mcp_queue()
            
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
                refined_query = "top 10 web3 cryptocurrencies 2025 by market cap coinmarketcap"
                logger.info(f"Auto-followup: Searching for '{refined_query}'")
                try:
                    return await self.jarvis_client.call_tool("jarvis_web_search", {"query": refined_query}, "jarvis")
                except Exception as e:
                    logger.warning(f"Auto-followup failed: {e}")
                    return None
        
        # If asking about tariffs and response is too brief
        if 'tariff' in query_lower and len(initial_response) < 300:
            refined_query = "new tariffs imposed 2025 Trump administration details list"
            logger.info(f"Auto-followup: Searching for '{refined_query}'")
            try:
                return await self.jarvis_client.call_tool("jarvis_web_search", {"query": refined_query}, "jarvis")
            except Exception as e:
                logger.warning(f"Auto-followup failed: {e}")
                return None
        
        return None
    
    def parse_command(self, message_content: str) -> Tuple[str, dict, str]:
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
        
        # Trading Commands
        elif content.startswith('/balance') or 'get balance' in content:
            return "trading.trading.get_balance", {}, "jarvis"
        elif content.startswith('/price') or 'get price' in content:
            symbol = message_content.replace('/price', '').replace('get price', '').strip().upper()
            if not symbol:
                return "jarvis_chat", {"message": "Please specify a symbol for price lookup. Example: /price BTC"}, "jarvis"
            if '/' not in symbol:
                symbol = f"{symbol}/USD"
            return "trading.trading.get_price", {"symbol": symbol}, "jarvis"
        elif content.startswith('/ohlcv') or 'ohlcv data' in content:
            symbol = message_content.replace('/ohlcv', '').replace('ohlcv data', '').strip().upper()
            if not symbol:
                return "jarvis_chat", {"message": "Please specify a symbol for OHLCV data. Example: /ohlcv BTC"}, "jarvis"
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
        
        # Portfolio Commands
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
            match = re.search(r'history\s+(\d+)', content)
            limit = int(match.group(1)) if match else 10
            return "events_get_history", {"limit": limit}, "local"
        elif content.startswith('/events test'):
            test_type = content.replace('/events test', '').strip()
            return "events_test_event", {"type": test_type if test_type else "market_alert"}, "local"
        elif content.startswith('/events check'):
            return "events_check_markets", {}, "local"
        
        # Music Commands
        elif content.startswith('/play'):
            song_name = message_content.replace('/play', '').strip()
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
            match = re.search(r'remove\s+(\d+)', content)
            if match:
                position = int(match.group(1))
                return "music_remove_from_queue", {"position": position}, "local"
            else:
                return "music_queue_view", {}, "local"
        elif content.startswith('/queue'):
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
            keyword = message_content.replace('/findsong', '').replace('/find', '').strip()
            if not keyword:
                return "music_list_songs", {}, "local"
            return "music_search", {"keyword": keyword}, "local"
        elif content.startswith('/mcpqueue'):
            return "music_mcp_queue", {}, "local"
        elif content.startswith('/leave') or content.startswith('/disconnect'):
            return "music_leave", {}, "local"
        elif content.startswith('/volume'):
            match = re.search(r'volume\s+(\d+)', content)
            if match:
                volume = int(match.group(1))
                return "music_volume", {"volume": volume}, "local"
            else:
                return "music_volume", {}, "local"
        elif content.startswith('/join'):
            return "music_join", {}, "local"
        
        # Search Commands
        elif content.startswith('/search') or 'web search' in content:
            query = message_content.replace('/search', '').replace('web search', '').strip()
            if not query:
                query = "latest technology news"
            
            intent = self.detect_query_intent(query)
            refined_query = self.refine_search_query(query, intent)
            logger.info(f"Search query refined: '{query}' -> '{refined_query}'")
            return "jarvis_web_search", {"query": refined_query}, "jarvis"
        
        # Help and Chat
        elif content.startswith('/help') or 'help' in content:
            return "jarvis_chat", {"message": "show available commands and help"}, "jarvis"
        elif any(word in content for word in ['date', 'time', 'today', 'what day', 'what time']):
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
        
        # Handle local commands
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
                    result = await self.jarvis_client.natural_language_query(arguments["query"])
                else:
                    result = await self.jarvis_client.call_tool(tool_name, arguments, server)
                
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a recoverable error
                if any(keyword in error_msg for keyword in ['closed', 'session', 'connection', 'timeout']):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Recoverable error on attempt {attempt + 1}/{max_retries}: {e}")
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        result = f"❌ Connection error after {max_retries} attempts. Please try again in a moment."
                        break
                else:
                    logger.error(f"Non-recoverable error: {e}")
                    result = f"❌ Error: {str(e)}"
                    break
        
        # Delete progress message if it was sent
        if progress_msg:
            try:
                await progress_msg.delete()
            except:
                pass
        
        # Validate response quality
        if result and not result.startswith("❌"):
            is_valid, reason = self.validate_response_quality(result, message.content)
            
            # If response is poor quality, try auto-followup
            if not is_valid:
                logger.info(f"Response validation failed: {reason}. Attempting auto-followup...")
                followup_result = await self.auto_followup(result, message.content)
                
                if followup_result:
                    result = f"{result}\n\n**📊 Additional Information:**\n{followup_result}"
                    logger.info("Auto-followup successful")
                else:
                    logger.info("Auto-followup didn't improve result, using original")
        
        return result or "No response received from Jarvis."

