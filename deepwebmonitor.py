#!/usr/bin/env python3
"""
Script for continuous monitoring of deep web intelligence and updating the security dashboard.
This implements parts of the post-deep web research plan, particularly:
- Continuous Monitoring Strategy
- Threat Intelligence Implementation
- Security Posture Enhancement

Usage:
    python deep_web_monitor.py --config config.json
"""

import os
import json
import time
import logging
import argparse
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import random
import urllib3
from requests.exceptions import RequestException, Timeout, ConnectionError
from backoff import on_exception, expo

# Import the security modules
import security
from config import API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/deep_web_monitor.log'
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "monitoring_interval": 3600,  # Default to hourly checks
    "max_retries": 3,              # Maximum number of retries for network operations
    "retry_delay": 5,              # Base delay between retries (seconds)
    "use_proxy_rotation": True,    # Whether to rotate proxies for monitoring
    "proxy_rotation_interval": 10, # How often to rotate proxies (in requests)
    "sources": [
        {
            "name": "Sample Forums",
            "type": "forums",
            "enabled": True,
            "last_check": None
        },
        {
            "name": "Sample Marketplaces",
            "type": "marketplaces",
            "enabled": False,
            "last_check": None
        }
    ],
    "alert_thresholds": {
        "critical": 8.0,  # Alert score threshold for critical alerts
        "high": 6.0,      # Alert score threshold for high alerts
        "medium": 4.0,    # Alert score threshold for medium alerts
        "low": 2.0        # Alert score threshold for low alerts
    },
    "dashboard_update_interval": 24,  # Update dashboard daily (in hours)
    "last_dashboard_update": None,
    "taxii_import_interval": 12,      # Import from TAXII server twice daily
    "last_taxii_import": None,
    "stix_export_interval": 24,       # Export to STIX daily
    "last_stix_export": None,
    "correlation_threshold": 0.6,     # Threshold for threat correlation
    "max_correlations": 100,          # Maximum correlations to process
    "threat_report_generation": True, # Auto-generate threat reports
    "automatic_ioc_enrichment": True, # Automatically enrich IOCs with context
    "enable_real_time_alerts": True   # Send alerts in real-time
}

