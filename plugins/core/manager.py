"""
Plugin manager class that handles discovering, loading, and managing plugins.
"""
import os
import sys
import inspect
import pkgutil
import importlib
import logging
from typing import Dict, List, Type, Optional, Any, Set

from .base import PluginInterface, PluginError

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manager for discovering, loading, and managing plugins.
    """
    
    def __init__(self):
        """
        Initialize the plugin manager.
        """
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_directories: List[str] = []
        
    def register_plugin_directory(self, directory: str) -> None:
        """
        Register a directory to search for plugins.
        
        Args:
            directory (str): The directory path to search for plugins.
        """
        if os.path.isdir(directory) and directory not in self._plugin_directories:
            logger.info(f"Registering plugin directory: {directory}")
            self._plugin_directories.append(directory)
        else:
            logger.warning(f"Plugin directory not found or already registered: {directory}")
    
    def discover_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """
        Discover all available plugins in the registered directories.
        
        Returns:
            Dict[str, Type[PluginInterface]]: Dictionary of plugin names to plugin classes.
        """
        discovered_plugins: Dict[str, Type[PluginInterface]] = {}
        
        for directory in self._plugin_directories:
            # Add directory to sys.path if it's not already there
            if directory not in sys.path:
                sys.path.append(directory)
            
            # Walk through all modules in the directory
            for _, name, ispkg in pkgutil.iter_modules([directory]):
                # Skip packages, we only want modules
                if ispkg:
                    continue
                
                # Import the module
                try:
                    module = importlib.import_module(name)
                    
                    # Look for plugin classes in the module
                    for item_name, item in inspect.getmembers(module, inspect.isclass):
                        # Check if the class is a PluginInterface (but not PluginInterface itself)
                        if (
                            issubclass(item, PluginInterface) 
                            and item != PluginInterface
                            and not item.__name__.startswith('_')
                        ):
                            # Create an instance to get the plugin name
                            try:
                                instance = item()
                                plugin_name = instance.name
                                discovered_plugins[plugin_name] = item
                                logger.info(f"Discovered plugin: {plugin_name} ({item.__name__})")
                            except Exception as e:
                                logger.warning(
                                    f"Failed to instantiate plugin class {item.__name__} in "
                                    f"module {name}: {str(e)}"
                                )
                except Exception as e:
                    logger.warning(f"Failed to import module {name}: {str(e)}")
        
        return discovered_plugins
    
    def load_plugin(self, plugin_class: Type[PluginInterface]) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin_class (Type[PluginInterface]): The plugin class to load.
            
        Returns:
            bool: True if the plugin was loaded successfully, False otherwise.
        """
        try:
            # Create an instance of the plugin
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.name
            
            # Check if the plugin is already loaded
            if plugin_name in self._plugins:
                logger.warning(f"Plugin already loaded: {plugin_name}")
                return False
            
            # Initialize the plugin
            if not plugin_instance.initialize():
                raise PluginError(f"Failed to initialize plugin: {plugin_name}")
            
            # Register the plugin
            self._plugins[plugin_name] = plugin_instance
            logger.info(f"Loaded plugin: {plugin_name} v{plugin_instance.version}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load plugin: {str(e)}")
            return False
    
    def load_plugins(self, plugin_classes: Dict[str, Type[PluginInterface]]) -> Dict[str, bool]:
        """
        Load multiple plugins.
        
        Args:
            plugin_classes (Dict[str, Type[PluginInterface]]): Dictionary of plugin names to plugin classes.
            
        Returns:
            Dict[str, bool]: Dictionary of plugin names to success/failure status.
        """
        results: Dict[str, bool] = {}
        
        # Sort plugins by dependencies
        sorted_plugins = self._sort_plugins_by_dependencies(plugin_classes)
        
        # Load plugins in dependency order
        for plugin_name in sorted_plugins:
            plugin_class = plugin_classes[plugin_name]
            results[plugin_name] = self.load_plugin(plugin_class)
        
        return results
    
    def _sort_plugins_by_dependencies(
        self, plugin_classes: Dict[str, Type[PluginInterface]]
    ) -> List[str]:
        """
        Sort plugins by dependencies.
        
        Args:
            plugin_classes (Dict[str, Type[PluginInterface]]): Dictionary of plugin names to plugin classes.
            
        Returns:
            List[str]: List of plugin names sorted by dependencies.
        """
        # Get dependencies for each plugin
        dependencies: Dict[str, List[str]] = {}
        for plugin_name, plugin_class in plugin_classes.items():
            try:
                instance = plugin_class()
                dependencies[plugin_name] = instance.dependencies
            except Exception as e:
                logger.warning(
                    f"Failed to get dependencies for plugin {plugin_name}: {str(e)}"
                )
                dependencies[plugin_name] = []
        
        # Perform topological sort
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        order: List[str] = []
        
        def visit(plugin_name: str) -> None:
            """
            Visit a plugin and its dependencies recursively.
            
            Args:
                plugin_name (str): The name of the plugin to visit.
            """
            if plugin_name in temp_visited:
                raise PluginError(f"Circular dependency detected: {plugin_name}")
            
            if plugin_name not in visited:
                temp_visited.add(plugin_name)
                
                # Visit dependencies
                for dependency in dependencies.get(plugin_name, []):
                    if dependency in plugin_classes:
                        visit(dependency)
                    else:
                        logger.warning(
                            f"Plugin {plugin_name} depends on {dependency}, "
                            f"but it is not available."
                        )
                
                temp_visited.remove(plugin_name)
                visited.add(plugin_name)
                order.append(plugin_name)
        
        # Visit all plugins
        for plugin_name in plugin_classes.keys():
            if plugin_name not in visited:
                visit(plugin_name)
        
        return order
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name (str): The name of the plugin to unload.
            
        Returns:
            bool: True if the plugin was unloaded successfully, False otherwise.
        """
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return False
        
        try:
            # Get the plugin
            plugin = self._plugins[plugin_name]
            
            # Shutdown the plugin
            if not plugin.shutdown():
                raise PluginError(f"Failed to shutdown plugin: {plugin_name}")
            
            # Remove the plugin
            del self._plugins[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {str(e)}")
            return False
    
    def unload_all_plugins(self) -> Dict[str, bool]:
        """
        Unload all plugins.
        
        Returns:
            Dict[str, bool]: Dictionary of plugin names to success/failure status.
        """
        results: Dict[str, bool] = {}
        
        # Make a copy of the plugin names to avoid modifying the dictionary while iterating
        plugin_names = list(self._plugins.keys())
        
        # Unload plugins in reverse dependency order
        for plugin_name in reversed(plugin_names):
            results[plugin_name] = self.unload_plugin(plugin_name)
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Get a plugin instance by name.
        
        Args:
            plugin_name (str): The name of the plugin to get.
            
        Returns:
            Optional[PluginInterface]: The plugin instance, or None if not found.
        """
        return self._plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """
        Get all loaded plugin instances.
        
        Returns:
            Dict[str, PluginInterface]: Dictionary of plugin names to plugin instances.
        """
        return self._plugins.copy()
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_name (str): The name of the plugin to enable.
            
        Returns:
            bool: True if the plugin was enabled successfully, False otherwise.
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        plugin.enabled = True
        logger.info(f"Enabled plugin: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_name (str): The name of the plugin to disable.
            
        Returns:
            bool: True if the plugin was disabled successfully, False otherwise.
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        plugin.enabled = False
        logger.info(f"Disabled plugin: {plugin_name}")
        return True
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        Check if a plugin is enabled.
        
        Args:
            plugin_name (str): The name of the plugin to check.
            
        Returns:
            bool: True if the plugin is enabled, False otherwise.
        """
        plugin = self.get_plugin(plugin_name)
        return plugin is not None and plugin.enabled
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """
        Configure a plugin.
        
        Args:
            plugin_name (str): The name of the plugin to configure.
            config (Dict[str, Any]): The configuration to set.
            
        Returns:
            bool: True if the plugin was configured successfully, False otherwise.
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        try:
            plugin.set_config(config)
            logger.info(f"Configured plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure plugin {plugin_name}: {str(e)}")
            return False
    
    def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a plugin's configuration.
        
        Args:
            plugin_name (str): The name of the plugin to get configuration for.
            
        Returns:
            Optional[Dict[str, Any]]: The plugin's configuration, or None if not found.
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin not found: {plugin_name}")
            return None
        
        return plugin.get_config()


# Global plugin manager instance
plugin_manager = PluginManager() 