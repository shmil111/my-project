#!/usr/bin/env python3
"""
Security module for API key verification, credential usage tracking, and 
threat intelligence management in Python.
"""
import os
import time
import uuid
import json
import hashlib
import logging
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import glob
import re
import secrets

# Add imports for STIX/TAXII integration
try:
    import stix2
    from taxii2client.v20 import Server, Collection
    STIX_AVAILABLE = True
except ImportError:
    STIX_AVAILABLE = False
    
from config import API_KEY, DB_PASSWORD, SECRET_TOKEN, MAIL_API_KEY, LOGGING_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store for tracking credential usage
usage_log = []
MAX_LOG_SIZE = 1000  # Maximum number of entries to keep in memory

# Intelligence storage
INTEL_STORE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'intel')
THREAT_IOC_PATH = os.path.join(os.path.dirname(__file__), 'data', 'iocs')

# Credential management paths
CREDENTIAL_STORE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'credentials')
CREDENTIAL_HISTORY_PATH = os.path.join(os.path.dirname(__file__), 'data', 'credential_history')

# Create storage directories if they don't exist
os.makedirs(INTEL_STORE_PATH, exist_ok=True)
os.makedirs(THREAT_IOC_PATH, exist_ok=True)
os.makedirs(CREDENTIAL_STORE_PATH, exist_ok=True)
os.makedirs(CREDENTIAL_HISTORY_PATH, exist_ok=True)

# Valid priority levels for intelligence categorization
PRIORITY_LEVELS = ['Critical', 'High', 'Medium', 'Low']

# Valid intelligence source types
SOURCE_TYPES = [
    'forums', 'marketplaces', 'paste_sites', 'social_media', 
    'dark_web', 'code_repositories', 'leaked_databases', 'other'
]

# STIX/TAXII configuration
TAXII_SERVER_URL = os.getenv('TAXII_SERVER_URL', '')
TAXII_USERNAME = os.getenv('TAXII_USERNAME', '')
TAXII_PASSWORD = os.getenv('TAXII_PASSWORD', '')
TAXII_COLLECTION_ID = os.getenv('TAXII_COLLECTION_ID', '')

# Credential management configuration
CREDENTIAL_TYPES = {
    'API_KEY': {
        'rotation_interval_days': 90,  # Rotate API keys every 90 days
        'warning_days': 14,            # Warn 14 days before expiration
        'validation_function': 'verify_api_key',
        'length': 32,
        'complexity': 'high'
    },
    'DB_PASSWORD': {
        'rotation_interval_days': 60,  # Rotate database passwords every 60 days
        'warning_days': 10,            # Warn 10 days before expiration
        'validation_function': 'verify_db_password',
        'length': 24,
        'complexity': 'high'
    },
    'MAIL_API_KEY': {
        'rotation_interval_days': 90,  # Rotate mail API keys every 90 days
        'warning_days': 14,            # Warn 14 days before expiration
        'validation_function': 'verify_mail_api_key',
        'length': 32,
        'complexity': 'high'
    },
    'LOGGING_API_KEY': {
        'rotation_interval_days': 90,  # Rotate logging API keys every 90 days
        'warning_days': 14,            # Warn 14 days before expiration
        'validation_function': 'verify_logging_api_key',
        'length': 32,
        'complexity': 'high'
    },
    'SECRET_TOKEN': {
        'rotation_interval_days': 30,  # Rotate secret tokens every 30 days
        'warning_days': 7,             # Warn 7 days before expiration
        'validation_function': None,   # No specific validation function
        'length': 48,
        'complexity': 'very_high'
    }
}

# Enhanced threat detection configuration
THREAT_DETECTION_CONFIG = {
    'max_failed_attempts': 5,
    'lockout_duration_minutes': 30,
    'suspicious_patterns': [
        r'\.\.\/',  # Directory traversal
        r'<script>',  # XSS attempts
        r'UNION SELECT',  # SQL injection
        r'exec\(',  # Command injection
        r'\.\.\/\.\.\/'  # Deep directory traversal
    ],
    'rate_limits': {
        'api': 100,  # requests per minute
        'auth': 5,   # login attempts per minute
        'general': 1000  # general requests per minute
    }
}

# Load existing credential metadata
def load_credential_metadata():
    """Load credential metadata from storage."""
    metadata_path = os.path.join(CREDENTIAL_STORE_PATH, 'metadata.json')
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading credential metadata: {e}")
    return {}

# Save credential metadata
def save_credential_metadata(metadata):
    """Save credential metadata to storage."""
    metadata_path = os.path.join(CREDENTIAL_STORE_PATH, 'metadata.json')
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving credential metadata: {e}")

# Initialize credential metadata
credential_metadata = load_credential_metadata()

# STIX/TAXII connection cache
_taxii_server = None
_taxii_collection = None

def generate_request_id() -> str:
    """Generate a unique request identifier.
    
    Returns:
        str: Unique request ID
    """
    return str(uuid.uuid4())


def mask_credential(credential: str) -> str:
    """Mask a credential for secure logging.
    
    Args:
        credential (str): The credential to mask
        
    Returns:
        str: Masked credential
    """
    if not credential:
        return 'undefined'
    if len(credential) <= 6:
        return '******'
    
    return f"{credential[:3]}...{credential[-3:]}"


