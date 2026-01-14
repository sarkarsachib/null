"""CLI for the Null compiler using Typer and Rich."""

import os
import subprocess
import sys
import time
import webbrowser
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
from .extensions import AdvancedCompressionPass, SuperBitSecurityLayer, KeyManager
from .extensions.compression import CompressionLevel
from .knowledge import GraphStore, InMemoryBackend, SuperBitEncoder
from .knowledge.query_language import QueryEngine
from .knowledge.inference import InferenceEngine, Rule, RuleType
from .knowledge.external.wikidata import ExternalKnowledgeBase
from .lsp import run_lsp_server
from .lang.syntax_modes import SyntaxMode, SyntaxConfig, SyntaxPreprocessor
from .config.project import discover_project_config

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
    compress: Optional[str] = typer.Option(None, "--compress", help="Compression level (low, medium, high)"),
    security_profile: Optional[str] = typer.Option(None, "--security-profile", help="Security profile (dev, prod)"),
    encryption_key_id: Optional[str] = typer.Option(None, "--key-id", help="Encryption key ID"),
    syntax: Optional[str] = typer.Option(None, "--syntax", help="Syntax mode (english, modern, hybrid)"),
    allow_hybrid: Optional[bool] = typer.Option(None, "--allow-hybrid/--no-allow-hybrid", help="Allow hybrid mode"),
    english_warnings: bool = typer.Option(False, "--english-warnings", help="Show warnings for English syntax"),
):
    """Compile a Null-Lang source file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        console.print(f"[cyan]Compiling {file}...[/cyan]")
        
        # Load project configuration
        project_config = discover_project_config(file.parent)
        
        # Resolve syntax mode with precedence: CLI > @syntax directive > project default
        cli_mode = None
        if syntax:
            try:
                cli_mode = SyntaxMode(syntax.lower())
            except ValueError:
                console.print(f"[red]Invalid syntax mode '{syntax}'. Valid modes: english, modern, hybrid[/red]")
                raise typer.Exit(1)
        
        # Initialize preprocessor with project config
        preprocessor = SyntaxPreprocessor()
        if project_config:
            preprocessor.config = project_config.get_syntax_config()
        
        # Resolve final syntax configuration
        syntax_config = preprocessor.resolve_mode(
            source=source,
            cli_mode=cli_mode,
            project_mode=project_config.default_syntax if project_config else None
        )
        
        # Apply CLI overrides
        if allow_hybrid is not None:
            syntax_config.allow_hybrid = allow_hybrid
        if english_warnings is not None:
            syntax_config.english_warnings = english_warnings
        
        # Validate the resolved mode
        error = preprocessor.validate_mode(syntax_config.mode)
        if error:
            console.print(f"[red]Syntax mode error: {error}[/red]")
            raise typer.Exit(1)
        
        # Display resolved syntax mode
        console.print(f"[green]Using syntax mode: {syntax_config.mode.value}[/green]")
        if syntax_config.mode != SyntaxMode.ENGLISH:
            console.print(f"[blue]Hybrid allowed: {syntax_config.allow_hybrid}, English warnings: {syntax_config.english_warnings}[/blue]")
        
        optimization_passes = []
        if optimize:
            optimization_passes = [DeduplicationPass(), CompressionPass()]
        
        if compress:
            try:
                level = CompressionLevel(compress.lower())
                optimization_passes.append(AdvancedCompressionPass(level=level))
            except ValueError:
                console.print(f"[red]Invalid compression level: {compress}[/red]")
                raise typer.Exit(1)
        
        compiler = NullCompiler(optimization_passes=optimization_passes)
        artifact = compiler.compile(source, syntax_config=syntax_config)
        
        if security_profile and security_profile.lower() in ["dev", "prod"]:
            try:
                key_manager = KeyManager()
                security_layer = SuperBitSecurityLayer(key_manager=key_manager)
                
                if encryption_key_id is None:
                    try:
                        encryption_key_id, _ = key_manager.get_active_key()
                    except ValueError:
                        if security_profile.lower() == "prod":
                            console.print("[yellow]No active encryption key found. Generating one...[/yellow]")
                            encryption_key_id, _ = key_manager.create_key(comment="Default key")
                        else:
                            console.print("[yellow]Skipping encryption for dev profile[/yellow]")
                            encryption_key_id = None
                
                if encryption_key_id:
                    ciphertext, key_id, nonce, tag = security_layer.encrypt_stream(artifact.superbit_stream, encryption_key_id)
                    console.print(f"[green]✓ Encrypted with key: {key_id}[/green]")
                    
                    compiler.binary_generator.set_encryption_metadata(
                        algorithm="AES-256-GCM",
                        key_id=key_id,
                        nonce=nonce.hex(),
                        tag=tag.hex()
                    )
            except Exception as e:
                console.print(f"[red]Encryption error: {e}[/red]")
                raise typer.Exit(1)
        
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
    compress: Optional[str] = typer.Option(None, "--compress", help="Compression level (low, medium, high)"),
    security_profile: Optional[str] = typer.Option(None, "--security-profile", help="Security profile (dev, prod)"),
    encryption_key_id: Optional[str] = typer.Option(None, "--key-id", help="Encryption key ID"),
    syntax: Optional[str] = typer.Option(None, "--syntax", help="Syntax mode (english, modern, hybrid)"),
    allow_hybrid: Optional[bool] = typer.Option(None, "--allow-hybrid/--no-allow-hybrid", help="Allow hybrid mode"),
    english_warnings: bool = typer.Option(False, "--english-warnings", help="Show warnings for English syntax"),
):
    """Compile and run a Null-Lang source file."""
    try:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        
        source = file.read_text()
        
        if verbose:
            console.print(f"[cyan]Compiling and running {file}...[/cyan]\n")
        
        # Load project configuration
        project_config = discover_project_config(file.parent)
        
        # Resolve syntax mode with precedence: CLI > @syntax directive > project default
        cli_mode = None
        if syntax:
            try:
                cli_mode = SyntaxMode(syntax.lower())
            except ValueError:
                console.print(f"[red]Invalid syntax mode '{syntax}'. Valid modes: english, modern, hybrid[/red]")
                raise typer.Exit(1)
        
        # Initialize preprocessor with project config
        preprocessor = SyntaxPreprocessor()
        if project_config:
            preprocessor.config = project_config.get_syntax_config()
        
        # Resolve final syntax configuration
        syntax_config = preprocessor.resolve_mode(
            source=source,
            cli_mode=cli_mode,
            project_mode=project_config.default_syntax if project_config else None
        )
        
        # Apply CLI overrides
        if allow_hybrid is not None:
            syntax_config.allow_hybrid = allow_hybrid
        if english_warnings is not None:
            syntax_config.english_warnings = english_warnings
        
        # Validate the resolved mode
        error = preprocessor.validate_mode(syntax_config.mode)
        if error:
            console.print(f"[red]Syntax mode error: {error}[/red]")
            raise typer.Exit(1)
        
        if verbose:
            console.print(f"[green]Using syntax mode: {syntax_config.mode.value}[/green]")
        
        optimization_passes = []
        if optimize:
            optimization_passes = [DeduplicationPass(), CompressionPass()]
        
        if compress:
            try:
                level = CompressionLevel(compress.lower())
                optimization_passes.append(AdvancedCompressionPass(level=level))
            except ValueError:
                console.print(f"[red]Invalid compression level: {compress}[/red]")
                raise typer.Exit(1)
        
        compiler = NullCompiler(optimization_passes=optimization_passes)
        result = compiler.compile_and_run(
            source,
            syntax_config=syntax_config,
            security_profile=security_profile,
            encryption_key_id=encryption_key_id
        )
        
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
def lsp(
    syntax: str = typer.Option("auto", "--syntax", help="Syntax mode (english|modern|hybrid|auto)"),
    port: int = typer.Option(2087, "--port", help="TCP port when not using --stdio"),
    stdio: bool = typer.Option(True, "--stdio/--tcp", help="Use stdio (default) or TCP"),
):
    """Start the Null Language Server (LSP)."""

    run_lsp_server(syntax=syntax, port=port, stdio=stdio)


@app.command()
def visualize(
    file: Path = typer.Argument(..., help="Null-Lang source file (.null)"),
    backend_port: int = typer.Option(8000, "--backend-port", help="Backend port"),
    frontend_port: int = typer.Option(5174, "--frontend-port", help="Frontend port"),
    demo: bool = typer.Option(False, "--demo", help="Use bundled sample session data"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open a browser tab"),
    syntax: Optional[str] = typer.Option(None, "--syntax", help="Syntax mode (english, modern, hybrid)"),
    allow_hybrid: Optional[bool] = typer.Option(None, "--allow-hybrid/--no-allow-hybrid", help="Allow hybrid mode"),
    english_warnings: bool = typer.Option(False, "--english-warnings", help="Show warnings for English syntax"),
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


kg_app = typer.Typer(help="Knowledge Graph tools")


@kg_app.command()
def init(
    backend: str = typer.Option("memory", "--backend", "-b", help="Backend type (memory, sqlite)"),
    db_path: str = typer.Option("knowledge.db", "--db-path", help="Database path for SQLite backend"),
):
    """Initialize knowledge graph."""
    try:
        if backend.lower() == "memory":
            graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
            console.print("[green]✓ Initialized in-memory knowledge graph[/green]")
        elif backend.lower() == "sqlite":
            from pathlib import Path
            graph_store = GraphStore(
                GraphStore.create_sqlite_backend(Path(db_path)),
                SuperBitEncoder()
            )
            console.print(f"[green]✓ Initialized SQLite knowledge graph at {db_path}[/green]")
        else:
            console.print(f"[red]Unknown backend: {backend}[/red]")
            raise typer.Exit(1)
        
        # Show initial stats
        stats = graph_store.get_graph_stats()
        table = Table(title="Knowledge Graph Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Entities", str(stats["total_entities"]))
        table.add_row("Relationships", str(stats["total_relationships"]))
        table.add_row("Entity Types", str(len(stats["entity_types"])))
        table.add_row("Relationship Types", str(len(stats["relationship_types"])))
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@kg_app.command()
def query(
    query_type: str = typer.Argument(..., help="Query type (entities, relationships, paths)"),
    entity_type: Optional[str] = typer.Option(None, "--entity-type", help="Entity type filter"),
    relationship_type: Optional[str] = typer.Option(None, "--relationship-type", help="Relationship type filter"),
    property_filter: Optional[str] = typer.Option(None, "--property", help="Property filter (key=value)"),
    limit: int = typer.Option(10, "--limit", help="Result limit"),
):
    """Query the knowledge graph."""
    try:
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        query_engine = QueryEngine(graph_store)
        
        result = None
        
        if query_type.lower() == "entities":
            properties = None
            if property_filter:
                key, value = property_filter.split("=", 1)
                properties = {key: value}
            
            result = query_engine.find_entities(
                entity_type=entity_type,
                properties=properties
            )
            
            console.print(f"[bold]Found {result.total_count} entities:[/bold]")
            
            table = Table(title="Entities")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Properties", style="white")
            
            for match in result.matches[:limit]:
                entity = match["entity"]
                props_str = ", ".join(f"{k}={v}" for k, v in entity.properties.items())
                table.add_row(str(entity.id)[:8], entity.type, props_str)
            
            console.print(table)
            
        elif query_type.lower() == "relationships":
            result = query_engine.find_relationships(
                relationship_type=relationship_type
            )
            
            console.print(f"[bold]Found {result.total_count} relationships:[/bold]")
            
            table = Table(title="Relationships")
            table.add_column("Source", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Target", style="yellow")
            table.add_column("Confidence", style="magenta")
            
            for match in result.matches[:limit]:
                table.add_row(
                    str(match["source_id"])[:8],
                    match["relationship_type"],
                    str(match["target_id"])[:8],
                    f"{match['confidence']:.2f}"
                )
            
            console.print(table)
            
        elif query_type.lower() == "paths":
            if not entity_type:
                console.print("[red]Start entity type required for path queries[/red]")
                raise typer.Exit(1)
            
            result = query_engine.find_paths(
                start_type=entity_type,
                max_length=limit
            )
            
            console.print(f"[bold]Found {result.total_count} paths:[/bold]")
            
            for i, match in enumerate(result.matches[:limit]):
                path = match["path"]
                entities = [item for item in path if hasattr(item, 'type')]
                console.print(f"Path {i+1}: {' → '.join(e.type for e in entities)}")
        else:
            console.print(f"[red]Unknown query type: {query_type}[/red]")
            raise typer.Exit(1)
        
        if result and result.execution_time:
            console.print(f"\n[green]✓ Query completed in {result.execution_time:.3f}s[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@kg_app.command()
def reason(
    reasoning_type: str = typer.Argument(..., help="Reasoning type (forward, backward)"),
    max_iterations: int = typer.Option(100, "--iterations", help="Maximum iterations"),
    goal: Optional[str] = typer.Option(None, "--goal", help="Goal for backward chaining"),
):
    """Perform rule-based reasoning."""
    try:
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        inference_engine = InferenceEngine(graph_store)
        
        # Add some example rules
        from uuid import uuid4
        
        if reasoning_type.lower() == "forward":
            # Add example rules
            rule = Rule(
                id=uuid4(),
                name="Works at TechCorp",
                rule_type=RuleType.FORWARD_CHAINING,
                premises=["Person WORKS_FOR Organization"],
                conclusions=["Person TECH_EMPLOYEE true"],
                confidence=0.9
            )
            inference_engine.add_rule(rule)
            
            new_facts = inference_engine.infer_forward(max_iterations)
            
            console.print(f"[bold]Forward chaining completed:[/bold]")
            console.print(f"Generated {len(new_facts)} new facts")
            
            for fact in new_facts[:10]:  # Show first 10
                console.print(f"  {fact.subject} {fact.predicate} {fact.object} (confidence: {fact.confidence:.2f})")
                
        elif reasoning_type.lower() == "backward":
            if not goal:
                console.print("[red]Goal required for backward chaining[/red]")
                raise typer.Exit(1)
            
            # Add example rules first
            rule = Rule(
                id=uuid4(),
                name="Tech employee inference",
                rule_type=RuleType.BACKWARD_CHAINING,
                premises=["Person TECH_EMPLOYEE true"],
                conclusions=["Person IS_TECH_WORKER true"],
                confidence=0.8
            )
            inference_engine.add_rule(rule)
            
            proof_paths = inference_engine.infer_backward(goal)
            
            console.print(f"[bold]Backward chaining for goal '{goal}':[/bold]")
            console.print(f"Found {len(proof_paths)} proof paths")
            
            for i, path in enumerate(proof_paths[:10]):  # Show first 10
                console.print(f"  Path {i+1}:")
                for fact in path:
                    console.print(f"    {fact.subject} {fact.predicate} {fact.object}")
        else:
            console.print(f"[red]Unknown reasoning type: {reasoning_type}[/red]")
            raise typer.Exit(1)
        
        # Show statistics
        stats = inference_engine.get_inference_statistics()
        console.print(f"\n[bold]Inference Statistics:[/bold]")
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Rules", str(stats["total_rules"]))
        table.add_row("Total Facts", str(stats["total_facts"]))
        table.add_row("Rule Types", str(stats["rule_types"]))
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@kg_app.command()
def link_external(
    sources: str = typer.Argument(..., help="External sources (comma-separated: wikidata,dbpedia)"),
    query: Optional[str] = typer.Option(None, "--query", help="Search query"),
    limit: int = typer.Option(10, "--limit", help="Result limit"),
    confidence_threshold: float = typer.Option(0.7, "--threshold", help="Confidence threshold"),
):
    """Link entities to external knowledge bases."""
    try:
        external_kb = ExternalKnowledgeBase()
        source_list = [s.strip() for s in sources.split(",")]
        
        if query:
            # Search external sources
            console.print(f"[bold]Searching external sources for: '{query}'[/bold]")
            
            results = external_kb.search_all_sources(query, limit)
            
            for source, entities in results.items():
                console.print(f"\n[bold]{source.upper()} Results:[/bold]")
                
                table = Table(title=f"{source.title()} Entities")
                table.add_column("ID", style="cyan")
                table.add_column("Label", style="green")
                table.add_column("Description", style="white")
                
                for entity in entities[:limit]:
                    desc = entity.descriptions.get("en", "")[:50]
                    if len(entity.descriptions.get("en", "")) > 50:
                        desc += "..."
                    table.add_row(entity.external_id, entity.labels.get("en", ""), desc)
                
                console.print(table)
        else:
            console.print("[yellow]No search query provided. Use --query to search external sources.[/yellow]")
        
        console.print(f"\n[green]✓ External linking completed[/green]")
        console.print(f"Threshold: {confidence_threshold}")
        console.print(f"Sources: {', '.join(source_list)}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@kg_app.command()
def visualize(
    backend_port: int = typer.Option(8080, "--backend-port", help="Backend port"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser"),
):
    """Launch knowledge graph visualizer."""
    try:
        console.print("[bold cyan]Knowledge Graph Visualizer[/bold cyan]")
        console.print(f"Starting server on port {backend_port}...")
        
        # Start simple HTTP server with knowledge graph data
        import http.server
        import socketserver
        import json
        from pathlib import Path
        import threading
        import webbrowser
        
        # Create sample data for visualization
        sample_data = {
            "entities": [],
            "relationships": [],
            "stats": {"total_entities": 0, "total_relationships": 0}
        }
        
        class KGHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/api/graph":
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(sample_data).encode())
                else:
                    super().do_GET()
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        def start_server():
            with socketserver.TCPServer(("", backend_port), KGHandler) as httpd:
                console.print(f"Server running at http://localhost:{backend_port}")
                httpd.serve_forever()
        
        # Start server in background
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        if open_browser:
            webbrowser.open(f"http://localhost:{backend_port}")
        
        console.print("\n[green]✓ Knowledge Graph Visualizer started[/green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping visualizer...[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@kg_app.command()
def metrics():
    """Display knowledge graph metrics and performance."""
    try:
        # Initialize graph for metrics
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        
        # Generate some sample data
        for i in range(1000):
            entity = graph_store.upsert_entity(
                entity_type="Person" if i % 2 == 0 else "Organization",
                properties={
                    "name": f"Entity_{i}",
                    "index": i,
                    "category": f"Category_{i % 10}"
                }
            )
            
            if i > 0 and i % 3 == 0:
                target_id = graph_store.list_entities()[i // 2].id
                graph_store.create_relationship(
                    entity.id, target_id, "RELATED_TO"
                )
        
        stats = graph_store.get_graph_stats()
        console.print("[bold]Knowledge Graph Performance Metrics[/bold]")
        
        table = Table(title="System Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # Entity metrics
        table.add_row("Total Entities", str(stats["total_entities"]), "✓")
        table.add_row("Entity Types", str(len(stats["entity_types"])), "✓")
        table.add_row("Total Relationships", str(stats["total_relationships"]), "✓")
        table.add_row("Relationship Types", str(len(stats["relationship_types"])), "✓")
        
        console.print(table)
        
        # Performance test
        import time
        
        # Query performance test
        start_time = time.time()
        for _ in range(100):
            graph_store.find_entities_by_properties({"category": "Category_1"})
        query_time = time.time() - start_time
        
        console.print(f"\n[bold]Performance Benchmarks:[/bold]")
        perf_table = Table()
        perf_table.add_column("Operation", style="cyan")
        perf_table.add_column("Time (100 ops)", style="green")
        perf_table.add_column("Rate", style="yellow")
        
        avg_query_time = query_time / 100
        rate = 100 / query_time
        perf_table.add_row("Entity Query", f"{query_time:.3f}s", f"{rate:.1f} ops/sec")
        perf_table.add_row("Average Query", f"{avg_query_time:.4f}s", f"{1/avg_query_time:.1f} ops/sec")
        
        console.print(perf_table)
        
        # Check if performance targets are met
        if avg_query_time < 0.01:  # Sub-second for million-node graphs
            console.print("[green]✓ Performance target met (< 10ms per query)[/green]")
        else:
            console.print("[yellow]⚠ Performance target not met (target: < 10ms per query)[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


app.add_typer(kg_app, name="kg")


if __name__ == "__main__":
    app()
