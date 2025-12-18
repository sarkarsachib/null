"""Debugger core implementation.

TODO: Breakpoint management (set, clear, conditional)
TODO: Step execution (into, over, out)
TODO: Frame introspection (locals, stack, heap)
TODO: Breakpoint hit callbacks
TODO: LSP integration
"""

from typing import Any, Dict, Optional


class ExecutionFrame:
    """Represents a single execution frame.

    Contains information about the current execution state including
    local variables, stack contents, and instruction pointer.
    """

    def __init__(self) -> None:
        """Initialize execution frame.

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError(
            "Debugger is not yet implemented. "
            "Set environment variable NULL_SUBSYSTEM_DEBUGGER=true when available."
        )


class Debugger:
    """Step-through debugger with breakpoint support.

    TODO Phase 1: Basic breakpoint management
    TODO Phase 2: Frame introspection
    TODO Phase 3: Conditional breakpoints
    TODO Phase 4: LSP integration for IDE support
    """

    def __init__(self) -> None:
        """Initialize debugger.

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError(
            "Debugger is not yet implemented. "
            "Set environment variable NULL_SUBSYSTEM_DEBUGGER=true when available."
        )

    def set_breakpoint(
        self, line: int, condition: Optional[str] = None
    ) -> None:
        """Set a breakpoint at the given line.

        Args:
            line: Line number for breakpoint
            condition: Optional conditional expression

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Breakpoint management not yet implemented")

    def clear_breakpoint(self, line: int) -> None:
        """Clear a breakpoint at the given line.

        Args:
            line: Line number for breakpoint

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Breakpoint management not yet implemented")

    def step_into(self) -> ExecutionFrame:
        """Step into the next function call.

        Returns:
            ExecutionFrame after step

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Step execution not yet implemented")

    def step_over(self) -> ExecutionFrame:
        """Step over the next statement.

        Returns:
            ExecutionFrame after step

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Step execution not yet implemented")

    def step_out(self) -> ExecutionFrame:
        """Step out of the current function.

        Returns:
            ExecutionFrame after step

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Step execution not yet implemented")

    def continue_execution(self) -> None:
        """Continue execution until next breakpoint.

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Step execution not yet implemented")

    def get_current_frame(self) -> ExecutionFrame:
        """Get the current execution frame.

        Returns:
            ExecutionFrame for current execution state

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Frame introspection not yet implemented")

    def get_locals(self) -> Dict[str, Any]:
        """Get local variables in current frame.

        Returns:
            Dictionary of local variable names and values

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Frame introspection not yet implemented")

    def get_stack(self) -> list[Any]:
        """Get the current execution stack.

        Returns:
            List of values on the stack

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Frame introspection not yet implemented")
