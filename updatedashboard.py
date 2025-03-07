#!/usr/bin/env python3
"""
Script to automatically update the API status dashboard by checking
the availability and validity of API credentials
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional, Tuple

# Import local modules
import security
from config import API_KEY, DB_PASSWORD, SECRET_TOKEN

# Constants
DASHBOARD_FILE = os.path.join(os.path.dirname(__file__), 'api_status_dashboard.md')
CREDENTIALS_DIR = 'C:/Documents/credentials/myproject'

# Service definitions with their required credentials
SERVICES = [
    {
        'name': 'Core Authentication API',
        'credential_file': 'API_KEY',
        'validate_fn': security.verify_api_key,
        'credential_var': API_KEY
    },
    {
        'name': 'Database Connection Service',
        'credential_file': 'DB_PASSWORD',
        'validate_fn': security.verify_db_password,
        'credential_var': DB_PASSWORD
    },
    {
        'name': 'Cryptographic Service',
        'credential_file': 'SECRET_TOKEN',
        'validate_fn': lambda token: token and len(token) >= 16,
        'credential_var': SECRET_TOKEN
    },
    {
        'name': 'Mail Service',
        'credential_file': 'MAIL_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'Logging Service',
        'credential_file': 'LOGGING_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'Analytics API',
        'credential_file': 'ANALYTICS_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'Payment Gateway',
        'credential_file': 'PAYMENT_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'External Movie Database API',
        'credential_file': 'MOVIE_DB_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'User Management Service',
        'credential_file': 'USER_MGMT_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    },
    {
        'name': 'Content Delivery Network',
        'credential_file': 'CDN_API_KEY',
        'validate_fn': lambda key: key and len(key) >= 8,
        'credential_var': None
    }
]


def check_service_status(service: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if a credential file exists and is valid
    
    Args:
        service: Service to check
        
    Returns:
        Status information dictionary
    """
    # Default status is RED
    status = {
        'color': '🔴 RED',
        'description': 'No codebase embedding created yet',
        'details': 'Pending implementation',
        'has_file': False,
        'is_valid': False
    }
    
    # Check if credential file exists
    file_path = os.path.join(CREDENTIALS_DIR, service['credential_file'])
    try:
        if os.path.exists(file_path):
            status['has_file'] = True
            status['description'] = f"API key found in {CREDENTIALS_DIR}"
            
            # For services integrated in config, check if loaded properly
            if service['credential_var'] is not None:
                is_valid = service['validate_fn'](service['credential_var'])
                if is_valid:
                    status['color'] = '🟢 GREEN'
                    status['details'] = 'Successfully integrated with security module'
                    status['is_valid'] = True
                else:
                    status['color'] = '🟡 ORANGE'
                    status['details'] = 'API key format validation failed'
            else:
                # Check if file content is valid by reading directly
                with open(file_path, 'r') as f:
                    credential = f.read().strip()
                
                try:
                    is_valid = service['validate_fn'](credential)
                    if is_valid:
                        status['color'] = '🟡 ORANGE'
                        status['details'] = 'Credential file exists but not integrated with security module'
                    else:
                        status['color'] = '🟡 ORANGE'
                        status['details'] = 'Credential file exists but has invalid format'
                except Exception as e:
                    status['color'] = '🟡 ORANGE'
                    status['details'] = f'Credential validation error: {str(e)}'
    except Exception as e:
        print(f"Error checking status for {service['name']}: {str(e)}")
    
    return status


def update_dashboard():
    """Update the API status dashboard markdown file"""
    try:
        # Read the current dashboard file
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            dashboard_content = f.read()
        
        # Update the timestamp
        now = datetime.now().isoformat()
        updated_content = re.sub(
            r'\*Last Updated: <!-- AUTO_UPDATE_TIMESTAMP -->\*',
            f'*Last Updated: {now}*',
            dashboard_content
        )
        
        # Check service statuses
        service_statuses = [
            (service, check_service_status(service)) 
            for service in SERVICES
        ]
        
        # Update the table in the dashboard
        table_rows = ''
        for service, status in service_statuses:
            table_rows += f"| {service['name']} | {status['color']} | {status['description']} | {status['details']} |\n"
        
        # Replace the table in the dashboard content
        updated_content = re.sub(
            r'\| Service \| Status \| Description \| Integration Details \|\n\|---------|--------|-------------|---------------------\|\n([\s\S]*?)(?=\n## Green Light Services Documentation)',
            f'| Service | Status | Description | Integration Details |\n|---------|--------|-------------|---------------------|\n{table_rows}\n',
            updated_content
        )
        
        # Write the updated dashboard back to file with utf-8 encoding
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print('API status dashboard updated successfully!')
    except Exception as e:
        print(f'Error updating API status dashboard: {str(e)}')


if __name__ == '__main__':
    update_dashboard() 