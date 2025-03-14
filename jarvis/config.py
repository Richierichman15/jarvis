"""
Configuration file for Jarvis assistant.
Contains API keys, model settings, and other configuration parameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_DIR = PROJECT_ROOT / "jarvis" / "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)  # Ensure memory directory exists

# Debug logs directory
DEBUG_LOGS_DIR = PROJECT_ROOT / "jarvis" / "debug_logs"
os.makedirs(DEBUG_LOGS_DIR, exist_ok=True)  # Ensure debug logs directory exists

# OpenAI API configuration
# First check for API key in environment, then use default if not available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Check if we need to set the API key in environment
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables or .env file")

# Available local models
LOCAL_MODELS = {
    "llama3": "llama3:8b-instruct-q4_0",     # Good all-rounder
    "mistral": "mistral:7b-instruct-v0.2-q4_0",  # Great reasoning
    "phi3": "phi3:mini"     # Efficient smaller model
}

# Model settings
LOCAL_MODEL_NAME = LOCAL_MODELS["phi3"]  # Default model
LOCAL_MODEL_BASE_URL = "http://localhost:11434/api"  # Ollama API endpoint

OPENAI_MODEL = "gpt-4o-mini"  # Default OpenAI model to use for complex reasoning

# Intelligence threshold - above this complexity we switch to OpenAI
# Scale of 1-10, where 10 is the most complex
COMPLEXITY_THRESHOLD = 7

# Memory settings
MEMORY_ENABLED = True
CONVERSATION_BUFFER_SIZE = 10  # Number of recent messages to keep for context

# Tools configuration
AVAILABLE_TOOLS = [
    "web_search",
    "calculator",
    "file_operations",
    "system_info",
    "code_editor",
]

# Tool settings
FILE_MAX_SIZE = 1024 * 1024  # Maximum file size for file operations (1MB)
SAFE_DIRECTORIES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.getcwd()
] 