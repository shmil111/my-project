#!/usr/bin/env python3
"""
Todo Management System for Plugin Evolution

This module provides a Python interface to the plugin system database schema
defined in todo.sql. It allows for management of core components, automation
scripts, tasks, maintenance schedules, and system health monitoring.

The module implements a clean separation between database operations and
business logic, with comprehensive error handling and logging.
"""

import os
import sys
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import sqlite3
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database file path
DB_FILE = os.path.join(os.path.dirname(__file__), 'todo.db')

# Create database tables if they don't exist
def initialize_database():
    """Create database tables if they don't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create core_components table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS core_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'No Active Connection',
            check_command TEXT,
            test_command TEXT,
            log_path TEXT,
            auto_command TEXT,
            last_check TIMESTAMP,
            last_test TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            due_date DATE,
            status TEXT DEFAULT 'pending',
            component_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (component_id) REFERENCES core_components (id)
        )
        ''')
        
        # Create task_dependencies table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            depends_on_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (depends_on_id) REFERENCES tasks (id)
        )
        ''')
        
        # Create maintenance_schedule table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_id INTEGER,
            task TEXT NOT NULL,
            frequency TEXT,
            description TEXT,
            next_run TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (component_id) REFERENCES core_components (id)
        )
        ''')
        
        # Create system_health table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            value TEXT,
            status TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create plugin_health table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plugin_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_name TEXT NOT NULL,
            status TEXT,
            details TEXT,
            check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create performance_metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            value REAL,
            context TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create ai_assistance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_assistance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL,
            query TEXT NOT NULL,
            context TEXT,
            response TEXT,
            performance_metrics TEXT,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time TIMESTAMP
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_maintenance_next_run ON maintenance_schedule(next_run)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugin_health_status ON plugin_health(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type)')
        
        conn.commit()

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures connections are properly closed after use.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database cursors.
    Automatically handles connection and cursor lifecycle.
    
    Args:
        commit (bool): Whether to commit changes after operations
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation error: {e}")
            raise
        finally:
            pass  # cursor is closed with the connection

# Helper function to convert SQLite Row objects to dictionaries
def dict_from_row(row):
    """Convert a sqlite3.Row to a dictionary"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}

class TodoException(Exception):
    """Base exception class for Todo module"""
    pass

class CoreComponentManager:
    """Manages core components of the plugin system"""
    
    @staticmethod
    def get_all_components() -> List[Dict[str, Any]]:
        """Retrieve all core components"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT * FROM core_components ORDER BY name")
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving core components: {e}")
            raise TodoException(f"Failed to retrieve core components: {e}")
    
    @staticmethod
    def get_component(component_id: int) -> Dict[str, Any]:
        """Retrieve a specific core component by ID"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT * FROM core_components WHERE id = ?", (component_id,))
                result = cursor.fetchone()
                if not result:
                    raise TodoException(f"Component with ID {component_id} not found")
                return dict_from_row(result)
        except Exception as e:
            logger.error(f"Error retrieving component {component_id}: {e}")
            raise TodoException(f"Failed to retrieve component {component_id}: {e}")
    
    @staticmethod
    def create_component(name: str, check_command: str, test_command: str, 
                        log_path: str, auto_command: str) -> int:
        """Create a new core component"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO core_components 
                    (name, check_command, test_command, log_path, auto_command)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, check_command, test_command, log_path, auto_command)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating component {name}: {e}")
            raise TodoException(f"Failed to create component {name}: {e}")
    
    @staticmethod
    def update_component_status(component_id: int, status: str) -> None:
        """Update the status of a core component"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE core_components
                    SET status = ?, last_check = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, component_id)
                )
                if cursor.rowcount == 0:
                    raise TodoException(f"Component with ID {component_id} not found")
        except Exception as e:
            logger.error(f"Error updating component {component_id} status: {e}")
            raise TodoException(f"Failed to update component status: {e}")

