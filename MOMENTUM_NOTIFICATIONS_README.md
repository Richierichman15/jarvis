# 📊 Momentum Notification Service

Automated Discord notifications for trading momentum signals every 3 hours.

## 🚀 Features

- **⏰ Scheduled Notifications**: Sends momentum updates every 3 hours automatically
- **📱 Discord Integration**: Rich embeds with momentum signals sent to your Discord channel
- **🤖 AI-Powered Formatting**: Uses the same AI formatter as the Discord bot for natural, readable messages
- **📊 Smart Data Parsing**: Automatically formats momentum signals with emojis, percentages, and signal strength
- **🔄 Continuous Operation**: Runs as a background service
- **🧪 Test Mode**: Send test notifications to verify setup
- **📊 Status Monitoring**: Check service status and configuration
- **🛡️ Error Handling**: Robust error handling with automatic retries

## 📋 Prerequisites

1. **Python 3.7+** installed
2. **Discord Webhook URL** configured
3. **Jarvis Client HTTP Server** running (default: http://localhost:3012)
4. **Trading MCP Server** connected and operational

## ⚙️ Setup

### 1. Environment Configuration

Add to your `.env` file:

```env
# Discord Webhook for Momentum Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Jarvis Client URL (optional, defaults to localhost:3012)
JARVIS_CLIENT_URL=http://localhost:3012
```

### 2. Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to **Integrations** → **Webhooks**
3. Click **Create Webhook**
4. Choose the channel where you want momentum notifications
5. Copy the webhook URL
6. Add it to your `.env` file as `DISCORD_WEBHOOK_URL`

### 3. Install Dependencies

The service uses these Python packages (should already be installed):
- `aiohttp` - HTTP client for API calls
- `python-dotenv` - Environment variable loading

## 🚀 Usage

### Quick Start (Windows)

```bash
# Double-click the batch file or run:
start_momentum_notifications.bat
```

### Command Line Usage

```bash
# Check environment configuration
python start_momentum_notifications.py check

# Test the service (sends one test notification)
python start_momentum_notifications.py test

# Start the service (runs continuously)
python start_momentum_notifications.py start

# Show service status
python start_momentum_notifications.py status
```

### Direct Service Usage

```bash
# Run the service directly
python momentum_notification_service.py
```

## 📊 What You'll Receive

Every 3 hours, you'll get a Discord notification with:

- **📈 Momentum Signals**: Current momentum indicators for various trading pairs
- **💰 Price Information**: Current prices and percentage changes
- **📊 Market Direction**: Bullish/Bearish/Neutral signals
- **⏰ Next Update Time**: When the next notification will be sent
- **🔄 Service Status**: Confirmation the service is running

### Example Notification

**AI-Formatted (Primary):**
```
🚀 Momentum Signals Update (last updated: 2025-10-20)

- Bitcoin (BTC-USD): 
  - Current Price: $110,555
  - 6h Momentum: 2.27% 📈
  - 24h Momentum: 3.52% 📈
  - Signal Strength: Weak Up

- Ethereum (ETH-USD):
  - Current Price: $4,050.15
  - 6h Momentum: 2.71% 📈
  - 24h Momentum: 4.32% 📈
  - Signal Strength: Weak Up

Keep an eye on these trends!
```

**Fallback Format (if AI unavailable):**
```
📈 BTC/USD: $110,555.00 | 6h: +2.27% | 24h: +3.52% | WEAK_UP
📈 ETH/USD: $4,050.15 | 6h: +2.71% | 24h: +4.32% | WEAK_UP
📈 SOL/USD: $192.13 | 6h: +3.46% | 24h: +3.51% | WEAK_UP
```

## 🛠️ Configuration

### Customizing the Interval

To change the notification interval, edit `momentum_notification_service.py`:

```python
# Change this line (currently 3 hours)
self.notification_interval = 3 * 60 * 60  # 3 hours in seconds

# Examples:
# 1 hour: 1 * 60 * 60
# 6 hours: 6 * 60 * 60
# 12 hours: 12 * 60 * 60
```

### Customizing the Discord Message

The service creates rich Discord embeds. You can customize the appearance by modifying the `_create_momentum_embed()` method in `momentum_notification_service.py`.

## 📝 Logging

The service creates detailed logs in `momentum_notifications.log`:

- **Service startup/shutdown events**
- **Notification sending attempts**
- **Error messages and retries**
- **API call results**

## 🔧 Troubleshooting

### Common Issues

**❌ "DISCORD_WEBHOOK_URL not set"**
- Make sure you've added the webhook URL to your `.env` file
- Verify the webhook URL is correct and active

**❌ "No momentum data received"**
- Check that the Jarvis Client HTTP Server is running
- Verify the trading MCP server is connected
- Test the momentum tool manually: `/momentum` in Discord

**❌ "Discord webhook failed"**
- Verify the webhook URL is correct
- Check that the Discord channel still exists
- Ensure the bot has permission to send messages

**❌ "Timeout while fetching momentum signals"**
- The Jarvis server might be overloaded
- Check server logs for errors
- Try restarting the Jarvis services

### Testing the Setup

1. **Test Environment**:
   ```bash
   python start_momentum_notifications.py check
   ```

2. **Test Notification**:
   ```bash
   python start_momentum_notifications.py test
   ```

3. **Check Service Status**:
   ```bash
   python start_momentum_notifications.py status
   ```

## 🔄 Running as a Service

### Windows Service (Advanced)

You can run this as a Windows service using tools like:
- **NSSM** (Non-Sucking Service Manager)
- **Windows Task Scheduler**

### Background Process (Linux/Mac)

```bash
# Run in background
nohup python momentum_notification_service.py > momentum_service.log 2>&1 &

# Check if running
ps aux | grep momentum_notification_service

# Stop the service
pkill -f momentum_notification_service
```

## 📊 Monitoring

### Service Health

The service includes built-in monitoring:
- **Automatic retries** on failures
- **Detailed logging** of all operations
- **Status indicators** in Discord notifications
- **Error reporting** with context

### Integration with Existing Monitoring

This service can be integrated with your existing Jarvis monitoring system by:
- Adding it to the system monitor dashboard
- Including it in health checks
- Sending alerts if the service stops

## 🛡️ Security

- **No sensitive data** is logged or transmitted
- **Webhook URLs** should be kept secure
- **Environment variables** are loaded from `.env` file
- **No persistent storage** of trading data

## 📈 Performance

- **Lightweight**: Minimal resource usage
- **Efficient**: Only runs every 3 hours
- **Resilient**: Handles network issues gracefully
- **Scalable**: Can be run on multiple machines

## 🤝 Support

If you encounter issues:

1. **Check the logs** in `momentum_notifications.log`
2. **Verify configuration** with the check command
3. **Test the setup** with the test command
4. **Check Jarvis services** are running properly

## 🔄 Updates

To update the service:
1. Stop the running service
2. Replace the files with new versions
3. Restart the service

The service will automatically resume its 3-hour schedule from the next interval.
