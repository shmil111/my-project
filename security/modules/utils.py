#!/usr/bin/env python3
"""
Utility functions for the security module.
"""
import os
import uuid
import hashlib
import logging
import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths for data storage
BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
INTEL_STORE_PATH = os.path.join(BASE_PATH, 'intel')
THREAT_IOC_PATH = os.path.join(BASE_PATH, 'iocs')
CREDENTIAL_STORE_PATH = os.path.join(BASE_PATH, 'credentials')
CREDENTIAL_HISTORY_PATH = os.path.join(BASE_PATH, 'credential_history')

# Create storage directories if they don't exist
os.makedirs(INTEL_STORE_PATH, exist_ok=True)
os.makedirs(THREAT_IOC_PATH, exist_ok=True)
os.makedirs(CREDENTIAL_STORE_PATH, exist_ok=True)
os.makedirs(CREDENTIAL_HISTORY_PATH, exist_ok=True)

def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def mask_credential(credential: str) -> str:
    """
    Mask a credential for logging purposes.
    
    Args:
        credential: The credential to mask
        
    Returns:
        A masked version of the credential
    """
    if not credential:
        return ""
    
    # Keep only first and last characters visible
    if len(credential) <= 8:
        return credential[0] + "*" * (len(credential) - 2) + credential[-1]
    else:
        return credential[:4] + "*" * (len(credential) - 8) + credential[-4:]

def generate_secure_credential(length: int = 32, complexity: str = 'high') -> str:
    """
    Generate a secure credential.
    
    Args:
        length: Length of the credential
        complexity: Complexity level ('low', 'medium', 'high')
        
    Returns:
        A secure credential string
    """
    if complexity == 'low':
        # Alphanumeric only
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    elif complexity == 'medium':
        # Alphanumeric + some special chars
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    else:
        # Full range of special chars
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?/~`"\'\\' 
    
    # Generate secure random string
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def dispose_sensitive_data(file_path: str, secure_delete: bool = False) -> bool:
    """
    Securely dispose of sensitive data.
    
    Args:
        file_path: Path to the file to dispose
        secure_delete: Whether to perform secure deletion
        
    Returns:
        True if disposed successfully, False otherwise
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for disposal: {file_path}")
        return False
    
    try:
        if secure_delete:
            # Overwrite with random data before deletion
            file_size = os.path.getsize(file_path)
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Delete the file
        os.remove(file_path)
        logger.info(f"Successfully disposed of sensitive data: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error disposing of sensitive data: {e}")
        return False
