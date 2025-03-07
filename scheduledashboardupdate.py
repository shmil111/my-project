#!/usr/bin/env python3
"""
Scheduler for automating dashboard updates and monitoring tasks.
This script sets up a scheduled task to run the deep_web_monitor.py and 
update_dashboard.py scripts at specified intervals.

Features:
- Flexible scheduling with cron-like syntax
- Email/webhook notifications on errors
- Automatic retry for failed tasks
- Detailed logging of all activities
- Status monitoring of scheduled tasks
- Fault tolerance with circuit breaker pattern
- Health status API endpoint for monitoring
- Resource usage monitoring
- Task prioritization during system stress
"""

import os
import sys
import time
import logging
import argparse
import json
import subprocess
import signal
import threading
import smtplib
import schedule
import requests
import psutil
import socket
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from contextlib import contextmanager
from functools import wraps

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'scheduler.log'))
    ]
)
logger = logging.getLogger('scheduler')

# Setup more detailed logging for debugging when needed
debug_logger = logging.getLogger('scheduler.debug')
debug_handler = logging.FileHandler(os.path.join('logs', 'scheduler_debug.log'))
debug_handler.setLevel(logging.DEBUG)
debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
debug_handler.setFormatter(debug_formatter)
debug_logger.addHandler(debug_handler)
debug_logger.setLevel(logging.DEBUG)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configuration with defaults
DEFAULT_CONFIG = {
    "tasks": [
        {
            "name": "Deep Web Monitoring",
            "script": "deep_web_monitor.py",
            "args": ["--config", "config.json"],
            "schedule": "hourly",  # hourly, daily, or cron expression
            "max_retries": 3,
            "retry_delay": 300,  # 5 minutes
            "timeout": 3600,  # 1 hour
            "enabled": True,
            "notify_on_error": True
        },
        {
            "name": "Dashboard Update",
            "script": "update_dashboard.py",
            "args": [],
            "schedule": "*/30 * * * *",  # Every 30 minutes
            "max_retries": 2,
            "retry_delay": 60,  # 1 minute
            "timeout": 300,  # 5 minutes
            "enabled": True,
            "notify_on_error": True
        },
        {
            "name": "Credential Rotation Check",
            "script": "check_credentials.py",
            "args": ["--auto-rotate"],
            "schedule": "daily",
            "max_retries": 2,
            "retry_delay": 300,  # 5 minutes
            "timeout": 600,  # 10 minutes
            "enabled": True,
            "notify_on_error": True
        }
    ],
    "notification": {
        "email": {
            "enabled": False,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_email": "security@example.com",
            "to_email": ["admin@example.com"]
        },
        "webhook": {
            "enabled": False,
            "url": "https://hooks.slack.com/services/xxx/yyy/zzz",
            "headers": {
                "Content-Type": "application/json"
            }
        }
    },
    "general": {
        "status_file": "data/scheduler_status.json",
        "python_executable": sys.executable,
        "max_concurrent_tasks": 2
    }
}

# Global variables
running_processes = {}
task_statuses = {}
config = {}
shutdown_event = threading.Event()

# Task runtime status tracking
task_status = {}

# Circuit breaker pattern implementation
class CircuitBreaker:
    """
    Implements the circuit breaker pattern to prevent repeated attempts at failing operations.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold reached, requests immediately fail
    - HALF-OPEN: After timeout period, allows one test request
    """
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'
    
    def __init__(self, name, failure_threshold=3, reset_timeout=300):
        self.name = name
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout  # seconds
        self.last_failure_time = None
        self.last_success_time = None
        debug_logger.debug(f"Circuit breaker '{name}' initialized in {self.state} state")
        
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning(f"Circuit '{self.name}' OPENED after {self.failure_count} failures")
        
        debug_logger.debug(f"Circuit '{self.name}' failure recorded. State: {self.state}, Count: {self.failure_count}")
    
    def record_success(self):
        """Record a success and reset failure count"""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            logger.info(f"Circuit '{self.name}' CLOSED after successful test")
        
        debug_logger.debug(f"Circuit '{self.name}' success recorded. State: {self.state}")
    
    def can_execute(self):
        """Check if the operation can be executed based on circuit state"""
        if self.state == self.CLOSED:
            return True
            
        if self.state == self.OPEN:
            # Check if timeout has elapsed to transition to HALF-OPEN
            if self.last_failure_time and (datetime.now() - self.last_failure_time).total_seconds() >= self.reset_timeout:
                self.state = self.HALF_OPEN
                logger.info(f"Circuit '{self.name}' entered HALF-OPEN state")
                return True
            return False
            
        # In HALF-OPEN state, we allow exactly one test request
        return True

    def __str__(self):
        return f"CircuitBreaker(name='{self.name}', state={self.state}, failures={self.failure_count})"

