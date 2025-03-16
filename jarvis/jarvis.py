"""
Jarvis AI Assistant.
This is the main class that integrates all components together.
"""
import os
import time
import logging
from typing import Dict, Any, Optional, List

from .models.model_manager import ModelManager
from .memory.conversation_memory import ConversationMemory
from .tools.tool_manager import ToolManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Jarvis:
    """
    Jarvis AI Assistant - Your personal AI companion.
    Modeled after the AI from Iron Man, this assistant uses a hybrid approach
    with local and cloud AI models for intelligence.
    """
    
    def __init__(self, user_name: str = "Boss", enable_plugins: bool = True, 
                 plugin_dir: Optional[str] = None, enable_api: bool = False,
                 api_host: str = "127.0.0.1", api_port: int = 5000):
        """
        Initialize Jarvis with all necessary components.
        
        Args:
            user_name: How Jarvis should address the user
            enable_plugins: Whether to enable the plugin system
            plugin_dir: Directory where plugins are stored (if None, use default)
            enable_api: Whether to enable the API server
            api_host: Host for the API server
            api_port: Port for the API server
        """
        self.user_name = user_name
        self._start_time = time.time()  # Track when Jarvis was started
        
        # Initialize core components
        self.model_manager = ModelManager()
        self.memory = ConversationMemory()
        self.tool_manager = ToolManager()
        
        # Add system introduction to memory
        self._initialize_system_messages()
        
        # Initialize plugin system if enabled
        self.plugin_manager = None
        if enable_plugins:
            try:
                from .plugins.plugin_manager import PluginManager
                self.plugin_manager = PluginManager(self, plugin_dir)
                logging.info("Plugin system initialized")
            except ImportError as e:
                logging.warning(f"Failed to initialize plugin system: {str(e)}")
        
        # Initialize API server if enabled
        self.api_server = None
        if enable_api:
            try:
                from .api.api_server import JarvisAPIServer
                self.api_server = JarvisAPIServer(self, host=api_host, port=api_port)
                logging.info(f"API server initialized at http://{api_host}:{api_port}")
            except ImportError as e:
                logging.warning(f"Failed to initialize API server: {str(e)}")
    
    def _initialize_system_messages(self):
        """Initialize system messages and introduction."""
        # Add system introduction to memory
        intro_message = (
            f"Hello {self.user_name}, I am JARVIS - Just A Rather Very Intelligent System. "
            "I'm here to assist you with various tasks, answer questions, and provide information. "
            "I can use tools like web search to find information for you, and I can remember our conversations. "
            "How can I help you today?"
        )
        
        # System message for model context
        self.system_prompt = (
            "You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant inspired by "
            "the AI from Iron Man. Your responses should be helpful, informative, and concise. "
            f"Address the user as {self.user_name}. Use a friendly, slightly formal tone. "
            "If you don't know something, say so clearly rather than making up information. "
            "You have access to various tools that you can use to help answer questions."
        )
        
        # Record the introduction in memory
        self.memory.add_message("system", self.system_prompt)
        self.memory.add_message("assistant", intro_message)
    
    def _prepare_context(self) -> str:
        """
        Prepare context for the model based on conversation history.
        
        Returns:
            Context string to provide to the model
        """
        return self.memory.format_for_context()
    
    def _should_use_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Determine if a tool should be used for the given query.
        
        Args:
            query: User's input query
            
        Returns:
            Tool call information or None
        """
        tool_calls = self.tool_manager.detect_tool_calls(query)
        if tool_calls:
            # For now, just use the first detected tool call
            return tool_calls[0]
        return None
        
    def process_query(self, query: str) -> str:
        """
        Process a user query and return a response.
        
        Args:
            query: User's input query
            
        Returns:
            Response from the model
        """
        # Add user query to memory
        self.memory.add_message("user", query)
        
        # Check if we should use a tool
        tool_call = self._should_use_tool(query)
        tool_response = None
        
        if tool_call:
            tool_name = tool_call["tool"]
            params = tool_call["params"]
            
            # Execute the tool
            tool_response = self.tool_manager.execute_tool(tool_name, params)
            
            if tool_response:
                # Add tool response to memory
                self.memory.add_message(
                    "system", 
                    f"[Tool '{tool_name}' was used]",
                    {"tool_name": tool_name, "params": params}
                )
        
        # Prepare context for the model
        context = self._prepare_context()
        
        # Prepare the prompt based on tool response
        if tool_response and "web_search" in tool_response.lower():
            enhanced_system_prompt = (
                f"{self.system_prompt}\n\n"
                f"IMPORTANT: I've just performed a web search for the user. "
                f"The search results are below. "
                f"When formulating my response, I should use the information from these search results "
                f"to provide the most accurate and helpful information."
            )
            
            prompt = (
                f"The user asked: {query}\n\n"
                f"I performed a web search and found the following information:\n\n"
                f"{tool_response}\n\n"
                f"Based on these search results, please provide a helpful and accurate response to {self.user_name}, "
                f"citing sources where appropriate. Synthesize the information rather than just listing facts."
            )
            
            system_prompt = enhanced_system_prompt
        elif tool_response:
            prompt = (
                f"I used the {tool_call['tool']} tool to help answer the query: '{query}'. "
                f"Here is the information I found:\n\n{tool_response}\n\n"
                "Based on this information, please provide a helpful response to the user's query."
            )
            system_prompt = self.system_prompt
        else:
            prompt = (
                f"The user's query is: {query}\n\n"
                f"Conversation history:\n{context}\n\n"
                "Please provide a helpful response."
            )
            system_prompt = self.system_prompt
        
        # Get response from the model
        response = self.model_manager.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Add assistant response to memory
        self.memory.add_message(
            "assistant", 
            response,
            {"model_used": "openai"}  # Default to OpenAI since it's our primary model
        )
        
        return response
        
    def get_introduction(self) -> str:
        """
        Get Jarvis's introduction message.
        
        Returns:
            Introduction message
        """
        messages = self.memory.get_conversation_history()
        for message in messages:
            if message["role"] == "assistant":
                return message["content"]
        
        # Fallback introduction
        return f"Hello {self.user_name}, I am JARVIS. How can I assist you today?"
    
    def start_api_server(self, debug: bool = False) -> bool:
        """
        Start the API server if it's initialized.
        
        Args:
            debug: Whether to run the server in debug mode
            
        Returns:
            True if the server was started successfully, False otherwise
        """
        if self.api_server is None:
            logging.warning("API server is not initialized")
            return False
        
        try:
            self.api_server.start(debug=debug)
            return True
        except Exception as e:
            logging.error(f"Failed to start API server: {str(e)}")
            return False
    
    def stop_api_server(self) -> bool:
        """
        Stop the API server if it's running.
        
        Returns:
            True if the server was stopped successfully, False otherwise
        """
        if self.api_server is None:
            logging.warning("API server is not initialized")
            return False
        
        try:
            self.api_server.stop()
            return True
        except Exception as e:
            logging.error(f"Failed to stop API server: {str(e)}")
            return False
    
    def get_api_key(self) -> Optional[str]:
        """
        Get the API key for the API server.
        
        Returns:
            API key or None if the API server is not initialized
        """
        if self.api_server is None:
            return None
        
        return self.api_server.get_api_key()
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        Discover available plugins.
        
        Returns:
            List of plugin information dictionaries or empty list if plugin system is not enabled
        """
        if self.plugin_manager is None:
            logging.warning("Plugin system is not initialized")
            return []
        
        return self.plugin_manager.discover_plugins()
    
    def load_plugin(self, module_name: str, class_name: str) -> bool:
        """
        Load a plugin.
        
        Args:
            module_name: Name of the module containing the plugin
            class_name: Name of the plugin class
            
        Returns:
            True if the plugin was loaded successfully, False otherwise
        """
        if self.plugin_manager is None:
            logging.warning("Plugin system is not initialized")
            return False
        
        plugin = self.plugin_manager.load_plugin(module_name, class_name)
        return plugin is not None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if the plugin was unloaded successfully, False otherwise
        """
        if self.plugin_manager is None:
            logging.warning("Plugin system is not initialized")
            return False
        
        return self.plugin_manager.unload_plugin(plugin_name)
    
    def get_plugin_settings(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get settings for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin settings or None if plugin system is not enabled or settings not found
        """
        if self.plugin_manager is None:
            logging.warning("Plugin system is not initialized")
            return None
        
        return self.plugin_manager.get_plugin_settings(plugin_name)
    
    def update_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]) -> bool:
        """
        Update settings for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            settings: New settings to apply
            
        Returns:
            True if settings were updated successfully, False otherwise
        """
        if self.plugin_manager is None:
            logging.warning("Plugin system is not initialized")
            return False
        
        return self.plugin_manager.update_plugin_settings(plugin_name, settings)
    
    def shutdown(self) -> None:
        """Perform cleanup and shutdown."""
        # Stop API server if running
        if self.api_server is not None and self.api_server.is_running:
            self.api_server.stop()
        
        # Unload all plugins
        if self.plugin_manager is not None:
            for plugin_name in list(self.plugin_manager.plugins.keys()):
                self.plugin_manager.unload_plugin(plugin_name)
        
        logging.info("Jarvis shutdown complete") 