def log_credential_usage(
    credential_type: str,
    component: str,
    operation: str,
    **options
) -> str:
    """Log credential usage with security tracking information.
    
    Args:
        credential_type (str): Type of credential (API_KEY, DB_PASSWORD, etc.)
        component (str): Component using the credential
        operation (str): Operation being performed
        **options: Additional options including requestId, clientIp, etc.
        
    Returns:
        str: Request ID for this operation
    """
    request_id = options.get('request_id') or generate_request_id()
    timestamp = datetime.now().isoformat()
    client_ip = options.get('client_ip') or 'internal'
    
    # Create usage record
    usage_record = {
        'request_id': request_id,
        'timestamp': timestamp,
        'credential_type': credential_type,
        'component': component,
        'operation': operation,
        'client_ip': client_ip,
        'success': options.get('success', True),
        'user_id': options.get('user_id', 'system')
    }
    
    # Add to in-memory log with size limit
    usage_log.insert(0, usage_record)
    if len(usage_log) > MAX_LOG_SIZE:
        usage_log.pop()
    
    # Log to console (in production, you'd use a proper logging system)
    logger.info(
        f"[{timestamp}] [{request_id}] Credential usage: "
        f"{credential_type} by {component} for {operation} from {client_ip}"
    )
    
    # In a real system, you might also write to a secure log file or database
    
    return request_id


def verify_api_key(api_key: str, **options) -> bool:
    """Verify API key format and validity.
    
    Args:
        api_key (str): The API key to verify
        **options: Verification options
        
    Returns:
        bool: True if valid, false otherwise
    """
    # Check API key format
    if not api_key or not isinstance(api_key, str) or len(api_key) < 10:
        log_credential_usage(
            'API_KEY',
            options.get('component', 'unknown'),
            'verify',
            success=False,
            request_id=options.get('request_id'),
            client_ip=options.get('client_ip'),
            user_id=options.get('user_id')
        )
        return False
    
    # In a real system, you might validate against a whitelist or check a hash
    # This is a simple example that just checks if it matches our stored API key
    is_valid = api_key == API_KEY
    
    log_credential_usage(
        'API_KEY',
        options.get('component', 'unknown'),
        'verify',
        success=is_valid,
        request_id=options.get('request_id'),
        client_ip=options.get('client_ip'),
        user_id=options.get('user_id')
    )
    
    return is_valid


def verify_db_password(password: str, **options) -> bool:
    """Verify database password.
    
    Args:
        password (str): The password to verify
        **options: Verification options
        
    Returns:
        bool: True if valid, false otherwise
    """
    # Basic validation
    if not password or not isinstance(password, str) or len(password) < 8:
        log_credential_usage(
            'DB_PASSWORD',
            options.get('component', 'unknown'),
            'verify',
            success=False,
            request_id=options.get('request_id'),
            client_ip=options.get('client_ip'),
            user_id=options.get('user_id')
        )
        return False
    
    # Simple verification
    is_valid = password == DB_PASSWORD
    
    log_credential_usage(
        'DB_PASSWORD',
        options.get('component', 'unknown'),
        'verify',
        success=is_valid,
        request_id=options.get('request_id'),
        client_ip=options.get('client_ip'),
        user_id=options.get('user_id')
    )
    
    return is_valid


def verify_mail_api_key(mail_api_key: str, **options) -> bool:
    """Verify mail API key format and validity.
    
    Args:
        mail_api_key (str): The mail API key to verify
        **options: Verification options
        
    Returns:
        bool: True if valid, false otherwise
    """
    # Check API key format
    if not mail_api_key or not isinstance(mail_api_key, str) or len(mail_api_key) < 8:
        log_credential_usage(
            'MAIL_API_KEY',
            options.get('component', 'unknown'),
            'verify',
            success=False,
            request_id=options.get('request_id'),
            client_ip=options.get('client_ip'),
            user_id=options.get('user_id')
        )
        return False
    
    # In a real system, you might validate against a whitelist or check a hash
    # This is a simple example that just checks if it matches our stored API key
    is_valid = mail_api_key == MAIL_API_KEY
    
    log_credential_usage(
        'MAIL_API_KEY',
        options.get('component', 'unknown'),
        'verify',
        success=is_valid,
        request_id=options.get('request_id'),
        client_ip=options.get('client_ip'),
        user_id=options.get('user_id')
    )
    
    return is_valid


def verify_logging_api_key(logging_api_key: str, **options) -> bool:
    """Verify logging service API key format and validity.
    
    Args:
        logging_api_key (str): The logging API key to verify
        **options: Verification options
        
    Returns:
        bool: True if valid, false otherwise
    """
    # Check API key format
    if not logging_api_key or not isinstance(logging_api_key, str) or len(logging_api_key) < 8:
        log_credential_usage(
            'LOGGING_API_KEY',
            options.get('component', 'unknown'),
            'verify',
            success=False,
            request_id=options.get('request_id'),
            client_ip=options.get('client_ip'),
            user_id=options.get('user_id')
        )
        return False
    
    # In a real system, you might validate against a whitelist or check a hash
    # This is a simple example that just checks if it matches our stored API key
    is_valid = logging_api_key == LOGGING_API_KEY
    
    log_credential_usage(
        'LOGGING_API_KEY',
        options.get('component', 'unknown'),
        'verify',
        success=is_valid,
        request_id=options.get('request_id'),
        client_ip=options.get('client_ip'),
        user_id=options.get('user_id')
    )
    
    return is_valid


