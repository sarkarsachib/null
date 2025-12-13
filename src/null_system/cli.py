"""CLI for the Null compiler using Typer and Rich."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .compiler import NullCompiler, CompilationError
from .compiler.optimization import DeduplicationPass, CompressionPass

app = typer.Typer(
    name="nullc",
    help="Null-Lang compiler and virtual machine",
    add_completion=False
)
console = Console()


@app.command()
def compile(
    file: Path = typer.Argument(..., help="Null-Lang source file (.null)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for binary"),
    show_ast: bool = typer.Option(False, "--show-ast", help="Display the AST"),
    show_superbit: bool = typer.Option(False, "--show-superbit", help="Display super-bit stream"),
    optimize: bool = typer.Option(True, "--optimize/--no-optimize", help="Apply optimizations"),
):
    """Compile a Null-Lang source file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        console.print(f"[cyan]Compiling {file}...[/cyan]")
        
        optimization_passes = []
        if optimize:
            optimization_passes = [DeduplicationPass(), CompressionPass()]
        
        compiler = NullCompiler(optimization_passes=optimization_passes)
        artifact = compiler.compile(source)
        
        if not artifact.is_valid():
            console.print("[red]Compilation failed with errors:[/red]")
            for error in artifact.validation_errors:
                console.print(f"  [red]• {error}[/red]")
            raise typer.Exit(1)
        
        console.print("[green]✓ Compilation successful![/green]")
        
        if show_ast:
            console.print("\n[bold]Abstract Syntax Tree:[/bold]")
            console.print(Panel(str(artifact.ast), border_style="blue"))
        
        if show_superbit:
            console.print("\n[bold]Super-bit Stream:[/bold]")
            console.print(Panel(str(artifact.superbit_stream), border_style="magenta"))
        
        table = Table(title="Compilation Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Statements", str(len(artifact.ast.statements)))
        table.add_row("Super-bit tokens", str(len(artifact.superbit_stream.tokens)))
        table.add_row("Binary frames", str(len(artifact.binary_frames)))
        table.add_row("Binary size", f"{sum(len(f) for f in artifact.binary_frames)} bytes")
        console.print("\n", table)
        
        if output:
            binary_data = b''.join(f.to_bytes() for f in artifact.binary_frames)
            output.write_bytes(binary_data)
            console.print(f"\n[green]Binary written to {output}[/green]")
        
    except CompilationError as e:
        console.print(f"[red]Compilation error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def run(
    file: Path = typer.Argument(..., help="Null-Lang source file (.null)"),
    optimize: bool = typer.Option(True, "--optimize/--no-optimize", help="Apply optimizations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Compile and run a Null-Lang source file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        if verbose:
            console.print(f"[cyan]Compiling and running {file}...[/cyan]\n")
        
        optimization_passes = []
        if optimize:
            optimization_passes = [DeduplicationPass(), CompressionPass()]
        
        compiler = NullCompiler(optimization_passes=optimization_passes)
        result = compiler.compile_and_run(source)
        
        if not result.success:
            console.print(f"[red]Execution failed: {result.error}[/red]")
            raise typer.Exit(1)
        
        if result.output:
            console.print("[bold]Program Output:[/bold]")
            for line in result.output:
                console.print(f"  {line}")
        
        if verbose:
            console.print("\n[bold]Final State:[/bold]")
            table = Table()
            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="green")
            for var, val in result.final_state.items():
                table.add_row(var, str(val))
            console.print(table)
        
    except CompilationError as e:
        console.print(f"[red]Compilation error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info():
    """Display information about the Null compiler."""
    console.print(Panel.fit(
        "[bold cyan]Null-Lang Compiler System[/bold cyan]\n\n"
        "An English-based programming language with multi-stage compilation.\n\n"
        "[bold]Pipeline:[/bold]\n"
        "  1. Parsing → Tokenize English-like syntax\n"
        "  2. AST Generation → Build abstract syntax tree\n"
        "  3. Validation → Semantic analysis\n"
        "  4. Super-bit Emission → Convert to intermediate representation\n"
        "  5. Optimization → Apply optimization passes\n"
        "  6. Binary Generation → Produce executable frames\n"
        "  7. Execution → Run in NullVM\n\n"
        "[bold]Example:[/bold]\n"
        "  set x to 5\n"
        "  set y to 10\n"
        "  add x and y\n"
        "  print x",
        border_style="green"
    ))


@app.command()
def debug(
    file: Path = typer.Argument(..., help="Null-Lang source file (.null)"),
    json_mode: bool = typer.Option(False, "--json", help="Output JSON for programmatic debugging"),
):
    """Launch the interactive debugger for a Null-Lang source file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        if json_mode:
            _debug_json_mode(source, str(file))
        else:
            _debug_interactive_mode(source, str(file))
        
    except Exception as e:
        console.print(f"[red]Debugger error: {e}[/red]")
        raise typer.Exit(1)


def _debug_interactive_mode(source: str, filename: str):
    """Run the debugger in interactive mode."""
    from .debugger import NullDebuggerSession
    
    console.print(f"[cyan]Null Debugger - {filename}[/cyan]")
    console.print("[dim]Type 'help' for commands[/dim]\n")
    
    try:
        session = NullDebuggerSession(source, filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return
    
    console.print("[green]✓ Program loaded successfully[/green]\n")
    
    _show_help()
    
    while True:
        try:
            cmd = console.input("[bold cyan]debug>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting debugger[/yellow]")
            break
        
        if not cmd:
            continue
        
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ["q", "quit", "exit"]:
            break
        
        elif command in ["h", "help"]:
            _show_help()
        
        elif command in ["r", "run"]:
            state = session.run()
            _display_state(session, state)
        
        elif command in ["c", "continue", "cont"]:
            state = session.continue_execution()
            _display_state(session, state)
        
        elif command in ["s", "step"]:
            state = session.step()
            _display_state(session, state)
        
        elif command in ["n", "next"]:
            state = session.step_over()
            _display_state(session, state)
        
        elif command in ["b", "break", "breakpoint"]:
            if not args:
                _list_breakpoints(session)
            else:
                _set_breakpoint(session, args)
        
        elif command in ["d", "delete"]:
            if args:
                _delete_breakpoint(session, args)
        
        elif command in ["p", "print"]:
            if args:
                _evaluate_expression(session, args)
            else:
                console.print("[yellow]Usage: print <expression>[/yellow]")
        
        elif command in ["l", "list"]:
            _show_source_context(session)
        
        elif command in ["i", "info"]:
            _show_detailed_info(session)
        
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type 'help' for available commands[/dim]")


def _show_help():
    """Display help information."""
    table = Table(title="Debugger Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("r, run", "Run the program until breakpoint or end")
    table.add_row("c, continue", "Continue execution from current position")
    table.add_row("s, step", "Execute a single instruction")
    table.add_row("n, next", "Step over (same as step for now)")
    table.add_row("b, break [line]", "Set breakpoint or list breakpoints")
    table.add_row("d, delete <line>", "Delete breakpoint at line")
    table.add_row("p, print <expr>", "Evaluate and print expression")
    table.add_row("l, list", "Show source code context")
    table.add_row("i, info", "Show detailed execution state")
    table.add_row("h, help", "Show this help")
    table.add_row("q, quit", "Exit debugger")
    
    console.print(table)
    console.print()


def _display_state(session, state):
    """Display execution state after a debugger action."""
    if state.is_finished:
        console.print("[green]✓ Program finished[/green]")
        _show_final_output(session)
        return
    
    if state.breakpoints_hit:
        for bp in state.breakpoints_hit:
            console.print(f"[yellow]⚠ Breakpoint hit: {bp}[/yellow]")
    
    _show_source_context(session)
    _show_vm_state(session, state)


def _show_source_context(session):
    """Show source code context around current line."""
    context = session.get_source_context(lines_before=2, lines_after=2)
    
    if not context:
        console.print("[dim]No source context available[/dim]")
        return
    
    console.print("\n[bold]Source:[/bold]")
    for line_num, line_text, is_current in context:
        prefix = "→" if is_current else " "
        style = "bold yellow" if is_current else "dim"
        console.print(f"{prefix} {line_num:3d} | {line_text}", style=style)
    console.print()


def _show_vm_state(session, state):
    """Show VM execution state."""
    table = Table(title="Execution State")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("PC (Instruction)", str(state.current_token_index))
    table.add_row("Source Line", str(state.current_line) if state.current_line else "N/A")
    
    token = session.get_current_token()
    if token:
        table.add_row("Current OpCode", token.opcode.name)
        if token.operand is not None:
            table.add_row("Operand", str(token.operand))
    
    binary_offset = session.get_binary_offset()
    if binary_offset is not None:
        table.add_row("Binary Offset", f"0x{binary_offset:04x}")
    
    console.print(table)
    
    if state.vm_state.stack:
        console.print(f"\n[bold]Stack:[/bold] {state.vm_state.stack}")
    
    if state.vm_state.variables:
        var_table = Table(title="Variables")
        var_table.add_column("Name", style="cyan")
        var_table.add_column("Value", style="green")
        for name, value in state.vm_state.variables.items():
            var_table.add_row(name, str(value))
        console.print(var_table)
    
    console.print()


def _show_final_output(session):
    """Show final program output."""
    state = session.vm.get_state()
    if state.output:
        console.print("\n[bold]Output:[/bold]")
        for line in state.output:
            console.print(f"  {line}")
    
    if state.variables:
        console.print("\n[bold]Final Variables:[/bold]")
        var_table = Table()
        var_table.add_column("Name", style="cyan")
        var_table.add_column("Value", style="green")
        for name, value in state.variables.items():
            var_table.add_row(name, str(value))
        console.print(var_table)


def _set_breakpoint(session, args: str):
    """Set a breakpoint."""
    try:
        line = int(args.strip())
        bp = session.set_breakpoint(session.source_file, line)
        console.print(f"[green]✓ Breakpoint set: {bp}[/green]")
    except ValueError:
        console.print(f"[red]Invalid line number: {args}[/red]")


def _delete_breakpoint(session, args: str):
    """Delete a breakpoint."""
    try:
        line = int(args.strip())
        if session.remove_breakpoint(session.source_file, line):
            console.print(f"[green]✓ Breakpoint removed at line {line}[/green]")
        else:
            console.print(f"[yellow]No breakpoint at line {line}[/yellow]")
    except ValueError:
        console.print(f"[red]Invalid line number: {args}[/red]")


def _list_breakpoints(session):
    """List all breakpoints."""
    breakpoints = session.list_breakpoints()
    if not breakpoints:
        console.print("[dim]No breakpoints set[/dim]")
        return
    
    table = Table(title="Breakpoints")
    table.add_column("Line", style="cyan")
    table.add_column("Instruction", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Hits", style="yellow")
    
    for bp in breakpoints:
        status = "enabled" if bp.enabled else "disabled"
        instr = str(bp.instruction_index) if bp.instruction_index is not None else "?"
        table.add_row(str(bp.line), instr, status, str(bp.hit_count))
    
    console.print(table)


def _evaluate_expression(session, expression: str):
    """Evaluate and print an expression."""
    result = session.evaluate_watch(expression)
    console.print(f"[green]{expression} = {result}[/green]")


def _show_detailed_info(session):
    """Show detailed execution information."""
    state = session._get_state()
    _show_source_context(session)
    _show_vm_state(session, state)


def _debug_json_mode(source: str, filename: str):
    """Run debugger in JSON streaming mode (for programmatic control)."""
    import json
    from .debugger import NullDebuggerSession
    
    try:
        session = NullDebuggerSession(source, filename)
        
        print(json.dumps({
            "status": "ready",
            "source_file": filename,
            "line_count": len(session.source_lines)
        }))
        
        while True:
            try:
                line = input()
                cmd_data = json.loads(line)
                command = cmd_data.get("command")
                
                if command == "run":
                    state = session.run()
                elif command == "step":
                    state = session.step()
                elif command == "continue":
                    state = session.continue_execution()
                elif command == "set_breakpoint":
                    bp = session.set_breakpoint(filename, cmd_data["line"])
                    print(json.dumps({"status": "breakpoint_set", "line": bp.line}))
                    continue
                elif command == "evaluate":
                    result = session.evaluate_watch(cmd_data["expression"])
                    print(json.dumps({"result": str(result)}))
                    continue
                elif command == "exit":
                    break
                else:
                    print(json.dumps({"error": f"Unknown command: {command}"}))
                    continue
                
                vm_state = session.vm.get_state()
                print(json.dumps({
                    "pc": vm_state.pc,
                    "line": session.get_current_line(),
                    "stack": vm_state.stack,
                    "variables": vm_state.variables,
                    "output": vm_state.output,
                    "is_finished": state.is_finished
                }))
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(json.dumps({"error": str(e)}))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    app()
