"""CLI for the Null compiler using Typer and Rich."""

from pathlib import Path
from typing import Optional
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .compiler import NullCompiler, CompilationError
from .compiler.optimization import DeduplicationPass, CompressionPass
from .nlp.pipeline import NLPPipeline
from .nlp.tokenizer import Tokenizer
from .nlp.translation import Translator
from .nlp.codegen import CodeGenerator

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


nlp_app = typer.Typer(help="Natural Language Processing tools")


@nlp_app.command()
def tokenize(
    text: str = typer.Argument(..., help="Text to tokenize"),
    language: str = typer.Option("auto", "--language", "-l", help="Language code (en, es, zh, auto)"),
):
    """Tokenize input text."""
    try:
        tokenizer = Tokenizer(language=language)
        tokens = tokenizer.tokenize(text)

        if not tokens:
            console.print("[yellow]No tokens found[/yellow]")
            return

        table = Table(title="Tokenization Result")
        table.add_column("Token", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Position", style="magenta")

        for token in tokens:
            table.add_row(token.text, token.token_type.value, str(token.position))

        console.print(table)
        console.print(f"\n[green]✓ Tokenized into {len(tokens)} tokens[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@nlp_app.command()
def translate(
    text: str = typer.Argument(..., help="Text to translate"),
    target: str = typer.Option("en", "--target", "-t", help="Target language (en, es, zh)"),
):
    """Translate text between languages."""
    try:
        translator = Translator()
        tokenizer = Tokenizer(language="auto")
        source_lang = tokenizer._detect_language(text)

        result = translator.translate(text, source_lang, target)

        console.print("[bold]Translation Result:[/bold]")
        console.print(f"[cyan]Source ({result.source_language}):[/cyan] {result.source_text}")
        console.print(f"[green]Target ({result.target_language}):[/green] {result.target_text}")
        console.print(f"[magenta]Confidence:[/magenta] {result.confidence:.2%}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@nlp_app.command()
def codegen(
    text: str = typer.Argument(..., help="Natural language description"),
    language: str = typer.Option("null", "--language", "-l", help="Target language (null, python)"),
    show_details: bool = typer.Option(False, "--details", "-d", help="Show detailed analysis"),
):
    """Generate code from natural language."""
    try:
        start_time = time.time()

        codegen = CodeGenerator(language="auto")
        result = codegen.generate(text, target_language=language)

        elapsed_ms = (time.time() - start_time) * 1000

        console.print(f"[bold]Natural Language:[/bold] {text}")
        console.print(f"\n[bold]Generated {language.upper()} Code:[/bold]")
        console.print(Panel(result.generated_code, border_style="green"))

        if show_details:
            details = Table(title="Generation Details")
            details.add_column("Metric", style="cyan")
            details.add_column("Value", style="green")

            if result.intent:
                details.add_row("Intent", result.intent.name)
                details.add_row("Intent Confidence", f"{result.intent.confidence:.2%}")

            details.add_row("Entity Count", str(len(result.entities)))
            details.add_row("Overall Confidence", f"{result.confidence:.2%}")
            details.add_row("Latency", f"{elapsed_ms:.2f} ms")

            console.print("\n", details)

        if elapsed_ms > 50:
            console.print(f"[yellow]⚠ Latency {elapsed_ms:.2f} ms exceeds target of 50ms[/yellow]")
        else:
            console.print(f"[green]✓ Generated in {elapsed_ms:.2f} ms[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


app.add_typer(nlp_app, name="nlp")


if __name__ == "__main__":
    app()
