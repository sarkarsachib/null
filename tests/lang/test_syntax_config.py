"""Tests for syntax mode configuration and preprocessor."""

import pytest
from pathlib import Path
import tempfile
import os

from null_system.lang.syntax_modes import (
    SyntaxMode, SyntaxConfig, SyntaxPreprocessor, SyntaxError
)
from null_system.config.project import ProjectConfig, ProjectConfigLoader


class TestSyntaxMode:
    """Tests for SyntaxMode enum."""
    
    def test_syntax_modes(self):
        """Test all supported syntax modes."""
        assert SyntaxMode.ENGLISH.value == "english"
        assert SyntaxMode.MODERN.value == "modern"
        assert SyntaxMode.HYBRID.value == "hybrid"
    
    def test_syntax_mode_from_string(self):
        """Test creating SyntaxMode from string."""
        assert SyntaxMode("english") == SyntaxMode.ENGLISH
        assert SyntaxMode("modern") == SyntaxMode.MODERN
        assert SyntaxMode("hybrid") == SyntaxMode.HYBRID
    
    def test_invalid_syntax_mode(self):
        """Test that invalid syntax modes raise ValueError."""
        with pytest.raises(ValueError):
            SyntaxMode("invalid_mode")


class TestSyntaxConfig:
    """Tests for SyntaxConfig dataclass."""
    
    def test_default_config(self):
        """Test default syntax configuration."""
        config = SyntaxConfig.default()
        
        assert config.mode == SyntaxMode.ENGLISH
        assert config.allow_hybrid is True
        assert config.english_warnings is False
        assert config.auto_translate is False
        assert config.linting is True
    
    def test_custom_config(self):
        """Test custom syntax configuration."""
        config = SyntaxConfig(
            mode=SyntaxMode.MODERN,
            allow_hybrid=False,
            english_warnings=True
        )
        
        assert config.mode == SyntaxMode.MODERN
        assert config.allow_hybrid is False
        assert config.english_warnings is True
    
    def test_config_from_string_mode(self):
        """Test creating config with string mode."""
        config = SyntaxConfig(mode="modern")
        assert config.mode == SyntaxMode.MODERN
    
    def test_config_serialization(self):
        """Test config to/from dictionary conversion."""
        config = SyntaxConfig(
            mode=SyntaxMode.HYBRID,
            allow_hybrid=True,  # Hybrid mode requires allow_hybrid to be True
            english_warnings=True,
            auto_translate=True,
            linting=False
        )
        
        data = config.to_dict()
        restored = SyntaxConfig.from_dict(data)
        
        assert restored.mode == config.mode
        assert restored.allow_hybrid == config.allow_hybrid
        assert restored.english_warnings == config.english_warnings
        assert restored.auto_translate == config.auto_translate
        assert restored.linting == config.linting
    
    def test_invalid_hybrid_mode(self):
        """Test that hybrid mode without allow_hybrid raises error."""
        with pytest.raises(ValueError):
            SyntaxConfig(mode=SyntaxMode.HYBRID, allow_hybrid=False)


