#!/usr/bin/env python3
"""
STIX/TAXII Integration Module for Threat Intelligence Sharing

This module implements STIX (Structured Threat Information Expression) and 
TAXII (Trusted Automated Exchange of Intelligence Information) protocols
for sharing threat intelligence gathered from deep web research and other sources.

The module provides functionality to:
1. Import threat intelligence from TAXII servers
2. Export local threat intelligence to STIX format
3. Convert between internal threat data format and STIX objects
4. Manage TAXII collections and subscriptions

Usage:
    from stix_taxii_integration import STIXTAXIIIntegration
    
    # Initialize the integration
    integration = STIXTAXIIIntegration(config_path='config/taxii_config.json')
    
    # Import from TAXII server
    new_indicators = integration.import_from_taxii()
    
    # Export local intel to STIX format
    stix_bundle = integration.export_to_stix(intel_ids=['intel_123', 'intel_456'])
"""

import os
import json
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union

# Import STIX 2.1 libraries
from stix2 import Bundle, Indicator, ThreatActor, Malware, AttackPattern
from stix2 import Relationship, Identity, Report, Sighting
from stix2.v21 import ObservedData, Vulnerability
from stix2.exceptions import STIXError

# Import TAXII libraries
from taxii2client.v21 import Server, Collection, ApiRoot
from taxii2client.exceptions import TAXIIServiceException

# Local imports
import security
from config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/stix_taxii.log'
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

