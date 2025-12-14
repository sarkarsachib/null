"""Benchmarking utilities for ML models."""

import time
import tracemalloc
from typing import Dict, List, Tuple, Callable, Any
import psutil
import os


class BenchmarkMetrics:
    """Container for benchmark metrics."""

    def __init__(self):
        """Initialize metrics."""
        self.latencies: List[float] = []
        self.memory_peak: float = 0.0
        self.memory_avg: float = 0.0
        self.throughput: float = 0.0
        self.model_size: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "latency_min": min(self.latencies) if self.latencies else 0,
            "latency_max": max(self.latencies) if self.latencies else 0,
            "latency_mean": sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            "latency_median": sorted(self.latencies)[len(self.latencies)//2] if self.latencies else 0,
            "latency_p95": sorted(self.latencies)[int(0.95*len(self.latencies))] if self.latencies else 0,
            "memory_peak_mb": self.memory_peak,
            "memory_avg_mb": self.memory_avg,
            "throughput": self.throughput,
            "model_size_mb": self.model_size,
        }

    def __str__(self) -> str:
        """String representation."""
        d = self.to_dict()
        return (
            f"Latency (ms): min={d['latency_min']:.2f}, "
            f"mean={d['latency_mean']:.2f}, "
            f"median={d['latency_median']:.2f}, "
            f"p95={d['latency_p95']:.2f}, "
            f"max={d['latency_max']:.2f}\n"
            f"Memory: peak={d['memory_peak_mb']:.2f}MB, "
            f"avg={d['memory_avg_mb']:.2f}MB\n"
            f"Throughput: {d['throughput']:.2f} samples/sec\n"
            f"Model size: {d['model_size_mb']:.2f}MB"
        )


class ModelBenchmark:
    """Benchmark a model's performance."""

    def __init__(self, warmup_runs: int = 5, num_runs: int = 100):
        """Initialize benchmark.
        
        Args:
            warmup_runs: Number of warmup runs
            num_runs: Number of benchmark runs
        """
        self.warmup_runs = warmup_runs
        self.num_runs = num_runs

    def benchmark(
        self,
        fn: Callable[[], Any],
        model_size_bytes: int = 0,
    ) -> BenchmarkMetrics:
        """Benchmark a function.
        
        Args:
            fn: Function to benchmark
            model_size_bytes: Model size in bytes
            
        Returns:
            BenchmarkMetrics
        """
        # Warmup
        for _ in range(self.warmup_runs):
            fn()
        
        metrics = BenchmarkMetrics()
        metrics.model_size = model_size_bytes / 1e6
        
        # Memory tracking
        tracemalloc.start()
        process = psutil.Process(os.getpid())
        memory_samples = []
        
        # Benchmark runs
        for _ in range(self.num_runs):
            mem_before = process.memory_info().rss / 1e6
            
            start = time.perf_counter()
            fn()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            
            mem_after = process.memory_info().rss / 1e6
            memory_samples.append(mem_after)
            
            metrics.latencies.append(elapsed)
        
        metrics.memory_peak = max(memory_samples)
        metrics.memory_avg = sum(memory_samples) / len(memory_samples)
        metrics.throughput = (self.num_runs * 1000) / sum(metrics.latencies)
        
        tracemalloc.stop()
        
        return metrics


class LatencyProfiler:
    """Profile latency of operations."""

    def __init__(self):
        """Initialize profiler."""
        self._measurements: Dict[str, List[float]] = {}

    def measure(self, name: str, fn: Callable[[], Any]) -> Any:
        """Measure execution time of function.
        
        Args:
            name: Operation name
            fn: Function to measure
            
        Returns:
            Function result
        """
        start = time.perf_counter()
        result = fn()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        if name not in self._measurements:
            self._measurements[name] = []
        
        self._measurements[name].append(elapsed)
        
        return result

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for an operation.
        
        Args:
            name: Operation name
            
        Returns:
            Statistics dictionary
        """
        if name not in self._measurements:
            return {}
        
        measurements = self._measurements[name]
        return {
            "min": min(measurements),
            "max": max(measurements),
            "mean": sum(measurements) / len(measurements),
            "median": sorted(measurements)[len(measurements)//2],
            "count": len(measurements),
        }

    def summary(self) -> str:
        """Get summary of all measurements.
        
        Returns:
            Summary string
        """
        lines = ["[Latency Profile]"]
        
        for name in sorted(self._measurements.keys()):
            stats = self.get_stats(name)
            lines.append(
                f"  {name}: min={stats['min']:.2f}ms, "
                f"mean={stats['mean']:.2f}ms, "
                f"median={stats['median']:.2f}ms, "
                f"max={stats['max']:.2f}ms (n={stats['count']})"
            )
        
        return "\n".join(lines)


class MemoryProfiler:
    """Profile memory usage."""

    @staticmethod
    def get_peak_memory(fn: Callable[[], Any]) -> Tuple[float, Any]:
        """Get peak memory usage of function.
        
        Args:
            fn: Function to profile
            
        Returns:
            Tuple of (peak_memory_mb, result)
        """
        tracemalloc.start()
        
        result = fn()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return peak / 1e6, result

    @staticmethod
    def estimate_size(obj: Any) -> int:
        """Estimate object size in bytes.
        
        Args:
            obj: Object to estimate
            
        Returns:
            Estimated size in bytes
        """
        if hasattr(obj, 'nbytes'):  # NumPy array
            return int(obj.nbytes)
        
        if hasattr(obj, '__sizeof__'):
            return obj.__sizeof__()
        
        return 0
