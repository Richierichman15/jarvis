#!/usr/bin/env python3
"""
Test script to check MCP server connections
"""

import asyncio
import aiohttp
import json

async def test_connections():
    """Test all server connections."""
    client_url = "http://localhost:3012"
    
    print("🔍 Testing Jarvis Client HTTP Server connections...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test servers endpoint
            print("\n📋 Checking connected servers...")
            async with session.get(f"{client_url}/servers", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    connected_servers = data.get("connected_servers", [])
                    print(f"✅ Connected servers: {connected_servers}")
                    
                    # Check if search server is connected
                    if "search" in connected_servers:
                        print("✅ Search server is connected!")
                        
                        # Test search functionality
                        print("\n🔍 Testing search functionality...")
                        search_data = {
                            "tool": "search.web.search",
                            "args": {"query": "AI developments"},
                            "server": "search"
                        }
                        
                        async with session.post(f"{client_url}/run-tool", json=search_data, timeout=30) as search_response:
                            if search_response.status == 200:
                                result = await search_response.json()
                                print("✅ Search test successful!")
                                print(f"📄 Result preview: {str(result)[:200]}...")
                            else:
                                print(f"❌ Search test failed: HTTP {search_response.status}")
                    else:
                        print("❌ Search server is not connected")
                        print("💡 Try running: python restart_client_server.py")
                else:
                    print(f"❌ Failed to get servers: HTTP {response.status}")
            
            # Test tools endpoint
            print("\n🛠️ Checking available tools...")
            async with session.get(f"{client_url}/tools", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("tools", [])
                    print(f"✅ Found {len(tools)} tools")
                    
                    # Look for search tools
                    search_tools = [tool for tool in tools if "search" in tool.get("name", "").lower()]
                    if search_tools:
                        print(f"🔍 Search tools found: {[tool['name'] for tool in search_tools]}")
                    else:
                        print("❌ No search tools found")
                else:
                    print(f"❌ Failed to get tools: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connections())
