#!/usr/bin/env python3
"""
Discord Bot System Monitor

This script monitors system resources and bot health to help diagnose
issues that might cause the bot to shut down unexpectedly.

Usage:
    python monitor_discord_bot.py [--interval 30] [--log-file monitor.log]
"""

import asyncio
import psutil
import aiohttp
import time
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiscordBotMonitor:
    """Monitor system resources and bot health."""
    
    def __init__(self, interval: int = 30, log_file: Optional[str] = None):
        self.interval = interval
        self.log_file = log_file
        self.jarvis_url = "http://localhost:3012"
        self.discord_bot_process = None
        self.jarvis_client_process = None
        self.monitoring = False
        
        # Setup file logging if specified
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    
    def find_bot_processes(self):
        """Find Discord bot and Jarvis client processes."""
        self.discord_bot_process = None
        self.jarvis_client_process = None
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                if 'discord_jarvis_bot_full.py' in cmdline:
                    self.discord_bot_process = proc
                    logger.info(f"Found Discord bot process: PID {proc.info['pid']}")
                
                elif 'run_client_http_server.py' in cmdline or 'client.api' in cmdline:
                    self.jarvis_client_process = proc
                    logger.info(f"Found Jarvis client process: PID {proc.info['pid']}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def get_process_stats(self) -> Dict[str, Any]:
        """Get stats for bot processes."""
        stats = {}
        
        for name, proc in [('discord_bot', self.discord_bot_process), 
                          ('jarvis_client', self.jarvis_client_process)]:
            if proc:
                try:
                    # Check if process is still running
                    if proc.is_running():
                        # Get process info
                        with proc.oneshot():
                            stats[name] = {
                                'pid': proc.pid,
                                'status': proc.status(),
                                'cpu_percent': proc.cpu_percent(),
                                'memory_info': proc.memory_info()._asdict(),
                                'create_time': proc.create_time(),
                                'num_threads': proc.num_threads(),
                                'connections': len(proc.connections())
                            }
                    else:
                        stats[name] = {'status': 'not_running'}
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    stats[name] = {'status': 'process_gone'}
            else:
                stats[name] = {'status': 'not_found'}
        
        return stats
    
    async def check_jarvis_server(self) -> Dict[str, Any]:
        """Check Jarvis server health."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check servers endpoint
                async with session.get(f"{self.jarvis_url}/servers", timeout=10) as response:
                    if response.status == 200:
                        servers_data = await response.json()
                        return {
                            'status': 'healthy',
                            'servers': servers_data,
                            'response_time': response.headers.get('X-Response-Time', 'unknown')
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'http_status': response.status,
                            'error': await response.text()
                        }
        except asyncio.TimeoutError:
            return {'status': 'timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def log_stats(self, system_stats: Dict[str, Any], process_stats: Dict[str, Any], 
                  jarvis_stats: Dict[str, Any]):
        """Log monitoring statistics."""
        logger.info("=== SYSTEM MONITORING REPORT ===")
        
        # System stats
        if system_stats:
            logger.info(f"CPU Usage: {system_stats.get('cpu_percent', 'N/A')}%")
            logger.info(f"Memory Usage: {system_stats.get('memory', {}).get('percent', 'N/A')}%")
            logger.info(f"Disk Usage: {system_stats.get('disk', {}).get('percent', 'N/A'):.1f}%")
        
        # Process stats
        for name, stats in process_stats.items():
            if stats.get('status') == 'not_found':
                logger.warning(f"{name}: Process not found")
            elif stats.get('status') == 'not_running':
                logger.warning(f"{name}: Process not running")
            elif stats.get('status') == 'process_gone':
                logger.warning(f"{name}: Process disappeared")
            else:
                logger.info(f"{name}: PID {stats.get('pid')}, "
                          f"CPU {stats.get('cpu_percent', 0):.1f}%, "
                          f"Memory {stats.get('memory_info', {}).get('rss', 0) / 1024 / 1024:.1f}MB, "
                          f"Status: {stats.get('status')}")
        
        # Jarvis server stats
        jarvis_status = jarvis_stats.get('status', 'unknown')
        if jarvis_status == 'healthy':
            logger.info(f"Jarvis Server: Healthy")
        else:
            logger.warning(f"Jarvis Server: {jarvis_status}")
        
        logger.info("=== END REPORT ===")
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        logger.info(f"Starting Discord Bot Monitor (interval: {self.interval}s)")
        logger.info("Press Ctrl+C to stop monitoring")
        
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Find processes
                self.find_bot_processes()
                
                # Get system stats
                system_stats = self.get_system_stats()
                
                # Get process stats
                process_stats = self.get_process_stats()
                
                # Check Jarvis server
                jarvis_stats = await self.check_jarvis_server()
                
                # Log everything
                self.log_stats(system_stats, process_stats, jarvis_stats)
                
                # Check for issues
                self.check_for_issues(system_stats, process_stats, jarvis_stats)
                
                # Wait for next check
                await asyncio.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def check_for_issues(self, system_stats: Dict[str, Any], process_stats: Dict[str, Any], 
                        jarvis_stats: Dict[str, Any]):
        """Check for potential issues that could cause bot shutdowns."""
        issues = []
        
        # Check system resources
        if system_stats:
            cpu_percent = system_stats.get('cpu_percent', 0)
            memory_percent = system_stats.get('memory', {}).get('percent', 0)
            disk_percent = system_stats.get('disk', {}).get('percent', 0)
            
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent}%")
            
            if disk_percent > 95:
                issues.append(f"Low disk space: {disk_percent:.1f}% used")
        
        # Check processes
        for name, stats in process_stats.items():
            if stats.get('status') in ['not_found', 'not_running', 'process_gone']:
                issues.append(f"{name} process is not running")
            
            # Check for high resource usage
            if stats.get('cpu_percent', 0) > 50:
                issues.append(f"{name} high CPU usage: {stats.get('cpu_percent', 0):.1f}%")
            
            memory_mb = stats.get('memory_info', {}).get('rss', 0) / 1024 / 1024
            if memory_mb > 1000:  # More than 1GB
                issues.append(f"{name} high memory usage: {memory_mb:.1f}MB")
        
        # Check Jarvis server
        if jarvis_stats.get('status') != 'healthy':
            issues.append(f"Jarvis server unhealthy: {jarvis_stats.get('status')}")
        
        # Report issues
        if issues:
            logger.warning("POTENTIAL ISSUES DETECTED:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("No issues detected")

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discord Bot System Monitor")
    parser.add_argument("--interval", type=int, default=30,
                       help="Monitoring interval in seconds (default: 30)")
    parser.add_argument("--log-file", type=str,
                       help="Log file for monitoring output")
    
    args = parser.parse_args()
    
    monitor = DiscordBotMonitor(
        interval=args.interval,
        log_file=args.log_file
    )
    
    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
