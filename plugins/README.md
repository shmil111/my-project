# MyProject Plugin System

The plugin system allows you to extend the functionality of MyProject without modifying the core code. Plugins can add new features, modify existing behavior, or integrate with external systems.

## Table of Contents

- [Plugin Directory Structure](#plugin-directory-structure)
- [Using Plugins](#using-plugins)
- [Creating Plugins](#creating-plugins)
- [Plugin Dependencies](#plugin-dependencies)
- [Plugin Configuration](#plugin-configuration)
- [Example Plugins](#example-plugins)

## Plugin Directory Structure

The plugin system uses the following directory structure:

```
myproject/
└── plugins/
    ├── core/               # Core plugin system files
    │   ├── __init__.py
    │   ├── base.py         # Base plugin interfaces and classes
    │   └── manager.py      # Plugin manager
    ├── examples/           # Example plugins
    │   ├── __init__.py
    │   ├── hello_world.py
    │   ├── logging_plugin.py
    │   └── notification_plugin.py
    ├── custom/             # User-created plugins
    │   └── ...
    ├── __init__.py
    ├── plugin_loader.py    # Plugin loader utilities
    └── README.md           # This file
```

Plugins can be placed in either the `examples` or `custom` directories. The `custom` directory is recommended for user-created plugins, as it won't be overwritten by updates.

## Using Plugins

To use the plugin system in your code, import the plugin loader and initialize the system:

```python
from myproject.plugins import plugin_loader

# Initialize the plugin system
plugin_loader.initialize_plugin_system()

# Discover and load plugins
plugin_results = plugin_loader.discover_and_load_plugins()

# Get a specific plugin
my_plugin = plugin_loader.get_plugin("plugin_name")
if my_plugin:
    # Use the plugin
    my_plugin.do_something()

# Configure a plugin
plugin_loader.configure_plugin("plugin_name", {
    "option1": "value1",
    "option2": "value2"
})

# Enable or disable a plugin
plugin_loader.enable_plugin("plugin_name")
plugin_loader.disable_plugin("plugin_name")

# Check if a plugin is enabled
if plugin_loader.is_plugin_enabled("plugin_name"):
    # Do something

# Unload a plugin
plugin_loader.unload_plugin("plugin_name")

# Unload all plugins
plugin_loader.unload_all_plugins()
```

## Creating Plugins

To create a plugin, create a new Python file in the `custom` directory that defines a class inheriting from `BasePlugin`:

```python
from myproject.plugins.core.base import BasePlugin

class MyPlugin(BasePlugin):
    """
    My custom plugin that does something useful.
    """
    
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A plugin that does something useful"
    
    @property
    def author(self) -> str:
        return "Your Name"
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        # Do initialization here
        return True
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        # Do cleanup here
        return True
    
    # Add your custom methods here
    def do_something(self) -> str:
        return "I did something!"
```

## Plugin Dependencies

Plugins can depend on other plugins by specifying a list of plugin names in the `dependencies` property:

```python
@property
def dependencies(self) -> List[str]:
    return ["other_plugin", "another_plugin"]
```

The plugin system will ensure that dependencies are loaded first. If a dependency can't be loaded, the plugin will not be loaded either.

## Plugin Configuration

Plugins can be configured using the `configure_plugin` function:

```python
plugin_loader.configure_plugin("plugin_name", {
    "option1": "value1",
    "option2": "value2"
})
```

Inside your plugin, you can access the configuration using the `get_config` method:

```python
def initialize(self) -> bool:
    config = self.get_config()
    option1 = config.get("option1", "default_value")
    option2 = config.get("option2", "default_value")
    # Use options
    return True
```

## Example Plugins

The plugin system comes with several example plugins:

### Hello World Plugin

A simple plugin that demonstrates the basic structure of a plugin.

```python
from myproject.plugins.core.base import BasePlugin

class HelloWorldPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "hello_world"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A simple Hello World plugin example"
    
    def initialize(self) -> bool:
        print("Hello, World! The Hello World plugin has been initialized.")
        return True
    
    def shutdown(self) -> bool:
        print("Goodbye, World! The Hello World plugin has been shut down.")
        return True
    
    def say_hello(self, name: str) -> str:
        return f"Hello, {name}! This is the Hello World plugin."
```

### Advanced Logging Plugin

A plugin that enhances the application's logging capabilities by adding file logging, log rotation, and structured logging.

### Notification Plugin

A plugin that provides notification capabilities like email, webhook notifications, and in-app notifications. This plugin depends on the Advanced Logging plugin.

## Plugin API Reference

### BasePlugin

The `BasePlugin` class is the base class for all plugins. It implements common functionality and defines the required interface.

#### Properties

- `name`: The name of the plugin. Must be unique.
- `version`: The version of the plugin.
- `description`: A brief description of the plugin.
- `author`: The author of the plugin. Defaults to "Unknown".
- `dependencies`: A list of plugin names that this plugin depends on. Defaults to an empty list.
- `enabled`: Whether the plugin is enabled. Defaults to False until `initialize()` is called.

#### Methods

- `initialize()`: Initialize the plugin. Called when the plugin is loaded.
- `shutdown()`: Shutdown the plugin. Called when the plugin is unloaded.
- `get_config()`: Get the plugin's configuration.
- `set_config(config)`: Set the plugin's configuration.

### Plugin Manager

The `plugin_manager` is a global instance of the `PluginManager` class that manages the plugin system.

#### Methods

- `register_plugin_directory(directory)`: Register a directory to search for plugins.
- `discover_plugins()`: Discover all available plugins in the registered directories.
- `load_plugin(plugin_class)`: Load a plugin.
- `load_plugins(plugin_classes)`: Load multiple plugins.
- `unload_plugin(plugin_name)`: Unload a plugin.
- `unload_all_plugins()`: Unload all plugins.
- `get_plugin(plugin_name)`: Get a plugin instance by name.
- `get_all_plugins()`: Get all loaded plugin instances.
- `enable_plugin(plugin_name)`: Enable a plugin.
- `disable_plugin(plugin_name)`: Disable a plugin.
- `is_plugin_enabled(plugin_name)`: Check if a plugin is enabled.
- `configure_plugin(plugin_name, config)`: Configure a plugin.
- `get_plugin_config(plugin_name)`: Get a plugin's configuration.

### Plugin Loader

The `plugin_loader` module provides simplified functions for working with the plugin system.

#### Functions

- `initialize_plugin_system(plugin_directories=None)`: Initialize the plugin system.
- `discover_and_load_plugins(auto_enable=True, excluded_plugins=None)`: Discover and load all available plugins.
- `load_plugin_from_file(file_path, auto_enable=True)`: Load a plugin from a file path.
- `configure_plugin(plugin_name, config)`: Configure a plugin.
- `enable_plugin(plugin_name)`: Enable a plugin.
- `disable_plugin(plugin_name)`: Disable a plugin.
- `get_plugin(plugin_name)`: Get a plugin instance by name.
- `get_all_plugins()`: Get all loaded plugin instances.
- `unload_plugin(plugin_name)`: Unload a plugin.
- `unload_all_plugins()`: Unload all plugins.
- `is_plugin_enabled(plugin_name)`: Check if a plugin is enabled. 