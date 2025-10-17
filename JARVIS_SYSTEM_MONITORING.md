# Jarvis System Monitoring & Self-Awareness

Jarvis now has comprehensive system monitoring capabilities with self-awareness of uptime, errors, and server load. This system provides real-time monitoring, health alerts, and a web-based diagnostics dashboard.

## 🚀 Features

### Core Monitoring Capabilities
- **CPU/Memory Tracking**: Per-server and system-wide resource monitoring
- **Active Tools Monitoring**: Response time tracking for all Jarvis tools
- **Discord Ping Latency**: Real-time Discord API latency measurement
- **MCP Server Health**: Automatic detection and monitoring of all MCP servers
- **Agent Status**: Heartbeat monitoring for modular agents (if running)
- **Process Monitoring**: Individual process resource usage and status

### Alert System
- **Discord Webhook Notifications**: Real-time alerts sent to Discord channel
- **Configurable Thresholds**: Customizable alert levels for all metrics
- **Smart Alerting**: Prevents spam with intelligent alert management
- **Health Scoring**: Overall system health score (0-100)

### Diagnostics Dashboard
- **Web Interface**: Real-time dashboard at `http://localhost:8080`
- **System Metrics**: Live CPU, memory, disk, and network statistics
- **Server Status**: Visual status indicators for all servers and agents
- **Performance History**: Historical data and trend analysis
- **Mobile Responsive**: Works on desktop and mobile devices

## 📋 Installation & Setup

### 1. Environment Configuration

Add to your `.env` file:
```env
# Discord Webhook for System Alerts
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Optional: Custom monitoring intervals
SYSTEM_MONITOR_INTERVAL=10
DISCORD_MONITOR_INTERVAL=30
```

### 2. Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to **Integrations** → **Webhooks**
3. Click **Create Webhook**
4. Copy the webhook URL
5. Add it to your `.env` file as `DISCORD_WEBHOOK_URL`

### 3. Test the Setup

```bash
# Test webhook functionality
python test_discord_webhook.py

# Test system monitoring
python -m jarvis.monitoring.system_monitor
```

## 🎯 Usage

### Automatic Integration

The system monitoring is automatically integrated into the Discord bot:

```bash
# Start the Discord bot (monitoring starts automatically)
python discord_jarvis_bot_full.py
```

### Manual Monitoring

```bash
# Start system monitoring only
python -m jarvis.monitoring.system_monitor

# Start enhanced monitoring (combines system + Discord bot monitoring)
python -m jarvis.monitoring.enhanced_monitor

# Start diagnostics dashboard
python -m jarvis.monitoring.diagnostics_dashboard
```

### Discord Commands

- `/diagnostics` - Get comprehensive system health status
- `/status` - Quick system overview
- `/health` - Detailed health metrics

## 📊 Monitoring Components

### SystemMonitor Class

The core monitoring class that provides:

```python
from jarvis.monitoring import SystemMonitor

# Create monitor instance
monitor = SystemMonitor(
    monitoring_interval=10,  # seconds
    discord_webhook_url="your_webhook_url"
)

# Start monitoring
await monitor.start_monitoring()

# Get health summary
health = monitor.get_health_summary()
print(f"Health Score: {health['health_score']}/100")

# Get detailed diagnostics
diagnostics = monitor.get_diagnostics_data()
```

### Metrics Collected

#### System Metrics
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Network I/O statistics
- Process count
- Discord API latency

#### Server Metrics (per server)
- Process status (running/stopped/error)
- CPU usage percentage
- Memory usage (MB)
- Response time (ms)
- Uptime (hours)
- Success/error rates
- Last heartbeat timestamp

#### Agent Metrics (if agent system is running)
- Health endpoint response time
- Agent status
- Communication latency

### Alert Thresholds

Default alert thresholds (configurable):

```python
alert_thresholds = {
    'cpu_percent': 80.0,           # CPU usage > 80%
    'memory_percent': 85.0,        # Memory usage > 85%
    'disk_percent': 90.0,          # Disk usage > 90%
    'response_time_ms': 5000.0,    # Response time > 5 seconds
    'discord_latency_ms': 1000.0,  # Discord latency > 1 second
    'error_rate_percent': 10.0     # Error rate > 10%
}
```

## 🖥️ Diagnostics Dashboard

### Accessing the Dashboard

1. Start the dashboard server:
   ```bash
   python -m jarvis.monitoring.diagnostics_dashboard
   ```

2. Open your browser to: `http://localhost:8080`

### Dashboard Features

#### Health Overview
- Overall health score (0-100)
- System status (excellent/good/fair/poor)
- Current issues and alerts
- System uptime

#### System Metrics
- Real-time CPU, memory, and disk usage
- Discord API latency
- Process count
- Network I/O statistics

#### Server Status
- Visual status indicators for all servers
- Individual server metrics (CPU, memory, response time)
- Server uptime and success rates
- Error counts and rates

#### Performance Averages
- Average metrics over time
- Monitoring duration
- Historical performance trends

### API Endpoints

The dashboard also provides REST API endpoints:

- `GET /api/health` - System health summary
- `GET /api/diagnostics` - Comprehensive diagnostics data
- `GET /api/metrics` - Raw metrics data
- `GET /api/servers` - Server status information
- `GET /api/alerts` - Current alerts

## 🔧 Configuration

### Customizing Monitoring

