# JARVIS Multi-Agent System Restart Instructions

## Environment Setup

Before starting the JARVIS multi-agent system, ensure the DATA_PATH environment variable is set correctly.

### Windows (PowerShell)
```powershell
# Set DATA_PATH environment variable
$env:DATA_PATH = "E:\Richie\github\jarvis\data"

# Verify the path exists
Test-Path $env:DATA_PATH

# Start the system
python discord_jarvis_bot_full.py
```

### Windows (Command Prompt)
```cmd
# Set DATA_PATH environment variable
set DATA_PATH=E:\Richie\github\jarvis\data

# Verify the path exists
dir %DATA_PATH%

# Start the system
python discord_jarvis_bot_full.py
```

### Linux/macOS
```bash
# Set DATA_PATH environment variable
export DATA_PATH="/home/richie/jarvis/data"

# Verify the path exists
ls -la $DATA_PATH

# Start the system
python discord_jarvis_bot_full.py
```

## Data Directory Structure

The system expects the following directory structure:
```
jarvis/
├── data/
│   ├── live/
│   │   ├── live_portfolio_state.json
│   │   ├── live_trades.json
│   │   └── exit_engine_state.json
│   └── system/
│       ├── quests.json
│       ├── goals.json
│       └── system_status.json
└── logs/
    └── agent_startup.log
```

## Agent Startup Process

When agents start, they will:

1. **Load DATA_PATH** from environment variables
2. **Log startup information** including:
   - Current working directory
   - DATA_PATH value
   - Absolute paths to data files
   - File existence status
3. **Create missing directories** automatically
4. **Create placeholder data files** if they don't exist
5. **Start normal operation**

## Startup Logs

All agent startup information is logged to:
- **Console output** - Real-time startup information
- **File**: `logs/agent_startup.log` - Persistent startup logs

Example startup log:
```
[TraderAgent] CWD: E:\Richie\github\jarvis
[TraderAgent] DATA_PATH: E:\Richie\github\jarvis\data
[TraderAgent] Portfolio Path -> E:\Richie\github\jarvis\data\live\live_portfolio_state.json
[TraderAgent] Exists: True
[TraderAgent] Live Trades Path -> E:\Richie\github\jarvis\data\live\live_trades.json
[TraderAgent] Exists: True
[TraderAgent] Exit Engine Path -> E:\Richie\github\jarvis\data\live\exit_engine_state.json
[TraderAgent] Exists: True
```

## Troubleshooting

### Issue: "Portfolio data not found"
**Solution**: Ensure DATA_PATH is set correctly and the data directory exists.

### Issue: "Permission denied" when creating files
**Solution**: Check write permissions on the data directory.

### Issue: Agents can't find data files
**Solution**: 
1. Verify DATA_PATH environment variable
2. Check that the path exists
3. Ensure agents are started from the correct working directory

## Quick Start Commands

### Full System Start
```bash
# Set environment variable
export DATA_PATH="/home/richie/jarvis/data"  # Linux/macOS
# or
$env:DATA_PATH = "E:\Richie\github\jarvis\data"  # Windows PowerShell

# Start the complete system
python discord_jarvis_bot_full.py
```

### Individual Agent Testing
```bash
# Test TraderAgent
python jarvis/agents/trader_agent.py

# Test SoloLevelingAgent  
python jarvis/agents/solo_leveling_agent.py

# Test ResearchAgent
python jarvis/agents/research_agent.py
```

## Data File Management

### Automatic Creation
- Agents automatically create missing directories
- Placeholder data files are created with default values
- All files use UTF-8 encoding

### Manual Data Reset
To reset all data files to defaults:
```bash
# Remove existing data files
rm -rf data/live/* data/system/*

# Restart agents (they will recreate files)
python discord_jarvis_bot_full.py
```

## Environment Variables

Required environment variables:
- `DATA_PATH` - Path to shared data directory
- `OPENAI_KEY` - OpenAI API key
- `DISCORD_BOT_TOKEN` - Discord bot token

Optional environment variables:
- `CLAUDE_API_KEY` - Claude API key (uses fallback if not set)
- `OPENWEATHER_API_KEY` - Weather API key (uses fallback if not set)
