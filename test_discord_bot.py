#!/usr/bin/env python3
"""
Test script for Discord Jarvis Bot

This script tests the core functionality without requiring Discord connection.
"""

import asyncio
import aiohttp
import sys
from discord_jarvis_bot import JarvisMCPClient, DiscordCommandRouter


async def test_jarvis_connection():
    """Test connection to Jarvis MCP server."""
    print("Testing Jarvis MCP connection...")
    
    async with aiohttp.ClientSession() as session:
        jarvis_client = JarvisMCPClient("http://localhost:3010/mcp/tools/call", session)
        
        try:
            # Test basic connection
            response = await jarvis_client.query_jarvis("jarvis_get_status", {})
            print(f"✅ Jarvis connection successful: {response[:100]}...")
            return True
        except Exception as e:
            print(f"❌ Jarvis connection failed: {e}")
            return False


async def test_command_router():
    """Test command routing functionality."""
    print("\nTesting command router...")
    
    async with aiohttp.ClientSession() as session:
        jarvis_client = JarvisMCPClient("http://localhost:3010/mcp/tools/call", session)
        router = DiscordCommandRouter(jarvis_client)
        
        # Test command parsing
        test_commands = [
            "/news",
            "scan news",
            "/portfolio", 
            "get portfolio",
            "/status",
            "get status",
            "/memory",
            "get memory",
            "/help",
            "help",
            "Hello Jarvis, how are you?"
        ]
        
        for cmd in test_commands:
            tool_name, args = router.parse_command(cmd)
            print(f"  '{cmd}' → '{tool_name}' with args: {args}")
        
        print("✅ Command router test completed")


async def main():
    """Run all tests."""
    print("Discord Jarvis Bot - Test Suite")
    print("=" * 40)
    
    # Test 1: Jarvis connection
    jarvis_ok = await test_jarvis_connection()
    
    # Test 2: Command router
    await test_command_router()
    
    # Summary
    print("\n" + "=" * 40)
    if jarvis_ok:
        print("✅ All tests passed! Bot is ready to run.")
        print("\nNext steps:")
        print("1. Set up your Discord bot token in .env file")
        print("2. Run: python discord_jarvis_bot.py")
    else:
        print("❌ Some tests failed. Please check:")
        print("1. Jarvis MCP server is running on port 3010")
        print("2. Server is accessible at http://localhost:3010")
        print("3. Run: python run_http_mcp_server.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
        sys.exit(1)
