#!/usr/bin/env python3
"""
Discord Bot Microservice for Jarvis

This is the refactored microservice version of discord_jarvis_bot_full.py.
Agent system has been removed for performance improvements.

Usage:
    python -m discord.main
"""

import asyncio
import aiohttp
import logging
import sys
import importlib
from datetime import datetime
from typing import Optional

# CRITICAL: Import the actual discord.py library FIRST and ensure it's in sys.modules
# This must happen before importing our discord package
import discord as discord_lib  # The actual discord.py library
sys.modules['discord'] = discord_lib  # Ensure it's the default

# Now import our discord package (config module)
# Since discord library is already in sys.modules, modules that import discord will get the library
import discord as _discord_pkg  # Import our package but keep it as _discord_pkg
from discord import config

# Restore discord to refer to the library (not our package)
discord = discord_lib
sys.modules['discord'] = discord_lib

# Now that discord library is properly set up, trigger config availability checks
config._ensure_checks_done()

# Import components
from discord.clients import RobustMCPClient, JarvisClientMCPClient
from discord.routers import DiscordCommandRouter
from discord.services import ConversationContext
from discord.utils import send_long_message, send_error_webhook
from discord.handlers.tool_executor import execute_intelligent_tool

# Import optional components
# The discord library should already be in sys.modules from config.py
try:
    from jarvis_event_listener import TradingEventListener
except ImportError:
    TradingEventListener = None

try:
    from jarvis_music_player import MusicPlayer
except ImportError:
    MusicPlayer = None

try:
    from jarvis.intelligence import IntentRouter
except ImportError:
    IntentRouter = None

try:
    from jarvis.models.model_manager import ModelManager
    from formatter import format_response
except ImportError:
    ModelManager = None
    format_response = None

try:
    from server_manager import ServerManager
except ImportError:
    ServerManager = None

logger = logging.getLogger(__name__)

# Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create Discord client
client = discord.Client(
    intents=intents,
    heartbeat_timeout=60.0,
    max_messages=1000,
    chunk_guilds_at_startup=False,
    member_cache_flags=discord.MemberCacheFlags.none()
)

# Global instances
session: Optional[aiohttp.ClientSession] = None
jarvis_client: Optional[JarvisClientMCPClient] = None
command_router: Optional[DiscordCommandRouter] = None
model_manager: Optional[ModelManager] = None
conversation_context: Optional[ConversationContext] = None
event_listener: Optional[TradingEventListener] = None
music_player: Optional[MusicPlayer] = None
intent_router: Optional[IntentRouter] = None
server_manager: Optional[ServerManager] = None
robust_mcp_client: Optional[RobustMCPClient] = None


