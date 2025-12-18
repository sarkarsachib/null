"""Tests for blocked subsystems configuration and placeholder modules.

Covers:
- Config defaults (all disabled)
- Enabling/disabling subsystems
- Dependency resolution
- Environment variable loading
- Placeholder module imports
- Graceful error messages
"""

import os
import pytest
from null_system.config import (
    FeatureConfig,
    Subsystem,
    SubsystemConfig,
    get_default_config,
)


class TestConfigDefaults:
    """Test that all subsystems are disabled by default."""

    def test_all_disabled_by_default(self) -> None:
        """All subsystems should be disabled by default."""
        config = FeatureConfig()
        for subsystem in Subsystem:
            assert not config.is_enabled(subsystem), f"{subsystem.value} should be disabled"

    def test_get_disabled_subsystems(self) -> None:
        """All subsystems should be in disabled list."""
        config = FeatureConfig()
        disabled = config.get_disabled_subsystems()
        assert len(disabled) == len(Subsystem)
        assert set(disabled) == set(Subsystem)

    def test_get_enabled_subsystems_empty(self) -> None:
        """Enabled subsystems list should be empty by default."""
        config = FeatureConfig()
        enabled = config.get_enabled_subsystems()
        assert len(enabled) == 0


class TestEnablementWithoutDependencies:
    """Test enabling subsystems without dependencies."""

    def test_enable_ai_core(self) -> None:
        """AI Core has no dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.AI_CORE)
        assert config.is_enabled(Subsystem.AI_CORE)

    def test_enable_visualizer(self) -> None:
        """Visualizer has no dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.VISUALIZER)
        assert config.is_enabled(Subsystem.VISUALIZER)

    def test_enable_nlp_knowledge(self) -> None:
        """NLP/Knowledge has no dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.NLP_KNOWLEDGE)
        assert config.is_enabled(Subsystem.NLP_KNOWLEDGE)

    def test_enable_quantum(self) -> None:
        """Quantum has no dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.QUANTUM)
        assert config.is_enabled(Subsystem.QUANTUM)

    def test_enable_secure_compression(self) -> None:
        """Secure compression has no dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.SECURE_COMPRESSION)
        assert config.is_enabled(Subsystem.SECURE_COMPRESSION)


class TestDependencyResolution:
    """Test automatic dependency resolution."""

    def test_enable_debugger_enables_visualizer(self) -> None:
        """Enabling debugger should enable visualizer."""
        config = FeatureConfig()
        config.enable(Subsystem.DEBUGGER, recursive=True)
        assert config.is_enabled(Subsystem.DEBUGGER)
        assert config.is_enabled(Subsystem.VISUALIZER)

    def test_enable_network_storage_enables_secure_compression(self) -> None:
        """Enabling network storage should enable secure compression."""
        config = FeatureConfig()
        config.enable(Subsystem.NETWORK_STORAGE, recursive=True)
        assert config.is_enabled(Subsystem.NETWORK_STORAGE)
        assert config.is_enabled(Subsystem.SECURE_COMPRESSION)

    def test_enable_null_lsp_enables_dependencies(self) -> None:
        """Enabling LSP should enable debugger, visualizer, and NLP."""
        config = FeatureConfig()
        config.enable(Subsystem.NULL_LSP, recursive=True)
        assert config.is_enabled(Subsystem.NULL_LSP)
        assert config.is_enabled(Subsystem.DEBUGGER)
        assert config.is_enabled(Subsystem.VISUALIZER)
        assert config.is_enabled(Subsystem.NLP_KNOWLEDGE)

    def test_enable_without_recursive_leaves_deps_disabled(self) -> None:
        """Enabling without recursive=True should not enable dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.DEBUGGER, recursive=False)
        assert config.is_enabled(Subsystem.DEBUGGER)
        assert not config.is_enabled(Subsystem.VISUALIZER)