class STIXTAXIIIntegration:
    """
    Handles integration with STIX/TAXII for threat intelligence sharing.
    """
    
    def __init__(self, config_path: str = 'config/taxii_config.json'):
        """
        Initialize the STIX/TAXII integration module.
        
        Args:
            config_path (str): Path to the TAXII configuration file
        """
        self.config = self._load_config(config_path)
        self.identity = self._create_identity()
        
        # Ensure data directories exist
        os.makedirs('data/stix', exist_ok=True)
        os.makedirs('data/stix/imported', exist_ok=True)
        os.makedirs('data/stix/exported', exist_ok=True)
        
        logger.info("STIX/TAXII Integration module initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load TAXII configuration from a JSON file.
        
        Args:
            config_path (str): Path to the config file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        default_config = {
            "identity": {
                "name": "Organization Security Team",
                "description": "Security research and threat intelligence unit",
                "identity_class": "organization",
                "sectors": ["technology"],
                "contact_information": "security@example.com"
            },
            "taxii_servers": [
                {
                    "name": "Example TAXII Server",
                    "url": "https://example.com/taxii2/",
                    "username": "",
                    "password": "",
                    "api_roots": ["default"],
                    "collections": ["collection1", "collection2"],
                    "enabled": False
                }
            ],
            "export_options": {
                "default_confidence": 75,
                "default_tlp": "AMBER",
                "include_sightings": True,
                "include_first_seen": True
            },
            "import_options": {
                "minimum_confidence": 60,
                "types_to_import": ["indicator", "malware", "threat-actor", "attack-pattern"],
                "auto_correlate": True
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge configurations
                for key, value in user_config.items():
                    if key in default_config and isinstance(value, dict) and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                logger.info(f"Loaded TAXII configuration from {config_path}")
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                # Create default config file
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                logger.info(f"Created default configuration at {config_path}")
        except Exception as e:
            logger.error(f"Error loading TAXII configuration: {e}")
        
        return default_config
    
    def _create_identity(self) -> Identity:
        """
        Create a STIX Identity object representing this organization.
        
        Returns:
            Identity: STIX Identity object
        """
        try:
            identity_config = self.config["identity"]
            identity = Identity(
                id=f"identity--{uuid.uuid4()}",
                name=identity_config["name"],
                description=identity_config.get("description", ""),
                identity_class=identity_config.get("identity_class", "organization"),
                sectors=identity_config.get("sectors", []),
                contact_information=identity_config.get("contact_information", "")
            )
            return identity
        except Exception as e:
            logger.error(f"Error creating identity: {e}")
            # Create minimal fallback identity
            return Identity(
                id=f"identity--{uuid.uuid4()}",
                name="Security Team",
                identity_class="organization"
            )
    
    def import_from_taxii(self, server_index: int = None) -> List[Dict[str, Any]]:
        """
        Import threat intelligence from TAXII servers.
        
        Args:
            server_index (int, optional): Index of specific server to query, or None for all enabled servers
            
        Returns:
            List[Dict[str, Any]]: List of imported intel items in internal format
        """
        imported_items = []
        
        try:
            servers_to_check = []
            
            if server_index is not None:
                if 0 <= server_index < len(self.config["taxii_servers"]):
                    servers_to_check = [self.config["taxii_servers"][server_index]]
                else:
                    logger.error(f"Invalid server index: {server_index}")
                    return []
            else:
                servers_to_check = [s for s in self.config["taxii_servers"] if s.get("enabled", False)]
            
            import_options = self.config["import_options"]
            min_confidence = import_options.get("minimum_confidence", 60)
            types_to_import = import_options.get("types_to_import", [])
            
            logger.info(f"Importing from {len(servers_to_check)} TAXII servers")
            
            for server_config in servers_to_check:
                try:
                    server_name = server_config["name"]
                    logger.info(f"Connecting to TAXII server: {server_name}")
                    
                    # Connect to TAXII server
                    auth = None
                    if server_config.get("username") and server_config.get("password"):
                        auth = (server_config["username"], server_config["password"])
                    
                    server = Server(
                        url=server_config["url"],
                        user=server_config.get("username", None),
                        password=server_config.get("password", None)
                    )
                    
                    # Process each API root
                    for api_root_name in server_config.get("api_roots", []):
                        try:
                            # Get the API root
                            api_root = None
                            for ar in server.api_roots:
                                if ar.title.lower() == api_root_name.lower():
                                    api_root = ar
                                    break
                            
                            if not api_root:
                                logger.warning(f"API root '{api_root_name}' not found in server {server_name}")
                                continue
                            
                            # Process each collection
                            for collection_name in server_config.get("collections", []):
                                try:
                                    # Get the collection
                                    collection = None
                                    for coll in api_root.collections:
                                        if coll.title.lower() == collection_name.lower():
                                            collection = coll
                                            break
                                    
                                    if not collection:
                                        logger.warning(f"Collection '{collection_name}' not found in API root {api_root_name}")
                                        continue
                                    
                                    # Get objects from the collection
                                    response = collection.get_objects()
                                    
                                    # Process each object
                                    for obj in response.get("objects", []):
                                        obj_type = obj.get("type", "")
                                        
                                        # Skip if not in types to import
                                        if types_to_import and obj_type not in types_to_import:
                                            continue
                                        
                                        # Convert to internal format and add to results
                                        internal_item = self._stix_to_internal(obj)
                                        if internal_item:
                                            # Store the original STIX object
                                            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                            stix_filename = f"data/stix/imported/{obj_type}_{timestamp}_{obj['id'].split('--')[1]}.json"
                                            with open(stix_filename, 'w') as f:
                                                json.dump(obj, f, indent=4)
                                            
                                            # Add to security database
                                            internal_item["source"] = f"TAXII:{server_name}:{collection_name}"
                                            security.add_intelligence(internal_item)
                                            imported_items.append(internal_item)
                                            
                                except Exception as e:
                                    logger.error(f"Error processing collection {collection_name}: {e}")
                                    
                        except Exception as e:
                            logger.error(f"Error processing API root {api_root_name}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error connecting to TAXII server {server_name}: {e}")
            
            logger.info(f"Successfully imported {len(imported_items)} items from TAXII servers")
            
            # Auto-correlate if enabled
            if import_options.get("auto_correlate", True) and imported_items:
                self._correlate_imported_items(imported_items)
                
            return imported_items
            
        except Exception as e:
            logger.error(f"Error in TAXII import: {e}")
            return []
    
    def export_to_stix(self, intel_ids: List[str] = None, min_priority: str = "medium") -> Optional[Bundle]:
        """
        Export intelligence items to STIX format.
        
        Args:
            intel_ids (List[str], optional): List of intel IDs to export, or None for all eligible
            min_priority (str): Minimum priority level to include ("critical", "high", "medium", "low")
            
        Returns:
            Optional[Bundle]: STIX bundle containing exported objects
        """
        try:
            export_options = self.config["export_options"]
            default_confidence = export_options.get("default_confidence", 75)
            default_tlp = export_options.get("default_tlp", "AMBER")
            include_sightings = export_options.get("include_sightings", True)
            
            # Get intelligence items to export
            if intel_ids:
                intel_items = [security.get_intelligence(intel_id) for intel_id in intel_ids]
                intel_items = [item for item in intel_items if item]  # Remove None values
            else:
                # Get items based on priority
                priority_levels = ["critical", "high", "medium", "low"]
                min_priority_index = priority_levels.index(min_priority.lower())
                eligible_priorities = priority_levels[:min_priority_index+1]
                
                intel_items = security.get_intelligence_by_priority(eligible_priorities)
            
            if not intel_items:
                logger.warning("No intelligence items to export")
                return None
            
            logger.info(f"Exporting {len(intel_items)} intelligence items to STIX")
            
            # Convert to STIX objects
            stix_objects = [self.identity]  # Start with our identity object
            
            for intel in intel_items:
                stix_obj = self._internal_to_stix(intel, default_confidence, default_tlp)
                if stix_obj:
                    if isinstance(stix_obj, list):
                        stix_objects.extend(stix_obj)
                    else:
                        stix_objects.append(stix_obj)
            
            # Create STIX bundle
            if stix_objects:
                bundle = Bundle(objects=stix_objects)
                
                # Save to file
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"data/stix/exported/stix_export_{timestamp}.json"
                with open(filename, 'w') as f:
                    f.write(bundle.serialize(pretty=True))
                
                logger.info(f"Exported STIX bundle to {filename}")
                return bundle
            else:
                logger.warning("No STIX objects created during export")
                return None
                
        except Exception as e:
            logger.error(f"Error in STIX export: {e}")
            return None
    
    def _stix_to_internal(self, stix_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert STIX object to internal intelligence format.
        
        Args:
            stix_obj (Dict[str, Any]): STIX object
            
        Returns:
            Optional[Dict[str, Any]]: Internal format or None if conversion fails
        """
        try:
            obj_type = stix_obj.get("type", "")
            
            # Base internal representation
            internal = {
                "id": f"intel_{uuid.uuid4()}",
                "title": stix_obj.get("name", "") or stix_obj.get("pattern", ""),
                "type": "stix_import",
                "description": stix_obj.get("description", ""),
                "created": stix_obj.get("created", datetime.datetime.now().isoformat()),
                "modified": stix_obj.get("modified", datetime.datetime.now().isoformat()),
                "source": "STIX Import",
                "confidence": stix_obj.get("confidence", 0),
                "stix_id": stix_obj.get("id", ""),
                "stix_type": obj_type,
                "original_data": stix_obj,
                "tags": []
            }
            
            # Type-specific processing
            if obj_type == "indicator":
                internal["iocs"] = [{
                    "type": "stix_pattern",
                    "value": stix_obj.get("pattern", ""),
                    "confidence": stix_obj.get("confidence", 50),
                    "description": stix_obj.get("description", "")
                }]
                internal["indicator_types"] = stix_obj.get("indicator_types", [])
                internal["tags"].extend(stix_obj.get("indicator_types", []))
                internal["valid_from"] = stix_obj.get("valid_from", "")
                internal["valid_until"] = stix_obj.get("valid_until", "")
                
            elif obj_type == "malware":
                internal["malware_types"] = stix_obj.get("malware_types", [])
                internal["tags"].extend(stix_obj.get("malware_types", []))
                internal["title"] = stix_obj.get("name", "Unnamed Malware")
                internal["is_family"] = stix_obj.get("is_family", False)
                
            elif obj_type == "threat-actor":
                internal["threat_actor_types"] = stix_obj.get("threat_actor_types", [])
                internal["tags"].extend(stix_obj.get("threat_actor_types", []))
                internal["title"] = stix_obj.get("name", "Unnamed Threat Actor")
                internal["aliases"] = stix_obj.get("aliases", [])
                internal["roles"] = stix_obj.get("roles", [])
                internal["tags"].extend(stix_obj.get("roles", []))
                
            elif obj_type == "attack-pattern":
                internal["title"] = stix_obj.get("name", "Unnamed Attack Pattern")
                if "external_references" in stix_obj:
                    for ref in stix_obj["external_references"]:
                        if ref.get("source_name") == "mitre-attack":
                            internal["mitre_id"] = ref.get("external_id", "")
                            internal["tags"].append(f"MITRE:{internal['mitre_id']}")
                
            elif obj_type == "vulnerability":
                internal["title"] = stix_obj.get("name", "Unnamed Vulnerability")
                if "external_references" in stix_obj:
                    for ref in stix_obj["external_references"]:
                        if ref.get("source_name") == "cve":
                            internal["cve_id"] = ref.get("external_id", "")
                            internal["tags"].append(f"CVE:{internal['cve_id']}")
            
            # Set priority based on confidence
            confidence = internal.get("confidence", 0)
            if confidence >= 85:
                internal["priority"] = "critical"
            elif confidence >= 70:
                internal["priority"] = "high"
            elif confidence >= 50:
                internal["priority"] = "medium"
            else:
                internal["priority"] = "low"
            
            return internal
            
        except Exception as e:
            logger.error(f"Error converting STIX to internal format: {e}")
            return None
    
    def _internal_to_stix(self, intel: Dict[str, Any], default_confidence: int, 
                          default_tlp: str) -> Union[List[Any], Any, None]:
        """
        Convert internal intelligence to STIX object(s).
        
        Args:
            intel (Dict[str, Any]): Internal intelligence data
            default_confidence (int): Default confidence level to use if not specified
            default_tlp (str): Default TLP level to use
            
        Returns:
            Union[List[Any], Any, None]: STIX object(s) or None if conversion fails
        """
        try:
            created = datetime.datetime.fromisoformat(intel.get("created", datetime.datetime.now().isoformat()))
            modified = datetime.datetime.fromisoformat(intel.get("modified", datetime.datetime.now().isoformat()))
            
            # Set object marking based on TLP
            tlp = intel.get("tlp", default_tlp).upper()
            marking_def = None
            
            # Get confidence level
            confidence = intel.get("confidence", default_confidence)
            
            # Base properties for STIX objects
            common_props = {
                "created_by_ref": self.identity.id,
                "created": created,
                "modified": modified,
                "object_marking_refs": [marking_def] if marking_def else [],
                "confidence": confidence
            }
            
            # Convert based on intel type
            intel_type = intel.get("stix_type", "")
            stix_objects = []
            
            if not intel_type:
                # Determine type based on internal data
                if "iocs" in intel and intel["iocs"]:
                    # Create indicators for each IOC
                    for ioc in intel["iocs"]:
                        pattern_type = "stix"
                        pattern_value = ""
                        
                        ioc_type = ioc.get("type", "").lower()
                        ioc_value = ioc.get("value", "")
                        
                        if ioc_type == "ip":
                            pattern_value = f"[ipv4-addr:value = '{ioc_value}']"
                        elif ioc_type == "domain":
                            pattern_value = f"[domain-name:value = '{ioc_value}']"
                        elif ioc_type == "url":
                            pattern_value = f"[url:value = '{ioc_value}']"
                        elif ioc_type == "hash":
                            if len(ioc_value) == 32:  # MD5
                                pattern_value = f"[file:hashes.'MD5' = '{ioc_value}']"
                            elif len(ioc_value) == 40:  # SHA-1
                                pattern_value = f"[file:hashes.'SHA-1' = '{ioc_value}']"
                            elif len(ioc_value) == 64:  # SHA-256
                                pattern_value = f"[file:hashes.'SHA-256' = '{ioc_value}']"
                        elif ioc_type == "file":
                            pattern_value = f"[file:name = '{ioc_value}']"
                        elif ioc_type == "email":
                            pattern_value = f"[email-addr:value = '{ioc_value}']"
                        elif ioc_type == "stix_pattern":
                            pattern_value = ioc_value
                        
                        if pattern_value:
                            indicator = Indicator(
                                id=f"indicator--{uuid.uuid4()}",
                                name=intel.get("title", ""),
                                description=ioc.get("description", intel.get("description", "")),
                                pattern=pattern_value,
                                pattern_type=pattern_type,
                                indicator_types=intel.get("indicator_types", ["malicious-activity"]),
                                valid_from=created,
                                **common_props
                            )
                            stix_objects.append(indicator)
                
                if "malware_name" in intel or "malware_family" in intel:
                    # Create malware object
                    malware = Malware(
                        id=f"malware--{uuid.uuid4()}",
                        name=intel.get("malware_name", intel.get("malware_family", intel.get("title", "Unknown Malware"))),
                        description=intel.get("description", ""),
                        is_family=intel.get("is_family", False),
                        malware_types=intel.get("malware_types", ["unknown"]),
                        **common_props
                    )
                    stix_objects.append(malware)
                
                if "threat_actor" in intel:
                    # Create threat actor object
                    actor = ThreatActor(
                        id=f"threat-actor--{uuid.uuid4()}",
                        name=intel.get("threat_actor", intel.get("title", "Unknown Threat Actor")),
                        description=intel.get("description", ""),
                        threat_actor_types=intel.get("threat_actor_types", ["unknown"]),
                        aliases=intel.get("aliases", []),
                        roles=intel.get("roles", []),
                        **common_props
                    )
                    stix_objects.append(actor)
                
                if "attack_pattern" in intel or "mitre_id" in intel:
                    # Create attack pattern object
                    external_refs = []
                    if "mitre_id" in intel:
                        external_refs.append({
                            "source_name": "mitre-attack",
                            "external_id": intel["mitre_id"]
                        })
                    
                    pattern = AttackPattern(
                        id=f"attack-pattern--{uuid.uuid4()}",
                        name=intel.get("attack_pattern", intel.get("title", "Unknown Attack Pattern")),
                        description=intel.get("description", ""),
                        external_references=external_refs if external_refs else None,
                        **common_props
                    )
                    stix_objects.append(pattern)
                
                if "vulnerability" in intel or "cve_id" in intel:
                    # Create vulnerability object
                    external_refs = []
                    if "cve_id" in intel:
                        external_refs.append({
                            "source_name": "cve",
                            "external_id": intel["cve_id"]
                        })
                    
                    vuln = Vulnerability(
                        id=f"vulnerability--{uuid.uuid4()}",
                        name=intel.get("vulnerability", intel.get("title", "Unknown Vulnerability")),
                        description=intel.get("description", ""),
                        external_references=external_refs if external_refs else None,
                        **common_props
                    )
                    stix_objects.append(vuln)
                
                # If no specific objects were created, create a generic report
                if not stix_objects:
                    report = Report(
                        id=f"report--{uuid.uuid4()}",
                        name=intel.get("title", "Intelligence Report"),
                        description=intel.get("description", ""),
                        published=modified,
                        report_types=["threat-report"],
                        **common_props
                    )
                    stix_objects.append(report)
            
            else:
                # Use the existing STIX type information
                if intel.get("original_data"):
                    # If we have the original STIX data, use it directly
                    return intel["original_data"]
            
            # Return the STIX objects
            if len(stix_objects) == 1:
                return stix_objects[0]
            else:
                return stix_objects
                
        except Exception as e:
            logger.error(f"Error converting internal to STIX format: {e}")
            return None
    
    def _correlate_imported_items(self, imported_items: List[Dict[str, Any]]) -> None:
        """
        Correlate newly imported items with existing intelligence.
        
        Args:
            imported_items (List[Dict[str, Any]]): List of newly imported intelligence items
        """
        try:
            logger.info(f"Correlating {len(imported_items)} imported items")
            
            # Get existing intelligence to correlate with
            existing_intel = security.get_all_intelligence(max_items=1000)
            
            # For each imported item
            for new_item in imported_items:
                correlations = []
                
                # Check for correlations with existing intelligence
                for existing_item in existing_intel:
                    # Skip if it's the same item
                    if existing_item.get("id") == new_item.get("id"):
                        continue
                    
                    correlation_score = self._calculate_correlation_score(new_item, existing_item)
                    
                    if correlation_score >= 0.6:  # Correlation threshold
                        correlations.append({
                            "intel_id": existing_item["id"],
                            "score": correlation_score,
                            "reason": self._get_correlation_reason(new_item, existing_item)
                        })
                
                # Add correlations to the item
                if correlations:
                    new_item["correlations"] = correlations
                    security.update_intelligence(new_item["id"], {"correlations": correlations})
                    
                    # Log correlations found
                    correlation_ids = [c["intel_id"] for c in correlations]
                    logger.info(f"Found {len(correlations)} correlations for item {new_item['id']}: {correlation_ids}")
            
        except Exception as e:
            logger.error(f"Error correlating imported items: {e}")
    
    def _calculate_correlation_score(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """
        Calculate a correlation score between two intelligence items.
        
        Args:
            item1 (Dict[str, Any]): First intelligence item
            item2 (Dict[str, Any]): Second intelligence item
            
        Returns:
            float: Correlation score between 0.0 and 1.0
        """
        # This is a simplified implementation - in reality, you would use more sophisticated algorithms
        score = 0.0
        matches = 0
        
        # Check IOCs
        iocs1 = [ioc.get("value", "").lower() for ioc in item1.get("iocs", [])]
        iocs2 = [ioc.get("value", "").lower() for ioc in item2.get("iocs", [])]
        
        common_iocs = set(iocs1).intersection(set(iocs2))
        if common_iocs:
            score += 0.8 * (len(common_iocs) / max(len(iocs1), len(iocs2), 1))
            matches += 1
        
        # Check tags
        tags1 = [tag.lower() for tag in item1.get("tags", [])]
        tags2 = [tag.lower() for tag in item2.get("tags", [])]
        
        common_tags = set(tags1).intersection(set(tags2))
        if common_tags:
            score += 0.3 * (len(common_tags) / max(len(tags1), len(tags2), 1))
            matches += 1
        
        # Check malware names or families
        malware1 = item1.get("malware_name", "").lower() or item1.get("malware_family", "").lower()
        malware2 = item2.get("malware_name", "").lower() or item2.get("malware_family", "").lower()
        
        if malware1 and malware2 and malware1 == malware2:
            score += 0.7
            matches += 1
        
        # Check threat actors
        actor1 = item1.get("threat_actor", "").lower()
        actor2 = item2.get("threat_actor", "").lower()
        
        if actor1 and actor2 and actor1 == actor2:
            score += 0.7
            matches += 1
        
        # Normalize score based on number of matches
        if matches > 0:
            return min(score / matches, 1.0)
        else:
            return 0.0
    
    def _get_correlation_reason(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> str:
        """
        Get a human-readable reason for correlation between two items.
        
        Args:
            item1 (Dict[str, Any]): First intelligence item
            item2 (Dict[str, Any]): Second intelligence item
            
        Returns:
            str: Reason for correlation
        """
        reasons = []
        
        # Check IOCs
        iocs1 = [ioc.get("value", "").lower() for ioc in item1.get("iocs", [])]
        iocs2 = [ioc.get("value", "").lower() for ioc in item2.get("iocs", [])]
        
        common_iocs = set(iocs1).intersection(set(iocs2))
        if common_iocs:
            if len(common_iocs) == 1:
                reasons.append(f"Matching IOC: {list(common_iocs)[0]}")
            else:
                reasons.append(f"Matching IOCs: {len(common_iocs)} indicators")
        
        # Check malware names or families
        malware1 = item1.get("malware_name", "") or item1.get("malware_family", "")
        malware2 = item2.get("malware_name", "") or item2.get("malware_family", "")
        
        if malware1 and malware2 and malware1.lower() == malware2.lower():
            reasons.append(f"Same malware: {malware1}")
        
        # Check threat actors
        actor1 = item1.get("threat_actor", "")
        actor2 = item2.get("threat_actor", "")
        
        if actor1 and actor2 and actor1.lower() == actor2.lower():
            reasons.append(f"Same threat actor: {actor1}")
        
        # Check tags
        tags1 = [tag.lower() for tag in item1.get("tags", [])]
        tags2 = [tag.lower() for tag in item2.get("tags", [])]
        
        common_tags = set(tags1).intersection(set(tags2))
        if common_tags:
            if len(common_tags) <= 3:
                reasons.append(f"Matching tags: {', '.join(common_tags)}")
            else:
                reasons.append(f"Matching tags: {len(common_tags)} shared tags")
        
        # Return combined reason
        if reasons:
            return "; ".join(reasons)
        else:
            return "Correlation based on multiple factors"


# Helper functions for module usage
def initialize_stix_taxii() -> STIXTAXIIIntegration:
    """
    Initialize the STIX/TAXII integration module.
    
    Returns:
        STIXTAXIIIntegration: Initialized integration instance
    """
    config_path = 'config/taxii_config.json'
    return STIXTAXIIIntegration(config_path)


def import_from_all_sources() -> List[Dict[str, Any]]:
    """
    Import threat intelligence from all configured TAXII sources.
    
    Returns:
        List[Dict[str, Any]]: List of imported intelligence items
    """
    integration = initialize_stix_taxii()
    return integration.import_from_taxii()


def export_critical_intel() -> Optional[Bundle]:
    """
    Export critical and high priority intelligence to STIX format.
    
    Returns:
        Optional[Bundle]: STIX bundle with exported objects
    """
    integration = initialize_stix_taxii()
    return integration.export_to_stix(min_priority="high")


if __name__ == "__main__":
    logging.info("STIX/TAXII integration module called directly")
    
    import argparse
    
    parser = argparse.ArgumentParser(description="STIX/TAXII Integration Tool")
    parser.add_argument("--import", dest="do_import", action="store_true", 
                        help="Import from TAXII sources")
    parser.add_argument("--export", dest="do_export", action="store_true", 
                        help="Export to STIX format")
    parser.add_argument("--server", type=int, default=None, 
                        help="Specific server index to import from")
    parser.add_argument("--priority", type=str, default="medium", 
                        choices=["critical", "high", "medium", "low"],
                        help="Minimum priority level for export")
    parser.add_argument("--config", type=str, default="config/taxii_config.json",
                        help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Create integration instance
    integration = STIXTAXIIIntegration(args.config)
    
    if args.do_import:
        logger.info("Starting TAXII import")
        imported = integration.import_from_taxii(server_index=args.server)
        logger.info(f"Imported {len(imported)} intelligence items")
    
    if args.do_export:
        logger.info(f"Starting STIX export with minimum priority: {args.priority}")
        bundle = integration.export_to_stix(min_priority=args.priority)
        if bundle:
            count = len(bundle.objects) - 1  # Subtract 1 for the identity object
            logger.info(f"Exported {count} intelligence items to STIX bundle")
        else:
            logger.warning("No items exported to STIX bundle") 