@client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global session, jarvis_client, command_router, model_manager
    global conversation_context, event_listener, music_player
    global intent_router, server_manager, robust_mcp_client
    
    logger.info(f'{client.user} has connected to Discord!')
    logger.info(f'Bot is in {len(client.guilds)} guilds')
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize server manager
    if config.SERVER_MANAGER_AVAILABLE and ServerManager:
        try:
            server_manager = ServerManager(config.JARVIS_CLIENT_URL)
            logger.info("🔧 Server manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize server manager: {e}")
    
    # Initialize Robust MCP Client (direct MCP connections)
    if config.MCP_CLIENT_AVAILABLE:
        try:
            robust_mcp_client = RobustMCPClient()
            await robust_mcp_client.start()
            logger.info("🔗 Robust MCP Client started")
        except Exception as e:
            logger.warning(f"⚠️ Could not start Robust MCP Client: {e}")
            robust_mcp_client = None
    
    # Initialize Jarvis HTTP client and command router
    try:
        jarvis_client = JarvisClientMCPClient(config.JARVIS_CLIENT_URL, session)
        
        # Initialize optional components for command router
        event_listener_inst = None
        if config.EVENT_LISTENER_AVAILABLE and config.EVENT_NOTIFICATION_CHANNEL_ID:
            try:
                channel_id = int(config.EVENT_NOTIFICATION_CHANNEL_ID)
                notification_channel = client.get_channel(channel_id)
                if notification_channel:
                    event_listener_inst = TradingEventListener(config.JARVIS_CLIENT_URL, notification_channel)
                    logger.info(f"✅ Event listener initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize event listener: {e}")
        
        music_player_inst = None
        if config.MUSIC_PLAYER_AVAILABLE and MusicPlayer:
            try:
                music_player_inst = MusicPlayer(jarvis_client)
                logger.info("✅ Music player initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize music player: {e}")
        
        command_router = DiscordCommandRouter(
            jarvis_client,
            event_listener=event_listener_inst,
            music_player=music_player_inst
        )
        event_listener = event_listener_inst
        music_player = music_player_inst
        
        logger.info("🔧 Jarvis client and command router initialized")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Jarvis client: {e}")
        jarvis_client = None
        command_router = None
    
    # Initialize intelligence core
    if config.INTELLIGENCE_AVAILABLE and IntentRouter:
        try:
            intent_router = IntentRouter()
            logger.info("🧠 Intelligence core initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize intelligence core: {e}")
            intent_router = None
    
    # Initialize model manager for AI-powered response formatting
    if config.MODEL_AVAILABLE and ModelManager:
        try:
            model_manager = ModelManager()
            logger.info("🤖 Model manager initialized")
            
            # Check Ollama availability
            if model_manager.ollama_model:
                try:
                    await model_manager.check_ollama_availability()
                    if model_manager.ollama_available:
                        logger.info(f"✅ Ollama is available: {model_manager.ollama_model.model_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Error checking Ollama availability: {e}")
            
            # Verify OpenAI availability
            if model_manager.openai_available and model_manager.openai_model:
                logger.info("✅ OpenAI GPT-4o-mini is available")
            elif model_manager.openai_model is None:
                logger.warning("⚠️ OpenAI model not initialized - check OPENAI_KEY or OPENAI_API_KEY")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize model manager: {e}")
            model_manager = None
    
    # Initialize conversation context
    try:
        conversation_context = ConversationContext(max_history=5)
        logger.info("💬 Conversation context initialized")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize conversation context: {e}")
        conversation_context = None
    
    # Get available tools
    try:
        if jarvis_client:
            tools = await jarvis_client.get_available_tools()
            if tools:
                logger.info("Available tools by server:")
                for server, server_tools in tools.items():
                    logger.info(f"  {server}: {len(server_tools)} tools")
    except Exception as e:
        logger.error(f"Failed to get available tools: {e}")


