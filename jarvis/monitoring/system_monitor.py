#!/usr/bin/env python3
"""
Jarvis System Monitor - Advanced System Monitoring with Self-Awareness

This module provides comprehensive system monitoring capabilities including:
- CPU/memory tracking per server and process
- Active tools and response time monitoring
- Discord ping latency tracking
- MCP server health monitoring
- Agent status and heartbeat tracking
- Discord webhook notifications for alerts
- Real-time diagnostics dashboard

Usage:
    from jarvis.monitoring.system_monitor import SystemMonitor
    
    monitor = SystemMonitor()
    await monitor.start_monitoring()
"""

import asyncio
import aiohttp
import psutil
import time
import logging
import json
import os
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import signal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerMetrics:
    """Metrics for a single server/process."""
    name: str
    pid: Optional[int]
    status: str  # running, stopped, error
    cpu_percent: float
    memory_mb: float
    response_time_ms: float
    uptime_seconds: float
    last_heartbeat: datetime
    error_count: int
    success_count: int


@dataclass
class SystemMetrics:
    """Overall system metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    discord_latency_ms: float
    servers: Dict[str, ServerMetrics]
    alerts: List[str]


class SystemMonitor:
    """Advanced system monitoring with self-awareness and Discord integration."""
    
    def __init__(self, 
                 monitoring_interval: int = 10,
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 discord_webhook_url: Optional[str] = None):
        """
        Initialize the system monitor.
        
        Args:
            monitoring_interval: Seconds between monitoring cycles
            alert_thresholds: Custom alert thresholds
            discord_webhook_url: Discord webhook URL for notifications
        """
        self.monitoring_interval = monitoring_interval
        self.discord_webhook_url = discord_webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'response_time_ms': 5000.0,
            'discord_latency_ms': 1000.0,
            'error_rate_percent': 10.0
        }
        
        # Monitoring state
        self.monitoring = False
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 100  # Keep last 100 measurements
        
        # Server configurations
        self.server_configs = {
            'jarvis_client': {
                'url': 'http://localhost:3012',
                'health_endpoint': '/health',
                'process_name': 'run_client_http_server.py'
            },
            'discord_bot': {
                'process_name': 'discord_jarvis_bot_full.py',
                'ping_endpoint': None  # Discord bot doesn't have HTTP endpoint
            },
            'search_server': {
                'process_name': 'search/mcp_server.py',
                'health_endpoint': None
            },
            'music_server': {
                'process_name': 'music_server.py',
                'health_endpoint': None
            },
            'trading_server': {
                'process_name': 'trading_mcp_server.py',
                'health_endpoint': None
            },
            'system_server': {
                'process_name': 'system_server.py',
                'health_endpoint': None
            }
        }
        
        # Agent configurations (if agent system is running)
        self.agent_configs = {
            'trader_agent': {'port': 8001, 'health_endpoint': '/health'},
            'music_agent': {'port': 8002, 'health_endpoint': '/health'},
            'system_agent': {'port': 8003, 'health_endpoint': '/health'},
            'fitness_agent': {'port': 8004, 'health_endpoint': '/health'},
            'research_agent': {'port': 8005, 'health_endpoint': '/health'}
        }
        
        # Performance tracking
        self.tool_response_times: Dict[str, List[float]] = {}
        self.discord_ping_history: List[float] = []
        
        logger.info(f"SystemMonitor initialized with {self.monitoring_interval}s interval")
    
    async def start_monitoring(self):
        """Start the monitoring loop."""
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.monitoring = True
        logger.info("Starting system monitoring...")
        
        try:
            while self.monitoring:
                start_time = time.time()
                
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Store in history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history.pop(0)
                
                # Check for alerts
                alerts = self._check_alerts(metrics)
                if alerts:
                    await self._send_alerts(alerts, metrics)
                
                # Log current status
                self._log_status(metrics)
                
                # Calculate sleep time to maintain consistent interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.monitoring = False
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.monitoring = False
        logger.info("Stopping system monitoring...")
    
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics."""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Discord latency
        discord_latency = await self._measure_discord_latency()
        
        # Server metrics
        servers = await self._collect_server_metrics()
        
        # Agent metrics (if running)
        agents = await self._collect_agent_metrics()
        servers.update(agents)
        
        return SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            network_io={
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            process_count=len(psutil.pids()),
            discord_latency_ms=discord_latency,
            servers=servers,
            alerts=[]
        )
    
    async def _collect_server_metrics(self) -> Dict[str, ServerMetrics]:
        """Collect metrics for all configured servers."""
        servers = {}
        
        for name, config in self.server_configs.items():
            try:
                # Find process
                process = self._find_process(config.get('process_name'))
                
                if process:
                    # Get process metrics
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    uptime = time.time() - process.create_time()
                    
                    # Test response time if HTTP endpoint available
                    response_time = 0.0
                    if config.get('url') and config.get('health_endpoint'):
                        response_time = await self._test_response_time(
                            f"{config['url']}{config['health_endpoint']}"
                        )
                    
                    servers[name] = ServerMetrics(
                        name=name,
                        pid=process.pid,
                        status='running',
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        response_time_ms=response_time,
                        uptime_seconds=uptime,
                        last_heartbeat=datetime.now(),
                        error_count=0,
                        success_count=1
                    )
                else:
                    servers[name] = ServerMetrics(
                        name=name,
                        pid=None,
                        status='stopped',
                        cpu_percent=0.0,
                        memory_mb=0.0,
                        response_time_ms=0.0,
                        uptime_seconds=0.0,
                        last_heartbeat=datetime.now(),
                        error_count=1,
                        success_count=0
                    )
                    
            except Exception as e:
                logger.error(f"Error collecting metrics for {name}: {e}")
                servers[name] = ServerMetrics(
                    name=name,
                    pid=None,
                    status='error',
                    cpu_percent=0.0,
                    memory_mb=0.0,
                    response_time_ms=0.0,
                    uptime_seconds=0.0,
                    last_heartbeat=datetime.now(),
                    error_count=1,
                    success_count=0
                )
        
        return servers
    
    async def _collect_agent_metrics(self) -> Dict[str, ServerMetrics]:
        """Collect metrics for all configured agents."""
        agents = {}
        
        for name, config in self.agent_configs.items():
            try:
                url = f"http://localhost:{config['port']}{config['health_endpoint']}"
                response_time = await self._test_response_time(url)
                
                if response_time > 0:
                    agents[name] = ServerMetrics(
                        name=name,
                        pid=None,  # Agents might not have direct process access
                        status='running',
                        cpu_percent=0.0,  # Would need process lookup
                        memory_mb=0.0,    # Would need process lookup
                        response_time_ms=response_time,
                        uptime_seconds=0.0,  # Would need process lookup
                        last_heartbeat=datetime.now(),
                        error_count=0,
                        success_count=1
                    )
                else:
                    agents[name] = ServerMetrics(
                        name=name,
                        pid=None,
                        status='stopped',
                        cpu_percent=0.0,
                        memory_mb=0.0,
                        response_time_ms=0.0,
                        uptime_seconds=0.0,
                        last_heartbeat=datetime.now(),
                        error_count=1,
                        success_count=0
                    )
                    
            except Exception as e:
                logger.error(f"Error collecting agent metrics for {name}: {e}")
                agents[name] = ServerMetrics(
                    name=name,
                    pid=None,
                    status='error',
                    cpu_percent=0.0,
                    memory_mb=0.0,
                    response_time_ms=0.0,
                    uptime_seconds=0.0,
                    last_heartbeat=datetime.now(),
                    error_count=1,
                    success_count=0
                )
        
        return agents
    
    def _find_process(self, process_name: str) -> Optional[psutil.Process]:
        """Find a process by name or command line."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if process_name in cmdline:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
    
    async def _test_response_time(self, url: str) -> float:
        """Test HTTP response time for a given URL."""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        return (time.time() - start_time) * 1000  # Convert to ms
        except Exception:
            pass
        return 0.0
    
    async def _measure_discord_latency(self) -> float:
        """Measure Discord API latency."""
        try:
            # This is a simplified measurement - in practice you'd ping Discord's API
            # For now, we'll measure the time to make a simple HTTP request
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get('https://discord.com/api/v10/gateway', timeout=5) as response:
                    if response.status == 200:
                        latency = (time.time() - start_time) * 1000
                        self.discord_ping_history.append(latency)
                        if len(self.discord_ping_history) > 10:
                            self.discord_ping_history.pop(0)
                        return latency
        except Exception as e:
            logger.debug(f"Discord latency measurement failed: {e}")
        return 0.0
    
    def _check_alerts(self, metrics: SystemMetrics) -> List[str]:
        """Check for alert conditions."""
        alerts = []
        
        # System resource alerts
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        if metrics.discord_latency_ms > self.alert_thresholds['discord_latency_ms']:
            alerts.append(f"High Discord latency: {metrics.discord_latency_ms:.1f}ms")
        
        # Server alerts
        for name, server in metrics.servers.items():
            if server.status == 'stopped':
                alerts.append(f"Server {name} is not running")
            elif server.status == 'error':
                alerts.append(f"Server {name} has errors")
            elif server.response_time_ms > self.alert_thresholds['response_time_ms']:
                alerts.append(f"Server {name} slow response: {server.response_time_ms:.1f}ms")
            
            # Check error rate
            total_requests = server.error_count + server.success_count
            if total_requests > 0:
                error_rate = (server.error_count / total_requests) * 100
                if error_rate > self.alert_thresholds['error_rate_percent']:
                    alerts.append(f"Server {name} high error rate: {error_rate:.1f}%")
        
        return alerts
    
    async def _send_alerts(self, alerts: List[str], metrics: SystemMetrics):
        """Send alerts via Discord webhook."""
        if not self.discord_webhook_url:
            logger.warning("Discord webhook URL not configured, cannot send alerts")
            return
        
        try:
            # Create alert message
            alert_text = "🚨 **Jarvis System Alert**\n\n"
            alert_text += f"**Time:** {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            alert_text += "**Issues Detected:**\n"
            for alert in alerts:
                alert_text += f"• {alert}\n"
            
            alert_text += f"\n**System Status:**\n"
            alert_text += f"• CPU: {metrics.cpu_percent:.1f}%\n"
            alert_text += f"• Memory: {metrics.memory_percent:.1f}%\n"
            alert_text += f"• Disk: {metrics.disk_percent:.1f}%\n"
            alert_text += f"• Discord Latency: {metrics.discord_latency_ms:.1f}ms\n"
            
            # Send webhook
            payload = {"content": alert_text}
            async with aiohttp.ClientSession() as session:
                async with session.post(self.discord_webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Alert sent to Discord: {len(alerts)} issues")
                    else:
                        logger.error(f"Failed to send Discord alert: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
    
    def _log_status(self, metrics: SystemMetrics):
        """Log current system status."""
        logger.info("=== SYSTEM STATUS ===")
        logger.info(f"CPU: {metrics.cpu_percent:.1f}% | Memory: {metrics.memory_percent:.1f}% | Disk: {metrics.disk_percent:.1f}%")
        logger.info(f"Discord Latency: {metrics.discord_latency_ms:.1f}ms | Processes: {metrics.process_count}")
        
        for name, server in metrics.servers.items():
            status_emoji = "✅" if server.status == "running" else "❌"
            logger.info(f"{status_emoji} {name}: {server.status} (PID: {server.pid}, CPU: {server.cpu_percent:.1f}%, Memory: {server.memory_mb:.1f}MB)")
    
    def get_diagnostics_data(self) -> Dict[str, Any]:
        """Get comprehensive diagnostics data for dashboard."""
        if not self.metrics_history:
            return {"error": "No metrics collected yet"}
        
        latest = self.metrics_history[-1]
        
        # Calculate averages over last 10 measurements
        recent_metrics = self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_discord_latency = sum(m.discord_latency_ms for m in recent_metrics) / len(recent_metrics)
        
        # Server uptime calculations
        server_stats = {}
        for name, server in latest.servers.items():
            uptime_hours = server.uptime_seconds / 3600
            success_rate = (server.success_count / (server.success_count + server.error_count) * 100) if (server.success_count + server.error_count) > 0 else 0
            
            server_stats[name] = {
                "status": server.status,
                "pid": server.pid,
                "uptime_hours": uptime_hours,
                "cpu_percent": server.cpu_percent,
                "memory_mb": server.memory_mb,
                "response_time_ms": server.response_time_ms,
                "success_rate": success_rate,
                "error_count": server.error_count
            }
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "current": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_percent": latest.disk_percent,
                "discord_latency_ms": latest.discord_latency_ms,
                "process_count": latest.process_count
            },
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "discord_latency_ms": avg_discord_latency
            },
            "servers": server_stats,
            "alerts": latest.alerts,
            "monitoring_duration": len(self.metrics_history) * self.monitoring_interval
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No monitoring data available"}
        
        latest = self.metrics_history[-1]
        
        # Determine overall health
        health_score = 100
        issues = []
        
        if latest.cpu_percent > 80:
            health_score -= 20
            issues.append("High CPU usage")
        
        if latest.memory_percent > 85:
            health_score -= 20
            issues.append("High memory usage")
        
        if latest.disk_percent > 90:
            health_score -= 15
            issues.append("High disk usage")
        
        if latest.discord_latency_ms > 1000:
            health_score -= 10
            issues.append("High Discord latency")
        
        # Check server health
        stopped_servers = [name for name, server in latest.servers.items() if server.status != "running"]
        if stopped_servers:
            health_score -= len(stopped_servers) * 10
            issues.append(f"Stopped servers: {', '.join(stopped_servers)}")
        
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 70:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "status": status,
            "health_score": health_score,
            "issues": issues,
            "timestamp": latest.timestamp.isoformat(),
            "uptime": len(self.metrics_history) * self.monitoring_interval
        }


# Global monitor instance
_monitor_instance: Optional[SystemMonitor] = None


async def start_system_monitoring(interval: int = 10, webhook_url: Optional[str] = None):
    """Start the global system monitoring instance."""
    global _monitor_instance
    
    if _monitor_instance and _monitor_instance.monitoring:
        logger.warning("System monitoring already running")
        return _monitor_instance
    
    _monitor_instance = SystemMonitor(
        monitoring_interval=interval,
        discord_webhook_url=webhook_url
    )
    
    # Start monitoring in background
    asyncio.create_task(_monitor_instance.start_monitoring())
    
    return _monitor_instance


def get_system_monitor() -> Optional[SystemMonitor]:
    """Get the global system monitor instance."""
    return _monitor_instance


def stop_system_monitoring():
    """Stop the global system monitoring instance."""
    global _monitor_instance
    
    if _monitor_instance:
        _monitor_instance.stop_monitoring()
        _monitor_instance = None


if __name__ == "__main__":
    # Test the system monitor
    async def test_monitor():
        monitor = SystemMonitor(monitoring_interval=5)
        await monitor.start_monitoring()
    
    asyncio.run(test_monitor())