# Resource monitoring functions
def get_system_resources():
    """Get current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'timestamp': datetime.now().isoformat()
    }

def is_system_under_stress():
    """Determine if the system is under high resource usage"""
    resources = get_system_resources()
    
    # Define thresholds for system stress
    cpu_threshold = 85
    memory_threshold = 90
    disk_threshold = 95
    
    is_stressed = (resources['cpu_percent'] > cpu_threshold or 
                  resources['memory_percent'] > memory_threshold or
                  resources['disk_percent'] > disk_threshold)
    
    if is_stressed:
        logger.warning(f"System under stress: CPU: {resources['cpu_percent']}%, "
                      f"Memory: {resources['memory_percent']}%, "
                      f"Disk: {resources['disk_percent']}%")
    
    return is_stressed

# Decorator for tracking execution time
def track_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_name = kwargs.get('task', {}).get('name', 'unknown')
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if task_name not in task_status:
            task_status[task_name] = {}
        
        task_status[task_name]['last_execution_time'] = execution_time
        task_status[task_name]['last_run_timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Task '{task_name}' executed in {execution_time:.2f} seconds")
        return result
    return wrapper

# Context manager for timeout handling
@contextmanager
def task_timeout(seconds, task_name):
    """Context manager to add timeout to a task"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Task '{task_name}' timed out after {seconds} seconds")
    
    original_handler = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

# Initialize circuit breakers for tasks
circuit_breakers = {}

def load_config(config_path=None):
    """Load configuration from file or use defaults."""
    global config
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                config = loaded_config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
            config = DEFAULT_CONFIG
    else:
        logger.info("No configuration file found, using default configuration")
        config = DEFAULT_CONFIG
    
    # Ensure the status file directory exists
    status_file = config.get('general', {}).get('status_file', 'data/scheduler_status.json')
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    
    return config