class DeepWebMonitor:
    """
    Deep web monitoring system that continuously checks sources for cyber threat intelligence,
    processes the information, and updates security dashboards.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the deep web monitor with the given configuration.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        self.running = False
        self.thread = None
        self.request_count = 0
        self.current_proxy_index = 0
        self.proxies = []
        self.proxy_last_updated = datetime.now()
        self.config = DEFAULT_CONFIG.copy()
        
        # Load configuration from file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update only the keys that exist in the default config
                    for key in self.config:
                        if key in loaded_config:
                            self.config[key] = loaded_config[key]
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('data/intel', exist_ok=True)
        os.makedirs('data/reports', exist_ok=True)
        os.makedirs('data/iocs', exist_ok=True)
        
        # Load proxy list if proxy rotation is enabled
        if self.config.get("use_proxy_rotation", True):
            self._load_proxies()
    
    def start(self):
        """Start the monitoring process in a separate thread."""
        if self.running:
            logger.warning("Monitor is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Deep web monitoring started")
    
    def stop(self):
        """Stop the monitoring process."""
        if not self.running:
            logger.warning("Monitor is not running")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)  # Wait up to 30 seconds for the thread to end
            if self.thread.is_alive():
                logger.warning("Monitoring thread did not stop gracefully")
            self.thread = None
        logger.info("Deep web monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop that periodically checks sources."""
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                # Check each source
                for source in self.config["sources"]:
                    if source["enabled"]:
                        # Check if this source needs to be processed
                        if (source["last_check"] is None or 
                            (datetime.fromisoformat(source["last_check"]) + 
                             timedelta(seconds=self.config["monitoring_interval"])) <= datetime.now()):
                            self._check_source(source)
                            source["last_check"] = datetime.now().isoformat()
                            self._save_config()
                
                # Check if dashboard update is needed
                self._update_dashboard_if_needed()
                
                # Check if TAXII import is needed
                self._check_taxii_import()
                
                # Check if STIX export is needed
                self._check_stix_export()
                
                # Correlate recent intelligence
                self._correlate_recent_intelligence()
                
                # Sleep for a bit before the next iteration
                time.sleep(60)  # Check every minute if any source needs processing
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Sleep on error before retrying
    
    def _check_source(self, source: Dict[str, Any]):
        """
        Check a specific source for new intelligence.
        
        Args:
            source: Source configuration dictionary
        """
        source_name = source["name"]
        source_type = source["type"]
        
        logger.info(f"Checking source: {source_name} (Type: {source_type})")
        
        try:
            # In a real implementation, this would connect to actual deep web sources
            # For this demo, we'll simulate finding some intelligence
            intelligence_items = self._simulate_source_check(source)
            
            # Process each intelligence item
            for intel in intelligence_items:
                # Calculate a priority score based on the intelligence
                priority_score = self._calculate_priority_score(intel)
                priority_level = self._get_priority_level(priority_score)
                
                # Categorize and store the intelligence
                categorized_intel = security.categorize_intelligence(
                    data=intel,
                    source_type=source_type,
                    priority_level=priority_level,
                    tags=intel.get("tags", [])
                )
                
                # Check if we should create an alert
                if self._should_alert(priority_level) and self.config["enable_real_time_alerts"]:
                    self._create_alert(categorized_intel, source_name)
                
                # Extract and store IOCs if present
                if "iocs" in intel:
                    for ioc_data in intel["iocs"]:
                        try:
                            # Enrich IOC with additional context if enabled
                            if self.config["automatic_ioc_enrichment"]:
                                ioc_data = self._enrich_ioc(ioc_data)
                            
                            # Add IOC to the security system
                            security.add_ioc(
                                ioc_type=ioc_data.get("type", "unknown"),
                                value=ioc_data.get("value", ""),
                                source=f"{source_name} via Deep Web Monitor",
                                confidence=ioc_data.get("confidence", 50),
                                description=ioc_data.get("description", ""),
                                tags=ioc_data.get("tags", []),
                                related_intel_ids=[categorized_intel["id"]]
                            )
                        except Exception as e:
                            logger.error(f"Error processing IOC: {e}")
            
            logger.info(f"Processed {len(intelligence_items)} intelligence items from {source_name}")
        
        except Exception as e:
            logger.error(f"Error checking source {source_name}: {e}", exc_info=True)
    
    def _enrich_ioc(self, ioc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an IOC with additional context from various sources.
        
        Args:
            ioc_data: The original IOC data
            
        Returns:
            Enriched IOC data with additional context
        """
        try:
            ioc_type = ioc_data.get("type")
            ioc_value = ioc_data.get("value")
            
            # Skip enrichment for certain IOC types or empty values
            if not ioc_type or not ioc_value:
                return ioc_data
            
            enriched_ioc = ioc_data.copy()
            
            # Simulate API enrichment (in a real implementation, this would call actual APIs)
            if ioc_type == "ip":
                # Add geolocation data
                enriched_ioc["geo"] = {
                    "country": "Simulated Country",
                    "city": "Simulated City",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "asn": "AS12345 Simulated ISP",
                    "reputation_score": 75
                }
                
            elif ioc_type == "domain":
                # Add WHOIS data
                enriched_ioc["whois"] = {
                    "registrar": "Simulated Registrar LLC",
                    "created_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "expires_date": (datetime.now() + timedelta(days=335)).isoformat(),
                    "updated_date": datetime.now().isoformat(),
                    "nameservers": ["ns1.example.com", "ns2.example.com"]
                }
                
            # Add more enrichment types as needed...
            
            # Add the timestamp of enrichment
            enriched_ioc["enriched_at"] = datetime.now().isoformat()
            enriched_ioc["enriched"] = True
            
            return enriched_ioc
        except Exception as e:
            logger.error(f"Error enriching IOC: {e}")
            return ioc_data  # Return original on error
    
    def _simulate_source_check(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simulate checking a source for intelligence.
        
        Args:
            source: Source configuration
            
        Returns:
            List of simulated intelligence items
        """
        # This is a simulation - in a real implementation, this would
        # connect to actual sources and extract real intelligence

        # Simulate finding 0-3 intelligence items
        num_items = random.randint(0, 3)
        
        intelligence_items = []
        for i in range(num_items):
            # Generate a unique ID for this intelligence
            intel_id = f"INTEL-{int(time.time())}-{i}"
            
            # Create a simulated intelligence item based on source type
            if source["type"] == "forums":
                intel = {
                    "id": intel_id,
                    "title": f"Simulated forum discussion about {random.choice(['data breach', 'vulnerability', 'ransomware'])}",
                    "source": source["name"],
                    "source_url": f"https://simulated-deepweb-forum.example/thread{random.randint(1000, 9999)}",
                    "discovered_at": datetime.now().isoformat(),
                    "content": "This is simulated content that would contain valuable intelligence.",
                    "technical_data": {
                        "mentioned_tools": [random.choice(["mimikatz", "cobalt strike", "metasploit", "empire"])],
                        "mentioned_vulnerabilities": [f"CVE-2023-{random.randint(1000, 9999)}"],
                    },
                    "tags": [
                        random.choice(["ransomware", "data-breach", "vulnerability", "threat-actor"]),
                        random.choice(["windows", "linux", "macos", "mobile"]),
                        random.choice(["financial", "healthcare", "government", "retail"])
                    ],
                    "iocs": [
                        {
                            "type": "domain",
                            "value": f"malicious{random.randint(100, 999)}.example.com",
                            "confidence": random.randint(50, 90),
                            "description": "C2 domain mentioned in forum post"
                        },
                        {
                            "type": "ip",
                            "value": f"192.0.2.{random.randint(1, 254)}",
                            "confidence": random.randint(50, 90),
                            "description": "IP address associated with malicious activity"
                        }
                    ],
                    "threat_actors": [random.choice(["Wizard Spider", "APT29", "LAPSUS$", "FIN7"])],
                    "tactics": [random.choice(["Initial Access", "Execution", "Persistence", "Privilege Escalation"])],
                    "techniques": [random.choice(["T1566", "T1190", "T1133", "T1078"])]
                }
            else:
                # Marketplace intelligence
                intel = {
                    "id": intel_id,
                    "title": f"Simulated listing for {random.choice(['stolen data', 'access credentials', 'exploit kit'])}",
                    "source": source["name"],
                    "source_url": f"https://simulated-deepweb-market.example/listing{random.randint(1000, 9999)}",
                    "discovered_at": datetime.now().isoformat(),
                    "content": "This is simulated content about a marketplace listing.",
                    "technical_data": {
                        "product_type": random.choice(["stolen data", "access", "malware", "exploit"]),
                        "price": f"${random.randint(100, 10000)}",
                        "seller_reputation": random.randint(1, 5)
                    },
                    "tags": [
                        random.choice(["marketplace", "data-sale", "access-sale", "ransomware-service"]),
                        random.choice(["financial", "healthcare", "government", "retail"])
                    ],
                    "iocs": [
                        {
                            "type": "file_hash",
                            "value": f"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b785{random.randint(1000, 9999)}",
                            "confidence": random.randint(50, 90),
                            "description": "Hash of malware sample"
                        }
                    ],
                    "tactics": [random.choice(["Initial Access", "Execution", "Persistence", "Privilege Escalation"])],
                    "techniques": [random.choice(["T1566", "T1190", "T1133", "T1078"])]
                }
            
            intelligence_items.append(intel)
        
        return intelligence_items
    
    def _calculate_priority_score(self, intel: Dict[str, Any]) -> float:
        """
        Calculate a priority score (0-10) for the given intelligence.
        
        Args:
            intel: Intelligence data
            
        Returns:
            Priority score from 0 to 10
        """
        score = 5.0  # Start with a medium score
        
        # Increase score based on presence of technical data
        if intel.get("technical_data"):
            score += 1.0
        
        # Increase score based on presence of IOCs
        if intel.get("iocs"):
            score += len(intel.get("iocs", [])) * 0.5  # 0.5 per IOC, up to 2.0
        
        # Adjust score based on threat actors (if known high-profile actors, increase score)
        high_profile_actors = ["APT29", "Wizard Spider", "LAPSUS$", "FIN7", "APT28"]
        for actor in intel.get("threat_actors", []):
            if actor in high_profile_actors:
                score += 2.0
                break
        
        # Cap the score at 10.0
        return min(10.0, score)
    
    def _get_priority_level(self, score: float) -> str:
        """
        Convert a numerical score to a priority level.
        
        Args:
            score: Numerical score from 0 to 10
            
        Returns:
            Priority level string ('Critical', 'High', 'Medium', or 'Low')
        """
        thresholds = self.config["alert_thresholds"]
        
        if score >= thresholds["critical"]:
            return "Critical"
        elif score >= thresholds["high"]:
            return "High"
        elif score >= thresholds["medium"]:
            return "Medium"
        else:
            return "Low"
    
    def _should_alert(self, priority: str) -> bool:
        """
        Determine if an alert should be created based on priority.
        
        Args:
            priority: Priority level string
            
        Returns:
            True if an alert should be created, False otherwise
        """
        # In this implementation, alert on High and Critical priorities
        return priority in ["Critical", "High"]
    
    def _create_alert(self, intelligence: Dict[str, Any], source_name: str):
        """
        Create an alert for the given intelligence.
        
        Args:
            intelligence: Intelligence data
            source_name: Name of the source
        """
        logger.info(f"ALERT: {intelligence['priority']} priority intelligence from {source_name}: {intelligence['title']}")
        
        # In a real implementation, this would send alerts via various channels
        # such as email, SMS, Slack, or a dedicated security platform
        
        alert_data = {
            "id": f"ALERT-{int(time.time())}",
            "title": intelligence["title"],
            "priority": intelligence["priority"],
            "source": source_name,
            "created_at": datetime.now().isoformat(),
            "intelligence_id": intelligence["id"],
            "description": intelligence.get("content", "No description available")[:200] + "...",
            "recommendations": [
                "Review the full intelligence entry",
                "Check for the presence of IOCs in your environment",
                "Update monitoring systems with new IOCs"
            ]
        }
        
        # Save alert to file (in a real implementation, this would go to a database)
        try:
            os.makedirs("data/alerts", exist_ok=True)
            alert_file = f"data/alerts/alert-{alert_data['id']}.json"
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            logger.info(f"Alert saved to {alert_file}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    
    def _correlate_recent_intelligence(self):
        """
        Correlate recent intelligence data to identify patterns and relationships.
        """
        if not self.config["threat_report_generation"]:
            return
            
        try:
            # Get all recent IOCs (last 24 hours)
            recent_iocs = []
            
            # In a real implementation, this would query a database
            # For this simulation, we'll scan JSON files in the IOCs directory
            ioc_files = glob.glob(os.path.join("data/iocs", "*.json"))
            yesterday = datetime.now() - timedelta(days=1)
            
            for file_path in ioc_files:
                try:
                    with open(file_path, 'r') as f:
                        ioc = json.load(f)
                        
                    # Check if the IOC is recent
                    if "created_at" in ioc:
                        created_at = datetime.fromisoformat(ioc["created_at"])
                        if created_at >= yesterday:
                            recent_iocs.append(ioc)
                except Exception as e:
                    logger.error(f"Error loading IOC file {file_path}: {e}")
            
            # Skip if no recent IOCs
            if not recent_iocs:
                return
                
            logger.info(f"Correlating {len(recent_iocs)} recent IOCs")
            
            # Use the security.correlate_threats function to find correlations
            correlations = security.correlate_threats(
                iocs=recent_iocs,
                threshold=self.config["correlation_threshold"],
                max_correlations=self.config["max_correlations"]
            )
            
            if correlations:
                logger.info(f"Found {len(correlations)} correlations in recent intelligence")
                
                # Generate a threat report
                report = security.generate_threat_report(correlations)
                
                # Save the report
                report_file = f"data/reports/threat-report-{report['report_id']}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"Threat report saved to {report_file}")
                
                # Create a markdown summary of the report
                self._create_report_summary(report)
        except Exception as e:
            logger.error(f"Error correlating intelligence: {e}", exc_info=True)
    
    def _create_report_summary(self, report: Dict[str, Any]):
        """
        Create a markdown summary of a threat report.
        
        Args:
            report: Threat report data
        """
        try:
            report_id = report["report_id"]
            timestamp = datetime.fromisoformat(report["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Create markdown content
            md_content = [
                f"# Threat Intelligence Report {report_id}",
                f"\nGenerated: {timestamp}",
                f"\n## Summary",
                f"\n{report['summary']}",
                f"\n## Key Findings"
            ]
            
            # Add priority summary
            priority_summary = report["details"]["priority_summary"]
            md_content.append("\n### Priority Distribution")
            md_content.append("\n| Priority | Count |")
            md_content.append("|----------|-------|")
            for priority, count in priority_summary.items():
                if count > 0:
                    md_content.append(f"| {priority} | {count} |")
            
            # Add top threat actors if available
            if report["details"].get("top_threat_actors"):
                md_content.append("\n### Top Threat Actors")
                md_content.append("\n| Actor | Count |")
                md_content.append("|-------|-------|")
                for actor in report["details"]["top_threat_actors"]:
                    md_content.append(f"| {actor['name']} | {actor['count']} |")
            
            # Add recommendations
            if report["details"].get("recommendations"):
                md_content.append("\n## Recommendations")
                for rec in report["details"]["recommendations"]:
                    md_content.append(f"\n### {rec['action']} (Priority: {rec['priority']})")
                    md_content.append(f"\n{rec['details']}")
            
            # Write the markdown file
            md_file = f"data/reports/threat-report-{report_id}.md"
            with open(md_file, 'w') as f:
                f.write("\n".join(md_content))
            logger.info(f"Threat report summary saved to {md_file}")
            
        except Exception as e:
            logger.error(f"Error creating report summary: {e}", exc_info=True)
    
    def _update_dashboard_if_needed(self):
        """Check if the dashboard needs to be updated and update if needed."""
        # Check if the dashboard update interval has passed
        last_update = self.config["last_dashboard_update"]
        update_interval = timedelta(hours=self.config["dashboard_update_interval"])
        
        if (last_update is None or 
            (datetime.fromisoformat(last_update) + update_interval) <= datetime.now()):
            self._update_dashboard()
            self.config["last_dashboard_update"] = datetime.now().isoformat()
            self._save_config()
    
    def _update_dashboard(self):
        """Update the security dashboard with current intelligence."""
        logger.info("Updating security dashboard")
        
        try:
            # In a real implementation, this would update a real dashboard
            # For this simulation, we'll just write to a file
            
            # Get statistics on collected intelligence
            num_critical = 0
            num_high = 0
            num_medium = 0
            num_low = 0
            
            # Count IOCs by type
            ioc_counts = {
                "domain": 0,
                "ip": 0,
                "url": 0,
                "file_hash": 0,
                "email": 0,
                "other": 0
            }
            
            # In a real implementation, this would query a database
            # For this simulation, we'll scan JSON files
            intel_files = glob.glob(os.path.join("data/intel", "*.json"))
            for file_path in intel_files:
                try:
                    with open(file_path, 'r') as f:
                        intel = json.load(f)
                        
                    # Count by priority
                    if intel.get("priority") == "Critical":
                        num_critical += 1
                    elif intel.get("priority") == "High":
                        num_high += 1
                    elif intel.get("priority") == "Medium":
                        num_medium += 1
                    else:
                        num_low += 1
                    
                    # Count IOCs by type
                    for ioc in intel.get("iocs", []):
                        ioc_type = ioc.get("type", "other")
                        if ioc_type in ioc_counts:
                            ioc_counts[ioc_type] += 1
                        else:
                            ioc_counts["other"] += 1
                            
                except Exception as e:
                    logger.error(f"Error loading intel file {file_path}: {e}")
            
            # Create dashboard content
            dashboard = [
                "# Deep Web Intelligence Dashboard",
                f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "\n## Intelligence Summary",
                "\n| Priority | Count |",
                "|----------|-------|",
                f"| 🔴 Critical | {num_critical} |",
                f"| 🟠 High | {num_high} |",
                f"| 🟡 Medium | {num_medium} |",
                f"| 🟢 Low | {num_low} |",
                f"| **Total** | **{num_critical + num_high + num_medium + num_low}** |",
                "\n## IOC Summary",
                "\n| Type | Count |",
                "|------|-------|"
            ]
            
            # Add IOC counts
            for ioc_type, count in ioc_counts.items():
                dashboard.append(f"| {ioc_type.capitalize()} | {count} |")
            
            # Add recent alerts section
            dashboard.append("\n## Recent Alerts")
            
            # Get recent alerts (last 5)
            alert_files = glob.glob(os.path.join("data/alerts", "*.json"))
            alert_files.sort(reverse=True)  # Sort by filename (should be timestamp-based)
            
            if alert_files:
                for i, file_path in enumerate(alert_files[:5]):
                    try:
                        with open(file_path, 'r') as f:
                            alert = json.load(f)
                            
                        priority_emoji = "🔴" if alert.get("priority") == "Critical" else "🟠"
                        dashboard.append(f"\n### {priority_emoji} {alert.get('title', 'Unnamed Alert')}")
                        dashboard.append(f"\n- **ID**: {alert.get('id', 'Unknown')}")
                        dashboard.append(f"- **Priority**: {alert.get('priority', 'Unknown')}")
                        dashboard.append(f"- **Source**: {alert.get('source', 'Unknown')}")
                        dashboard.append(f"- **Time**: {datetime.fromisoformat(alert.get('created_at', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if alert.get("description"):
                            dashboard.append(f"\n{alert['description']}")
                            
                    except Exception as e:
                        logger.error(f"Error loading alert file {file_path}: {e}")
            else:
                dashboard.append("\nNo recent alerts.")
            
            # Add recent reports section
            dashboard.append("\n## Recent Threat Reports")
            
            # Get recent reports (last 3)
            report_files = glob.glob(os.path.join("data/reports", "*.md"))
            report_files.sort(reverse=True)  # Sort by filename (should be timestamp-based)
            
            if report_files:
                for i, file_path in enumerate(report_files[:3]):
                    try:
                        # Extract report ID from filename
                        report_id = os.path.basename(file_path).replace("threat-report-", "").replace(".md", "")
                        
                        # Read the first few lines of the report
                        with open(file_path, 'r') as f:
                            report_lines = [next(f) for _ in range(5)]
                        
                        dashboard.append(f"\n### Threat Report {report_id}")
                        dashboard.append(f"\n[View full report]({file_path})")
                        dashboard.append("\n```")
                        dashboard.extend(report_lines)
                        dashboard.append("...")
                        dashboard.append("```")
                        
                    except Exception as e:
                        logger.error(f"Error loading report file {file_path}: {e}")
            else:
                dashboard.append("\nNo recent threat reports.")
            
            # Write the dashboard file
            with open("deep_web_intelligence_dashboard.md", 'w') as f:
                f.write("\n".join(dashboard))
                
            logger.info("Dashboard updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}", exc_info=True)
    
    def _check_taxii_import(self):
        """Check if TAXII import is needed and import if needed."""
        last_import = self.config["last_taxii_import"]
        import_interval = timedelta(hours=self.config["taxii_import_interval"])
        
        if (last_import is None or 
            (datetime.fromisoformat(last_import) + import_interval) <= datetime.now()):
            self._import_from_taxii()
            self.config["last_taxii_import"] = datetime.now().isoformat()
            self._save_config()
    
    def _import_from_taxii(self):
        """Import intelligence from TAXII server."""
        logger.info("Importing intelligence from TAXII server")
        
        if not security.STIX_AVAILABLE:
            logger.warning("STIX/TAXII libraries not available, skipping import")
            return
        
        try:
            # Use the security module to import STIX indicators
            indicators = security.import_stix_indicators(limit=100)
            
            if indicators:
                logger.info(f"Imported {len(indicators)} indicators from TAXII server")
            else:
                logger.info("No new indicators imported from TAXII server")
                
        except Exception as e:
            logger.error(f"Error importing from TAXII server: {e}", exc_info=True)
    
    def _check_stix_export(self):
        """Check if STIX export is needed and export if needed."""
        last_export = self.config["last_stix_export"]
        export_interval = timedelta(hours=self.config["stix_export_interval"])
        
        if (last_export is None or 
            (datetime.fromisoformat(last_export) + export_interval) <= datetime.now()):
            self._export_to_stix()
            self.config["last_stix_export"] = datetime.now().isoformat()
            self._save_config()
    
    def _export_to_stix(self):
        """Export intelligence to STIX format."""
        logger.info("Exporting intelligence to STIX format")
        
        if not security.STIX_AVAILABLE:
            logger.warning("STIX/TAXII libraries not available, skipping export")
            return
        
        try:
            # Use the security module to export IOCs to STIX
            stix_bundle = security.export_iocs_to_stix()
            
            if stix_bundle:
                logger.info(f"Exported IOCs to STIX format: {stix_bundle}")
            else:
                logger.info("No IOCs exported to STIX format")
                
        except Exception as e:
            logger.error(f"Error exporting to STIX: {e}", exc_info=True)
    
    def _save_config(self):
        """Save the current configuration to file."""
        try:
            with open("deep_web_monitor_config.json", 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def _load_proxies(self):
        """Load proxy list from file or from a secure service."""
        proxy_file = os.path.join('config', 'proxies.json')
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r') as f:
                    proxy_data = json.load(f)
                    self.proxies = proxy_data.get('proxies', [])
                logger.info(f"Loaded {len(self.proxies)} proxies from configuration")
            except Exception as e:
                logger.error(f"Error loading proxies: {str(e)}")
                self.proxies = []
        else:
            # Default to empty list if file doesn't exist
            self.proxies = []
            logger.warning("No proxy configuration found, will use direct connections")
    
    def _get_next_proxy(self) -> Dict[str, str]:
        """Get the next proxy in the rotation."""
        if not self.proxies:
            return {}
            
        # Check if we need to refresh the proxy list
        if (datetime.now() - self.proxy_last_updated).total_seconds() > 86400:  # 24 hours
            self._load_proxies()
            self.proxy_last_updated = datetime.now()
            
        # Rotate proxies
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    @on_exception(expo, (RequestException, ConnectionError, Timeout), max_tries=3)
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Tuple[bool, Any]:
        """
        Make a request with retry logic and proxy rotation.
        
        Args:
            url: The URL to request
            method: HTTP method to use
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Tuple of (success, response data or error message)
        """
        # Increment request counter and check if we need to rotate proxy
        self.request_count += 1
        if self.config.get("use_proxy_rotation", True) and self.proxies and \
           self.request_count % self.config.get("proxy_rotation_interval", 10) == 0:
            logger.info("Rotating proxy for next request batch")
        
        # Get proxy if proxy rotation is enabled
        if self.config.get("use_proxy_rotation", True) and self.proxies:
            proxy = self._get_next_proxy()
            if proxy:
                kwargs.setdefault('proxies', proxy)
        
        try:
            # Add a user agent to avoid basic blocking
            headers = kwargs.get('headers', {})
            if not headers.get('User-Agent'):
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            kwargs['headers'] = headers
            
            # Make the request
            response = requests.request(method, url, timeout=30, **kwargs)
            if response.status_code < 400:
                return True, response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
            else:
                logger.warning(f"Request to {url} failed with status code {response.status_code}")
                return False, f"HTTP error: {response.status_code}"
                
        except Timeout:
            logger.error(f"Request to {url} timed out")
            return False, "Request timed out"
        except ConnectionError:
            logger.error(f"Connection error when requesting {url}")
            return False, "Connection error"
        except RequestException as e:
            logger.error(f"Request error when accessing {url}: {str(e)}")
            return False, f"Request error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error when accessing {url}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Deep Web Intelligence Monitor')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    # Create and start the monitor
    monitor = DeepWebMonitor(config_path=args.config)
    try:
        monitor.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 