# Blocked Subsystems: Requirements, Dependencies, and Phased Deliverables

## Overview

This document captures the requirements, dependencies, and phased deliverables for eight optional subsystems that are currently blocked (LIMIT_REACHED). These subsystems are disabled by default but can be enabled via environment variables or programmatic API.

Each subsystem has placeholder implementations that provide clear TODO hooks for future development. The feature-flag infrastructure (`src/null_system/config.py`) owns the enable/disable switches and dependency ordering.

## The Eight Subsystems

### 1. AI Super-Bit Core (ai_core)

**Purpose**: ML inference engine and tensor operations

**Location**: `src/null_system/ai/core.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- PyTorch 2.0+ integration for tensor operations
- Inference pipeline for neural network models
- Integration with SuperBit IR for AI-optimized instruction encoding
- Support for common architectures (transformers, CNNs, RNNs)

**Dependencies**: None

**API Surface**:
```python
class AIInferenceEngine:
    def __init__(self, model_path: str): ...
    def infer(self, input_tensor: Tensor) -> Tensor: ...
    def load_model(self, path: str) -> None: ...
    def optimize_ir(self, ir: SuperBitStream) -> SuperBitStream: ...
```

**Phased Deliverables**:
- **Phase 1**: Basic PyTorch loader and inference wrapper
- **Phase 2**: SuperBit IR optimization passes
- **Phase 3**: Model quantization and pruning
- **Phase 4**: Distributed inference support

**Acceptance**: Unit tests covering model loading, inference, and IR optimization

---

### 2. Debugger (debugger)

**Purpose**: Step-through debugging and breakpoints

**Location**: `src/null_system/debugger/__init__.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- Breakpoint management (set, clear, conditional)
- Step execution (into, over, out)
- Execution frame introspection (locals, stack, heap)
- Breakpoint hit callbacks
- Integration with LSP for IDE support

**Dependencies**: Visualizer (for execution visualization)

**API Surface**:
```python
class Debugger:
    def set_breakpoint(self, line: int, condition: Optional[str] = None) -> None: ...
    def step_into(self) -> ExecutionFrame: ...
    def step_over(self) -> ExecutionFrame: ...
    def step_out(self) -> ExecutionFrame: ...
    def continue_execution(self) -> None: ...
    def get_current_frame(self) -> ExecutionFrame: ...
```

**Phased Deliverables**:
- **Phase 1**: Basic breakpoint management
- **Phase 2**: Frame introspection
- **Phase 3**: Conditional breakpoints
- **Phase 4**: LSP integration for IDE support

**Acceptance**: Integration tests with step-through scenarios

---

### 3. Visualizer (visualizer)

**Purpose**: AST and execution flow visualization

**Location**: `src/null_system/visualizer/__init__.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- AST visualization (graphviz/mermaid output)
- Execution flow diagrams
- Variable state snapshots
- Interactive rendering (HTML/SVG)
- Export to common formats (PNG, PDF, SVG)

**Dependencies**: None

**API Surface**:
```python
class Visualizer:
    def visualize_ast(self, ast: Program, format: str = "mermaid") -> str: ...
    def visualize_execution_flow(self, trace: ExecutionTrace) -> str: ...
    def render_html(self, diagram: str) -> str: ...
    def export_image(self, diagram: str, format: str, output_path: str) -> None: ...
```

**Phased Deliverables**:
- **Phase 1**: AST to mermaid diagram conversion
- **Phase 2**: Execution trace visualization
- **Phase 3**: HTML/interactive rendering
- **Phase 4**: Advanced features (diff visualization, time-travel debugging)

**Acceptance**: Visual tests confirming diagram correctness

---

### 4. NLP/Knowledge Layer (nlp_knowledge)

**Purpose**: Natural language understanding and knowledge graphs

**Location**: `src/null_system/nlp/__init__.py`

**Status**: Partial implementation with placeholder enhancements

**Existing Implementation**:
- Tokenization, entity extraction, intent classification
- Embeddings and knowledge graph construction

**Requirements**:
- Semantic understanding of Null-Lang code comments
- Knowledge graph querying and inference
- Cross-reference linking
- Semantic search over codebase

**Dependencies**: None

**API Surface**:
```python
class NLPLayer:
    def analyze_semantic_meaning(self, code: str, comments: str) -> SemanticAnalysis: ...
    def build_knowledge_graph(self, ast: Program) -> KnowledgeGraph: ...
    def query_knowledge_graph(self, query: str) -> List[GraphNode]: ...
    def semantic_search(self, query: str, codebase: Codebase) -> List[Match]: ...
```

**Phased Deliverables**:
- **Phase 1**: Enhanced semantic understanding
- **Phase 2**: Knowledge graph querying and inference
- **Phase 3**: Cross-reference linking
- **Phase 4**: Semantic search and recommendations

**Acceptance**: Unit tests for semantic understanding and graph operations

---

### 5. Quantum Hooks (quantum)

**Purpose**: Quantum computing simulation and hooks

**Location**: `src/null_system/quantum/__init__.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- Qiskit integration for quantum simulation
- Quantum circuit encoding in SuperBit IR
- Measurement result handling
- Hybrid classical-quantum execution support

