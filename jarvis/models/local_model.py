"""
Local model handler for Jarvis using Ollama API.
"""
import json
import requests
import logging
import time
from typing import Dict, List, Any, Optional

from ..config import LOCAL_MODEL_NAME, LOCAL_MODEL_BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaModel:
    """Interface for local LLM models via Ollama."""
    
    def __init__(self, model_name: str = LOCAL_MODEL_NAME, base_url: str = LOCAL_MODEL_BASE_URL):
        """Initialize the Ollama model.
        
        Args:
            model_name: Name of the model in Ollama
            base_url: Base URL for the Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.generate_endpoint = f"{base_url}/generate"
        
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1000) -> str:
        """Generate a response from the local model.
        
        Args:
            prompt: User's input text
            system_prompt: Optional system instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            The model's response as a string
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False  # Important to get a single response
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.info(f"Sending request to Ollama API: {self.generate_endpoint}")
            response = requests.post(self.generate_endpoint, json=payload, timeout=30)
            if response.status_code == 200:
                # Attempt to parse the JSON response
                try:
                    data = response.json()
                    return data.get("response", "")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # If JSON parsing fails, return the raw text
                    return "Error: Failed to parse response from local model."
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from local model. Status code: {response.status_code}"
        except Exception as e:
            logger.error(f"Exception when calling Ollama API: {str(e)}")
            return f"Error: Failed to communicate with local model: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if the model is available and responding.
        
        Returns:
            True if model is available, False otherwise
        """
        logger.info(f"Checking availability of local model: {self.model_name}")
        
        # Give Ollama a few seconds to initialize if just started
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Simple test query to check if model is responding
                payload = {
                    "model": self.model_name,
                    "prompt": "Hello",
                    "max_tokens": 1,
                    "stream": False  # Important to get a single response
                }
                logger.info(f"Sending test request to {self.generate_endpoint} (attempt {attempt+1}/{max_retries})")
                response = requests.post(self.generate_endpoint, json=payload, timeout=15)
                
                is_available = response.status_code == 200
                logger.info(f"Local model available: {is_available}, Status code: {response.status_code}")
                
                if is_available:
                    return True
                    
                # If not available, wait before retrying
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"Exception when checking local model availability: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        return False 