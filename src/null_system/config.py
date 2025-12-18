"""Configuration module for optional subsystems and feature flags.

This module manages enable/disable switches and dependency ordering for optional
subsystems that can be integrated with the Null compiler and VM.

The eight blocked subsystems are:
1. AI super-bit core - ML inference and tensor operations
2. Debugger - Step-through debugging and breakpoints
3. Visualizer - AST and execution flow visualization
4. NLP/knowledge layer - Natural language understanding and knowledge graphs
5. Quantum hooks - Quantum computing simulation
6. Secure compression - Advanced encryption and compression
7. AI network storage - Distributed storage with AI optimization
8. Null LSP - Language Server Protocol implementation

Each subsystem can be individually enabled/disabled and has dependencies that are
automatically resolved.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, Optional, List


class Subsystem(str, Enum):
    """Enumeration of optional subsystems."""

    AI_CORE = "ai_core"
    DEBUGGER = "debugger"
    VISUALIZER = "visualizer"
    NLP_KNOWLEDGE = "nlp_knowledge"
    QUANTUM = "quantum"
    SECURE_COMPRESSION = "secure_compression"
    NETWORK_STORAGE = "network_storage"
    NULL_LSP = "null_lsp"


@dataclass
class SubsystemConfig:
    """Configuration for a single subsystem."""

    name: Subsystem
    enabled: bool = False
    dependencies: Set[Subsystem] = field(default_factory=set)
    description: str = ""

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SubsystemConfig):
            return False
        return self.name == other.name


class FeatureConfig:
    """Central feature-flag configuration for optional subsystems.

    Manages enable/disable switches, dependency ordering, and provides access to
    subsystem capabilities. By default, all subsystems are disabled and must be
    explicitly enabled.
    """

    SUBSYSTEM_DEPENDENCIES: Dict[Subsystem, Set[Subsystem]] = {
        Subsystem.AI_CORE: set(),
        Subsystem.DEBUGGER: {Subsystem.VISUALIZER},
        Subsystem.VISUALIZER: set(),
        Subsystem.NLP_KNOWLEDGE: set(),
        Subsystem.QUANTUM: set(),
        Subsystem.SECURE_COMPRESSION: set(),
        Subsystem.NETWORK_STORAGE: {Subsystem.SECURE_COMPRESSION},
        Subsystem.NULL_LSP: {Subsystem.DEBUGGER, Subsystem.NLP_KNOWLEDGE},
    }

    SUBSYSTEM_DESCRIPTIONS: Dict[Subsystem, str] = {
        Subsystem.AI_CORE: "ML inference engine and tensor operations",
        Subsystem.DEBUGGER: "Step-through debugging and breakpoints",
        Subsystem.VISUALIZER: "AST and execution flow visualization",
        Subsystem.NLP_KNOWLEDGE: "Natural language understanding and knowledge graphs",
        Subsystem.QUANTUM: "Quantum computing simulation and hooks",
        Subsystem.SECURE_COMPRESSION: "Advanced encryption and compression algorithms",
        Subsystem.NETWORK_STORAGE: "Distributed storage with AI optimization",
        Subsystem.NULL_LSP: "Language Server Protocol implementation",
    }

    def __init__(self) -> None:
        """Initialize feature configuration with all subsystems disabled by default."""
        self.subsystems: Dict[Subsystem, SubsystemConfig] = {}
        for subsystem in Subsystem:
            self.subsystems[subsystem] = SubsystemConfig(
                name=subsystem,
                enabled=False,
                dependencies=self.SUBSYSTEM_DEPENDENCIES.get(subsystem, set()).copy(),
                description=self.SUBSYSTEM_DESCRIPTIONS.get(subsystem, ""),
            )
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables.

        Environment variables follow the pattern:
        - NULL_SUBSYSTEM_<NAME>=true/false (e.g., NULL_SUBSYSTEM_AI_CORE=true)
        - NULL_SUBSYSTEM_ALL=true/false (enable/disable all at once)
        """
        env_all = os.getenv("NULL_SUBSYSTEM_ALL", "").lower()
        if env_all in ("true", "1", "yes"):
            for subsystem in self.subsystems.values():
                subsystem.enabled = True
        elif env_all in ("false", "0", "no"):
            for subsystem in self.subsystems.values():
                subsystem.enabled = False

        for subsystem in Subsystem:
            env_var = f"NULL_SUBSYSTEM_{subsystem.value.upper()}"
            env_value = os.getenv(env_var, "").lower()
            if env_value in ("true", "1", "yes"):
                self.enable(subsystem)
            elif env_value in ("false", "0", "no"):
                self.disable(subsystem)

    def enable(self, subsystem: Subsystem, *, recursive: bool = True) -> None:
        """Enable a subsystem.

        Args:
            subsystem: The subsystem to enable
            recursive: If True, automatically enable dependencies
        """
        config = self.subsystems[subsystem]
        config.enabled = True

        if recursive:
            for dep in config.dependencies:
                if not self.subsystems[dep].enabled:
                    self.enable(dep, recursive=True)

    def disable(self, subsystem: Subsystem, *, recursive: bool = False) -> None:
        """Disable a subsystem.

        Args:
            subsystem: The subsystem to disable
            recursive: If True, recursively disable dependents
        """
        config = self.subsystems[subsystem]
        config.enabled = False

        if recursive:
            for other in Subsystem:
                if subsystem in self.subsystems[other].dependencies:
                    if self.subsystems[other].enabled:
                        self.disable(other, recursive=True)

    def is_enabled(self, subsystem: Subsystem) -> bool:
        """Check if a subsystem is enabled.

        Args:
            subsystem: The subsystem to check

        Returns:
            True if the subsystem is enabled, False otherwise
        """
        return self.subsystems[subsystem].enabled

    def toggle(self, subsystem: Subsystem) -> bool:
        """Toggle a subsystem's enabled state.

        Args:
            subsystem: The subsystem to toggle

        Returns:
            The new enabled state
        """
        if self.is_enabled(subsystem):
            self.disable(subsystem)
        else:
            self.enable(subsystem)
        return self.is_enabled(subsystem)

    def get_enabled_subsystems(self) -> List[Subsystem]:
        """Get list of all enabled subsystems.

        Returns:
            List of enabled subsystems
        """
        return [s for s in Subsystem if self.is_enabled(s)]

    def get_disabled_subsystems(self) -> List[Subsystem]:
        """Get list of all disabled subsystems.

        Returns:
            List of disabled subsystems
        """
        return [s for s in Subsystem if not self.is_enabled(s)]

    def get_dependencies(self, subsystem: Subsystem) -> Set[Subsystem]:
        """Get dependencies of a subsystem.

        Args:
            subsystem: The subsystem to check

        Returns:
            Set of subsystems that must be enabled for this one
        """
        return self.subsystems[subsystem].dependencies.copy()

    def get_dependents(self, subsystem: Subsystem) -> Set[Subsystem]:
        """Get subsystems that depend on this one.

        Args:
            subsystem: The subsystem to check

        Returns:
            Set of subsystems that depend on this one
        """
        dependents = set()
        for other in Subsystem:
            if subsystem in self.subsystems[other].dependencies:
                dependents.add(other)
        return dependents

    def validate_dependencies(self, subsystem: Subsystem) -> Optional[str]:
        """Validate that all dependencies are met.

        Args:
            subsystem: The subsystem to validate

        Returns:
            None if valid, otherwise an error message
        """
        if not self.is_enabled(subsystem):
            return None

        missing = []
        for dep in self.subsystems[subsystem].dependencies:
            if not self.is_enabled(dep):
                missing.append(dep.value)

        if missing:
            return (
                f"Subsystem '{subsystem.value}' requires: {', '.join(missing)} "
                f"(use enable() with recursive=True)"
            )
        return None

    def validate_all(self) -> List[str]:
        """Validate all enabled subsystems.

        Returns:
            List of error messages for invalid configurations
        """
        errors = []
        for subsystem in self.get_enabled_subsystems():
            error = self.validate_dependencies(subsystem)
            if error:
                errors.append(error)
        return errors

    def get_error_message(self, subsystem: Subsystem) -> str:
        """Get a graceful error message for a disabled subsystem.

        Args:
            subsystem: The subsystem that is disabled

        Returns:
            An actionable error message
        """
        desc = self.SUBSYSTEM_DESCRIPTIONS.get(subsystem, "subsystem")
        deps = self.get_dependencies(subsystem)
        dep_str = ", ".join(d.value for d in deps) if deps else "none"

        message = f"Subsystem '{subsystem.value}' is not enabled. {desc}\n"
        message += f"  Dependencies: {dep_str}\n"
        message += f"  To enable: Set NULL_SUBSYSTEM_{subsystem.value.upper()}=true or use config.enable()\n"
        message += f"  Location: src/null_system/{subsystem.value}/"

        return message

    def to_dict(self) -> Dict[str, object]:
        """Export configuration as dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            subsystem.value: {
                "enabled": self.is_enabled(subsystem),
                "dependencies": [d.value for d in self.get_dependencies(subsystem)],
                "description": self.SUBSYSTEM_DESCRIPTIONS.get(subsystem, ""),
            }
            for subsystem in Subsystem
        }


def get_default_config() -> FeatureConfig:
    """Get the default feature configuration instance.

    Returns:
        A FeatureConfig with all subsystems disabled by default
    """
    return FeatureConfig()
