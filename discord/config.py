"""Configuration module for Discord bot."""
import os
import logging
import sys
import importlib
from typing import Optional
from dotenv import load_dotenv

# CRITICAL: Import the actual discord.py library FIRST before our package might interfere
# This ensures that when other modules (jarvis_event_listener, jarvis_music_player) import discord,
# they get the library, not our discord package
try:
    # Import the actual discord library and ensure it's in sys.modules
    discord_lib = importlib.import_module('discord')
    # Temporarily save our package name if it exists
    if 'discord' in sys.modules and not hasattr(sys.modules['discord'], 'Client'):
        # If 'discord' is already our package, we need to work around this
        _discord_pkg_backup = sys.modules.pop('discord', None)
        sys.modules['discord'] = discord_lib
        # Now other modules can safely import discord
except ImportError:
    pass  # discord library not available

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_jarvis_bot_full.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration values
JARVIS_CLIENT_URL = os.getenv('JARVIS_CLIENT_URL', 'http://localhost:3012')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN_HERE')
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', 'YOUR_DISCORD_CLIENT_ID_HERE')
DISCORD_CLIENT_SERVER = os.getenv('DISCORD_CLIENT_SERVER', 'YOUR_DISCORD_SERVER_ID_HERE')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
EVENT_NOTIFICATION_CHANNEL_ID = os.getenv('EVENT_NOTIFICATION_CHANNEL_ID', None)

# Feature flags
MODEL_AVAILABLE = False
EVENT_LISTENER_AVAILABLE = False
INTELLIGENCE_AVAILABLE = False
SERVER_MANAGER_AVAILABLE = False
SYSTEM_MONITORING_AVAILABLE = False
MUSIC_PLAYER_AVAILABLE = False
MCP_CLIENT_AVAILABLE = False

# Initialize feature flags - use lazy imports to avoid conflicts
# These will be checked when actually needed, not at module import time

def _check_model_available():
    """Check if model is available (lazy import)."""
    try:
        import jarvis.models.model_manager
        import formatter
        return True
    except ImportError:
        return False

def _check_event_listener_available():
    """Check if event listener is available (lazy import)."""
    try:
        # This check is deferred - actual import happens in main.py
        # where we handle the discord import conflict properly
        return True  # Assume available, actual check happens at runtime
    except Exception:
        return False

def _check_intelligence_available():
    """Check if intelligence is available (lazy import)."""
    try:
        from jarvis.intelligence import IntentRouter, IntentResult, IntentType
        return True
    except ImportError:
        return False

def _check_server_manager_available():
    """Check if server manager is available (lazy import)."""
    try:
        import server_manager
        return True
    except ImportError:
        return False

def _check_monitoring_available():
    """Check if monitoring is available (lazy import)."""
    try:
        from jarvis.monitoring import start_system_monitoring, get_system_monitor
        return True
    except ImportError:
        return False

def _check_music_player_available():
    """Check if music player is available (lazy import)."""
    try:
        import jarvis_music_player
        return True
    except ImportError:
        return False

def _check_mcp_client_available():
    """Check if MCP client is available (lazy import)."""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        return True
    except ImportError:
        return False

# Set defaults - use lazy evaluation to avoid import conflicts
# These will be checked when actually accessed, not at module import time
# This prevents conflicts with discord library imports
_MODEL_AVAILABLE = None
_EVENT_LISTENER_AVAILABLE = None
_INTELLIGENCE_AVAILABLE = None
_SERVER_MANAGER_AVAILABLE = None
_SYSTEM_MONITORING_AVAILABLE = None
_MUSIC_PLAYER_AVAILABLE = None
_MCP_CLIENT_AVAILABLE = None

def _get_model_available():
    global _MODEL_AVAILABLE
    if _MODEL_AVAILABLE is None:
        _MODEL_AVAILABLE = _check_model_available()
    return _MODEL_AVAILABLE

def _get_event_listener_available():
    global _EVENT_LISTENER_AVAILABLE
    if _EVENT_LISTENER_AVAILABLE is None:
        _EVENT_LISTENER_AVAILABLE = _check_event_listener_available()
    return _EVENT_LISTENER_AVAILABLE

def _get_intelligence_available():
    global _INTELLIGENCE_AVAILABLE
    if _INTELLIGENCE_AVAILABLE is None:
        _INTELLIGENCE_AVAILABLE = _check_intelligence_available()
    return _INTELLIGENCE_AVAILABLE

def _get_server_manager_available():
    global _SERVER_MANAGER_AVAILABLE
    if _SERVER_MANAGER_AVAILABLE is None:
        _SERVER_MANAGER_AVAILABLE = _check_server_manager_available()
    return _SERVER_MANAGER_AVAILABLE

def _get_monitoring_available():
    global _SYSTEM_MONITORING_AVAILABLE
    if _SYSTEM_MONITORING_AVAILABLE is None:
        _SYSTEM_MONITORING_AVAILABLE = _check_monitoring_available()
    return _SYSTEM_MONITORING_AVAILABLE

def _get_music_player_available():
    global _MUSIC_PLAYER_AVAILABLE
    if _MUSIC_PLAYER_AVAILABLE is None:
        _MUSIC_PLAYER_AVAILABLE = _check_music_player_available()
    return _MUSIC_PLAYER_AVAILABLE

def _get_mcp_client_available():
    global _MCP_CLIENT_AVAILABLE
    if _MCP_CLIENT_AVAILABLE is None:
        _MCP_CLIENT_AVAILABLE = _check_mcp_client_available()
    return _MCP_CLIENT_AVAILABLE

# Use lazy evaluation - checks are done when _ensure_checks_done() is called
# We'll access them through functions when needed, but for compatibility,
# set them to False initially and they'll be checked when first accessed
_MODULE_LOADED = False

def _ensure_checks_done():
    """Ensure availability checks are done (called after discord library is set up)."""
    global MODEL_AVAILABLE, EVENT_LISTENER_AVAILABLE, INTELLIGENCE_AVAILABLE
    global SERVER_MANAGER_AVAILABLE, SYSTEM_MONITORING_AVAILABLE, MUSIC_PLAYER_AVAILABLE, MCP_CLIENT_AVAILABLE
    global _MODULE_LOADED
    
    if not _MODULE_LOADED:
        MODEL_AVAILABLE = _check_model_available()
        EVENT_LISTENER_AVAILABLE = _check_event_listener_available()
        INTELLIGENCE_AVAILABLE = _check_intelligence_available()
        SERVER_MANAGER_AVAILABLE = _check_server_manager_available()
        SYSTEM_MONITORING_AVAILABLE = _check_monitoring_available()
        MUSIC_PLAYER_AVAILABLE = _check_music_player_available()
        MCP_CLIENT_AVAILABLE = _check_mcp_client_available()
        _MODULE_LOADED = True

# Set initial defaults to False - will be properly checked when _ensure_checks_done() is called
MODEL_AVAILABLE = False
EVENT_LISTENER_AVAILABLE = False
INTELLIGENCE_AVAILABLE = False
SERVER_MANAGER_AVAILABLE = False
SYSTEM_MONITORING_AVAILABLE = False
MUSIC_PLAYER_AVAILABLE = False
MCP_CLIENT_AVAILABLE = False

