#!/usr/bin/env python3
"""
Script to restart the Jarvis Client HTTP Server to pick up new MCP servers
"""

import asyncio
import aiohttp
import subprocess
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_URL = "http://localhost:3012"

async def restart_client_server():
    """Restart the Jarvis Client HTTP Server."""
    logger.info("🔄 Restarting Jarvis Client HTTP Server...")
    
    try:
        # First, try to gracefully stop the server
        logger.info("🛑 Stopping current server...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{CLIENT_URL}/shutdown", timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ Server shutdown requested")
                    else:
                        logger.warning(f"Shutdown request failed: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"Could not request graceful shutdown: {e}")
        
        # Wait a moment for shutdown
        await asyncio.sleep(3)
        
        # Start the server again
        logger.info("🚀 Starting server...")
        server_process = subprocess.Popen(
            ["python", "run_client_http_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        logger.info("⏳ Waiting for server to start...")
        await asyncio.sleep(5)
        
        # Check if server is running
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{CLIENT_URL}/servers", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        connected_servers = data.get("connected_servers", [])
                        logger.info(f"✅ Server restarted successfully")
                        logger.info(f"📋 Connected servers: {connected_servers}")
                        return True
                    else:
                        logger.error(f"Server not responding: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Could not verify server restart: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error restarting server: {e}")
        return False

async def main():
    """Main function."""
    success = await restart_client_server()
    if success:
        logger.info("🎉 Client server restart completed successfully")
    else:
        logger.error("❌ Client server restart failed")

if __name__ == "__main__":
    asyncio.run(main())
