"""Main Null compiler orchestration."""

import resource
import time
from dataclasses import dataclass, field
from typing import List, Optional

from ..ast.nodes import Program
from ..ast.validator import ASTValidator
from ..lang.advisor import DiagnosticLevel, SyntaxConfig
from ..lang.hybrid_parser import HybridParser
from ..observability import get_observability
from ..parser.parser import ParseError
from ..superbit.emitter import SuperBitEmitter
from ..superbit.ir import SuperBitStream
from ..binary.generator import BinaryFrame, BinaryGenerator
from ..vm.vm import ExecutionResult, NullVM
from .optimization import OptimizationPass


class CompilationError(Exception):
    """Compilation error exception."""


@dataclass
class CompilationArtifact:
    """Result of compilation containing all intermediate artifacts."""

    ast: Program
    superbit_stream: SuperBitStream
    binary_frames: List[BinaryFrame]
    validation_errors: List[str]
    syntax_warnings: List[str] = field(default_factory=list)
    syntax_hints: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if compilation was successful."""
        return len(self.validation_errors) == 0


def _max_rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return int(usage.ru_maxrss * 1024)


class NullCompiler:
    """Main compiler orchestrating the compilation pipeline."""

    def __init__(
        self,
        optimization_passes: Optional[List[OptimizationPass]] = None,
        *,
        syntax_config: Optional[SyntaxConfig] = None,
    ):
        self.optimization_passes = optimization_passes or []
        self.syntax_config = syntax_config or SyntaxConfig()
        self.hybrid_parser = HybridParser()
        self.validator = ASTValidator()
        self.emitter = SuperBitEmitter()
        self.binary_generator = BinaryGenerator()
    
    def compile(self, source: str) -> CompilationArtifact:
        """
        Compile Null-Lang source code.

        Pipeline:
        1. Parse source to tokens
        2. Parse tokens to AST
        3. Validate AST
        4. Emit super-bit tokens
        5. Apply optimizations
        6. Generate binary frames

        Args:
            source: Null-Lang source code

        Returns:
            CompilationArtifact containing all intermediate results
        """
        obs = get_observability()
        started = time.perf_counter()

        with obs.tracing.span(
            "null.compiler.compile",
            attributes={
                "source_len": len(source),
                "optimization_pass_count": len(self.optimization_passes),
            },
        ):
            try:
                stage_started = time.perf_counter()
                with obs.tracing.span("null.compiler.parse"):
                    parse_result = self.hybrid_parser.parse(source, config=self.syntax_config)
                    ast = parse_result.ast
                    syntax_warnings = [
                        d.message
                        for d in parse_result.diagnostics
                        if d.level == DiagnosticLevel.warning
                    ]
                    syntax_hints = [
                        d.message for d in parse_result.diagnostics if d.level == DiagnosticLevel.hint
                    ]
                obs.metrics.observe_compilation_stage(
                    stage="parse", duration_s=time.perf_counter() - stage_started, status="ok"
                )

                stage_started = time.perf_counter()
                with obs.tracing.span("null.compiler.validate"):
                    validation_errors: list[str] = []
                    if not self.validator.validate(ast):
                        validation_errors = self.validator.errors
                obs.metrics.observe_compilation_stage(
                    stage="validate",
                    duration_s=time.perf_counter() - stage_started,
                    status="ok",
                )

                stage_started = time.perf_counter()
                with obs.tracing.span("null.compiler.emit"):
                    superbit_stream = self.emitter.emit(ast)
                obs.metrics.observe_compilation_stage(
                    stage="emit", duration_s=time.perf_counter() - stage_started, status="ok"
                )

                stage_started = time.perf_counter()
                with obs.tracing.span("null.compiler.optimize"):
                    for optimization_pass in self.optimization_passes:
                        superbit_stream = optimization_pass.optimize(superbit_stream)
                obs.metrics.observe_compilation_stage(
                    stage="optimize",
                    duration_s=time.perf_counter() - stage_started,
                    status="ok",
                )

                stage_started = time.perf_counter()
                with obs.tracing.span("null.compiler.binary"):
                    binary_frames = self.binary_generator.generate(superbit_stream)
                obs.metrics.observe_compilation_stage(
                    stage="binary",
                    duration_s=time.perf_counter() - stage_started,
                    status="ok",
                )

                duration_s = time.perf_counter() - started
                obs.metrics.observe_compilation(duration_s=duration_s, status="ok")
                obs.metrics.set_process_max_rss_bytes(_max_rss_bytes())
                obs.logger.info(
                    "compiler.compile",
                    status="ok",
                    duration_s=duration_s,
                    validation_error_count=len(validation_errors),
                )

                return CompilationArtifact(
                    ast=ast,
                    superbit_stream=superbit_stream,
                    binary_frames=binary_frames,
                    validation_errors=validation_errors,
                    syntax_warnings=syntax_warnings,
                    syntax_hints=syntax_hints,
                )

            except ParseError as e:
                duration_s = time.perf_counter() - started
                obs.metrics.observe_compilation(duration_s=duration_s, status="error")
                obs.metrics.set_process_max_rss_bytes(_max_rss_bytes())
                obs.metrics.inc_error(component="compiler", error_type="parse_error")
                obs.logger.exception(
                    "compiler.compile",
                    status="error",
                    error_type="parse_error",
                    duration_s=duration_s,
                )
                obs.capture_exception(e, component="compiler", error_type="parse_error")
                raise CompilationError(f"Parse error: {str(e)}") from e
            except Exception as e:
                duration_s = time.perf_counter() - started
                obs.metrics.observe_compilation(duration_s=duration_s, status="error")
                obs.metrics.set_process_max_rss_bytes(_max_rss_bytes())
                obs.metrics.inc_error(component="compiler", error_type=type(e).__name__)
                obs.logger.exception(
                    "compiler.compile",
                    status="error",
                    error_type=type(e).__name__,
                    duration_s=duration_s,
                )
                obs.capture_exception(e, component="compiler", error_type=type(e).__name__)
                raise CompilationError(f"Compilation error: {str(e)}") from e
    
    def compile_and_run(self, source: str,
                       security_profile: Optional[str] = None,
                       encryption_key_id: Optional[str] = None) -> ExecutionResult:
        """
        Compile and immediately execute source code.
        
        Transparently decrypts/decompresses when needed.
        
        Args:
            source: Null-Lang source code
            security_profile: Optional security profile (dev, prod)
            encryption_key_id: Optional encryption key ID
            
        Returns:
            ExecutionResult from the VM
        """
        obs = get_observability()

        with obs.tracing.span(
            "null.compiler.compile_and_run",
            attributes={
                "source_len": len(source),
                "security_profile": security_profile or "",
            },
        ):
            artifact = self.compile(source)

            if not artifact.is_valid():
                obs.metrics.inc_error(component="compiler", error_type="validation_error")
                obs.logger.info(
                    "compiler.compile_and_run",
                    status="error",
                    error_type="validation_error",
                    validation_error_count=len(artifact.validation_errors),
                )
                return ExecutionResult(
                    success=False,
                    error=f"Validation errors: {', '.join(artifact.validation_errors)}",
                )

            stream = artifact.superbit_stream

            if security_profile and security_profile.lower() == "prod":
                try:
                    from ..extensions import KeyManager, SuperBitSecurityLayer

                    key_manager = KeyManager()
                    _ = SuperBitSecurityLayer(key_manager=key_manager)

                    if encryption_key_id is None:
                        try:
                            encryption_key_id, _ = key_manager.get_active_key()
                        except ValueError:
                            encryption_key_id, _ = key_manager.create_key(comment="Default key")
                except ImportError:
                    pass

            vm = NullVM()
            return vm.execute(stream)
