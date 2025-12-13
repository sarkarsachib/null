"""Tests for the debugger package."""

import pytest
from src.null_system.debugger import Breakpoint, NullDebuggerSession


class TestBreakpoint:
    """Tests for Breakpoint class."""
    
    def test_breakpoint_creation(self):
        """Test creating a breakpoint."""
        bp = Breakpoint(filename="test.null", line=5)
        assert bp.filename == "test.null"
        assert bp.line == 5
        assert bp.enabled is True
        assert bp.hit_count == 0
    
    def test_breakpoint_hit(self):
        """Test breakpoint hit tracking."""
        bp = Breakpoint(filename="test.null", line=5)
        
        assert bp.hit() is True
        assert bp.hit_count == 1
        
        assert bp.hit() is True
        assert bp.hit_count == 2
    
    def test_disabled_breakpoint(self):
        """Test disabled breakpoint doesn't count hits."""
        bp = Breakpoint(filename="test.null", line=5, enabled=False)
        
        assert bp.hit() is False
        assert bp.hit_count == 0


class TestDebuggerSession:
    """Tests for NullDebuggerSession."""
    
    def test_session_creation(self):
        """Test creating a debugger session."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        assert session.source == source
        assert session.vm is not None
        assert session.artifact is not None
    
    def test_compilation_error(self):
        """Test session creation with invalid source."""
        source = "print undefined_var"
        
        with pytest.raises(ValueError, match="Compilation errors"):
            NullDebuggerSession(source)
    
    def test_set_breakpoint(self):
        """Test setting a breakpoint."""
        source = """set x to 5
print x"""
        session = NullDebuggerSession(source)
        
        bp = session.set_breakpoint("<input>", 2)
        
        assert bp.line == 2
        assert bp.instruction_index is not None
        assert len(session.breakpoints) == 1
    
    def test_remove_breakpoint(self):
        """Test removing a breakpoint."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 1)
        assert len(session.breakpoints) == 1
        
        removed = session.remove_breakpoint("<input>", 1)
        assert removed is True
        assert len(session.breakpoints) == 0
        
        removed = session.remove_breakpoint("<input>", 1)
        assert removed is False
    
    def test_step_execution(self):
        """Test stepping through instructions."""
        source = """set x to 5
set y to 10"""
        session = NullDebuggerSession(source)
        
        initial_pc = session.vm.pc
        assert initial_pc == 0
        
        state = session.step()
        assert state.current_token_index > initial_pc
        assert state.is_paused is True
        assert state.is_finished is False
    
    def test_run_to_end(self):
        """Test running program to completion."""
        source = """set x to 5
print x"""
        session = NullDebuggerSession(source)
        
        state = session.run()
        
        assert state.is_finished is True
        assert state.vm_state.variables["x"] == 5
        assert len(state.vm_state.output) == 1
        assert state.vm_state.output[0] == "5"
    
    def test_breakpoint_hit_during_run(self):
        """Test that breakpoints pause execution."""
        source = """set x to 5
set y to 10
print x"""
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 2)
        
        state = session.run()
        
        assert state.is_paused is True
        assert state.is_finished is False
        assert len(state.breakpoints_hit) == 1
        assert state.breakpoints_hit[0].line == 2
    
    def test_continue_after_breakpoint(self):
        """Test continuing execution after breakpoint."""
        source = """set x to 5
set y to 10
print x"""
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 2)
        
        state = session.run()
        assert state.is_paused is True
        
        state = session.continue_execution()
        assert state.is_finished is True
    
    def test_evaluate_watch_variable(self):
        """Test evaluating a variable watch expression."""
        source = """set x to 5
set y to 10"""
        session = NullDebuggerSession(source)
        
        session.run()
        
        result = session.evaluate_watch("x")
        assert result == 5
        
        result = session.evaluate_watch("y")
        assert result == 10
    
    def test_evaluate_watch_undefined(self):
        """Test evaluating undefined variable."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        session.run()
        
        result = session.evaluate_watch("undefined_var")
        assert "<error:" in str(result)
    
    def test_get_current_line(self):
        """Test getting current source line."""
        source = """set x to 5
