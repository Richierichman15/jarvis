"""
Base class for Jarvis plugins.
All plugins should inherit from this class and implement the required methods.
"""
import abc
from typing import Dict, Any, List, Optional


class JarvisPlugin(abc.ABC):
    """Base class for all Jarvis plugins."""
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the plugin."""
        pass
    
    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Return the version of the plugin."""
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Return a description of what the plugin does."""
        pass
    
    @property
    def author(self) -> str:
        """Return the author of the plugin."""
        return "Unknown"
    
    @property
    def required_permissions(self) -> List[str]:
        """Return a list of permissions required by this plugin."""
        return []
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Return the default settings for this plugin."""
        return {}
    
    @abc.abstractmethod
    def initialize(self, jarvis_instance: Any) -> bool:
        """
        Initialize the plugin.
        
        Args:
            jarvis_instance: The instance of Jarvis this plugin is attached to
            
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or Jarvis is shutting down."""
        pass
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the provided settings against the plugin's requirements.
        
        Args:
            settings: The settings to validate
            
        Returns:
            The validated settings, potentially with defaults applied
        """
        # By default, return the settings as-is
        return settings
    
    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """
        Handle a command directed to this plugin.
        
        Args:
            command: The command name
            args: List of command arguments
            
        Returns:
            Response string or None if command not handled
        """
        return None


class ToolPlugin(JarvisPlugin):
    """Base class for plugins that provide tools."""
    
    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        """Return the name of the tool this plugin provides."""
        pass
    
    @property
    @abc.abstractmethod
    def tool_description(self) -> str:
        """Return a description of the tool for the AI to understand its usage."""
        pass
    
    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            params: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        pass
    
    @property
    def intent_patterns(self) -> List[str]:
        """
        Return a list of regex patterns that can be used to detect when this tool should be used.
        
        Returns:
            List of regex patterns
        """
        return []


class SensorPlugin(JarvisPlugin):
    """Base class for plugins that provide sensor data."""
    
    @abc.abstractmethod
    def get_current_data(self) -> Dict[str, Any]:
        """
        Get the current data from the sensor.
        
        Returns:
            Dictionary of sensor readings
        """
        pass
    
    @property
    def sampling_rate(self) -> float:
        """
        Return the recommended sampling rate in seconds.
        
        Returns:
            Sampling rate in seconds
        """
        return 60.0  # Default to once per minute


class IntegrationPlugin(JarvisPlugin):
    """Base class for plugins that integrate with external services."""
    
    @property
    @abc.abstractmethod
    def service_name(self) -> str:
        """Return the name of the external service."""
        pass
    
    @abc.abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the plugin is authenticated with the external service.
        
        Returns:
            True if authenticated, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the external service.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        pass 