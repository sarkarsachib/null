"""Breakpoint management for the Null debugger."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Breakpoint:
    """Represents a breakpoint in source code or at an instruction index.
    
    Attributes:
        filename: Source file where breakpoint is set
        line: Line number in source file (1-indexed)
        instruction_index: Resolved instruction index in super-bit stream
        enabled: Whether the breakpoint is active
        condition: Optional condition expression
        hit_count: Number of times this breakpoint has been hit
    """
    
    filename: str
    line: int
    instruction_index: Optional[int] = None
    enabled: bool = True
    condition: Optional[str] = None
    hit_count: int = 0
    
    def hit(self) -> bool:
        """Mark the breakpoint as hit and return True if enabled."""
        if self.enabled:
            self.hit_count += 1
            return True
        return False
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        loc = f"{self.filename}:{self.line}"
        if self.instruction_index is not None:
            loc += f" (instr #{self.instruction_index})"
        return f"Breakpoint({loc}, {status}, hits={self.hit_count})"
