"""
Plugin Ecosystem - Environmental management for evolving plugins.

This module manages the plugin environment, including resource allocation,
plugin interactions, and evolutionary pressures.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from .PluginDNA import PluginDNA
from .manager import plugin_manager

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentalFactor:
    """Represents an environmental pressure or condition."""
    name: str
    weight: float = 1.0
    description: str = ""
    active: bool = True
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class ResourcePool:
    """Manages available resources for plugins."""
    total: float = 100.0
    allocated: Dict[str, float] = field(default_factory=dict)
    threshold: float = 0.1
    
    def allocate(self, plugin_id: str, amount: float) -> bool:
        """
        Attempt to allocate resources to a plugin.
        
        Args:
            plugin_id: Plugin identifier
            amount: Amount of resources to allocate
            
        Returns:
            bool: True if allocation was successful
        """
        available = self.total - sum(self.allocated.values())
        if amount > available or amount < self.threshold:
            return False
            
        self.allocated[plugin_id] = amount
        return True
    
    def release(self, plugin_id: str) -> float:
        """
        Release resources allocated to a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            float: Amount of resources released
        """
        return self.allocated.pop(plugin_id, 0.0)

class PluginEcosystem:
    """
    Manages the plugin ecosystem environment.
    
    This class handles:
    - Environmental factors affecting plugins
    - Resource allocation and management
    - Plugin interaction and evolution
    - Ecosystem health monitoring
    """
    
    def __init__(self):
        """Initialize the plugin ecosystem."""
        self.factors: Dict[str, EnvironmentalFactor] = {}
        self.resources = ResourcePool()
        self.plugin_dna: Dict[str, PluginDNA] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        self._data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ecosystem_data"
        )
        
        # Create data directory if it doesn't exist
        os.makedirs(self._data_dir, exist_ok=True)
        
        # Initialize default environmental factors
        self._initialize_default_factors()
    
    def _initialize_default_factors(self) -> None:
        """Initialize default environmental factors."""
        defaults = {
            "memory_pressure": {
                "weight": 1.5,
                "description": "System memory availability"
            },
            "cpu_load": {
                "weight": 1.2,
                "description": "CPU utilization pressure"
            },
            "api_usage": {
                "weight": 1.0,
                "description": "API endpoint utilization"
            },
            "error_rate": {
                "weight": 2.0,
                "description": "System error frequency"
            },
            "user_interaction": {
                "weight": 1.3,
                "description": "User engagement level"
            }
        }
        
        for name, data in defaults.items():
            self.add_factor(name, data["weight"], data["description"])
    
    def add_factor(self, name: str, weight: float, description: str = "") -> None:
        """
        Add an environmental factor.
        
        Args:
            name: Factor name
            weight: Factor weight
            description: Factor description
        """
        if name in self.factors:
            logger.warning(f"Environmental factor {name} already exists")
            return
            
        self.factors[name] = EnvironmentalFactor(
            name=name,
            weight=weight,
            description=description
        )
        logger.info(f"Added environmental factor: {name}")
    
    def register_plugin(self, plugin: Any) -> bool:
        """
        Register a plugin with the ecosystem.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            bool: True if registration was successful
        """
        try:
            # Create DNA profile
            dna = PluginDNA.create_from_plugin(plugin)
            
            # Allocate initial resources
            if not self.resources.allocate(dna.plugin_id, 1.0):
                logger.error(f"Failed to allocate resources for plugin {plugin.name}")
                return False
            
            # Store DNA profile
            self.plugin_dna[plugin.name] = dna
            
            # Calculate initial fitness
            environment = {
                name: factor.weight
                for name, factor in self.factors.items()
                if factor.active
            }
            dna.calculate_fitness(environment)
            
            logger.info(
                f"Registered plugin {plugin.name} (DNA: {dna.plugin_id}) "
                f"with fitness {dna.fitness_score:.2f}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {str(e)}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the ecosystem.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            bool: True if unregistration was successful
        """
        if plugin_name not in self.plugin_dna:
            logger.warning(f"Plugin {plugin_name} not registered in ecosystem")
            return False
            
        dna = self.plugin_dna[plugin_name]
        self.resources.release(dna.plugin_id)
        del self.plugin_dna[plugin_name]
        
        logger.info(f"Unregistered plugin {plugin_name}")
        return True
    
    def update_environment(self, metrics: Dict[str, float]) -> None:
        """
        Update environmental factors based on metrics.
        
        Args:
            metrics: Dictionary of metric names to values
        """
        timestamp = datetime.now()
        
        for name, value in metrics.items():
            if name in self.factors:
                factor = self.factors[name]
                factor.weight = value
                factor.last_update = timestamp
                logger.debug(f"Updated factor {name} to {value}")
    
    def trigger_evolution(self) -> Dict[str, Any]:
        """
        Trigger evolutionary cycle in the ecosystem.
        
        Returns:
            Dict[str, Any]: Evolution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "mutations": [],
            "reproductions": [],
            "extinctions": []
        }
        
        # Get current environment
        environment = {
            name: factor.weight
            for name, factor in self.factors.items()
            if factor.active
        }
        
        # Update fitness scores
        fitness_scores = {}
        for name, dna in self.plugin_dna.items():
            fitness_scores[name] = dna.calculate_fitness(environment)
        
        # Trigger mutations based on fitness
        for name, dna in self.plugin_dna.items():
            if dna.mutate(fitness_scores[name]):
                results["mutations"].append({
                    "plugin": name,
                    "dna_id": dna.plugin_id,
                    "fitness": fitness_scores[name]
                })
        
        # Attempt reproduction between compatible plugins
        plugin_names = list(self.plugin_dna.keys())
        for i in range(len(plugin_names)):
            for j in range(i + 1, len(plugin_names)):
                name1, name2 = plugin_names[i], plugin_names[j]
                dna1, dna2 = self.plugin_dna[name1], self.plugin_dna[name2]
                
                offspring = dna1.reproduce_with(dna2)
                if offspring:
                    results["reproductions"].append({
                        "parents": [name1, name2],
                        "offspring_id": offspring.plugin_id
                    })
        
        # Handle potential extinctions
        extinction_threshold = 0.3
        for name, dna in list(self.plugin_dna.items()):
            if fitness_scores[name] < extinction_threshold:
                self.unregister_plugin(name)
                results["extinctions"].append({
                    "plugin": name,
                    "dna_id": dna.plugin_id,
                    "fitness": fitness_scores[name]
                })
        
        # Record interaction
        self.interaction_history.append(results)
        return results
    
    def get_ecosystem_state(self) -> Dict[str, Any]:
        """
        Get current state of the ecosystem.
        
        Returns:
            Dict[str, Any]: Ecosystem state data
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "factors": {
                name: {
                    "weight": factor.weight,
                    "active": factor.active,
                    "last_update": factor.last_update.isoformat()
                }
                for name, factor in self.factors.items()
            },
            "resources": {
                "total": self.resources.total,
                "allocated": dict(self.resources.allocated),
                "available": self.resources.total - sum(self.resources.allocated.values())
            },
            "plugins": {
                name: dna.to_dict()
                for name, dna in self.plugin_dna.items()
            },
            "history": self.interaction_history[-10:]  # Last 10 interactions
        }
    
    def save_state(self) -> bool:
        """
        Save ecosystem state to disk.
        
        Returns:
            bool: True if save was successful
        """
        try:
            state = self.get_ecosystem_state()
            state_file = os.path.join(self._data_dir, "ecosystem_state.json")
            
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
            
            logger.info("Saved ecosystem state to disk")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save ecosystem state: {str(e)}")
            return False
    
    def load_state(self) -> bool:
        """
        Load ecosystem state from disk.
        
        Returns:
            bool: True if load was successful
        """
        try:
            state_file = os.path.join(self._data_dir, "ecosystem_state.json")
            
            if not os.path.exists(state_file):
                logger.warning("No ecosystem state file found")
                return False
            
            with open(state_file, "r") as f:
                state = json.load(f)
            
            # Restore environmental factors
            self.factors.clear()
            for name, data in state["factors"].items():
                self.add_factor(
                    name=name,
                    weight=data["weight"],
                    description=""  # Description not stored in state
                )
                self.factors[name].active = data["active"]
                self.factors[name].last_update = datetime.fromisoformat(
                    data["last_update"]
                )
            
            # Restore plugin DNA
            self.plugin_dna.clear()
            for name, dna_data in state["plugins"].items():
                self.plugin_dna[name] = PluginDNA.from_dict(dna_data)
            
            # Restore interaction history
            self.interaction_history = state.get("history", [])
            
            logger.info("Loaded ecosystem state from disk")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ecosystem state: {str(e)}")
            return False 