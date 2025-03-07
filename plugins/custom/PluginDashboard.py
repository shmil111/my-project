"""
Plugin Dashboard - A plugin that provides a web dashboard for managing plugins.
"""
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from myproject.plugins.core.base import BasePlugin
from myproject.plugins.core.manager import plugin_manager

logger = logging.getLogger(__name__)


class PluginDashboardPlugin(BasePlugin):
    """
    A plugin that provides a web dashboard for managing plugins.
    This allows users to view, enable/disable, configure, and monitor plugins
    through a web interface.
    """
    
    @property
    def name(self) -> str:
        return "plugin_dashboard"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides a web dashboard for managing plugins"
    
    @property
    def author(self) -> str:
        return "MyProject Team"
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        super().__init__()
        self._blueprint = None
        self._template_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates"
        )
        
        # Create template directory if it doesn't exist
        os.makedirs(self._template_folder, exist_ok=True)
        
        # Create basic template file if it doesn't exist
        self._create_default_templates()
        
        # Plugin activity log
        self._activity_log = []
        self._max_log_entries = 100
    
    def _create_default_templates(self):
        """
        Create default template files if they don't exist.
        """
        dashboard_template = os.path.join(self._template_folder, "plugin_dashboard.html")
        if not os.path.exists(dashboard_template):
            with open(dashboard_template, "w") as f:
                f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plugin Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .plugin-card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .plugin-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .plugin-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #2c3e50;
        }
        .plugin-version {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        .plugin-status {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status-enabled {
            background-color: #2ecc71;
            color: white;
        }
        .status-disabled {
            background-color: #e74c3c;
            color: white;
        }
        .plugin-description {
            margin-bottom: 15px;
            color: #555;
        }
        .plugin-author {
            font-style: italic;
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        .plugin-dependencies {
            margin-top: 10px;
            font-size: 0.9rem;
        }
        .dependency-tag {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        .plugin-actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.3s;
        }
        .btn-enable {
            background-color: #2ecc71;
            color: white;
        }
        .btn-disable {
            background-color: #e74c3c;
            color: white;
        }
        .btn-config {
            background-color: #3498db;
            color: white;
        }
        .btn:hover {
            opacity: 0.8;
        }
        .config-section {
            margin-top: 15px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #fff;
        }
        .config-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .config-form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group label {
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-control {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .activity-log {
            margin-top: 30px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .log-entry {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-time {
            font-size: 0.8rem;
            color: #7f8c8d;
        }
        .log-message {
            margin-left: 10px;
        }
        .log-info {
            color: #3498db;
        }
        .log-warning {
            color: #f39c12;
        }
        .log-error {
            color: #e74c3c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Plugin Dashboard</h1>
        
        <div id="plugins-container">
            {% for plugin_name, plugin in plugins.items() %}
            <div class="plugin-card">
                <div class="plugin-header">
                    <div class="plugin-title">{{ plugin.name }}</div>
                    <div class="plugin-version">v{{ plugin.version }}</div>
                    <div class="plugin-status {% if plugin.enabled %}status-enabled{% else %}status-disabled{% endif %}">
                        {{ "Enabled" if plugin.enabled else "Disabled" }}
                    </div>
                </div>
                <div class="plugin-description">{{ plugin.description }}</div>
                <div class="plugin-author">By: {{ plugin.author }}</div>
                
                {% if plugin.dependencies %}
                <div class="plugin-dependencies">
                    Dependencies:
                    {% for dependency in plugin.dependencies %}
                    <span class="dependency-tag">{{ dependency }}</span>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="plugin-actions">
                    {% if plugin.enabled %}
                    <form action="/plugins/disable" method="post">
                        <input type="hidden" name="plugin_name" value="{{ plugin.name }}">
                        <button type="submit" class="btn btn-disable">Disable</button>
                    </form>
                    {% else %}
                    <form action="/plugins/enable" method="post">
                        <input type="hidden" name="plugin_name" value="{{ plugin.name }}">
                        <button type="submit" class="btn btn-enable">Enable</button>
                    </form>
                    {% endif %}
                    
                    <button class="btn btn-config" onclick="toggleConfig('{{ plugin.name }}')">Configure</button>
                </div>
                
                <div id="config-{{ plugin.name }}" class="config-section" style="display: none;">
                    <div class="config-title">Configure {{ plugin.name }}</div>
                    <form class="config-form" action="/plugins/configure" method="post">
                        <input type="hidden" name="plugin_name" value="{{ plugin.name }}">
                        
                        {% for key, value in plugin.config.items() %}
                        <div class="form-group">
                            <label for="{{ key }}">{{ key }}</label>
                            <input type="text" class="form-control" id="{{ key }}" name="{{ key }}" value="{{ value }}">
                        </div>
                        {% endfor %}
                        
                        <button type="submit" class="btn btn-config">Save Configuration</button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="activity-log">
            <h2>Activity Log</h2>
            {% for entry in activity_log %}
            <div class="log-entry">
                <span class="log-time">{{ entry.timestamp }}</span>
                <span class="log-message log-{{ entry.level }}">{{ entry.message }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function toggleConfig(pluginName) {
            const configSection = document.getElementById(`config-${pluginName}`);
            if (configSection.style.display === "none") {
                configSection.style.display = "block";
            } else {
                configSection.style.display = "none";
            }
        }
    </script>
</body>
</html>
                """)
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            from flask import current_app
            
            # Create a Blueprint for the plugin dashboard
            self._blueprint = Blueprint(
                "plugin_dashboard",
                __name__,
                template_folder=self._template_folder,
                url_prefix="/plugins"
            )
            
            # Define routes
            self._define_routes()
            
            # Register the blueprint with the Flask app
            if current_app:
                current_app.register_blueprint(self._blueprint)
                logger.info("Plugin dashboard registered at /plugins")
                self._log_activity("Plugin dashboard initialized", "info")
            else:
                logger.warning("No Flask app context available. Dashboard routes won't be accessible.")
                self._log_activity("Failed to register plugin dashboard routes", "warning")
            
            self._enabled = True
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize plugin dashboard: {str(e)}")
            self._log_activity(f"Failed to initialize: {str(e)}", "error")
            return False
    
    def shutdown(self) -> bool:
        """
        Shutdown the plugin.
        
        Returns:
            bool: True if shutdown was successful, False otherwise.
        """
        try:
            # There's no direct way to unregister a blueprint in Flask,
            # but we can log the shutdown
            logger.info("Plugin dashboard shutting down")
            self._log_activity("Plugin dashboard shut down", "info")
            
            self._enabled = False
            return True
        
        except Exception as e:
            logger.error(f"Failed to shut down plugin dashboard: {str(e)}")
            return False
    
    def _define_routes(self):
        """
        Define routes for the plugin dashboard.
        """
        @self._blueprint.route("/", methods=["GET"])
        def dashboard():
            """
            Render the plugin dashboard.
            """
            plugins_data = {}
            
            for name, plugin in plugin_manager.get_all_plugins().items():
                plugins_data[name] = {
                    "name": name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "enabled": plugin.enabled,
                    "dependencies": plugin.dependencies,
                    "config": plugin_manager.get_plugin_config(name) or {}
                }
            
            return render_template(
                "plugin_dashboard.html",
                plugins=plugins_data,
                activity_log=self._activity_log
            )
        
        @self._blueprint.route("/enable", methods=["POST"])
        def enable_plugin():
            """
            Enable a plugin.
            """
            plugin_name = request.form.get("plugin_name")
            
            if not plugin_name:
                self._log_activity("Failed to enable plugin: No plugin name provided", "error")
                return jsonify({"success": False, "message": "No plugin name provided"})
            
            result = plugin_manager.enable_plugin(plugin_name)
            
            if result:
                self._log_activity(f"Enabled plugin: {plugin_name}", "info")
                return redirect(url_for("plugin_dashboard.dashboard"))
            else:
                self._log_activity(f"Failed to enable plugin: {plugin_name}", "error")
                return jsonify({"success": False, "message": f"Failed to enable plugin: {plugin_name}"})
        
        @self._blueprint.route("/disable", methods=["POST"])
        def disable_plugin():
            """
            Disable a plugin.
            """
            plugin_name = request.form.get("plugin_name")
            
            if not plugin_name:
                self._log_activity("Failed to disable plugin: No plugin name provided", "error")
                return jsonify({"success": False, "message": "No plugin name provided"})
            
            # Don't allow disabling the dashboard itself
            if plugin_name == self.name:
                self._log_activity("Cannot disable the plugin dashboard itself", "warning")
                return jsonify({"success": False, "message": "Cannot disable the plugin dashboard itself"})
            
            result = plugin_manager.disable_plugin(plugin_name)
            
            if result:
                self._log_activity(f"Disabled plugin: {plugin_name}", "info")
                return redirect(url_for("plugin_dashboard.dashboard"))
            else:
                self._log_activity(f"Failed to disable plugin: {plugin_name}", "error")
                return jsonify({"success": False, "message": f"Failed to disable plugin: {plugin_name}"})
        
        @self._blueprint.route("/configure", methods=["POST"])
        def configure_plugin():
            """
            Configure a plugin.
            """
            plugin_name = request.form.get("plugin_name")
            
            if not plugin_name:
                self._log_activity("Failed to configure plugin: No plugin name provided", "error")
                return jsonify({"success": False, "message": "No plugin name provided"})
            
            # Extract configuration from form data
            config = {}
            for key, value in request.form.items():
                if key != "plugin_name":
                    config[key] = value
            
            result = plugin_manager.configure_plugin(plugin_name, config)
            
            if result:
                self._log_activity(f"Configured plugin: {plugin_name}", "info")
                return redirect(url_for("plugin_dashboard.dashboard"))
            else:
                self._log_activity(f"Failed to configure plugin: {plugin_name}", "error")
                return jsonify({"success": False, "message": f"Failed to configure plugin: {plugin_name}"})
        
        @self._blueprint.route("/api/plugins", methods=["GET"])
        def get_plugins():
            """
            Get all plugins as JSON.
            """
            plugins_data = {}
            
            for name, plugin in plugin_manager.get_all_plugins().items():
                plugins_data[name] = {
                    "name": name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "enabled": plugin.enabled,
                    "dependencies": plugin.dependencies,
                    "config": plugin_manager.get_plugin_config(name) or {}
                }
            
            return jsonify(plugins_data)
        
        @self._blueprint.route("/api/log", methods=["GET"])
        def get_activity_log():
            """
            Get the activity log as JSON.
            """
            return jsonify(self._activity_log)
    
    def _log_activity(self, message: str, level: str = "info") -> None:
        """
        Log an activity to the activity log.
        
        Args:
            message (str): The message to log.
            level (str): The log level (info, warning, error).
        """
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "level": level
        }
        
        self._activity_log.append(entry)
        
        # Keep log size limited
        if len(self._activity_log) > self._max_log_entries:
            self._activity_log.pop(0)
        
        # Also log to the application logger
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        else:
            logger.info(message) 