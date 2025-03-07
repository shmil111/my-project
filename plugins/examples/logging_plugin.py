"""
A logging plugin that enhances the application's logging capabilities.
"""
import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from myproject.plugins.core.base import BasePlugin

logger = logging.getLogger(__name__)


class LoggingPlugin(BasePlugin):
    """
    A plugin that enhances the application's logging capabilities by
    adding file logging, log rotation, and structured logging.
    """
    
    @property
    def name(self) -> str:
        return "advanced_logging"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Enhances the application's logging capabilities"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        super().__init__()
        self._log_file = None
        self._log_level = logging.INFO
        self._log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self._log_dir = "logs"
        self._file_handler = None
        self._log_entries = []
        self._max_log_entries = 1000
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Apply configuration
            config = self.get_config()
            if "log_level" in config:
                self._log_level = self._parse_log_level(config["log_level"])
            if "log_format" in config:
                self._log_format = config["log_format"]
            if "log_dir" in config:
                self._log_dir = config["log_dir"]
            if "max_log_entries" in config:
                self._max_log_entries = int(config["max_log_entries"])
            
            # Ensure log directory exists
            os.makedirs(self._log_dir, exist_ok=True)
            
            # Set up file logging
            log_filename = self._get_log_filename()
            self._log_file = os.path.join(self._log_dir, log_filename)
            
            # Create file handler
            self._file_handler = logging.FileHandler(self._log_file)
            self._file_handler.setLevel(self._log_level)
            formatter = logging.Formatter(self._log_format)
            self._file_handler.setFormatter(formatter)
            
            # Add file handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(self._file_handler)
            
            logger.info(f"Logging plugin initialized. Logs will be written to {self._log_file}")
            self._enabled = True
            
            # Register our custom handlers
            self._register_handlers()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize logging plugin: {str(e)}")
            return False
    
    def _register_handlers(self) -> None:
        """
        Register custom log handlers.
        """
        # Create a custom handler to capture logs in memory
        class MemoryHandler(logging.Handler):
            def __init__(self, plugin):
                super().__init__()
                self.plugin = plugin
            
            def emit(self, record):
                self.plugin.add_log_entry(record)
        
        # Add the memory handler to the root logger
        memory_handler = MemoryHandler(self)
        memory_handler.setLevel(self._log_level)
        root_logger = logging.getLogger()
        root_logger.addHandler(memory_handler)
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        try:
            # Remove file handler from root logger
            if self._file_handler:
                root_logger = logging.getLogger()
                root_logger.removeHandler(self._file_handler)
                self._file_handler.close()
            
            logger.info("Logging plugin shut down.")
            self._enabled = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to shutdown logging plugin: {str(e)}")
            return False
    
    def _parse_log_level(self, level_str: str) -> int:
        """
        Parse a log level string to a logging level.
        
        Args:
            level_str (str): The log level string.
            
        Returns:
            int: The logging level.
        """
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        return level_map.get(level_str.lower(), logging.INFO)
    
    def _get_log_filename(self) -> str:
        """
        Get a log filename based on the current date.
        
        Returns:
            str: The log filename.
        """
        now = datetime.now()
        return f"myproject_{now.strftime('%Y-%m-%d')}.log"
    
    def add_log_entry(self, record: logging.LogRecord) -> None:
        """
        Add a log entry to the in-memory log buffer.
        
        Args:
            record (logging.LogRecord): The log record to add.
        """
        entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if available
        if record.exc_info:
            import traceback
            entry["exception"] = "".join(traceback.format_exception(*record.exc_info))
        
        # Add to in-memory buffer with rotation
        self._log_entries.append(entry)
        if len(self._log_entries) > self._max_log_entries:
            self._log_entries.pop(0)
    
    def get_logs(self, 
                level: Optional[str] = None, 
                limit: int = 100, 
                start_time: Optional[str] = None, 
                end_time: Optional[str] = None
               ) -> List[Dict[str, Any]]:
        """
        Get logs from the in-memory log buffer, filtered by criteria.
        
        Args:
            level (Optional[str]): Filter by log level.
            limit (int): Maximum number of logs to return.
            start_time (Optional[str]): Filter logs after this ISO timestamp.
            end_time (Optional[str]): Filter logs before this ISO timestamp.
            
        Returns:
            List[Dict[str, Any]]: The filtered log entries.
        """
        result = self._log_entries.copy()
        
        # Apply filters
        if level:
            result = [entry for entry in result if entry["level"].lower() == level.lower()]
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            result = [
                entry for entry in result 
                if datetime.fromisoformat(entry["timestamp"]) >= start_dt
            ]
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            result = [
                entry for entry in result 
                if datetime.fromisoformat(entry["timestamp"]) <= end_dt
            ]
        
        # Apply limit
        return result[-limit:]
    
    def export_logs(self, format: str = "json", path: Optional[str] = None) -> str:
        """
        Export logs to a file.
        
        Args:
            format (str): The export format (json, csv, or text).
            path (Optional[str]): The path to write the exported logs to.
                If None, a default path will be used.
                
        Returns:
            str: The path to the exported logs.
        """
        if not path:
            now = datetime.now()
            filename = f"logs_export_{now.strftime('%Y%m%d_%H%M%S')}.{format}"
            path = os.path.join(self._log_dir, filename)
        
        try:
            if format.lower() == "json":
                with open(path, "w") as f:
                    json.dump(self._log_entries, f, indent=2)
            
            elif format.lower() == "csv":
                import csv
                with open(path, "w", newline="") as f:
                    fieldnames = [
                        "timestamp", "level", "logger", "message", 
                        "module", "function", "line"
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for entry in self._log_entries:
                        # Filter out keys not in fieldnames
                        row = {k: v for k, v in entry.items() if k in fieldnames}
                        writer.writerow(row)
            
            elif format.lower() == "text":
                with open(path, "w") as f:
                    for entry in self._log_entries:
                        f.write(
                            f"{entry['timestamp']} [{entry['level']}] "
                            f"{entry['logger']}: {entry['message']}\n"
                        )
                        if "exception" in entry:
                            f.write(f"{entry['exception']}\n")
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Logs exported to {path}")
            return path
        
        except Exception as e:
            logger.error(f"Failed to export logs: {str(e)}")
            raise 