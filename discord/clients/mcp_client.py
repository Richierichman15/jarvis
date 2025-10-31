"""Robust MCP client for direct server connections."""
import asyncio
import sys
import logging
from typing import Dict, Any, Optional

# Import config from discord_bot namespace
try:
    from discord_bot import config
except ImportError:
    # Fallback: try relative import if running as normal package
    try:
        from .. import config
    except ImportError:
        # Last resort: try importing discord_bot.config directly
        import sys
        if 'discord_bot.config' in sys.modules:
            import discord_bot.config as config
        else:
            raise ImportError("Could not import config module")
MCP_CLIENT_AVAILABLE = config.MCP_CLIENT_AVAILABLE

if MCP_CLIENT_AVAILABLE:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class RobustMCPClient:
    """Robust MCP client based on CLI approach for reliable server connections."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self._server_tasks: Dict[str, asyncio.Task] = {}
        self.tools: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start MCP servers using the robust CLI approach."""
        if not MCP_CLIENT_AVAILABLE:
            self.logger.warning("MCP client not available")
            return
            
        try:
            # Start the main jarvis server
            await self._spawn_and_hold("jarvis", StdioServerParameters(
                command=sys.executable,
                args=["-u", "run_mcp_server.py", "Boss"]
            ))
            
            # Start trading server if available
            try:
                await self._spawn_and_hold("trading", StdioServerParameters(
                    command=sys.executable,
                    args=["-u", "run_mcp_server.py"]
                ))
            except Exception as e:
                self.logger.warning(f"Could not start trading server: {e}")
            
            # Start search server if available
            try:
                await self._spawn_and_hold("search", StdioServerParameters(
                    command=sys.executable,
                    args=["-u", "search/mcp_server.py"]
                ))
            except Exception as e:
                self.logger.warning(f"Could not start search server: {e}")
            
            # Start system server if available
            try:
                await self._spawn_and_hold("system", StdioServerParameters(
                    command="C:\\Program Files\\Python313\\python.exe",
                    args=["-u", "E:/Richie/github/system/system_server.py"],
                    cwd="E:/Richie/github/system"
                ))
            except Exception as e:
                self.logger.warning(f"Could not start system server: {e}")
                
            self.logger.info(f"✅ Connected to {len(self.sessions)} MCP servers: {list(self.sessions.keys())}")
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP servers: {e}")
    
    async def _spawn_and_hold(self, alias: str, params: StdioServerParameters) -> None:
        """Spawn a subprocess MCP server and hold its session open under alias."""
        if alias in self.sessions:
            self.logger.warning(f"Server '{alias}' already connected")
            return
            
        ready_fut: asyncio.Future = asyncio.get_event_loop().create_future()

        async def runner():
            try:
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        self.sessions[alias] = session
                        if not ready_fut.done():
                            ready_fut.set_result(True)
                        # Hold open until cancelled
                        try:
                            while True:
                                await asyncio.sleep(3600)
                        except asyncio.CancelledError:
                            pass
            except Exception as e:
                if not ready_fut.done():
                    ready_fut.set_exception(e)
                else:
                    self.logger.error(f"Server '{alias}' stopped: {e}")
            finally:
                self.sessions.pop(alias, None)
                self._server_tasks.pop(alias, None)

        task = asyncio.create_task(runner(), name=f"mcp-server:{alias}")
        self._server_tasks[alias] = task
        await ready_fut
        self.logger.info(f"✅ Connected MCP server '{alias}'")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None, server: str = "jarvis") -> str:
        """Call a tool on the specified server."""
        session = self.sessions.get(server)
        if not session:
            return f"Server '{server}' not connected"
        
        try:
            result = await session.call_tool(tool_name, arguments or {})
            return self._extract_text(result)
        except Exception as e:
            return f"Error calling tool: {str(e)}"
    
    def _extract_text(self, result: Any) -> str:
        """Extract textual content from a tool call result."""
        if isinstance(result, str):
            return result
        if hasattr(result, 'content') and getattr(result, 'content') is not None:
            texts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    texts.append(getattr(content, 'text') or '')
                elif isinstance(content, dict) and 'text' in content:
                    texts.append(str(content.get('text') or ''))
            return "\n".join(t for t in texts if t)
        return str(result)
    
    async def stop(self):
        """Stop all MCP servers."""
        tasks = list(self._server_tasks.values())
        for t in tasks:
            t.cancel()
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                self._server_tasks.clear()
        self.sessions.clear()
        self.logger.info("🛑 All MCP servers stopped")

