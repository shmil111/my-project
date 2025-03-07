"""
Plugin DNA - Core genetic structure for the evolutionary plugin system.

This module defines the fundamental building blocks of plugin evolution,
including genetic markers, mutation patterns, and adaptation capabilities.
"""
import logging
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class GeneticMarker:
    """Represents a specific trait or capability in the plugin's DNA."""
    name: str
    strength: float = 1.0
    mutations: int = 0
    last_mutation: Optional[datetime] = None
    dependencies: Set[str] = field(default_factory=set)
    
    def mutate(self, factor: float = 1.0) -> bool:
        """
        Attempt to mutate this genetic marker.
        
        Args:
            factor: Mutation strength factor
            
        Returns:
            bool: True if mutation was successful
        """
        if factor <= 0:
            return False
            
        self.mutations += 1
        self.last_mutation = datetime.now()
        self.strength *= (1.0 + (factor * 0.1))
        
        # Cap strength at reasonable limits
        self.strength = min(max(self.strength, 0.1), 10.0)
        return True

@dataclass
class PluginDNA:
    """
    Represents the genetic structure of a plugin.
    
    This is the core of the plugin evolution system, defining how
    plugins can adapt, evolve, and interact with the ecosystem.
    """
    
    plugin_id: str
    creation_time: datetime = field(default_factory=datetime.now)
    generation: int = 0
    fitness_score: float = 1.0
    markers: Dict[str, GeneticMarker] = field(default_factory=dict)
    mutation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def create_from_plugin(cls, plugin: Any) -> 'PluginDNA':
        """
        Create DNA structure from an existing plugin.
        
        Args:
            plugin: The plugin instance to analyze
            
        Returns:
            PluginDNA: The generated DNA structure
        """
        # Generate unique ID based on plugin properties
        plugin_id = hashlib.sha256(
            f"{plugin.name}:{plugin.version}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        dna = cls(plugin_id=plugin_id)
        
        # Extract genetic markers from plugin attributes
        for attr_name in dir(plugin):
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(plugin, attr_name)
            if callable(attr):
                # Function-based markers
                dna.add_marker(f"function:{attr_name}", 1.0)
            elif isinstance(attr, property):
                # Property-based markers
                dna.add_marker(f"property:{attr_name}", 1.0)
        
        # Add dependency markers
        for dep in getattr(plugin, 'dependencies', []):
            dna.add_marker(f"dependency:{dep}", 1.0, {dep})
        
        return dna
    
    def add_marker(self, name: str, strength: float = 1.0, 
                  dependencies: Optional[Set[str]] = None) -> None:
        """
        Add a genetic marker to the DNA.
        
        Args:
            name: Marker name
            strength: Initial strength
            dependencies: Optional set of dependencies
        """
        if name in self.markers:
            logger.warning(f"Marker {name} already exists in DNA")
            return
            
        self.markers[name] = GeneticMarker(
            name=name,
            strength=strength,
            dependencies=dependencies or set()
        )
    
    def mutate(self, factor: float = 1.0) -> bool:
        """
        Trigger mutation in the DNA structure.
        
        Args:
            factor: Mutation strength factor
            
        Returns:
            bool: True if any mutations occurred
        """
        if factor <= 0:
            return False
            
        mutations_occurred = False
        mutation_record = {
            "timestamp": datetime.now().isoformat(),
            "factor": factor,
            "changes": []
        }
        
        for marker in self.markers.values():
            if marker.mutate(factor):
                mutations_occurred = True
                mutation_record["changes"].append({
                    "marker": marker.name,
                    "new_strength": marker.strength,
                    "mutations": marker.mutations
                })
        
        if mutations_occurred:
            self.generation += 1
            self.mutation_history.append(mutation_record)
            
        return mutations_occurred
    
    def calculate_fitness(self, environment: Dict[str, float]) -> float:
        """
        Calculate fitness score based on environmental factors.
        
        Args:
            environment: Dictionary of environmental factors and their weights
            
        Returns:
            float: The calculated fitness score
        """
        if not environment:
            return self.fitness_score
            
        total_score = 0.0
        total_weight = 0.0
        
        for factor, weight in environment.items():
            if factor in self.markers:
                total_score += self.markers[factor].strength * weight
                total_weight += weight
        
        if total_weight > 0:
            self.fitness_score = total_score / total_weight
        
        return self.fitness_score
    
    def can_reproduce_with(self, other: 'PluginDNA') -> bool:
        """
        Check if this DNA can reproduce with another.
        
        Args:
            other: Another PluginDNA instance
            
        Returns:
            bool: True if reproduction is possible
        """
        # Check for minimum shared markers
        shared_markers = set(self.markers.keys()) & set(other.markers.keys())
        return len(shared_markers) >= min(len(self.markers), len(other.markers)) // 2
    
    def reproduce_with(self, other: 'PluginDNA') -> Optional['PluginDNA']:
        """
        Create new DNA by combining with another.
        
        Args:
            other: Another PluginDNA instance
            
        Returns:
            Optional[PluginDNA]: New DNA instance or None if reproduction failed
        """
        if not self.can_reproduce_with(other):
            return None
            
        # Create new DNA with combined ID
        new_id = hashlib.sha256(
            f"{self.plugin_id}:{other.plugin_id}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        offspring = PluginDNA(plugin_id=new_id)
        
        # Combine markers from both parents
        all_markers = set(self.markers.keys()) | set(other.markers.keys())
        for marker_name in all_markers:
            marker1 = self.markers.get(marker_name)
            marker2 = other.markers.get(marker_name)
            
            if marker1 and marker2:
                # Average strength for shared markers
                strength = (marker1.strength + marker2.strength) / 2
                deps = marker1.dependencies | marker2.dependencies
            else:
                # Use existing marker values for unique markers
                marker = marker1 or marker2
                strength = marker.strength
                deps = marker.dependencies
            
            offspring.add_marker(marker_name, strength, deps)
        
        offspring.generation = max(self.generation, other.generation) + 1
        return offspring
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DNA to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of DNA
        """
        return {
            "plugin_id": self.plugin_id,
            "creation_time": self.creation_time.isoformat(),
            "generation": self.generation,
            "fitness_score": self.fitness_score,
            "markers": {
                name: {
                    "strength": marker.strength,
                    "mutations": marker.mutations,
                    "last_mutation": marker.last_mutation.isoformat() if marker.last_mutation else None,
                    "dependencies": list(marker.dependencies)
                }
                for name, marker in self.markers.items()
            },
            "mutation_history": self.mutation_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginDNA':
        """
        Create DNA from dictionary representation.
        
        Args:
            data: Dictionary representation of DNA
            
        Returns:
            PluginDNA: New DNA instance
        """
        dna = cls(plugin_id=data["plugin_id"])
        dna.creation_time = datetime.fromisoformat(data["creation_time"])
        dna.generation = data["generation"]
        dna.fitness_score = data["fitness_score"]
        dna.mutation_history = data["mutation_history"]
        
        for name, marker_data in data["markers"].items():
            dna.markers[name] = GeneticMarker(
                name=name,
                strength=marker_data["strength"],
                mutations=marker_data["mutations"],
                last_mutation=datetime.fromisoformat(marker_data["last_mutation"]) 
                    if marker_data["last_mutation"] else None,
                dependencies=set(marker_data["dependencies"])
            )
        
        return dna 