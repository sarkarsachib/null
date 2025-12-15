"""Syntax mode definitions and configuration for Null-Lang."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Any
import re


class SyntaxMode(Enum):
    """Supported syntax modes for Null-Lang."""
    ENGLISH = "english"
    MODERN = "modern"
    HYBRID = "hybrid"


@dataclass
class SyntaxConfig:
    """Configuration for syntax mode selection."""
    mode: SyntaxMode
    allow_hybrid: bool = True
    english_warnings: bool = False
    auto_translate: bool = False
    linting: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if isinstance(self.mode, str):
            self.mode = SyntaxMode(self.mode)
        
        # Validate mode combinations
        if self.mode == SyntaxMode.HYBRID and not self.allow_hybrid:
            raise ValueError("Cannot use hybrid mode when allow_hybrid is False")
    
    @classmethod
    def default(cls) -> "SyntaxConfig":
        """Create default syntax configuration."""
        return cls(
            mode=SyntaxMode.ENGLISH,
            allow_hybrid=True,
            english_warnings=False,
            auto_translate=False,
            linting=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode.value,
            "allow_hybrid": self.allow_hybrid,
            "english_warnings": self.english_warnings,
            "auto_translate": self.auto_translate,
            "linting": self.linting
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyntaxConfig":
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "english"),
            allow_hybrid=data.get("allow_hybrid", True),
            english_warnings=data.get("english_warnings", False),
            auto_translate=data.get("auto_translate", False),
            linting=data.get("linting", True)
        )
    
    def copy(self) -> "SyntaxConfig":
        """Create a copy of this configuration."""
        return SyntaxConfig(
            mode=self.mode,
            allow_hybrid=self.allow_hybrid,
            english_warnings=self.english_warnings,
            auto_translate=self.auto_translate,
            linting=self.linting
        )


class SyntaxPreprocessor:
    """Preprocessor to detect @syntax directives in source files."""
    
    SYNTAX_DIRECTIVE_PATTERN = re.compile(r'^\s*@syntax\s+(\w+)', re.IGNORECASE)
    
    def __init__(self, config: Optional[SyntaxConfig] = None):
        """Initialize preprocessor with configuration."""
        self.config = config or SyntaxConfig.default()
    
    def scan_source(self, source: str) -> Optional[SyntaxMode]:
        """
        Scan source code for @syntax directive in leading lines.
        
        Args:
            source: Source code to scan
            
        Returns:
            SyntaxMode if directive found, None otherwise
        """
        lines = source.splitlines()
        
        # Only scan first 10 lines for performance
        scan_lines = lines[:10]
        
        for line in scan_lines:
            match = self.SYNTAX_DIRECTIVE_PATTERN.match(line)
            if match:
                try:
                    mode_str = match.group(1).lower()
                    return SyntaxMode(mode_str)
                except ValueError:
                    # Invalid mode name in directive
                    continue
        
        return None
    
    def preprocess_source(self, source: str) -> str:
        """
        Remove @syntax directives from source code.
        
        Args:
            source: Source code with potential @syntax directives
            
        Returns:
            Source code with @syntax directives removed
        """
        lines = source.splitlines()
        filtered_lines = []
        
        for line in lines:
            if not self.SYNTAX_DIRECTIVE_PATTERN.match(line):
                filtered_lines.append(line)
        
        return "\n".join(filtered_lines)
    
    def resolve_mode(self, source: str, cli_mode: Optional[SyntaxMode] = None, 
                    project_mode: Optional[SyntaxMode] = None) -> SyntaxConfig:
        """
        Resolve the final syntax mode using precedence rules.
        
        Precedence order:
        1. CLI --syntax flag (highest)
        2. @syntax directive in source
        3. Project configuration (lowest)
        
        Args:
            source: Source code to scan for directives
            cli_mode: Mode specified via CLI
            project_mode: Default mode from project config
            
        Returns:
            Resolved SyntaxConfig
        """
        # Start with our config or default
        resolved_config = self.config.copy() if self.config else SyntaxConfig.default()
        
        # Apply project mode if provided and not overridden by higher precedence
        if project_mode and not cli_mode:
            resolved_config.mode = project_mode
        
        # Check for @syntax directive in source
        source_mode = self.scan_source(source)
        if source_mode and not cli_mode:
            resolved_config.mode = source_mode
        
        # Apply CLI mode (highest precedence)
        if cli_mode:
            resolved_config.mode = cli_mode
        
        return resolved_config
    
    def validate_mode(self, mode: SyntaxMode) -> Optional[str]:
        """
        Validate a syntax mode.
        
        Args:
            mode: Syntax mode to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        valid_modes = {m.value for m in SyntaxMode}
        
        if mode.value not in valid_modes:
            return f"Invalid syntax mode '{mode.value}'. Valid modes: {', '.join(sorted(valid_modes))}"
        
        if mode == SyntaxMode.HYBRID and not self.config.allow_hybrid:
            return "Hybrid mode is not allowed in this project configuration"
        
        return None


class SyntaxError(Exception):
    """Exception raised for syntax mode related errors."""
    pass