def save_task_status():
    """Save task status to file."""
    status_file = config.get('general', {}).get('status_file', 'data/scheduler_status.json')
    
    try:
        with open(status_file, 'w') as f:
            status_data = {
                "last_updated": datetime.now().isoformat(),
                "tasks": task_statuses
            }
            json.dump(status_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving task status: {e}")

def load_task_status():
    """Load task status from file."""
    global task_statuses
    
    status_file = config.get('general', {}).get('status_file', 'data/scheduler_status.json')
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                task_statuses = data.get('tasks', {})
        except Exception as e:
            logger.error(f"Error loading task status: {e}")
            task_statuses = {}
    else:
        task_statuses = {}

def send_notification(task_name, status, message):
    """Send notification via email and/or webhook."""
    notification_config = config.get('notification', {})
    
    # Email notification
    email_config = notification_config.get('email', {})
    if email_config.get('enabled', False):
        try:
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port')
            username = email_config.get('username')
            password = email_config.get('password')
            from_email = email_config.get('from_email')
            to_emails = email_config.get('to_email', [])
            
            if not all([smtp_server, smtp_port, from_email, to_emails]):
                logger.error("Email notification configured but missing required settings")
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"Task {task_name}: {status}"
            
            # Email body
            body = f"""
            Task: {task_name}
            Status: {status}
            Time: {datetime.now().isoformat()}
            
            Message:
            {message}
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                server.send_message(msg)
                
            logger.info(f"Sent email notification for task {task_name}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    # Webhook notification
    webhook_config = notification_config.get('webhook', {})
    if webhook_config.get('enabled', False):
        try:
            url = webhook_config.get('url')
            headers = webhook_config.get('headers', {})
            
            if not url:
                logger.error("Webhook notification configured but missing URL")
                return
            
            # Prepare webhook payload
            payload = {
                "task_name": task_name,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            
            # Send webhook
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Sent webhook notification for task {task_name}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

@track_execution_time
def execute_task(task):
    """
    Execute a scheduled task with retry logic and error handling.
    
    Args:
        task (dict): Task configuration
    
    Returns:
        bool: True if successful, False otherwise
    """
    task_name = task.get('name', 'Unknown Task')
    command = task.get('command')
    timeout = task.get('timeout', 300)  # Default timeout: 5 minutes
    priority = task.get('priority', 'medium')
    
    if not command:
        logger.error(f"No command specified for task '{task_name}'")
        return False
    
    # Check if this task has a circuit breaker
    if task_name not in circuit_breakers:
        failure_threshold = task.get('failure_threshold', 3)
        reset_timeout = task.get('reset_timeout', 300)
        circuit_breakers[task_name] = CircuitBreaker(task_name, failure_threshold, reset_timeout)
    
    # Check circuit breaker state
    if not circuit_breakers[task_name].can_execute():
        logger.warning(f"Circuit breaker for '{task_name}' is OPEN, skipping execution")
        return False
    
    # Check system resources if not a high priority task
    if priority != 'high' and is_system_under_stress():
        if priority == 'low':
            logger.warning(f"System under stress, skipping low priority task '{task_name}'")
            return False
        logger.warning(f"System under stress while running task '{task_name}', but continuing due to medium priority")
    
    logger.info(f"Executing task: {task_name}")
    
    # Track task execution status
    if task_name not in task_status:
        task_status[task_name] = {}
    
    task_status[task_name]['last_attempt_timestamp'] = datetime.now().isoformat()
    task_status[task_name]['state'] = 'running'
    
    # Execute task in a subprocess
    env = os.environ.copy()
    max_retries = task.get('max_retries', 3)
    retry_delay = task.get('retry_delay', 5)
    
    success = False
    error_message = None
    attempt = 0
    start_time = time.time()
    
    while attempt < max_retries and not success and not shutdown_event.is_set():
        if attempt > 0:
            retry_sleep = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
            logger.info(f"Retry attempt {attempt} for task '{task_name}', waiting {retry_sleep} seconds...")
            time.sleep(retry_sleep)
        
        attempt += 1
        task_status[task_name]['current_attempt'] = attempt
        
        try:
            # Take system snapshot before task execution
            pre_resources = get_system_resources()
            task_status[task_name]['pre_resources'] = pre_resources
            
            # Add a timeout to prevent tasks from hanging
            with task_timeout(timeout, task_name):
                logger.info(f"Running command: {command}")
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                exit_code = process.returncode
                
                # Take snapshot after task execution
                post_resources = get_system_resources()
                task_status[task_name]['post_resources'] = post_resources
                
                # Calculate resource usage deltas
                cpu_delta = post_resources['cpu_percent'] - pre_resources['cpu_percent']
                memory_delta = post_resources['memory_percent'] - pre_resources['memory_percent']
                
                if stdout:
                    debug_logger.debug(f"Task '{task_name}' stdout: {stdout}")
                
                if stderr:
                    debug_logger.debug(f"Task '{task_name}' stderr: {stderr}")
                
                if exit_code == 0:
                    success = True
                    logger.info(f"Task '{task_name}' completed successfully (CPU delta: {cpu_delta:.1f}%, "
                                f"Memory delta: {memory_delta:.1f}%)")
                else:
                    error_message = f"Command exited with code {exit_code}: {stderr}"
                    logger.error(f"Task '{task_name}' failed: {error_message}")
                    
        except TimeoutError as e:
            error_message = str(e)
            logger.error(f"Task '{task_name}' timed out after {timeout} seconds")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error executing task '{task_name}': {error_message}", exc_info=True)
    
    # Update task status
    task_status[task_name]['success'] = success
    task_status[task_name]['last_run_duration'] = time.time() - start_time
    task_status[task_name]['state'] = 'completed'
    
    if success:
        task_status[task_name]['last_success_timestamp'] = datetime.now().isoformat()
        circuit_breakers[task_name].record_success()
    else:
        task_status[task_name]['last_error'] = error_message
        task_status[task_name]['last_failure_timestamp'] = datetime.now().isoformat()
        circuit_breakers[task_name].record_failure()
        
        # Send notification about failure
        if task.get('notify_on_error', True):
            try:
                send_notification(
                    task_name=task_name,
                    status='failed',
                    message=f"Task failed after {attempt} attempts. Error: {error_message}"
                )
            except Exception as e:
                logger.error(f"Failed to send notification for task '{task_name}': {e}")
    
    # Save task status to disk
    save_task_status()
    
    return success

def schedule_tasks():
    """Schedule all enabled tasks according to their configuration."""
    tasks = config.get('tasks', [])
    
    # Clear existing schedule
    schedule.clear()
    
    for task in tasks:
        if not task.get('enabled', True):
            logger.info(f"Task {task.get('name')} is disabled, skipping")
            continue
        
        task_schedule = task.get('schedule', 'daily')
        
        if task_schedule == 'hourly':
            schedule.every().hour.do(execute_task, task)
            logger.info(f"Scheduled task {task.get('name')} to run hourly")
        
        elif task_schedule == 'daily':
            schedule.every().day.at("00:00").do(execute_task, task)
            logger.info(f"Scheduled task {task.get('name')} to run daily at midnight")
        
        elif task_schedule == 'weekly':
            schedule.every().monday.at("00:00").do(execute_task, task)
            logger.info(f"Scheduled task {task.get('name')} to run weekly on Monday at midnight")
        
        else:
            # Assume it's a cron-like expression
            try:
                # Parse the cron expression
                parts = task_schedule.split()
                
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    
                    # Handle */n syntax for minutes
                    if minute.startswith('*/'):
                        interval = int(minute.split('/')[1])
                        schedule.every(interval).minutes.do(execute_task, task)
                        logger.info(f"Scheduled task {task.get('name')} to run every {interval} minutes")
                    else:
                        # For simplicity, just run at the specified minute of each hour
                        if minute.isdigit():
                            schedule.every().hour.at(f":{minute}").do(execute_task, task)
                            logger.info(f"Scheduled task {task.get('name')} to run at minute {minute} of each hour")
                        else:
                            logger.warning(f"Unsupported cron expression for task {task.get('name')}: {task_schedule}")
                            logger.warning(f"Defaulting to hourly schedule for task {task.get('name')}")
                            schedule.every().hour.do(execute_task, task)
                else:
                    logger.warning(f"Invalid cron expression for task {task.get('name')}: {task_schedule}")
                    logger.warning(f"Defaulting to hourly schedule for task {task.get('name')}")
                    schedule.every().hour.do(execute_task, task)
            
            except Exception as e:
                logger.error(f"Error parsing schedule for task {task.get('name')}: {e}")
                logger.warning(f"Defaulting to hourly schedule for task {task.get('name')}")
                schedule.every().hour.do(execute_task, task)

def handle_shutdown(signum, frame):
    """Handle shutdown signal gracefully."""
    logger.info("Shutdown signal received, stopping scheduler...")
    shutdown_event.set()
    
    # Terminate all running processes
    for task_name, process in list(running_processes.items()):
        if process.poll() is None:
            logger.info(f"Terminating running task: {task_name}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Task {task_name} did not terminate gracefully, killing it")
                process.kill()
    
    # Save final task status
    save_task_status()
    
    logger.info("Scheduler stopped")
    sys.exit(0)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scheduler for security monitoring tasks")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--run-now", "-r", help="Run a specific task immediately")
    parser.add_argument("--status", "-s", action="store_true", help="Show status of all tasks")
    args = parser.parse_args()
    
    # Load configuration
    load_config(args.config)
    
    # Load task status
    load_task_status()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Handle special commands
    if args.run_now:
        task_name = args.run_now
        task = next((t for t in config.get('tasks', []) if t.get('name') == task_name), None)
        
        if task:
            logger.info(f"Running task {task_name} immediately")
            execute_task(task)
        else:
            logger.error(f"Task {task_name} not found in configuration")
        
        return
    
    if args.status:
        print(json.dumps(task_statuses, indent=2))
        return
    
    # Schedule tasks
    schedule_tasks()
    
    # Run immediately if requested
    
    # Run the scheduler
    logger.info("Starting scheduler")
    
    while not shutdown_event.is_set():
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 