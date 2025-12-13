"""CLI for the Null compiler using Typer and Rich."""

import os
import subprocess
import sys
import time
import webbrowser
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
def visualize(
    file: Path = typer.Argument(..., help="Null-Lang source file (.null)"),
    backend_port: int = typer.Option(8000, "--backend-port", help="Backend port"),
    frontend_port: int = typer.Option(5174, "--frontend-port", help="Frontend port"),
    demo: bool = typer.Option(False, "--demo", help="Use bundled sample session data"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab"),
):
    """Launch the execution visualizer (backend + React UI)."""

    project_root = Path(__file__).resolve().parents[2]

    if demo:
        session_path = project_root / "examples" / "visualizer" / "sample.session.json"
        if not session_path.exists():
            console.print(f"[red]Missing sample session data at {session_path}[/red]")
            raise typer.Exit(1)
        env = {**os.environ, "NULL_VISUALIZER_SESSION_JSON": str(session_path)}
    else:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        env = {**os.environ, "NULL_VISUALIZER_SOURCE": str(file)}

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "tools.visualizer.backend.server:app",
        "--port",
        str(backend_port),
        "--log-level",
        "warning",
    ]

    frontend_cmd = [
        "npm",
        "--workspace",
        "null-visualizer-frontend",
        "run",
        "dev",
        "--",
        "--port",
        str(frontend_port),
        "--strictPort",
    ]

    console.print(
        Panel.fit(
            f"[bold cyan]Null Visualizer[/bold cyan]\n\n"
            f"Backend: http://localhost:{backend_port}\n"
            f"Frontend: http://localhost:{frontend_port}",
            border_style="cyan",
        )
    )

    backend = subprocess.Popen(backend_cmd, cwd=str(project_root), env=env)
    frontend = subprocess.Popen(frontend_cmd, cwd=str(project_root), env=env)

    try:
        time.sleep(1.0)
        if open_browser:
            webbrowser.open(f"http://localhost:{frontend_port}")

        while True:
            if backend.poll() is not None:
                raise typer.Exit(backend.returncode or 1)
            if frontend.poll() is not None:
                raise typer.Exit(frontend.returncode or 1)
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()


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


if __name__ == "__main__":
    app()
