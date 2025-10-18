"""
Data utilities for agent file management.
Provides functions for verifying and creating data files with proper paths.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from jarvis.config import DATA_PATH, AGENT_LOGS_DIR

# Setup logging for agent startup
def setup_agent_logging(agent_name: str) -> logging.Logger:
    """Setup logging for agent startup with file output."""
    logger = logging.getLogger(f"{agent_name}_startup")
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs(AGENT_LOGS_DIR, exist_ok=True)
    
    # File handler for startup logs
    log_file = os.path.join(AGENT_LOGS_DIR, "agent_startup.log")
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_agent_startup(agent_name: str, file_paths: Dict[str, str]) -> None:
    """Log agent startup information including working directory and file paths."""
    logger = setup_agent_logging(agent_name)
    
    logger.info(f"[{agent_name}] Starting up...")
    logger.info(f"[{agent_name}] CWD: {os.getcwd()}")
    logger.info(f"[{agent_name}] DATA_PATH: {DATA_PATH}")
    
    for file_type, file_path in file_paths.items():
        abs_path = os.path.abspath(file_path)
        exists = os.path.exists(file_path)
        logger.info(f"[{agent_name}] {file_type} Path → {abs_path}")
        logger.info(f"[{agent_name}] {file_type} Exists: {exists}")

def verify_data_files(required_files: List[Dict[str, Any]]) -> None:
    """
    Verify and create placeholder data files if they don't exist.
    
    Args:
        required_files: List of dicts with 'path' and 'default_data' keys
    """
    for file_info in required_files:
        file_path = file_info['path']
        default_data = file_info.get('default_data', {})
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create file with default data if it doesn't exist
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
                print(f"WARNING: Created placeholder: {file_path}")
            except Exception as e:
                print(f"ERROR: Failed to create {file_path}: {e}")

def get_portfolio_path() -> str:
    """Get the absolute path to the live portfolio state file."""
    return os.path.join(DATA_PATH, "live", "live_portfolio_state.json")

def get_live_trades_path() -> str:
    """Get the absolute path to the live trades file."""
    return os.path.join(DATA_PATH, "live", "live_trades.json")

def get_exit_engine_path() -> str:
    """Get the absolute path to the exit engine state file."""
    return os.path.join(DATA_PATH, "live", "exit_engine_state.json")

def get_quests_path() -> str:
    """Get the absolute path to the quests file."""
    return os.path.join(DATA_PATH, "system", "quests.json")

def get_goals_path() -> str:
    """Get the absolute path to the goals file."""
    return os.path.join(DATA_PATH, "system", "goals.json")

def get_system_status_path() -> str:
    """Get the absolute path to the system status file."""
    return os.path.join(DATA_PATH, "system", "system_status.json")

# Default data structures for placeholder files
DEFAULT_PORTFOLIO_DATA = {
    "portfolio_value": 5000.0,
    "cash": 5000.0,
    "initial_balance": 5000.0,
    "return_percentage": 0.0,
    "trading_active": True,
    "positions": {},
    "crypto_symbols": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "TRX-USD", "XLM-USD", "PAXG-USD"],
    "last_updated": "2025-01-18T12:00:00Z",
    "daily_pnl": 0.0,
    "daily_drawdown": 0.0,
    "daily_trade_count": 0,
    "daily_start_value": 5000.0,
    "daily_start_value_date": "2025-01-18"
}

DEFAULT_LIVE_TRADES_DATA = {
    "trades": []
}

DEFAULT_EXIT_ENGINE_DATA = {
    "active_trades": {},
    "trailing_stops": {},
    "trade_states": {},
    "last_updated": "2025-01-18T12:00:00Z"
}

DEFAULT_QUESTS_DATA = {
    "quests": [
        {
            "id": "quest_1",
            "title": "Complete Python Tutorial",
            "description": "Finish the Python basics tutorial",
            "status": "active",
            "progress": 69,
            "experience_reward": 150,
            "difficulty": "easy",
            "estimated_time": "2 hours",
            "created_at": "2025-01-18T10:00:00Z"
        },
        {
            "id": "quest_2", 
            "title": "Practice Coding Daily",
            "description": "Code for at least 30 minutes every day",
            "status": "active",
            "progress": 49,
            "experience_reward": 100,
            "difficulty": "medium",
            "estimated_time": "30 minutes daily",
            "created_at": "2025-01-18T10:00:00Z"
        }
    ],
    "completed_quests": [],
    "last_updated": "2025-01-18T12:00:00Z"
}

DEFAULT_GOALS_DATA = {
    "goals": [
        {
            "id": "goal_1",
            "title": "Learn AI and Machine Learning",
            "description": "Master the fundamentals of AI and ML",
            "status": "active",
            "priority": "high",
            "deadline": "2025-06-01",
            "created_at": "2025-01-18T10:00:00Z"
        }
    ],
    "completed_goals": [],
    "last_updated": "2025-01-18T12:00:00Z"
}

DEFAULT_SYSTEM_STATUS_DATA = {
    "agent_status": "operational",
    "timestamp": "2025-01-18T12:00:00Z",
    "user_level": 1,
    "user_experience": 0,
    "total_quests_completed": 0,
    "daily_quests_completed": 0,
    "active_goals": 1,
    "active_quests": 2,
    "achievements_unlocked": 1,
    "uptime": 0
}
