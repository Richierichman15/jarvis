"""
Conversation memory module for Jarvis.
Stores and retrieves conversation history.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

from ..config import MEMORY_DIR, CONVERSATION_BUFFER_SIZE


class ConversationMemory:
    """Stores and manages conversation history."""
    
    def __init__(self, memory_dir: str = str(MEMORY_DIR), buffer_size: int = CONVERSATION_BUFFER_SIZE):
        """Initialize the conversation memory.
        
        Args:
            memory_dir: Directory to store conversation history
            buffer_size: Number of recent messages to keep in memory
        """
        self.memory_dir = memory_dir
        self.buffer_size = buffer_size
        self.conversation_buffer = []
        
        # Create memory directory if it doesn't exist
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Create a new session file
        self.session_id = int(time.time())
        self.session_file = os.path.join(self.memory_dir, f"session_{self.session_id}.json")
        
        # Initialize session file
        self._initialize_session()
        
    def _initialize_session(self):
        """Initialize a new session file."""
        session_data = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation memory.
        
        Args:
            role: Role of the message sender (user/assistant/system)
            content: The message content
            metadata: Optional metadata about the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add to in-memory buffer
        self.conversation_buffer.append(message)
        
        # Trim buffer if needed
        if len(self.conversation_buffer) > self.buffer_size:
            self.conversation_buffer = self.conversation_buffer[-self.buffer_size:]
            
        # Append to session file
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
                
            session_data["messages"].append(message)
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving message to session file: {e}")
    
    def get_recent_messages(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the most recent messages.
        
        Args:
            count: Number of messages to return (None for all)
            
        Returns:
            List of recent messages
        """
        if count is None or count >= len(self.conversation_buffer):
            return self.conversation_buffer
        
        return self.conversation_buffer[-count:]
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history from the session file.
        
        Returns:
            List of all messages in the current session
        """
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            return session_data["messages"]
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []
            
    def format_for_context(self, count: Optional[int] = None) -> str:
        """Format recent messages for context.
        
        Args:
            count: Number of messages to include
            
        Returns:
            Formatted conversation string
        """
        messages = self.get_recent_messages(count)
        formatted = ""
        
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            formatted += f"{role}: {content}\n\n"
            
        return formatted 