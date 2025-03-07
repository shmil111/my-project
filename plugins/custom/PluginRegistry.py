"""
Plugin Registry - A central registry for plugin metadata and integration.

This plugin provides an enhanced registry service that maintains
metadata about all plugins and enables better integration between
plugins and the core application.
"""
import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

from myproject.plugins.core.base import BasePlugin
from myproject.plugins.core.manager import plugin_manager

logger = logging.getLogger(__name__)


class PluginRegistryPlugin(BasePlugin):
    """
    A central registry for plugin metadata and integration.
    
    The Plugin Registry maintains extended information about plugins beyond
    what the core plugin manager tracks, including:
    
    - Usage statistics
    - Health status
    - Performance metrics
    - Dependency relationships
    - Compatibility information
    - Integration points
    - Event hooks
    """
    
    @property
    def name(self) -> str:
        return "plugin_registry"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Central registry for plugin metadata and integration"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        super().__init__()
        self._registry_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "registry_data"
        )
        
        # Create registry data directory if it doesn't exist
        os.makedirs(self._registry_data_dir, exist_ok=True)
        
        # Plugin metadata (extended information beyond what the plugin manager provides)
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Plugin usage statistics
        self._usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Integration points (key: integration_point, value: List of plugin names)
        self._integration_points: Dict[str, List[str]] = {}
        
        # Event hooks (key: event_name, value: Dict of plugin_name -> handler_info)
        self._event_hooks: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Last check time for plugin health
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Load metadata from disk if it exists
            self._load_registry_data()
            
            # Initialize metadata for all currently loaded plugins
            self._initialize_plugin_metadata()
            
            # Register for plugin events
            self._register_for_plugin_events()
            
            # Perform initial health check
            self._check_plugin_health()
            
            logger.info("Plugin registry initialized")
            self._enabled = True
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize plugin registry: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        try:
            # Save metadata to disk
            self._save_registry_data()
            
            logger.info("Plugin registry shut down")
            self._enabled = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to shut down plugin registry: {str(e)}")
            return False
    
    def _load_registry_data(self) -> None:
        """
        Load registry data from disk.
        """
        metadata_file = os.path.join(self._registry_data_dir, "plugin_metadata.json")
        usage_file = os.path.join(self._registry_data_dir, "usage_stats.json")
        integration_file = os.path.join(self._registry_data_dir, "integration_points.json")
        hooks_file = os.path.join(self._registry_data_dir, "event_hooks.json")
        
        try:
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    self._plugin_metadata = json.load(f)
            
            if os.path.exists(usage_file):
                with open(usage_file, "r") as f:
                    self._usage_stats = json.load(f)
            
            if os.path.exists(integration_file):
                with open(integration_file, "r") as f:
                    self._integration_points = json.load(f)
            
            if os.path.exists(hooks_file):
                with open(hooks_file, "r") as f:
                    self._event_hooks = json.load(f)
            
            logger.info("Loaded registry data from disk")
        
        except Exception as e:
            logger.warning(f"Failed to load registry data: {str(e)}")
    
    def _save_registry_data(self) -> None:
        """
        Save registry data to disk.
        """
        metadata_file = os.path.join(self._registry_data_dir, "plugin_metadata.json")
        usage_file = os.path.join(self._registry_data_dir, "usage_stats.json")
        integration_file = os.path.join(self._registry_data_dir, "integration_points.json")
        hooks_file = os.path.join(self._registry_data_dir, "event_hooks.json")
        
        try:
            with open(metadata_file, "w") as f:
                json.dump(self._plugin_metadata, f, indent=2)
            
            with open(usage_file, "w") as f:
                json.dump(self._usage_stats, f, indent=2)
            
            with open(integration_file, "w") as f:
                json.dump(self._integration_points, f, indent=2)
            
            with open(hooks_file, "w") as f:
                json.dump(self._event_hooks, f, indent=2)
            
            logger.info("Saved registry data to disk")
        
        except Exception as e:
            logger.warning(f"Failed to save registry data: {str(e)}")
    
    def _initialize_plugin_metadata(self) -> None:
        """
        Initialize metadata for all currently loaded plugins.
        """
        for plugin_name, plugin in plugin_manager.get_all_plugins().items():
            # Skip if we already have metadata for this plugin
            if plugin_name in self._plugin_metadata:
                continue
            
            # Create basic metadata entry
            self._plugin_metadata[plugin_name] = {
                "name": plugin_name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "dependencies": plugin.dependencies,
                "first_registered": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "category": self._detect_plugin_category(plugin),
                "features": self._detect_plugin_features(plugin),
                "health_status": "unknown",
                "compatibility": {
                    "min_app_version": "1.0.0",
                    "max_app_version": None,
                    "platform_compatibility": ["all"]
                }
            }
            
            # Initialize usage stats
            if plugin_name not in self._usage_stats:
                self._usage_stats[plugin_name] = {
                    "load_count": 0,
                    "initialization_time": 0,
                    "last_used": None,
                    "usage_count": 0,
                    "error_count": 0,
                    "performance": {
                        "avg_response_time": 0,
                        "samples": 0
                    }
                }
            
            # Increment load count
            self._usage_stats[plugin_name]["load_count"] += 1
            
            # Auto-detect and register integration points
            self._detect_integration_points(plugin_name, plugin)
            
            logger.info(f"Initialized metadata for plugin: {plugin_name}")
    
    def _detect_plugin_category(self, plugin: Any) -> str:
        """
        Detect the category of a plugin based on its name, description, or functionality.
        
        Args:
            plugin: The plugin instance.
            
        Returns:
            str: The detected category.
        """
        name = plugin.name.lower()
        description = plugin.description.lower()
        
        if "dashboard" in name or "dashboard" in description or "ui" in name:
            return "ui"
        elif "log" in name or "logging" in description:
            return "logging"
        elif "notification" in name or "notification" in description or "alert" in name:
            return "notification"
        elif "integration" in name or "connect" in description:
            return "integration"
        elif "security" in name or "auth" in name:
            return "security"
        elif "data" in name or "database" in description or "storage" in name:
            return "data"
        elif "utility" in name or "util" in name:
            return "utility"
        else:
            return "other"
    
    def _detect_plugin_features(self, plugin: Any) -> List[str]:
        """
        Detect the features of a plugin based on its methods and attributes.
        
        Args:
            plugin: The plugin instance.
            
        Returns:
            List[str]: The detected features.
        """
        features = []
        
        # Check for common method patterns
        for attr_name in dir(plugin):
            if attr_name.startswith("_"):
                continue
                
            attr = getattr(plugin, attr_name)
            attr_name_lower = attr_name.lower()
            
            if callable(attr):
                # UI-related methods
                if "render" in attr_name_lower or "display" in attr_name_lower or "view" in attr_name_lower:
                    features.append("ui")
                
                # Data processing methods
                if "process" in attr_name_lower or "transform" in attr_name_lower or "convert" in attr_name_lower:
                    features.append("data_processing")
                
                # Export/import methods
                if "export" in attr_name_lower or "import" in attr_name_lower:
                    features.append("data_exchange")
                
                # API-related methods
                if "api" in attr_name_lower or "endpoint" in attr_name_lower or "route" in attr_name_lower:
                    features.append("api")
                
                # Authentication methods
                if "auth" in attr_name_lower or "login" in attr_name_lower or "permission" in attr_name_lower:
                    features.append("authentication")
        
        return list(set(features))  # Remove duplicates
    
    def _detect_integration_points(self, plugin_name: str, plugin: Any) -> None:
        """
        Automatically detect integration points for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            plugin: The plugin instance.
        """
        # Look for integration methods
        for attr_name in dir(plugin):
            if attr_name.startswith("_") or not callable(getattr(plugin, attr_name)):
                continue
            
            attr_name_lower = attr_name.lower()
            
            # Handle integration methods named after common patterns
            if "integrate_with" in attr_name_lower or "register_with" in attr_name_lower:
                integration_point = attr_name_lower.replace("integrate_with_", "").replace("register_with_", "")
                self.register_integration_point(plugin_name, integration_point)
            
            # Handle hook methods
            if "on_" in attr_name_lower:
                event_name = attr_name_lower.replace("on_", "")
                self.register_event_hook(plugin_name, event_name, attr_name)
    
    def _register_for_plugin_events(self) -> None:
        """
        Register for plugin events from the plugin manager.
        
        This method sets up callbacks for plugin lifecycle events.
        """
        # We don't have direct event registration in the plugin manager,
        # but we can setup periodic checks or register with other plugins
        pass
    
    def _check_plugin_health(self) -> None:
        """
        Check the health status of all plugins.
        """
        current_time = time.time()
        
        # Only check health at certain intervals
        if current_time - self._last_health_check < self._health_check_interval:
            return
        
        self._last_health_check = current_time
        
        for plugin_name, plugin in plugin_manager.get_all_plugins().items():
            # Skip self
            if plugin_name == self.name:
                continue
            
            try:
                # Check if plugin is enabled
                is_enabled = plugin_manager.is_plugin_enabled(plugin_name)
                
                # Check dependencies
                dependencies_ok = True
                for dependency in plugin.dependencies:
                    if not plugin_manager.get_plugin(dependency) or not plugin_manager.is_plugin_enabled(dependency):
                        dependencies_ok = False
                        break
                
                # Determine health status
                if is_enabled and dependencies_ok:
                    health_status = "healthy"
                elif is_enabled and not dependencies_ok:
                    health_status = "degraded"
                else:
                    health_status = "disabled"
                
                # Update metadata
                if plugin_name in self._plugin_metadata:
                    self._plugin_metadata[plugin_name]["health_status"] = health_status
                    self._plugin_metadata[plugin_name]["last_health_check"] = datetime.now().isoformat()
            
            except Exception as e:
                logger.warning(f"Failed to check health for plugin {plugin_name}: {str(e)}")
                
                # Update metadata to indicate error
                if plugin_name in self._plugin_metadata:
                    self._plugin_metadata[plugin_name]["health_status"] = "error"
                    self._plugin_metadata[plugin_name]["last_health_check"] = datetime.now().isoformat()
                    self._plugin_metadata[plugin_name]["last_error"] = str(e)
                
                # Update usage stats
                if plugin_name in self._usage_stats:
                    self._usage_stats[plugin_name]["error_count"] += 1
        
        logger.info("Completed plugin health check")
    
    #
    # Public API
    #
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get extended metadata for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            
        Returns:
            Optional[Dict[str, Any]]: The plugin metadata, or None if not found.
        """
        return self._plugin_metadata.get(plugin_name)
    
    def get_all_plugin_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get extended metadata for all plugins.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of plugin names to metadata.
        """
        return self._plugin_metadata.copy()
    
    def update_plugin_metadata(self, plugin_name: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            metadata (Dict[str, Any]): The metadata to update.
            
        Returns:
            bool: True if the metadata was updated, False otherwise.
        """
        if plugin_name not in self._plugin_metadata:
            logger.warning(f"Plugin {plugin_name} not found in registry")
            return False
        
        # Update the metadata
        self._plugin_metadata[plugin_name].update(metadata)
        
        # Update the last_updated timestamp
        self._plugin_metadata[plugin_name]["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"Updated metadata for plugin: {plugin_name}")
        return True
    
    def record_plugin_usage(self, plugin_name: str, operation: str = "usage") -> bool:
        """
        Record usage of a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            operation (str): The operation being performed (usage, error, etc).
            
        Returns:
            bool: True if the usage was recorded, False otherwise.
        """
        if plugin_name not in self._usage_stats:
            logger.warning(f"Plugin {plugin_name} not found in usage stats")
            return False
        
        # Update usage stats based on operation
        if operation == "usage":
            self._usage_stats[plugin_name]["usage_count"] += 1
            self._usage_stats[plugin_name]["last_used"] = datetime.now().isoformat()
        elif operation == "error":
            self._usage_stats[plugin_name]["error_count"] += 1
        
        logger.debug(f"Recorded {operation} for plugin: {plugin_name}")
        return True
    
    def get_plugin_usage_stats(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get usage statistics for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            
        Returns:
            Optional[Dict[str, Any]]: The usage statistics, or None if not found.
        """
        return self._usage_stats.get(plugin_name)
    
    def get_all_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get usage statistics for all plugins.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of plugin names to usage statistics.
        """
        return self._usage_stats.copy()
    
    def register_integration_point(self, plugin_name: str, integration_point: str) -> bool:
        """
        Register a plugin for an integration point.
        
        Args:
            plugin_name (str): The name of the plugin.
            integration_point (str): The integration point to register for.
            
        Returns:
            bool: True if the plugin was registered, False otherwise.
        """
        # Ensure plugin exists
        if not plugin_manager.get_plugin(plugin_name):
            logger.warning(f"Cannot register integration point: Plugin {plugin_name} not found")
            return False
        
        # Create integration point if it doesn't exist
        if integration_point not in self._integration_points:
            self._integration_points[integration_point] = []
        
        # Add plugin to integration point if not already registered
        if plugin_name not in self._integration_points[integration_point]:
            self._integration_points[integration_point].append(plugin_name)
            logger.info(f"Registered plugin {plugin_name} for integration point: {integration_point}")
        
        return True
    
    def unregister_integration_point(self, plugin_name: str, integration_point: str) -> bool:
        """
        Unregister a plugin from an integration point.
        
        Args:
            plugin_name (str): The name of the plugin.
            integration_point (str): The integration point to unregister from.
            
        Returns:
            bool: True if the plugin was unregistered, False otherwise.
        """
        # Check if integration point exists
        if integration_point not in self._integration_points:
            logger.warning(f"Integration point {integration_point} not found")
            return False
        
        # Remove plugin from integration point
        if plugin_name in self._integration_points[integration_point]:
            self._integration_points[integration_point].remove(plugin_name)
            logger.info(f"Unregistered plugin {plugin_name} from integration point: {integration_point}")
            return True
        
        logger.warning(f"Plugin {plugin_name} not registered for integration point: {integration_point}")
        return False
    
    def get_plugins_for_integration_point(self, integration_point: str) -> List[str]:
        """
        Get all plugins registered for an integration point.
        
        Args:
            integration_point (str): The integration point to get plugins for.
            
        Returns:
            List[str]: List of plugin names registered for the integration point.
        """
        return self._integration_points.get(integration_point, []).copy()
    
    def get_all_integration_points(self) -> Dict[str, List[str]]:
        """
        Get all integration points and their registered plugins.
        
        Returns:
            Dict[str, List[str]]: Dictionary of integration points to lists of plugin names.
        """
        return self._integration_points.copy()
    
    def register_event_hook(self, plugin_name: str, event_name: str, handler_name: str) -> bool:
        """
        Register a plugin event hook.
        
        Args:
            plugin_name (str): The name of the plugin.
            event_name (str): The name of the event to hook into.
            handler_name (str): The name of the handler method in the plugin.
            
        Returns:
            bool: True if the hook was registered, False otherwise.
        """
        # Ensure plugin exists
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Cannot register event hook: Plugin {plugin_name} not found")
            return False
        
        # Ensure handler method exists
        if not hasattr(plugin, handler_name) or not callable(getattr(plugin, handler_name)):
            logger.warning(f"Cannot register event hook: Handler method {handler_name} not found in plugin {plugin_name}")
            return False
        
        # Create event if it doesn't exist
        if event_name not in self._event_hooks:
            self._event_hooks[event_name] = {}
        
        # Add handler to event
        self._event_hooks[event_name][plugin_name] = {
            "handler_name": handler_name,
            "registered_at": datetime.now().isoformat()
        }
        
        logger.info(f"Registered event hook: {plugin_name}.{handler_name} for event {event_name}")
        return True
    
    def unregister_event_hook(self, plugin_name: str, event_name: str) -> bool:
        """
        Unregister a plugin event hook.
        
        Args:
            plugin_name (str): The name of the plugin.
            event_name (str): The name of the event to unhook from.
            
        Returns:
            bool: True if the hook was unregistered, False otherwise.
        """
        # Check if event exists
        if event_name not in self._event_hooks:
            logger.warning(f"Event {event_name} not found")
            return False
        
        # Remove handler from event
        if plugin_name in self._event_hooks[event_name]:
            del self._event_hooks[event_name][plugin_name]
            logger.info(f"Unregistered event hook: {plugin_name} for event {event_name}")
            return True
        
        logger.warning(f"Plugin {plugin_name} not registered for event: {event_name}")
        return False
    
    def trigger_event(self, event_name: str, **event_data) -> Dict[str, Any]:
        """
        Trigger an event and call all registered handlers.
        
        Args:
            event_name (str): The name of the event to trigger.
            **event_data: Event data to pass to handlers.
            
        Returns:
            Dict[str, Any]: Dictionary of plugin names to handler results.
        """
        results = {}
        
        # Check if event exists
        if event_name not in self._event_hooks:
            logger.warning(f"No handlers registered for event: {event_name}")
            return results
        
        # Call each handler
        for plugin_name, hook_info in self._event_hooks[event_name].items():
            handler_name = hook_info["handler_name"]
            
            # Get plugin
            plugin = plugin_manager.get_plugin(plugin_name)
            if not plugin:
                logger.warning(f"Plugin {plugin_name} not found, skipping event handler")
                continue
            
            # Check if plugin is enabled
            if not plugin_manager.is_plugin_enabled(plugin_name):
                logger.warning(f"Plugin {plugin_name} is disabled, skipping event handler")
                continue
            
            # Get handler method
            if not hasattr(plugin, handler_name) or not callable(getattr(plugin, handler_name)):
                logger.warning(f"Handler method {handler_name} not found in plugin {plugin_name}")
                continue
            
            handler = getattr(plugin, handler_name)
            
            # Call handler
            try:
                # Record start time for performance measurement
                start_time = time.time()
                
                # Call the handler with event data
                result = handler(**event_data)
                
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                
                # Update performance stats
                if plugin_name in self._usage_stats:
                    stats = self._usage_stats[plugin_name]["performance"]
                    avg_time = stats["avg_response_time"]
                    samples = stats["samples"]
                    
                    # Update average using weighted average formula
                    if samples > 0:
                        stats["avg_response_time"] = (avg_time * samples + elapsed_time) / (samples + 1)
                    else:
                        stats["avg_response_time"] = elapsed_time
                    
                    stats["samples"] += 1
                
                # Record usage
                self.record_plugin_usage(plugin_name)
                
                # Store result
                results[plugin_name] = result
                
                logger.debug(f"Triggered event {event_name} handler in {plugin_name}: {handler_name} (took {elapsed_time:.6f}s)")
            
            except Exception as e:
                logger.error(f"Error in event handler {plugin_name}.{handler_name}: {str(e)}")
                
                # Record error
                self.record_plugin_usage(plugin_name, "error")
                
                # Store error result
                results[plugin_name] = {"error": str(e)}
        
        return results
    
    def get_event_hooks(self, event_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all plugins registered for an event.
        
        Args:
            event_name (str): The name of the event to get hooks for.
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of plugin names to hook information.
        """
        return self._event_hooks.get(event_name, {}).copy()
    
    def get_all_event_hooks(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get all events and their registered hooks.
        
        Returns:
            Dict[str, Dict[str, Dict[str, Any]]]: Dictionary of events to dictionaries of plugin names to hook information.
        """
        return self._event_hooks.copy()
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the dependency graph of all plugins.
        
        Returns:
            Dict[str, List[str]]: Dictionary of plugin names to lists of dependent plugin names.
        """
        graph = {}
        
        # Build the dependency graph
        for plugin_name, plugin in plugin_manager.get_all_plugins().items():
            # Add the plugin to the graph if not already there
            if plugin_name not in graph:
                graph[plugin_name] = []
            
            # Add dependencies to the graph
            for dependency in plugin.dependencies:
                if dependency not in graph:
                    graph[dependency] = []
                
                # Add the plugin as dependent on its dependency
                if plugin_name not in graph[dependency]:
                    graph[dependency].append(plugin_name)
        
        return graph
    
    def analyze_plugin_compatibility(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze compatibility between plugins.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of plugin names to compatibility information.
        """
        compatibility = {}
        
        # Analyze dependency graph for conflicts and unmet dependencies
        dependency_graph = self.get_dependency_graph()
        
        for plugin_name, plugin in plugin_manager.get_all_plugins().items():
            compatibility[plugin_name] = {
                "missing_dependencies": [],
                "dependent_plugins": dependency_graph.get(plugin_name, []),
                "conflicts": []
            }
            
            # Check for missing dependencies
            for dependency in plugin.dependencies:
                if not plugin_manager.get_plugin(dependency):
                    compatibility[plugin_name]["missing_dependencies"].append(dependency)
        
        return compatibility
    
    def get_plugin_categories(self) -> Dict[str, List[str]]:
        """
        Get plugins grouped by category.
        
        Returns:
            Dict[str, List[str]]: Dictionary of categories to lists of plugin names.
        """
        categories = {}
        
        for plugin_name, metadata in self._plugin_metadata.items():
            category = metadata.get("category", "other")
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(plugin_name)
        
        return categories
    
    def get_plugins_by_feature(self, feature: str) -> List[str]:
        """
        Get plugins that have a specific feature.
        
        Args:
            feature (str): The feature to search for.
            
        Returns:
            List[str]: List of plugin names with the specified feature.
        """
        result = []
        
        for plugin_name, metadata in self._plugin_metadata.items():
            if feature in metadata.get("features", []):
                result.append(plugin_name)
        
        return result
    
    def get_health_summary(self) -> Dict[str, int]:
        """
        Get a summary of plugin health status.
        
        Returns:
            Dict[str, int]: Dictionary of health status to count of plugins with that status.
        """
        summary = {
            "healthy": 0,
            "degraded": 0,
            "disabled": 0,
            "error": 0,
            "unknown": 0
        }
        
        for metadata in self._plugin_metadata.values():
            status = metadata.get("health_status", "unknown")
            if status in summary:
                summary[status] += 1
        
        return summary 