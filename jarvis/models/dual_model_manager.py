"""
Dual Model Manager for Jarvis.
This module handles running both local and OpenAI models in parallel and time them
"""
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple

from .local_model import OllamaModel
from .openai_model import OpenAIModel
from ..config import COMPLEXITY_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualModelManager:
    """
    Manager for running both local and OpenAI models in parallel to compare results and performance.
    """
    
    def __init__(self):
        """Initialize the dual model manager with local and remote models."""
        # Initialize local model first
        self.local_model = OllamaModel()
        self.local_available = self.local_model.is_available()
        logger.info(f"Local model available: {self.local_available}")
        
        # Try to initialize OpenAI model
        self.openai_available = False
        try:
            self.openai_model = OpenAIModel()
            self.openai_available = self.openai_model.is_available()
            logger.info(f"OpenAI model available: {self.openai_available}")
        except ValueError as e:
            # OpenAI API key not set
            logger.warning(f"OpenAI model initialization failed: {str(e)}")
            self.openai_model = None
        except Exception as e:
            logger.warning(f"OpenAI model initialization failed: {str(e)}")
            self.openai_model = None
    
    def _determine_complexity(self, prompt: str) -> int:
        """Determine the complexity of a prompt on a scale of 1-10.
        
        Args:
            prompt: The user's query
            
        Returns:
            Complexity score from 1-10
        """
        # Simple heuristic based on length and complexity indicators
        complexity = 5  # Default middle complexity
        
        # Length-based adjustment
        words = prompt.split()
        if len(words) < 5:
            complexity -= 2
        elif len(words) > 50:
            complexity += 2
            
        # Content-based adjustment
        complexity_indicators = [
            "explain", "analyze", "compare", "contrast", "summarize", 
            "evaluate", "synthesize", "create", "develop", "design",
            "complex", "technical", "difficult", "advanced", "expert"
        ]
        
        simplicity_indicators = [
            "what is", "how do", "where is", "who is", "when is",
            "simple", "basic", "easy", "beginner", "help me"
        ]
        
        # Adjust based on presence of indicators
        for indicator in complexity_indicators:
            if indicator in prompt.lower():
                complexity += 1
                
        for indicator in simplicity_indicators:
            if indicator in prompt.lower():
                complexity -= 1
                
        # Ensure complexity is within range
        complexity = max(1, min(10, complexity))
        
        return complexity
    
    def _run_model(self, model, model_name, prompt, system_prompt, results):
        """Run a model in a separate thread and record the timing.
        
        Args:
            model: The model instance to run
            model_name: Name of the model for logging
            prompt: User prompt
            system_prompt: System instructions
            results: Dictionary to store results
        """
        try:
            start_time = time.time()
            response = model.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
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
    
    def get_dual_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate responses from both local and OpenAI models in parallel.
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            
        Returns:
            Dictionary with responses from both models and timing information
        """
        # Determine the complexity of the prompt (1-10)
        complexity = self._determine_complexity(prompt)
        logger.info(f"Prompt complexity: {complexity}")
        
        # Results will be stored here
        results = {}
        threads = []
        
        # Create threads for each model
        if self.local_available:
            local_thread = threading.Thread(
                target=self._run_model,
                args=(self.local_model, "local", prompt, system_prompt, results)
            )
            threads.append(local_thread)
        
        if self.openai_available:
            openai_thread = threading.Thread(
                target=self._run_model,
                args=(self.openai_model, "openai", prompt, system_prompt, results)
            )
            threads.append(openai_thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Prepare the final response with performance comparison
        if not results:
            return {
                "response": "Error: No models available to generate a response.",
                "model_used": "none",
                "complexity": complexity,
                "success": False,
                "local_time": None,
                "openai_time": None,
                "local_response": None,
                "openai_response": None
            }
        
        # Extract timing information
        local_time = results.get("local", {}).get("time_taken")
        openai_time = results.get("openai", {}).get("time_taken")
        
        # Determine which model was faster
        faster_model = None
        if local_time is not None and openai_time is not None:
            faster_model = "local" if local_time <= openai_time else "openai"
            time_difference = abs(local_time - openai_time)
            
            comparison = (
                f"\n\n---\n"
                f"**Performance Comparison:**\n"
                f"- Local model: {local_time:.2f} seconds\n"
                f"- OpenAI model: {openai_time:.2f} seconds\n"
                f"- {faster_model.capitalize()} model was faster by {time_difference:.2f} seconds"
            )
        else:
            comparison = "\n\n---\n**Performance Comparison:** Could not compare performance as one model failed."
        
        # Format the main response
        local_response = results.get("local", {}).get("response", "No response from local model")
        openai_response = results.get("openai", {}).get("response", "No response from OpenAI model")
        
        combined_response = (
            f"**Local Model Response:**\n{local_response}\n\n"
            f"**OpenAI Model Response:**\n{openai_response}"
            f"{comparison}"
        )
        
        return {
            "response": combined_response,
            "model_used": "both",
            "complexity": complexity,
            "success": True,
            "local_time": local_time,
            "openai_time": openai_time,
            "local_response": local_response,
            "openai_response": openai_response
        } 