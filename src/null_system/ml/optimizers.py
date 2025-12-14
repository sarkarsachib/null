"""Gradient-free optimizers for model adaptation."""

from abc import ABC, abstractmethod
from typing import Callable, Tuple, List
import numpy as np


class GradientFreeOptimizer(ABC):
    """Base class for gradient-free optimizers."""

    @abstractmethod
    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        initial: np.ndarray,
        max_iterations: int = 100,
    ) -> Tuple[np.ndarray, float, List[float]]:
        """Optimize objective function.
        
        Args:
            objective: Function to minimize
            initial: Initial parameters
            max_iterations: Maximum iterations
            
        Returns:
            Tuple of (best_params, best_loss, loss_history)
        """


class NelderMeadOptimizer(GradientFreeOptimizer):
    """Nelder-Mead simplex optimizer."""

    def __init__(self, alpha: float = 1.0, beta: float = 0.5, gamma: float = 2.0):
        """Initialize Nelder-Mead optimizer.
        
        Args:
            alpha: Reflection coefficient
            beta: Contraction coefficient
            gamma: Expansion coefficient
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        initial: np.ndarray,
        max_iterations: int = 100,
    ) -> Tuple[np.ndarray, float, List[float]]:
        """Optimize using Nelder-Mead simplex method.
        
        Args:
            objective: Function to minimize
            initial: Initial parameters
            max_iterations: Maximum iterations
            
        Returns:
            Tuple of (best_params, best_loss, loss_history)
        """
        dim = len(initial)
        
        # Initialize simplex
        simplex = self._create_simplex(initial, dim)
        losses = [objective(point) for point in simplex]
        
        loss_history = []
        
        for iteration in range(max_iterations):
            # Sort by loss
            sorted_indices = np.argsort(losses)
            simplex = simplex[sorted_indices]
            losses = [losses[i] for i in sorted_indices]
            
            loss_history.append(losses[0])
            
            # Centroid of best points
            centroid = np.mean(simplex[:-1], axis=0)
            
            # Reflection
            reflected = centroid + self.alpha * (centroid - simplex[-1])
            reflected_loss = objective(reflected)
            
            if reflected_loss < losses[-2]:
                if reflected_loss < losses[0]:
                    # Expansion
                    expanded = centroid + self.gamma * (reflected - centroid)
                    expanded_loss = objective(expanded)
                    
                    if expanded_loss < reflected_loss:
                        simplex[-1] = expanded
                        losses[-1] = expanded_loss
                    else:
                        simplex[-1] = reflected
                        losses[-1] = reflected_loss
                else:
                    simplex[-1] = reflected
                    losses[-1] = reflected_loss
            else:
                # Contraction
                contracted = centroid + self.beta * (simplex[-1] - centroid)
                contracted_loss = objective(contracted)
                
                if contracted_loss < losses[-1]:
                    simplex[-1] = contracted
                    losses[-1] = contracted_loss
                else:
                    # Shrinkage
                    simplex[1:] = simplex[0] + 0.5 * (simplex[1:] - simplex[0])
                    losses[1:] = [objective(point) for point in simplex[1:]]
        
        best_idx = np.argmin(losses)
        return simplex[best_idx], losses[best_idx], loss_history

    def _create_simplex(self, initial: np.ndarray, dim: int) -> np.ndarray:
        """Create initial simplex."""
        simplex = [initial.copy()]
        for i in range(dim):
            point = initial.copy()
            point[i] += 1.0
            simplex.append(point)
        return np.array(simplex)


class CMAESOptimizer(GradientFreeOptimizer):
    """Covariance Matrix Adaptation Evolution Strategy (CMA-ES)."""

    def __init__(
        self,
        population_size: int = 20,
        initial_sigma: float = 1.0,
    ):
        """Initialize CMA-ES optimizer.
        
        Args:
            population_size: Population size
            initial_sigma: Initial step-size
        """
        self.population_size = population_size
        self.initial_sigma = initial_sigma

    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        initial: np.ndarray,
        max_iterations: int = 100,
    ) -> Tuple[np.ndarray, float, List[float]]:
        """Optimize using CMA-ES.
        
        Args:
            objective: Function to minimize
            initial: Initial parameters
            max_iterations: Maximum iterations
            
        Returns:
            Tuple of (best_params, best_loss, loss_history)
        """
        dim = len(initial)
        
        # Initialize
        m = initial.copy()
        sigma = self.initial_sigma
        C = np.eye(dim)
        pc = np.zeros(dim)
        ps = np.zeros(dim)
        
        eigenvalues, eigenvectors = np.linalg.eigh(C)
        B = eigenvectors
        D = np.sqrt(np.abs(eigenvalues))
        
        loss_history = []
        best_loss = float('inf')
        best_params = m.copy()
        
        for iteration in range(max_iterations):
            # Sample population
            population = []
            losses = []
            
            for _ in range(self.population_size):
                z = np.random.randn(dim)
                y = B @ (D * z)
                x = m + sigma * y
                
                loss = objective(x)
                population.append((x, loss))
                losses.append(loss)
                
                if loss < best_loss:
                    best_loss = loss
                    best_params = x.copy()
            
            loss_history.append(best_loss)
            
            # Select elite
            sorted_pop = sorted(population, key=lambda x: x[1])
            elite = sorted_pop[:self.population_size//2]
            
            # Update mean
            m_old = m.copy()
            m = np.mean([x[0] for x in elite], axis=0)
            
            # Simple step-size adaptation
            sigma *= np.exp(0.01 * (np.mean(losses[:self.population_size//2]) - 
                                   np.mean(losses[self.population_size//2:])))
            sigma = np.clip(sigma, 1e-6, 1e1)
        
        return best_params, best_loss, loss_history


class RandomSearchOptimizer(GradientFreeOptimizer):
    """Simple random search optimizer."""

    def __init__(self, search_radius: float = 1.0):
        """Initialize random search optimizer.
        
        Args:
            search_radius: Search radius around initial point
        """
        self.search_radius = search_radius

    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        initial: np.ndarray,
        max_iterations: int = 100,
    ) -> Tuple[np.ndarray, float, List[float]]:
        """Optimize using random search.
        
        Args:
            objective: Function to minimize
            initial: Initial parameters
            max_iterations: Maximum iterations
            
        Returns:
            Tuple of (best_params, best_loss, loss_history)
        """
        dim = len(initial)
        best_params = initial.copy()
        best_loss = objective(best_params)
        
        loss_history = [best_loss]
        
        for _ in range(max_iterations):
            # Random perturbation
            perturbation = np.random.randn(dim) * self.search_radius
            candidate = initial + perturbation
            
            loss = objective(candidate)
            loss_history.append(min(loss, loss_history[-1]))
            
            if loss < best_loss:
                best_loss = loss
                best_params = candidate.copy()
        
        return best_params, best_loss, loss_history
