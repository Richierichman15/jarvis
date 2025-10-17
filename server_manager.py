#!/usr/bin/env python3
"""
Server Manager for Jarvis MCP Servers

This module provides automatic startup and management of MCP servers
that are needed by the Discord bot but may not be running.
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
import aiohttp
import time

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages MCP server processes and connections."""
    
    def __init__(self, client_url: str = "http://localhost:3012"):
        self.client_url = client_url
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.server_configs = self._load_server_configs()
        self.required_servers = {"search", "trading", "system", "music"}
        
    def _load_server_configs(self) -> Dict[str, Dict]:
        """Load server configurations from .jarvis_servers.json"""
        config_file = Path(".jarvis_servers.json")
        if not config_file.exists():
            logger.warning("No server configuration file found at .jarvis_servers.json")
            return {}
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading server configs: {e}")
            return {}
    
    async def check_server_availability(self) -> Dict[str, bool]:
        """Check which servers are available through the client HTTP server."""
        available = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.client_url}/servers", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        connected_servers = set(data.get("connected_servers", []))
                        
                        for server in self.required_servers:
                            available[server] = server in connected_servers
                    else:
                        logger.warning(f"Failed to check server availability: HTTP {response.status}")
                        # Assume all servers are unavailable
                        for server in self.required_servers:
                            available[server] = False
        except Exception as e:
            logger.error(f"Error checking server availability: {e}")
            # Assume all servers are unavailable
            for server in self.required_servers:
                available[server] = False
        
        return available
    
    async def start_missing_servers(self) -> Dict[str, bool]:
        """Start any missing servers that are configured but not running."""
        logger.info("🔍 Checking for missing servers...")
        
        # Check which servers are available
        available = await self.check_server_availability()
        missing_servers = [server for server, is_available in available.items() if not is_available]
        
        if not missing_servers:
            logger.info("✅ All required servers are available")
            return available
        
        logger.info(f"⚠️ Missing servers: {missing_servers}")
        
        # Start missing servers
        started = {}
        for server in missing_servers:
            if server in self.server_configs:
                success = await self._start_server(server)
                started[server] = success
                if success:
                    logger.info(f"✅ Started {server} server")
                else:
                    logger.error(f"❌ Failed to start {server} server")
            else:
                logger.warning(f"⚠️ No configuration found for {server} server")
                started[server] = False
        
        # Wait a moment for servers to initialize
        if any(started.values()):
            logger.info("⏳ Waiting for servers to initialize...")
            await asyncio.sleep(5)
            
            # Try to reconnect servers to the client HTTP server
            await self._reconnect_servers_to_client()
            
            # Recheck availability
            available = await self.check_server_availability()
        
        return available
    
    async def _start_server(self, server_name: str) -> bool:
        """Start a specific server process."""
        if server_name not in self.server_configs:
            logger.error(f"No configuration found for {server_name} server")
            return False
        
        config = self.server_configs[server_name]
        
        try:
            # Check if server is already running
            if server_name in self.running_processes:
                process = self.running_processes[server_name]
                if process.poll() is None:  # Process is still running
                    logger.info(f"{server_name} server is already running")
                    return True
                else:
                    # Process died, remove it
                    del self.running_processes[server_name]
            
            # Start the server process
            logger.info(f"🚀 Starting {server_name} server...")
            
            # Prepare command
            command = [config["command"]] + config["args"]
            cwd = config.get("cwd", ".")
            
            # Start process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store the process
            self.running_processes[server_name] = process
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                logger.info(f"✅ {server_name} server started successfully (PID: {process.pid})")
                return True
            else:
                # Process died immediately
                stdout, stderr = process.communicate()
                logger.error(f"❌ {server_name} server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {server_name} server: {e}")
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific server process."""
        if server_name not in self.running_processes:
            logger.warning(f"{server_name} server is not running")
            return True
        
        try:
            process = self.running_processes[server_name]
            if process.poll() is None:  # Process is still running
                logger.info(f"🛑 Stopping {server_name} server...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {server_name} server...")
                    process.kill()
                    process.wait()
                
                logger.info(f"✅ {server_name} server stopped")
            
            del self.running_processes[server_name]
            return True
            
        except Exception as e:
            logger.error(f"Error stopping {server_name} server: {e}")
            return False
    
    async def stop_all_servers(self):
        """Stop all managed server processes."""
        logger.info("🛑 Stopping all managed servers...")
        
        for server_name in list(self.running_processes.keys()):
            await self.stop_server(server_name)
        
        logger.info("✅ All servers stopped")
    
    def get_server_status(self) -> Dict[str, Dict]:
        """Get status of all servers."""
        status = {}
        
        for server_name in self.required_servers:
            is_running = False
            pid = None
            
            if server_name in self.running_processes:
                process = self.running_processes[server_name]
                if process.poll() is None:
                    is_running = True
                    pid = process.pid
            
            status[server_name] = {
                "configured": server_name in self.server_configs,
                "running": is_running,
                "pid": pid
            }
        
        return status
    
    async def _reconnect_servers_to_client(self):
        """Try to reconnect servers to the client HTTP server."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to trigger a reconnection by calling the servers endpoint
                async with session.get(f"{self.client_url}/servers", timeout=10) as response:
                    if response.status == 200:
                        logger.info("🔄 Triggered server reconnection check")
                    else:
                        logger.warning(f"Failed to trigger reconnection: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"Could not trigger server reconnection: {e}")


async def main():
    """Test the server manager."""
    manager = ServerManager()
    
    print("🔍 Checking server status...")
    status = manager.get_server_status()
    for server, info in status.items():
        print(f"{server}: {'✅' if info['running'] else '❌'} (configured: {info['configured']})")
    
    print("\n🚀 Starting missing servers...")
    available = await manager.start_missing_servers()
    
    print("\n📊 Final status:")
    for server, is_available in available.items():
        print(f"{server}: {'✅' if is_available else '❌'}")
    
    # Keep running for a bit to test
    print("\n⏳ Running for 30 seconds to test...")
    await asyncio.sleep(30)
    
    print("\n🛑 Stopping all servers...")
    await manager.stop_all_servers()


if __name__ == "__main__":
    asyncio.run(main())