class TaskManager:
    """Manages tasks in the plugin system"""
    
    @staticmethod
    def get_all_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks, optionally filtered by status
        
        Args:
            status: Filter tasks by this status if provided
        """
        try:
            with get_db_cursor() as cursor:
                if status:
                    cursor.execute(
                        "SELECT * FROM tasks WHERE status = ? ORDER BY priority, due_date",
                        (status,)
                    )
                else:
                    cursor.execute("SELECT * FROM tasks ORDER BY priority, due_date")
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving tasks: {e}")
            raise TodoException(f"Failed to retrieve tasks: {e}")
    
    @staticmethod
    def get_active_tasks() -> List[Dict[str, Any]]:
        """Retrieve all active tasks"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM tasks 
                    WHERE status IN ('pending', 'in_progress') 
                    ORDER BY priority, due_date
                    """
                )
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving active tasks: {e}")
            raise TodoException(f"Failed to retrieve active tasks: {e}")
    
    @staticmethod
    def create_task(title: str, description: str, priority: str, 
                   due_date: datetime.date, component_id: Optional[int] = None) -> int:
        """Create a new task"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks 
                    (title, description, priority, due_date, status, component_id)
                    VALUES (?, ?, ?, ?, 'pending', ?)
                    """,
                    (title, description, priority, due_date, component_id)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating task {title}: {e}")
            raise TodoException(f"Failed to create task: {e}")
    
    @staticmethod
    def update_task_status(task_id: int, status: str) -> None:
        """Update the status of a task"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = ?
                    WHERE id = ?
                    """,
                    (status, task_id)
                )
                if cursor.rowcount == 0:
                    raise TodoException(f"Task with ID {task_id} not found")
        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {e}")
            raise TodoException(f"Failed to update task status: {e}")
    
    @staticmethod
    def add_task_dependency(task_id: int, depends_on_id: int) -> None:
        """Add a dependency between tasks"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO task_dependencies (task_id, depends_on_id)
                    VALUES (?, ?)
                    """,
                    (task_id, depends_on_id)
                )
        except Exception as e:
            logger.error(f"Error adding task dependency {task_id} -> {depends_on_id}: {e}")
            raise TodoException(f"Failed to add task dependency: {e}")

class MaintenanceManager:
    """Manages maintenance schedules and system health"""
    
    @staticmethod
    def get_maintenance_overview() -> List[Dict[str, Any]]:
        """Get an overview of all maintenance tasks"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT m.id, m.task, m.frequency, m.description, m.next_run,
                           c.name as component_name
                    FROM maintenance_schedule m
                    JOIN core_components c ON m.component_id = c.id
                    ORDER BY m.next_run
                    """
                )
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving maintenance overview: {e}")
            raise TodoException(f"Failed to retrieve maintenance overview: {e}")
    
    @staticmethod
    def schedule_maintenance(component_id: int, task: str, frequency: str, 
                            description: str) -> int:
        """Schedule a new maintenance task"""
        try:
            with get_db_cursor(commit=True) as cursor:
                # Calculate next_run as current time + 1 day
                next_run = datetime.datetime.now() + datetime.timedelta(days=1)
                cursor.execute(
                    """
                    INSERT INTO maintenance_schedule 
                    (component_id, task, frequency, description, next_run)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (component_id, task, frequency, description, next_run)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error scheduling maintenance for component {component_id}: {e}")
            raise TodoException(f"Failed to schedule maintenance: {e}")
    
    @staticmethod
    def schedule_next_maintenance(frequency: str) -> None:
        """Schedule next maintenance"""
        try:
            with get_db_cursor(commit=True) as cursor:
                # Get all maintenance tasks with the given frequency
                cursor.execute(
                    "SELECT id, frequency FROM maintenance_schedule WHERE frequency = ?",
                    (frequency,)
                )
                tasks = cursor.fetchall()
                
                for task in tasks:
                    # Calculate next run time based on frequency
                    if frequency == 'daily':
                        delta = datetime.timedelta(days=1)
                    elif frequency == 'weekly':
                        delta = datetime.timedelta(weeks=1)
                    elif frequency == 'monthly':
                        delta = datetime.timedelta(days=30)
                    else:
                        delta = datetime.timedelta(days=1)
                    
                    next_run = datetime.datetime.now() + delta
                    
                    # Update the next run time
                    cursor.execute(
                        "UPDATE maintenance_schedule SET next_run = ? WHERE id = ?",
                        (next_run, task['id'])
                    )
        except Exception as e:
            logger.error(f"Error scheduling next maintenance: {e}")
            raise TodoException(f"Failed to schedule next maintenance: {e}")
    
    @staticmethod
    def log_system_health(metric_name: str, value: str, status: str) -> int:
        """Log system health metrics"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO system_health 
                    (metric_name, value, status, recorded_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (metric_name, value, status)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging system health for {metric_name}: {e}")
            raise TodoException(f"Failed to log system health: {e}")
    
    @staticmethod
    def get_system_health_status() -> List[Dict[str, Any]]:
        """Get the current system health status"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT metric_name, value, status, MAX(recorded_at) as last_update
                    FROM system_health
                    GROUP BY metric_name
                    ORDER BY metric_name
                    """
                )
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving system health status: {e}")
            raise TodoException(f"Failed to retrieve system health status: {e}")

class PluginHealthManager:
    """Manages plugin health monitoring"""
    
    @staticmethod
    def log_plugin_health(plugin_name: str, status: str, details: str) -> int:
        """Log plugin health status"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO plugin_health 
                    (plugin_name, status, details, check_time)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (plugin_name, status, details)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging plugin health for {plugin_name}: {e}")
            raise TodoException(f"Failed to log plugin health: {e}")
    
    @staticmethod
    def get_plugin_health(plugin_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get plugin health status, optionally filtered by plugin name"""
        try:
            with get_db_cursor() as cursor:
                if plugin_name:
                    cursor.execute(
                        """
                        SELECT * FROM plugin_health 
                        WHERE plugin_name = ? 
                        ORDER BY check_time DESC
                        """,
                        (plugin_name,)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT plugin_name, status, details, MAX(check_time) as last_check
                        FROM plugin_health
                        GROUP BY plugin_name
                        ORDER BY plugin_name
                        """
                    )
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving plugin health: {e}")
            raise TodoException(f"Failed to retrieve plugin health: {e}")

