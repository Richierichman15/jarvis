#!/usr/bin/env python3
"""
Discord Bot Service Manager

This script provides a robust way to run the Discord bot with automatic restart
capabilities and better error handling. It's designed to prevent the bot from
shutting down unexpectedly.

Usage:
    python start_discord_bot_service.py [--restart-on-error] [--max-restarts 10]
"""

import asyncio
import sys
import time
import signal
import logging
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_bot_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiscordBotService:
    """Service manager for the Discord bot with automatic restart capabilities."""
    
    def __init__(self, restart_on_error: bool = True, max_restarts: int = 10):
        self.restart_on_error = restart_on_error
        self.max_restarts = max_restarts
        self.restart_count = 0
        self.last_restart_time = 0
        self.min_restart_interval = 30  # Minimum 30 seconds between restarts
        self.running = False
        self.bot_process: Optional[asyncio.subprocess.Process] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down service...")
        self.running = False
        if self.bot_process:
            self.bot_process.terminate()
    
    async def _start_bot(self) -> asyncio.subprocess.Process:
        """Start the Discord bot as a subprocess."""
        logger.info("Starting Discord bot...")
        
        # Start the bot process
        process = await asyncio.create_subprocess_exec(
            sys.executable, "discord_jarvis_bot_full.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_root
        )
        
        logger.info(f"Discord bot started with PID: {process.pid}")
        return process
    
    async def _monitor_bot(self, process: asyncio.subprocess.Process):
        """Monitor the bot process and handle its output."""
        try:
            # Read stdout and stderr
            stdout_task = asyncio.create_task(process.stdout.readline())
            stderr_task = asyncio.create_task(process.stderr.readline())
            
            while self.running and process.returncode is None:
                # Wait for either stdout or stderr data
                done, pending = await asyncio.wait(
                    [stdout_task, stderr_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    if task == stdout_task:
                        line = await task
                        if line:
                            logger.info(f"BOT: {line.decode().strip()}")
                            stdout_task = asyncio.create_task(process.stdout.readline())
                        else:
                            # EOF reached
                            break
                    elif task == stderr_task:
                        line = await task
                        if line:
                            logger.error(f"BOT ERROR: {line.decode().strip()}")
                            stderr_task = asyncio.create_task(process.stderr.readline())
                        else:
                            # EOF reached
                            break
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error monitoring bot: {e}")
    
    def _should_restart(self) -> bool:
        """Determine if the bot should be restarted."""
        if not self.restart_on_error:
            return False
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"Maximum restart limit ({self.max_restarts}) reached")
            return False
        
        current_time = time.time()
        if current_time - self.last_restart_time < self.min_restart_interval:
            logger.warning("Restart interval not met, waiting...")
            return False
        
        return True
    
    async def run(self):
        """Main service loop."""
        logger.info("Starting Discord Bot Service...")
        logger.info(f"Restart on error: {self.restart_on_error}")
        logger.info(f"Max restarts: {self.max_restarts}")
        
        self.running = True
        
        while self.running:
            try:
                # Start the bot
                self.bot_process = await self._start_bot()
                
                # Monitor the bot
                monitor_task = asyncio.create_task(self._monitor_bot(self.bot_process))
                
                # Wait for the bot to finish
                return_code = await self.bot_process.wait()
                
                # Cancel monitoring task
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                
                logger.warning(f"Bot process ended with return code: {return_code}")
                
                # Check if we should restart
                if self._should_restart():
                    self.restart_count += 1
                    self.last_restart_time = time.time()
                    
                    wait_time = min(30, 5 * self.restart_count)  # Exponential backoff, max 30s
                    logger.info(f"Restarting bot in {wait_time} seconds (restart #{self.restart_count})")
                    
                    await asyncio.sleep(wait_time)
                else:
                    logger.info("Not restarting bot, service stopping")
                    break
                    
            except Exception as e:
                logger.error(f"Service error: {e}")
                if self._should_restart():
                    self.restart_count += 1
                    self.last_restart_time = time.time()
                    await asyncio.sleep(10)  # Wait 10 seconds before retry
                else:
                    break
        
        logger.info("Discord Bot Service stopped")

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discord Bot Service Manager")
    parser.add_argument("--restart-on-error", action="store_true", default=True,
                       help="Automatically restart the bot on error (default: True)")
    parser.add_argument("--max-restarts", type=int, default=10,
                       help="Maximum number of restarts (default: 10)")
    parser.add_argument("--no-restart", action="store_true",
                       help="Disable automatic restart")
    
    args = parser.parse_args()
    
    # Override restart setting if --no-restart is specified
    restart_on_error = args.restart_on_error and not args.no_restart
    
    # Create and run the service
    service = DiscordBotService(
        restart_on_error=restart_on_error,
        max_restarts=args.max_restarts
    )
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal service error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
