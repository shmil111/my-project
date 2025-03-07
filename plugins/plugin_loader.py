"""
Plugin loader module that simplifies loading plugins in the main application.
"""
import os
import logging
import importlib.util
from typing import List, Dict, Any, Optional

from .core.manager import plugin_manager

logger = logging.getLogger(__name__)


def initialize_plugin_system(plugin_directories: List[str] = None) -> None:
    """
    Initialize the plugin system by registering plugin directories.
    
    Args:
        plugin_directories (List[str]): List of directories to search for plugins.
            If None, use the default directories.
    """
    if plugin_directories is None:
        # Use default plugin directories
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_directories = [
            os.path.join(base_dir, "plugins", "examples"),
            os.path.join(base_dir, "plugins", "custom")
        ]
    
    # Register plugin directories
    for directory in plugin_directories:
        if os.path.isdir(directory):
            plugin_manager.register_plugin_directory(directory)
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                plugin_manager.register_plugin_directory(directory)
            except Exception as e:
                logger.warning(f"Failed to create plugin directory {directory}: {str(e)}")


def discover_and_load_plugins(
    auto_enable: bool = True, 
    excluded_plugins: List[str] = None
) -> Dict[str, bool]:
    """
    Discover and load all available plugins.
    
    Args:
        auto_enable (bool): Whether to automatically enable all loaded plugins.
        excluded_plugins (List[str]): List of plugin names to exclude from loading.
            
    Returns:
        Dict[str, bool]: Dictionary of plugin names to success/failure status.
    """
    # Discover plugins
    discovered_plugins = plugin_manager.discover_plugins()
    
    # Filter out excluded plugins
    if excluded_plugins:
        for plugin_name in excluded_plugins:
            if plugin_name in discovered_plugins:
                del discovered_plugins[plugin_name]
    
    # Load plugins
    results = plugin_manager.load_plugins(discovered_plugins)
    
    # Enable plugins if requested
    if auto_enable:
        for plugin_name, success in results.items():
            if success:
                plugin_manager.enable_plugin(plugin_name)
    
    return results


def load_plugin_from_file(file_path: str, auto_enable: bool = True) -> bool:
    """
    Load a plugin from a file path.
    
    Args:
        file_path (str): The path to the plugin file.
        auto_enable (bool): Whether to automatically enable the loaded plugin.
            
    Returns:
        bool: True if the plugin was loaded successfully, False otherwise.
    """
    try:
        # Get the module name from the file path
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load plugin from {file_path}: Invalid module specification")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for plugin classes in the module
        from .core.base import PluginInterface
        plugin_class = None
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type) 
                and issubclass(attr, PluginInterface) 
                and attr.__name__ != "PluginInterface"
                and not attr.__name__.startswith("_")
            ):
                plugin_class = attr
                break
        
        if plugin_class is None:
            logger.error(f"No plugin class found in {file_path}")
            return False
        
        # Load the plugin
        result = plugin_manager.load_plugin(plugin_class)
        
        # Enable the plugin if requested
        if result and auto_enable:
            # Create an instance to get the plugin name
            instance = plugin_class()
            plugin_manager.enable_plugin(instance.name)
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to load plugin from {file_path}: {str(e)}")
        return False


def configure_plugin(
    plugin_name: str, config: Dict[str, Any]
) -> bool:
    """
    Configure a plugin.
    
    Args:
        plugin_name (str): The name of the plugin to configure.
        config (Dict[str, Any]): The configuration to set.
            
    Returns:
        bool: True if the plugin was configured successfully, False otherwise.
    """
    return plugin_manager.configure_plugin(plugin_name, config)


def enable_plugin(plugin_name: str) -> bool:
    """
    Enable a plugin.
    
    Args:
        plugin_name (str): The name of the plugin to enable.
            
    Returns:
        bool: True if the plugin was enabled successfully, False otherwise.
    """
    return plugin_manager.enable_plugin(plugin_name)


def disable_plugin(plugin_name: str) -> bool:
    """
    Disable a plugin.
    
    Args:
        plugin_name (str): The name of the plugin to disable.
            
    Returns:
        bool: True if the plugin was disabled successfully, False otherwise.
    """
    return plugin_manager.disable_plugin(plugin_name)


def get_plugin(plugin_name: str) -> Optional[Any]:
    """
    Get a plugin instance by name.
    
    Args:
        plugin_name (str): The name of the plugin to get.
            
    Returns:
        Optional[Any]: The plugin instance, or None if not found.
    """
    return plugin_manager.get_plugin(plugin_name)


def get_all_plugins() -> Dict[str, Any]:
    """
    Get all loaded plugin instances.
    
    Returns:
        Dict[str, Any]: Dictionary of plugin names to plugin instances.
    """
    return plugin_manager.get_all_plugins()


def unload_plugin(plugin_name: str) -> bool:
    """
    Unload a plugin.
    
    Args:
        plugin_name (str): The name of the plugin to unload.
            
    Returns:
        bool: True if the plugin was unloaded successfully, False otherwise.
    """
    return plugin_manager.unload_plugin(plugin_name)


def unload_all_plugins() -> Dict[str, bool]:
    """
    Unload all plugins.
    
    Returns:
        Dict[str, bool]: Dictionary of plugin names to success/failure status.
    """
    return plugin_manager.unload_all_plugins()


def is_plugin_enabled(plugin_name: str) -> bool:
    """
    Check if a plugin is enabled.
    
    Args:
        plugin_name (str): The name of the plugin to check.
            
    Returns:
        bool: True if the plugin is enabled, False otherwise.
    """
    return plugin_manager.is_plugin_enabled(plugin_name) 