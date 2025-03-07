"""
A notification plugin that provides various notification capabilities.
"""
import logging
import smtplib
import time
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union, Callable

from myproject.plugins.core.base import BasePlugin
from myproject.plugins.core.manager import plugin_manager

logger = logging.getLogger(__name__)


class NotificationPlugin(BasePlugin):
    """
    A plugin that provides notification capabilities like email, 
    webhook notifications, and in-app notifications.
    
    This plugin depends on the advanced_logging plugin for logging
    notification events.
    """
    
    @property
    def name(self) -> str:
        return "notifications"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides notification capabilities"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    @property
    def dependencies(self) -> List[str]:
        return ["advanced_logging"]
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        super().__init__()
        self._notification_handlers = {}
        self._notifications = []
        self._max_notifications = 100
        self._handlers = {
            "email": self._send_email_notification,
            "webhook": self._send_webhook_notification,
            "slack": self._send_slack_notification,
            "console": self._send_console_notification,
            "in_app": self._store_in_app_notification
        }
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Apply configuration
            config = self.get_config()
            
            # Create notification directory if specified
            notification_dir = config.get("notification_dir", "notifications")
            if not os.path.exists(notification_dir):
                os.makedirs(notification_dir, exist_ok=True)
            
            # Check if the logging plugin is available
            if not plugin_manager.get_plugin("advanced_logging"):
                logger.warning(
                    "The advanced_logging plugin is not available. "
                    "Notification events will be logged to the console only."
                )
            
            # Register default notification handlers
            for handler_name, handler_func in self._handlers.items():
                self.register_notification_handler(handler_name, handler_func)
            
            logger.info("Notification plugin initialized")
            self._enabled = True
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize notification plugin: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        try:
            # Clear handlers
            self._notification_handlers.clear()
            
            logger.info("Notification plugin shut down")
            self._enabled = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to shutdown notification plugin: {str(e)}")
            return False
    
    def register_notification_handler(
        self, name: str, handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a notification handler.
        
        Args:
            name (str): The name of the handler.
            handler (Callable[[Dict[str, Any]], bool]): The handler function.
        """
        if name in self._notification_handlers:
            logger.warning(f"Notification handler {name} already registered. Overwriting.")
        
        self._notification_handlers[name] = handler
        logger.info(f"Registered notification handler: {name}")
    
    def unregister_notification_handler(self, name: str) -> bool:
        """
        Unregister a notification handler.
        
        Args:
            name (str): The name of the handler to unregister.
            
        Returns:
            bool: True if the handler was unregistered, False otherwise.
        """
        if name not in self._notification_handlers:
            logger.warning(f"Notification handler {name} not registered")
            return False
        
        del self._notification_handlers[name]
        logger.info(f"Unregistered notification handler: {name}")
        return True
    
    def send_notification(
        self, 
        message: str, 
        subject: str = "Notification",
        level: str = "info",
        channels: List[str] = None,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send a notification via all specified channels.
        
        Args:
            message (str): The notification message.
            subject (str): The notification subject.
            level (str): The notification level (info, warning, error, critical).
            channels (List[str]): The channels to send the notification to.
                If None, use all available channels.
            **kwargs: Additional arguments to pass to the notification handlers.
            
        Returns:
            Dict[str, bool]: A dictionary of channel names to success/failure status.
        """
        if not self.enabled:
            logger.warning("Notification plugin is not enabled")
            return {channel: False for channel in (channels or self._notification_handlers.keys())}
        
        # Create notification data
        notification_data = {
            "id": str(int(time.time() * 1000)),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "subject": subject,
            "message": message,
            "level": level,
            **kwargs
        }
        
        # Log the notification
        log_message = f"Notification [{level}]: {subject} - {message}"
        if level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        elif level == "critical":
            logger.critical(log_message)
        else:
            logger.info(log_message)
        
        # Store the notification in memory
        self._store_notification(notification_data)
        
        # If no channels specified, use all available handlers
        if not channels:
            channels = list(self._notification_handlers.keys())
        
        # Send notification through each channel
        results = {}
        for channel in channels:
            if channel in self._notification_handlers:
                try:
                    handler = self._notification_handlers[channel]
                    results[channel] = handler(notification_data)
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel}: {str(e)}")
                    results[channel] = False
            else:
                logger.warning(f"Notification channel {channel} not registered")
                results[channel] = False
        
        return results
    
    def _store_notification(self, notification_data: Dict[str, Any]) -> None:
        """
        Store a notification in the in-memory list.
        
        Args:
            notification_data (Dict[str, Any]): The notification data to store.
        """
        self._notifications.append(notification_data)
        if len(self._notifications) > self._max_notifications:
            self._notifications.pop(0)
    
    def get_notifications(
        self,
        level: Optional[str] = None,
        limit: int = 10,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notifications from the in-memory list, filtered by criteria.
        
        Args:
            level (Optional[str]): Filter by notification level.
            limit (int): Maximum number of notifications to return.
            start_time (Optional[str]): Filter notifications after this time.
            end_time (Optional[str]): Filter notifications before this time.
            
        Returns:
            List[Dict[str, Any]]: The filtered notifications.
        """
        result = self._notifications.copy()
        
        # Apply filters
        if level:
            result = [n for n in result if n["level"] == level]
        
        if start_time:
            result = [n for n in result if n["timestamp"] >= start_time]
        
        if end_time:
            result = [n for n in result if n["timestamp"] <= end_time]
        
        # Apply limit
        return result[-limit:]
    
    def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send an email notification.
        
        Args:
            notification_data (Dict[str, Any]): The notification data.
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise.
        """
        config = self.get_config()
        
        # Check if email configuration is available
        if not all(key in config for key in ["smtp_server", "smtp_port", "smtp_username", "smtp_password"]):
            logger.warning("Email notification configuration incomplete")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = config.get("email_from", config["smtp_username"])
            msg["To"] = notification_data.get("email_to", config.get("email_to", "admin@example.com"))
            msg["Subject"] = notification_data["subject"]
            
            # Add body
            body = f"""
            <html>
            <body>
                <h2>{notification_data['subject']}</h2>
                <p style="font-size: 16px;">{notification_data['message']}</p>
                <p style="color: #666;">Sent at: {notification_data['timestamp']}</p>
                <p style="color: #666;">Level: {notification_data['level']}</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, "html"))
            
            # Connect to server
            server = smtplib.SMTP(config["smtp_server"], int(config["smtp_port"]))
            server.starttls()
            server.login(config["smtp_username"], config["smtp_password"])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {msg['To']}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def _send_webhook_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send a webhook notification.
        
        Args:
            notification_data (Dict[str, Any]): The notification data.
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise.
        """
        config = self.get_config()
        
        # Check if webhook configuration is available
        if "webhook_url" not in config:
            logger.warning("Webhook notification configuration incomplete")
            return False
        
        try:
            import requests
            
            # Prepare payload
            payload = {
                "id": notification_data["id"],
                "timestamp": notification_data["timestamp"],
                "subject": notification_data["subject"],
                "message": notification_data["message"],
                "level": notification_data["level"]
            }
            
            # Send webhook
            response = requests.post(
                config["webhook_url"],
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info(f"Webhook notification sent to {config['webhook_url']}")
                return True
            else:
                logger.warning(
                    f"Webhook notification failed with status code {response.status_code}: "
                    f"{response.text}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            return False
    
    def _send_slack_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send a Slack notification.
        
        Args:
            notification_data (Dict[str, Any]): The notification data.
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise.
        """
        config = self.get_config()
        
        # Check if Slack configuration is available
        if "slack_webhook_url" not in config:
            logger.warning("Slack notification configuration incomplete")
            return False
        
        try:
            import requests
            
            # Get emoji based on level
            emoji_map = {
                "info": ":information_source:",
                "warning": ":warning:",
                "error": ":x:",
                "critical": ":fire:"
            }
            emoji = emoji_map.get(notification_data["level"], ":bell:")
            
            # Prepare payload
            payload = {
                "text": f"{emoji} *{notification_data['subject']}*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} {notification_data['subject']}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": notification_data["message"]
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Level:* {notification_data['level']} | *Time:* {notification_data['timestamp']}"
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                config["slack_webhook_url"],
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code < 400:
                logger.info("Slack notification sent")
                return True
            else:
                logger.warning(
                    f"Slack notification failed with status code {response.status_code}: "
                    f"{response.text}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False
    
    def _send_console_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send a console notification (print to console).
        
        Args:
            notification_data (Dict[str, Any]): The notification data.
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise.
        """
        try:
            level_formatting = {
                "info": "\033[94m",      # Blue
                "warning": "\033[93m",   # Yellow
                "error": "\033[91m",     # Red
                "critical": "\033[91m\033[1m"  # Bold Red
            }
            reset = "\033[0m"
            
            level = notification_data["level"]
            formatting = level_formatting.get(level, "")
            
            print(f"\n{formatting}[{level.upper()}] {notification_data['subject']}{reset}")
            print(f"Time: {notification_data['timestamp']}")
            print(f"Message: {notification_data['message']}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send console notification: {str(e)}")
            return False
    
    def _store_in_app_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Store an in-app notification.
        
        Args:
            notification_data (Dict[str, Any]): The notification data.
            
        Returns:
            bool: True if the notification was stored successfully, False otherwise.
        """
        try:
            # Notification is already stored in _store_notification
            # This handler is just a marker that the notification was processed for in-app display
            return True
        
        except Exception as e:
            logger.error(f"Failed to store in-app notification: {str(e)}")
            return False 