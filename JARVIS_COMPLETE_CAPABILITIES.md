# 🤖 Jarvis - Complete Capabilities Guide

**Your AI Assistant with 60+ Tools and Features**

Jarvis is a comprehensive AI assistant that can help you with trading, system management, fitness, music, news, web search, and much more. This guide covers everything Jarvis can do.

---

## 🎯 **Quick Start**

### **Discord Bot Commands**
- Type `/help` in Discord to see available commands
- Use natural language: "What's my portfolio balance?"
- All commands work in Discord when the bot is running

### **Direct CLI Access**
```bash
# Start Jarvis CLI
python -m jarvis.cli

# Start HTTP API server
python run_client_http_server.py

# Start Discord bot
python discord_jarvis_bot_full.py
```

---

## 💰 **Trading & Finance (15+ Tools)**

### **Portfolio Management**
| Command | Description | Example |
|---------|-------------|---------|
| `/portfolio` | Get trading portfolio overview | `/portfolio` |
| `/balance` | Get current trading balance | `/balance` |
| `/positions` | Get active trading positions | `/positions` |
| `/paper` | Get paper trading portfolio balance | `/paper` |
| `/performance` | Get portfolio performance metrics | `/performance` |
| `/export` | Export portfolio data to CSV | `/export` |

### **Market Data & Analysis**
| Command | Description | Example |
|---------|-------------|---------|
| `/price <symbol>` | Get current price for symbol | `/price BTC` |
| `/ohlcv <symbol>` | Get OHLCV data for symbol | `/ohlcv ETH` |
| `/pairs <query>` | Search for trading pairs | `/pairs BTC` |
| `/momentum` | Get momentum signals for crypto | `/momentum` |
| `/doctor` | Run trading system diagnostics | `/doctor` |

### **Trade History & Analysis**
| Command | Description | Example |
|---------|-------------|---------|
| `/trades` | Get recent trade executions (last 20) | `/trades` |
| `/history` | Get complete trade history | `/history` |
| `/pnl` | Get profit/loss summary | `/pnl` |
| `/state` | Get current trading system state | `/state` |
| `/exit` | Get exit engine status | `/exit` |

### **Natural Language Trading**
- "Show me my portfolio balance"
- "What's the current price of Bitcoin?"
- "Get my recent trades"
- "Show me my profit and loss"
- "What are the momentum signals?"

---

## 🎵 **Music & Entertainment (15+ Commands)**

### **Playback Control**
| Command | Description | Example |
|---------|-------------|---------|
| `/play [song_name]` | Play song or resume if paused | `/play 90210` |
| `/pause` | Pause currently playing song | `/pause` |
| `/resume` | Resume playback if paused | `/resume` |
| `/stop` | Stop playback and clear queue | `/stop` |
| `/skip` | Skip to next song in queue | `/skip` |
| `/random` | Add random song to queue | `/random` |

### **Queue Management**
| Command | Description | Example |
|---------|-------------|---------|
| `/queue` | View current music queue | `/queue` |
| `/queue [song_name]` | Add song to queue | `/queue Flawless` |
| `/queue clear` | Clear all songs from queue | `/queue clear` |
| `/queue remove [position]` | Remove song by position | `/queue remove 3` |
| `/nowplaying` | Show currently playing song | `/nowplaying` |

### **Discovery & Search**
| Command | Description | Example |
|---------|-------------|---------|
| `/songs` | List all available songs | `/songs` |
| `/findsong [keyword]` | Search for songs by keyword | `/findsong travis` |
| `/mcpqueue` | View MCP server queue status | `/mcpqueue` |

### **Voice Channel Control**
| Command | Description | Example |
|---------|-------------|---------|
| `/join` | Join your voice channel | `/join` |
| `/leave` | Leave voice channel | `/leave` |
| `/volume [level]` | Set volume (0-100) | `/volume 50` |

### **Supported Audio Formats**
- MP3, FLAC, WAV, M4A, OGG, AAC, WMA

---

## 📰 **News & Web Search (5+ Tools)**

### **News & Information**
| Command | Description | Example |
|---------|-------------|---------|
| `/news` | Scan latest tech news (AI, Crypto, Finance) | `/news` |
| `/search <query>` | Web search for any topic | `/search latest AI developments` |

### **Natural Language Search**
- "Get me the latest news about AI"
- "Search for information about Bitcoin"
- "Find news about Tesla stock"
- "What's happening in the crypto market?"

---

## 🏋️ **Fitness & Workouts (10+ Categories)**

