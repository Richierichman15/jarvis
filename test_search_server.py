#!/usr/bin/env python3
"""
Test script for the search MCP server
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_search_server():
    """Test the search server directly."""
    print("🔍 Testing search server...")
    
    try:
        # Import the search server
        from search.mcp_server import SERVER, call_tool
        
        print("✅ Search server imported successfully")
        
        # Test the call_tool function
        print("🔧 Testing tool call...")
        result = await call_tool("search.web.search", {"query": "AI developments"})
        
        print(f"📋 Search result: {result}")
        print("✅ Search server test completed successfully")
        
    except Exception as e:
        print(f"❌ Search server test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_server())
