"""
Optional components for Discord bot.

This module documents optional components that exist in discord_jarvis_bot_full.py
but are conditionally loaded based on availability.

## Components Already Migrated

These components have been fully migrated and are imported/initialized in discord/main.py:

1. **TradingEventListener** (from jarvis_event_listener)
   - Provides real-time trading event notifications
   - Initialized in on_ready() if EVENT_LISTENER_AVAILABLE and EVENT_NOTIFICATION_CHANNEL_ID is set

2. **MusicPlayer** (from jarvis_music_player)
   - Handles Discord voice channel music playback
   - Initialized in on_ready() if MUSIC_PLAYER_AVAILABLE

3. **IntentRouter** (from jarvis.intelligence)
   - Provides intelligent intent analysis and routing
   - Initialized in on_ready() if INTELLIGENCE_AVAILABLE

4. **ModelManager** (from jarvis.models.model_manager)
   - Provides AI-powered response formatting
   - Initialized in on_ready() if MODEL_AVAILABLE

5. **ServerManager** (from server_manager)
   - Manages MCP server lifecycle
   - Initialized in on_ready() if SERVER_MANAGER_AVAILABLE

## Components Not Yet Migrated

These components exist in discord_jarvis_bot_full.py but are not yet in the microservice:

1. **System Monitoring** (from jarvis.monitoring)
   - Provides system health monitoring
   - Currently: Not migrated
   - Status: Can be added if needed

2. **Agent System** (from jarvis.agents)
   - Multi-agent orchestration system
   - Currently: Intentionally removed for performance
   - Status: Documented in discord/agents/REMOVED.md
   - Reason: Caused performance degradation and increased latency

## Usage

All optional components are conditionally imported and initialized in discord/main.py.
They are wrapped in try/except blocks to gracefully handle missing dependencies.
"""

__all__ = []
