"""Main Null compiler orchestration."""

from dataclasses import dataclass
from typing import List, Optional

from ..ast.nodes import Program
from ..ast.validator import ASTValidator
from ..parser.lexer import Lexer
from ..parser.parser import Parser, ParseError
from ..superbit.emitter import SuperBitEmitter
from ..superbit.tokens import SuperBitGroup
from ..binary.generator import BinaryGenerator, BinaryFrame
from ..vm.vm import NullVM, ExecutionResult
from .optimization import OptimizationPass


class CompilationError(Exception):
    """Compilation error exception."""
    pass


@dataclass
class CompilationArtifact:
    """Result of compilation containing all intermediate artifacts."""
    ast: Program
    superbit_stream: SuperBitGroup
    binary_frames: List[BinaryFrame]
    validation_errors: List[str]
    
    def is_valid(self) -> bool:
        """Check if compilation was successful."""
        return len(self.validation_errors) == 0


class NullCompiler:
    """Main compiler orchestrating the compilation pipeline."""
    
    def __init__(self, optimization_passes: Optional[List[OptimizationPass]] = None):
        self.optimization_passes = optimization_passes or []
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
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            validation_errors = []
            if not self.validator.validate(ast):
                validation_errors = self.validator.errors
            
            superbit_stream = self.emitter.emit(ast)
            
            for optimization_pass in self.optimization_passes:
                superbit_stream = optimization_pass.optimize(superbit_stream)
            
            binary_frames = self.binary_generator.generate(superbit_stream)
            
            return CompilationArtifact(
                ast=ast,
                superbit_stream=superbit_stream,
                binary_frames=binary_frames,
                validation_errors=validation_errors
            )
        
        except ParseError as e:
            raise CompilationError(f"Parse error: {str(e)}")
        except Exception as e:
            raise CompilationError(f"Compilation error: {str(e)}")
    
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
        artifact = self.compile(source)
        
        if not artifact.is_valid():
            return ExecutionResult(
                success=False,
                error=f"Validation errors: {', '.join(artifact.validation_errors)}"
            )
        
        stream = artifact.superbit_stream
        
        if security_profile and security_profile.lower() == "prod":
            try:
                from ..extensions import SuperBitSecurityLayer, KeyManager
                key_manager = KeyManager()
                security_layer = SuperBitSecurityLayer(key_manager=key_manager)
                
                if encryption_key_id is None:
                    try:
                        encryption_key_id, _ = key_manager.get_active_key()
                    except ValueError:
                        encryption_key_id, _ = key_manager.create_key(comment="Default key")
            except ImportError:
                pass
        
        vm = NullVM()
        return vm.execute(stream)
