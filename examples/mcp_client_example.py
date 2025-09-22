#!/usr/bin/env python3
"""
Example MCP Client for Jarvis.
This demonstrates how to interact with the Jarvis MCP server.
"""
import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List


class JarvisMCPClient:
    """Simple MCP client for testing Jarvis functionality."""
    
    def __init__(self, server_path: str, user_name: str = "Boss"):
        """Initialize the MCP client."""
        self.server_path = server_path
        self.user_name = user_name
        self.process = None
    
    async def start_server(self):
        """Start the MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, self.server_path, self.user_name,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    
    async def stop_server(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        if not self.process:
            raise RuntimeError("Server not started")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        
        return response
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        response = await self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a tool."""
        response = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return response.get("result", {}).get("content", [])


async def main():
    """Main example function."""
    # Path to the MCP server script
    server_path = "../run_mcp_server.py"
    user_name = "TestUser"
    
    client = JarvisMCPClient(server_path, user_name)
    
    try:
        print(f"Starting Jarvis MCP server for {user_name}...")
        await client.start_server()
        
        # Wait a moment for server to initialize
        await asyncio.sleep(1)
        
        print("\n1. Listing available tools...")
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        print("\n2. Testing chat functionality...")
        chat_result = await client.call_tool("jarvis_chat", {
            "message": "Hello Jarvis! Can you help me understand what you can do?"
        })
        print("Chat response:")
        for content in chat_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n3. Testing task creation...")
        task_result = await client.call_tool("jarvis_schedule_task", {
            "description": "Test task from MCP client",
            "priority": "medium",
            "category": "general"
        })
        print("Task creation result:")
        for content in task_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n4. Testing task listing...")
        tasks_result = await client.call_tool("jarvis_get_tasks", {
            "status": "all"
        })
        print("Current tasks:")
        for content in tasks_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n5. Testing system status...")
        status_result = await client.call_tool("jarvis_get_status", {})
        print("System status:")
        for content in status_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n6. Testing web search...")
        search_result = await client.call_tool("jarvis_web_search", {
            "query": "Python programming"
        })
        print("Web search result:")
        for content in search_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n7. Testing calculator...")
        calc_result = await client.call_tool("jarvis_calculate", {
            "expression": "2 + 2 * 3"
        })
        print("Calculation result:")
        for content in calc_result:
            if content.get("type") == "text":
                print(f"  {content['text']}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        print("\nStopping MCP server...")
        await client.stop_server()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