```python
# Custom alert thresholds
custom_thresholds = {
    'cpu_percent': 70.0,    # More sensitive to CPU usage
    'memory_percent': 80.0, # More sensitive to memory usage
    'disk_percent': 85.0,   # More sensitive to disk usage
}

# Create monitor with custom settings
monitor = SystemMonitor(
    monitoring_interval=5,  # Check every 5 seconds
    alert_thresholds=custom_thresholds,
    discord_webhook_url="your_webhook_url"
)
```

### Server Configuration

The monitor automatically detects these servers:

```python
server_configs = {
    'jarvis_client': {
        'url': 'http://localhost:3012',
        'health_endpoint': '/health',
        'process_name': 'run_client_http_server.py'
    },
    'discord_bot': {
        'process_name': 'discord_jarvis_bot_full.py'
    },
    'search_server': {
        'process_name': 'search/mcp_server.py'
    },
    'music_server': {
        'process_name': 'music_server.py'
    },
    'trading_server': {
        'process_name': 'trading_mcp_server.py'
    },
    'system_server': {
        'process_name': 'system_server.py'
    }
}
```

## 🚨 Alert Examples

### System Resource Alerts
```
🚨 Jarvis System Alert

Time: 2024-01-15 14:30:25

Issues Detected:
• High CPU usage: 85.2%
• High memory usage: 88.7%
• Server search_server is not running

System Status:
• CPU: 85.2%
• Memory: 88.7%
• Disk: 45.3%
• Discord Latency: 125.4ms
```

### Server Health Alerts
```
🚨 Jarvis System Alert

Time: 2024-01-15 14:35:10

Issues Detected:
• Server trading_server slow response: 6.2s
• Server music_server high error rate: 15.3%

System Status:
• CPU: 45.2%
• Memory: 62.1%
• Disk: 45.3%
• Discord Latency: 98.7ms
```

## 🔍 Troubleshooting

### Common Issues

#### Discord Webhook Not Working
1. Check `DISCORD_WEBHOOK_URL` in `.env` file
2. Verify webhook URL is correct and not deleted
3. Test with: `python test_discord_webhook.py`

#### System Monitor Not Starting
1. Check dependencies: `pip install psutil aiohttp`
2. Verify permissions for process monitoring
3. Check logs for specific error messages

#### Dashboard Not Loading
1. Ensure dashboard server is running
2. Check port 8080 is not in use
3. Verify firewall settings

#### High False Positive Alerts
1. Adjust alert thresholds in configuration
2. Increase monitoring interval
3. Check for system resource constraints

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Health Check Commands

```bash
# Test webhook
python test_discord_webhook.py

# Test system monitor
python -c "from jarvis.monitoring import SystemMonitor; print('SystemMonitor imported successfully')"

# Check dashboard
curl http://localhost:8080/api/health
```

## 📈 Performance Impact

The monitoring system is designed to be lightweight:

- **CPU Usage**: < 1% on modern systems
- **Memory Usage**: ~10-20MB
- **Network**: Minimal (only webhook notifications)
- **Disk I/O**: Minimal (only log files)

### Optimization Tips

1. **Adjust Monitoring Interval**: Increase interval for less frequent checks
2. **Disable Unused Servers**: Remove server configs for unused services
3. **Limit History**: Reduce `max_history` for less memory usage
4. **Selective Monitoring**: Monitor only critical servers

## 🔮 Future Enhancements

### Planned Features
- **Predictive Alerts**: ML-based anomaly detection
- **Custom Dashboards**: User-configurable dashboard layouts
- **Historical Analytics**: Long-term trend analysis
- **Mobile App**: Native mobile app for monitoring
- **Integration APIs**: REST API for external monitoring tools
- **Automated Recovery**: Auto-restart failed services
- **Performance Optimization**: Automatic system tuning recommendations

### Integration Opportunities
- **Grafana**: Export metrics to Grafana dashboards
- **Prometheus**: Prometheus metrics endpoint
- **Slack**: Slack webhook integration
- **Email**: Email alert notifications
- **PagerDuty**: Incident management integration

## 📚 API Reference

### SystemMonitor Class

```python
class SystemMonitor:
    def __init__(self, monitoring_interval=10, alert_thresholds=None, discord_webhook_url=None)
    async def start_monitoring()
    def stop_monitoring()
    def get_health_summary() -> Dict[str, Any]
    def get_diagnostics_data() -> Dict[str, Any]
```

### Global Functions

```python
async def start_system_monitoring(interval=10, webhook_url=None) -> SystemMonitor
def get_system_monitor() -> Optional[SystemMonitor]
def stop_system_monitoring()
```

### Data Structures

```python
@dataclass
class ServerMetrics:
    name: str
    pid: Optional[int]
    status: str
    cpu_percent: float
    memory_mb: float
    response_time_ms: float
    uptime_seconds: float
    last_heartbeat: datetime
    error_count: int
    success_count: int

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    discord_latency_ms: float
    servers: Dict[str, ServerMetrics]
    alerts: List[str]
```

## 🎉 Conclusion

Jarvis now has comprehensive self-awareness and monitoring capabilities that provide:

- **Real-time system health monitoring**
- **Proactive alerting via Discord**
- **Beautiful web-based diagnostics dashboard**
- **Historical performance tracking**
- **Automated server health checks**
- **Configurable alert thresholds**

This monitoring system ensures Jarvis can detect and report issues before they become critical, providing you with peace of mind and proactive system management.

For support or feature requests, please check the logs and use the troubleshooting guide above.
