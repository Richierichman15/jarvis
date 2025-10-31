"""
Model Manager for Jarvis.
This module handles model selection and interaction.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from .openai_model import OpenAIModel
from .local_model import OllamaModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manager for handling model selection and interaction.
    Uses OpenAI GPT-4o-mini by default, with local Ollama LLM as fallback.
    """
    
    def __init__(self):
        """Initialize the model manager."""
        logger.info("🚀 Initializing ModelManager...")
        
        # Thread pool for running synchronous Ollama calls without blocking event loop
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ollama")
        
        # Try to initialize Ollama model (primary for local usage)
        self.ollama_available = False  # Default to False, will be checked async later
        self.ollama_model = None
        try:
            self.ollama_model = OllamaModel()
            logger.info("🔄 [ModelManager] Ollama model initialized, availability will be checked asynchronously")
        except Exception as e:
            logger.warning(f"⚠️ [ModelManager] Ollama model initialization failed: {str(e)}")
            self.ollama_model = None
            
        # Try to initialize OpenAI model (backup)
        self.openai_available = False
        self.openai_model = None
        try:
            # Remove proxies from environment if present to avoid version conflicts
            import os
            proxies_backup = {}
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                if key in os.environ:
                    proxies_backup[key] = os.environ.pop(key)
            
            try:
                self.openai_model = OpenAIModel()
                self.openai_available = True
                logger.info("✅ [ModelManager] Backup model: GPT-4o-mini (if OpenAI key is active)")
            except Exception as e:
                logger.warning(f"⚠️ [ModelManager] OpenAI model initialization failed: {str(e)}")
                self.openai_model = None
            finally:
                # Restore proxy environment variables
                for key, value in proxies_backup.items():
                    os.environ[key] = value
        except Exception as e:
            logger.warning(f"⚠️ [ModelManager] OpenAI model initialization failed: {str(e)}")
            self.openai_model = None
            
        # Log initial status
        logger.info("📊 [ModelManager] Initialization complete - Ollama availability will be checked when needed")
        
        if not self.openai_available:
            logger.warning("⚠️ [ModelManager] OpenAI not available - ensure OPENAI_API_KEY is configured")
    
    async def check_ollama_availability(self):
        """Check if Ollama is available asynchronously."""
        if self.ollama_model is None:
            return False
        
        try:
            self.ollama_available = await self.ollama_model.is_available()
            if self.ollama_available:
                logger.info(f"✅ [ModelManager] Ollama is now available: {self.ollama_model.model_name}")
            else:
                logger.info("⚠️ [ModelManager] Ollama is not available")
            return self.ollama_available
        except Exception as e:
            logger.warning(f"⚠️ [ModelManager] Error checking Ollama availability: {str(e)}")
            self.ollama_available = False
            return False
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Generate a response using the available model (async version to avoid blocking).
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        # Try Ollama first (primary for local usage)
        # Run in thread pool to avoid blocking event loop
        if self.ollama_model:
            try:
                # Run synchronous Ollama call in thread pool with short timeout
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor,
                        lambda: self.ollama_model.generate(prompt, system_prompt, temperature, max_tokens)
                    ),
                    timeout=15.0  # Fast timeout to avoid blocking Discord
                )
                # If successful, mark as available for future use
                if not self.ollama_available and not response.startswith("Error:"):
                    self.ollama_available = True
                    logger.info(f"✅ Ollama confirmed available: {self.ollama_model.model_name}")
                logger.debug(f"✅ Response generated by {self.ollama_model.model_name}")
                return response
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Ollama request timed out (>{15}s), falling back to OpenAI")
                self.ollama_available = False
            except Exception as e:
                logger.warning(f"⚠️ {self.ollama_model.model_name if self.ollama_model else 'Ollama'} failed: {str(e)}")
                self.ollama_available = False
                logger.info("🔄 Falling back to OpenAI GPT-4o-mini...")
                
        # Fall back to OpenAI if Ollama fails or is not available
        if self.openai_available and self.openai_model:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.openai_model.generate_response(messages, temperature, max_tokens)
                logger.debug("✅ Response generated by GPT-4o-mini (fallback)")
                return response
            except Exception as e:
                logger.warning(f"⚠️ GPT-4o-mini failed: {str(e)}")
                
        return "Error: No models available. Please configure OPENAI_API_KEY or ensure Ollama is running."
    
    async def generate_response(self, messages: List[Dict[str, str]], 
                                temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Generate a response using the available model with message format (async to avoid blocking).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        # Try Ollama first (primary for local usage)
        # Run in thread pool to avoid blocking event loop
        if self.ollama_model:
            try:
                # Convert messages to prompt format for Ollama
                prompt = ""
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        prompt = f"System: {content}\n\n{prompt}"
                    elif role == "user":
                        prompt += f"User: {content}\n"
                    elif role == "assistant":
                        prompt += f"Assistant: {content}\n"
                
                # Run synchronous Ollama call in thread pool with short timeout
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor,
                        lambda: self.ollama_model.generate(prompt, temperature=temperature, max_tokens=max_tokens)
                    ),
                    timeout=15.0  # Fast timeout to avoid blocking Discord
                )
                # If successful, mark as available for future use
                if not self.ollama_available and not response.startswith("Error:"):
                    self.ollama_available = True
                    logger.info(f"✅ Ollama confirmed available: {self.ollama_model.model_name}")
                logger.debug(f"✅ Response generated by {self.ollama_model.model_name}")
                return response
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Ollama request timed out (>{15}s), falling back to OpenAI")
                self.ollama_available = False
            except Exception as e:
                logger.warning(f"⚠️ {self.ollama_model.model_name if self.ollama_model else 'Ollama'} failed: {str(e)}")
                self.ollama_available = False
                logger.info("🔄 Falling back to OpenAI GPT-4o-mini...")
                
        # Fall back to OpenAI if Ollama fails or is not available
        if self.openai_available and self.openai_model:
            try:
                response = self.openai_model.generate_response(messages, temperature, max_tokens)
                logger.debug("✅ Response generated by GPT-4o-mini (fallback)")
                return response
            except Exception as e:
                logger.warning(f"⚠️ GPT-4o-mini failed: {str(e)}")
                
        return "Error: No models available. Please configure OPENAI_API_KEY or ensure Ollama is running."

def get_model():
    """Get a model instance for text generation.
    
    Returns:
        A model instance that can generate text responses
    """
    manager = ModelManager()
    
    # Return the first available model (prioritize Ollama)
    if manager.ollama_available:
        return manager.ollama_model
    elif manager.openai_available:
        return manager.openai_model
    else:
        raise RuntimeError("No models available. Please configure OPENAI_API_KEY or ensure Ollama is running.") 