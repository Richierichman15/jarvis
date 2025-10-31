"""Tool execution handler (agent system removed for performance)."""
import logging
from typing import Dict, Any

from discord.clients import RobustMCPClient, JarvisClientMCPClient
from discord.routers import DiscordCommandRouter

logger = logging.getLogger(__name__)


async def execute_intelligent_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    message,
    jarvis_client: JarvisClientMCPClient,
    command_router: DiscordCommandRouter,
    robust_mcp_client: RobustMCPClient = None
) -> str:
    """
    Execute a tool based on intelligent intent analysis.
    
    NOTE: Agent system has been removed for performance. This function directly
    routes to MCP clients instead of going through agents.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        message: Discord message object
        jarvis_client: HTTP MCP client
        command_router: Command router instance
        robust_mcp_client: Direct MCP client (optional)
        
    Returns:
        Tool execution result
    """
    try:
        # Determine server based on tool name
        # Note: Most tools go through "jarvis" server which proxies to other MCP servers
        server = "jarvis"  # Default server
        
        if tool_name.startswith("music_"):
            server = "local"
        elif tool_name.startswith("events_"):
            server = "local"
        elif tool_name.startswith("trading.trading.") or tool_name.startswith("trading.portfolio.") or tool_name.startswith("trading.paper."):
            server = "jarvis"
        elif tool_name.startswith("trading."):
            server = "jarvis"
        elif tool_name.startswith("system."):
            server = "jarvis"
        elif tool_name.startswith("jarvis_"):
            server = "jarvis"
        elif tool_name.startswith("search."):
            server = "jarvis"
        
        logger.info(f"🔧 Executing intelligent tool: {tool_name} on server: {server}")
        logger.info(f"📝 Arguments: {arguments}")
        
        # Handle local commands (music, events)
        if server == "local":
            return await command_router._handle_local_command(tool_name, arguments, message)
        
        # Try robust MCP client first (like CLI uses)
        if robust_mcp_client:
            try:
                result = await robust_mcp_client.call_tool(tool_name, arguments, server)
                if not result.startswith("Server '") and not result.startswith("Error calling tool:"):
                    logger.info(f"✅ Tool executed by robust MCP client: {tool_name}")
                    return result
                else:
                    logger.warning(f"Robust MCP client couldn't handle tool, falling back to HTTP: {result}")
            except Exception as e:
                logger.warning(f"Robust MCP client error, falling back to HTTP: {e}")
        
        # Final fallback to HTTP client
        if tool_name == "jarvis_chat":
            return await jarvis_client.natural_language_query(arguments.get("message", ""))
        else:
            return await jarvis_client.call_tool(tool_name, arguments, server)
            
    except Exception as e:
        logger.error(f"Error executing intelligent tool: {e}")
        return f"❌ Error executing tool: {str(e)}"