**Dependencies**: None

**API Surface**:
```python
class QuantumSimulator:
    def create_circuit(self, qubits: int) -> QuantumCircuit: ...
    def execute_circuit(self, circuit: QuantumCircuit) -> MeasurementResults: ...
    def encode_to_superbit(self, circuit: QuantumCircuit) -> SuperBitStream: ...
    def hybrid_execute(self, classical_code: str, quantum_circuit: QuantumCircuit) -> Result: ...
```

**Phased Deliverables**:
- **Phase 1**: Basic Qiskit simulator wrapper
- **Phase 2**: SuperBit encoding for quantum circuits
- **Phase 3**: Measurement and result handling
- **Phase 4**: Hybrid execution framework

**Acceptance**: Unit tests for circuit creation and execution

---

### 6. Secure Compression (secure_compression)

**Purpose**: Advanced encryption and compression algorithms

**Location**: `src/null_system/compression/secure_compression.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- ChaCha20-Poly1305 authenticated encryption
- ZSTD compression with dictionary optimization
- Key derivation (Argon2)
- Secure key management
- Compression-then-encryption pipeline

**Dependencies**: None

**API Surface**:
```python
class SecureCompressor:
    def compress_and_encrypt(self, data: bytes, key: bytes) -> bytes: ...
    def decrypt_and_decompress(self, data: bytes, key: bytes) -> bytes: ...
    def derive_key(self, password: str, salt: bytes) -> bytes: ...
    def estimate_compression_ratio(self, data: bytes) -> float: ...
```

**Phased Deliverables**:
- **Phase 1**: Basic ZSTD compression
- **Phase 2**: ChaCha20-Poly1305 encryption
- **Phase 3**: Key derivation and management
- **Phase 4**: Adaptive compression and optimization

**Acceptance**: Roundtrip tests (compress→encrypt→decrypt→decompress)

---

### 7. Network Storage (network_storage)

**Purpose**: Distributed storage with AI optimization

**Location**: `src/null_system/storage/network_store.py`

**Status**: Placeholder – raises `NotImplementedError`

**Requirements**:
- S3-compatible distributed storage interface
- AI-driven data locality optimization
- Replication and failure recovery
- Versioning and snapshots
- Integration with SuperBit IR for efficient encoding

**Dependencies**: Secure Compression (for transport security)

**API Surface**:
```python
class NetworkStore:
    def put(self, key: str, data: bytes, metadata: Dict[str, str]) -> str: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def list(self, prefix: str) -> List[StorageObject]: ...
    def optimize_locality(self, access_pattern: str) -> None: ...
```

**Phased Deliverables**:
- **Phase 1**: S3 client wrapper
- **Phase 2**: Caching and locality optimization
- **Phase 3**: Replication and recovery
- **Phase 4**: Analytics and recommendation engine

**Acceptance**: Integration tests with mock S3 backend

---

### 8. Null LSP (null_lsp)

**Purpose**: Language Server Protocol implementation

**Location**: `src/null_system/lsp/server.py`

**Status**: Partial implementation with placeholder enhancements

**Existing Implementation**:
- Basic LSP server structure
- Document synchronization

**Requirements**:
- Complete language server features (completion, hover, diagnostics, etc.)
- Integration with debugger for debugging support
- Integration with NLP layer for semantic analysis
- Real-time compilation and validation
- Incremental parsing

**Dependencies**: Debugger, NLP/Knowledge Layer

**API Surface**:
```python
class NullLSPServer:
    def on_completion(self, uri: str, position: Position) -> List[CompletionItem]: ...
    def on_hover(self, uri: str, position: Position) -> Optional[Hover]: ...
    def on_definition(self, uri: str, position: Position) -> Optional[Location]: ...
    def on_diagnostic(self, uri: str) -> List[Diagnostic]: ...
    def on_debug_start(self, uri: str) -> DebugSession: ...
```

**Phased Deliverables**:
- **Phase 1**: Code completion and hover
- **Phase 2**: Diagnostics and semantic highlighting
- **Phase 3**: Definition lookup and references
- **Phase 4**: Debugger integration

**Acceptance**: LSP tests against VS Code and Neovim clients

---

## Dependency Graph

```
AI_CORE                 (no dependencies)
VISUALIZER              (no dependencies)
DEBUGGER        ──→     VISUALIZER
QUANTUM                 (no dependencies)
NLP_KNOWLEDGE           (no dependencies)
SECURE_COMPRESSION      (no dependencies)
NETWORK_STORAGE ──→     SECURE_COMPRESSION
NULL_LSP        ──→     DEBUGGER, NLP_KNOWLEDGE
                            ↓
                        VISUALIZER
```

### Dependency Resolution Algorithm

When enabling a subsystem with `config.enable(subsystem, recursive=True)`:
1. Check if all dependencies are already enabled
2. Recursively enable missing dependencies (depth-first)
3. Report any unresolvable conflicts (should not occur with acyclic graph)

Example: Enabling `NULL_LSP` automatically enables:
- `DEBUGGER` → enables `VISUALIZER`
- `NLP_KNOWLEDGE` → enables (no further dependencies)

---

## Feature Flag Configuration

### Environment Variables

```bash
# Enable all subsystems
NULL_SUBSYSTEM_ALL=true

