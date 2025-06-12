"""
Model Manager for Jarvis.
This module handles model selection and interaction.
"""
import logging
from typing import Dict, Any, Optional, List

from .openai_model import OpenAIModel
from .claude_model import ClaudeModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manager for handling model selection and interaction.
    Uses OpenAI GPT-4 by default, with Claude as a backup option.
    """
    
    def __init__(self):
        """Initialize the model manager."""
        # Try to initialize OpenAI model
        self.openai_available = False
        try:
            self.openai_model = OpenAIModel()
            self.openai_available = True
            logger.info("OpenAI model initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI model initialization failed: {str(e)}")
            self.openai_model = None
            
        # Try to initialize Claude model as backup
        self.claude_available = False
        try:
            self.claude_model = ClaudeModel()
            self.claude_available = True
            logger.info("Claude model initialized successfully")
        except Exception as e:
            logger.warning(f"Claude model initialization failed: {str(e)}")
            self.claude_model = None
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using the available model.
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            
        Returns:
            Generated response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Try OpenAI first
        if self.openai_available:
            try:
                response = self.openai_model.generate_response(messages)
                return response
            except Exception as e:
                logger.warning(f"OpenAI model failed: {str(e)}")
                
        # Fall back to Claude if OpenAI fails
        if self.claude_available:
            try:
                response = self.claude_model.generate_response(messages)
                return response
            except Exception as e:
                logger.error(f"Claude model failed: {str(e)}")
                return "Error: Both OpenAI and Claude models failed to generate a response."
                
        return "Error: No models available to generate a response."

def get_model():
    """Get a model instance for text generation.
    
    Returns:
        A model instance that can generate text responses
    """
    manager = ModelManager()
    
    # Return the first available model
    if manager.openai_available:
        return manager.openai_model
    elif manager.claude_available:
        return manager.claude_model
    else:
        raise RuntimeError("No models available. Please check your API keys and model configurations.") 