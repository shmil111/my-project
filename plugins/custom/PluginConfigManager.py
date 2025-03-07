"""
Plugin Configuration Manager - Advanced configuration management for plugins.

This plugin provides enhanced configuration management for plugins,
including configuration validation, inheritance, templates, and versioning.
"""
import logging
import os
import json
import copy
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable

from myproject.plugins.core.base import BasePlugin
from myproject.plugins.core.manager import plugin_manager

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass


class PluginConfigManagerPlugin(BasePlugin):
    """
    Plugin Configuration Manager

    Provides advanced configuration management for plugins, including:
    
    - Schema-based configuration validation
    - Configuration inheritance and templates
    - Version tracking of configuration changes
    - Import/export of configurations
    - Environment-specific configurations
    - Configuration presets
    """
    
    @property
    def name(self) -> str:
        return "plugin_config_manager"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Advanced configuration management for plugins"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        super().__init__()
        self._config_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config_data"
        )
        
        # Create config directory if it doesn't exist
        os.makedirs(self._config_dir, exist_ok=True)
        
        # Configuration schemas (validation rules)
        self._config_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Configuration templates
        self._config_templates: Dict[str, Dict[str, Any]] = {}
        
        # Configuration history (version tracking)
        self._config_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Configuration presets
        self._config_presets: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Environment-specific configurations
        self._environments: List[str] = ["development", "testing", "production"]
        self._current_environment = "development"
        
        # Configuration versions
        self._config_versions: Dict[str, int] = {}
        
        # Default validation functions
        self._validators: Dict[str, Callable] = {
            "string": lambda v, p: isinstance(v, str),
            "number": lambda v, p: isinstance(v, (int, float)),
            "integer": lambda v, p: isinstance(v, int),
            "boolean": lambda v, p: isinstance(v, bool),
            "array": lambda v, p: isinstance(v, list),
            "object": lambda v, p: isinstance(v, dict),
            "email": lambda v, p: isinstance(v, str) and bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v)),
            "url": lambda v, p: isinstance(v, str) and bool(re.match(r"^https?://", v)),
            "enum": lambda v, p: v in p.get("enum", []),
            "min": lambda v, p: isinstance(v, (int, float)) and v >= p.get("min", float("-inf")),
            "max": lambda v, p: isinstance(v, (int, float)) and v <= p.get("max", float("inf")),
            "minLength": lambda v, p: isinstance(v, str) and len(v) >= p.get("minLength", 0),
            "maxLength": lambda v, p: isinstance(v, str) and len(v) <= p.get("maxLength", float("inf")),
            "pattern": lambda v, p: isinstance(v, str) and bool(re.match(p.get("pattern", ""), v)),
            "required": lambda v, p: p.get("required", False) is False or v is not None
        }
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Load configuration data from disk
            self._load_config_data()
            
            # Initialize default schemas and templates
            self._initialize_default_schemas()
            self._initialize_default_templates()
            
            logger.info("Plugin configuration manager initialized")
            self._enabled = True
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize plugin configuration manager: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        try:
            # Save configuration data to disk
            self._save_config_data()
            
            logger.info("Plugin configuration manager shut down")
            self._enabled = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to shut down plugin configuration manager: {str(e)}")
            return False
    
    def _load_config_data(self) -> None:
        """
        Load configuration data from disk.
        """
        schemas_file = os.path.join(self._config_dir, "config_schemas.json")
        templates_file = os.path.join(self._config_dir, "config_templates.json")
        history_file = os.path.join(self._config_dir, "config_history.json")
        presets_file = os.path.join(self._config_dir, "config_presets.json")
        versions_file = os.path.join(self._config_dir, "config_versions.json")
        
        try:
            if os.path.exists(schemas_file):
                with open(schemas_file, "r") as f:
                    self._config_schemas = json.load(f)
            
            if os.path.exists(templates_file):
                with open(templates_file, "r") as f:
                    self._config_templates = json.load(f)
            
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    self._config_history = json.load(f)
            
            if os.path.exists(presets_file):
                with open(presets_file, "r") as f:
                    self._config_presets = json.load(f)
            
            if os.path.exists(versions_file):
                with open(versions_file, "r") as f:
                    self._config_versions = json.load(f)
            
            logger.info("Loaded configuration data from disk")
        
        except Exception as e:
            logger.warning(f"Failed to load configuration data: {str(e)}")
    
    def _save_config_data(self) -> None:
        """
        Save configuration data to disk.
        """
        schemas_file = os.path.join(self._config_dir, "config_schemas.json")
        templates_file = os.path.join(self._config_dir, "config_templates.json")
        history_file = os.path.join(self._config_dir, "config_history.json")
        presets_file = os.path.join(self._config_dir, "config_presets.json")
        versions_file = os.path.join(self._config_dir, "config_versions.json")
        
        try:
            with open(schemas_file, "w") as f:
                json.dump(self._config_schemas, f, indent=2)
            
            with open(templates_file, "w") as f:
                json.dump(self._config_templates, f, indent=2)
            
            with open(history_file, "w") as f:
                json.dump(self._config_history, f, indent=2)
            
            with open(presets_file, "w") as f:
                json.dump(self._config_presets, f, indent=2)
            
            with open(versions_file, "w") as f:
                json.dump(self._config_versions, f, indent=2)
            
            logger.info("Saved configuration data to disk")
        
        except Exception as e:
            logger.warning(f"Failed to save configuration data: {str(e)}")
    
    def _initialize_default_schemas(self) -> None:
        """
        Initialize default configuration schemas.
        """
        # Default schema for logging plugins
        if "advanced_logging" not in self._config_schemas:
            self._config_schemas["advanced_logging"] = {
                "type": "object",
                "properties": {
                    "log_level": {
                        "type": "string",
                        "enum": ["debug", "info", "warning", "error", "critical"],
                        "default": "info",
                        "description": "Logging level"
                    },
                    "log_dir": {
                        "type": "string",
                        "default": "logs",
                        "description": "Directory for log files"
                    },
                    "log_format": {
                        "type": "string",
                        "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        "description": "Format string for log messages"
                    },
                    "max_log_entries": {
                        "type": "integer",
                        "default": 1000,
                        "min": 10,
                        "max": 100000,
                        "description": "Maximum number of log entries to keep in memory"
                    }
                }
            }
        
        # Default schema for notification plugins
        if "notifications" not in self._config_schemas:
            self._config_schemas["notifications"] = {
                "type": "object",
                "properties": {
                    "notification_dir": {
                        "type": "string",
                        "default": "notifications",
                        "description": "Directory for notification files"
                    },
                    "smtp_server": {
                        "type": "string",
                        "description": "SMTP server for email notifications"
                    },
                    "smtp_port": {
                        "type": "integer",
                        "default": 587,
                        "description": "SMTP port for email notifications"
                    },
                    "smtp_username": {
                        "type": "string",
                        "description": "SMTP username for email notifications"
                    },
                    "smtp_password": {
                        "type": "string",
                        "sensitive": True,
                        "description": "SMTP password for email notifications"
                    },
                    "email_from": {
                        "type": "string",
                        "description": "From address for email notifications"
                    },
                    "email_to": {
                        "type": "string",
                        "description": "Default recipient for email notifications"
                    },
                    "webhook_url": {
                        "type": "string",
                        "description": "Webhook URL for webhook notifications"
                    },
                    "slack_webhook_url": {
                        "type": "string",
                        "description": "Slack webhook URL for Slack notifications"
                    }
                }
            }
        
        # Default schema for dashboard plugins
        if "plugin_dashboard" not in self._config_schemas:
            self._config_schemas["plugin_dashboard"] = {
                "type": "object",
                "properties": {
                    "theme": {
                        "type": "string",
                        "enum": ["light", "dark", "auto"],
                        "default": "light",
                        "description": "Dashboard theme"
                    },
                    "refresh_interval": {
                        "type": "integer",
                        "default": 60000,
                        "min": 5000,
                        "max": 3600000,
                        "description": "Auto-refresh interval in milliseconds"
                    },
                    "show_disabled_plugins": {
                        "type": "boolean",
                        "default": true,
                        "description": "Whether to show disabled plugins in the dashboard"
                    },
                    "show_system_plugins": {
                        "type": "boolean",
                        "default": true,
                        "description": "Whether to show system plugins in the dashboard"
                    }
                }
            }
        
        logger.info("Initialized default configuration schemas")
    
    def _initialize_default_templates(self) -> None:
        """
        Initialize default configuration templates.
        """
        # Basic template for all plugins
        if "basic" not in self._config_templates:
            self._config_templates["basic"] = {
                "description": "Basic template for all plugins",
                "config": {}
            }
        
        # Debug template for development
        if "debug" not in self._config_templates:
            self._config_templates["debug"] = {
                "description": "Debug template with verbose logging",
                "config": {
                    "log_level": "debug"
                }
            }
        
        # Production template for deployment
        if "production" not in self._config_templates:
            self._config_templates["production"] = {
                "description": "Production template with minimal logging",
                "config": {
                    "log_level": "warning"
                }
            }
        
        logger.info("Initialized default configuration templates")
    
    #
    # Public API
    #
    
    def register_config_schema(self, plugin_name: str, schema: Dict[str, Any]) -> bool:
        """
        Register a configuration schema for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            schema (Dict[str, Any]): The configuration schema.
            
        Returns:
            bool: True if the schema was registered, False otherwise.
        """
        # Validate the schema (basic checks)
        if not isinstance(schema, dict) or "properties" not in schema:
            logger.warning(f"Invalid schema for plugin {plugin_name}")
            return False
        
        # Store the schema
        self._config_schemas[plugin_name] = schema
        
        logger.info(f"Registered configuration schema for plugin: {plugin_name}")
        return True
    
    def get_config_schema(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration schema for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            
        Returns:
            Optional[Dict[str, Any]]: The configuration schema, or None if not found.
        """
        return self._config_schemas.get(plugin_name)
    
    def create_config_template(self, template_name: str, config: Dict[str, Any], description: str = "") -> bool:
        """
        Create a configuration template.
        
        Args:
            template_name (str): The name of the template.
            config (Dict[str, Any]): The template configuration.
            description (str): A description of the template.
            
        Returns:
            bool: True if the template was created, False otherwise.
        """
        self._config_templates[template_name] = {
            "description": description,
            "config": config,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created configuration template: {template_name}")
        return True
    
    def get_config_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a configuration template.
        
        Args:
            template_name (str): The name of the template.
            
        Returns:
            Optional[Dict[str, Any]]: The template, or None if not found.
        """
        template = self._config_templates.get(template_name)
        if template:
            return template.get("config", {})
        return None
    
    def apply_config_template(self, plugin_name: str, template_name: str) -> bool:
        """
        Apply a configuration template to a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            template_name (str): The name of the template to apply.
            
        Returns:
            bool: True if the template was applied, False otherwise.
        """
        # Get the plugin
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin {plugin_name} not found")
            return False
        
        # Get the template
        template_config = self.get_config_template(template_name)
        if not template_config:
            logger.warning(f"Template {template_name} not found")
            return False
        
        # Get the current config
        current_config = plugin_manager.get_plugin_config(plugin_name) or {}
        
        # Merge the template config with the current config
        new_config = {**current_config, **template_config}
        
        # Apply the new config
        result = plugin_manager.configure_plugin(plugin_name, new_config)
        
        if result:
            # Record the change in history
            self._record_config_change(plugin_name, current_config, new_config, f"Applied template: {template_name}")
            logger.info(f"Applied configuration template {template_name} to plugin {plugin_name}")
        
        return result
    
    def create_config_preset(self, preset_name: str, configs: Dict[str, Dict[str, Any]], description: str = "") -> bool:
        """
        Create a configuration preset for multiple plugins.
        
        Args:
            preset_name (str): The name of the preset.
            configs (Dict[str, Dict[str, Any]]): Dictionary of plugin names to configurations.
            description (str): A description of the preset.
            
        Returns:
            bool: True if the preset was created, False otherwise.
        """
        self._config_presets[preset_name] = {
            "description": description,
            "configs": configs,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created configuration preset: {preset_name}")
        return True
    
    def apply_config_preset(self, preset_name: str) -> Dict[str, bool]:
        """
        Apply a configuration preset to multiple plugins.
        
        Args:
            preset_name (str): The name of the preset to apply.
            
        Returns:
            Dict[str, bool]: Dictionary of plugin names to success/failure status.
        """
        results = {}
        
        # Get the preset
        preset = self._config_presets.get(preset_name)
        if not preset:
            logger.warning(f"Preset {preset_name} not found")
            return results
        
        # Apply the preset to each plugin
        for plugin_name, config in preset["configs"].items():
            # Get the plugin
            plugin = plugin_manager.get_plugin(plugin_name)
            if not plugin:
                logger.warning(f"Plugin {plugin_name} not found, skipping preset application")
                results[plugin_name] = False
                continue
            
            # Get the current config
            current_config = plugin_manager.get_plugin_config(plugin_name) or {}
            
            # Merge the preset config with the current config
            new_config = {**current_config, **config}
            
            # Apply the new config
            result = plugin_manager.configure_plugin(plugin_name, new_config)
            results[plugin_name] = result
            
            if result:
                # Record the change in history
                self._record_config_change(plugin_name, current_config, new_config, f"Applied preset: {preset_name}")
                logger.info(f"Applied configuration preset {preset_name} to plugin {plugin_name}")
            else:
                logger.warning(f"Failed to apply configuration preset {preset_name} to plugin {plugin_name}")
        
        return results
    
    def validate_config(self, plugin_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a configuration against a plugin's schema.
        
        Args:
            plugin_name (str): The name of the plugin.
            config (Dict[str, Any]): The configuration to validate.
            
        Returns:
            Tuple[bool, List[str]]: A tuple of (is_valid, errors).
        """
        # Get the schema
        schema = self._config_schemas.get(plugin_name)
        if not schema:
            logger.warning(f"No schema found for plugin {plugin_name}")
            return True, []  # No schema means no validation
        
        # Validate the config against the schema
        errors = []
        
        # Check required properties
        required = schema.get("required", [])
        for prop in required:
            if prop not in config:
                errors.append(f"Missing required property: {prop}")
        
        # Check property types and constraints
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in config:
                value = config[prop_name]
                
                # Check type
                prop_type = prop_schema.get("type")
                if prop_type:
                    validator = self._validators.get(prop_type)
                    if validator and not validator(value, prop_schema):
                        errors.append(f"Invalid type for {prop_name}: expected {prop_type}")
                
                # Check enum values
                if "enum" in prop_schema and value not in prop_schema["enum"]:
                    errors.append(f"Invalid value for {prop_name}: must be one of {prop_schema['enum']}")
                
                # Check min/max constraints
                if prop_type in ["number", "integer"]:
                    if "min" in prop_schema and value < prop_schema["min"]:
                        errors.append(f"Invalid value for {prop_name}: must be >= {prop_schema['min']}")
                    if "max" in prop_schema and value > prop_schema["max"]:
                        errors.append(f"Invalid value for {prop_name}: must be <= {prop_schema['max']}")
                
                # Check string constraints
                if prop_type == "string":
                    if "minLength" in prop_schema and len(value) < prop_schema["minLength"]:
                        errors.append(f"Invalid length for {prop_name}: must be >= {prop_schema['minLength']}")
                    if "maxLength" in prop_schema and len(value) > prop_schema["maxLength"]:
                        errors.append(f"Invalid length for {prop_name}: must be <= {prop_schema['maxLength']}")
                    if "pattern" in prop_schema and not re.match(prop_schema["pattern"], value):
                        errors.append(f"Invalid format for {prop_name}: must match pattern {prop_schema['pattern']}")
        
        return len(errors) == 0, errors
    
    def get_default_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get the default configuration for a plugin based on its schema.
        
        Args:
            plugin_name (str): The name of the plugin.
            
        Returns:
            Dict[str, Any]: The default configuration.
        """
        # Get the schema
        schema = self._config_schemas.get(plugin_name)
        if not schema:
            return {}  # No schema means no defaults
        
        # Extract default values from the schema
        defaults = {}
        properties = schema.get("properties", {})
        
        for prop_name, prop_schema in properties.items():
            if "default" in prop_schema:
                defaults[prop_name] = prop_schema["default"]
        
        return defaults
    
    def safe_configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate and apply a configuration to a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            config (Dict[str, Any]): The configuration to apply.
            
        Returns:
            Tuple[bool, List[str]]: A tuple of (success, errors).
        """
        # Validate the config
        is_valid, errors = self.validate_config(plugin_name, config)
        if not is_valid:
            logger.warning(f"Invalid configuration for plugin {plugin_name}: {errors}")
            return False, errors
        
        # Get the plugin
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin {plugin_name} not found")
            return False, ["Plugin not found"]
        
        # Get the current config
        current_config = plugin_manager.get_plugin_config(plugin_name) or {}
        
        # Apply the config
        result = plugin_manager.configure_plugin(plugin_name, config)
        
        if result:
            # Record the change in history
            self._record_config_change(plugin_name, current_config, config, "Configuration updated")
            logger.info(f"Configured plugin {plugin_name}")
        else:
            logger.warning(f"Failed to configure plugin {plugin_name}")
            errors.append("Failed to apply configuration")
        
        return result, errors
    
    def _record_config_change(self, plugin_name: str, old_config: Dict[str, Any], new_config: Dict[str, Any], reason: str) -> None:
        """
        Record a configuration change in the history.
        
        Args:
            plugin_name (str): The name of the plugin.
            old_config (Dict[str, Any]): The old configuration.
            new_config (Dict[str, Any]): The new configuration.
            reason (str): The reason for the change.
        """
        # Initialize history for plugin if not exists
        if plugin_name not in self._config_history:
            self._config_history[plugin_name] = []
        
        # Increment version
        version = self._config_versions.get(plugin_name, 0) + 1
        self._config_versions[plugin_name] = version
        
        # Calculate changes
        changes = {}
        
        # Find added or changed properties
        for key, value in new_config.items():
            if key not in old_config:
                changes[key] = {"old": None, "new": value, "action": "added"}
            elif old_config[key] != value:
                changes[key] = {"old": old_config[key], "new": value, "action": "changed"}
        
        # Find removed properties
        for key in old_config:
            if key not in new_config:
                changes[key] = {"old": old_config[key], "new": None, "action": "removed"}
        
        # Record the change
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "reason": reason,
            "environment": self._current_environment,
            "changes": changes
        }
        
        # Add to history
        self._config_history[plugin_name].append(change_record)
        
        logger.debug(f"Recorded configuration change for plugin {plugin_name} (v{version})")
    
    def get_config_history(self, plugin_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the configuration change history for a plugin.
        
        Args:
            plugin_name (str): The name of the plugin.
            limit (int): Maximum number of history entries to return.
            
        Returns:
            List[Dict[str, Any]]: The configuration change history.
        """
        history = self._config_history.get(plugin_name, [])
        return sorted(history, key=lambda x: x["version"], reverse=True)[:limit]
    
    def rollback_config(self, plugin_name: str, version: int) -> bool:
        """
        Rollback a plugin's configuration to a previous version.
        
        Args:
            plugin_name (str): The name of the plugin.
            version (int): The version to rollback to.
            
        Returns:
            bool: True if the rollback was successful, False otherwise.
        """
        # Check if plugin exists
        plugin = plugin_manager.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin {plugin_name} not found")
            return False
        
        # Check if history exists
        history = self._config_history.get(plugin_name, [])
        if not history:
            logger.warning(f"No configuration history for plugin {plugin_name}")
            return False
        
        # Find the target version
        target_version = None
        for change in history:
            if change["version"] == version:
                target_version = change
                break
        
        if not target_version:
            logger.warning(f"Version {version} not found in history for plugin {plugin_name}")
            return False
        
        # Reconstruct the configuration at that version
        reconstructed_config = {}
        
        # Start from the earliest version and apply changes up to the target version
        for change in sorted(history, key=lambda x: x["version"]):
            if change["version"] > version:
                break
            
            for key, value_info in change["changes"].items():
                action = value_info["action"]
                if action == "added" or action == "changed":
                    reconstructed_config[key] = value_info["new"]
                elif action == "removed":
                    if key in reconstructed_config:
                        del reconstructed_config[key]
        
        # Apply the reconstructed configuration
        current_config = plugin_manager.get_plugin_config(plugin_name) or {}
        result = plugin_manager.configure_plugin(plugin_name, reconstructed_config)
        
        if result:
            # Record the rollback
            self._record_config_change(
                plugin_name,
                current_config,
                reconstructed_config,
                f"Rolled back to version {version}"
            )
            logger.info(f"Rolled back configuration for plugin {plugin_name} to version {version}")
        else:
            logger.warning(f"Failed to rollback configuration for plugin {plugin_name}")
        
        return result
    
    def export_config(self, plugin_name: str, format: str = "json") -> Optional[str]:
        """
        Export a plugin's configuration to a specific format.
        
        Args:
            plugin_name (str): The name of the plugin.
            format (str): The export format (json, yaml, env).
            
        Returns:
            Optional[str]: The exported configuration, or None if an error occurred.
        """
        # Get the plugin's configuration
        config = plugin_manager.get_plugin_config(plugin_name)
        if not config:
            logger.warning(f"No configuration found for plugin {plugin_name}")
            return None
        
        try:
            if format.lower() == "json":
                return json.dumps(config, indent=2)
            
            elif format.lower() == "yaml":
                try:
                    import yaml
                    return yaml.dump(config, default_flow_style=False)
                except ImportError:
                    logger.warning("YAML export requires PyYAML package")
                    return json.dumps(config, indent=2)  # Fallback to JSON
            
            elif format.lower() == "env":
                # Convert to environment variables format
                lines = []
                for key, value in config.items():
                    if isinstance(value, (str, int, float, bool)):
                        lines.append(f"{plugin_name.upper()}_{key.upper()}={value}")
                return "\n".join(lines)
            
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {str(e)}")
            return None
    
    def import_config(self, plugin_name: str, config_data: str, format: str = "json") -> bool:
        """
        Import a plugin's configuration from a specific format.
        
        Args:
            plugin_name (str): The name of the plugin.
            config_data (str): The configuration data to import.
            format (str): The import format (json, yaml, env).
            
        Returns:
            bool: True if the import was successful, False otherwise.
        """
        try:
            # Parse the configuration data
            config = None
            
            if format.lower() == "json":
                config = json.loads(config_data)
            
            elif format.lower() == "yaml":
                try:
                    import yaml
                    config = yaml.safe_load(config_data)
                except ImportError:
                    logger.warning("YAML import requires PyYAML package")
                    return False
            
            elif format.lower() == "env":
                # Parse environment variables format
                config = {}
                prefix = f"{plugin_name.upper()}_"
                
                for line in config_data.splitlines():
                    if "=" in line and line.startswith(prefix):
                        key, value = line.split("=", 1)
                        key = key[len(prefix):].lower()
                        
                        # Try to convert value to appropriate type
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                            value = float(value)
                        
                        config[key] = value
            
            else:
                logger.warning(f"Unsupported import format: {format}")
                return False
            
            if not config:
                logger.warning("Failed to parse configuration data")
                return False
            
            # Apply the configuration
            success, errors = self.safe_configure_plugin(plugin_name, config)
            
            if not success:
                logger.warning(f"Failed to apply imported configuration: {errors}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {str(e)}")
            return False
    
    def set_environment(self, environment: str) -> bool:
        """
        Set the current environment.
        
        Args:
            environment (str): The environment to set.
            
        Returns:
            bool: True if the environment was set, False otherwise.
        """
        if environment not in self._environments:
            logger.warning(f"Unknown environment: {environment}")
            return False
        
        self._current_environment = environment
        logger.info(f"Set environment to: {environment}")
        
        return True 