# Enable specific subsystems
NULL_SUBSYSTEM_AI_CORE=true
NULL_SUBSYSTEM_DEBUGGER=true
NULL_SUBSYSTEM_NULL_LSP=true

# Disable specific subsystems (overrides ALL=true)
NULL_SUBSYSTEM_QUANTUM=false
```

### Programmatic API

```python
from null_system.config import get_default_config, Subsystem

config = get_default_config()

# Enable with automatic dependency resolution
config.enable(Subsystem.NULL_LSP)

# Check if enabled
if config.is_enabled(Subsystem.DEBUGGER):
    # Use debugger
    pass

# Get all enabled subsystems
enabled = config.get_enabled_subsystems()

# Graceful error message
error_msg = config.get_error_message(Subsystem.QUANTUM)
print(error_msg)
```

### CLI Flags

The Typer CLI exposes subsystem toggles:

```bash
nullc compile --enable-ai-core --enable-debugger file.null
nullc run --disable-quantum --enable-lsp file.null
nullc --show-subsystems  # List all with descriptions
```

---

## Integration Points

### NullCompiler Integration

```python
from null_system.config import get_default_config

config = get_default_config()
config.enable(Subsystem.AI_CORE)

compiler = NullCompiler(feature_config=config)
artifact = compiler.compile(source)
```

### NullVM Integration

```python
vm = NullVM(registry=registry, feature_config=config)
result = vm.execute(program)
```

### CLI Integration

```python
@app.command()
def compile(
    file: Path = typer.Argument(...),
    enable_ai_core: bool = typer.Option(False, "--enable-ai-core"),
    enable_debugger: bool = typer.Option(False, "--enable-debugger"),
    # ... other options
):
    config = get_default_config()
    if enable_ai_core:
        config.enable(Subsystem.AI_CORE)
    if enable_debugger:
        config.enable(Subsystem.DEBUGGER)
    # ... use config
```

---

## Placeholder Implementation Strategy

Each placeholder module:
1. **Exports typed interfaces** with clear signatures
2. **Raises `NotImplementedError`** with actionable error message
3. **Includes TODO markers** for implementation phases
4. **Gracefully degrades** when disabled via config

Example:
```python
# src/null_system/ai/core.py
"""AI super-bit core (placeholder)."""

class AIInferenceEngine:
    """ML inference engine. TODO: Integrate PyTorch 2.0+"""
    
    def __init__(self, model_path: str) -> None:
        """Initialize inference engine.
        
        TODO: Phase 1 - Load PyTorch model from path
        """
        raise NotImplementedError(
            "AI super-bit core is not yet implemented. "
            "Set NULL_SUBSYSTEM_AI_CORE=true when available."
        )
```

---

## Testing Strategy

### Unit Tests (`tests/test_blocked_modules.py`)

```python
def test_config_defaults():
    """All subsystems disabled by default."""
    
def test_enable_with_dependencies():
    """Enabling subsystem enables dependencies."""
    
def test_disable_cascades():
    """Disabling subsystem can cascade to dependents."""
    
def test_env_var_loading():
    """Environment variables correctly override defaults."""
    
def test_placeholder_raises():
    """Placeholder implementations raise NotImplementedError."""
    
def test_error_messages():
    """Graceful error messages for disabled subsystems."""
```

### Integration Tests

- Compile with various subsystem combinations
- Verify no side effects when disabled
- Validate dependency resolution

---

## Rollout Plan

### Week 1: Foundation
- [x] Config module with feature flags
- [x] Documentation (this file)
- [x] Placeholder packages
- [x] Unit tests
- [ ] CLI integration (optional for MVP)

### Week 2: First Subsystem
- [ ] Pick highest-priority subsystem (e.g., DEBUGGER or AI_CORE)
- [ ] Implement Phase 1
- [ ] Add integration tests
- [ ] Update documentation

### Week 3+: Phased Rollout
- [ ] Implement remaining subsystems in phases
- [ ] Each phase in isolated PR with smaller diff
- [ ] Maintain feature flag coverage

---

## Design Principles

1. **Modularity**: Each subsystem is self-contained, with clear interfaces
2. **Graceful Degradation**: Disabled subsystems fail with actionable error messages
3. **No Side Effects**: Placeholder modules import without execution
4. **Testability**: All subsystems and configuration are thoroughly tested
5. **Dependency Management**: Automatic recursive dependency resolution
6. **Environment-Driven**: Enable/disable via env vars or CLI for CI/CD flexibility
7. **Documentation**: Each subsystem has clear requirements and phased deliverables

---

## Future Enhancements

- [ ] Dynamic subsystem loading (plugins)
- [ ] Version constraints for subsystems
- [ ] Subsystem health checks
- [ ] Automatic subsystem dependency graph visualization
- [ ] Telemetry for subsystem usage
- [ ] Performance profiling per subsystem