### **Workout Categories Available**
- **Chest**: Push-ups, Bench Press, Incline Dumbbell Press, Chest Fly
- **Back**: Pull-ups, Deadlifts, Bent-Over Rows, Lat Pulldowns
- **Legs**: Squats, Lunges, Leg Press, Calf Raises
- **Arms**: Bicep Curls, Tricep Dips, Hammer Curls, Overhead Press
- **Shoulders**: Lateral Raises, Arnold Press, Front Raises
- **Core**: Planks, Crunches, Russian Twists, Mountain Climbers
- **Cardio**: Running, Cycling, Jump Rope, Burpees
- **Push**: Push-ups, Bench Press, Overhead Press, Lateral Raises
- **Pull**: Pull-ups, Deadlifts, Bent-Over Rows, Barbell Curl

### **Workout Features**
- **Equipment Types**: Bodyweight, Barbell, Dumbbell, Machine
- **Difficulty Levels**: Beginner, Intermediate, Advanced
- **Workout Types**: Strength, Hypertrophy, Endurance
- **Detailed Instructions**: Reps, sets, and descriptions for each exercise

### **Natural Language Fitness**
- "Show me chest workouts"
- "What are some beginner leg exercises?"
- "Find bodyweight workouts"
- "Show me strength training exercises"

---

## 🎮 **System & Quest Management (10+ Tools)**

### **System Status & Monitoring**
| Command | Description | Example |
|---------|-------------|---------|
| `/status` | Get Jarvis system status | `/status` |
| `/system` | Get system status (XP, goals) | `/system` |
| `/memory` | Get recent conversation history | `/memory` |
| `/tasks` | Get all Jarvis tasks | `/tasks` |

### **Quest & Goal Management**
| Command | Description | Example |
|---------|-------------|---------|
| `/quests` | List available quests/tasks | `/quests` |

### **Natural Language System**
- "What's my system status?"
- "Show me my recent conversations"
- "What tasks do I have?"
- "List my available quests"

---

## 🔧 **Technical Tools & Utilities (15+ Tools)**

### **File Operations**
- Read, write, and list files and directories
- File search and management
- Directory navigation

### **System Information**
- CPU and memory usage monitoring
- System resource tracking
- Performance metrics

### **Code Editor**
- Edit code in various programming languages
- Syntax highlighting
- Code execution capabilities

### **Calculator**
- Mathematical calculations
- Unit conversions
- Complex mathematical operations

### **Web Research**
- Advanced web search capabilities
- Information gathering and analysis
- Research automation

---

## 📊 **Event Monitoring & Notifications**

### **Trading Event Monitoring**
| Command | Description | Example |
|---------|-------------|---------|
| `/events start` | Start real-time trading notifications | `/events start` |
| `/events stop` | Stop trading notifications | `/events stop` |
| `/events stats` | Get event statistics | `/events stats` |
| `/events history [limit]` | Get event history | `/events history 10` |
| `/events test [type]` | Send test event | `/events test market_alert` |
| `/events check` | Manually check markets | `/events check` |

### **Event Types Monitored**
- **Market Alerts**: Price changes, volume spikes
- **Trade Executions**: Buy/sell orders completed
- **Risk Limits**: Daily loss limits reached
- **Daily Summaries**: Performance reports

---

## 💬 **Natural Language Processing**

### **Chat & Conversation**
- Intelligent conversation with context awareness
- Follow-up question handling
- Conversation history tracking
- Multi-turn dialogue support

### **Command Routing**
- Automatic command detection from natural language
- Intent recognition and routing
- Context-aware responses
- Smart follow-up suggestions

### **Examples of Natural Language**
- "What's my portfolio balance?" → Trading tools
- "Play some music" → Music player
- "Show me chest workouts" → Fitness tools
- "What's the latest news?" → News scanning
- "How are you doing?" → Chat response
- "What time is it?" → Date/time information

---

## 🚀 **Advanced Features**

### **Multi-Server Architecture**
- **Jarvis Server**: Core AI and system management
- **Trading Server**: Financial data and portfolio management
- **System Server**: Quest and goal tracking
- **Search Server**: Web search and research
- **Music Server**: Audio playback and management

### **MCP (Model Context Protocol) Integration**
- Standardized tool communication
- Extensible architecture
- Multiple server connections
- Tool aggregation and routing

### **Automatic Recovery & Stability**
- Session management with auto-reconnection
- Health monitoring and diagnostics
- Error handling with retry logic
- Graceful degradation on failures

### **Real-time Monitoring**
- System resource tracking
- Connection health checks
- Performance metrics
- Automatic restart capabilities

---

## 🛠️ **Setup & Configuration**

### **Required Services**
1. **Jarvis Client HTTP Server** (Port 3012)
2. **Discord Bot** (with bot token)
3. **MCP Servers** (Trading, System, Search, Music)

### **Environment Variables**
```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SERVER=your_server_id

# Optional
DISCORD_WEBHOOK_URL=your_webhook_url
EVENT_NOTIFICATION_CHANNEL_ID=your_channel_id
JARVIS_CLIENT_URL=http://localhost:3012
```

### **Quick Start Commands**
```bash
# Start all services
python run_client_http_server.py &
python discord_jarvis_bot_full.py &

# Or use the service manager
python start_discord_bot_service.py

# Monitor system health
python monitor_discord_bot.py
```

