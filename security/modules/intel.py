#!/usr/bin/env python3
"""
Intelligence data management module for storing and retrieving intelligence data.
"""
import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Import from local modules
from .utils import INTEL_STORE_PATH, THREAT_IOC_PATH, dispose_sensitive_data

# Set up logging
logger = logging.getLogger(__name__)

def categorize_intelligence(data: Dict[str, Any], source_type: str, priority_level: str) -> Dict[str, Any]:
    """
    Categorize and preprocess intelligence data.
    
    Args:
        data: Intelligence data to categorize
        source_type: Type of intelligence source
        priority_level: Priority level ('low', 'medium', 'high', 'critical')
        
    Returns:
        Categorized and preprocessed data
    """
    # Validate priority level
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if priority_level not in valid_priorities:
        logger.warning(f"Invalid priority level: {priority_level}, defaulting to 'medium'")
        priority_level = 'medium'
    
    # Current timestamp
    timestamp = datetime.now().isoformat()
    
    # Add metadata
    categorized_data = {
        **data,
        'metadata': {
            'source_type': source_type,
            'priority_level': priority_level,
            'ingestion_timestamp': timestamp,
            'last_updated': timestamp,
            'version': 1,
        }
    }
    
    # Add tags if not present
    if 'tags' not in categorized_data:
        categorized_data['tags'] = []
    
    # Add source type as a tag if not present
    if source_type not in categorized_data['tags']:
        categorized_data['tags'].append(source_type)
    
    # Add priority level as a tag if not present
    priority_tag = f"priority:{priority_level}"
    if priority_tag not in categorized_data['tags']:
        categorized_data['tags'].append(priority_tag)
    
    return categorized_data

def _store_intelligence_data(intel_id: str, categorized_data: Dict[str, Any]) -> None:
    """
    Store intelligence data to a file.
    
    Args:
        intel_id: Intelligence ID
        categorized_data: Preprocessed intelligence data
    """
    # Create file path
    file_path = os.path.join(INTEL_STORE_PATH, f"{intel_id}.json")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(categorized_data, f, indent=2)
        logger.info(f"Stored intelligence data: {intel_id}")
    except Exception as e:
        logger.error(f"Error storing intelligence data: {e}")
        raise

def retrieve_intelligence(intel_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve intelligence data by ID.
    
    Args:
        intel_id: Intelligence ID to retrieve
        
    Returns:
        Intelligence data or None if not found
    """
    file_path = os.path.join(INTEL_STORE_PATH, f"{intel_id}.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"Intelligence data not found: {intel_id}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            intel_data = json.load(f)
        return intel_data
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
    Search for intelligence data.
    
    Args:
        query: Query parameters to match
        source_type: Source type to filter
        priority_level: Priority level to filter
        tags: Tags to filter
        limit: Maximum number of results to return
        
    Returns:
        List of matching intelligence data
    """
    # Default query to empty dict
    query = query or {}
    tags = tags or []
    
    # Get all intelligence files
    intel_files = glob.glob(os.path.join(INTEL_STORE_PATH, "*.json"))
    
    results = []
    
    for file_path in intel_files:
        try:
            with open(file_path, 'r') as f:
                intel_data = json.load(f)
            
            # Filter by source type
            if source_type and intel_data.get('metadata', {}).get('source_type') != source_type:
                continue
            
            # Filter by priority level
            if priority_level and intel_data.get('metadata', {}).get('priority_level') != priority_level:
                continue
            
            # Filter by tags
            if tags:
                intel_tags = intel_data.get('tags', [])
                if not all(tag in intel_tags for tag in tags):
                    continue
            
            # Filter by custom query
            match = True
            for key, value in query.items():
                # Handle nested keys with dot notation
                if '.' in key:
                    parts = key.split('.')
                    current = intel_data
                    for part in parts[:-1]:
                        if part not in current:
                            match = False
                            break
                        current = current[part]
                    
                    if match and parts[-1] not in current or current[parts[-1]] != value:
                        match = False
                else:
                    if key not in intel_data or intel_data[key] != value:
                        match = False
            
            if match:
                # Get intel ID from filename
                intel_id = os.path.basename(file_path).replace('.json', '')
                results.append({
                    'intel_id': intel_id,
                    **intel_data
                })
                
                # Check limit
                if len(results) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Error processing intelligence file {file_path}: {e}")
    
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
    Add an Indicator of Compromise (IOC).
    
    Args:
        ioc_type: Type of IOC (ip, domain, hash, url, etc.)
        value: Value of the IOC
        source: Source of the IOC
        confidence: Confidence level (0-100)
        description: Description of the IOC
        tags: Tags to associate with the IOC
        related_intel_ids: Related intelligence IDs
        
    Returns:
        Added IOC data
    """
    # Validate IOC type
    valid_types = ['ip', 'domain', 'hash', 'url', 'email', 'file', 'custom']
    if ioc_type not in valid_types:
        logger.warning(f"Invalid IOC type: {ioc_type}, defaulting to 'custom'")
        ioc_type = 'custom'
    
    # Validate confidence
    if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
        logger.warning(f"Invalid confidence: {confidence}, clamping to [0, 100]")
        confidence = max(0, min(confidence, 100))
    
    # Default values
    tags = tags or []
    related_intel_ids = related_intel_ids or []
    
    # Generate IOC ID from type and value
    ioc_id = f"{ioc_type}_{value.replace('.', '_').replace(':', '_').replace('/', '_')}"
    
    # Create IOC data
    ioc_data = {
        'ioc_id': ioc_id,
        'ioc_type': ioc_type,
        'value': value,
        'source': source,
        'confidence': confidence,
        'description': description,
        'tags': tags,
        'related_intel_ids': related_intel_ids,
        'timestamp': datetime.now().isoformat(),
    }
    
    # Store IOC data
    file_path = os.path.join(THREAT_IOC_PATH, f"{ioc_id}.json")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(ioc_data, f, indent=2)
        logger.info(f"Added IOC: {ioc_id}")
        return ioc_data
    except Exception as e:
        logger.error(f"Error adding IOC: {e}")
        raise

def check_ioc(ioc_type: str, value: str) -> Dict[str, Any]:
    """
    Check if an IOC exists and retrieve its data.
    
    Args:
        ioc_type: Type of IOC
        value: Value of the IOC
        
    Returns:
        IOC data if exists, or empty dict if not
    """
    # Generate IOC ID
    ioc_id = f"{ioc_type}_{value.replace('.', '_').replace(':', '_').replace('/', '_')}"
    
    # Check if IOC exists
    file_path = os.path.join(THREAT_IOC_PATH, f"{ioc_id}.json")
    
    if not os.path.exists(file_path):
        # Also search by value in case the ID format changed
        found_files = glob.glob(os.path.join(THREAT_IOC_PATH, "*.json"))
        for found_path in found_files:
            try:
                with open(found_path, 'r') as f:
                    data = json.load(f)
                if data.get('ioc_type') == ioc_type and data.get('value') == value:
                    return data
            except Exception as e:
                logger.error(f"Error checking IOC file {found_path}: {e}")
        
        # Not found
        return {}
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error checking IOC: {e}")
        return {}