class TestDisablement:
    """Test disabling subsystems."""

    def test_disable_subsystem(self) -> None:
        """Disabling a subsystem should work."""
        config = FeatureConfig()
        config.enable(Subsystem.AI_CORE)
        assert config.is_enabled(Subsystem.AI_CORE)
        config.disable(Subsystem.AI_CORE)
        assert not config.is_enabled(Subsystem.AI_CORE)

    def test_disable_with_recursive_disables_dependents(self) -> None:
        """Disabling with recursive=True should disable dependents."""
        config = FeatureConfig()
        config.enable(Subsystem.NULL_LSP, recursive=True)
        assert config.is_enabled(Subsystem.DEBUGGER)
        config.disable(Subsystem.VISUALIZER, recursive=True)
        assert not config.is_enabled(Subsystem.DEBUGGER)
        assert not config.is_enabled(Subsystem.NULL_LSP)

    def test_disable_without_recursive_leaves_dependents(self) -> None:
        """Disabling without recursive=True should leave dependents."""
        config = FeatureConfig()
        config.enable(Subsystem.NULL_LSP, recursive=True)
        config.disable(Subsystem.VISUALIZER, recursive=False)
        assert not config.is_enabled(Subsystem.VISUALIZER)
        assert config.is_enabled(Subsystem.DEBUGGER)


class TestToggle:
    """Test toggling subsystem state."""

    def test_toggle_disabled_to_enabled(self) -> None:
        """Toggle should enable a disabled subsystem."""
        config = FeatureConfig()
        assert not config.is_enabled(Subsystem.QUANTUM)
        result = config.toggle(Subsystem.QUANTUM)
        assert result is True
        assert config.is_enabled(Subsystem.QUANTUM)

    def test_toggle_enabled_to_disabled(self) -> None:
        """Toggle should disable an enabled subsystem."""
        config = FeatureConfig()
        config.enable(Subsystem.QUANTUM)
        assert config.is_enabled(Subsystem.QUANTUM)
        result = config.toggle(Subsystem.QUANTUM)
        assert result is False
        assert not config.is_enabled(Subsystem.QUANTUM)


class TestDependencyQueries:
    """Test querying dependencies and dependents."""

    def test_get_dependencies_with_none(self) -> None:
        """Subsystems with no dependencies should return empty set."""
        config = FeatureConfig()
        deps = config.get_dependencies(Subsystem.AI_CORE)
        assert len(deps) == 0

    def test_get_dependencies_debugger(self) -> None:
        """Debugger should depend on visualizer."""
        config = FeatureConfig()
        deps = config.get_dependencies(Subsystem.DEBUGGER)
        assert Subsystem.VISUALIZER in deps

    def test_get_dependencies_null_lsp(self) -> None:
        """LSP should depend on debugger and NLP."""
        config = FeatureConfig()
        deps = config.get_dependencies(Subsystem.NULL_LSP)
        assert Subsystem.DEBUGGER in deps
        assert Subsystem.NLP_KNOWLEDGE in deps

    def test_get_dependents_visualizer(self) -> None:
        """Visualizer should be depended on by debugger."""
        config = FeatureConfig()
        dependents = config.get_dependents(Subsystem.VISUALIZER)
        assert Subsystem.DEBUGGER in dependents

    def test_get_dependents_debugger(self) -> None:
        """Debugger should be depended on by LSP."""
        config = FeatureConfig()
        dependents = config.get_dependents(Subsystem.DEBUGGER)
        assert Subsystem.NULL_LSP in dependents

    def test_get_dependents_no_dependents(self) -> None:
        """Subsystems with no dependents should return empty set."""
        config = FeatureConfig()
        dependents = config.get_dependents(Subsystem.NETWORK_STORAGE)
        assert len(dependents) == 0