def get_recent_usage(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent credential usage logs.
    
    Args:
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict[str, Any]]: Usage records
    """
    return usage_log[:limit]


def analyze_for_suspicious_activity() -> List[Dict[str, Any]]:
    """Analyze credential usage for suspicious patterns.
    
    Returns:
        List[Dict[str, Any]]: List of suspicious activities
    """
    # In a real implementation, this would contain logic to detect:
    # - Unusual access patterns
    # - Access from unexpected IPs
    # - Credential usage at unusual times
    # - Multiple failed verification attempts
    
    # This is a placeholder that simply looks for failed verifications
    suspicious_activities = [
        {
            'level': 'warning',
            'message': f"Failed credential verification: {record['credential_type']}",
            'timestamp': record['timestamp'],
            'request_id': record['request_id'],
            'client_ip': record['client_ip'],
            'component': record['component']
        }
        for record in usage_log if not record['success']
    ]
    
    return suspicious_activities


def is_ip_trusted(ip_address: str) -> bool:
    """Check if an IP address is from a trusted range.
    
    Args:
        ip_address (str): IP address to check
        
    Returns:
        bool: True if trusted, False otherwise
    """
    if ip_address == 'localhost' or ip_address == '127.0.0.1':
        return True
        
    try:
        # Example trusted network ranges (for demonstration)
        trusted_ranges = [
            '10.0.0.0/8',       # Private network
            '172.16.0.0/12',    # Private network
            '192.168.0.0/16',   # Private network
        ]
        
        ip = ipaddress.ip_address(ip_address)
        
        for network_range in trusted_ranges:
            network = ipaddress.ip_network(network_range)
            if ip in network:
                return True
                
        return False
    except ValueError:
        # Invalid IP address format
        return False


def create_security_middleware(app):
    """Create a Flask middleware that adds request ID and logs API key usage.
    
    Args:
        app: Flask application
    """
    from flask import request, g

    @app.before_request
    def before_request():
        # Add request ID to request context
        g.request_id = generate_request_id()
        
        # Capture IP address
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        g.client_ip = client_ip
        
        # Check for API key in Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            is_valid = verify_api_key(
                api_key,
                component='api-middleware',
                operation=f"{request.method} {request.path}",
                request_id=g.request_id,
                client_ip=client_ip
            )
            
            # Attach validation result to g for use in route handlers
            g.api_key_valid = is_valid
        else:
            g.api_key_valid = False

    @app.after_request
    def after_request(response):
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    return app


def categorize_intelligence(data, source_type, priority_level):
    """
    Categorizes intelligence data from deep web research.

    Args:
        data (dict): The intelligence data to categorize.  Should include a 'description' key.
        source_type (str): The source of the intelligence (e.g., 'forums', 'marketplaces', 'paste sites').
        priority_level (str): Priority level ('Critical', 'High', 'Medium', 'Low').

    Returns:
        dict: Categorized data with metadata, or None if input is invalid.
    """
    # Input validation
    if not isinstance(data, dict) or 'description' not in data:
        print("Error: Invalid data format. Must be a dictionary with a 'description' key.")
        return None
    if not isinstance(source_type, str) or not source_type:
        print("Error: Invalid source_type. Must be a non-empty string.")
        return None
    if priority_level not in ('Critical', 'High', 'Medium', 'Low'):
        print("Error: Invalid priority_level. Must be one of: 'Critical', 'High', 'Medium', 'Low'.")
        return None

    # Add metadata
    categorized_data = {
        'original_data': data,
        'source': source_type,
        'priority': priority_level,
        'timestamp': datetime.datetime.now().isoformat(),  # Use ISO 8601 format for timestamps
        'category': 'deep_web_research', # Add a category tag for easy filtering
        'status': 'new' # Add a status for workflow management
    }

    return categorized_data


def _store_intelligence_data(intel_id: str, categorized_data: Dict[str, Any]) -> None:
    """
    Securely stores intelligence data on disk
    
    Args:
        intel_id (str): The intelligence ID
        categorized_data (dict): The data to store
    """
    file_path = os.path.join(INTEL_STORE_PATH, f"{intel_id}.json")
    
    # Ensure the storage directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Store the data
    with open(file_path, 'w') as f:
        json.dump(categorized_data, f, indent=2)
    
    logger.info(f"Stored intelligence data with ID: {intel_id}")


def retrieve_intelligence(intel_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves intelligence data by ID
    
    Args:
        intel_id (str): The intelligence ID to retrieve
    
    Returns:
        dict or None: The intelligence data if found
    """
    file_path = os.path.join(INTEL_STORE_PATH, f"{intel_id}.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"Intelligence data with ID {intel_id} not found")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update access metadata
        data['metadata']['access_count'] += 1
        data['metadata']['last_accessed'] = datetime.now().isoformat()
        
        # Save the updated metadata
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        logger.error(f"Error retrieving intelligence data: {e}")
        return None


def search_intelligence(
    query: Dict[str, Any] = None,
    source_type: str = None,
    priority_level: str = None,
    tags: List[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Searches intelligence data based on criteria
    
    Args:
        query (dict): Specific data to search for
        source_type (str): Filter by source type
        priority_level (str): Filter by priority level
        tags (list): Filter by tags (any match)
        limit (int): Maximum number of results to return
    
    Returns:
        list: Matching intelligence entries
    """
    results = []
    
    # Validate filters
    if source_type and source_type not in SOURCE_TYPES:
        raise ValueError(f"Invalid source_type. Must be one of: {', '.join(SOURCE_TYPES)}")
    
    if priority_level and priority_level not in PRIORITY_LEVELS:
        raise ValueError(f"Invalid priority_level. Must be one of: {', '.join(PRIORITY_LEVELS)}")
    
    for filename in os.listdir(INTEL_STORE_PATH):
        if not filename.endswith('.json'):
            continue
        
        file_path = os.path.join(INTEL_STORE_PATH, filename)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Apply filters
            if source_type and data['metadata']['source_type'] != source_type:
                continue
                
            if priority_level and data['metadata']['priority_level'] != priority_level:
                continue
                
            if tags and not any(tag in data['metadata']['tags'] for tag in tags):
                continue
                
            if query:
                # Simple data matching - could be enhanced with more complex querying
                match = True
                for key, value in query.items():
                    keys = key.split('.')
                    current = data
                    for k in keys:
                        if k not in current:
                            match = False
                            break
                        current = current[k]
                    
                    if match and current != value:
                        match = False
                
                if not match:
                    continue
            
            results.append(data)
            
            if len(results) >= limit:
                break
                
        except Exception as e:
            logger.error(f"Error processing intelligence file {filename}: {e}")
    
    return results


def add_ioc(
    ioc_type: str,
    value: str,
    source: str,
    confidence: int,
    description: str = "",
    tags: List[str] = None,
    related_intel_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Adds an Indicator of Compromise (IOC) to the database
    
    Args:
        ioc_type (str): Type of IOC (e.g., 'ip', 'domain', 'hash', 'url')
        value (str): The actual IOC value
        source (str): Where the IOC was found
        confidence (int): Confidence score (0-100)
        description (str): Additional description
        tags (list): Optional list of tags
        related_intel_ids (list): Related intelligence IDs
    
    Returns:
        dict: The created IOC record
    """
    if confidence < 0 or confidence > 100:
        raise ValueError("Confidence must be between 0 and 100")
    
    # Generate a unique ID for the IOC
    ioc_id = generate_request_id()
    
    # Create IOC structure
    ioc = {
        "ioc_id": ioc_id,
        "type": ioc_type,
        "value": value,
        "source": source,
        "confidence": confidence,
        "description": description,
        "tags": tags or [],
        "related_intel_ids": related_intel_ids or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat(),
        "active": True
    }
    
    # Store the IOC
    file_path = os.path.join(THREAT_IOC_PATH, f"{ioc_id}.json")
    with open(file_path, 'w') as f:
        json.dump(ioc, f, indent=2)
    
    logger.info(f"Added new IOC {ioc_type}:{value} with ID: {ioc_id}")
    return ioc


def check_ioc(ioc_type: str, value: str) -> Dict[str, Any]:
    """
    Checks if a given value matches any known IOCs
    
    Args:
        ioc_type (str): Type of IOC to check
        value (str): The value to check
    
    Returns:
        dict: Matching IOCs with match details
    """
    matches = []
    
    for filename in os.listdir(THREAT_IOC_PATH):
        if not filename.endswith('.json'):
            continue
        
        file_path = os.path.join(THREAT_IOC_PATH, filename)
        
        try:
            with open(file_path, 'r') as f:
                ioc = json.load(f)
            
            if not ioc['active']:
                continue
                
            if ioc['type'] != ioc_type:
                continue
                
            # Exact matching for now, could be enhanced with regex, CIDR matching, etc.
            if ioc['value'] == value:
                # Update last seen time
                ioc['last_seen'] = datetime.now().isoformat()
                with open(file_path, 'w') as f:
                    json.dump(ioc, f, indent=2)
                    
                matches.append({
                    "ioc": ioc,
                    "match_type": "exact",
                    "match_time": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error processing IOC file {filename}: {e}")
    
    return {
        "matches": matches,
        "count": len(matches),
        "matched": len(matches) > 0
    }


def dispose_sensitive_data(intel_id: str, secure_delete: bool = False) -> bool:
    """
    Properly disposes of sensitive intelligence data
    
    Args:
        intel_id (str): The ID of the intelligence to dispose
        secure_delete (bool): Whether to use secure deletion
    
    Returns:
        bool: Success status
    """
    file_path = os.path.join(INTEL_STORE_PATH, f"{intel_id}.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"Intelligence data with ID {intel_id} not found for disposal")
        return False
    
    try:
        if secure_delete:
            # Overwrite with random data before deletion
            file_size = os.path.getsize(file_path)
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
            
        # Delete the file
        os.remove(file_path)
        logger.info(f"Successfully disposed of intelligence data with ID: {intel_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error disposing of intelligence data: {e}")
        return False


def generate_compliance_report() -> Dict[str, Any]:
    """
    Generates a compliance report for all stored intelligence
    
    Returns:
        dict: Compliance report data
    """
    intel_count = 0
    sources = {}
    priorities = {level: 0 for level in PRIORITY_LEVELS}
    oldest = None
    newest = None
    
    for filename in os.listdir(INTEL_STORE_PATH):
        if not filename.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(INTEL_STORE_PATH, filename), 'r') as f:
                data = json.load(f)
            
            intel_count += 1
            
            # Track source types
            source = data['metadata']['source_type']
            sources[source] = sources.get(source, 0) + 1
            
            # Track priorities
            priority = data['metadata']['priority_level']
            priorities[priority] += 1
            
            # Track dates
            timestamp = datetime.fromisoformat(data['metadata']['timestamp'])
            if oldest is None or timestamp < oldest:
                oldest = timestamp
            if newest is None or timestamp > newest:
                newest = timestamp
                
        except Exception:
            continue
    
    return {
        "generated_at": datetime.now().isoformat(),
        "intelligence_count": intel_count,
        "source_distribution": sources,
        "priority_distribution": priorities,
        "oldest_record": oldest.isoformat() if oldest else None,
        "newest_record": newest.isoformat() if newest else None,
        "storage_size_bytes": sum(os.path.getsize(os.path.join(INTEL_STORE_PATH, f)) 
                                for f in os.listdir(INTEL_STORE_PATH) 
                                if f.endswith('.json')),
        "ioc_count": len([f for f in os.listdir(THREAT_IOC_PATH) if f.endswith('.json')]),
    }


# STIX/TAXII integration functions

def connect_to_taxii_server() -> Optional[Server]:
    """
    Connect to the configured TAXII server.
    
    Returns:
        Optional[Server]: TAXII server connection or None if not available
    """
    global _taxii_server
    
    if not STIX_AVAILABLE:
        logger.warning("STIX/TAXII libraries not installed, skipping connection")
        return None
        
    if not TAXII_SERVER_URL:
        logger.warning("TAXII server URL not configured, skipping connection")
        return None
        
    if _taxii_server is not None:
        return _taxii_server
        
    try:
        if TAXII_USERNAME and TAXII_PASSWORD:
            _taxii_server = Server(
                TAXII_SERVER_URL,
                user=TAXII_USERNAME,
                password=TAXII_PASSWORD
            )
        else:
            _taxii_server = Server(TAXII_SERVER_URL)
            
        logger.info(f"Connected to TAXII server: {TAXII_SERVER_URL}")
        return _taxii_server
    except Exception as e:
        logger.error(f"Failed to connect to TAXII server: {str(e)}")
        return None

def get_taxii_collection() -> Optional[Collection]:
    """
    Get the configured TAXII collection.
    
    Returns:
        Optional[Collection]: TAXII collection or None if not available
    """
    global _taxii_collection
    
    if _taxii_collection is not None:
        return _taxii_collection
        
    server = connect_to_taxii_server()
    if not server:
        return None
        
    if not TAXII_COLLECTION_ID:
        logger.warning("TAXII collection ID not configured, skipping collection")
        return None
        
    try:
        for api_root in server.api_roots:
            for collection in api_root.collections:
                if collection.id == TAXII_COLLECTION_ID:
                    _taxii_collection = collection
                    logger.info(f"Found TAXII collection: {collection.title}")
                    return _taxii_collection
                    
        logger.warning(f"Could not find collection with ID: {TAXII_COLLECTION_ID}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving TAXII collection: {str(e)}")
        return None

def import_stix_indicators(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Import indicators from the TAXII server and convert to internal IOC format.
    
    Args:
        limit: Maximum number of indicators to import
        
    Returns:
        List[Dict[str, Any]]: List of imported indicators as IOCs
    """
    if not STIX_AVAILABLE:
        logger.warning("STIX/TAXII libraries not installed, skipping import")
        return []
        
    collection = get_taxii_collection()
    if not collection:
        return []
        
    imported_iocs = []
    
    try:
        # Get the indicators from the collection
        indicators = collection.get_objects(limit=limit, type="indicator")
        
        for indicator in indicators:
            if not hasattr(indicator, 'pattern'):
                continue
                
            # Extract the indicator value from the pattern
            # This is a simplified extraction and might need adjustment
            pattern = indicator.pattern
            ioc_value = None
            ioc_type = None
            
            if 'ipv4-addr' in pattern:
                ioc_type = 'ip'
                ioc_value = pattern.split("'")[1]
            elif 'domain-name' in pattern:
                ioc_type = 'domain'
                ioc_value = pattern.split("'")[1]
            elif 'url' in pattern:
                ioc_type = 'url'
                ioc_value = pattern.split("'")[1]
            elif 'file:hashes' in pattern and 'MD5' in pattern:
                ioc_type = 'file_hash'
                ioc_value = pattern.split("'")[1]
            
            if ioc_type and ioc_value:
                # Convert confidence from STIX to our scale (0-100)
                confidence = int(getattr(indicator, 'confidence', 50))
                
                # Add the IOC to our system
                try:
                    ioc = add_ioc(
                        ioc_type=ioc_type,
                        value=ioc_value,
                        source=f"TAXII:{collection.id}",
                        confidence=confidence,
                        description=getattr(indicator, 'description', ''),
                        tags=['stix_import']
                    )
                    imported_iocs.append(ioc)
                except Exception as e:
                    logger.error(f"Error importing IOC {ioc_value}: {str(e)}")
        
        logger.info(f"Imported {len(imported_iocs)} indicators from TAXII server")
        return imported_iocs
    except Exception as e:
        logger.error(f"Error getting indicators from TAXII server: {str(e)}")
        return []

def export_iocs_to_stix() -> Optional[str]:
    """
    Export our IOCs to STIX format.
    
    Returns:
        Optional[str]: Path to the exported STIX bundle file, or None on failure
    """
    if not STIX_AVAILABLE:
        logger.warning("STIX libraries not installed, skipping export")
        return None
        
    try:
        # Get all IOCs from our system
        ioc_types = ['ip', 'domain', 'url', 'file_hash']
        stix_objects = []
        
        for ioc_type in ioc_types:
            # Simulated function to get all IOCs of a specific type
            # In a real implementation, you would query your IOC storage
            iocs = []
            ioc_files = glob.glob(os.path.join(THREAT_IOC_PATH, f"{ioc_type}_*.json"))
            
            for ioc_file in ioc_files:
                try:
                    with open(ioc_file, 'r') as f:
                        ioc = json.load(f)
                        iocs.append(ioc)
                except Exception as e:
                    logger.error(f"Error loading IOC from {ioc_file}: {str(e)}")
            
            # Convert each IOC to a STIX indicator
            for ioc in iocs:
                try:
                    # Create a STIX pattern based on IOC type
                    if ioc_type == 'ip':
                        pattern = f"[ipv4-addr:value = '{ioc['value']}']"
                    elif ioc_type == 'domain':
                        pattern = f"[domain-name:value = '{ioc['value']}']"
                    elif ioc_type == 'url':
                        pattern = f"[url:value = '{ioc['value']}']"
                    elif ioc_type == 'file_hash':
                        pattern = f"[file:hashes.'MD5' = '{ioc['value']}']"
                    else:
                        continue
                    
                    # Create the STIX indicator
                    indicator = stix2.Indicator(
                        id=f"indicator--{str(uuid.uuid4())}",
                        created=datetime.utcnow(),
                        modified=datetime.utcnow(),
                        name=f"{ioc_type.upper()} - {ioc['value']}",
                        description=ioc.get('description', ''),
                        pattern_type="stix",
                        pattern=pattern,
                        valid_from=datetime.utcnow(),
                        confidence=ioc.get('confidence', 50)
                    )
                    
                    stix_objects.append(indicator)
                except Exception as e:
                    logger.error(f"Error converting IOC to STIX: {str(e)}")
        
        if not stix_objects:
            logger.warning("No IOCs to export")
            return None
        
        # Create a STIX bundle with all indicators
        bundle = stix2.Bundle(objects=stix_objects)
        
        # Save the bundle to a file
        export_path = os.path.join(INTEL_STORE_PATH, f"stix_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(export_path, 'w') as f:
            f.write(bundle.serialize(pretty=True))
        
        logger.info(f"Exported {len(stix_objects)} IOCs to STIX bundle: {export_path}")
        return export_path
    except Exception as e:
        logger.error(f"Error exporting IOCs to STIX: {str(e)}")
        return None

def correlate_threats(iocs: List[Dict[str, Any]], 
                     intel_data: List[Dict[str, Any]] = None,
                     threshold: float = 0.6,
                     max_correlations: int = 100) -> List[Dict[str, Any]]:
    """
    Advanced threat correlation function that combines IOCs with intelligence data
    to identify related threats and potential attack patterns.
    
    Args:
        iocs: List of Indicators of Compromise to correlate
        intel_data: Optional list of intelligence data entries to correlate against.
                   If None, will load from storage.
        threshold: Similarity threshold for correlation (0.0-1.0)
        max_correlations: Maximum number of correlations to return
        
    Returns:
        List of correlation results with associated threat context
    """
    logger.info(f"Correlating {len(iocs)} IOCs against intelligence data")
    
    # Load intelligence data if not provided
    if intel_data is None:
        intel_data = []
        # Load all intelligence files
        intel_files = glob.glob(os.path.join(INTEL_STORE_PATH, "*.json"))
        for file_path in intel_files[:500]:  # Limit to 500 files for performance
            try:
                with open(file_path, 'r') as f:
                    intel_data.append(json.load(f))
            except Exception as e:
                logger.error(f"Error loading intel file {file_path}: {e}")
    
    correlations = []
    
    # Create IOC lookup for faster reference
    ioc_lookup = {}
    for ioc in iocs:
        key = f"{ioc.get('type', 'unknown')}:{ioc.get('value', '')}"
        ioc_lookup[key] = ioc
    
    # Find correlations
    for intel in intel_data:
        # Skip if no technical data or IOCs in the intel
        if not intel.get('technical_data') or not intel.get('iocs'):
            continue
            
        matched_iocs = []
        total_score = 0.0
        
        # Check each IOC in the intel against our input IOCs
        for intel_ioc in intel.get('iocs', []):
            ioc_key = f"{intel_ioc.get('type', 'unknown')}:{intel_ioc.get('value', '')}"
            
            # Direct match
            if ioc_key in ioc_lookup:
                matched_iocs.append({
                    'input_ioc': ioc_lookup[ioc_key],
                    'intel_ioc': intel_ioc,
                    'match_type': 'exact',
                    'confidence': 1.0
                })
                total_score += 1.0
            else:
                # Partial matches for certain IOC types
                if intel_ioc.get('type') in ['domain', 'url', 'file_hash', 'email']:
                    for input_key, input_ioc in ioc_lookup.items():
                        # Skip if types don't match
                        if input_ioc.get('type') != intel_ioc.get('type'):
                            continue
                            
                        # Calculate similarity based on IOC type
                        similarity = 0.0
                        
                        if intel_ioc.get('type') == 'domain':
                            # Domain similarity (e.g., subdomain matches)
                            intel_domain = intel_ioc.get('value', '')
                            input_domain = input_ioc.get('value', '')
                            if intel_domain in input_domain or input_domain in intel_domain:
                                similarity = 0.7
                                
                        elif intel_ioc.get('type') == 'url':
                            # URL similarity
                            intel_url = intel_ioc.get('value', '')
                            input_url = input_ioc.get('value', '')
                            if intel_url in input_url or input_url in intel_url:
                                similarity = 0.6
                                
                        # Add more similarity calculations for other IOC types...
                        
                        if similarity >= threshold:
                            matched_iocs.append({
                                'input_ioc': input_ioc,
                                'intel_ioc': intel_ioc,
                                'match_type': 'partial',
                                'confidence': similarity
                            })
                            total_score += similarity
        
        # If we have matches, create a correlation result
        if matched_iocs:
            avg_score = total_score / len(matched_iocs)
            if avg_score >= threshold:
                correlation = {
                    'intel_id': intel.get('id'),
                    'title': intel.get('title'),
                    'source': intel.get('source'),
                    'priority': intel.get('priority'),
                    'matched_iocs': matched_iocs,
                    'correlation_score': avg_score,
                    'correlation_time': datetime.utcnow().isoformat(),
                    'tactics': intel.get('tactics', []),
                    'techniques': intel.get('techniques', []),
                    'threat_actors': intel.get('threat_actors', [])
                }
                correlations.append(correlation)
    
    # Sort by correlation score and limit results
    correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
    return correlations[:max_correlations]

def generate_threat_report(correlation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive threat report based on correlation results.
    
    Args:
        correlation_results: List of correlation results from correlate_threats
        
    Returns:
        Dict containing the threat report with actionable insights
    """
    if not correlation_results:
        return {
            "report_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "no_threats_detected",
            "summary": "No threats detected from the provided IOCs.",
            "details": {}
        }
    
    # Count threats by priority
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for result in correlation_results:
        priority = result.get('priority', 'Low')
        if priority in priority_counts:
            priority_counts[priority] += 1
    
    # Identify top threat actors
    threat_actors = {}
    for result in correlation_results:
        for actor in result.get('threat_actors', []):
            if actor in threat_actors:
                threat_actors[actor] += 1
            else:
                threat_actors[actor] = 1
    
    # Sort threat actors by frequency
    top_actors = [{"name": k, "count": v} for k, v in 
                 sorted(threat_actors.items(), key=lambda x: x[1], reverse=True)][:5]
    
    # Identify common TTPs (Tactics, Techniques, Procedures)
    tactics = {}
    techniques = {}
    
    for result in correlation_results:
        for tactic in result.get('tactics', []):
            if tactic in tactics:
                tactics[tactic] += 1
            else:
                tactics[tactic] = 1
                
        for technique in result.get('techniques', []):
            if technique in techniques:
                techniques[technique] += 1
            else:
                techniques[technique] = 1
    
    # Sort TTPs by frequency
    top_tactics = [{"name": k, "count": v} for k, v in 
                  sorted(tactics.items(), key=lambda x: x[1], reverse=True)][:5]
    top_techniques = [{"name": k, "count": v} for k, v in 
                     sorted(techniques.items(), key=lambda x: x[1], reverse=True)][:5]
    
    # Generate actionable recommendations based on findings
    recommendations = []
    
    # Add recommendations based on priority of findings
    if priority_counts["Critical"] > 0 or priority_counts["High"] > 0:
        recommendations.append({
            "priority": "Critical",
            "action": "Immediate remediation required",
            "details": f"Address {priority_counts['Critical']} critical and {priority_counts['High']} high severity findings"
        })
    
    # Add more context-specific recommendations
    if any(actor["name"].lower() in ["apt29", "apt28", "wizard spider"] for actor in top_actors):
        recommendations.append({
            "priority": "High",
            "action": "Nation-state actor detected",
            "details": "Engage incident response team and notify relevant authorities"
        })
    
    # Generate the final report
    threat_report = {
        "report_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "threats_detected" if correlation_results else "no_threats_detected",
        "summary": f"Detected {len(correlation_results)} potential threats with {priority_counts['Critical']} critical, {priority_counts['High']} high, {priority_counts['Medium']} medium, and {priority_counts['Low']} low severity findings.",
        "details": {
            "correlation_count": len(correlation_results),
            "priority_summary": priority_counts,
            "top_threat_actors": top_actors,
            "top_tactics": top_tactics,
            "top_techniques": top_techniques,
            "findings": correlation_results[:10],  # Include top 10 correlation results
            "recommendations": recommendations
        }
    }
    
    return threat_report

def generate_secure_credential(length: int = 32, complexity: str = 'high') -> str:
    """
    Generate a secure credential with specified length and complexity.
    
    Args:
        length: Length of the credential
        complexity: Complexity level ('medium', 'high', 'very_high')
        
    Returns:
        str: Generated credential
    """
    import string
    import secrets
    
    if complexity == 'medium':
        # Use alphanumeric characters
        alphabet = string.ascii_letters + string.digits
    elif complexity == 'high':
        # Use alphanumeric + some special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    elif complexity == 'very_high':
        # Use all printable ASCII characters except whitespace
        alphabet = string.ascii_letters + string.digits + string.punctuation
    else:
        # Default to high complexity
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    
    # Generate the credential
    credential = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return credential

def check_credential_expiration() -> List[Dict[str, Any]]:
    """
    Check if any credentials are approaching expiration.
    
    Returns:
        List[Dict[str, Any]]: List of credentials approaching expiration
    """
    global credential_metadata
    warnings = []
    now = datetime.now()
    
    # Ensure metadata is loaded
    if not credential_metadata:
        credential_metadata = load_credential_metadata()
    
    # Check each credential
    for cred_type, metadata in credential_metadata.items():
        if 'expiration_date' in metadata:
            try:
                expiration_date = datetime.fromisoformat(metadata['expiration_date'])
                days_remaining = (expiration_date - now).days
                
                # Get warning threshold for this credential type
                warning_days = CREDENTIAL_TYPES.get(cred_type, {}).get('warning_days', 14)
                
                if days_remaining <= 0:
                    # Credential has expired
                    warnings.append({
                        'type': cred_type,
                        'status': 'expired',
                        'expiration_date': metadata['expiration_date'],
                        'days_overdue': -days_remaining
                    })
                elif days_remaining <= warning_days:
                    # Credential is approaching expiration
                    warnings.append({
                        'type': cred_type,
                        'status': 'warning',
                        'expiration_date': metadata['expiration_date'],
                        'days_remaining': days_remaining
                    })
            except Exception as e:
                logger.error(f"Error checking expiration for {cred_type}: {e}")
    
    return warnings

def rotate_credential(credential_type: str, request_id: str) -> str:
    """
    Rotate a credential and generate a new secure key.
    
    Args:
        credential_type: Type of credential to rotate
        request_id: Unique identifier for this request
        
    Returns:
        str: New credential value
    """
    if credential_type not in CREDENTIAL_TYPES:
        raise ValueError(f"Invalid credential type: {credential_type}")
        
    config = CREDENTIAL_TYPES[credential_type]
    
    # Generate new secure key based on type
    if config['complexity'] == 'high':
        new_key = secrets.token_urlsafe(config['length'])
    else:
        new_key = secrets.token_hex(config['length'] // 2)
        
    # Store old key in history
    store_credential_history(credential_type, request_id)
    
    # Update credential in secure storage
    update_credential_storage(credential_type, new_key)
    
    logger.info(f"Rotated {credential_type} credential")
    return new_key

def init_credential_metadata():
    """
    Initialize credential metadata for all credential types.
    This should be called once during application startup.
    """
    global credential_metadata
    
    # Load existing metadata
    credential_metadata = load_credential_metadata()
    
    now = datetime.now()
    modified = False
    
    # Initialize metadata for each credential type
    for cred_type, config in CREDENTIAL_TYPES.items():
        if cred_type not in credential_metadata:
            rotation_interval = timedelta(days=config.get('rotation_interval_days', 90))
            
            # Create initial metadata
            credential_metadata[cred_type] = {
                'created_date': now.isoformat(),
                'expiration_date': (now + rotation_interval).isoformat(),
                'last_rotated': now.isoformat(),
                'rotations': 0,
                'masked_value': mask_credential(globals().get(cred_type, 'unknown'))
            }
            modified = True
    
    # Save if changes were made
    if modified:
        save_credential_metadata(credential_metadata)
        logger.info("Initialized credential metadata")

def schedule_credential_rotation():
    """
    Check for credentials that need rotation and schedule rotation tasks.
    This function should be called periodically, e.g., daily.
    
    Returns:
        List[Dict[str, Any]]: Credentials that were rotated
    """
    rotated_credentials = []
    warnings = check_credential_expiration()
    
    for warning in warnings:
        if warning['status'] == 'expired':
            try:
                # Rotate expired credential
                rotation_result = rotate_credential(warning['type'], generate_request_id())
                rotated_credentials.append(rotation_result)
                
                logger.warning(
                    f"Automatically rotated expired credential: {warning['type']}, "
                    f"was {warning['days_overdue']} days overdue"
                )
            except Exception as e:
                logger.error(f"Error rotating expired credential {warning['type']}: {e}")
    
    return rotated_credentials

# Initialize credential metadata at module load time
init_credential_metadata()

# Enhanced threat detection
def detect_threats(request_data: Dict[str, Any], request_id: str) -> bool:
    """
    Detect potential security threats in request data.
    
    Args:
        request_data: Request data to analyze
        request_id: Unique identifier for this request
        
    Returns:
        bool: True if threat detected, False otherwise
    """
    threats_detected = False
    
    # Check for suspicious patterns
    for pattern in THREAT_DETECTION_CONFIG['suspicious_patterns']:
        if re.search(pattern, str(request_data), re.IGNORECASE):
            logger.warning(f"Threat detected: Suspicious pattern {pattern} in request {request_id}")
            threats_detected = True
            break
            
    # Check for rate limiting violations
    if not check_rate_limits(request_data.get('client_ip', 'unknown')):
        logger.warning(f"Rate limit violation detected for request {request_id}")
        threats_detected = True
        
    # Check for unusual behavior
    if detect_unusual_behavior(request_data):
        logger.warning(f"Unusual behavior detected in request {request_id}")
        threats_detected = True
        
    return threats_detected

# Enhanced credential validation
def validate_credential(credential: str, credential_type: str, request_id: str) -> bool:
    """
    Validate a credential with enhanced security checks.
    
    Args:
        credential: Credential to validate
        credential_type: Type of credential
        request_id: Unique identifier for this request
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not credential:
        return False
        
    # Basic format validation
    if not re.match(r'^[A-Za-z0-9-_]+$', credential):
        return False
        
    # Length validation
    if len(credential) < CREDENTIAL_TYPES[credential_type]['length']:
        return False
        
    # Complexity validation
    if not validate_complexity(credential, credential_type):
        return False
        
    # Check for common patterns
    if has_common_patterns(credential):
        return False
        
    # Check against known compromised credentials
    if is_compromised(credential):
        return False
        
    return True

__all__ = [
    'generate_request_id',
    'mask_credential',
    'log_credential_usage',
    'verify_api_key',
    'verify_db_password',
    'verify_mail_api_key',
    'verify_logging_api_key',
    'get_recent_usage',
    'analyze_for_suspicious_activity',
    'is_ip_trusted',
    'create_security_middleware',
    'categorize_intelligence',
    'retrieve_intelligence',
    'search_intelligence',
    'add_ioc',
    'check_ioc',
    'dispose_sensitive_data',
    'generate_compliance_report',
    'connect_to_taxii_server',
    'get_taxii_collection',
    'import_stix_indicators',
    'export_iocs_to_stix',
    'correlate_threats',
    'generate_threat_report',
    'generate_secure_credential',
    'check_credential_expiration',
    'rotate_credential',
    'init_credential_metadata',
    'schedule_credential_rotation',
    'detect_threats',
    'validate_credential'
] 