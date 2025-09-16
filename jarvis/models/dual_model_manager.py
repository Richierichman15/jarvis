"""
Model Manager for Jarvis.
This module handles running local Ollama models
"""
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple

from .local_model import OllamaModel
from ..config import LOCAL_MODEL_NAME, LOCAL_MODEL_BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualModelManager:
    """
    Manager for running local Ollama models.
    """
    
    def __init__(self):
        """Initialize the model manager with Ollama models."""
        # Initialize Ollama model
        self.ollama_available = False
        try:
            self.ollama_model = OllamaModel()
            self.ollama_available = True
            logger.info("Ollama model initialized successfully")
        except Exception as e:
            logger.error(f"Ollama model initialization failed: {str(e)}")
            self.ollama_model = None
    
    def _determine_complexity(self, prompt: str) -> int:
        """Determine the complexity of a prompt on a scale of 1-10.
        
        Args:
            prompt: The user's query
            
        Returns:
            Complexity score from 1-10
        """
        # Simple heuristic: count words and sentences
        word_count = len(prompt.split())
        sentence_count = len([c for c in prompt if c in '.!?'])
        
        # Base complexity on word count and sentence structure
        if word_count < 10:
            return 1
        elif word_count < 20:
            return 2 if sentence_count > 1 else 1
    def _run_model(self, model, model_name, prompt, system_prompt, results):
        """Run the Ollama model and record the timing."""
        try:
            start_time = time.time()
            response = model.generate(prompt, system_prompt=system_prompt)
            end_time = time.time()
            
            results[model_name] = {
                "response": response,
                "time_taken": end_time - start_time,
                "success": True
            }
            logger.info(f"Generated response using {model_name} model in {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"{model_name} model failed: {str(e)}")
            results[model_name] = {
                "response": f"Error: Failed to get a response from {model_name} model: {str(e)}",
                "time_taken": None,
                "success": False
            }
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate a response using the Ollama model.
        
        Args:
            prompt: The user's query
            **kwargs: Additional arguments to pass to the model
            
        Returns:
            Dictionary containing the response and timing information
        """
        start_time = time.time()
        results = {
            'ollama': None,
            'ollama_time': None,
            'error': None
        }
        
        if not self.ollama_available:
            results['error'] = "Ollama model is not available"
            return results
            
        try:
            start = time.time()
            response = self.ollama_model.generate(prompt, **kwargs)
            results['ollama'] = response
            results['ollama_time'] = time.time() - start
        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
            results['error'] = f"Ollama error: {str(e)}"
            
        results['total_time'] = time.time() - start_time
        return results
    
    def get_dual_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Ollama model.
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            
        Returns:
            Dictionary with the response and timing information
        """
        if not self.ollama_available:
            return {
                "response": "Error: Ollama model is not available.",
                "model_used": "none",
                "success": False,
                "ollama_time": None,
                "ollama_response": None
            }
            
        try:
            start_time = time.time()
            response = self.ollama_model.generate(prompt, system_prompt=system_prompt)
            time_taken = time.time() - start_time
            
            return {
                "response": response,
                "model_used": "ollama",
                "success": True,
                "ollama_time": time_taken,
                "ollama_response": response
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "model_used": "ollama",
                "success": False,
                "ollama_time": None,
                "ollama_response": None
            }