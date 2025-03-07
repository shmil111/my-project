#!/usr/bin/env python3
"""
Data sharing module for myproject, enabling secure data export, import, and synchronization
between systems through a REST API.
"""
import os
import json
import uuid
import time
import hashlib
import logging
import hmac
import base64
import csv
import io
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for data sharing
DATA_SHARE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'shared')
SHARE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'data', 'share_tokens')
WEBHOOK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'webhooks')

# Create directories if they don't exist
os.makedirs(DATA_SHARE_PATH, exist_ok=True)
os.makedirs(SHARE_TOKEN_PATH, exist_ok=True)
os.makedirs(WEBHOOK_CONFIG_PATH, exist_ok=True)

# Supported export formats
EXPORT_FORMATS = ['json', 'csv', 'stix']

# Rate limiting settings
RATE_LIMITS = {
    'default': {
        'requests_per_minute': 60,
        'requests_per_day': 1000
    },
    'partner': {
        'requests_per_minute': 300,
        'requests_per_day': 5000
    },
    'enterprise': {
        'requests_per_minute': 600, 
        'requests_per_day': 10000
    }
}

# In-memory cache for rate limiting
rate_limit_cache = {}

# Custom exception for data sharing errors
class DataSharingError(Exception):
    """Custom exception for data sharing errors"""
    pass

def generate_share_token(
    name: str,
    tier: str = 'default',
    expires_in_days: int = 30,
    allowed_datasets: List[str] = None,
    allowed_formats: List[str] = None,
    source_ip: str = None
) -> Dict[str, Any]:
    """
    Generate a secure token for data sharing access.
    
    Args:
        name: Identifier for the token (e.g., partner name, system name)
        tier: Access tier for rate limiting ('default', 'partner', 'enterprise')
        expires_in_days: Number of days until token expires
        allowed_datasets: List of dataset IDs this token can access
        allowed_formats: List of formats this token can export data in
        source_ip: Optional IP restriction for using this token
    
    Returns:
        Dict containing token details including the token itself
    """
    if tier not in RATE_LIMITS:
        tier = 'default'
    
    if not allowed_datasets:
        allowed_datasets = ['intel', 'iocs', 'reports']
        
    if not allowed_formats:
        allowed_formats = ['json', 'csv']

    # Generate a secure random token
    token_bytes = os.urandom(32)
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    # Calculate expiration time
    now = datetime.utcnow()
    expires_at = now + timedelta(days=expires_in_days)
    
    token_data = {
        'id': str(uuid.uuid4()),
        'name': name,
        'token': token,
        'tier': tier,
        'created_at': now.isoformat(),
        'expires_at': expires_at.isoformat(),
        'allowed_datasets': allowed_datasets,
        'allowed_formats': allowed_formats,
        'source_ip': source_ip,
        'last_used': None,
        'usage_count': 0
    }
    
    # Save token to file
    token_file = os.path.join(SHARE_TOKEN_PATH, f"{token_data['id']}.json")
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    return token_data