set y to 10"""
        session = NullDebuggerSession(source)
        
        line = session.get_current_line()
        assert line == 1
        
        session.step()
        line = session.get_current_line()
        assert line in [1, 2]
    
    def test_get_current_token(self):
        """Test getting current super-bit token."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        token = session.get_current_token()
        assert token is not None
        assert token.opcode is not None
    
    def test_get_binary_offset(self):
        """Test getting binary offset."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        offset = session.get_binary_offset()
        assert offset is not None
        assert offset == 0
        
        session.step()
        offset = session.get_binary_offset()
        assert offset > 0
    
    def test_source_context(self):
        """Test getting source code context."""
        source = """set x to 5
set y to 10
set z to 15
print x"""
        session = NullDebuggerSession(source)
        
        context = session.get_source_context(lines_before=1, lines_after=1)
        
        assert len(context) > 0
        
        current_line = None
        for line_num, line_text, is_current in context:
            if is_current:
                current_line = line_num
                break
        
        assert current_line is not None
    
    def test_multiple_steps(self):
        """Test multiple step operations."""
        source = """set x to 5
set y to 10
add x and y"""
        session = NullDebuggerSession(source)
        
        for i in range(3):
            state = session.step()
            if state.is_finished:
                break
        
        assert session.vm.get_state().variables.get("x") in [None, 5]
    
    def test_conditional_debugging(self):
        """Test debugging conditional statements."""
        source = """set x to 25
if x is greater than 18 then print 'adult' else print 'minor'"""
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 2)
        
        state = session.run()
        assert state.is_paused is True
        
        state = session.continue_execution()
        assert state.is_finished is True
        assert "adult" in state.vm_state.output
    
    def test_list_breakpoints(self):
        """Test listing breakpoints."""
        source = """set x to 5
set y to 10
print x"""
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 1)
        session.set_breakpoint("<input>", 2)
        
        breakpoints = session.list_breakpoints()
        assert len(breakpoints) == 2
        assert breakpoints[0].line == 1
        assert breakpoints[1].line == 2
    
    def test_step_with_finished_program(self):
        """Test stepping after program finishes."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        session.run()
        assert session.is_finished is True
        
        state = session.step()
        assert state.is_finished is True
    
    def test_breakpoint_on_first_line(self):
        """Test breakpoint on first instruction."""
        source = """set x to 5
print x"""
        session = NullDebuggerSession(source)
        
        bp = session.set_breakpoint("<input>", 1)
        assert bp.instruction_index == 0
        
        state = session.run()
        assert len(state.breakpoints_hit) == 1


class TestDebuggerIntegration:
    """Integration tests for full debugging scenarios."""
    
    def test_full_debug_session(self):
        """Test a complete debugging session."""
        source = """set x to 5
set y to 10
add x and y
print x"""
        
        session = NullDebuggerSession(source)
        
        session.set_breakpoint("<input>", 2)
        
        state = session.run()
        assert state.is_paused
        assert session.vm.variables.get("x") == 5
        
        result = session.evaluate_watch("x")
        assert result == 5
        
        state = session.step()
        
        if "y" not in session.vm.variables:
            state = session.step()
        assert "y" in session.vm.variables
        
        state = session.continue_execution()
        assert state.is_finished
    
    def test_breakpoint_mapping_accuracy(self):
        """Test that breakpoints map to correct instructions."""
        source = """set x to 5
set y to 10
print x"""
        
        session = NullDebuggerSession(source)
        
        bp1 = session.set_breakpoint("<input>", 1)
        bp2 = session.set_breakpoint("<input>", 2)
        bp3 = session.set_breakpoint("<input>", 3)
        
        assert bp1.instruction_index is not None
        assert bp2.instruction_index is not None
        assert bp3.instruction_index is not None
        
        assert bp1.instruction_index < bp2.instruction_index
        assert bp2.instruction_index < bp3.instruction_index
    
    def test_state_snapshot_accuracy(self):
        """Test that state snapshots are accurate."""
        source = """set x to 5
set y to 10"""
        
        session = NullDebuggerSession(source)
        
        session.run()
        
        state = session._get_state()
        
        assert state.vm_state.variables["x"] == 5
        assert state.vm_state.variables["y"] == 10
        assert len(state.vm_state.stack) >= 0
    
    def test_watch_expression_with_literals(self):
        """Test watch expressions with literal values."""
        source = "set x to 5"
        session = NullDebuggerSession(source)
        
        session.run()
        
        result = session.evaluate_watch("x")
        assert result == 5
