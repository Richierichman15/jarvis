"""Configuration module for Discord bot."""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

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

# Initialize feature flags
try:
    from jarvis.models.model_manager import ModelManager
    from formatter import format_response
    MODEL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import Jarvis model or formatter: {e}")

try:
    from jarvis_event_listener import TradingEventListener
    EVENT_LISTENER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import event listener: {e}")

try:
    from jarvis.intelligence import IntentRouter, IntentResult, IntentType
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import intelligence core: {e}")

try:
    from server_manager import ServerManager
    SERVER_MANAGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import server manager: {e}")

try:
    from jarvis.monitoring import start_system_monitoring, get_system_monitor
    SYSTEM_MONITORING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import system monitoring: {e}")

try:
    from jarvis_music_player import MusicPlayer
    MUSIC_PLAYER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import music player: {e}")

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_CLIENT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import MCP client: {e}")

