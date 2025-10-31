"""Conversation context tracking service."""
from typing import Dict, List, Optional
from datetime import datetime


class ConversationContext:
    """Track conversation context for follow-up questions."""
    
    def __init__(self, max_history: int = 5):
        self.history: Dict[int, List[Dict]] = {}  # user_id -> messages
        self.max_history = max_history
    
    def add_message(self, user_id: int, query: str, response: str, metadata: dict = None):
        """Add a message to conversation history."""
        if user_id not in self.history:
            self.history[user_id] = []
        
        self.history[user_id].append({
            "query": query,
            "response": response,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        })
        
        # Trim to max history
        if len(self.history[user_id]) > self.max_history:
            self.history[user_id] = self.history[user_id][-self.max_history:]
    
    def get_context(self, user_id: int, last_n: int = 2) -> str:
        """Get recent conversation context."""
        if user_id not in self.history:
            return ""
        
        recent = self.history[user_id][-last_n:]
        context_parts = []
        
        for msg in recent:
            context_parts.append(f"Previous: {msg['query'][:100]}")
        
        return "\n".join(context_parts)
    
    def extract_relevant_data(self, user_id: int, keyword: str) -> Optional[str]:
        """Extract relevant data from previous responses."""
        if user_id not in self.history:
            return None
        
        # Search backwards through history
        for msg in reversed(self.history[user_id]):
            if keyword.lower() in msg['query'].lower():
                return msg.get('metadata', {})
        
        return None