---

## 📋 **Complete Tool List (60+ Tools)**

### **Trading Tools (15)**
- `trading.get_price` - Get current price
- `trading.get_ohlcv` - Get OHLCV data
- `trading.search_pairs` - Search trading pairs
- `trading.doctor` - System diagnostics
- `trading.get_balance` - Get exchange balance
- `trading.get_positions` - Get open positions
- `trading.get_trade_history` - Get trade history
- `trading.get_pnl_summary` - Get P&L summary
- `trading.get_recent_executions` - Get recent trades
- `trading.get_portfolio_balance` - Paper trading balance
- `trading.get_momentum_signals` - Momentum signals
- `portfolio.get_overview` - Portfolio overview
- `portfolio.get_positions` - Current positions
- `portfolio.get_trades` - Recent trades
- `portfolio.get_performance` - Performance metrics

### **Jarvis Core Tools (10)**
- `jarvis_chat` - Chat with Jarvis AI
- `jarvis_get_status` - System status
- `jarvis_get_system_info` - Detailed system info
- `jarvis_get_memory` - Conversation history
- `jarvis_get_tasks` - All tasks
- `jarvis_scan_news` - Scan news sources
- `jarvis_web_search` - Web search
- `jarvis_schedule_task` - Schedule tasks
- `jarvis_get_weather` - Weather information
- `jarvis_calculate` - Mathematical calculations

### **System Tools (8)**
- `system.system.list_quests` - List quests
- `system.system.get_status` - System status
- `system.system.create_quest` - Create quest
- `system.system.update_quest` - Update quest
- `system.system.complete_quest` - Complete quest
- `system.system.get_goals` - Get goals
- `system.system.set_goal` - Set goal
- `system.system.track_progress` - Track progress

### **Music Tools (12)**
- `music.play_song` - Play specific song
- `music.play_random` - Play random song
- `music.search_songs` - Search songs
- `music.list_songs` - List all songs
- `music.add_to_queue` - Add to queue
- `music.get_queue` - Get queue status
- `music.clear_queue` - Clear queue
- `music.remove_from_queue` - Remove from queue
- `music.play_next` - Play next song
- `music.pause` - Pause playback
- `music.resume` - Resume playback
- `music.stop` - Stop playback

### **Fitness Tools (5)**
- `fitness.list_workouts` - List workouts by category
- `fitness.search_workouts` - Search workouts
- `fitness.get_workout_plan` - Get workout plan
- `fitness.track_workout` - Track workout
- `fitness.get_progress` - Get fitness progress

### **Utility Tools (10+)**
- `web_search` - Web search
- `calculator` - Mathematical calculations
- `file_operations` - File management
- `system_info` - System information
- `code_editor` - Code editing
- `web_researcher` - Advanced research
- `debug` - Debugging tools
- `weather` - Weather information
- `time` - Time and date
- `converter` - Unit conversions

---

## 🎉 **Getting Started**

### **1. Start the Services**
```bash
# Start the HTTP server
python run_client_http_server.py

# Start the Discord bot
python discord_jarvis_bot_full.py
```

### **2. Test Basic Commands**
```
/status          # Check if everything is working
/portfolio       # Check your portfolio
/price BTC       # Get Bitcoin price
/news            # Get latest news
/help            # See all commands
```

### **3. Try Natural Language**
```
"What's my portfolio balance?"
"Play some music"
"Show me chest workouts"
"Get the latest news about AI"
```

### **4. Explore Advanced Features**
```
/events start    # Start trading notifications
/play 90210      # Play specific song
/queue random    # Add random songs
/quests          # See available quests
```

---

## 🔍 **Troubleshooting**

### **Common Issues**
1. **"Session is closed" errors** - Bot will auto-reconnect
2. **Music not playing** - Check FFmpeg installation
3. **Trading data not loading** - Verify API credentials
4. **Bot not responding** - Check if services are running

### **Monitoring & Diagnostics**
```bash
# Monitor system health
python monitor_discord_bot.py

# Check service logs
tail -f discord_jarvis_bot_full.log

# Test individual tools
python -m jarvis.cli
```

### **Service Management**
```bash
# Use service manager for auto-restart
python start_discord_bot_service.py

# Or use Windows batch file
start_discord_bot.bat
```

---

## 📚 **Additional Resources**

- **Discord Bot Commands**: `DISCORD_BOT_COMMANDS.md`
- **Music Commands**: `MUSIC_COMMANDS.md`
- **Trading Tools**: `TRADING_MCP_TOOLS_REFERENCE.md`
- **Setup Guide**: `MCP_SETUP_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

**Jarvis is your comprehensive AI assistant with 60+ tools covering trading, music, fitness, news, system management, and much more. Start with basic commands and explore the full range of capabilities!**

*Last updated: January 2025*
