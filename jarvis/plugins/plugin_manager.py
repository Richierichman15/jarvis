"""
Plugin manager for Jarvis.
This module handles the loading, enabling, and disabling of plugins.
"""
import os
import sys
import importlib
import logging
import json
import pkgutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from .plugin_base import JarvisPlugin, ToolPlugin, SensorPlugin, IntegrationPlugin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginManager:
    """Manager for handling Jarvis plugins."""
    
    def __init__(self, jarvis_instance: Any, plugin_dir: Optional[str] = None, 
                 settings_file: Optional[str] = None):
        """
        Initialize the plugin manager.
        
        Args:
            jarvis_instance: The instance of Jarvis this manager is attached to
            plugin_dir: The directory where plugins are stored
            settings_file: The file where plugin settings are stored
        """
        self.jarvis = jarvis_instance
        
        # Determine plugin directory
        if plugin_dir is None:
            # Default to plugins directory in the Jarvis package
            self.plugin_dir = os.path.join(os.path.dirname(__file__), 'installed')
        else:
            self.plugin_dir = plugin_dir
            
        # Create the plugin directory if it doesn't exist
        os.makedirs(self.plugin_dir, exist_ok=True)
        
        # Determine settings file
        if settings_file is None:
            self.settings_file = os.path.join(os.path.dirname(__file__), 'plugin_settings.json')
        else:
            self.settings_file = settings_file
            
        # Dictionary to hold loaded plugin instances
        self.plugins: Dict[str, JarvisPlugin] = {}
        
        # Dictionary to hold plugin settings
        self.settings: Dict[str, Dict[str, Any]] = {}
        
        # Load plugin settings
        self._load_settings()
        
        # Add the plugin directory to the Python path
        if self.plugin_dir not in sys.path:
            sys.path.append(self.plugin_dir)
    
    def _load_settings(self) -> None:
        """Load plugin settings from the settings file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
                # Create an empty settings file
                with open(self.settings_file, 'w') as f:
                    json.dump({}, f, indent=4)
        except Exception as e:
            logger.error(f"Error loading plugin settings: {str(e)}")
            self.settings = {}
    
    def _save_settings(self) -> None:
        """Save plugin settings to the settings file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving plugin settings: {str(e)}")
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        Discover available plugins in the plugin directory.
        
        Returns:
            List of plugin information dictionaries
        """
        discovered_plugins: List[Dict[str, Any]] = []
        
        # Scan all Python modules in the plugin directory
        plugin_path = Path(self.plugin_dir)
        for (_, name, ispkg) in pkgutil.iter_modules([str(plugin_path)]):
            if ispkg:  # Only import packages
                try:
                    # Import the package
                    module = importlib.import_module(name, package=self.plugin_dir)
                    
                    # Look for a plugin class in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, JarvisPlugin) and 
                            attr is not JarvisPlugin and
                            attr is not ToolPlugin and
                            attr is not SensorPlugin and
                            attr is not IntegrationPlugin):
                            
                            # Create a temporary instance to get information
                            try:
                                temp_instance = attr()
                                discovered_plugins.append({
                                    'name': temp_instance.name,
                                    'version': temp_instance.version,
                                    'description': temp_instance.description,
                                    'author': temp_instance.author,
                                    'required_permissions': temp_instance.required_permissions,
                                    'module_name': name,
                                    'class_name': attr_name,
                                    'enabled': temp_instance.name in self.plugins,
                                    'type': self._get_plugin_type(attr)
                                })
                            except Exception as e:
                                logger.error(f"Error instantiating plugin class {attr_name} in module {name}: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error discovering plugin in module {name}: {str(e)}")
        
        return discovered_plugins
    
    def _get_plugin_type(self, plugin_class: Type) -> str:
        """Get the type of a plugin class."""
        if issubclass(plugin_class, ToolPlugin):
            return "tool"
        elif issubclass(plugin_class, SensorPlugin):
            return "sensor"
        elif issubclass(plugin_class, IntegrationPlugin):
            return "integration"
        else:
            return "generic"
    
    def load_plugin(self, module_name: str, class_name: str) -> Optional[JarvisPlugin]:
        """
        Load a plugin by its module and class name.
        
        Args:
            module_name: Name of the module containing the plugin
            class_name: Name of the plugin class
            
        Returns:
            The loaded plugin instance or None if loading failed
        """
        try:
            # Import the module
            module = importlib.import_module(module_name, package=self.plugin_dir)
            
            # Get the plugin class
            plugin_class = getattr(module, class_name)
            
            # Create an instance of the plugin
            plugin_instance = plugin_class()
            
            # Get plugin settings or create default ones
            if plugin_instance.name not in self.settings:
                self.settings[plugin_instance.name] = plugin_instance.settings
                self._save_settings()
            
            # Validate settings
            validated_settings = plugin_instance.validate_settings(self.settings[plugin_instance.name])
            self.settings[plugin_instance.name] = validated_settings
            
            # Initialize the plugin
            if plugin_instance.initialize(self.jarvis):
                self.plugins[plugin_instance.name] = plugin_instance
                logger.info(f"Plugin '{plugin_instance.name}' v{plugin_instance.version} loaded successfully")
                
                # Save updated settings
                self._save_settings()
                
                return plugin_instance
            else:
                logger.error(f"Plugin '{plugin_instance.name}' initialization failed")
                return None
                
        except Exception as e:
            logger.error(f"Error loading plugin from module {module_name}, class {class_name}: {str(e)}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if the plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' is not loaded")
            return False
        
        try:
            # Call the plugin's shutdown method
            self.plugins[plugin_name].shutdown()
            
            # Remove the plugin from the loaded plugins dictionary
            del self.plugins[plugin_name]
            
            logger.info(f"Plugin '{plugin_name}' unloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[JarvisPlugin]:
        """
        Get a loaded plugin by name.
        
        Args:
            plugin_name: Name of the plugin to get
            
        Returns:
            The plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, JarvisPlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary of plugin names to plugin instances
        """
        return self.plugins.copy()
    
    def get_plugins_by_type(self, plugin_type: str) -> Dict[str, JarvisPlugin]:
        """
        Get all loaded plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to get ('tool', 'sensor', 'integration', or 'generic')
            
        Returns:
            Dictionary of plugin names to plugin instances
        """
        result = {}
        for name, plugin in self.plugins.items():
            if (plugin_type == 'tool' and isinstance(plugin, ToolPlugin) or
                plugin_type == 'sensor' and isinstance(plugin, SensorPlugin) or
                plugin_type == 'integration' and isinstance(plugin, IntegrationPlugin) or
                plugin_type == 'generic' and not isinstance(plugin, (ToolPlugin, SensorPlugin, IntegrationPlugin))):
                result[name] = plugin
        return result
    
    def get_plugin_settings(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get settings for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary of plugin settings or None if not found
        """
        return self.settings.get(plugin_name)
    
    def update_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]) -> bool:
        """
        Update settings for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            settings: New settings to apply
            
        Returns:
            True if settings were updated successfully, False otherwise
        """
        if plugin_name not in self.settings:
            logger.warning(f"No settings found for plugin '{plugin_name}'")
            return False
        
        plugin = self.get_plugin(plugin_name)
        if plugin:
            # Validate settings
            validated_settings = plugin.validate_settings(settings)
            self.settings[plugin_name] = validated_settings
        else:
            # If plugin is not loaded, just update the settings directly
            self.settings[plugin_name].update(settings)
        
        # Save updated settings
        self._save_settings()
        
        return True
    
    def reset_plugin_settings(self, plugin_name: str) -> bool:
        """
        Reset settings for a specific plugin to defaults.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if settings were reset successfully, False otherwise
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            self.settings[plugin_name] = plugin.settings
            self._save_settings()
            return True
        else:
            logger.warning(f"Plugin '{plugin_name}' is not loaded, cannot reset settings")
            return False
    
    def get_tool_plugins(self) -> Dict[str, ToolPlugin]:
        """
        Get all loaded tool plugins.
        
        Returns:
            Dictionary of plugin names to tool plugin instances
        """
        return {name: plugin for name, plugin in self.plugins.items() 
                if isinstance(plugin, ToolPlugin)}
    
    def get_sensor_plugins(self) -> Dict[str, SensorPlugin]:
        """
        Get all loaded sensor plugins.
        
        Returns:
            Dictionary of plugin names to sensor plugin instances
        """
        return {name: plugin for name, plugin in self.plugins.items() 
                if isinstance(plugin, SensorPlugin)}
    
    def get_integration_plugins(self) -> Dict[str, IntegrationPlugin]:
        """
        Get all loaded integration plugins.
        
        Returns:
            Dictionary of plugin names to integration plugin instances
        """
        return {name: plugin for name, plugin in self.plugins.items() 
                if isinstance(plugin, IntegrationPlugin)} 