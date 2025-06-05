"""
Centralized configuration management for Jarvis System.
Handles environment variables, Firebase config, and application settings.
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JarvisConfig:
    """Centralized configuration for the Jarvis system."""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load all configuration from environment variables and defaults."""
        
        # Firebase Configuration
        self.firebase_config = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID", "system-31e58"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
        }
        
        # Firebase Web Config (for frontend)
        self.firebase_web_config = {
            "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyAFhRXD0uuv9--e8O6gqB6MsV2Ms85AaUI"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "system-31e58.firebaseapp.com"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", "system-31e58"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "system-31e58.firebasestorage.app"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "1059252367741"),
            "appId": os.getenv("FIREBASE_APP_ID", "1:1059252367741:web:bd5938787385b00957dc14"),
            "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "G-WJY4ET97CE")
        }
        
        # VAPID Key for push notifications
        self.vapid_key = os.getenv("VAPID_KEY")
        
        # Application Configuration
        self.app_config = {
            "secret_key": os.getenv("SECRET_KEY", os.urandom(24)),
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", 8080)),  # Changed to 8080 for Firebase deployment
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        # Model Configuration
        self.model_config = {
            "default_model": os.getenv("DEFAULT_MODEL", "mistral"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        }
        
        # System Configuration
        self.system_config = {
            "memory_file": os.getenv("MEMORY_FILE", "jarvis_memory.json"),
            "skills_config_file": os.getenv("SKILLS_CONFIG_FILE", "jarvis/skills_config.json"),
            "three_month_plan_file": os.getenv("THREE_MONTH_PLAN_FILE", "three_month_plan.json"),
            "max_memory_entries": int(os.getenv("MAX_MEMORY_ENTRIES", 1000)),
            "notification_schedule": {
                "morning": os.getenv("MORNING_NOTIFICATION", "07:00"),
                "evening": os.getenv("EVENING_NOTIFICATION", "18:00"),
                "night": os.getenv("NIGHT_NOTIFICATION", "21:00")
            }
        }
        
        # Quest System Configuration
        self.quest_config = {
            "daily_quest_count": int(os.getenv("DAILY_QUEST_COUNT", 4)),
            "xp_multiplier": float(os.getenv("XP_MULTIPLIER", 1.0)),
            "level_up_base_xp": int(os.getenv("LEVEL_UP_BASE_XP", 150)),
            "max_level": int(os.getenv("MAX_LEVEL", 50)),
            "rank_requirements": {
                "E": int(os.getenv("RANK_E_REQUIREMENT", 1000)),
                "D": int(os.getenv("RANK_D_REQUIREMENT", 2500)),
                "C": int(os.getenv("RANK_C_REQUIREMENT", 5000)),
                "B": int(os.getenv("RANK_B_REQUIREMENT", 10000)),
                "A": int(os.getenv("RANK_A_REQUIREMENT", 20000)),
                "S": int(os.getenv("RANK_S_REQUIREMENT", 50000))
            }
        }
    
    def is_firebase_configured(self) -> bool:
        """Check if Firebase is properly configured."""
        required_fields = ["project_id", "private_key", "client_email"]
        return all(self.firebase_config.get(field) for field in required_fields)
    
    def get_firebase_credentials(self) -> Optional[Dict[str, Any]]:
        """Get Firebase credentials dict for admin SDK."""
        if not self.is_firebase_configured():
            return None
        return self.firebase_config
    
    def get_firebase_web_config(self) -> Dict[str, Any]:
        """Get Firebase web configuration for frontend."""
        return self.firebase_web_config
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_config["environment"] == "production"
    
    def get_database_url(self) -> str:
        """Get database URL (for future database integration)."""
        return os.getenv("DATABASE_URL", "sqlite:///jarvis.db")
    
    def get_cors_origins(self) -> list:
        """Get allowed CORS origins."""
        origins = os.getenv("CORS_ORIGINS", "*")
        if origins == "*":
            return ["*"]
        return origins.split(",")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "firebase_web_config": self.firebase_web_config,
            "app_config": {
                "host": self.app_config["host"],
                "port": self.app_config["port"],
                "debug": self.app_config["debug"],
                "environment": self.app_config["environment"]
            },
            "system_config": self.system_config,
            "quest_config": self.quest_config,
            "firebase_configured": self.is_firebase_configured()
        }

# Global configuration instance
config = JarvisConfig() 