def validate_share_token(token: str, dataset: str, format: str = None, source_ip: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a data sharing token.
    
    Args:
        token: The token to validate
        dataset: The dataset being accessed
        format: The export format being requested (optional)
        source_ip: The source IP of the request (optional)
    
    Returns:
        Tuple of (is_valid, token_data)
    """
    # Look through all token files to find matching token
    for token_file in os.listdir(SHARE_TOKEN_PATH):
        if not token_file.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(SHARE_TOKEN_PATH, token_file), 'r') as f:
                token_data = json.load(f)
                
                # Check if token matches
                if token_data.get('token') != token:
                    continue
                    
                # Check if token is expired
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    logger.warning(f"Token {token_data['id']} is expired")
                    return False, {}
                
                # Check dataset access
                if dataset not in token_data['allowed_datasets']:
                    logger.warning(f"Token {token_data['id']} not authorized for dataset {dataset}")
                    return False, {}
                
                # Check format if specified
                if format and format not in token_data['allowed_formats']:
                    logger.warning(f"Token {token_data['id']} not authorized for format {format}")
                    return False, {}
                
                # Check source IP if restricted
                if token_data.get('source_ip') and source_ip and token_data['source_ip'] != source_ip:
                    logger.warning(f"Token {token_data['id']} not authorized from IP {source_ip}")
                    return False, {}
                
                # Update usage information
                token_data['last_used'] = datetime.utcnow().isoformat()
                token_data['usage_count'] += 1
                
                # Save updated token data
                with open(os.path.join(SHARE_TOKEN_PATH, token_file), 'w') as f_update:
                    json.dump(token_data, f_update, indent=2)
                
                return True, token_data
                
        except Exception as e:
            logger.error(f"Error validating token file {token_file}: {e}")
    
    return False, {}

def check_rate_limit(token_data: Dict[str, Any], source_ip: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if the request is within rate limits.
    
    Args:
        token_data: The token data dictionary
        source_ip: Source IP of the request
    
    Returns:
        Tuple of (is_allowed, limit_info)
    """
    # Get tier rate limits
    tier = token_data.get('tier', 'default')
    limits = RATE_LIMITS.get(tier, RATE_LIMITS['default'])
    
    # Create cache key
    cache_key = f"{token_data['id']}:{source_ip}"
    
    # Get current time
    now = time.time()
    current_minute = int(now / 60)
    current_day = int(now / 86400)
    
    # Initialize if not in cache
    if cache_key not in rate_limit_cache:
        rate_limit_cache[cache_key] = {
            'minute_count': 0,
            'day_count': 0,
            'current_minute': current_minute,
            'current_day': current_day
        }
    
    # Reset counters if we're in a new time period
    cache_data = rate_limit_cache[cache_key]
    if cache_data['current_minute'] != current_minute:
        cache_data['minute_count'] = 0
        cache_data['current_minute'] = current_minute
    
    if cache_data['current_day'] != current_day:
        cache_data['day_count'] = 0
        cache_data['current_day'] = current_day
    
    # Increment counters
    cache_data['minute_count'] += 1
    cache_data['day_count'] += 1
    
    # Check against limits
    minute_limit = limits['requests_per_minute']
    day_limit = limits['requests_per_day']
    
    is_allowed = True
    limit_info = {
        'minute_limit': minute_limit,
        'minute_current': cache_data['minute_count'],
        'day_limit': day_limit,
        'day_current': cache_data['day_count']
    }
    
    if cache_data['minute_count'] > minute_limit:
        is_allowed = False
        limit_info['exceeded'] = 'minute_limit'
    elif cache_data['day_count'] > day_limit:
        is_allowed = False
        limit_info['exceeded'] = 'day_limit'
    
    return is_allowed, limit_info

def export_data(dataset: str, format: str = 'json', filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export data from a specific dataset in the requested format.
    
    Args:
        dataset: Dataset ID to export ('intel', 'iocs', 'reports')
        format: Format to export ('json', 'csv', 'stix')
        filters: Optional filters to apply to the dataset
    
    Returns:
        Dict containing export details and data
    """
    # Validate dataset and format
    if dataset not in ['intel', 'iocs', 'reports']:
        raise DataSharingError(f"Invalid dataset: {dataset}")
    
    if format not in EXPORT_FORMATS:
        raise DataSharingError(f"Invalid export format: {format}")
    
    # Define paths based on dataset
    if dataset == 'intel':
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'intel')
    elif dataset == 'iocs':
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'iocs')
    elif dataset == 'reports':
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'reports')
    
    # Collect data from files
    data_items = []
    for file_name in os.listdir(data_path):
        if not file_name.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(data_path, file_name), 'r') as f:
                item = json.load(f)
                
                # Apply filters if provided
                if filters:
                    include_item = True
                    for key, value in filters.items():
                        if key in item:
                            if isinstance(value, list) and item[key] not in value:
                                include_item = False
                                break
                            elif item[key] != value:
                                include_item = False
                                break
                    
                    if not include_item:
                        continue
                
                data_items.append(item)
        except Exception as e:
            logger.error(f"Error loading data file {file_name}: {e}")
    
    # Generate export ID
    export_id = str(uuid.uuid4())
    
    # Process data based on format
    if format == 'json':
        export_data = data_items
        export_content = json.dumps(export_data, indent=2)
        content_type = 'application/json'
    
    elif format == 'csv':
        if not data_items:
            export_content = ""
            content_type = 'text/csv'
        else:
            # Extract headers from first item
            headers = list(data_items[0].keys())
            
            # Create CSV data
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            
            for item in data_items:
                # Ensure all complex objects are converted to strings
                row = {}
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
                writer.writerow(row)
            
            export_content = output.getvalue()
            content_type = 'text/csv'
    
    elif format == 'stix':
        # This would implement STIX format conversion
        # For simplicity, we're just returning JSON with a STIX note
        export_data = {
            "stix_version": "2.1",
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": data_items
        }
        export_content = json.dumps(export_data, indent=2)
        content_type = 'application/json'
    
    # Save export to shared directory
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    export_filename = f"{dataset}_{timestamp}_{format}.{format}"
    export_path = os.path.join(DATA_SHARE_PATH, export_filename)
    
    with open(export_path, 'w') as f:
        f.write(export_content)
    
    # Create export result
    result = {
        'export_id': export_id,
        'dataset': dataset,
        'format': format,
        'timestamp': datetime.utcnow().isoformat(),
        'count': len(data_items),
        'filename': export_filename,
        'content_type': content_type,
        'content': export_content
    }
    
    return result

def mask_secret(secret: str) -> str:
    """Mask a secret value for display purposes."""
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]

def register_webhook(
    name: str,
    url: str,
    datasets: List[str],
    events: List[str],
    secret: str = None
) -> Dict[str, Any]:
    """
    Register a webhook for data updates.
    
    Args:
        name: Friendly name for the webhook
        url: URL to call when events occur
        datasets: List of datasets to watch ('intel', 'iocs', 'reports')
        events: List of events to trigger on ('create', 'update', 'delete')
        secret: Secret key for signing webhook payloads
    
    Returns:
        Dict containing webhook configuration
    """
    # Validate datasets
    for dataset in datasets:
        if dataset not in ['intel', 'iocs', 'reports']:
            raise DataSharingError(f"Invalid dataset: {dataset}")
    
    # Validate events
    for event in events:
        if event not in ['create', 'update', 'delete']:
            raise DataSharingError(f"Invalid event: {event}")
    
    # Generate webhook ID and secret if not provided
    webhook_id = str(uuid.uuid4())
    if not secret:
        secret = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    
    webhook_data = {
        'id': webhook_id,
        'name': name,
        'url': url,
        'datasets': datasets,
        'events': events,
        'secret': secret,
        'created_at': datetime.utcnow().isoformat(),
        'last_triggered': None,
        'trigger_count': 0,
        'active': True
    }
    
    # Save webhook configuration
    webhook_file = os.path.join(WEBHOOK_CONFIG_PATH, f"{webhook_id}.json")
    with open(webhook_file, 'w') as f:
        json.dump(webhook_data, f, indent=2)
    
    # Don't include secret in return value for security
    result = webhook_data.copy()
    result['secret'] = mask_secret(secret)
    
    return result

def trigger_webhooks(dataset: str, event: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Trigger registered webhooks for a specific dataset and event.
    
    Args:
        dataset: The dataset that was modified
        event: The event that occurred ('create', 'update', 'delete')
        data: The data associated with the event
    
    Returns:
        List of webhook trigger results
    """
    import requests
    
    results = []
    
    # Look for matching webhooks
    for webhook_file in os.listdir(WEBHOOK_CONFIG_PATH):
        if not webhook_file.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(WEBHOOK_CONFIG_PATH, webhook_file), 'r') as f:
                webhook = json.load(f)
                
                # Skip inactive webhooks
                if not webhook.get('active', True):
                    continue
                
                # Check if this webhook should be triggered
                if dataset in webhook['datasets'] and event in webhook['events']:
                    # Prepare payload
                    payload = {
                        'webhook_id': webhook['id'],
                        'dataset': dataset,
                        'event': event,
                        'timestamp': datetime.utcnow().isoformat(),
                        'data': data
                    }
                    
                    # Create signature if secret is available
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': 'MyProject-Webhook-Trigger/1.0'
                    }
                    
                    if webhook.get('secret'):
                        payload_str = json.dumps(payload)
                        signature = hmac.new(
                            webhook['secret'].encode(), 
                            payload_str.encode(),
                            hashlib.sha256
                        ).hexdigest()
                        headers['X-Webhook-Signature'] = signature
                    
                    # Send webhook request
                    try:
                        response = requests.post(
                            webhook['url'],
                            json=payload,
                            headers=headers,
                            timeout=5
                        )
                        
                        success = 200 <= response.status_code < 300
                        
                        result = {
                            'webhook_id': webhook['id'],
                            'success': success,
                            'status_code': response.status_code,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        # Update webhook stats
                        webhook['last_triggered'] = datetime.utcnow().isoformat()
                        webhook['trigger_count'] += 1
                        
                        with open(os.path.join(WEBHOOK_CONFIG_PATH, webhook_file), 'w') as f_update:
                            json.dump(webhook, f_update, indent=2)
                        
                    except Exception as e:
                        result = {
                            'webhook_id': webhook['id'],
                            'success': False,
                            'error': str(e),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    
                    results.append(result)
                
        except Exception as e:
            logger.error(f"Error processing webhook file {webhook_file}: {e}")
    
    return results

def get_active_webhooks() -> List[Dict[str, Any]]:
    """Get all active webhooks with sensitive data masked."""
    webhooks = []
    
    for webhook_file in os.listdir(WEBHOOK_CONFIG_PATH):
        if not webhook_file.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(WEBHOOK_CONFIG_PATH, webhook_file), 'r') as f:
                webhook = json.load(f)
                
                # Mask secret
                if 'secret' in webhook:
                    webhook['secret'] = mask_secret(webhook['secret'])
                
                webhooks.append(webhook)
                
        except Exception as e:
            logger.error(f"Error reading webhook file {webhook_file}: {e}")
    
    return webhooks

def list_webhooks(
    dataset: str = None,
    event: str = None,
    active_only: bool = False,
    include_secrets: bool = False
) -> List[Dict[str, Any]]:
    """
    List registered webhooks with optional filtering.
    
    Args:
        dataset: Filter by dataset ('intel', 'iocs', 'reports')
        event: Filter by event ('create', 'update', 'delete')
        active_only: Only return active webhooks
        include_secrets: Include webhook secrets in response (default: False)
    
    Returns:
        List of webhook configurations
    """
    webhooks = []
    
    # Look through all webhook files
    for webhook_file in os.listdir(WEBHOOK_CONFIG_PATH):
        if not webhook_file.endswith('.json'):
            continue
            
        try:
            with open(os.path.join(WEBHOOK_CONFIG_PATH, webhook_file), 'r') as f:
                webhook = json.load(f)
                
                # Apply filters
                if active_only and not webhook.get('active', True):
                    continue
                    
                if dataset and dataset not in webhook['datasets']:
                    continue
                    
                if event and event not in webhook['events']:
                    continue
                
                # Create result dict
                result = webhook.copy()
                
                # Mask secret unless explicitly requested
                if not include_secrets and 'secret' in result:
                    result['secret'] = mask_secret(result['secret'])
                
                webhooks.append(result)
                
        except Exception as e:
            logger.error(f"Error reading webhook file {webhook_file}: {e}")
    
    return webhooks

def update_webhook(
    webhook_id: str,
    name: str = None,
    url: str = None,
    datasets: List[str] = None,
    events: List[str] = None,
    secret: str = None,
    active: bool = None
) -> Dict[str, Any]:
    """
    Update an existing webhook configuration.
    
    Args:
        webhook_id: ID of the webhook to update
        name: New name for the webhook
        url: New URL for the webhook
        datasets: New list of datasets to watch
        events: New list of events to trigger on
        secret: New secret key for signing
        active: New active status
    
    Returns:
        Updated webhook configuration
    """
    webhook_file = os.path.join(WEBHOOK_CONFIG_PATH, f"{webhook_id}.json")
    
    if not os.path.exists(webhook_file):
        raise DataSharingError(f"Webhook {webhook_id} not found")
    
    try:
        with open(webhook_file, 'r') as f:
            webhook = json.load(f)
        
        # Update fields if provided
        if name is not None:
            webhook['name'] = name
            
        if url is not None:
            webhook['url'] = url
            
        if datasets is not None:
            # Validate datasets
            for dataset in datasets:
                if dataset not in ['intel', 'iocs', 'reports']:
                    raise DataSharingError(f"Invalid dataset: {dataset}")
            webhook['datasets'] = datasets
            
        if events is not None:
            # Validate events
            for event in events:
                if event not in ['create', 'update', 'delete']:
                    raise DataSharingError(f"Invalid event: {event}")
            webhook['events'] = events
            
        if secret is not None:
            webhook['secret'] = secret
            
        if active is not None:
            webhook['active'] = active
        
        # Save updated configuration
        with open(webhook_file, 'w') as f:
            json.dump(webhook, f, indent=2)
        
        # Return masked version
        result = webhook.copy()
        result['secret'] = mask_secret(result.get('secret', ''))
        return result
        
    except Exception as e:
        logger.error(f"Error updating webhook {webhook_id}: {e}")
        raise DataSharingError(f"Failed to update webhook: {str(e)}")

def delete_webhook(webhook_id: str) -> bool:
    """
    Delete a webhook configuration.
    
    Args:
        webhook_id: ID of the webhook to delete
    
    Returns:
        True if webhook was deleted, False otherwise
    """
    webhook_file = os.path.join(WEBHOOK_CONFIG_PATH, f"{webhook_id}.json")
    
    if not os.path.exists(webhook_file):
        return False
    
    try:
        os.remove(webhook_file)
        return True
    except Exception as e:
        logger.error(f"Error deleting webhook {webhook_id}: {e}")
        return False

def get_webhook_stats(webhook_id: str) -> Dict[str, Any]:
    """
    Get statistics for a specific webhook.
    
    Args:
        webhook_id: ID of the webhook to get stats for
    
    Returns:
        Dictionary containing webhook statistics
    """
    webhook_file = os.path.join(WEBHOOK_CONFIG_PATH, f"{webhook_id}.json")
    
    if not os.path.exists(webhook_file):
        raise DataSharingError(f"Webhook {webhook_id} not found")
    
    try:
        with open(webhook_file, 'r') as f:
            webhook = json.load(f)
        
        return {
            'id': webhook['id'],
            'name': webhook['name'],
            'created_at': webhook['created_at'],
            'last_triggered': webhook.get('last_triggered'),
            'trigger_count': webhook.get('trigger_count', 0),
            'active': webhook.get('active', True),
            'datasets': webhook['datasets'],
            'events': webhook['events']
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for webhook {webhook_id}: {e}")
        raise DataSharingError(f"Failed to get webhook stats: {str(e)}") 