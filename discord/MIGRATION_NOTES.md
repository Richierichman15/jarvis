# Discord Bot Microservice Migration Notes

## Overview
This document describes the migration of `discord_jarvis_bot_full.py` into a microservice architecture under the `discord/` directory. The agent system has been **removed** to improve performance, but is documented here for potential future re-integration.

## Architecture Overview

### Original Structure (discord_jarvis_bot_full.py)
The original file was a monolithic 1920-line script containing:
- Multiple client implementations (RobustMCPClient, JarvisClientMCPClient)
- Command routing logic (DiscordCommandRouter, AgentToolRouter)
- Event handlers (on_ready, on_message, etc.)
- Utility functions (message splitting, formatting)
- Global state management
- Agent system integration

### New Microservice Structure (discord/)

```
discord/
├── __init__.py
├── main.py                 # Clean entry point
├── config.py              # Configuration and environment loading
├── clients/               # MCP and HTTP clients
│   ├── __init__.py
│   ├── mcp_client.py      # RobustMCPClient (direct MCP connections)
│   └── http_client.py     # JarvisClientMCPClient (HTTP API client)
├── routers/               # Command routing
│   ├── __init__.py
│   └── command_router.py  # DiscordCommandRouter (command parsing & routing)
├── handlers/              # Discord event handlers
│   ├── __init__.py
│   ├── message_handler.py # Message processing logic
│   └── event_handlers.py  # Discord event handlers (on_ready, on_message, etc.)
├── services/              # Core services
│   ├── __init__.py
│   └── conversation_context.py # ConversationContext
├── utils/                 # Utilities
│   ├── __init__.py
│   └── message_utils.py   # Message splitting, formatting helpers
├── components/            # Optional components
│   ├── __init__.py
│   ├── music.py           # Music player integration
│   └── events.py          # Event listener integration
└── agents/                # REMOVED AGENT SYSTEM
    └── REMOVED.md         # Documentation for future re-integration
```

## Components Ported

### 1. Configuration (`config.py`)
**What:** Environment variable loading, Discord bot configuration, logging setup
**Notes:** Centralized configuration management, replaces scattered global config

### 2. MCP Clients (`clients/`)
**What:** 
- `RobustMCPClient` - Direct MCP server connections (stdio-based)
- `JarvisClientMCPClient` - HTTP client to Jarvis Client HTTP Server
**Notes:** Both clients provide tool calling capabilities with different backends

### 3. Command Router (`routers/command_router.py`)
**What:** `DiscordCommandRouter` class that:
- Parses Discord messages into tool commands
- Routes to appropriate tools/servers
- Handles local commands (music, events)
- Validates response quality
- Performs auto-followup searches
**Notes:** Core routing logic, handles `/momentum`, `/portfolio`, etc.

### 4. Message Handler (`handlers/message_handler.py`)
**What:** Main message processing logic that:
- Uses IntentRouter for intelligent routing (if available)
- Falls back to command router
- Formats responses with AI (if available)
- Manages conversation context
**Notes:** Central processing logic moved from `on_message` handler

### 5. Event Handlers (`handlers/event_handlers.py`)
**What:** Discord event handlers:
- `on_ready()` - Initialization of all components
- `on_message()` - Entry point for messages
- `on_disconnect()` - Cleanup
- `on_resumed()` - Reconnection handling
**Notes:** Clean separation of Discord-specific event handling

### 6. Conversation Context (`services/conversation_context.py`)
**What:** `ConversationContext` class tracking user conversation history
**Notes:** Enables follow-up questions and context-aware responses

### 7. Message Utilities (`utils/message_utils.py`)
**What:** Helper functions:
- `split_message_intelligently()` - Split long messages
- `send_long_message()` - Send multi-part messages
- `send_error_webhook()` - Error notifications
**Notes:** Utilities for Discord message handling

