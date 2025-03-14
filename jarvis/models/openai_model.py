"""
OpenAI model handler for Jarvis using the OpenAI API.
"""
import os
from typing import Dict, List, Any, Optional

from openai import OpenAI
from ..config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIModel:
    """Interface for OpenAI models via their API."""
    
    def __init__(self, api_key: str = OPENAI_API_KEY, model_name: str = OPENAI_MODEL):
        """Initialize the OpenAI model.
        
        Args:
            api_key: OpenAI API key
            model_name: Name of the OpenAI model to use
        """
        # Try to get the API key from the environment first, then use the provided key
        self.api_key = os.environ.get("OPENAI_API_KEY", "") or api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in the environment or pass it to the constructor.")
        
        self.model_name = model_name
        self.client = OpenAI(api_key=self.api_key)
        
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1000) -> str:
        """Generate a response from the OpenAI model.
        
        Args:
            prompt: User's input text
            system_prompt: Optional system instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            The model's response as a string
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error: Failed to get response from OpenAI: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if the OpenAI API is available and responding.
        
        Returns:
            True if API is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            # Simple test query to check if API is responding
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"OpenAI availability check failed: {str(e)}")
            return False 