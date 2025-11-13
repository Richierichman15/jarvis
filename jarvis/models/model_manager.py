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
try:
    from .claude_model import ClaudeModel
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manager for handling model selection and interaction.
    Priority: Claude (if available) > OpenAI GPT-4o-mini > Ollama local LLM
    """
    
    def __init__(self):
        """Initialize the model manager."""
        logger.info("🚀 Initializing ModelManager...")
        
        # Thread pool for running synchronous Ollama calls without blocking event loop
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ollama")
        
        # Try to initialize Claude model (primary if available)
        self.claude_available = False
        self.claude_model = None
        if CLAUDE_AVAILABLE:
            try:
                self.claude_model = ClaudeModel()
                self.claude_available = True
                logger.info("✅ [ModelManager] Claude model initialized (primary if API key is active)")
            except Exception as e:
                logger.warning(f"⚠️ [ModelManager] Claude model initialization failed: {str(e)}")
                self.claude_model = None
        else:
            logger.info("ℹ️ [ModelManager] Claude not available (anthropic package not installed)")
        
        # Try to initialize Ollama model (local fallback)
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
                logger.info("✅ [ModelManager] OpenAI model initialized: GPT-4o-mini (if API key is active)")
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
        logger.info("📊 [ModelManager] Initialization complete - Priority: Claude > OpenAI > Ollama")
        
        if not self.claude_available and not self.openai_available:
            logger.warning("⚠️ [ModelManager] Neither Claude nor OpenAI available - ensure API keys are configured")
    
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
        Priority: Claude > OpenAI > Ollama
        
        Args:
            prompt: The user's query
            system_prompt: Optional system instructions
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        # Try Claude first (primary if available)
        if self.claude_available and self.claude_model:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                # Claude API calls are async-compatible, run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    self._executor,
                    lambda: self.claude_model.generate_response(messages, temperature, max_tokens)
                )
                
                if not response.startswith("Error"):
                    logger.debug("✅ Response generated by Claude")
                    return response
                else:
                    logger.warning(f"⚠️ Claude returned error, falling back")
            except Exception as e:
                logger.warning(f"⚠️ Claude failed: {str(e)}")
                logger.info("🔄 Falling back to OpenAI...")
                
        # Fall back to OpenAI
        if self.openai_available and self.openai_model:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.openai_model.generate_response(messages, temperature, max_tokens)
                logger.debug("✅ Response generated by GPT-4o-mini")
                return response
            except Exception as e:
                logger.warning(f"⚠️ GPT-4o-mini failed: {str(e)}")
                logger.info("🔄 Falling back to Ollama...")
                
        # Final fallback to Ollama (local)
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
                logger.warning(f"⚠️ Ollama request timed out (>{15}s)")
                self.ollama_available = False
            except Exception as e:
                logger.warning(f"⚠️ {self.ollama_model.model_name if self.ollama_model else 'Ollama'} failed: {str(e)}")
                self.ollama_available = False
                
        return "Error: No models available. Please configure CLAUDE_API_KEY, OPENAI_API_KEY, or ensure Ollama is running."
    
    async def generate_response(self, messages: List[Dict[str, str]], 
                                temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Generate a response using the available model with message format (async to avoid blocking).
        Priority: Claude > OpenAI > Ollama
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        # Try Claude first (primary if available)
        if self.claude_available and self.claude_model:
            try:
                # Claude API calls are async-compatible, run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    self._executor,
                    lambda: self.claude_model.generate_response(messages, temperature, max_tokens)
                )
                
                if not response.startswith("Error"):
                    logger.debug("✅ Response generated by Claude")
                    return response
                else:
                    logger.warning(f"⚠️ Claude returned error, falling back")
            except Exception as e:
                logger.warning(f"⚠️ Claude failed: {str(e)}")
                logger.info("🔄 Falling back to OpenAI...")
                
        # Fall back to OpenAI
        if self.openai_available and self.openai_model:
            try:
                response = self.openai_model.generate_response(messages, temperature, max_tokens)
                logger.debug("✅ Response generated by GPT-4o-mini")
                return response
            except Exception as e:
                logger.warning(f"⚠️ GPT-4o-mini failed: {str(e)}")
                logger.info("🔄 Falling back to Ollama...")
                
        # Final fallback to Ollama (local)
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
                logger.warning(f"⚠️ Ollama request timed out (>{15}s)")
                self.ollama_available = False
            except Exception as e:
                logger.warning(f"⚠️ {self.ollama_model.model_name if self.ollama_model else 'Ollama'} failed: {str(e)}")
                self.ollama_available = False
                
        return "Error: No models available. Please configure CLAUDE_API_KEY, OPENAI_API_KEY, or ensure Ollama is running."

def get_model():
    """Get a model instance for text generation.
    
    Returns:
        A model instance that can generate text responses
    Priority: Claude > OpenAI > Ollama
    """
    manager = ModelManager()
    
    # Return the first available model (prioritize Claude, then OpenAI, then Ollama)
    if manager.claude_available and manager.claude_model:
        return manager.claude_model
    elif manager.openai_available and manager.openai_model:
        return manager.openai_model
    elif manager.ollama_available and manager.ollama_model:
        return manager.ollama_model
    else:
        raise RuntimeError("No models available. Please configure CLAUDE_API_KEY, OPENAI_API_KEY, or ensure Ollama is running.") 