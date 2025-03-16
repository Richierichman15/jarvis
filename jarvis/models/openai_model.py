"""
OpenAI model implementation for Jarvis.
"""
import os
import openai
from typing import Dict, List, Optional, Union

class OpenAIModel:
    """OpenAI model implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI model with API key."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment or .env file")
            
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo-preview"  # Using the latest GPT-4 model
        
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a response using the OpenAI API."""
        try:
            # Create the chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"Error generating response from OpenAI API: {str(e)}"
            print(error_msg)
            return error_msg
            
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the text."""
        # GPT-4 uses roughly 4 characters per token on average
        return len(text) // 4

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
                model=self.model,
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
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            print(f"OpenAI availability check failed: {str(e)}")
            return False 