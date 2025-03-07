#!/usr/bin/env python3
"""
Credentials management module for verifying and tracking API keys and other credentials.
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Import from local modules
from .utils import (
    generate_request_id, 
    mask_credential, 
    generate_secure_credential, 
    CREDENTIAL_STORE_PATH, 
    CREDENTIAL_HISTORY_PATH
)

# Set up logging
logger = logging.getLogger(__name__)

# Configuration - should be moved to a config file in production
from config import API_KEY, DB_PASSWORD, SECRET_TOKEN, MAIL_API_KEY, LOGGING_API_KEY

# Store for tracking credential usage
usage_log = []
MAX_LOG_SIZE = 1000  # Maximum number of entries to keep in memory

def load_credential_metadata() -> Dict[str, Any]:
    """
    Load credential metadata from storage.
    
    Returns:
        Dictionary containing credential metadata
    """
    metadata_path = os.path.join(CREDENTIAL_STORE_PATH, 'metadata.json')
    if not os.path.exists(metadata_path):
        return {}
        
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credential metadata: {e}")
        return {}

def save_credential_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Save credential metadata to storage.
    
    Args:
        metadata: Dictionary containing credential metadata
        
    Returns:
        True if saved successfully, False otherwise
    """
    metadata_path = os.path.join(CREDENTIAL_STORE_PATH, 'metadata.json')
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving credential metadata: {e}")
        return False

def log_credential_usage(
    credential_type: str,
    component: str,
    operation: str,
    **options
) -> str:
    """
    Log credential usage for tracking and analysis.
    
    Args:
        credential_type: Type of credential (api_key, db_password, etc.)
        component: Component using the credential
        operation: Operation being performed
        options: Additional context information
        
    Returns:
        Request ID for reference
    """
    request_id = options.get('request_id', generate_request_id())
    
    # Create log entry
    log_entry = {
        'request_id': request_id,
        'timestamp': datetime.now().isoformat(),
        'credential_type': credential_type,
        'component': component,
        'operation': operation,
        'ip_address': options.get('ip_address', ''),
        'user_agent': options.get('user_agent', ''),
        'success': options.get('success', True),
        'error': options.get('error', ''),
    }
    
    # Add to in-memory log
    usage_log.append(log_entry)
    
    # Trim log if it's getting too large
    if len(usage_log) > MAX_LOG_SIZE:
        usage_log.pop(0)
    
    # Log the usage
    logger.info(
        f"Credential usage: {credential_type} for {operation} by {component} "
        f"(request_id: {request_id}, success: {log_entry['success']})"
    )
    
    return request_id

def verify_api_key(api_key: str, **options) -> bool:
    """
    Verify an API key against the stored value.
    
    Args:
        api_key: The API key to verify
        options: Additional context information
        
    Returns:
        True if verified successfully, False otherwise
    """
    component = options.get('component', 'unknown')
    operation = options.get('operation', 'api_access')
    
    # Default to unsuccessful
    success = False
    error = ""
    
    try:
        # Simple comparison - in a real system, would use secure comparison
        if api_key == API_KEY:
            success = True
        else:
            error = "Invalid API key"
    except Exception as e:
        error = str(e)
    
    # Log the usage
    log_credential_usage(
        'api_key',
        component,
        operation,
        success=success,
        error=error,
        **options
    )
    
    return success

def verify_db_password(password: str, **options) -> bool:
    """
    Verify a database password against the stored value.
    
    Args:
        password: The database password to verify
        options: Additional context information
        
    Returns:
        True if verified successfully, False otherwise
    """
    component = options.get('component', 'unknown')
    operation = options.get('operation', 'db_access')
    
    # Default to unsuccessful
    success = False
    error = ""
    
    try:
        # Simple comparison - in a real system, would use secure comparison
        if password == DB_PASSWORD:
            success = True
        else:
            error = "Invalid database password"
    except Exception as e:
        error = str(e)
    
    # Log the usage
    log_credential_usage(
        'db_password',
        component,
        operation,
        success=success,
        error=error,
        **options
    )
    
    return success

def verify_mail_api_key(mail_api_key: str, **options) -> bool:
    """
    Verify a mail API key against the stored value.
    
    Args:
        mail_api_key: The mail API key to verify
        options: Additional context information
        
    Returns:
        True if verified successfully, False otherwise
    """
    component = options.get('component', 'unknown')
    operation = options.get('operation', 'mail_send')
    
    # Default to unsuccessful
    success = False
    error = ""
    
    try:
        # Simple comparison - in a real system, would use secure comparison
        if mail_api_key == MAIL_API_KEY:
            success = True
        else:
            error = "Invalid mail API key"
    except Exception as e:
        error = str(e)
    
    # Log the usage
    log_credential_usage(
        'mail_api_key',
        component,
        operation,
        success=success,
        error=error,
        **options
    )
    
    return success

def verify_logging_api_key(logging_api_key: str, **options) -> bool:
    """
    Verify a logging API key against the stored value.
    
    Args:
        logging_api_key: The logging API key to verify
        options: Additional context information
        
    Returns:
        True if verified successfully, False otherwise
    """
    component = options.get('component', 'unknown')
    operation = options.get('operation', 'logging')
    
    # Default to unsuccessful
    success = False
    error = ""
    
    try:
        # Simple comparison - in a real system, would use secure comparison
        if logging_api_key == LOGGING_API_KEY:
            success = True
        else:
            error = "Invalid logging API key"
    except Exception as e:
        error = str(e)
    
    # Log the usage
    log_credential_usage(
        'logging_api_key',
        component,
        operation,
        success=success,
        error=error,
        **options
    )
    
    return success

