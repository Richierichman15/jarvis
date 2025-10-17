#!/usr/bin/env python3
"""
Jarvis System Monitoring Startup Script

This script provides an easy way to start the Jarvis system monitoring components.
It can start the diagnostics dashboard, system monitoring, or both.

Usage:
    python start_monitoring.py [--dashboard] [--monitor] [--enhanced] [--port 8080]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_diagnostics_dashboard(port: int = 8080):
    """Start the diagnostics dashboard."""
    try:
        from jarvis.monitoring.diagnostics_dashboard import DiagnosticsDashboard
        
        logger.info(f"🚀 Starting diagnostics dashboard on port {port}")
        dashboard = DiagnosticsDashboard(host="localhost", port=port)
        runner = await dashboard.start()
        
        logger.info(f"📊 Dashboard available at: http://localhost:{port}")
        logger.info("Press Ctrl+C to stop the dashboard")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        finally:
            await runner.cleanup()
            
    except ImportError as e:
        logger.error(f"❌ Could not import diagnostics dashboard: {e}")
        logger.error("Make sure the jarvis.monitoring module is properly installed")
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")


async def start_system_monitor():
    """Start the system monitor."""
    try:
        from jarvis.monitoring import start_system_monitoring
        import os
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            logger.info("🔗 Discord webhook configured for alerts")
        else:
            logger.warning("⚠️ No Discord webhook URL found - alerts disabled")
        
        logger.info("🚀 Starting system monitor")
        monitor = await start_system_monitoring(
            interval=10,
            webhook_url=webhook_url
        )
        
        logger.info("📊 System monitoring started")
        logger.info("Press Ctrl+C to stop monitoring")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("System monitor stopped by user")
            
    except ImportError as e:
        logger.error(f"❌ Could not import system monitor: {e}")
        logger.error("Make sure the jarvis.monitoring module is properly installed")
    except Exception as e:
        logger.error(f"❌ Error starting system monitor: {e}")


async def start_enhanced_monitor():
    """Start the enhanced monitor (combines system + Discord bot monitoring)."""
    try:
        from jarvis.monitoring.enhanced_monitor import EnhancedMonitor
        import os
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            logger.info("🔗 Discord webhook configured for alerts")
        else:
            logger.warning("⚠️ No Discord webhook URL found - alerts disabled")
        
        logger.info("🚀 Starting enhanced monitor")
        monitor = EnhancedMonitor(
            interval=30,
            webhook_url=webhook_url
        )
        
        await monitor.start_monitoring()
        
    except ImportError as e:
        logger.error(f"❌ Could not import enhanced monitor: {e}")
        logger.error("Make sure the jarvis.monitoring module is properly installed")
    except Exception as e:
        logger.error(f"❌ Error starting enhanced monitor: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Jarvis System Monitoring Startup")
    parser.add_argument("--dashboard", action="store_true",
                       help="Start the diagnostics dashboard")
    parser.add_argument("--monitor", action="store_true",
                       help="Start the system monitor")
    parser.add_argument("--enhanced", action="store_true",
                       help="Start the enhanced monitor (system + Discord bot monitoring)")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port for the diagnostics dashboard (default: 8080)")
    
    args = parser.parse_args()
    
    # If no specific option is chosen, start both dashboard and monitor
    if not any([args.dashboard, args.monitor, args.enhanced]):
        logger.info("🎯 No specific option chosen, starting dashboard and system monitor")
        args.dashboard = True
        args.monitor = True
    
    tasks = []
    
    if args.dashboard:
        tasks.append(start_diagnostics_dashboard(args.port))
    
    if args.monitor:
        tasks.append(start_system_monitor())
    
    if args.enhanced:
        tasks.append(start_enhanced_monitor())
    
    if not tasks:
        logger.error("❌ No monitoring components to start")
        return
    
    try:
        if len(tasks) == 1:
            await tasks[0]
        else:
            # Run multiple tasks concurrently
            await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Startup interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal startup error: {e}")
        sys.exit(1)
