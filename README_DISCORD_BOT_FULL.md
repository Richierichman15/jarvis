# 🚀 Full-Featured Discord Jarvis Bot

A comprehensive Discord bot that provides access to **ALL** Jarvis MCP tools through a single interface. This bot connects to multiple MCP servers (trading, system, search, jarvis) and offers enhanced functionality compared to the basic bot.

## 🎯 **What Makes This "Full-Featured"?**

### **Basic Bot vs Full-Featured Bot**

| Feature | Basic Bot | Full-Featured Bot |
|---------|-----------|-------------------|
| **Server Access** | Single Jarvis server only | ALL connected MCP servers |
| **Trading Tools** | ❌ Not available | ✅ Portfolio, balance, positions |
| **System Tools** | ❌ Not available | ✅ Quests, system status |
| **Search Tools** | ❌ Limited | ✅ Web search, news search |
| **Natural Language** | ❌ Basic routing | ✅ Advanced routing across all tools |
| **Commands** | 5 basic commands | 10+ enhanced commands |

## 📋 **Prerequisites**

- **Python 3.11+** installed
- **Discord Bot** created and configured
- **All MCP servers** running and connected
- **Dependencies** installed

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
JARVIS_CLIENT_URL=http://localhost:3012
```

### 3. Configure Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications/)
2. Select your bot application
3. Go to **Bot** → **Privileged Gateway Intents**
4. Enable **Message Content Intent**
5. Save changes

## 🚀 **Quick Start**

### Step 1: Start the Jarvis Client HTTP Server
```bash
python -m uvicorn client.api:create_app --host 0.0.0.0 --port 3012 --factory
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3012 (Press CTRL+C to quit)
```

### Step 2: Test the Setup
```bash
python test_discord_bot_full.py
```

**Expected Output:**
```
Full-Featured Discord Jarvis Bot - Test Suite
==================================================
Testing Jarvis Client HTTP Server connection...
✅ Connected to Jarvis Client HTTP Server
📊 Available servers: ['jarvis', 'trading', 'system', 'search']
🔧 Total tools available: 25

Testing tool calls across servers...
  '/status' → 'jarvis_get_status' on 'jarvis' with args: {}
  '/portfolio' → 'trading.portfolio.get_overview' on 'trading' with args: {}
  '/balance' → 'trading.trading.get_balance' on 'trading' with args: {}
  '/positions' → 'trading.portfolio.get_positions' on 'trading' with args: {}
  '/quests' → 'system.system.list_quests' on 'system' with args: {}
  '/system' → 'system.system.get_status' on 'system' with args: {}
  '/news' → 'jarvis_scan_news' on 'jarvis' with args: {}
  '/memory' → 'jarvis_get_memory' on 'jarvis' with args: {'limit': 10}
  '/tasks' → 'jarvis_get_tasks' on 'jarvis' with args: {'status': 'all'}
  '/search latest AI news' → 'search.web.search' on 'search' with args: {'query': 'latest AI news'}
  'Hello Jarvis' → 'natural_language' on 'default' with args: {'query': 'Hello Jarvis'}
✅ Command routing test completed

==================================================
✅ All tests passed! Full-featured bot is ready to run.
```

### Step 3: Start the Discord Bot
```bash
python discord_jarvis_bot_full.py
```

**Expected Output:**
```
Starting Full-Featured Discord Jarvis Bot...
Connecting to Jarvis Client HTTP Server: http://localhost:3012
Loaded 25 tools from 4 servers
✅ Bot connected to Discord!
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
    ↓ HTTP requests to port 3012
Jarvis Client HTTP Server (client.api)
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
1. **Check if Client HTTP Server is running:**
   ```bash
   curl http://localhost:3012/servers
   ```
   Should return JSON with connected servers.

2. **Verify Discord bot token in `.env` file:**
   ```env
   DISCORD_BOT_TOKEN=your_actual_token_here
   ```

3. **Check Discord Developer Portal:**
   - Go to your bot application
   - Bot → Privileged Gateway Intents
   - Enable "Message Content Intent"

### **"Server not connected" Errors**
1. **Ensure all MCP servers are running:**
   ```bash
   # Check if servers are running
   python client/cli.py
   ```

2. **Check Client HTTP Server logs for connection errors**

3. **Verify server configurations in `client/storage/`**

### **Tool Not Found Errors**
1. **Run the test script to see available tools:**
   ```bash
   python test_discord_bot_full.py
   ```

2. **Check if the specific MCP server is connected**

3. **Verify tool names match exactly**

### **Port Conflicts**
- **Client HTTP Server uses port 3012**
- **Basic Jarvis HTTP Server uses port 3010**
- **Make sure ports are not in use:**
  ```bash
  netstat -ano | findstr :3012
  ```

### **Common Error Messages**

| Error | Solution |
|-------|----------|
| `Cannot connect to host localhost:3012` | Start the Client HTTP Server |
| `Invalid Discord bot token` | Check your `.env` file |
| `Privileged intents not enabled` | Enable Message Content Intent in Discord Developer Portal |
| `Server 'trading' not connected` | Ensure trading MCP server is running |
| `Tool 'trading.portfolio.get_overview' not found` | Check if trading server is connected |

## 📝 **Logs and Monitoring**

### **Log Files**
- `discord_jarvis_bot_full.log` - Discord bot logs
- Client HTTP Server logs in terminal

### **Health Checks**
- **Client HTTP Server:** `http://localhost:3012/servers`
- **Available tools:** `http://localhost:3012/tools`

### **Webhook Notifications**
If `DISCORD_WEBHOOK_URL` is configured, the bot will send error notifications to the webhook.

## 🔄 **Upgrading from Basic Bot**

If you're currently using the basic bot:

1. **Stop the basic bot** and `run_http_mcp_server.py`
2. **Start the Client HTTP Server:**
   ```bash
   python -m uvicorn client.api:create_app --host 0.0.0.0 --port 3012 --factory
   ```
3. **Update your .env** to include:
   ```env
   JARVIS_CLIENT_URL=http://localhost:3012
   ```
4. **Run the full bot:**
   ```bash
   python discord_jarvis_bot_full.py
   ```

## 🎉 **Benefits of Full-Featured Bot**

- **Complete Access**: All MCP tools in one interface
- **Better Routing**: Natural language processing routes to correct tools
- **Enhanced Commands**: Trading, system, and search functionality
- **Scalable**: Easy to add new MCP servers
- **Robust**: Better error handling and logging
- **Unified Interface**: Single Discord bot for all Jarvis functionality

## 📞 **Support**

If you encounter issues:

1. **Check the logs** for error messages
2. **Run the test script** to verify setup
3. **Ensure all servers are running** and connected
4. **Verify Discord bot configuration**

## 🚀 **Next Steps**

Once your bot is running:

1. **Test all commands** in Discord
2. **Set up webhook notifications** for error monitoring
3. **Customize commands** by modifying `DiscordCommandRouter`
4. **Add new MCP servers** by connecting them to the Client HTTP Server

The full-featured bot provides a complete integration with your Jarvis ecosystem, giving you access to all available tools through a single Discord interface!

---

**Happy chatting with Jarvis! 🤖✨**
