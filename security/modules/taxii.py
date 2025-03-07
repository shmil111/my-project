#!/usr/bin/env python3
"""
TAXII client module for integrating with STIX/TAXII threat intelligence platforms.
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Import from local modules
from .utils import INTEL_STORE_PATH
from .intel import categorize_intelligence, _store_intelligence_data

# Set up logging
logger = logging.getLogger(__name__)

# Check if STIX/TAXII is available
try:
    import stix2
    from taxii2client.v20 import Server, Collection
    STIX_AVAILABLE = True
except ImportError:
    logger.warning("STIX/TAXII libraries not available. TAXII integration disabled.")
    STIX_AVAILABLE = False

# TAXII server configurations
TAXII_CONFIGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'taxii_configs')
os.makedirs(TAXII_CONFIGS_PATH, exist_ok=True)

class TAXIIClient:
    """Client for connecting to TAXII servers and retrieving intelligence."""
    
    def __init__(self, config_name: str = None):
        """
        Initialize TAXII client.
        
        Args:
            config_name: Name of configuration to use (or None for default)
        """
        if not STIX_AVAILABLE:
            raise ImportError("STIX/TAXII libraries not available. Please install 'stix2' and 'taxii2-client'.")
        
        self.connections = {}
        self.collections = {}
        
        # Load configuration
        if config_name:
            self.load_config(config_name)
    
    def load_config(self, config_name: str) -> bool:
        """
        Load TAXII server configuration.
        
        Args:
            config_name: Name of configuration to load
            
        Returns:
            True if loaded successfully, False otherwise
        """
        config_path = os.path.join(TAXII_CONFIGS_PATH, f"{config_name}.json")
        
        if not os.path.exists(config_path):
            logger.error(f"TAXII configuration not found: {config_name}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Store configuration
            self.config = config
            
            # Initialize connections for all servers in config
            for server_id, server_config in config.get('servers', {}).items():
                self._init_server_connection(server_id, server_config)
            
            logger.info(f"Loaded TAXII configuration: {config_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading TAXII configuration: {e}")
            return False
    
    def _init_server_connection(self, server_id: str, server_config: Dict[str, Any]) -> bool:
        """
        Initialize connection to a TAXII server.
        
        Args:
            server_id: Server identifier
            server_config: Server configuration
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Create server connection
            server_url = server_config.get('url')
            if not server_url:
                logger.error(f"Missing URL in server configuration: {server_id}")
                return False
            
            # Check for authentication
            auth = None
            auth_type = server_config.get('auth_type')
            
            if auth_type == 'basic':
                from requests.auth import HTTPBasicAuth
                username = server_config.get('username')
                password = server_config.get('password')
                
                if username and password:
                    auth = HTTPBasicAuth(username, password)
                else:
                    logger.warning(f"Missing credentials for basic auth: {server_id}")
            
            # Connect to server
            server = Server(server_url, auth=auth)
            
            # Store server connection
            self.connections[server_id] = {
                'server': server,
                'config': server_config,
                'connected_at': datetime.now().isoformat()
            }
            
            # Initialize collections if specified
            collection_ids = server_config.get('collections', [])
            
            if collection_ids and collection_ids != 'auto':
                for collection_id in collection_ids:
                    self._init_collection(server_id, collection_id)
            elif collection_ids == 'auto':
                # Discover and initialize all available collections
                for api_root in server.api_roots:
                    for collection in api_root.collections:
                        self._init_collection(server_id, collection.id)
            
            logger.info(f"Connected to TAXII server: {server_id} ({server_url})")
            return True
        except Exception as e:
            logger.error(f"Error connecting to TAXII server {server_id}: {e}")
            return False
    
    def _init_collection(self, server_id: str, collection_id: str) -> bool:
        """
        Initialize a TAXII collection.
        
        Args:
            server_id: Server identifier
            collection_id: Collection identifier
            
        Returns:
            True if initialized successfully, False otherwise
        """
        if server_id not in self.connections:
            logger.error(f"Server not connected: {server_id}")
            return False
        
        try:
            # Get server
            server_connection = self.connections[server_id]
            server = server_connection['server']
            
            # Find collection
            for api_root in server.api_roots:
                for collection in api_root.collections:
                    if collection.id == collection_id:
                        # Store collection
                        collection_key = f"{server_id}:{collection_id}"
                        self.collections[collection_key] = {
                            'collection': collection,
                            'api_root': api_root,
                            'server_id': server_id,
                            'collection_id': collection_id
                        }
                        
                        logger.info(f"Initialized TAXII collection: {collection_key}")
                        return True
            
            logger.warning(f"Collection not found: {collection_id} on server {server_id}")
            return False
        except Exception as e:
            logger.error(f"Error initializing collection {collection_id} on server {server_id}: {e}")
            return False
    
    def get_collection(self, server_id: str, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a TAXII collection.
        
        Args:
            server_id: Server identifier
            collection_id: Collection identifier
            
        Returns:
            Collection information or None if not found
        """
        collection_key = f"{server_id}:{collection_id}"
        return self.collections.get(collection_key)
    
    def list_collections(self, server_id: str = None) -> List[Dict[str, Any]]:
        """
        List available collections.
        
        Args:
            server_id: Server identifier (or None for all servers)
            
        Returns:
            List of collection information
        """
        collections = []
        
        for collection_key, collection_info in self.collections.items():
            if server_id is None or collection_info['server_id'] == server_id:
                collections.append({
                    'key': collection_key,
                    'server_id': collection_info['server_id'],
                    'collection_id': collection_info['collection_id'],
                    'title': collection_info['collection'].title,
                    'description': collection_info['collection'].description,
                    'can_read': collection_info['collection'].can_read,
                    'can_write': collection_info['collection'].can_write,
                })
        
        return collections
    
    def fetch_intelligence(
        self,
        server_id: str,
        collection_id: str,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch intelligence from a TAXII collection.
        
        Args:
            server_id: Server identifier
            collection_id: Collection identifier
            start_time: Start time for filtering (or None for no start filter)
            end_time: End time for filtering (or None for no end filter)
            limit: Maximum number of objects to retrieve
            
        Returns:
            List of intelligence objects
        """
        collection_info = self.get_collection(server_id, collection_id)
        
        if not collection_info:
            logger.error(f"Collection not found: {server_id}:{collection_id}")
            return []
        
        try:
            collection = collection_info['collection']
            
            # Prepare filters
            filters = {}
            
            if start_time:
                filters['added_after'] = start_time.isoformat()
            
            # Fetch objects
            response = collection.get_objects(**filters)
            
            # Process objects
            objects = []
            
            for obj in response.get('objects', [])[:limit]:
                # Convert to simpler dict format
                intel_obj = {
                    'id': obj.get('id'),
                    'type': obj.get('type'),
                    'created': obj.get('created'),
                    'modified': obj.get('modified'),
                    'source': f"taxii:{server_id}:{collection_id}",
                    'content': obj
                }
                
                objects.append(intel_obj)
            
            logger.info(f"Fetched {len(objects)} objects from {server_id}:{collection_id}")
            return objects
        except Exception as e:
            logger.error(f"Error fetching intelligence from {server_id}:{collection_id}: {e}")
            return []
    
    def ingest_intelligence(
        self,
        server_id: str,
        collection_id: str,
        start_time: datetime = None,
        priority_level: str = 'medium',
        store: bool = True
    ) -> List[str]:
        """
        Ingest intelligence from a TAXII collection and store it.
        
        Args:
            server_id: Server identifier
            collection_id: Collection identifier
            start_time: Start time for filtering (or None for recent)
            priority_level: Priority level for categorization
            store: Whether to store the intelligence
            
        Returns:
            List of ingested intelligence IDs
        """
        # Default to recent intelligence if no start time
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        
        # Fetch intelligence
        intel_objects = self.fetch_intelligence(
            server_id,
            collection_id,
            start_time=start_time
        )
        
        intel_ids = []
        
        for obj in intel_objects:
            try:
                # Generate ID
                intel_id = obj.get('id', '').replace(':', '_')
                if not intel_id:
                    intel_id = f"taxii_{int(time.time())}_{len(intel_ids)}"
                
                # Categorize
                source_type = f"taxii:{server_id}"
                categorized_data = categorize_intelligence(obj, source_type, priority_level)
                
                # Store if requested
                if store:
                    _store_intelligence_data(intel_id, categorized_data)
                
                intel_ids.append(intel_id)
            except Exception as e:
                logger.error(f"Error processing intelligence object: {e}")
        
        logger.info(f"Ingested {len(intel_ids)} intelligence objects from {server_id}:{collection_id}")
        return intel_ids

def create_taxii_config(
    config_name: str,
    server_url: str,
    username: str = None,
    password: str = None,
    collections: List[str] = None,
    description: str = ""
) -> bool:
    """
    Create a TAXII server configuration.
    
    Args:
        config_name: Configuration name
        server_url: TAXII server URL
        username: Username for authentication (or None for no auth)
        password: Password for authentication (or None for no auth)
        collections: List of collections to use (or None/'auto' for all)
        description: Configuration description
        
    Returns:
        True if created successfully, False otherwise
    """
    if not STIX_AVAILABLE:
        logger.error("STIX/TAXII libraries not available. Cannot create configuration.")
        return False
    
    # Prepare configuration
    config = {
        'name': config_name,
        'description': description,
        'created': datetime.now().isoformat(),
        'servers': {
            'default': {
                'url': server_url,
                'collections': collections or 'auto'
            }
        }
    }
    
    # Add authentication if provided
    if username and password:
        config['servers']['default']['auth_type'] = 'basic'
        config['servers']['default']['username'] = username
        config['servers']['default']['password'] = password
    
    # Save configuration
    config_path = os.path.join(TAXII_CONFIGS_PATH, f"{config_name}.json")
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Created TAXII configuration: {config_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating TAXII configuration: {e}")
        return False

def list_taxii_configs() -> List[Dict[str, Any]]:
    """
    List available TAXII configurations.
    
    Returns:
        List of configuration information
    """
    configs = []
    
    # Get configuration files
    config_files = glob.glob(os.path.join(TAXII_CONFIGS_PATH, "*.json"))
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Extract basic information
            configs.append({
                'name': config.get('name', os.path.basename(config_file).replace('.json', '')),
                'description': config.get('description', ''),
                'created': config.get('created', ''),
                'servers': len(config.get('servers', {}))
            })
        except Exception as e:
            logger.error(f"Error reading TAXII configuration {config_file}: {e}")
    
    return configs
