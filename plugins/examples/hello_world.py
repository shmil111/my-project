"""
A simple Hello World plugin example.
"""
import logging
from myproject.plugins.core.base import BasePlugin

logger = logging.getLogger(__name__)


class HelloWorldPlugin(BasePlugin):
    """
    A simple Hello World plugin that logs a greeting on initialization
    and a farewell on shutdown.
    """
    
    @property
    def name(self) -> str:
        return "hello_world"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A simple Hello World plugin example"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        logger.info("Hello, World! The Hello World plugin has been initialized.")
        self._enabled = True
        return True
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        logger.info("Goodbye, World! The Hello World plugin has been shut down.")
        self._enabled = False
        return True
    
    def say_hello(self, name: str) -> str:
        """
        Say hello to someone.
        
        Args:
            name (str): The name of the person to greet.
            
        Returns:
            str: The greeting message.
        """
        message = f"Hello, {name}! This is the Hello World plugin."
        logger.info(message)
        return message 