"""
Dual Model Manager for Jarvis.
This module handles running both OpenAI and Claude models in parallel and time them
"""
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple

from .openai_model import OpenAIModel
from .claude_model import ClaudeModel
from ..config import MODEL_A, MODEL_B

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualModelManager:
    """
    Manager for running both OpenAI and Claude models in parallel to compare results and performance.
    """
    
    def __init__(self):
        """Initialize the dual model manager with OpenAI and Claude models."""
        # Initialize OpenAI model
        self.openai_available = False
        try:
            self.openai_model = OpenAIModel()
            self.openai_available = True
            logger.info("OpenAI model initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI model initialization failed: {str(e)}")
            self.openai_model = None
            
        # Initialize Claude model
        self.claude_available = False
        try:
            self.claude_model = ClaudeModel()
            self.claude_available = True
            logger.info("Claude model initialized successfully")
        except Exception as e:
            logger.warning(f"Claude model initialization failed: {str(e)}")
            self.claude_model = None
    
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
        """Run a model in a separate thread and record the timing."""
        try:
            start_time = time.time()
            response = model.generate_response(
                messages=[
                    {"role": "system", "content": system_prompt} if system_prompt else None,
                    {"role": "user", "content": prompt}
                ]
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
        """Generate responses from both OpenAI and Claude models in parallel.
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            
        Returns:
            Dictionary with responses from both models and timing information
        """
        # Results will be stored here
        results = {}
        threads = []
        
        # Create threads for each model
        if self.openai_available:
            openai_thread = threading.Thread(
                target=self._run_model,
                args=(self.openai_model, "openai", prompt, system_prompt, results)
            )
            threads.append(openai_thread)
        
        if self.claude_available:
            claude_thread = threading.Thread(
                target=self._run_model,
                args=(self.claude_model, "claude", prompt, system_prompt, results)
            )
            threads.append(claude_thread)
        
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
                "success": False,
                "openai_time": None,
                "claude_time": None,
                "openai_response": None,
                "claude_response": None
            }
        
        # Extract timing information
        openai_time = results.get("openai", {}).get("time_taken")
        claude_time = results.get("claude", {}).get("time_taken")
        
        # Determine which model was faster
        faster_model = None
        if openai_time is not None and claude_time is not None:
            faster_model = "OpenAI" if openai_time <= claude_time else "Claude"
            time_difference = abs(openai_time - claude_time)
            
            comparison = (
                f"\n\n---\n"
                f"**Performance Comparison:**\n"
                f"- OpenAI model: {openai_time:.2f} seconds\n"
                f"- Claude model: {claude_time:.2f} seconds\n"
                f"- {faster_model} model was faster by {time_difference:.2f} seconds"
            )
        else:
            comparison = "\n\n---\n**Performance Comparison:** Could not compare performance as one model failed."
        
        # Format the main response
        openai_response = results.get("openai", {}).get("response", "No response from OpenAI model")
        claude_response = results.get("claude", {}).get("response", "No response from Claude model")
        
        combined_response = (
            f"**OpenAI Model Response:**\n{openai_response}\n\n"
            f"**Claude Model Response:**\n{claude_response}"
            f"{comparison}"
        )
        
        return {
            "response": combined_response,
            "model_used": "both",
            "success": True,
            "openai_time": openai_time,
            "claude_time": claude_time,
            "openai_response": openai_response,
            "claude_response": claude_response
        } 