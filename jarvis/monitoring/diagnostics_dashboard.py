#!/usr/bin/env python3
"""
Jarvis Diagnostics Dashboard

A web-based dashboard for real-time system monitoring and diagnostics.
Provides a comprehensive view of system health, server status, and performance metrics.

Usage:
    python -m jarvis.monitoring.diagnostics_dashboard
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .system_monitor import get_system_monitor, SystemMonitor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiagnosticsDashboard:
    """Web-based diagnostics dashboard for Jarvis system monitoring."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # Static files directory
        self.static_dir = Path(__file__).parent / "static"
        self.static_dir.mkdir(exist_ok=True)
        
        # Create default HTML template if it doesn't exist
        self._create_default_template()
    
    def setup_routes(self):
        """Set up web routes."""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/health', self.health_handler)
        self.app.router.add_get('/api/diagnostics', self.diagnostics_handler)
        self.app.router.add_get('/api/metrics', self.metrics_handler)
        self.app.router.add_get('/api/servers', self.servers_handler)
        self.app.router.add_get('/api/alerts', self.alerts_handler)
        self.app.router.add_static('/static', self.static_dir)
    
    def _create_default_template(self):
        """Create default HTML template for the dashboard."""
        html_file = self.static_dir / "dashboard.html"
        
        if not html_file.exists():
            html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis System Diagnostics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        .card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #2d3748;
        }
        
        .metric-value {
            font-weight: 600;
            color: #1a202c;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-running {
            background-color: #48bb78;
            box-shadow: 0 0 10px rgba(72, 187, 120, 0.5);
        }
        
        .status-stopped {
            background-color: #f56565;
            box-shadow: 0 0 10px rgba(245, 101, 101, 0.5);
        }
        
        .status-error {
            background-color: #ed8936;
            box-shadow: 0 0 10px rgba(237, 137, 54, 0.5);
        }
        
        .health-score {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        
        .health-excellent { color: #48bb78; }
        .health-good { color: #38b2ac; }
        .health-fair { color: #ed8936; }
        .health-poor { color: #f56565; }
        
        .alerts {
            background: #fed7d7;
            border: 1px solid #feb2b2;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .alerts h4 {
            color: #c53030;
            margin-bottom: 10px;
        }
        
        .alerts ul {
            list-style: none;
        }
        
        .alerts li {
            color: #742a2a;
            margin: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        
        .alerts li:before {
            content: "⚠️";
            position: absolute;
            left: 0;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 20px auto;
            display: block;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Jarvis System Diagnostics</h1>
            <p>Real-time system monitoring and health status</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        
        <div id="dashboard" class="dashboard">
            <div class="loading">Loading system data...</div>
        </div>
        
        <div class="timestamp" id="timestamp"></div>
    </div>
    
    <script>
        async function fetchData(endpoint) {
            try {
                const response = await fetch(`/api/${endpoint}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            } catch (error) {
                console.error(`Error fetching ${endpoint}:`, error);
                return null;
            }
        }
        
        async function refreshData() {
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '<div class="loading">Loading system data...</div>';
            
            try {
                const [health, diagnostics, metrics, servers] = await Promise.all([
                    fetchData('health'),
                    fetchData('diagnostics'),
                    fetchData('metrics'),
                    fetchData('servers')
                ]);
                
                if (!health || !diagnostics) {
                    dashboard.innerHTML = '<div class="card"><h3>❌ Error</h3><p>Unable to load system data. Please check if monitoring is running.</p></div>';
                    return;
                }
                
                renderDashboard(health, diagnostics, metrics, servers);
                document.getElementById('timestamp').textContent = `Last updated: ${new Date().toLocaleString()}`;
                
            } catch (error) {
                dashboard.innerHTML = `<div class="card"><h3>❌ Error</h3><p>Failed to load data: ${error.message}</p></div>`;
            }
        }
        
        function renderDashboard(health, diagnostics, metrics, servers) {
            const dashboard = document.getElementById('dashboard');
            
            let html = '';
            
            // Health Overview Card
            html += `
                <div class="card">
                    <h3>🏥 System Health</h3>
                    <div class="health-score health-${health.status}">${health.health_score}/100</div>
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="metric-value">${health.status.toUpperCase()}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime:</span>
                        <span class="metric-value">${Math.floor(health.uptime / 60)}m</span>
                    </div>
                    ${health.issues.length > 0 ? `
                        <div class="alerts">
                            <h4>Issues Detected</h4>
                            <ul>
                                ${health.issues.map(issue => `<li>${issue}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
            
            // System Metrics Card
            if (diagnostics.current) {
                html += `
                    <div class="card">
                        <h3>📊 System Metrics</h3>
                        <div class="metric">
                            <span class="metric-label">CPU Usage:</span>
                            <span class="metric-value">${diagnostics.current.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory Usage:</span>
                            <span class="metric-value">${diagnostics.current.memory_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Disk Usage:</span>
                            <span class="metric-value">${diagnostics.current.disk_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Discord Latency:</span>
                            <span class="metric-value">${diagnostics.current.discord_latency_ms.toFixed(1)}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Process Count:</span>
                            <span class="metric-value">${diagnostics.current.process_count}</span>
                        </div>
                    </div>
                `;
            }
            
            // Servers Status Card
            if (diagnostics.servers) {
                html += `
                    <div class="card">
                        <h3>🖥️ Server Status</h3>
                        ${Object.entries(diagnostics.servers).map(([name, server]) => `
                            <div class="metric">
                                <span class="metric-label">
                                    <span class="status-indicator status-${server.status}"></span>
                                    ${name}
                                </span>
                                <span class="metric-value">
                                    ${server.status === 'running' ? 
                                        `PID: ${server.pid || 'N/A'}` : 
                                        server.status.toUpperCase()
                                    }
                                </span>
                            </div>
                            ${server.status === 'running' ? `
                                <div class="metric">
                                    <span class="metric-label">CPU:</span>
                                    <span class="metric-value">${server.cpu_percent.toFixed(1)}%</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Memory:</span>
                                    <span class="metric-value">${server.memory_mb.toFixed(1)}MB</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Response Time:</span>
                                    <span class="metric-value">${server.response_time_ms.toFixed(1)}ms</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Uptime:</span>
                                    <span class="metric-value">${server.uptime_hours.toFixed(1)}h</span>
                                </div>
                            ` : ''}
                        `).join('')}
                    </div>
                `;
            }
            
            // Performance Averages Card
            if (diagnostics.averages) {
                html += `
                    <div class="card">
                        <h3>📈 Performance Averages</h3>
                        <div class="metric">
                            <span class="metric-label">Avg CPU:</span>
                            <span class="metric-value">${diagnostics.averages.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Memory:</span>
                            <span class="metric-value">${diagnostics.averages.memory_percent.toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Discord Latency:</span>
                            <span class="metric-value">${diagnostics.averages.discord_latency_ms.toFixed(1)}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Monitoring Duration:</span>
                            <span class="metric-value">${Math.floor(diagnostics.monitoring_duration / 60)}m</span>
                        </div>
                    </div>
                `;
            }
            
            dashboard.innerHTML = html;
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
            """
            
            html_file.write_text(html_content, encoding='utf-8')
            logger.info(f"Created default dashboard template at {html_file}")
    
    async def index_handler(self, request):
        """Serve the main dashboard page."""
        html_file = self.static_dir / "dashboard.html"
        if html_file.exists():
            return web.FileResponse(html_file)
        else:
            return web.Response(text="Dashboard template not found", status=404)
    
    async def health_handler(self, request):
        """Get system health summary."""
        monitor = get_system_monitor()
        if not monitor:
            return web.json_response({"error": "System monitor not running"}, status=503)
        
        health = monitor.get_health_summary()
        return web.json_response(health)
    
    async def diagnostics_handler(self, request):
        """Get comprehensive diagnostics data."""
        monitor = get_system_monitor()
        if not monitor:
            return web.json_response({"error": "System monitor not running"}, status=503)
        
        diagnostics = monitor.get_diagnostics_data()
        return web.json_response(diagnostics)
    
    async def metrics_handler(self, request):
        """Get raw metrics data."""
        monitor = get_system_monitor()
        if not monitor:
            return web.json_response({"error": "System monitor not running"}, status=503)
        
        # Return the last 50 metrics points
        metrics = monitor.metrics_history[-50:] if monitor.metrics_history else []
        return web.json_response([asdict(m) for m in metrics])
    
    async def servers_handler(self, request):
        """Get server status information."""
        monitor = get_system_monitor()
        if not monitor:
            return web.json_response({"error": "System monitor not running"}, status=503)
        
        if not monitor.metrics_history:
            return web.json_response({"error": "No metrics available"}, status=503)
        
        latest = monitor.metrics_history[-1]
        servers_data = {}
        
        for name, server in latest.servers.items():
            servers_data[name] = {
                "status": server.status,
                "pid": server.pid,
                "uptime_hours": server.uptime_seconds / 3600,
                "cpu_percent": server.cpu_percent,
                "memory_mb": server.memory_mb,
                "response_time_ms": server.response_time_ms,
                "success_rate": (server.success_count / (server.success_count + server.error_count) * 100) if (server.success_count + server.error_count) > 0 else 0,
                "error_count": server.error_count,
                "last_heartbeat": server.last_heartbeat.isoformat()
            }
        
        return web.json_response(servers_data)
    
    async def alerts_handler(self, request):
        """Get current alerts."""
        monitor = get_system_monitor()
        if not monitor:
            return web.json_response({"error": "System monitor not running"}, status=503)
        
        if not monitor.metrics_history:
            return web.json_response({"alerts": []})
        
        latest = monitor.metrics_history[-1]
        return web.json_response({"alerts": latest.alerts})
    
    async def start(self):
        """Start the dashboard server."""
        logger.info(f"Starting diagnostics dashboard on http://{self.host}:{self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Dashboard available at: http://{self.host}:{self.port}")
        return runner


async def main():
    """Main entry point for the diagnostics dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jarvis Diagnostics Dashboard")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    dashboard = DiagnosticsDashboard(host=args.host, port=args.port)
    
    try:
        runner = await dashboard.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
    finally:
        if 'runner' in locals():
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
