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
            
    
    def assess_complexity(self, prompt: str) -> int:
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
        """
        Get a response from the appropriate model based on complexity.
        
        Args:
            prompt: The user's input prompt
            system_prompt: Optional system instructions
            force_model: Optional model to force use ('local' or 'openai')
            
        Returns:
            Dictionary with response and metadata
        """
        complexity = self.assess_complexity(prompt)
        logger.info(f"Prompt complexity: {complexity}")
        
        # Determine which model to use
        use_openai = False
        
        if force_model == "local":
            use_openai = False
            logger.info("Forcing use of local model")
        elif force_model == "openai":
            use_openai = True
            logger.info("Forcing use of OpenAI model")
        else:
            # Prefer local model first, only use OpenAI as fallback
            if not self.local_available and self.openai_available:
                use_openai = True
                logger.info("Local model not available, using OpenAI")
            elif not self.local_available and not self.openai_available:
                logger.error("No AI models are available")
                return {
                    "response": "Error: No AI models are currently available. Please check your configuration.",
                    "model_used": "none",
                    "complexity": complexity,
                    "success": False
                }
            else:
                # Local model is available
                use_openai = False
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
                model_used = "local"
                logger.info("Generated response using local model")
            except Exception as e:
                logger.error(f"Local model failed: {str(e)}")
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