class TestSyntaxPreprocessor:
    """Tests for SyntaxPreprocessor."""
    
    def test_init_default(self):
        """Test preprocessor initialization with defaults."""
        preprocessor = SyntaxPreprocessor()
        assert preprocessor.config.mode == SyntaxMode.ENGLISH
        assert preprocessor.config.allow_hybrid is True
    
    def test_scan_source_no_directive(self):
        """Test scanning source without @syntax directive."""
        preprocessor = SyntaxPreprocessor()
        source = "set x to 5\nprint x"
        
        mode = preprocessor.scan_source(source)
        assert mode is None
    
    def test_scan_source_with_directive(self):
        """Test scanning source with @syntax directive."""
        preprocessor = SyntaxPreprocessor()
        source = "@syntax modern\nset x to 5\nprint x"
        
        mode = preprocessor.scan_source(source)
        assert mode == SyntaxMode.MODERN
    
    def test_scan_source_directive_variations(self):
        """Test different @syntax directive formats."""
        preprocessor = SyntaxPreprocessor()
        
        # With spaces
        source1 = "@syntax   hybrid  \nset x to 5"
        assert preprocessor.scan_source(source1) == SyntaxMode.HYBRID
        
        # Case insensitive
        source2 = "@SYNTAX ENGLISH\nset x to 5"
        assert preprocessor.scan_source(source2) == SyntaxMode.ENGLISH
        
        # With leading spaces
        source3 = "  @syntax modern\nset x to 5"
        assert preprocessor.scan_source(source3) == SyntaxMode.MODERN
    
    def test_scan_source_only_leading_lines(self):
        """Test that only leading lines are scanned."""
        preprocessor = SyntaxPreprocessor()
        # Create source with directive beyond line 10
        lines = ["set x to 5"] * 10
        lines.insert(5, "@syntax modern")
        lines.insert(10, "@syntax hybrid")  # This should be ignored
        source = "\n".join(lines)
        
        # Should find the first directive at line 6
        mode = preprocessor.scan_source(source)
        assert mode == SyntaxMode.MODERN
    
    def test_scan_source_invalid_mode(self):
        """Test scanning with invalid mode name."""
        preprocessor = SyntaxPreprocessor()
        source = "@syntax invalid_mode\nset x to 5"
        
        mode = preprocessor.scan_source(source)
        assert mode is None  # Should return None for invalid modes
    
    def test_resolve_mode_cli_precedence(self):
        """Test CLI mode has highest precedence."""
        preprocessor = SyntaxPreprocessor()
        source = "@syntax english\nset x to 5"
        
        # CLI should override @syntax directive
        config = preprocessor.resolve_mode(
            source=source,
            cli_mode=SyntaxMode.MODERN,
            project_mode=SyntaxMode.HYBRID
        )
        
        assert config.mode == SyntaxMode.MODERN
    
    def test_resolve_mode_directive_precedence(self):
        """Test @syntax directive precedence over project default."""
        preprocessor = SyntaxPreprocessor()
        source = "@syntax modern\nset x to 5"
        
        config = preprocessor.resolve_mode(
            source=source,
            cli_mode=None,
            project_mode=SyntaxMode.ENGLISH
        )
        
        assert config.mode == SyntaxMode.MODERN
    
    def test_resolve_mode_project_default(self):
        """Test project default is used when no overrides."""
        preprocessor = SyntaxPreprocessor()
        source = "set x to 5\nprint x"
        
        config = preprocessor.resolve_mode(
            source=source,
            cli_mode=None,
            project_mode=SyntaxMode.HYBRID
        )
        
        assert config.mode == SyntaxMode.HYBRID
    
    def test_resolve_mode_no_project_config(self):
        """Test resolution when no project config provided."""
        preprocessor = SyntaxPreprocessor()
        source = "set x to 5"
        
        config = preprocessor.resolve_mode(
            source=source,
            cli_mode=None,
            project_mode=None
        )
        
        assert config.mode == SyntaxMode.ENGLISH  # Default
    
    def test_validate_mode_valid(self):
        """Test validation of valid modes."""
        preprocessor = SyntaxPreprocessor()
        
        assert preprocessor.validate_mode(SyntaxMode.ENGLISH) is None
        assert preprocessor.validate_mode(SyntaxMode.MODERN) is None
        assert preprocessor.validate_mode(SyntaxMode.HYBRID) is None
    
    def test_validate_mode_invalid(self):
        """Test validation of invalid modes."""
        preprocessor = SyntaxPreprocessor()
        
        # Test with a string that doesn't correspond to a valid mode
        # by temporarily creating a SyntaxMode-like object
        class FakeMode:
            value = "invalid_mode"
        
        error = preprocessor.validate_mode(FakeMode())
        assert error is not None
        assert "Invalid syntax mode" in error
    
    def test_validate_mode_hybrid_disallowed(self):
        """Test validation rejects hybrid when not allowed."""
        preprocessor = SyntaxPreprocessor(SyntaxConfig(mode=SyntaxMode.ENGLISH, allow_hybrid=False))
        
        error = preprocessor.validate_mode(SyntaxMode.HYBRID)
        assert error is not None
        assert "Hybrid mode is not allowed" in error


