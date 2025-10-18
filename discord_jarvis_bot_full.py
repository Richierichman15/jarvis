#!/usr/bin/env python3
"""
Full-Featured Discord Bot for Jarvis MCP Integration - Fixed Auto-Connection
"""

import asyncio
import aiohttp
import discord
import logging
import os
import sys
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

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

# Configuration - Fixed port consistency
JARVIS_CLIENT_URL = os.getenv('JARVIS_CLIENT_URL', 'http://localhost:3012')  # Consistent port
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN_HERE')
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', 'YOUR_DISCORD_CLIENT_ID_HERE')
DISCORD_CLIENT_SERVER = os.getenv('DISCORD_CLIENT_SERVER', 'YOUR_DISCORD_SERVER_ID_HERE')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create Discord client with enhanced connection settings
client = discord.Client(
    intents=intents,
    heartbeat_timeout=60.0,
    max_messages=1000,
    chunk_guilds_at_startup=False,
    member_cache_flags=discord.MemberCacheFlags.none()
)

# Global aiohttp session for connection reuse
session: Optional[aiohttp.ClientSession] = None


class ImprovedServerManager:
    """Enhanced server manager with better startup coordination."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.startup_timeout = 30  # seconds
        self.check_interval = 2  # seconds
        
    async def wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for the HTTP server to be available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as temp_session:
                    async with temp_session.get(
                        f"{self.base_url}/servers",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            self.logger.info("✅ HTTP server is available")
                            return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            
            await asyncio.sleep(self.check_interval)
        
        return False
    
    async def ensure_servers_running(self) -> Dict[str, bool]:
        """Ensure all necessary servers are running."""
        results = {}
        
        # First, wait for HTTP server to be available
        if not await self.wait_for_server():
            self.logger.error("❌ HTTP server is not available after timeout")
            return {"http_server": False}
        
        # Check which servers are already running
        try:
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.get(
                    f"{self.base_url}/servers",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for server_name, server_info in data.items():
                            is_connected = server_info.get("connected", False)
                            results[server_name] = is_connected
                            
                            if not is_connected:
                                # Try to start this server
                                self.logger.info(f"🔄 Attempting to start {server_name} server...")
                                success = await self.start_server(server_name)
                                results[server_name] = success
                                
                                if success:
                                    self.logger.info(f"✅ Started {server_name} server")
                                else:
                                    self.logger.warning(f"⚠️ Failed to start {server_name} server")
                    else:
                        self.logger.error(f"Failed to get server status: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error checking servers: {e}")
        
        return results
    
    async def start_server(self, server_name: str) -> bool:
        """Start a specific server by name."""
        try:
            # Map server names to their startup commands
            server_configs = {
                "jarvis": {
                    "command": sys.executable,
                    "args": ["-u", "run_mcp_server.py", "Boss"]
                },
                "trading": {
                    "command": sys.executable,
                    "args": ["-u", "run_mcp_server.py"]
                },
                "search": {
                    "command": sys.executable,
                    "args": ["-u", "search/mcp_server.py"]
                },
                "system": {
                    "command": sys.executable,
                    "args": ["-u", "system/mcp_server.py"]
                }
            }
            
            config = server_configs.get(server_name)
            if not config:
                self.logger.warning(f"Unknown server: {server_name}")
                return False
            
            # Send start command to HTTP server
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.post(
                    f"{self.base_url}/servers/{server_name}/start",
                    json=config,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status in [200, 201]:
                        # Wait a bit for server to initialize
                        await asyncio.sleep(3)
                        return True
                    else:
                        self.logger.error(f"Failed to start {server_name}: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error starting {server_name}: {e}")
            return False


class JarvisClientMCPClient:
    """Enhanced client for communicating with Jarvis Client HTTP Server."""
    
    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.base_url = base_url
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.available_tools: Dict[str, Any] = {}
        self.connection_retries = 0
        self.max_connection_retries = 5
        self.last_health_check = 0
        self.health_check_interval = 30
        self.server_manager = ImprovedServerManager(base_url)
    
    async def initialize(self) -> bool:
        """Initialize connection and ensure servers are running."""
        try:
            # Ensure servers are running
            self.logger.info("🚀 Initializing MCP connection and servers...")
            server_status = await self.server_manager.ensure_servers_running()
            
            # Log server status
            for server, is_running in server_status.items():
                status_icon = "✅" if is_running else "❌"
                self.logger.info(f"  {server}: {status_icon}")
            
            # Get available tools
            await self.get_available_tools()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if the server is healthy and responsive."""
        try:
            current_time = time.time()
            if current_time - self.last_health_check < self.health_check_interval:
                return True
            
            async with self.session.get(
                f"{self.base_url}/servers",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                self.last_health_check = current_time
                if response.status == 200:
                    self.connection_retries = 0
                    
                    # Check if any servers are disconnected
                    data = await response.json()
                    disconnected = [name for name, info in data.items() 
                                  if not info.get("connected", False)]
                    
                    if disconnected:
                        self.logger.warning(f"⚠️ Disconnected servers: {disconnected}")
                        # Try to reconnect them
                        for server_name in disconnected:
                            self.logger.info(f"🔄 Attempting to reconnect {server_name}...")
                            await self.server_manager.start_server(server_name)
                    
                    return True
                else:
                    self.logger.warning(f"Health check failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.warning(f"Health check error: {e}")
            return False

    async def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools from all connected servers."""
        try:
            # Perform health check first
            if not await self.health_check():
                self.logger.warning("Server health check failed, attempting to reconnect...")
                await self.initialize()
            
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
                    self.logger.info(f"Loaded {len(tools_data)} tools from {len(tools_by_server)} servers")
                    return tools_by_server
                else:
                    self.logger.error(f"Failed to get tools: HTTP {response.status}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error getting tools: {e}")
            return {}
    
    async def call_tool(self, tool_name: str, arguments: dict = None, server: str = None) -> str:
        """Call a tool with automatic reconnection on failure."""
        if arguments is None:
            arguments = {}
            
        payload = {
            "tool": tool_name,
            "args": arguments
        }
        
        if server:
            payload["server"] = server
        
        self.logger.info(f"Calling tool: {tool_name} on server: {server or 'default'}")
        
        # Enhanced retry logic with reconnection
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Check server health before making request
                if attempt > 0:
                    if not await self.health_check():
                        self.logger.warning(f"Server health check failed on attempt {attempt + 1}")
                        # Try to reinitialize connection
                        await self.initialize()
                        await asyncio.sleep(2 ** attempt)
                
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
                            
                            # If server not connected, try to reconnect
                            if 'not connected' in error_msg.lower():
                                self.logger.warning(f"Server not connected, attempting to reconnect...")
                                await self.initialize()
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                            
                            self.logger.error(f"Tool call failed: {error_msg}")
                            return f"Error: {error_msg}"
                    else:
                        error_msg = await response.text()
                        self.logger.error(f"HTTP {response.status}: {error_msg}")
                        
                        # Check if it's a recoverable error
                        if response.status in [502, 503, 504] and attempt < max_retries - 1:
                            self.logger.warning(f"Recoverable HTTP error {response.status}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                            continue
                        
                        return f"Error: HTTP {response.status} - {error_msg}"
                        
            except asyncio.TimeoutError:
                error_msg = f"Request timed out (attempt {attempt + 1}/{max_retries})"
                self.logger.error(error_msg)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
            except aiohttp.ClientError as e:
                error_msg = f"Network error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                self.logger.error(error_msg)
                
                # Try to reinitialize on network errors
                if attempt < max_retries - 1:
                    await self.initialize()
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
            except Exception as e:
                error_msg = f"Unexpected error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                self.logger.error(error_msg)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return error_msg
        
        return f"Error: Failed to call tool after {max_retries} attempts"
    
    async def natural_language_query(self, query: str) -> str:
        """Send a natural language query to the Jarvis Client."""
        try:
            payload = {"message": query}
            
            self.logger.info(f"Sending natural language query: {query}")
            
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
                    self.logger.error(f"Natural language query failed: HTTP {response.status} - {error_msg}")
                    return f"Error: {error_msg}"
                    
        except Exception as e:
            error_msg = f"Natural language query error: {str(e)}"
            self.logger.error(error_msg)
            return error_msg


# Global instances
jarvis_client: Optional[JarvisClientMCPClient] = None


async def startup_sequence():
    """Startup sequence to ensure servers are running before bot connects."""
    global jarvis_client, session
    
    max_startup_attempts = 3
    
    for attempt in range(max_startup_attempts):
        try:
            self.logger.info(f"🚀 Startup attempt {attempt + 1}/{max_startup_attempts}")
            
            # Create aiohttp session if not exists
            if not session:
                session = aiohttp.ClientSession()
            
            # Initialize Jarvis client
            if not jarvis_client:
                jarvis_client = JarvisClientMCPClient(JARVIS_CLIENT_URL, session)
            
            # Initialize connection and servers
            if await jarvis_client.initialize():
                self.logger.info("✅ Startup sequence completed successfully")
                return True
            else:
                self.logger.warning(f"⚠️ Startup attempt {attempt + 1} failed")
                
                if attempt < max_startup_attempts - 1:
                    wait_time = 5 * (attempt + 1)
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                    
        except Exception as e:
            self.logger.error(f"Startup error: {e}")
            if attempt < max_startup_attempts - 1:
                await asyncio.sleep(5)
    
    return False


@client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global session, jarvis_client
    
    self.logger.info(f'{client.user} has connected to Discord!')
    self.logger.info(f'Bot is in {len(client.guilds)} guilds')
    
    # Run startup sequence
    if await startup_sequence():
        self.logger.info("✅ Bot fully initialized and ready")
    else:
        self.logger.error("❌ Failed to complete startup sequence")
        self.logger.info("Bot will continue but some features may not work")


async def connection_monitor():
    """Enhanced connection monitor with auto-reconnection."""
    global jarvis_client
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if jarvis_client and client.is_ready():
                # Perform health check
                if not await jarvis_client.health_check():
                    self.logger.warning("⚠️ Health check failed, attempting to reconnect...")
                    
                    # Try to reinitialize
                    if await jarvis_client.initialize():
                        self.logger.info("✅ Successfully reconnected")
                    else:
                        self.logger.error("❌ Failed to reconnect")
                        
        except Exception as e:
            self.logger.error(f"Error in connection monitor: {e}")
            await asyncio.sleep(30)


async def main():
    """Main entry point with enhanced error handling."""
    # Validate configuration
    if DISCORD_BOT_TOKEN == 'YOUR_DISCORD_BOT_TOKEN_HERE' or not DISCORD_BOT_TOKEN:
        self.logger.error("Please set DISCORD_BOT_TOKEN environment variable")
        return
    
    self.logger.info("Starting Discord Jarvis Bot with Auto-Connection...")
    self.logger.info(f"Jarvis Client URL: {JARVIS_CLIENT_URL}")
    
    # Start connection monitor task
    monitor_task = asyncio.create_task(connection_monitor())
    
    try:
        # Start the bot
        await client.start(DISCORD_BOT_TOKEN)
                
    except discord.LoginFailure:
        self.logger.error("Invalid Discord bot token")
    except discord.PrivilegedIntentsRequired:
        self.logger.error("Privileged intents not enabled!")
        self.logger.error("Enable 'Message Content Intent' in Discord Developer Portal")
    except Exception as e:
        self.logger.error(f"Fatal error: {e}")
    finally:
        # Cleanup
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        if session:
            await session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        self.logger.info("Bot stopped by user")
    except Exception as e:
        self.logger.error(f"Fatal error: {e}")