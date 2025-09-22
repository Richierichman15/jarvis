#!/usr/bin/env python3
"""
Standalone MCP Server Runner for Jarvis.
This script starts the Jarvis MCP server with stdio transport.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from jarvis.mcp_server import create_mcp_server
except ImportError as e:
    print(f"Error importing Jarvis MCP server: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


async def main():
    """Main entry point for the MCP server."""
    # Get user name from command line or use default
    user_name = "Boss"
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    
    print(f"Starting Jarvis MCP Server for user: {user_name}", file=sys.stderr)
    print("Server will communicate via stdio transport", file=sys.stderr)
    
    try:
        server = create_mcp_server(user_name)
        await server.run()
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
