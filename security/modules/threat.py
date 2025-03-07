#!/usr/bin/env python3
"""
Threat monitoring and analysis module for detecting and responding to threats.
"""
import os
import json
import logging
import ipaddress
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Import from local modules
from .utils import THREAT_IOC_PATH
from .intel import check_ioc, search_intelligence

# Set up logging
logger = logging.getLogger(__name__)

# Threat scoring thresholds
THREAT_SEVERITY = {
    'critical': 80,  # Critical threats (80-100)
    'high': 60,      # High threats (60-79)
    'medium': 40,    # Medium threats (40-59)
    'low': 20,       # Low threats (20-39)
    'info': 0        # Informational (0-19)
}

# Common IOC patterns
IOC_PATTERNS = {
    'ip': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    'domain': r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$',
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'md5': r'^[a-fA-F0-9]{32}$',
    'sha1': r'^[a-fA-F0-9]{40}$',
    'sha256': r'^[a-fA-F0-9]{64}$',
    'url': r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
}

class ThreatDetector:
    """Threat detection and monitoring service."""
    
    def __init__(self):
        """Initialize threat detector."""
        # Threat rules
        self.rules = []
        # Recent alerts
        self.recent_alerts = []
    
    def load_rules(self, rules_dir: str = None) -> int:
        """
        Load threat detection rules from directory.
        
        Args:
            rules_dir: Directory containing rule files (or None for default)
            
        Returns:
            Number of rules loaded
        """
        if not rules_dir:
            # Default to project data directory
            rules_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'threat_rules')
        
        if not os.path.exists(rules_dir):
            logger.warning(f"Rules directory does not exist: {rules_dir}")
            return 0
        
        try:
            # Load all JSON files in directory
            rule_files = [f for f in os.listdir(rules_dir) if f.endswith('.json')]
            
            loaded_rules = []
            
            for rule_file in rule_files:
                rule_path = os.path.join(rules_dir, rule_file)
                
                try:
                    with open(rule_path, 'r') as f:
                        rule = json.load(f)
                    
                    # Validate rule
                    if self._validate_rule(rule):
                        loaded_rules.append(rule)
                    else:
                        logger.warning(f"Invalid rule in {rule_file}")
                except Exception as e:
                    logger.error(f"Error loading rule from {rule_file}: {e}")
            
            # Update rules
            self.rules = loaded_rules
            
            logger.info(f"Loaded {len(self.rules)} threat detection rules")
            return len(self.rules)
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return 0
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """
        Validate a threat detection rule.
        
        Args:
            rule: Rule to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Required fields
        required_fields = ['id', 'name', 'description', 'severity', 'detection']
        
        for field in required_fields:
            if field not in rule:
                logger.warning(f"Rule missing required field: {field}")
                return False
        
        # Validate severity
        if rule['severity'] not in THREAT_SEVERITY:
            logger.warning(f"Invalid severity in rule {rule.get('id')}: {rule.get('severity')}")
            return False
        
        # Validate detection
        detection = rule.get('detection', {})
        
        if not detection or not isinstance(detection, dict):
            logger.warning(f"Invalid detection in rule {rule.get('id')}")
            return False
        
        # Must have at least one detection method
        if not any(key in detection for key in ['pattern', 'ioc', 'condition']):
            logger.warning(f"No detection method in rule {rule.get('id')}")
            return False
        
        return True
    
    def analyze(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze data for threats using loaded rules.
        
        Args:
            data: Data to analyze
            context: Additional context for analysis
            
        Returns:
            List of threat alerts
        """
        if not self.rules:
            logger.warning("No rules loaded for threat detection")
            return []
        
        context = context or {}
        alerts = []
        
        # Apply each rule
        for rule in self.rules:
            try:
                # Check if rule applies
                if self._rule_matches(rule, data, context):
                    # Generate alert
                    alert = self._create_alert(rule, data, context)
                    alerts.append(alert)
                    
                    # Store in recent alerts
                    self.recent_alerts.append(alert)
                    
                    # Trim recent alerts if needed
                    if len(self.recent_alerts) > 100:
                        self.recent_alerts.pop(0)
            except Exception as e:
                logger.error(f"Error applying rule {rule.get('id')}: {e}")
        
        return alerts
    
    def _rule_matches(self, rule: Dict[str, Any], data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Check if a rule matches the data.
        
        Args:
            rule: Rule to check
            data: Data to analyze
            context: Additional context
            
        Returns:
            True if rule matches, False otherwise
        """
        detection = rule.get('detection', {})
        
        # Check pattern matching
        if 'pattern' in detection:
            pattern = detection['pattern']
            field = detection.get('field', '')
            
            # Get field value using dot notation
            value = data
            for part in field.split('.'):
                if part and isinstance(value, dict):
                    value = value.get(part, {})
            
            # If we have a string value, check against pattern
            if isinstance(value, str):
                if re.search(pattern, value):
                    return True
        
        # Check IOC matching
        if 'ioc' in detection:
            ioc_type = detection['ioc'].get('type')
            ioc_value = detection['ioc'].get('value')
            
            if ioc_type and ioc_value:
                # Check if this exact IOC is known
                ioc_data = check_ioc(ioc_type, ioc_value)
                if ioc_data:
                    return True
                
                # Also check if the data contains this IOC
                for key, value in data.items():
                    if isinstance(value, str) and value == ioc_value:
                        return True
        
        # Check conditional logic
        if 'condition' in detection:
            condition = detection['condition']
            
            # Implement simple condition checking
            if condition == 'contains':
                field = detection.get('field', '')
                value = detection.get('value', '')
                
                # Get field value using dot notation
                field_value = data
                for part in field.split('.'):
                    if part and isinstance(field_value, dict):
                        field_value = field_value.get(part, {})
                
                # Check if field value contains the target value
                if isinstance(field_value, str) and value in field_value:
                    return True
                elif isinstance(field_value, list) and value in field_value:
                    return True
            
            elif condition == 'equals':
                field = detection.get('field', '')
                value = detection.get('value', '')
                
                # Get field value using dot notation
                field_value = data
                for part in field.split('.'):
                    if part and isinstance(field_value, dict):
                        field_value = field_value.get(part, {})
                
                # Check if field value equals the target value
                if field_value == value:
                    return True
        
        return False
    
    def _create_alert(self, rule: Dict[str, Any], data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an alert from a matched rule.
        
        Args:
            rule: Rule that matched
            data: Data that triggered the rule
            context: Additional context
            
        Returns:
            Alert data
        """
        # Generate alert ID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        alert_id = f"alert_{rule.get('id')}_{timestamp}"
        
        # Create alert
        alert = {
            'id': alert_id,
            'rule_id': rule.get('id'),
            'name': rule.get('name'),
            'description': rule.get('description'),
            'severity': rule.get('severity'),
            'score': THREAT_SEVERITY.get(rule.get('severity', 'medium'), 50),
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'data': data
        }
        
        # Add tags from rule
        if 'tags' in rule:
            alert['tags'] = rule['tags']
        
        # Add recommendations from rule
        if 'recommendations' in rule:
            alert['recommendations'] = rule['recommendations']
        
        logger.info(f"Generated threat alert: {alert_id} ({rule.get('severity', 'unknown')} severity)")
        return alert
    
    def get_recent_alerts(self, severity: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts.
        
        Args:
            severity: Filter by severity (or None for all)
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        if severity:
            filtered_alerts = [alert for alert in self.recent_alerts 
                              if alert.get('severity') == severity]
        else:
            filtered_alerts = self.recent_alerts
        
        # Sort by timestamp (newest first) and limit
        sorted_alerts = sorted(filtered_alerts, 
                              key=lambda x: x.get('timestamp', ''), 
                              reverse=True)
        
        return sorted_alerts[:limit]

def identify_ioc_type(value: str) -> Optional[str]:
    """
    Identify the type of an indicator of compromise.
    
    Args:
        value: Value to identify
        
    Returns:
        Type of IOC or None if not identified
    """
    # Check each pattern
    for ioc_type, pattern in IOC_PATTERNS.items():
        if re.match(pattern, value):
            return ioc_type
    
    # Special case for hashes
    if re.match(r'^[a-fA-F0-9]+$', value):
        if len(value) == 32:
            return 'md5'
        elif len(value) == 40:
            return 'sha1'
        elif len(value) == 64:
            return 'sha256'
    
    return None

def extract_iocs(text: str) -> List[Dict[str, Any]]:
    """
    Extract indicators of compromise from text.
    
    Args:
        text: Text to extract IOCs from
        
    Returns:
        List of extracted IOCs
    """
    iocs = []
    
    # Extract IPs
    ip_pattern = IOC_PATTERNS['ip']
    for match in re.finditer(ip_pattern, text):
        iocs.append({
            'type': 'ip',
            'value': match.group(0),
            'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
        })
    
    # Extract domains
    domain_pattern = IOC_PATTERNS['domain']
    for match in re.finditer(domain_pattern, text):
        # Make sure it's not part of a URL or email
        if not re.search(r'https?://' + re.escape(match.group(0)), text) and \
           not re.search(r'@' + re.escape(match.group(0)), text):
            iocs.append({
                'type': 'domain',
                'value': match.group(0),
                'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
            })
    
    # Extract emails
    email_pattern = IOC_PATTERNS['email']
    for match in re.finditer(email_pattern, text):
        iocs.append({
            'type': 'email',
            'value': match.group(0),
            'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
        })
    
    # Extract URLs
    url_pattern = IOC_PATTERNS['url']
    for match in re.finditer(url_pattern, text):
        iocs.append({
            'type': 'url',
            'value': match.group(0),
            'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
        })
    
    # Extract hashes
    for hash_type in ['md5', 'sha1', 'sha256']:
        hash_pattern = IOC_PATTERNS[hash_type]
        for match in re.finditer(hash_pattern, text):
            iocs.append({
                'type': hash_type,
                'value': match.group(0),
                'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
            })
    
    return iocs

def check_threat_intelligence(value: str, ioc_type: str = None) -> Dict[str, Any]:
    """
    Check a value against threat intelligence.
    
    Args:
        value: Value to check
        ioc_type: Type of IOC (or None to auto-detect)
        
    Returns:
        Threat intelligence information
    """
    # Auto-detect IOC type if not provided
    if not ioc_type:
        ioc_type = identify_ioc_type(value)
        
        if not ioc_type:
            return {
                'value': value,
                'type': 'unknown',
                'found': False,
                'score': 0,
                'message': 'Unknown IOC type'
            }
    
    # Check if IOC exists in our database
    ioc_data = check_ioc(ioc_type, value)
    
    if ioc_data:
        return {
            'value': value,
            'type': ioc_type,
            'found': True,
            'source': ioc_data.get('source', 'local'),
            'confidence': ioc_data.get('confidence', 50),
            'score': ioc_data.get('confidence', 50),
            'description': ioc_data.get('description', ''),
            'timestamp': ioc_data.get('timestamp', '')
        }
    
    # If not found, check if there's any intelligence about similar IOCs
    related_intel = search_intelligence(
        query={'type': ioc_type},
        limit=5
    )
    
    # Not found
    return {
        'value': value,
        'type': ioc_type,
        'found': False,
        'score': 0,
        'related_count': len(related_intel),
        'message': f'No threat intelligence found for {ioc_type}'
    }

def create_threat_rule(
    name: str,
    description: str,
    detection: Dict[str, Any],
    severity: str = 'medium',
    tags: List[str] = None,
    recommendations: List[str] = None
) -> Dict[str, Any]:
    """
    Create a new threat detection rule.
    
    Args:
        name: Rule name
        description: Rule description
        detection: Detection criteria
        severity: Rule severity
        tags: Tags to associate with the rule
        recommendations: Recommended actions
        
    Returns:
        Created rule
    """
    # Validate severity
    if severity not in THREAT_SEVERITY:
        logger.warning(f"Invalid severity: {severity}, defaulting to 'medium'")
        severity = 'medium'
    
    # Generate ID based on name
    rule_id = f"rule_{hashlib.md5(name.encode()).hexdigest()[:12]}"
    
    # Create rule
    rule = {
        'id': rule_id,
        'name': name,
        'description': description,
        'severity': severity,
        'detection': detection,
        'created': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'version': 1
    }
    
    # Add optional fields
    if tags:
        rule['tags'] = tags
    
    if recommendations:
        rule['recommendations'] = recommendations
    
    # Save rule
    rules_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'threat_rules')
    os.makedirs(rules_dir, exist_ok=True)
    
    rule_path = os.path.join(rules_dir, f"{rule_id}.json")
    
    try:
        with open(rule_path, 'w') as f:
            json.dump(rule, f, indent=2)
        logger.info(f"Created threat rule: {rule_id}")
        return rule
    except Exception as e:
        logger.error(f"Error creating threat rule: {e}")
        raise
