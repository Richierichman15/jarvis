# Full-Featured Discord Jarvis Bot

This is the **full-featured** Discord bot that provides access to ALL Jarvis MCP tools through the Client HTTP Server. Unlike the basic bot, this version connects to multiple MCP servers (trading, system, search, jarvis) and provides comprehensive functionality.

## 🚀 **What's Different from the Basic Bot**

### **Basic Bot (`discord_jarvis_bot.py`)**
- Connects to single Jarvis HTTP server (`run_http_mcp_server.py`)
- Limited to core Jarvis tools only
- Commands: `/status`, `/memory`, `/tasks`, `/news`, `/help`

### **Full-Featured Bot (`discord_jarvis_bot_full.py`)**
- Connects to Jarvis Client HTTP Server (`run_client_http_server.py`)
- Access to ALL connected MCP servers
- **Trading tools**: `/portfolio`, `/balance`, `/positions`
- **System tools**: `/quests`, `/system`
- **Search tools**: `/search <query>`
- **Enhanced chat**: Natural language processing across all tools

## 📋 **Prerequisites**

1. **Python 3.11+** installed
2. **Discord Bot** created and configured
3. **All MCP servers** running and connected
4. **Dependencies** installed

## 🛠 **Installation**

### 1. Install Dependencies
```bash
pip install -r requirements-discord-bot.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_actual_discord_bot_token_here
DISCORD_CLIENT_ID=your_actual_discord_client_id_here
DISCORD_CLIENT_SERVER=your_actual_discord_server_id_here
DISCORD_WEBHOOK_URL=your_actual_discord_webhook_url_here

# Jarvis Client HTTP Server Configuration
JARVIS_CLIENT_URL=http://localhost:3011
```

### 3. Configure Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications/)
2. Select your bot application
3. Go to **Bot** → **Privileged Gateway Intents**
4. Enable **Message Content Intent**
5. Save changes

## 🚀 **Running the Full-Featured Bot**

### Step 1: Start the Jarvis Client HTTP Server
```bash
python run_client_http_server.py
```

This will:
- Start the FastAPI server on port 3011
- Connect to all configured MCP servers
- Provide HTTP endpoints for all tools

### Step 2: Test the Setup
```bash
python test_discord_bot_full.py
```

This will verify:
- Connection to the Client HTTP Server
- Available tools from all servers
- Command routing
- Tool functionality

### Step 3: Start the Discord Bot
```bash
python discord_jarvis_bot_full.py
```

## 🎯 **Available Commands**

### **Core Jarvis Commands**
- `/status` - System status and health
- `/memory` - Recent conversation history
- `/tasks` - All Jarvis tasks
- `/news` - Latest tech news (if search server connected)
- `/help` - Show available commands

### **Trading Commands** (if trading server connected)
- `/portfolio` - Trading portfolio overview
- `/balance` - Current trading balance
- `/positions` - Active trading positions

### **System Commands** (if system server connected)
- `/quests` - List available quests
- `/system` - System status and information

### **Search Commands** (if search server connected)
- `/search <query>` - Web search for any topic
- Example: `/search latest AI developments`

### **Natural Language**
- Any other message will be processed as natural language
- The bot will automatically route to the appropriate tool
- Example: "What's my portfolio balance?" → trading tools

## 🔧 **Server Architecture**

```
Discord Bot (discord_jarvis_bot_full.py)
    ↓ HTTP requests
Jarvis Client HTTP Server (run_client_http_server.py)
    ↓ MCP connections
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   Jarvis MCP    │  Trading MCP    │  System MCP     │  Search MCP     │
│   Server        │   Server        │   Server        │   Server        │
│                 │                 │                 │                 │
│ • jarvis_chat   │ • portfolio.*   │ • system.*      │ • search.*      │
│ • jarvis_*      │ • trading.*     │ • quests        │ • web.search    │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

## 📊 **Available Tools by Server**

### **Jarvis Server** (`jarvis`)
- `jarvis_chat` - Chat with Jarvis
- `jarvis_get_status` - System status
- `jarvis_get_memory` - Conversation history
- `jarvis_get_tasks` - Task management
- `jarvis_scan_news` - News scanning

### **Trading Server** (`trading`)
- `trading.portfolio.get_overview` - Portfolio overview
- `trading.portfolio.get_positions` - Active positions
- `trading.trading.get_balance` - Account balance
- `trading.trading.get_orders` - Order history

### **System Server** (`system`)
- `system.system.list_quests` - Available quests
- `system.system.get_status` - System status
- `system.system.complete_quest` - Complete quests

### **Search Server** (`search`)
- `search.web.search` - Web search
- `search.news.search` - News search

## 🐛 **Troubleshooting**

### **Bot Not Responding**
1. Check if Client HTTP Server is running: `http://localhost:3011/tools`
2. Verify Discord bot token in `.env` file
3. Check Discord Developer Portal for Message Content Intent

### **"Server not connected" Errors**
1. Ensure all MCP servers are running
2. Check Client HTTP Server logs for connection errors
3. Verify server configurations in `client/storage/`

### **Tool Not Found Errors**
1. Run `python test_discord_bot_full.py` to see available tools
2. Check if the specific MCP server is connected
3. Verify tool names match exactly

### **Port Conflicts**
- Client HTTP Server uses port 3011
- Basic Jarvis HTTP Server uses port 3010
- Make sure ports are not in use

## 📝 **Logs and Monitoring**

### **Log Files**
- `discord_jarvis_bot_full.log` - Discord bot logs
- Client HTTP Server logs in terminal

### **Health Checks**
- Client HTTP Server: `http://localhost:3011/servers`
- Available tools: `http://localhost:3011/tools`

### **Webhook Notifications**
If `DISCORD_WEBHOOK_URL` is configured, the bot will send error notifications to the webhook.

## 🔄 **Upgrading from Basic Bot**

If you're currently using the basic bot:

1. **Stop the basic bot** and `run_http_mcp_server.py`
2. **Start the Client HTTP Server**: `python run_client_http_server.py`
3. **Update your .env** to include `JARVIS_CLIENT_URL=http://localhost:3011`
4. **Run the full bot**: `python discord_jarvis_bot_full.py`

## 🎉 **Benefits of Full-Featured Bot**

- **Complete Access**: All MCP tools in one interface
- **Better Routing**: Natural language processing routes to correct tools
- **Enhanced Commands**: Trading, system, and search functionality
- **Scalable**: Easy to add new MCP servers
- **Robust**: Better error handling and logging

## 📞 **Support**

If you encounter issues:
1. Check the logs for error messages
2. Run the test script to verify setup
3. Ensure all servers are running and connected
4. Verify Discord bot configuration

The full-featured bot provides a complete integration with your Jarvis ecosystem, giving you access to all available tools through a single Discord interface!
