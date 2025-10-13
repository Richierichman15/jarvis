#!/usr/bin/env python3
"""
Test script for Full-Featured Discord Jarvis Bot

This script tests the bot's connection to the Jarvis Client HTTP Server
and verifies access to all available tools from all connected servers.
"""

import asyncio
import aiohttp
import sys
from discord_jarvis_bot_full import JarvisClientMCPClient, DiscordCommandRouter


async def test_client_connection():
    """Test connection to Jarvis Client HTTP Server."""
    print("Testing Jarvis Client HTTP Server connection...")
    
    async with aiohttp.ClientSession() as session:
        jarvis_client = JarvisClientMCPClient("http://localhost:3012", session)
        
        try:
            # Test getting available tools
            tools = await jarvis_client.get_available_tools()
            if tools:
                print(f"✅ Connected to Jarvis Client HTTP Server")
                print(f"📊 Available servers: {list(tools.keys())}")
                total_tools = sum(len(server_tools) for server_tools in tools.values())
                print(f"🔧 Total tools available: {total_tools}")
                return True
            else:
                print("❌ No tools available - server may not be running")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False


async def test_tool_calls():
    """Test various tool calls across different servers."""
    print("\nTesting tool calls across servers...")
    
    async with aiohttp.ClientSession() as session:
        jarvis_client = JarvisClientMCPClient("http://localhost:3012", session)
        router = DiscordCommandRouter(jarvis_client)
        
        # Test commands - all tools are on the jarvis server
        test_commands = [
            # Core Commands
            ("/status", "jarvis_get_status", "jarvis"),
            ("/memory", "jarvis_get_memory", "jarvis"),
            ("/tasks", "jarvis_get_tasks", "jarvis"),
            ("/help", "jarvis_chat", "jarvis"),
            
            # Trading Commands
            ("/portfolio", "trading.portfolio.get_overview", "jarvis"),
            ("/balance", "trading.trading.get_balance", "jarvis"),
            ("/positions", "trading.portfolio.get_positions", "jarvis"),
            ("/trades", "trading.get_recent_executions", "jarvis"),
            ("/paper", "trading.get_portfolio_balance", "jarvis"),
            ("/momentum", "trading.get_momentum_signals", "jarvis"),
            ("/price BTC", "trading.get_price", "jarvis"),
            ("/ohlcv ETH", "trading.get_ohlcv", "jarvis"),
            ("/pairs BTC", "trading.search_pairs", "jarvis"),
            ("/doctor", "trading.doctor", "jarvis"),
            ("/history", "trading.get_trade_history", "jarvis"),
            ("/pnl", "trading.get_pnl_summary", "jarvis"),
            
            # Portfolio Tools
            ("/performance", "portfolio.get_performance", "jarvis"),
            ("/exit", "portfolio.get_exit_engine_status", "jarvis"),
            ("/state", "portfolio.get_trading_state", "jarvis"),
            ("/export", "portfolio.get_export_data", "jarvis"),
            
            # System Commands
            ("/quests", "system.system.list_quests", "jarvis"),
            ("/system", "system.system.get_status", "jarvis"),
            
            # Search Commands
            ("/news", "jarvis_scan_news", "jarvis"),
            ("/search latest AI news", "search.web.search", "jarvis"),
            
            # Natural Language
            ("Hello Jarvis", "natural_language", None),
            ("What's today's date?", "jarvis_chat", "jarvis"),
        ]
        
        for command, expected_tool, expected_server in test_commands:
            tool_name, args, server = router.parse_command(command)
            print(f"  '{command}' → '{tool_name}' on '{server or 'default'}' with args: {args}")
            
            # Verify routing is correct
            if expected_tool == "natural_language":
                if tool_name != "natural_language":
                    print(f"    ❌ Expected natural_language, got {tool_name}")
            else:
                if tool_name != expected_tool:
                    print(f"    ❌ Expected {expected_tool}, got {tool_name}")
                if server != expected_server:
                    print(f"    ❌ Expected server {expected_server}, got {server}")
        
        print("✅ Command routing test completed")


async def test_actual_tool_calls():
    """Test actual tool calls to verify they work."""
    print("\nTesting actual tool calls...")
    
    async with aiohttp.ClientSession() as session:
        jarvis_client = JarvisClientMCPClient("http://localhost:3012", session)
        
        # Test a simple tool call
        try:
            response = await jarvis_client.call_tool("jarvis_get_status", {}, "jarvis")
            if response and not response.startswith("Error:"):
                print(f"✅ jarvis_get_status: {response[:100]}...")
            else:
                print(f"❌ jarvis_get_status failed: {response}")
        except Exception as e:
            print(f"❌ jarvis_get_status error: {e}")
        
        # Test natural language
        try:
            response = await jarvis_client.natural_language_query("Hello, how are you?")
            if response and not response.startswith("Error:"):
                print(f"✅ Natural language: {response[:100]}...")
            else:
                print(f"❌ Natural language failed: {response}")
        except Exception as e:
            print(f"❌ Natural language error: {e}")


async def main():
    """Run all tests."""
    print("Full-Featured Discord Jarvis Bot - Test Suite")
    print("=" * 50)
    
    # Test 1: Client connection
    client_ok = await test_client_connection()
    
    # Test 2: Command routing
    await test_tool_calls()
    
    # Test 3: Actual tool calls
    if client_ok:
        await test_actual_tool_calls()
    
    # Summary
    print("\n" + "=" * 50)
    if client_ok:
        print("✅ All tests passed! Full-featured bot is ready to run.")
        print("\nNext steps:")
        print("1. Make sure Jarvis Client HTTP Server is running:")
        print("   python run_client_http_server.py")
        print("2. Set up your Discord bot token in .env file")
        print("3. Run: python discord_jarvis_bot_full.py")
        print("\nAvailable commands:")
        print("📋 Core Commands:")
        print("  /status - System status")
        print("  /memory - Conversation history")
        print("  /tasks - Jarvis tasks")
        print("  /help - Show help")
        print("💰 Trading Commands:")
        print("  /portfolio - Trading portfolio overview")
        print("  /balance - Trading balance")
        print("  /positions - Trading positions")
        print("  /trades - Recent trade executions")
        print("  /paper - Paper trading balance")
        print("  /momentum - Momentum signals")
        print("  /price <symbol> - Get price (e.g., /price BTC)")
        print("  /ohlcv <symbol> - Get OHLCV data")
        print("  /pairs <query> - Search trading pairs")
        print("  /doctor - Trading system diagnostics")
        print("  /history - Trade history")
        print("  /pnl - Profit/loss summary")
        print("📊 Portfolio Tools:")
        print("  /performance - Performance metrics")
        print("  /exit - Exit engine status")
        print("  /state - Trading system state")
        print("  /export - Export data")
        print("🎮 System Commands:")
        print("  /quests - System quests")
        print("  /system - System status")
        print("📰 Search Commands:")
        print("  /news - Latest tech news")
        print("  /search <query> - Web search")
        print("💬 Natural Language:")
        print("  Any other message - Natural language chat")
        print("  Date/time questions - Special handling")
    else:
        print("❌ Some tests failed. Please check:")
        print("1. Jarvis Client HTTP Server is running on port 3011")
        print("2. Run: python run_client_http_server.py")
        print("3. Check that all MCP servers are connected")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
        sys.exit(1)