class TestProjectConfig:
    """Tests for ProjectConfig."""
    
    def test_default_project_config(self):
        """Test default project configuration."""
        config = ProjectConfig.default()
        
        assert config.default_syntax == SyntaxMode.ENGLISH
        assert config.english_warnings is False
        assert config.allow_hybrid_mode is True
        assert config.auto_translate is False
        assert config.linting is True
        assert config.source_dir is None
        assert config.build_dir is None
    
    def test_custom_project_config(self):
        """Test custom project configuration."""
        config = ProjectConfig(
            default_syntax=SyntaxMode.MODERN,
            english_warnings=True,
            allow_hybrid_mode=False
        )
        
        assert config.default_syntax == SyntaxMode.MODERN
        assert config.english_warnings is True
        assert config.allow_hybrid_mode is False
    
    def test_project_config_from_dict(self):
        """Test creating project config from dictionary."""
        data = {
            "default_syntax": "hybrid",
            "english_warnings": True,
            "allow_hybrid_mode": True,
            "auto_translate": False,
            "linting": True,
            "source_dir": "src",
            "build_dir": "build"
        }
        
        config = ProjectConfig.from_dict(data)
        
        assert config.default_syntax == SyntaxMode.HYBRID
        assert config.english_warnings is True
        assert config.allow_hybrid_mode is True
        assert config.source_dir == Path("src")
        assert config.build_dir == Path("build")
    
    def test_project_config_to_dict(self):
        """Test project config to dictionary conversion."""
        config = ProjectConfig(
            default_syntax=SyntaxMode.MODERN,
            source_dir=Path("my_src"),
            build_dir=Path("my_build")
        )
        
        data = config.to_dict()
        
        assert data["default_syntax"] == "modern"
        assert data["source_dir"] == "my_src"
        assert data["build_dir"] == "my_build"
    
    def test_get_syntax_config(self):
        """Test deriving SyntaxConfig from ProjectConfig."""
        project_config = ProjectConfig(
            default_syntax=SyntaxMode.HYBRID,
            english_warnings=True,
            allow_hybrid_mode=True  # Hybrid mode requires allow_hybrid_mode to be True
        )
        
        syntax_config = project_config.get_syntax_config()
        
        assert syntax_config.mode == SyntaxMode.HYBRID
        assert syntax_config.english_warnings is True
        assert syntax_config.allow_hybrid is True


class TestProjectConfigLoader:
    """Tests for ProjectConfigLoader."""
    
    def test_find_project_root_no_config(self):
        """Test finding project root when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ProjectConfigLoader(Path(tmpdir))
            root = loader.find_project_root()
            
            # Should return None when no config files found
            assert root is None
    
    def test_find_project_root_with_config(self):
        """Test finding project root with config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nullproject.toml"
            config_path.write_text("[project]\ndefault_syntax = \"modern\"")
            
            # Start searching from the temp directory itself
            loader = ProjectConfigLoader(Path(tmpdir))
            root = loader.find_project_root(Path(tmpdir))
            
            assert root == Path(tmpdir)
    
    def test_load_config_toml(self):
        """Test loading TOML configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nullproject.toml"
            config_path.write_text("""
[project]
default_syntax = "hybrid"
english_warnings = true
allow_hybrid_mode = false
""")
            
            loader = ProjectConfigLoader(Path(tmpdir))
            config = loader.load_config()
            
            assert config.default_syntax == SyntaxMode.HYBRID
            assert config.english_warnings is True
            assert config.allow_hybrid_mode is False
    
    def test_load_config_custom_format(self):
        """Test loading custom project.null.config format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "project.null.config"
            config_path.write_text("""
# Project configuration
default_syntax=modern
english_warnings=false
allow_hybrid_mode=true
auto_translate=false
""")
            
            loader = ProjectConfigLoader(Path(tmpdir))
            config = loader.load_config()
            
            assert config.default_syntax == SyntaxMode.MODERN
            assert config.english_warnings is False
            assert config.allow_hybrid_mode is True
    
    def test_save_config_toml(self):
        """Test saving configuration to TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ProjectConfigLoader(Path(tmpdir))
            config = ProjectConfig(default_syntax=SyntaxMode.MODERN)
            
            # Save to the default config file name that the loader looks for
            saved_path = loader.save_config(config, "nullproject.toml")
            
            assert saved_path.exists()
            assert saved_path.name == "nullproject.toml"
            
            # Create a new loader to test loading the saved config
            loader2 = ProjectConfigLoader(Path(tmpdir))
            loaded = loader2.load_config()
            assert loaded.default_syntax == SyntaxMode.MODERN
    
    def test_save_config_custom_format(self):
        """Test saving configuration to custom format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ProjectConfigLoader(Path(tmpdir))
            config = ProjectConfig(
                default_syntax=SyntaxMode.HYBRID,
                english_warnings=True,
                allow_hybrid_mode=True  # Hybrid mode requires allow_hybrid_mode to be True
            )
            
            saved_path = loader.save_config(config, "project.null.config")
            
            assert saved_path.exists()
            assert saved_path.name == "project.null.config"
            
            # Verify content
            content = saved_path.read_text()
            assert "default_syntax=hybrid" in content
            assert "english_warnings=true" in content
            assert "allow_hybrid_mode=true" in content