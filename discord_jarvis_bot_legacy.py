#!/usr/bin/env python3
"""
Discord Bot for Jarvis MCP Integration

This bot listens to Discord messages and triggers the correct MCP tool through Jarvis.
It runs asynchronously and integrates with the local Jarvis MCP client.

Usage:
    python discord_jarvis_bot.py

Environment Variables:
    DISCORD_BOT_TOKEN - Discord bot token
    DISCORD_CLIENT_ID - Discord client ID
    DISCORD_CLIENT_SERVER - Discord server ID
    DISCORD_WEBHOOK_URL - Discord webhook URL (optional)
"""

import asyncio
import aiohttp
import discord
import logging
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_jarvis_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
JARVIS_URL = "http://localhost:3010/mcp/tools/call"  # Jarvis MCP HTTP server endpoint
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


class JarvisMCPClient:
    """Client for communicating with Jarvis MCP server."""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def query_jarvis(self, tool_name: str, arguments: dict = None) -> str:
        """
        Send a query to Jarvis MCP server and return the response.
        
        Args:
            tool_name: The name of the Jarvis tool to call
            arguments: The arguments for the tool
            
        Returns:
            Response from Jarvis or error message
        """
        try:
            if arguments is None:
                arguments = {}
                
            payload = {
                "name": tool_name,
                "arguments": arguments
            }
            
            logger.info(f"Sending query to Jarvis: {tool_name} with args: {arguments}")
            
            async with self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle Jarvis MCP response format
                    if isinstance(data, dict):
                        if 'result' in data and isinstance(data['result'], dict):
                            # Extract response from result object
                            result_data = data['result']
                            if 'response' in result_data and result_data['response'] is not None:
                                result = result_data['response']
                            elif 'content' in result_data and result_data['content'] is not None:
                                result = result_data['content']
                            elif 'message' in result_data and result_data['message'] is not None:
                                result = result_data['message']
                            elif 'status' in result_data and result_data['status'] is not None:
                                result = result_data['status']
                            elif 'tasks' in result_data and result_data['tasks'] is not None:
                                result = str(result_data['tasks'])
                            elif 'conversations' in result_data and result_data['conversations'] is not None:
                                result = str(result_data['conversations'])
                            elif 'error' in result_data and result_data['error'] is not None:
                                # Handle error responses
                                error_msg = result_data['error']
                                if 'search server not connected' in error_msg.lower():
                                    result = "🔍 **News Search Unavailable**\n\nThe search server is not connected. To enable news scanning, the search MCP server needs to be connected to Jarvis.\n\n**Available commands:**\n- `/status` - System status\n- `/memory` - Conversation history\n- `/tasks` - Task management"
                                elif 'web search tool not available' in error_msg.lower():
                                    result = "🌐 **Web Search Unavailable**\n\nWeb search functionality is not currently available.\n\n**Available commands:**\n- `/status` - System status\n- `/memory` - Conversation history\n- `/tasks` - Task management"
                                else:
                                    result = f"❌ **Error:** {error_msg}"
                            else:
                                # Handle null/empty responses
                                result = "No response received from Jarvis. The tool may not be properly configured."
                        elif 'response' in data and data['response'] is not None:
                            result = data['response']
                        elif 'content' in data and data['content'] is not None:
                            result = data['content']
                        elif 'message' in data and data['message'] is not None:
                            result = data['message']
                        else:
                            # If no standard field, try to extract meaningful content
                            result = str(data)
                    else:
                        result = str(data)
                    
                    logger.info(f"Received response from Jarvis: {result[:200]}...")
                    return result
                else:
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    logger.error(f"Jarvis API error: {error_msg}")
                    return f"Error communicating with Jarvis: {error_msg}"
                    
        except asyncio.TimeoutError:
            error_msg = "Request to Jarvis timed out"
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


class DiscordCommandRouter:
    """Routes Discord commands to appropriate Jarvis queries."""
    
    def __init__(self, jarvis_client: JarvisMCPClient):
        self.jarvis_client = jarvis_client
    
    def parse_command(self, message_content: str) -> tuple[str, dict]:
        """
        Parse Discord message and return appropriate Jarvis tool and arguments.
        
        Args:
            message_content: The Discord message content
            
        Returns:
            Tuple of (tool_name, arguments)
        """
        content = message_content.lower().strip()
        
        # Command routing
        if content.startswith('/news') or 'scan news' in content:
            return "jarvis_scan_news", {}
        elif content.startswith('/portfolio') or 'get portfolio' in content:
            return "jarvis_chat", {"message": "get trading portfolio"}
        elif content.startswith('/status') or 'get status' in content:
            return "jarvis_get_status", {}
        elif content.startswith('/memory') or 'get memory' in content:
            return "jarvis_get_memory", {"limit": 10}
        elif content.startswith('/tasks') or 'get tasks' in content:
            return "jarvis_get_tasks", {"status": "all"}
        elif content.startswith('/help') or 'help' in content:
            return "jarvis_chat", {"message": "show available commands and help"}
        else:
            # For any other message, try jarvis_chat
            return "jarvis_chat", {"message": message_content}
    
    async def handle_message(self, message: discord.Message) -> str:
        """
        Handle a Discord message and return Jarvis response.
        
        Args:
            message: The Discord message object
            
        Returns:
            Response from Jarvis
        """
        tool_name, arguments = self.parse_command(message.content)
        return await self.jarvis_client.query_jarvis(tool_name, arguments)


# Global instances
jarvis_client: Optional[JarvisMCPClient] = None
command_router: Optional[DiscordCommandRouter] = None


@client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global session, jarvis_client, command_router
    
    logger.info(f'{client.user} has connected to Discord!')
    logger.info(f'Bot is in {len(client.guilds)} guilds')
    
    # Create aiohttp session
    session = aiohttp.ClientSession()
    
    # Initialize Jarvis client and command router
    jarvis_client = JarvisMCPClient(JARVIS_URL, session)
    command_router = DiscordCommandRouter(jarvis_client)
    
    # Test connection to Jarvis
    try:
        test_response = await jarvis_client.query_jarvis("jarvis_get_status", {})
        logger.info(f"Jarvis connection test: {test_response[:100]}...")
    except Exception as e:
        logger.error(f"Failed to connect to Jarvis: {e}")


@client.event
async def on_message(message):
    """Event handler for incoming Discord messages."""
    global command_router
    
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
            # Get response from Jarvis
            response = await command_router.handle_message(message)
            
            # Handle empty or error responses
            if not response or response.strip() == "":
                response = "No response received from Jarvis."
            elif len(response) > 2000:  # Discord message limit
                response = response[:1900] + "...\n\n*Response truncated due to length*"
            
            # Send response
            await message.reply(response)
            
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
    
    # Validate configuration
    if DISCORD_BOT_TOKEN == 'YOUR_DISCORD_BOT_TOKEN_HERE' or not DISCORD_BOT_TOKEN:
        logger.error("Please set DISCORD_BOT_TOKEN environment variable")
        logger.error("Create a .env file with: DISCORD_BOT_TOKEN=your_actual_token_here")
        return
    
    logger.info("Starting Discord Jarvis Bot...")
    logger.info(f"Jarvis URL: {JARVIS_URL}")
    logger.info(f"Discord Server ID: {DISCORD_CLIENT_SERVER}")
    
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