class TestValidation:
    """Test dependency validation."""

    def test_validate_dependencies_valid(self) -> None:
        """Valid dependency configuration should pass."""
        config = FeatureConfig()
        config.enable(Subsystem.DEBUGGER, recursive=True)
        error = config.validate_dependencies(Subsystem.DEBUGGER)
        assert error is None

    def test_validate_dependencies_missing(self) -> None:
        """Invalid dependency configuration should return error."""
        config = FeatureConfig()
        config.enable(Subsystem.DEBUGGER, recursive=False)
        error = config.validate_dependencies(Subsystem.DEBUGGER)
        assert error is not None
        assert "VISUALIZER" in error or "visualizer" in error

    def test_validate_dependencies_disabled_subsystem(self) -> None:
        """Validation should pass for disabled subsystems."""
        config = FeatureConfig()
        error = config.validate_dependencies(Subsystem.DEBUGGER)
        assert error is None

    def test_validate_all_empty(self) -> None:
        """Validation should pass for default config."""
        config = FeatureConfig()
        errors = config.validate_all()
        assert len(errors) == 0

    def test_validate_all_with_errors(self) -> None:
        """Validation should catch missing dependencies."""
        config = FeatureConfig()
        config.enable(Subsystem.DEBUGGER, recursive=False)
        errors = config.validate_all()
        assert len(errors) > 0
        assert any("DEBUGGER" in error or "debugger" in error for error in errors)


class TestErrorMessages:
    """Test graceful error messages for disabled subsystems."""

    def test_error_message_includes_description(self) -> None:
        """Error message should include subsystem description."""
        config = FeatureConfig()
        msg = config.get_error_message(Subsystem.AI_CORE)
        assert "AI_CORE" in msg or "ai_core" in msg
        assert "ML inference" in msg or "tensor" in msg

    def test_error_message_includes_env_var(self) -> None:
        """Error message should mention environment variable."""
        config = FeatureConfig()
        msg = config.get_error_message(Subsystem.QUANTUM)
        assert "NULL_SUBSYSTEM" in msg
        assert "QUANTUM" in msg or "quantum" in msg

    def test_error_message_includes_location(self) -> None:
        """Error message should include module location."""
        config = FeatureConfig()
        msg = config.get_error_message(Subsystem.DEBUGGER)
        assert "src/null_system" in msg

    def test_error_message_includes_dependencies(self) -> None:
        """Error message should list dependencies."""
        config = FeatureConfig()
        msg = config.get_error_message(Subsystem.DEBUGGER)
        assert "visualizer" in msg.lower() or "VISUALIZER" in msg


class TestEnvironmentVariables:
    """Test loading configuration from environment variables."""

    def test_env_var_enable_all(self, monkeypatch) -> None:
        """NULL_SUBSYSTEM_ALL=true should enable all."""
        monkeypatch.setenv("NULL_SUBSYSTEM_ALL", "true")
        config = FeatureConfig()
        for subsystem in Subsystem:
            assert config.is_enabled(subsystem), f"{subsystem.value} should be enabled"

    def test_env_var_enable_specific(self, monkeypatch) -> None:
        """NULL_SUBSYSTEM_<NAME>=true should enable specific subsystem."""
        monkeypatch.setenv("NULL_SUBSYSTEM_AI_CORE", "true")
        config = FeatureConfig()
        assert config.is_enabled(Subsystem.AI_CORE)
        assert not config.is_enabled(Subsystem.QUANTUM)

    def test_env_var_disable_specific(self, monkeypatch) -> None:
        """NULL_SUBSYSTEM_<NAME>=false should disable specific subsystem."""
        monkeypatch.setenv("NULL_SUBSYSTEM_ALL", "true")
        monkeypatch.setenv("NULL_SUBSYSTEM_QUANTUM", "false")
        config = FeatureConfig()
        assert config.is_enabled(Subsystem.AI_CORE)
        assert not config.is_enabled(Subsystem.QUANTUM)

    def test_env_var_multiple_enables(self, monkeypatch) -> None:
        """Multiple env vars should work together."""
        monkeypatch.setenv("NULL_SUBSYSTEM_AI_CORE", "true")
        monkeypatch.setenv("NULL_SUBSYSTEM_QUANTUM", "true")
        config = FeatureConfig()
        assert config.is_enabled(Subsystem.AI_CORE)
        assert config.is_enabled(Subsystem.QUANTUM)
        assert not config.is_enabled(Subsystem.DEBUGGER)


