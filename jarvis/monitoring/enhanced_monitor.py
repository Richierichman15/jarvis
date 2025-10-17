#!/usr/bin/env python3
"""
Enhanced Discord Bot Monitor with System Monitoring Integration

This script combines the existing monitor_discord_bot.py functionality with
the new SystemMonitor for comprehensive monitoring and Discord notifications.

Usage:
    python -m jarvis.monitoring.enhanced_monitor [--interval 30] [--webhook-url URL]
"""

import asyncio
import logging
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the path to import from jarvis
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jarvis.monitoring.system_monitor import SystemMonitor
from monitor_discord_bot import DiscordBotMonitor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class EnhancedMonitor:
    """Enhanced monitoring that combines system monitoring with Discord bot monitoring."""
    
    def __init__(self, 
                 interval: int = 30,
                 webhook_url: Optional[str] = None,
                 log_file: Optional[str] = None):
        """
        Initialize the enhanced monitor.
        
        Args:
            interval: Monitoring interval in seconds
            webhook_url: Discord webhook URL for notifications
            log_file: Optional log file for monitoring output
        """
        self.interval = interval
        self.webhook_url = webhook_url
        self.log_file = log_file
        
        # Initialize the system monitor
        self.system_monitor = SystemMonitor(
            monitoring_interval=10,  # More frequent system monitoring
            discord_webhook_url=webhook_url
        )
        
        # Initialize the Discord bot monitor
        self.discord_monitor = DiscordBotMonitor(
            interval=interval,
            log_file=log_file
        )
        
        self.monitoring = False
        
        logger.info(f"Enhanced monitor initialized with {interval}s interval")
    
    async def start_monitoring(self):
        """Start both monitoring systems."""
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.monitoring = True
        logger.info("🚀 Starting enhanced monitoring...")
        
        try:
            # Start system monitoring in background
            system_task = asyncio.create_task(self.system_monitor.start_monitoring())
            logger.info("📊 System monitoring started")
            
            # Start Discord bot monitoring in background
            discord_task = asyncio.create_task(self.discord_monitor.monitor_loop())
            logger.info("🤖 Discord bot monitoring started")
            
            # Wait for either task to complete (or be cancelled)
            done, pending = await asyncio.wait(
                [system_task, discord_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in enhanced monitoring: {e}")
        finally:
            self.monitoring = False
            self.system_monitor.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        self.system_monitor.stop_monitoring()
        logger.info("🛑 Enhanced monitoring stopped")
    
    def get_combined_status(self) -> dict:
        """Get combined status from both monitoring systems."""
        status = {
            "system_monitor": {
                "running": self.system_monitor.monitoring,
                "health": self.system_monitor.get_health_summary() if self.system_monitor.metrics_history else None
            },
            "discord_monitor": {
                "running": self.discord_monitor.monitoring,
                "processes": self.discord_monitor.get_process_stats()
            }
        }
        return status


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced Discord Bot System Monitor")
    parser.add_argument("--interval", type=int, default=30,
                       help="Monitoring interval in seconds (default: 30)")
    parser.add_argument("--webhook-url", type=str,
                       help="Discord webhook URL for notifications")
    parser.add_argument("--log-file", type=str,
                       help="Log file for monitoring output")
    
    args = parser.parse_args()
    
    # Get webhook URL from environment if not provided
    webhook_url = args.webhook_url
    if not webhook_url:
        import os
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if webhook_url:
        logger.info(f"🔗 Discord webhook configured: {webhook_url[:50]}...")
    else:
        logger.warning("⚠️ No Discord webhook URL provided - notifications disabled")
    
    monitor = EnhancedMonitor(
        interval=args.interval,
        webhook_url=webhook_url,
        log_file=args.log_file
    )
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        sys.exit(1)
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
