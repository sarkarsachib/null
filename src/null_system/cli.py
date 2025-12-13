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
from .extensions import (
    ProbabilisticEvaluator, NullDecisionEngine, ModelConfig, ModelType,
    NetworkingManager, TLSConfig,
    NullFSManager, CompressionType, EncryptionType, ProbabilisticValue, NullFSArchive
)
import asyncio

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


# Networking commands
net_app = typer.Typer(help="Networking operations for distributed execution")
app.add_typer(net_app, name="net")


@net_app.command()
def serve(
    host: str = typer.Option("localhost", "--host", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", help="Port to bind to"),
    tls: bool = typer.Option(True, "--tls/--no-tls", help="Enable TLS"),
    cert_file: Optional[Path] = typer.Option(None, "--cert", help="TLS certificate file"),
    key_file: Optional[Path] = typer.Option(None, "--key", help="TLS private key file"),
):
    """Start a Null network server."""
    try:
        console.print(f"[cyan]Starting Null network server on {host}:{port}...[/cyan]")
        
        tls_config = TLSConfig(
            enabled=tls,
            cert_path=cert_file,
            key_path=key_file
        )
        
        networking_manager = NetworkingManager(tls_config)
        
        # Start server
        success = asyncio.run(networking_manager.start_server("main", host, port))
        
        if success:
            console.print("[green]✓ Server started successfully![/green]")
            console.print(f"[yellow]Server is running. Press Ctrl+C to stop.[/yellow]")
            
            # Keep server running
            try:
                asyncio.run(networking_manager.servers["main"].start())
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping server...[/yellow]")
                asyncio.run(networking_manager.stop_server("main"))
                console.print("[green]✓ Server stopped[/green]")
        else:
            console.print("[red]✗ Failed to start server[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        raise typer.Exit(1)


@net_app.command()
def exec(
    host: str = typer.Argument(..., help="Remote host to execute on"),
    port: int = typer.Option(8080, "--port", help="Remote port"),
    file: Path = typer.Argument(..., help="Null-Lang source file"),
    tls: bool = typer.Option(True, "--tls/--no-tls", help="Enable TLS"),
    timeout: float = typer.Option(30.0, "--timeout", help="Execution timeout"),
):
    """Execute a Null-Lang program on a remote server."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[cyan]Executing {file} on {host}:{port}...[/cyan]")
        
        tls_config = TLSConfig(enabled=tls)
        networking_manager = NetworkingManager(tls_config)
        
        # Connect to server
        success = asyncio.run(networking_manager.connect_to_server("remote", host, port))
        
        if not success:
            console.print(f"[red]✗ Failed to connect to {host}:{port}[/red]")
            raise typer.Exit(1)
        
        # Read program source
        program_source = file.read_text()
        
        # Execute remotely
        response = asyncio.run(networking_manager.execute_remote("remote", program_source, timeout))
        
        if response:
            if response.status.value == "success":
                console.print("[green]✓ Execution successful![/green]")
                
                if response.output:
                    console.print("\n[bold]Program Output:[/bold]")
                    for line in response.output:
                        console.print(f"  {line}")
                
                if response.execution_time > 0:
                    console.print(f"\nExecution time: {response.execution_time:.3f}s")
                
            else:
                console.print(f"[red]✗ Execution failed: {response.error_message}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]✗ No response from server[/red]")
            raise typer.Exit(1)
        
        # Disconnect
        asyncio.run(networking_manager.disconnect_from_server("remote"))
        
    except Exception as e:
        console.print(f"[red]Remote execution error: {e}[/red]")
        raise typer.Exit(1)


@net_app.command()
def status(
    host: str = typer.Argument(..., help="Remote host to query"),
    port: int = typer.Option(8080, "--port", help="Remote port"),
    tls: bool = typer.Option(True, "--tls/--no-tls", help="Enable TLS"),
):
    """Get status of a remote Null server."""
    try:
        console.print(f"[cyan]Querying status of {host}:{port}...[/cyan]")
        
        tls_config = TLSConfig(enabled=tls)
        networking_manager = NetworkingManager(tls_config)
        
        # Connect to server
        success = asyncio.run(networking_manager.connect_to_server("remote", host, port))
        
        if not success:
            console.print(f"[red]✗ Failed to connect to {host}:{port}[/red]")
            raise typer.Exit(1)
        
        # Get server state
        state = asyncio.run(networking_manager.get_server_info("remote"))
        
        if state:
            console.print("[green]✓ Connected to server[/green]")
            
            # Display server information
            table = Table(title="Server Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in state.items():
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
        else:
            console.print("[red]✗ Failed to get server status[/red]")
        
        # Disconnect
        asyncio.run(networking_manager.disconnect_from_server("remote"))
        
    except Exception as e:
        console.print(f"[red]Status query error: {e}[/red]")
        raise typer.Exit(1)


# File system commands
fs_app = typer.Typer(help="File system operations with super-bit archives")
app.add_typer(fs_app, name="fs")


@fs_app.command()
def pack(
    source: Path = typer.Argument(..., help="Source directory to pack"),
    output: Path = typer.Argument(..., help="Output .nfsb archive file"),
    compression: CompressionType = typer.Option(CompressionType.GZIP, "--compression", help="Compression type"),
    encryption: EncryptionType = typer.Option(EncryptionType.NONE, "--encryption", help="Encryption type"),
):
    """Pack a directory into a NullFS archive (.nfsb)."""
    try:
        if not source.exists():
            console.print(f"[red]Error: Source directory not found: {source}[/red]")
            raise typer.Exit(1)
        
        if output.suffix != '.nfsb':
            console.print("[yellow]Warning: Output file should have .nfsb extension[/yellow]")
        
        console.print(f"[cyan]Packing {source} into {output}...[/cyan]")
        
        # Import the helper function
        from .extensions.filesystem import create_archive_from_directory
        
        # Create archive
        create_archive_from_directory(source, output, compression)
        
        console.print(f"[green]✓ Successfully packed {source} into {output}[/green]")
        
        # Show archive info
        archive = NullFSManager().get_archive(output.stem) or NullFSArchive.load_from_file(output)
        info = archive.get_archive_info()
        
        table = Table(title="Archive Information")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Files", str(info["total_files"]))
        table.add_row("Total Size", f"{info['total_size']} bytes")
        table.add_row("Compressed Size", f"{info['compressed_size']} bytes")
        compression_ratio = (1 - info['compressed_size'] / info['total_size']) * 100 if info['total_size'] > 0 else 0
        table.add_row("Compression Ratio", f"{compression_ratio:.1f}%")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Pack error: {e}[/red]")
        raise typer.Exit(1)


@fs_app.command()
def unpack(
    archive: Path = typer.Argument(..., help="Source .nfsb archive file"),
    output: Path = typer.Option(..., "--output", "-o", help="Output directory"),
):
    """Unpack a NullFS archive (.nfsb) to a directory."""
    try:
        if not archive.exists():
            console.print(f"[red]Error: Archive file not found: {archive}[/red]")
            raise typer.Exit(1)
        
        if archive.suffix != '.nfsb':
            console.print("[yellow]Warning: Input file should have .nfsb extension[/yellow]")
        
        console.print(f"[cyan]Unpacking {archive} to {output}...[/cyan]")
        
        # Import the helper function
        from .extensions.filesystem import extract_archive_to_directory
        
        # Extract archive
        extract_archive_to_directory(archive, output)
        
        console.print(f"[green]✓ Successfully unpacked {archive} to {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Unpack error: {e}[/red]")
        raise typer.Exit(1)


@fs_app.command()
def info(archive: Path = typer.Argument(..., help="Archive file to inspect")):
    """Show information about a NullFS archive."""
    try:
        if not archive.exists():
            console.print(f"[red]Error: Archive file not found: {archive}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[cyan]Inspecting {archive}...[/cyan]")
        
        # Load and inspect archive
        from .extensions.filesystem import NullFSArchive
        null_archive = NullFSArchive.load_from_file(archive)
        info = null_archive.get_archive_info()
        
        console.print("[green]✓ Archive loaded successfully[/green]")
        
        # Display header information
        header = info["header"]
        table = Table(title="Archive Header")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Version", header["version"])
        table.add_row("Archive ID", header["archive_id"])
        table.add_row("Created", header["created_at"])
        table.add_row("File Count", str(info["total_files"]))
        table.add_row("Total Size", f"{info['total_size']} bytes")
        table.add_row("Compressed Size", f"{info['compressed_size']} bytes")
        
        compression_ratio = (1 - info['compressed_size'] / info['total_size']) * 100 if info['total_size'] > 0 else 0
        table.add_row("Compression Ratio", f"{compression_ratio:.1f}%")
        
        console.print(table)
        
        # Display file listing
        if info["files"]:
            console.print("\n[bold]Files:[/bold]")
            files_table = Table()
            files_table.add_column("Path", style="cyan")
            files_table.add_column("Size", style="green")
            files_table.add_column("Compressed", style="yellow")
            files_table.add_column("Compression", style="magenta")
            
            for path, metadata in info["files"].items():
                files_table.add_row(
                    path,
                    f"{metadata['size']} bytes",
                    f"{metadata['compressed_size']} bytes",
                    metadata['compression_type']
                )
            
            console.print(files_table)
        
    except Exception as e:
        console.print(f"[red]Archive info error: {e}[/red]")
        raise typer.Exit(1)


# Probabilistic execution command
@app.command()
def probabilistic(
    file: Path = typer.Argument(..., help="Null-Lang source file"),
    model_path: Optional[Path] = typer.Option(None, "--model", help="AI model path"),
    model_type: ModelType = typer.Option(ModelType.SKLEARN, "--model-type", help="AI model type"),
    threshold: float = typer.Option(0.5, "--threshold", help="Confidence threshold"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run a program with probabilistic execution and AI-driven decisions."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        if verbose:
            console.print(f"[cyan]Compiling and running {file} with probabilistic execution...[/cyan]\n")
        
        # Set up probabilistic evaluation
        decision_engine = NullDecisionEngine()
        
        # Load model if specified
        if model_path:
            model_config = ModelConfig(
                model_path=model_path,
                model_type=model_type,
                input_features=["confidence", "value", "uncertainty"],
                output_mapping={"decision": 0, "confidence": 1}
            )
            decision_engine.register_model("main", model_config)
            success = decision_engine.load_model("main")
            
            if not success:
                console.print(f"[yellow]Warning: Failed to load model {model_path}, using heuristic decisions[/yellow]")
            elif verbose:
                console.print(f"[green]✓ Loaded AI model: {model_path}[/green]")
        
        evaluator = ProbabilisticEvaluator(decision_engine)
        
        # Compile program
        optimization_passes = [DeduplicationPass(), CompressionPass()]
        compiler = NullCompiler(optimization_passes=optimization_passes)
        result = compiler.compile_and_run(source)
        
        if not result.success:
            console.print(f"[red]Execution failed: {result.error}[/red]")
            raise typer.Exit(1)
        
        # Apply probabilistic evaluation if requested
        console.print("[green]✓ Program executed successfully![/green]")
        
        if verbose:
            console.print("\n[bold]Probabilistic Analysis:[/bold]")
            
            # Simulate probabilistic evaluation
            variables = {}
            for var, val in result.final_state.items():
                variables[var] = ProbabilisticValue(val, confidence=0.8, uncertainty=0.1)
            
            # Evaluate some sample conditions
            conditions = ["x > 5", "result > 0", "status == true"]
            prob_table = Table()
            prob_table.add_column("Condition", style="cyan")
            prob_table.add_column("Result", style="green")
            prob_table.add_column("Confidence", style="yellow")
            prob_table.add_column("Uncertainty", style="magenta")
            
            for condition in conditions:
                prob_result = evaluator.evaluate_condition_with_confidence(
                    condition, variables, use_ai=model_path is not None
                )
                prob_table.add_row(
                    condition,
                    str(prob_result.value),
                    f"{prob_result.confidence:.2f}",
                    f"{prob_result.uncertainty:.2f}"
                )
            
            console.print(prob_table)
        
        if result.output:
            console.print("\n[bold]Program Output:[/bold]")
            for line in result.output:
                console.print(f"  {line}")
        
    except CompilationError as e:
        console.print(f"[red]Compilation error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
