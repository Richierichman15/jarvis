#!/usr/bin/env python3
"""
Standalone HTTP MCP Server Runner for Jarvis.
This script starts the Jarvis MCP HTTP server on localhost:3010.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from jarvis.mcp_http_server import create_http_mcp_server
except ImportError as e:
    print(f"Error importing Jarvis HTTP MCP server: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


async def main():
    """Main entry point for the HTTP MCP server."""
    # Get user name from command line or use default
    user_name = "Boss"
    host = "0.0.0.0"  # Bind to all interfaces for external access
    port = 3010
    
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    if len(sys.argv) > 2:
        host = sys.argv[2]
    if len(sys.argv) > 3:
        port = int(sys.argv[3])
    
    print(f"Starting Jarvis MCP HTTP Server for user: {user_name}", file=sys.stderr)
    print(f"Server will run on: http://{host}:{port}", file=sys.stderr)
    
    try:
        server = create_http_mcp_server(user_name, host, port)
        await server.run()
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