class TestExportConfig:
    """Test exporting configuration."""

    def test_to_dict_structure(self) -> None:
        """Config should export to dict with correct structure."""
        config = FeatureConfig()
        config.enable(Subsystem.AI_CORE)
        d = config.to_dict()

        assert isinstance(d, dict)
        for subsystem in Subsystem:
            assert subsystem.value in d
            assert "enabled" in d[subsystem.value]
            assert "dependencies" in d[subsystem.value]
            assert "description" in d[subsystem.value]

    def test_to_dict_reflects_state(self) -> None:
        """Exported dict should reflect current state."""
        config = FeatureConfig()
        config.enable(Subsystem.AI_CORE)
        d = config.to_dict()

        assert d[Subsystem.AI_CORE.value]["enabled"] is True
        assert d[Subsystem.QUANTUM.value]["enabled"] is False


class TestPlaceholderModules:
    """Test that placeholder modules can be imported and raise NotImplementedError."""

    def test_ai_core_module_imports(self) -> None:
        """AI core module should import without side effects."""
        from null_system.ai import AIInferenceEngine

        assert AIInferenceEngine is not None

    def test_ai_core_raises_on_instantiation(self) -> None:
        """AI core should raise NotImplementedError on instantiation."""
        from null_system.ai import AIInferenceEngine

        with pytest.raises(NotImplementedError):
            AIInferenceEngine("dummy_path")

    def test_debugger_module_imports(self) -> None:
        """Debugger module should import without side effects."""
        from null_system.debugger import Debugger

        assert Debugger is not None

    def test_debugger_raises_on_instantiation(self) -> None:
        """Debugger should raise NotImplementedError on instantiation."""
        from null_system.debugger import Debugger

        with pytest.raises(NotImplementedError):
            Debugger()

    def test_visualizer_module_imports(self) -> None:
        """Visualizer module should import without side effects."""
        from null_system.visualizer import Visualizer

        assert Visualizer is not None

    def test_visualizer_raises_on_instantiation(self) -> None:
        """Visualizer should raise NotImplementedError on instantiation."""
        from null_system.visualizer import Visualizer

        with pytest.raises(NotImplementedError):
            Visualizer()

    def test_quantum_module_imports(self) -> None:
        """Quantum module should import without side effects."""
        from null_system.quantum import QuantumSimulator

        assert QuantumSimulator is not None

    def test_quantum_raises_on_instantiation(self) -> None:
        """Quantum should raise NotImplementedError on instantiation."""
        from null_system.quantum import QuantumSimulator

        with pytest.raises(NotImplementedError):
            QuantumSimulator()

    def test_secure_compression_module_imports(self) -> None:
        """Secure compression module should import without side effects."""
        from null_system.compression.secure_compression import SecureCompressor

        assert SecureCompressor is not None

    def test_secure_compression_raises_on_instantiation(self) -> None:
        """Secure compression should raise NotImplementedError on instantiation."""
        from null_system.compression.secure_compression import SecureCompressor

        with pytest.raises(NotImplementedError):
            SecureCompressor()

    def test_network_storage_module_imports(self) -> None:
        """Network storage module should import without side effects."""
        from null_system.storage.network_store import NetworkStore

        assert NetworkStore is not None

    def test_network_storage_raises_on_instantiation(self) -> None:
        """Network storage should raise NotImplementedError on instantiation."""
        from null_system.storage.network_store import NetworkStore

        with pytest.raises(NotImplementedError):
            NetworkStore("endpoint", "bucket")


class TestDefaultConfig:
    """Test the default config function."""

    def test_get_default_config_returns_config(self) -> None:
        """get_default_config should return a FeatureConfig."""
        config = get_default_config()
        assert isinstance(config, FeatureConfig)

    def test_get_default_config_all_disabled(self) -> None:
        """Default config should have all subsystems disabled."""
        config = get_default_config()
        for subsystem in Subsystem:
            assert not config.is_enabled(subsystem)


