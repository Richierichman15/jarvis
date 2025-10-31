"""HTTP client for Jarvis Client HTTP Server."""
import asyncio
import time
import logging
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


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

