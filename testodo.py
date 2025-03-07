#!/usr/bin/env python3
"""
Test script for todo.py module

This script demonstrates the usage of the todo.py module by creating
sample components, tasks, and health metrics in the SQLite database.
"""

import os
import sys
import datetime
import json
from typing import Dict, Any

# Import the todo module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import todo

def print_separator(title):
    """Print a separator with a title"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")

def test_components():
    """Test component management functionality"""
    print_separator("Testing Component Management")
    
    # Create sample components
    print("Creating sample components...")
    
    db_component_id = todo.CoreComponentManager.create_component(
        "Database Service", 
        "check_db.sh", 
        "test_db_queries.sh", 
        "/var/log/db", 
        "restart_db.sh"
    )
    print(f"Created Database component with ID: {db_component_id}")
    
    api_component_id = todo.CoreComponentManager.create_component(
        "API Gateway", 
        "check_api.sh", 
        "test_api_endpoints.sh", 
        "/var/log/api", 
        "restart_api.sh"
    )
    print(f"Created API Gateway component with ID: {api_component_id}")
    
    ui_component_id = todo.CoreComponentManager.create_component(
        "UI Service", 
        "check_ui.sh", 
        "test_ui_rendering.sh", 
        "/var/log/ui", 
        "restart_ui.sh"
    )
    print(f"Created UI Service component with ID: {ui_component_id}")
    
    # List all components
    print("\nListing all components:")
    components = todo.CoreComponentManager.get_all_components()
    for comp in components:
        print(f"[{comp['id']}] {comp['name']} - Status: {comp['status']}")
    
    # Update component status
    print("\nUpdating component statuses...")
    todo.CoreComponentManager.update_component_status(db_component_id, "Running")
    todo.CoreComponentManager.update_component_status(api_component_id, "Running")
    todo.CoreComponentManager.update_component_status(ui_component_id, "Degraded")
    
    # Get updated components
    print("\nUpdated component statuses:")
    for comp_id in [db_component_id, api_component_id, ui_component_id]:
        comp = todo.CoreComponentManager.get_component(comp_id)
        print(f"[{comp['id']}] {comp['name']} - Status: {comp['status']}")
    
    return db_component_id, api_component_id, ui_component_id

def test_tasks(component_ids):
    """Test task management functionality"""
    print_separator("Testing Task Management")
    
    db_id, api_id, ui_id = component_ids
    
    # Create sample tasks
    print("Creating sample tasks...")
    
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    next_week = today + datetime.timedelta(days=7)
    
    task1_id = todo.TaskManager.create_task(
        "Fix database connection issue",
        "Database connections are timing out after 30 seconds",
        "high",
        tomorrow,
        db_id
    )
    print(f"Created task with ID: {task1_id}")
    
    task2_id = todo.TaskManager.create_task(
        "Update API documentation",
        "Add new endpoints to the API documentation",
        "medium",
        next_week,
        api_id
    )
    print(f"Created task with ID: {task2_id}")
    
    task3_id = todo.TaskManager.create_task(
        "Optimize UI rendering",
        "UI is slow to render on mobile devices",
        "high",
        tomorrow,
        ui_id
    )
    print(f"Created task with ID: {task3_id}")
    
    # Add task dependencies
    print("\nAdding task dependencies...")
    todo.TaskManager.add_task_dependency(task3_id, task1_id)
    print(f"Task {task3_id} now depends on task {task1_id}")
    
    # List all tasks
    print("\nListing all tasks:")
    tasks = todo.TaskManager.get_all_tasks()
    for task in tasks:
        print(f"[{task['id']}] {task['title']} - {task['status']} (Priority: {task['priority']})")
    
    # Update task status
    print("\nUpdating task statuses...")
    todo.TaskManager.update_task_status(task1_id, "in_progress")
    print(f"Updated task {task1_id} status to 'in_progress'")
    
    # List active tasks
    print("\nListing active tasks:")
    active_tasks = todo.TaskManager.get_active_tasks()
    for task in active_tasks:
        print(f"[{task['id']}] {task['title']} - {task['status']} (Priority: {task['priority']})")
    
    return task1_id, task2_id, task3_id

def test_maintenance(component_ids):
    """Test maintenance scheduling functionality"""
    print_separator("Testing Maintenance Scheduling")
    
    db_id, api_id, ui_id = component_ids
    
    # Schedule maintenance tasks
    print("Scheduling maintenance tasks...")
    
    maint1_id = todo.MaintenanceManager.schedule_maintenance(
        db_id,
        "Database backup",
        "daily",
        "Perform daily database backup"
    )
    print(f"Scheduled maintenance with ID: {maint1_id}")
    
    maint2_id = todo.MaintenanceManager.schedule_maintenance(
        api_id,
        "API health check",
        "hourly",
        "Check API endpoint health"
    )
    print(f"Scheduled maintenance with ID: {maint2_id}")
    
    maint3_id = todo.MaintenanceManager.schedule_maintenance(
        ui_id,
        "UI performance test",
        "weekly",
        "Run UI performance tests"
    )
    print(f"Scheduled maintenance with ID: {maint3_id}")
    
    # Get maintenance overview
    print("\nMaintenance overview:")
    overview = todo.MaintenanceManager.get_maintenance_overview()
    for item in overview:
        print(f"{item['component_name']} - {item['task']}: Next run at {item['next_run']}")
    
    # Schedule next maintenance
    print("\nScheduling next maintenance for weekly tasks...")
    todo.MaintenanceManager.schedule_next_maintenance("weekly")
    
    # Get updated maintenance overview
    print("\nUpdated maintenance overview:")
    overview = todo.MaintenanceManager.get_maintenance_overview()
    for item in overview:
        print(f"{item['component_name']} - {item['task']}: Next run at {item['next_run']}")
    
    return maint1_id, maint2_id, maint3_id

def test_system_health():
    """Test system health monitoring functionality"""
    print_separator("Testing System Health Monitoring")
    
    # Log system health metrics
    print("Logging system health metrics...")
    
    metric1_id = todo.MaintenanceManager.log_system_health(
        "CPU Usage",
        "45%",
        "normal"
    )
    print(f"Logged CPU Usage metric with ID: {metric1_id}")
    
    metric2_id = todo.MaintenanceManager.log_system_health(
        "Memory Usage",
        "78%",
        "warning"
    )
    print(f"Logged Memory Usage metric with ID: {metric2_id}")
    
    metric3_id = todo.MaintenanceManager.log_system_health(
        "Disk Space",
        "92%",
        "critical"
    )
    print(f"Logged Disk Space metric with ID: {metric3_id}")
    
    # Get system health status
    print("\nSystem health status:")
    health = todo.MaintenanceManager.get_system_health_status()
    for item in health:
        print(f"{item['metric_name']}: {item['status']} - {item['value']} (Last updated: {item['last_update']})")
    
    return metric1_id, metric2_id, metric3_id

def test_plugin_health():
    """Test plugin health monitoring functionality"""
    print_separator("Testing Plugin Health Monitoring")
    
    # Log plugin health
    print("Logging plugin health...")
    
    plugin1_id = todo.PluginHealthManager.log_plugin_health(
        "Authentication Plugin",
        "healthy",
        "All authentication services operational"
    )
    print(f"Logged Authentication Plugin health with ID: {plugin1_id}")
    
    plugin2_id = todo.PluginHealthManager.log_plugin_health(
        "Payment Gateway Plugin",
        "degraded",
        "Increased latency in payment processing"
    )
    print(f"Logged Payment Gateway Plugin health with ID: {plugin2_id}")
    
    plugin3_id = todo.PluginHealthManager.log_plugin_health(
        "Analytics Plugin",
        "failed",
        "Unable to connect to analytics service"
    )
    print(f"Logged Analytics Plugin health with ID: {plugin3_id}")
    
    # Get plugin health
    print("\nPlugin health status:")
    plugin_health = todo.PluginHealthManager.get_plugin_health()
    for item in plugin_health:
        print(f"{item['plugin_name']}: {item['status']} - {item['details']}")
    
    return plugin1_id, plugin2_id, plugin3_id

def test_performance_metrics():
    """Test performance metrics functionality"""
    print_separator("Testing Performance Metrics")
    
    # Log performance metrics
    print("Logging performance metrics...")
    
    metric1_id = todo.PerformanceMetricsManager.log_performance_metric(
        "response_time",
        "api_login",
        245.6,
        {"endpoint": "/api/login", "method": "POST", "user_count": 1000}
    )
    print(f"Logged API Login response time metric with ID: {metric1_id}")
    
    metric2_id = todo.PerformanceMetricsManager.log_performance_metric(
        "throughput",
        "database_queries",
        1250.0,
        {"database": "users", "query_type": "SELECT", "period": "1 minute"}
    )
    print(f"Logged Database Queries throughput metric with ID: {metric2_id}")
    
    metric3_id = todo.PerformanceMetricsManager.log_performance_metric(
        "error_rate",
        "payment_processing",
        0.05,
        {"gateway": "stripe", "transaction_count": 500}
    )
    print(f"Logged Payment Processing error rate metric with ID: {metric3_id}")
    
    # Get performance metrics
    print("\nPerformance metrics:")
    metrics = todo.PerformanceMetricsManager.get_performance_metrics()
    for metric in metrics:
        context = json.loads(metric['context']) if metric['context'] else {}
        print(f"{metric['metric_type']} - {metric['metric_name']}: {metric['value']} ({context})")
    
    return metric1_id, metric2_id, metric3_id

def test_ai_assistance():
    """Test AI assistance functionality"""
    print_separator("Testing AI Assistance")
    
    # Log AI requests
    print("Logging AI assistance requests...")
    
    request1_id = todo.AIAssistanceManager.log_ai_request(
        "code_completion",
        "Complete this function: def calculate_average(numbers):",
        {"language": "python", "context": "data processing"}
    )
    print(f"Logged Code Completion request with ID: {request1_id}")
    
    request2_id = todo.AIAssistanceManager.log_ai_request(
        "error_analysis",
        "Why am I getting a NullPointerException in my Java code?",
        {"language": "java", "stack_trace": "java.lang.NullPointerException at line 42"}
    )
    print(f"Logged Error Analysis request with ID: {request2_id}")
    
    # Update with responses
    print("\nUpdating AI assistance responses...")
    
    todo.AIAssistanceManager.update_ai_response(
        request1_id,
        """def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)""",
        {"response_time_ms": 120, "model": "gpt-4", "tokens": 45}
    )
    print(f"Updated response for request {request1_id}")
    
    todo.AIAssistanceManager.update_ai_response(
        request2_id,
        "You're getting a NullPointerException because you're trying to access a method or property of an object that is null. Check line 42 in your code.",
        {"response_time_ms": 180, "model": "gpt-4", "tokens": 78}
    )
    print(f"Updated response for request {request2_id}")
    
    # Get AI assistance history
    print("\nAI assistance history:")
    history = todo.AIAssistanceManager.get_ai_assistance_history()
    for item in history:
        print(f"[{item['id']}] {item['request_type']} - Query: {item['query'][:50]}...")
        if item['response']:
            print(f"  Response: {item['response'][:50]}...")
        print()
    
    return request1_id, request2_id

def main():
    """Main function to run all tests"""
    print("Initializing database...")
    todo.initialize_database()
    
    # Run all tests
    component_ids = test_components()
    task_ids = test_tasks(component_ids)
    maintenance_ids = test_maintenance(component_ids)
    health_metric_ids = test_system_health()
    plugin_health_ids = test_plugin_health()
    performance_metric_ids = test_performance_metrics()
    ai_request_ids = test_ai_assistance()
    
    print_separator("All Tests Completed Successfully")
    print("The todo.py module is working correctly!")

if __name__ == "__main__":
    main() 