@client.event
async def on_message(message):
    """Event handler for incoming Discord messages."""
    global command_router, model_manager, conversation_context, intent_router
    global jarvis_client, robust_mcp_client
    
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Only respond to messages in the configured server (if specified)
    if config.DISCORD_CLIENT_SERVER and config.DISCORD_CLIENT_SERVER != 'YOUR_DISCORD_SERVER_ID_HERE':
        if str(message.guild.id) != config.DISCORD_CLIENT_SERVER:
            return
    
    logger.info(f"Received message from {message.author}: {message.content}")
    
    try:
        async with message.channel.typing():
            # Get conversation context
            user_context = ""
            if conversation_context:
                user_context = conversation_context.get_context(message.author.id)
            
            # Step 1: Intelligent intent analysis (if available)
            raw_response = None
            intent_result = None
            
            if intent_router and config.INTELLIGENCE_AVAILABLE:
                try:
                    intent_result = await intent_router.analyze_intent(
                        message.content,
                        str(message.author.id),
                        str(message.channel.id)
                    )
                    
                    logger.info(f"🧠 Intent: {intent_result.intent_type.value} (confidence: {intent_result.confidence:.2f})")
                    logger.info(f"🔧 Tool: {intent_result.tool_name}")
                    
                    # Execute tool (agent system removed - direct MCP routing)
                    raw_response = await execute_intelligent_tool(
                        intent_result.tool_name,
                        intent_result.arguments,
                        message,
                        jarvis_client,
                        command_router,
                        robust_mcp_client
                    )
                    
                except Exception as e:
                    logger.warning(f"Intelligent routing failed, falling back to command router: {e}")
                    intent_result = None
            
            # Step 2: Fallback to command router
            if raw_response is None:
                if command_router:
                    raw_response = await command_router.handle_message(message)
                else:
                    raw_response = "❌ Bot is still initializing. Please wait a moment and try again."
            
            # Step 3: Format response using AI (if available)
            if model_manager and config.MODEL_AVAILABLE and format_response:
                try:
                    context = f"User asked: {message.content[:100]}"
                    if user_context:
                        context += f"\nPrevious context: {user_context[:100]}"
                    if intent_result:
                        context += f"\nIntent: {intent_result.intent_type.value} (confidence: {intent_result.confidence:.2f})"
                    
                    formatted_response = await format_response(
                        raw_response=raw_response,
                        model_manager=model_manager,
                        context=context
                    )
                    response = formatted_response
                    logger.info("✨ Response formatted by AI")
                except Exception as format_error:
                    logger.warning(f"Formatting failed, using raw response: {format_error}")
                    response = raw_response
            else:
                response = raw_response
            
            # Handle empty responses
            if not response or response.strip() == "":
                response = "No response received from Jarvis."
            
            # Send response
            await send_long_message(message, response)
            
            # Store in conversation context
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
            
            logger.info(f"Sent response to {message.author}: {response[:100]}...")
            
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        await message.reply("Sorry, I encountered an error processing your request.")
        
        # Send error to webhook if configured
        if config.DISCORD_WEBHOOK_URL and session:
            await send_error_webhook(error_msg, message.content, session)


@client.event
async def on_disconnect():
    """Event handler for bot disconnection."""
    global server_manager, robust_mcp_client
    
    logger.info("Bot disconnected from Discord")
    
    # Stop robust MCP client
    if robust_mcp_client:
        try:
            await robust_mcp_client.stop()
            logger.info("🛑 Robust MCP Client stopped")
        except Exception as e:
            logger.error(f"Error stopping robust MCP client: {e}")
    
    # Stop managed servers
    if server_manager and config.SERVER_MANAGER_AVAILABLE:
        try:
            await server_manager.stop_all_servers()
        except Exception as e:
            logger.error(f"Error stopping servers: {e}")


@client.event
async def on_resumed():
    """Event handler for when the bot resumes connection."""
    logger.info("Bot connection resumed successfully")


async def cleanup():
    """Cleanup resources on shutdown."""
    global session, event_listener, music_player
    
    if event_listener:
        try:
            await event_listener.cleanup()
            logger.info("Event listener cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up event listener: {e}")
    
    if music_player:
        try:
            await music_player.cleanup()
            logger.info("Music player cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up music player: {e}")
    
    if session:
        await session.close()
        logger.info("Closed aiohttp session")


async def main():
    """Main entry point."""
    logger.info("Environment variables loaded:")
    logger.info(f"DISCORD_BOT_TOKEN: {'SET' if config.DISCORD_BOT_TOKEN and config.DISCORD_BOT_TOKEN != 'YOUR_DISCORD_BOT_TOKEN_HERE' else 'NOT SET'}")
    logger.info(f"JARVIS_CLIENT_URL: {config.JARVIS_CLIENT_URL}")
    
    # Validate configuration
    if config.DISCORD_BOT_TOKEN == 'YOUR_DISCORD_BOT_TOKEN_HERE' or not config.DISCORD_BOT_TOKEN:
        logger.error("Please set DISCORD_BOT_TOKEN environment variable")
        return
    
    logger.info("Starting Discord Jarvis Bot (Microservice)...")
    
    try:
        await client.start(config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token")
    except discord.PrivilegedIntentsRequired:
        logger.error("Privileged intents not enabled! Enable 'Message Content Intent' in Discord Developer Portal")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

