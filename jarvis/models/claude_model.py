"""
Claude API model implementation for Jarvis.
"""
import os
import json
import anthropic
from typing import Dict, List, Optional, Union

class ClaudeModel:
    """Claude API model implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude model with API key."""
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY", "")
        if not self.api_key:
            raise ValueError("Claude API key not found in environment or .env file")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-sonnet"  # Using Claude 3 Sonnet model
        
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a response using the Claude API."""
        try:
            # Convert messages to Claude format
            formatted_messages = []
            for msg in messages:
                role = msg["role"]
                if role == "system":
                    # System messages are handled differently in Claude
                    formatted_messages.append({
                        "role": "user",
                        "content": f"System instruction: {msg['content']}"
                    })
                else:
                    formatted_messages.append({
                        "role": "user" if role == "user" else "assistant",
                        "content": msg["content"]
                    })
            
            # Create the message for Claude
            response = self.client.messages.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.content[0].text
            
        except Exception as e:
            error_msg = f"Error generating response from Claude API: {str(e)}"
            print(error_msg)
            return error_msg
            
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the text."""
        # Claude uses roughly 4 characters per token on average
        return len(text) // 4 