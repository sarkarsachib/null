"""Project configuration loader for Null-Lang."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import json

try:
    import toml
except ImportError:
    toml = None

from ..lang.syntax_modes import SyntaxConfig, SyntaxMode


@dataclass
class ProjectConfig:
    """Project-level configuration for Null-Lang."""
    default_syntax: SyntaxMode = SyntaxMode.ENGLISH
    english_warnings: bool = False
    allow_hybrid_mode: bool = True
    auto_translate: bool = False
    linting: bool = True
    source_dir: Optional[Path] = None
    build_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not isinstance(self.default_syntax, SyntaxMode):
            self.default_syntax = SyntaxMode(self.default_syntax)
    
    @classmethod
    def default(cls) -> "ProjectConfig":
        """Create default project configuration."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Create project config from dictionary."""
        return cls(
            default_syntax=data.get("default_syntax", "english"),
            english_warnings=data.get("english_warnings", False),
            allow_hybrid_mode=data.get("allow_hybrid_mode", True),
            auto_translate=data.get("auto_translate", False),
            linting=data.get("linting", True),
            source_dir=Path(data.get("source_dir", ".")) if data.get("source_dir") else None,
            build_dir=Path(data.get("build_dir", "build")) if data.get("build_dir") else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "default_syntax": self.default_syntax.value,
            "english_warnings": self.english_warnings,
            "allow_hybrid_mode": self.allow_hybrid_mode,
            "auto_translate": self.auto_translate,
            "linting": self.linting,
            "source_dir": str(self.source_dir) if self.source_dir else ".",
            "build_dir": str(self.build_dir) if self.build_dir else "build"
        }
    
    def get_syntax_config(self) -> SyntaxConfig:
        """Get SyntaxConfig derived from project settings."""
        return SyntaxConfig(
            mode=self.default_syntax,
            allow_hybrid=self.allow_hybrid_mode,
            english_warnings=self.english_warnings,
            auto_translate=self.auto_translate,
            linting=self.linting
        )


class ProjectConfigLoader:
    """Loads and manages project configuration."""
    
    CONFIG_FILES = [
        "nullproject.toml",
        "project.null.config",
        ".nullproject.json"
    ]
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize config loader.
        
        Args:
            project_root: Root directory to search for config files
        """
        self.project_root = project_root or Path.cwd()
        self._config: Optional[ProjectConfig] = None
    
    def load_config(self) -> Optional[ProjectConfig]:
        """Load project configuration from files.
        
        Returns:
            ProjectConfig if found, None otherwise
        """
        if self._config is not None:
            return self._config
        
        for config_file in self.CONFIG_FILES:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    self._config = self._load_from_file(config_path)
                    return self._config
                except Exception as e:
                    # Log error but continue to try other files
                    print(f"Warning: Failed to load {config_path}: {e}")
                    continue
        
        # No config file found, use defaults
        self._config = ProjectConfig.default()
        return self._config
    
    def _load_from_file(self, config_path: Path) -> ProjectConfig:
        """Load configuration from a specific file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded ProjectConfig
        """
        content = config_path.read_text()
        
        if config_path.suffix == ".toml":
            if toml is None:
                raise ImportError("toml package not available")
            data = toml.loads(content)
        elif config_path.suffix == ".json":
            data = json.loads(content)
        elif config_path.name == "project.null.config":
            # Custom format - simple key=value pairs
            data = self._parse_custom_format(content)
        else:
            raise ValueError(f"Unsupported config file format: {config_path}")
        
        return ProjectConfig.from_dict(data.get("project", data))
    
    def _parse_custom_format(self, content: str) -> Dict[str, Any]:
        """Parse custom project.null.config format.
        
        Expected format:
        default_syntax=english
        english_warnings=false
        allow_hybrid_mode=true
        
        Args:
            content: Config file content
            
        Returns:
            Parsed configuration dictionary
        """
        data = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Convert boolean strings
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                # Convert syntax mode
                elif key == "default_syntax":
                    value = value.lower()
                
                data[key] = value
        
        return data
    
    def save_config(self, config: ProjectConfig, config_file: str = "nullproject.toml") -> Path:
        """Save configuration to file.
        
        Args:
            config: Configuration to save
            config_file: Name of config file to use
            
        Returns:
            Path to saved config file
        """
        config_path = self.project_root / config_file
        data = {"project": config.to_dict()}
        
        if config_file.endswith(".toml"):
            if toml is None:
                raise ImportError("toml package not available")
            content = toml.dumps(data)
        elif config_file.endswith(".json"):
            content = json.dumps(data, indent=2)
        else:
            # Custom format
            content = self._format_custom_config(config)
        
        config_path.write_text(content)
        return config_path
    
    def _format_custom_config(self, config: ProjectConfig) -> str:
        """Format configuration in custom format.
        
        Args:
            config: Configuration to format
            
        Returns:
            Formatted configuration string
        """
        lines = ["# Null-Lang Project Configuration"]
        lines.append("")
        
        for key, value in config.to_dict().items():
            if isinstance(value, bool):
                lines.append(f"{key}={str(value).lower()}")
            else:
                lines.append(f"{key}={value}")
        
        return "\n".join(lines) + "\n"
    
    def find_project_root(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """Find project root by searching for config files.
        
        Args:
            start_path: Starting path to search from
            
        Returns:
            Path to project root if found, None otherwise
        """
        search_path = start_path or Path.cwd()
        
        # Walk up directory tree looking for config files
        current = search_path.resolve()
        while current != current.parent:
            for config_file in self.CONFIG_FILES:
                if (current / config_file).exists():
                    return current
            current = current.parent
        
        return None


def discover_project_config(start_path: Optional[Path] = None) -> Optional[ProjectConfig]:
    """Discover and load project configuration.
    
    Args:
        start_path: Starting path to search from
        
    Returns:
        ProjectConfig if found, None otherwise
    """
    loader = ProjectConfigLoader(start_path)
    return loader.load_config()