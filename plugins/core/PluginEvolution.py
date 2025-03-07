"""
Plugin Evolution - Evolutionary algorithms for plugin adaptation.

This module implements the evolutionary algorithms that drive plugin
adaptation and improvement over time.
"""
import logging
import random
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field

from .PluginDNA import PluginDNA
from .PluginEcosystem import PluginEcosystem

logger = logging.getLogger(__name__)

@dataclass
class EvolutionConfig:
    """Configuration for evolution parameters."""
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    population_size: int = 100
    generation_limit: int = 1000
    fitness_threshold: float = 0.8
    extinction_threshold: float = 0.3
    elite_size: int = 5
    tournament_size: int = 3

@dataclass
class EvolutionMetrics:
    """Metrics tracking evolution progress."""
    generation: int = 0
    best_fitness: float = 0.0
    average_fitness: float = 0.0
    worst_fitness: float = 0.0
    mutation_count: int = 0
    crossover_count: int = 0
    extinction_count: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

class PluginEvolution:
    """
    Manages plugin evolution through genetic algorithms.
    
    This class implements:
    - Genetic algorithm operations
    - Fitness evaluation
    - Population management
    - Evolution tracking
    """
    
    def __init__(self, ecosystem: PluginEcosystem, config: Optional[EvolutionConfig] = None):
        """
        Initialize the evolution manager.
        
        Args:
            ecosystem: The plugin ecosystem to evolve
            config: Optional evolution configuration
        """
        self.ecosystem = ecosystem
        self.config = config or EvolutionConfig()
        self.metrics = EvolutionMetrics()
        self.population: List[PluginDNA] = []
        
        # Initialize RNG for reproducibility
        self.rng = random.Random()
        self.rng.seed(int(datetime.now().timestamp()))
    
    def initialize_population(self) -> None:
        """Initialize the evolution population."""
        # Start with existing plugins
        self.population = list(self.ecosystem.plugin_dna.values())
        
        # Generate additional random variants if needed
        while len(self.population) < self.config.population_size:
            if self.population:
                # Create variant of existing plugin
                template = self.rng.choice(self.population)
                variant = PluginDNA(
                    plugin_id=f"{template.plugin_id}_variant_{len(self.population)}"
                )
                
                # Copy and mutate markers
                for name, marker in template.markers.items():
                    variant.add_marker(
                        name=name,
                        strength=marker.strength * (0.5 + self.rng.random()),
                        dependencies=marker.dependencies.copy()
                    )
                
                self.population.append(variant)
            else:
                # Create basic plugin if none exist
                basic = PluginDNA(f"basic_plugin_{len(self.population)}")
                basic.add_marker("core", 1.0)
                self.population.append(basic)
    
    def evaluate_fitness(self, dna: PluginDNA) -> float:
        """
        Evaluate fitness of a DNA instance.
        
        Args:
            dna: The DNA instance to evaluate
            
        Returns:
            float: Calculated fitness score
        """
        # Get current environment
        environment = {
            name: factor.weight
            for name, factor in self.ecosystem.factors.items()
            if factor.active
        }
        
        return dna.calculate_fitness(environment)
    
    def select_parent(self) -> PluginDNA:
        """
        Select a parent using tournament selection.
        
        Returns:
            PluginDNA: Selected parent
        """
        tournament = self.rng.sample(self.population, self.config.tournament_size)
        return max(tournament, key=self.evaluate_fitness)
    
    def crossover(self, parent1: PluginDNA, parent2: PluginDNA) -> Optional[PluginDNA]:
        """
        Perform crossover between two parents.
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            Optional[PluginDNA]: New offspring or None if crossover failed
        """
        if self.rng.random() > self.config.crossover_rate:
            return None
            
        offspring = parent1.reproduce_with(parent2)
        if offspring:
            self.metrics.crossover_count += 1
            
        return offspring
    
    def mutate(self, dna: PluginDNA) -> bool:
        """
        Attempt to mutate a DNA instance.
        
        Args:
            dna: The DNA instance to mutate
            
        Returns:
            bool: True if mutation occurred
        """
        if self.rng.random() > self.config.mutation_rate:
            return False
            
        # Calculate mutation factor based on fitness
        fitness = self.evaluate_fitness(dna)
        factor = 1.0 + ((1.0 - fitness) * 0.5)
        
        if dna.mutate(factor):
            self.metrics.mutation_count += 1
            return True
            
        return False
    
    def evolve_generation(self) -> Dict[str, Any]:
        """
        Evolve the population by one generation.
        
        Returns:
            Dict[str, Any]: Generation statistics
        """
        # Evaluate current population
        fitness_scores = [(dna, self.evaluate_fitness(dna)) for dna in self.population]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Update metrics
        self.metrics.generation += 1
        self.metrics.best_fitness = fitness_scores[0][1]
        self.metrics.worst_fitness = fitness_scores[-1][1]
        self.metrics.average_fitness = sum(f for _, f in fitness_scores) / len(fitness_scores)
        
        # Create new population starting with elite
        new_population = [dna for dna, _ in fitness_scores[:self.config.elite_size]]
        
        # Fill rest of population through selection and reproduction
        while len(new_population) < self.config.population_size:
            parent1 = self.select_parent()
            parent2 = self.select_parent()
            
            offspring = self.crossover(parent1, parent2)
            if offspring:
                self.mutate(offspring)
                new_population.append(offspring)
            else:
                # If crossover fails, clone and mutate parent
                clone = PluginDNA(f"{parent1.plugin_id}_clone_{len(new_population)}")
                for name, marker in parent1.markers.items():
                    clone.add_marker(
                        name=name,
                        strength=marker.strength,
                        dependencies=marker.dependencies.copy()
                    )
                self.mutate(clone)
                new_population.append(clone)
        
        # Handle extinctions
        extinct = [
            dna for dna, fitness in fitness_scores
            if fitness < self.config.extinction_threshold
        ]
        self.metrics.extinction_count += len(extinct)
        
        # Update population
        self.population = new_population
        
        # Record generation stats
        stats = {
            "generation": self.metrics.generation,
            "timestamp": datetime.now().isoformat(),
            "population_size": len(self.population),
            "best_fitness": self.metrics.best_fitness,
            "average_fitness": self.metrics.average_fitness,
            "worst_fitness": self.metrics.worst_fitness,
            "mutations": self.metrics.mutation_count,
            "crossovers": self.metrics.crossover_count,
            "extinctions": self.metrics.extinction_count
        }
        self.metrics.history.append(stats)
        
        return stats
    
    def run_evolution(self, 
                     max_generations: Optional[int] = None,
                     target_fitness: Optional[float] = None,
                     callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Run the evolution process.
        
        Args:
            max_generations: Maximum number of generations to evolve
            target_fitness: Target fitness score to achieve
            callback: Optional callback function called after each generation
            
        Returns:
            Dict[str, Any]: Evolution results
        """
        if not self.population:
            self.initialize_population()
        
        max_generations = max_generations or self.config.generation_limit
        target_fitness = target_fitness or self.config.fitness_threshold
        
        logger.info(
            f"Starting evolution with population size {len(self.population)}, "
            f"target fitness {target_fitness}"
        )
        
        start_time = datetime.now()
        
        while (self.metrics.generation < max_generations and 
               self.metrics.best_fitness < target_fitness):
            
            stats = self.evolve_generation()
            
            if callback:
                try:
                    callback(stats)
                except Exception as e:
                    logger.error(f"Error in evolution callback: {str(e)}")
            
            # Log progress every 10 generations
            if self.metrics.generation % 10 == 0:
                logger.info(
                    f"Generation {self.metrics.generation}: "
                    f"Best={self.metrics.best_fitness:.3f}, "
                    f"Avg={self.metrics.average_fitness:.3f}"
                )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        results = {
            "success": self.metrics.best_fitness >= target_fitness,
            "generations": self.metrics.generation,
            "duration_seconds": duration,
            "final_stats": {
                "best_fitness": self.metrics.best_fitness,
                "average_fitness": self.metrics.average_fitness,
                "population_size": len(self.population),
                "mutations": self.metrics.mutation_count,
                "crossovers": self.metrics.crossover_count,
                "extinctions": self.metrics.extinction_count
            },
            "history": self.metrics.history
        }
        
        logger.info(
            f"Evolution completed in {duration:.1f}s: "
            f"{'Success' if results['success'] else 'Incomplete'} "
            f"after {self.metrics.generation} generations"
        )
        
        return results
    
    def get_best_plugins(self, count: int = 1) -> List[Tuple[PluginDNA, float]]:
        """
        Get the best performing plugins.
        
        Args:
            count: Number of plugins to return
            
        Returns:
            List[Tuple[PluginDNA, float]]: List of (DNA, fitness) tuples
        """
        if not self.population:
            return []
            
        # Evaluate and sort population
        scored = [(dna, self.evaluate_fitness(dna)) for dna in self.population]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:count]
    
    def apply_best_plugins(self) -> Dict[str, Any]:
        """
        Apply the best evolved plugins to the ecosystem.
        
        Returns:
            Dict[str, Any]: Results of applying plugins
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "applied": [],
            "failed": []
        }
        
        # Get top plugins that exceed fitness threshold
        best_plugins = [
            (dna, fitness) for dna, fitness in self.get_best_plugins(count=10)
            if fitness >= self.config.fitness_threshold
        ]
        
        for dna, fitness in best_plugins:
            try:
                # Register plugin with ecosystem
                if self.ecosystem.register_plugin(dna):
                    results["applied"].append({
                        "dna_id": dna.plugin_id,
                        "fitness": fitness
                    })
                else:
                    results["failed"].append({
                        "dna_id": dna.plugin_id,
                        "fitness": fitness,
                        "reason": "Registration failed"
                    })
            except Exception as e:
                results["failed"].append({
                    "dna_id": dna.plugin_id,
                    "fitness": fitness,
                    "reason": str(e)
                })
        
        return results 