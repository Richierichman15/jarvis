"""
Local model handler for Jarvis using Ollama API.
"""
import json
import requests
import logging
import time
import os
import subprocess
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
        self.generate_endpoint = f"{base_url}/api/generate"
        self.current_retry_count = 0
        self.max_retries = 3
        self.max_timeout = 60  # Increased from 30 seconds
        self.backoff_factor = 1.5  # For exponential backoff
        
    def _is_ollama_running(self) -> bool:
        """Check if Ollama service is running.
        
        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            # First check if we can reach the API
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code == 200:
                return True
                
            # If API check fails, try a more system-level check
            if os.name == 'posix':  # Linux/Mac
                # Check for running process
                result = subprocess.run(
                    ["pgrep", "-f", "ollama"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                return result.returncode == 0
            else:  # Windows
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                return "ollama.exe" in result.stdout
        except Exception as e:
            logger.warning(f"Error checking if Ollama is running: {str(e)}")
            return False
    
    def _calculate_timeout(self) -> int:
        """Calculate timeout with exponential backoff.
        
        Returns:
            Timeout in seconds
        """
        if self.current_retry_count == 0:
            return 30  # Start with default 30s timeout
        
        # Apply exponential backoff
        timeout = min(30 * (self.backoff_factor ** self.current_retry_count), self.max_timeout)
        return int(timeout)
    
    def _restart_ollama_if_needed(self) -> bool:
        """Try to restart Ollama if it's not running.
        
        Returns:
            True if restart was successful or not needed, False otherwise
        """
        if self._is_ollama_running():
            return True
            
        logger.warning("Ollama appears to be not running. Attempting to start...")
        try:
            if os.name == 'posix':  # Linux/Mac
                # Start Ollama in the background
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            else:  # Windows
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            # Give it a moment to start
            time.sleep(5)
            return self._is_ollama_running()
        except Exception as e:
            logger.error(f"Failed to start Ollama: {str(e)}")
            return False
        
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
        
        # Reset retry counter if this is a new request
        self.current_retry_count = 0
        
        while self.current_retry_count <= self.max_retries:
            # Check if Ollama is running and try to restart it if needed
            if not self._restart_ollama_if_needed():
                return "Error: Ollama service is not running and could not be started. Please start Ollama manually."
            
            try:
                timeout = self._calculate_timeout()
                logger.info(f"Sending request to Ollama API: {self.generate_endpoint} (attempt {self.current_retry_count+1}/{self.max_retries+1}, timeout: {timeout}s)")
                
                response = requests.post(self.generate_endpoint, json=payload, timeout=timeout)
                
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
                    
                    # Check if model doesn't exist and suggest pulling
                    if response.status_code == 404:
                        return f"Error: Model '{self.model_name}' not found. Try running 'ollama pull {self.model_name}' to download it."
                    
                    # Increment retry counter and try again
                    self.current_retry_count += 1
                    if self.current_retry_count <= self.max_retries:
                        logger.info(f"Retrying in {self.current_retry_count * 2} seconds...")
                        time.sleep(self.current_retry_count * 2)
                    else:
                        return f"Error: Failed to get response from local model after {self.max_retries+1} attempts. Status code: {response.status_code}"
            except requests.exceptions.Timeout:
                logger.error(f"Timeout when calling Ollama API (timeout was {timeout}s)")
                self.current_retry_count += 1
                if self.current_retry_count <= self.max_retries:
                    logger.info(f"Retrying with longer timeout...")
                else:
                    return "Error: Ollama is taking too long to respond. The model might be too large for your system or Ollama may be having issues."
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error when calling Ollama API")
                self.current_retry_count += 1
                if self.current_retry_count <= self.max_retries:
                    logger.info(f"Retrying after connection error...")
                    # Give more time for connection issues
                    time.sleep(self.current_retry_count * 3)
                else:
                    return "Error: Could not connect to Ollama. Make sure the Ollama service is running."
            except Exception as e:
                logger.error(f"Exception when calling Ollama API: {str(e)}")
                self.current_retry_count += 1
                if self.current_retry_count <= self.max_retries:
                    logger.info(f"Retrying after error...")
                    time.sleep(self.current_retry_count * 2)
                else:
                    return f"Error: Failed to communicate with local model: {str(e)}"
        
        # If we've exhausted retries
        return "Error: Failed to get a response from the local model after multiple attempts."
    
    def is_available(self) -> bool:
        """Check if the model is available and responding.
        
        Returns:
            True if model is available, False otherwise
        """
        logger.info(f"Checking availability of local model: {self.model_name}")
        
        # First, check if Ollama service is running
        if not self._restart_ollama_if_needed():
            logger.error("Ollama service is not running and could not be started")
            return False
        
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
                    
                # If model not found, let the user know
                if response.status_code == 404:
                    logger.error(f"Model '{self.model_name}' not found in Ollama")
                    return False
                    
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