class PerformanceMetricsManager:
    """Manages performance metrics collection and analysis"""
    
    @staticmethod
    def log_performance_metric(metric_type: str, metric_name: str, 
                              value: float, context: Dict[str, Any]) -> int:
        """Log a performance metric"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO performance_metrics 
                    (metric_type, metric_name, value, context, recorded_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (metric_type, metric_name, value, json.dumps(context))
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging performance metric {metric_name}: {e}")
            raise TodoException(f"Failed to log performance metric: {e}")
    
    @staticmethod
    def get_performance_metrics(metric_type: Optional[str] = None,
                               from_date: Optional[datetime.datetime] = None,
                               to_date: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """Get performance metrics with optional filtering"""
        try:
            with get_db_cursor() as cursor:
                query = "SELECT * FROM performance_metrics WHERE 1=1"
                params = []
                
                if metric_type:
                    query += " AND metric_type = ?"
                    params.append(metric_type)
                
                if from_date:
                    query += " AND recorded_at >= ?"
                    params.append(from_date)
                
                if to_date:
                    query += " AND recorded_at <= ?"
                    params.append(to_date)
                
                query += " ORDER BY recorded_at DESC"
                
                cursor.execute(query, params)
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving performance metrics: {e}")
            raise TodoException(f"Failed to retrieve performance metrics: {e}")

class AIAssistanceManager:
    """Manages AI assistance requests and responses"""
    
    @staticmethod
    def log_ai_request(request_type: str, query: str, context: Dict[str, Any]) -> int:
        """Log an AI assistance request"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO ai_assistance 
                    (request_type, query, context, request_time)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (request_type, query, json.dumps(context))
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging AI request: {e}")
            raise TodoException(f"Failed to log AI request: {e}")
    
    @staticmethod
    def update_ai_response(request_id: int, response: str, 
                          performance_metrics: Dict[str, Any]) -> None:
        """Update an AI assistance request with its response"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE ai_assistance
                    SET response = ?, 
                        performance_metrics = ?,
                        response_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (response, json.dumps(performance_metrics), request_id)
                )
                if cursor.rowcount == 0:
                    raise TodoException(f"AI request with ID {request_id} not found")
        except Exception as e:
            logger.error(f"Error updating AI response for request {request_id}: {e}")
            raise TodoException(f"Failed to update AI response: {e}")
    
    @staticmethod
    def get_ai_assistance_history(request_type: Optional[str] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get AI assistance history with optional filtering"""
        try:
            with get_db_cursor() as cursor:
                if request_type:
                    cursor.execute(
                        """
                        SELECT * FROM ai_assistance 
                        WHERE request_type = ?
                        ORDER BY request_time DESC
                        LIMIT ?
                        """,
                        (request_type, limit)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM ai_assistance 
                        ORDER BY request_time DESC
                        LIMIT ?
                        """,
                        (limit,)
                    )
                return [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving AI assistance history: {e}")
            raise TodoException(f"Failed to retrieve AI assistance history: {e}")

def main():
    """Main function for command-line interface"""
    # Initialize the database if it doesn't exist
    initialize_database()
    
    if len(sys.argv) < 2:
        print("Usage: python todo.py <command> [args]")
        print("Commands:")
        print("  list-tasks [status]        - List all tasks, optionally filtered by status")
        print("  list-active-tasks          - List all active tasks")
        print("  create-task <title> <desc> <priority> <due_date> [component_id]")
        print("  update-task <task_id> <status>")
        print("  list-components            - List all core components")
        print("  create-component <name> <check_cmd> <test_cmd> <log_path> <auto_cmd>")
        print("  system-health              - Show system health status")
        print("  log-health <metric> <value> <status> - Log system health metric")
        print("  maintenance-overview       - Show maintenance overview")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "list-tasks":
            status = sys.argv[2] if len(sys.argv) > 2 else None
            tasks = TaskManager.get_all_tasks(status)
            print(f"Found {len(tasks)} tasks:")
            for task in tasks:
                print(f"[{task['id']}] {task['title']} - {task['status']} (Priority: {task['priority']})")
        
        elif command == "list-active-tasks":
            tasks = TaskManager.get_active_tasks()
            print(f"Found {len(tasks)} active tasks:")
            for task in tasks:
                print(f"[{task['id']}] {task['title']} - Due: {task['due_date']} (Priority: {task['priority']})")
        
        elif command == "create-task":
            if len(sys.argv) < 6:
                print("Error: Missing arguments for create-task")
                return
            
            title = sys.argv[2]
            description = sys.argv[3]
            priority = sys.argv[4]
            due_date = datetime.datetime.strptime(sys.argv[5], "%Y-%m-%d").date()
            component_id = int(sys.argv[6]) if len(sys.argv) > 6 else None
            
            task_id = TaskManager.create_task(title, description, priority, due_date, component_id)
            print(f"Created task with ID: {task_id}")
        
        elif command == "update-task":
            if len(sys.argv) < 4:
                print("Error: Missing arguments for update-task")
                return
            
            task_id = int(sys.argv[2])
            status = sys.argv[3]
            
            TaskManager.update_task_status(task_id, status)
            print(f"Updated task {task_id} status to {status}")
        
        elif command == "list-components":
            components = CoreComponentManager.get_all_components()
            print(f"Found {len(components)} components:")
            for comp in components:
                print(f"[{comp['id']}] {comp['name']} - Status: {comp['status']}")
        
        elif command == "create-component":
            if len(sys.argv) < 7:
                print("Error: Missing arguments for create-component")
                return
            
            name = sys.argv[2]
            check_command = sys.argv[3]
            test_command = sys.argv[4]
            log_path = sys.argv[5]
            auto_command = sys.argv[6]
            
            component_id = CoreComponentManager.create_component(
                name, check_command, test_command, log_path, auto_command
            )
            print(f"Created component with ID: {component_id}")
        
        elif command == "system-health":
            health = MaintenanceManager.get_system_health_status()
            print("System Health Status:")
            for item in health:
                print(f"{item['metric_name']}: {item['status']} - {item['value']} (Last updated: {item['last_update']})")
        
        elif command == "log-health":
            if len(sys.argv) < 5:
                print("Error: Missing arguments for log-health")
                return
            
            metric_name = sys.argv[2]
            value = sys.argv[3]
            status = sys.argv[4]
            
            health_id = MaintenanceManager.log_system_health(metric_name, value, status)
            print(f"Logged health metric with ID: {health_id}")
        
        elif command == "maintenance-overview":
            overview = MaintenanceManager.get_maintenance_overview()
            print("Maintenance Overview:")
            for item in overview:
                print(f"{item['component_name']} - {item['task']}: Next run at {item['next_run']}")
        
        else:
            print(f"Unknown command: {command}")
    
    except TodoException as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 