class TestSubsystemConfigDataclass:
    """Test SubsystemConfig dataclass."""

    def test_subsystem_config_creation(self) -> None:
        """SubsystemConfig should be creatable."""
        config = SubsystemConfig(
            name=Subsystem.AI_CORE,
            enabled=True,
            dependencies=set(),
            description="Test",
        )
        assert config.name == Subsystem.AI_CORE
        assert config.enabled is True

    def test_subsystem_config_hashable(self) -> None:
        """SubsystemConfig should be hashable."""
        config1 = SubsystemConfig(name=Subsystem.AI_CORE)
        config2 = SubsystemConfig(name=Subsystem.AI_CORE)
        s = {config1, config2}
        assert len(s) == 1

    def test_subsystem_config_equality(self) -> None:
        """SubsystemConfigs should be equal by name."""
        config1 = SubsystemConfig(name=Subsystem.AI_CORE, enabled=True)
        config2 = SubsystemConfig(name=Subsystem.AI_CORE, enabled=False)
        assert config1 == config2


class TestSubsystemEnum:
    """Test Subsystem enumeration."""

    def test_all_eight_subsystems_defined(self) -> None:
        """All eight subsystems should be defined."""
        subsystems = list(Subsystem)
        assert len(subsystems) == 8

    def test_subsystem_names(self) -> None:
        """Check that all expected subsystems exist."""
        expected = {
            "ai_core",
            "debugger",
            "visualizer",
            "nlp_knowledge",
            "quantum",
            "secure_compression",
            "network_storage",
            "null_lsp",
        }
        actual = {s.value for s in Subsystem}
        assert actual == expected

    def test_subsystem_descriptions_complete(self) -> None:
        """All subsystems should have descriptions."""
        for subsystem in Subsystem:
            desc = FeatureConfig.SUBSYSTEM_DESCRIPTIONS.get(subsystem)
            assert desc is not None
            assert len(desc) > 0

    def test_subsystem_dependencies_complete(self) -> None:
        """All subsystems should have dependency entries."""
        for subsystem in Subsystem:
            deps = FeatureConfig.SUBSYSTEM_DEPENDENCIES.get(subsystem)
            assert deps is not None
            assert isinstance(deps, set)


class TestCompilerIntegration:
    """Test FeatureConfig integration with NullCompiler."""

    def test_compiler_accepts_feature_config(self) -> None:
        """NullCompiler should accept feature_config parameter."""
        from null_system.compiler import NullCompiler

        config = get_default_config()
        compiler = NullCompiler(feature_config=config)
        assert compiler.feature_config is config

    def test_compiler_feature_config_optional(self) -> None:
        """NullCompiler should work without feature_config."""
        from null_system.compiler import NullCompiler

        compiler = NullCompiler()
        assert compiler.feature_config is None


class TestVMIntegration:
    """Test FeatureConfig integration with NullVM."""

    def test_vm_accepts_feature_config(self) -> None:
        """NullVM should accept feature_config parameter."""
        from null_system.vm.vm import NullVM

        config = get_default_config()
        vm = NullVM(feature_config=config)
        assert vm.feature_config is config

    def test_vm_feature_config_optional(self) -> None:
        """NullVM should work without feature_config."""
        from null_system.vm.vm import NullVM

        vm = NullVM()
        assert vm.feature_config is None


class TestConfigImports:
    """Test that config can be imported from main package."""

    def test_import_from_null_system(self) -> None:
        """Config classes should be importable from null_system."""
        from null_system import FeatureConfig, Subsystem, get_default_config

        config = get_default_config()
        assert isinstance(config, FeatureConfig)
        assert len(list(Subsystem)) == 8

    def test_all_subsystems_accessible(self) -> None:
        """All subsystems should be accessible from enum."""
        from null_system import Subsystem

        subsystem_names = {s.value for s in Subsystem}
        assert "ai_core" in subsystem_names
        assert "debugger" in subsystem_names
        assert "visualizer" in subsystem_names
        assert "nlp_knowledge" in subsystem_names
        assert "quantum" in subsystem_names
        assert "secure_compression" in subsystem_names
        assert "network_storage" in subsystem_names
        assert "null_lsp" in subsystem_names
