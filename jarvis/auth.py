"""
Authentication system for Jarvis.
Handles user login, signup, and session management.
"""
import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

class UserAuth:
    def __init__(self):
        self.users_file = Path("jarvis/data/users.json")
        self.sessions_file = Path("jarvis/data/sessions.json") 
        self.desires_file = Path("jarvis/data/user_desires.json")
        
        # Create data directory if it doesn't exist
        self.users_file.parent.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
        
    def _init_files(self):
        """Initialize user and session files with default data."""
        if not self.users_file.exists():
            # Create with hardcoded admin user
            users = {
                "buck": {
                    "password_hash": self._hash_password("nasty"),
                    "role": "admin",
                    "created_at": datetime.now().isoformat(),
                    "desires": None
                }
            }
            self._save_json(self.users_file, users)
            
        if not self.sessions_file.exists():
            self._save_json(self.sessions_file, {})
            
        if not self.desires_file.exists():
            self._save_json(self.desires_file, {})
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        users = self._load_json(self.users_file)
        
        if username in users:
            return {"success": False, "error": "Username already exists"}
        
        users[username] = {
            "password_hash": self._hash_password(password),
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "desires": None
        }
        
        self._save_json(self.users_file, users)
        return {"success": True, "message": "User registered successfully"}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login a user and create session."""
        users = self._load_json(self.users_file)
        
        if username not in users:
            return {"success": False, "error": "Invalid username or password"}
        
        user = users[username]
        if user["password_hash"] != self._hash_password(password):
            return {"success": False, "error": "Invalid username or password"}
        
        # Create session
        session_id = self._generate_session_id()
        sessions = self._load_json(self.sessions_file)
        
        sessions[session_id] = {
            "username": username,
            "role": user["role"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        self._save_json(self.sessions_file, sessions)
        
        return {
            "success": True, 
            "session_id": session_id,
            "user": {
                "username": username,
                "role": user["role"]
            }
        }
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session and return user info if valid."""
        sessions = self._load_json(self.sessions_file)
        
        if session_id not in sessions:
            return None
        
        session = sessions[session_id]
        expires_at = datetime.fromisoformat(session["expires_at"])
        
        if datetime.now() > expires_at:
            # Session expired, remove it
            del sessions[session_id]
            self._save_json(self.sessions_file, sessions)
            return None
        
        return {
            "username": session["username"],
            "role": session["role"]
        }
    
    def logout(self, session_id: str) -> Dict[str, Any]:
        """Logout a user by removing their session."""
        sessions = self._load_json(self.sessions_file)
        
        if session_id in sessions:
            del sessions[session_id]
            self._save_json(self.sessions_file, sessions)
        
        return {"success": True, "message": "Logged out successfully"}
    
    def save_user_desires(self, username: str, desires: str):
        """Save user's desires for future reference."""
        desires_data = self._load_json(self.desires_file)
        desires_data[username] = {
            "desires": desires,
            "saved_at": datetime.now().isoformat()
        }
        self._save_json(self.desires_file, desires_data)
        
        # Also update in users file
        users = self._load_json(self.users_file)
        if username in users:
            users[username]["desires"] = desires
            self._save_json(self.users_file, users)
    
    def get_user_desires(self, username: str) -> Optional[str]:
        """Get user's saved desires."""
        desires_data = self._load_json(self.desires_file)
        return desires_data.get(username, {}).get("desires")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())