### 8. Optional Components (`components/`)
**What:** 
- `music.py` - Music player wrapper (if MUSIC_PLAYER_AVAILABLE)
- `events.py` - Event listener wrapper (if EVENT_LISTENER_AVAILABLE)
**Notes:** These components are optional and gracefully degrade if not available

## Agent System - REMOVED

### What Was Removed
The following agent-related code has been **removed** to improve performance:
- `AgentManager` initialization and usage
- `AgentToolRouter` class
- Agent system as first-priority tool routing
- All imports from `jarvis.agents`

### Why Removed
1. **Performance Issues:** Agents added significant latency to responses
2. **Complexity:** Added unnecessary complexity for direct tool calls
3. **Redundancy:** MCP servers already handle tool execution efficiently

### Original Agent Integration Points
1. **Initialization** (around line 1335-1346):
   ```python
   agent_manager = AgentManager()
   await agent_manager.start()
   ```

2. **Tool Routing** (around line 1223-1235):
   ```python
   if agent_manager is not None:
       agent_router = AgentToolRouter(agent_manager)
       result = await agent_router.call_tool(tool_name, arguments)
   ```

3. **Tool Mapping** (AgentToolRouter.tool_mapping):
   - Trading commands → TraderAgent
   - System commands → SoloLevelingAgent  
   - Research commands → ResearchAgent

### How to Re-enable Agents (Future)
If agents are needed in the future:

1. **Add AgentManager back:**
   ```python
   from jarvis.agents import AgentManager, AgentCapability
   agent_manager = AgentManager()
   await agent_manager.start()
   ```

2. **Restore AgentToolRouter:**
   - See `discord/agents/REMOVED.md` for full `AgentToolRouter` implementation
   - Re-integrate into `execute_intelligent_tool()` function

3. **Update routing logic:**
   - Add agent routing as first priority in `execute_intelligent_tool()`
   - Fall back to MCP clients if agents fail

### Agent Tool Mapping (Reference)
```python
{
    "trading.trading.get_momentum_signals": (AgentCapability.TRADING, "trading.get_momentum_signals"),
    "trading.portfolio.get_overview": (AgentCapability.TRADING, "portfolio.get_overview"),
    "system.system.list_quests": (AgentCapability.SYSTEM, "get_quests"),
    "jarvis_scan_news": (AgentCapability.RESEARCH, "scan_news"),
}
```

## Performance Improvements

### Before (with agents):
1. User message → IntentRouter
2. IntentRouter → AgentToolRouter
3. AgentToolRouter → AgentManager → Redis → Agent process
4. Agent process → MCP tool call
5. Response back through chain

### After (without agents):
1. User message → IntentRouter (optional)
2. IntentRouter → MCP client (direct)
3. MCP client → Tool execution
4. Response back

**Result:** Eliminated Redis communication, agent process overhead, and multiple routing layers.

## Migration Checklist

- [x] Extract configuration
- [x] Extract MCP clients
- [x] Extract command router
- [x] Extract message handler
- [x] Extract event handlers
- [x] Extract utilities
- [x] Extract services
- [x] Remove agent system
- [x] Document agent system for future use
- [x] Create clean main entry point

## Quick Reference

### Starting the Bot
```python
# Old way
python discord_jarvis_bot_full.py

# New way
python -m discord.main
```

### Key Entry Points
- `discord/main.py` - Main entry point, creates Discord client and runs bot
- `discord/handlers/event_handlers.py` - Discord event handlers
- `discord/handlers/message_handler.py` - Message processing logic
- `discord/routers/command_router.py` - Command parsing and routing

### Key Classes
- `RobustMCPClient` - Direct MCP connections (`clients/mcp_client.py`)
- `JarvisClientMCPClient` - HTTP API client (`clients/http_client.py`)
- `DiscordCommandRouter` - Command routing (`routers/command_router.py`)
- `ConversationContext` - Context tracking (`services/conversation_context.py`)

