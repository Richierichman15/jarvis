#!/usr/bin/env python3
"""
Run the Jarvis Client HTTP Server

This script starts the FastAPI HTTP server that exposes all connected MCP servers
(trading, system, search, jarvis) as HTTP endpoints for the Discord bot.

Usage:
    python run_client_http_server.py [port]

Default port: 3011
"""

import sys
import asyncio
import socket
import uvicorn
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from client.api import create_app, preflight_jarvis_mcp
except ImportError as e:
    print(f"Error importing client API: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
            return False
        except OSError:
            return True


def _verify_python() -> None:
    expected = (project_root / ".venv" / "Scripts" / "python.exe").resolve()
    actual = Path(sys.executable).resolve()
    if expected.is_file() and actual != expected:
        print(f"\nWARNING: Not using the project venv Python.")
        print(f"  Current:  {actual}")
        print(f"  Expected: {expected}")
        print("  Use: .venv/Scripts/python.exe run_client_http_server.py")
        print()


async def main():
    """Main entry point for the client HTTP server."""
    # Get port from command line or use default
    port = 3012  # Changed from 3011 to avoid conflicts
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"Starting Jarvis Client HTTP Server...")
    print(f"Server will run on: http://localhost:{port}")
    print(f"Available endpoints:")
    print(f"  - GET  /tools - List all available tools from all servers")
    print(f"  - POST /run-tool - Run a tool: {{'tool': 'name', 'args': {{}}, 'server': 'optional'}}")
    print(f"  - POST /nl - Natural language processing")
    print(f"  - GET  /servers - List connected servers")
    print(f"  - POST /servers/connect - Connect to additional servers")
    print()
    print("Server will auto-connect to all MCP servers in .jarvis_servers.json")
    print("Watch the logs below to see which servers connect successfully...")
    print()
    print("Press Ctrl+C to stop the server")

    if _port_in_use(port):
        print(f"\nERROR: Port {port} is already in use.")
        print("Another Jarvis client may still be running. Stop it first, then retry.")
        print(f"  Windows: netstat -ano | findstr :{port}")
        sys.exit(1)

    _verify_python()
    print("Running MCP preflight check...")
    try:
        await preflight_jarvis_mcp()
    except Exception as exc:
        print(f"\nERROR: MCP preflight failed: {exc}")
        print("The Jarvis MCP subprocess could not start. Common causes:")
        print("  - Wrong Python (activate .venv first)")
        print("  - MCP_SERVER_PATH points to a missing file")
        print("  - Another process interfering with stdio")
        sys.exit(1)
    print()
    
    # Create the FastAPI app
    app = create_app()
    
    # Run the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
