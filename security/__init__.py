#!/usr/bin/env python3
"""
Security module for API key verification, credential management, and 
threat intelligence management in Python.

This module has been refactored from a monolithic structure into
a more modular architecture with specialized submodules.
"""
import logging
import os
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import submodules
from .modules.utils import (
    generate_request_id,
    mask_credential,
    generate_secure_credential,
    dispose_sensitive_data
)

from .modules.credentials import (
    verify_api_key,
    verify_db_password,
    verify_mail_api_key,
    verify_logging_api_key,
    log_credential_usage,
    get_recent_usage,
    analyze_for_suspicious_activity,
    validate_credential,
    check_credential_expiration,
    rotate_credential,
    init_credential_metadata
)

from .modules.intel import (
    categorize_intelligence,
    retrieve_intelligence,
    search_intelligence,
    add_ioc,
    check_ioc
)

from .modules.taxii import (
    TAXIIClient,
    create_taxii_config,
    list_taxii_configs
)

from .modules.threat import (
    ThreatDetector,
    identify_ioc_type,
    extract_iocs,
    check_threat_intelligence,
    create_threat_rule
)

from .modules.middleware import (
    is_ip_trusted,
    require_api_key,
    create_security_middleware
)

# Initialize data directories
def init_data_directories():
    """Initialize data directories for the security module."""
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Create directories
    directories = [
        'credentials',
        'credential_history',
        'intel',
        'iocs',
        'taxii_configs',
        'threat_rules',
        'logs'
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
    
    logger.info("Initialized security data directories")

# Initialize security module
def initialize(auto_init_directories: bool = True):
    """
    Initialize the security module.
    
    Args:
        auto_init_directories: Whether to automatically create data directories
    """
    if auto_init_directories:
        init_data_directories()
    
    # Initialize credential metadata
    init_credential_metadata()
    
    logger.info("Initialized security module")

# Create a singleton threat detector
threat_detector = ThreatDetector()

# Version information
__version__ = '1.0.0'
__author__ = 'Security Team'
