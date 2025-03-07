"""
Base plugin class and interfaces for the plugin system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class PluginInterface(ABC):
    """
    Base interface that all plugins must implement.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: The name of the plugin.
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: The version of the plugin.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            str: The description of the plugin.
        """
        pass
    
    @property
    def author(self) -> str:
        """
        Get the author of the plugin.
        
        Returns:
            str: The author of the plugin.
        """
        return "Unknown"
    
    @property
    def dependencies(self) -> List[str]:
        """
        Get the list of plugin dependencies.
        
        Returns:
            List[str]: List of plugin names that this plugin depends on.
        """
        return []
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin. This method is called when the plugin is loaded.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Shutdown the plugin. This method is called when the plugin is unloaded.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        pass
    
    @property
    def enabled(self) -> bool:
        """
        Check if the plugin is enabled.
        
        Returns:
            bool: True if the plugin is enabled, False otherwise.
        """
        return hasattr(self, "_enabled") and self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """
        Set whether the plugin is enabled.
        
        Args:
            value (bool): True to enable the plugin, False to disable it.
        """
        self._enabled = value
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration of the plugin.
        
        Returns:
            Dict[str, Any]: The configuration of the plugin.
        """
        return getattr(self, "_config", {})
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set the configuration of the plugin.
        
        Args:
            config (Dict[str, Any]): The configuration to set.
        """
        self._config = config


class BasePlugin(PluginInterface):
    """
    Base class for plugins that implements common functionality.
    Subclass this class to create a new plugin.
    """
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        self._enabled = False
        self._config = {}
        
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    def initialize(self) -> bool:
        """
        Default implementation of initialize.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        self._enabled = True
        return True
    
    def shutdown(self) -> bool:
        """
        Default implementation of shutdown.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        self._enabled = False
        return True


class PluginError(Exception):
    """
    Exception raised for plugin-related errors.
    """
    
    def __init__(self, message: str, plugin_name: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            message (str): The error message.
            plugin_name (Optional[str]): The name of the plugin that caused the error.
        """
        if plugin_name:
            message = f"[Plugin {plugin_name}] {message}"
        super().__init__(message) 