def get_recent_usage(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent credential usage logs.
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of usage log entries
    """
    return sorted(usage_log, key=lambda x: x['timestamp'], reverse=True)[:limit]

def analyze_for_suspicious_activity() -> List[Dict[str, Any]]:
    """
    Analyze credential usage for suspicious activity.
    
    Returns:
        List of suspicious activity reports
    """
    suspicious_activities = []
    
    # Analyze for repeated failures
    credentials = {}
    
    for entry in usage_log:
        credential_type = entry['credential_type']
        if not entry['success']:
            if credential_type not in credentials:
                credentials[credential_type] = {'failures': 0, 'latest': entry}
            credentials[credential_type]['failures'] += 1
    
    # Report credentials with high failure rates
    for cred_type, data in credentials.items():
        if data['failures'] > 5:  # Threshold for suspicious activity
            suspicious_activities.append({
                'type': 'repeated_failure',
                'credential_type': cred_type,
                'failures': data['failures'],
                'latest_timestamp': data['latest']['timestamp'],
                'latest_request_id': data['latest']['request_id'],
                'severity': 'high' if data['failures'] > 10 else 'medium'
            })
    
    return suspicious_activities

def validate_credential(credential: str, credential_type: str, request_id: str) -> bool:
    """
    Validate credential format and constraints.
    
    Args:
        credential: The credential to validate
        credential_type: Type of credential (api_key, db_password, etc.)
        request_id: Request ID for tracking
        
    Returns:
        True if valid, False otherwise
    """
    if not credential:
        logger.error(f"Empty credential provided for {credential_type} (request_id: {request_id})")
        return False
    
    # Validate length
    min_length = 8  # Minimum length for any credential
    if len(credential) < min_length:
        logger.error(f"Credential too short for {credential_type} (request_id: {request_id})")
        return False
    
    # Validate complexity based on type
    if credential_type == 'db_password':
        # Check for uppercase, lowercase, digit, and special char
        has_upper = any(c.isupper() for c in credential)
        has_lower = any(c.islower() for c in credential)
        has_digit = any(c.isdigit() for c in credential)
        has_special = any(not c.isalnum() for c in credential)
        
        if not (has_upper and has_lower and has_digit and has_special):
            logger.error(f"Password complexity requirements not met (request_id: {request_id})")
            return False
    
    return True

def check_credential_expiration() -> List[Dict[str, Any]]:
    """
    Check for expired or soon-to-expire credentials.
    
    Returns:
        List of credential expiration reports
    """
    metadata = load_credential_metadata()
    expiration_reports = []
    
    now = datetime.now()
    
    for cred_type, data in metadata.items():
        if 'expiration' in data:
            expiration_date = datetime.fromisoformat(data['expiration'])
            days_remaining = (expiration_date - now).days
            
            if days_remaining <= 0:
                expiration_reports.append({
                    'credential_type': cred_type,
                    'status': 'expired',
                    'expiration_date': data['expiration'],
                    'days_past': abs(days_remaining),
                    'severity': 'critical'
                })
            elif days_remaining <= 7:
                expiration_reports.append({
                    'credential_type': cred_type,
                    'status': 'expiring_soon',
                    'expiration_date': data['expiration'],
                    'days_remaining': days_remaining,
                    'severity': 'high' if days_remaining <= 3 else 'medium'
                })
    
    return expiration_reports

def rotate_credential(credential_type: str, request_id: str) -> str:
    """
    Rotate a credential to a new value.
    
    Args:
        credential_type: Type of credential to rotate
        request_id: Request ID for tracking
        
    Returns:
        The new credential value
    """
    # Generate a new credential with appropriate complexity
    if credential_type == 'db_password':
        complexity = 'high'
        length = 16
    elif credential_type == 'api_key':
        complexity = 'medium'
        length = 32
    else:
        complexity = 'medium'
        length = 24
    
    new_credential = generate_secure_credential(length, complexity)
    
    # In a real system, would update the credential in the appropriate system
    # For this example, we'll just log it
    logger.info(f"Rotated credential for {credential_type} (request_id: {request_id})")
    
    # Update metadata with new expiration
    metadata = load_credential_metadata()
    
    if credential_type not in metadata:
        metadata[credential_type] = {}
    
    # Set expiration to 90 days from now
    expiration_date = (datetime.now() + timedelta(days=90)).isoformat()
    metadata[credential_type]['expiration'] = expiration_date
    metadata[credential_type]['last_rotated'] = datetime.now().isoformat()
    
    save_credential_metadata(metadata)
    
    return new_credential

def init_credential_metadata():
    """Initialize credential metadata if it doesn't exist."""
    metadata = load_credential_metadata()
    
    # Create metadata for each credential type if it doesn't exist
    credential_types = ['api_key', 'db_password', 'mail_api_key', 'logging_api_key']
    
    for cred_type in credential_types:
        if cred_type not in metadata:
            # Set initial expiration to 90 days from now
            expiration_date = (datetime.now() + timedelta(days=90)).isoformat()
            metadata[cred_type] = {
                'created': datetime.now().isoformat(),
                'last_rotated': datetime.now().isoformat(),
                'expiration': expiration_date,
                'rotation_interval_days': 90
            }
    
    save_credential_metadata(metadata)
    logger.info("Initialized credential metadata")
