"""
Model manager for Jarvis.
This module handles the logic of selecting between local and remote models.
"""
import logging
from typing import Dict, Any, Optional

from .local_model import OllamaModel
from .openai_model import OpenAIModel
from ..config import COMPLEXITY_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manager for handling multiple LLM models and determining which one to use.
    """
    
    def __init__(self):
        """Initialize the model manager with local and remote models."""
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
        """
        Assess the complexity of a prompt to determine which model to use.
        This is a simple heuristic-based approach that could be improved.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            Complexity score (1-10)
        """
        # Simple heuristics for complexity
        complexity = 1
        
        # Check length - longer prompts are more complex
        if len(prompt) > 500:
            complexity += 2
        elif len(prompt) > 200:
            complexity += 1
            
        # Check for programming/technical keywords
        technical_keywords = [
            "code", "function", "class", "algorithm", "debug", 
            "error", "exception", "programming", "software",
            "complexity", "optimize", "refactor", "architecture",
            "design pattern", "database", "API", "framework"
        ]
        
        for keyword in technical_keywords:
            if keyword.lower() in prompt.lower():
                complexity += 1
                # Cap at 10
                if complexity >= 10:
                    break
                    
        # Check for asking "why" or "how" questions (more complex)
        if prompt.lower().startswith("why ") or prompt.lower().startswith("how "):
            complexity += 1
            
        # Check for multi-part questions
        if ";" in prompt or "\n" in prompt:
            complexity += 1
            
        return min(complexity, 10)  # Cap at 10
    
    def get_response(self, 
                    prompt: str, 
                    system_prompt: Optional[str] = None, 
                    force_model: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response using the appropriate model.
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            force_model: Force the use of a specific model ('local' or 'openai')
            
        Returns:
            Dictionary with response and metadata
        """
        # Determine the complexity of the prompt (1-10)
        complexity = self._determine_complexity(prompt)
        
        # Decide which model to use based on complexity
        if force_model == "local":
            use_openai = False
        elif force_model == "openai":
            use_openai = True
        else:
            use_openai = complexity >= COMPLEXITY_THRESHOLD
            
        logger.info(f"Prompt complexity: {complexity}")
        
        if use_openai:
            logger.info("Using OpenAI model")
        else:
            logger.info("Using local model")
        
        # Generate response using the selected model
        if use_openai and self.openai_available:
            try:
                response = self.openai_model.generate(
                    prompt=prompt,
                    system_prompt=system_prompt
                )
                model_used = "openai"
                logger.info("Generated response using OpenAI model")
            except Exception as e:
                logger.error(f"OpenAI model failed: {str(e)}")
                # Fallback to local model if available
                if self.local_available:
                    response = self.local_model.generate(
                        prompt=prompt,
                        system_prompt=system_prompt
                    )
                    model_used = "local (fallback)"
                    logger.info("Fallback to local model")
                else:
                    return {
                        "response": f"Error: Failed to get a response. OpenAI error: {str(e)}",
                        "model_used": "none",
                        "complexity": complexity,
                        "success": False
                    }
        else:
            try:
                response = self.local_model.generate(
                    prompt=prompt,
                    system_prompt=system_prompt
                )
                
                # Check if the response is an error message from the local model
                if response.startswith("Error:") and self.openai_available:
                    logger.warning("Local model returned an error, trying to fall back to OpenAI")
                    
                    try:
                        fallback_response = self.openai_model.generate(
                            prompt=prompt,
                            system_prompt=system_prompt
                        )
                        model_used = "openai (fallback)"
                        logger.info("Fallback to OpenAI model successful")
                        response = fallback_response
                    except Exception as e:
                        logger.error(f"OpenAI fallback also failed: {str(e)}")
                        # Keep the original error from the local model
                        model_used = "none"
                        # Add additional info about OpenAI fallback failure
                        response += f"\n\nOpenAI fallback also failed: {str(e)}"
                else:
                    model_used = "local"
                    logger.info("Generated response using local model")
            except Exception as e:
                logger.error(f"Local model failed: {str(e)}")
                
                # Try to fall back to OpenAI if available
                if self.openai_available:
                    try:
                        logger.info("Attempting to fall back to OpenAI model")
                        response = self.openai_model.generate(
                            prompt=prompt,
                            system_prompt=system_prompt
                        )
                        model_used = "openai (fallback)"
                        logger.info("Fallback to OpenAI model successful")
                    except Exception as fallback_error:
                        logger.error(f"OpenAI fallback also failed: {str(fallback_error)}")
                        return {
                            "response": f"Error: Local model failed: {str(e)}\nOpenAI fallback also failed: {str(fallback_error)}",
                            "model_used": "none",
                            "complexity": complexity,
                            "success": False
                        }
                else:
                    return {
                        "response": f"Error: Failed to get a response from local model: {str(e)}",
                        "model_used": "none",
                        "complexity": complexity,
                        "success": False
                    }
            
        return {
            "response": response,
            "model_used": model_used,
            "complexity": complexity,
            "success": True
        } 