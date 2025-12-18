# Null-Lang Module System

## Overview

The Null-Lang module system provides namespacing, code organization, and symbol visibility management across multiple source files. It enables large-scale program development with clear module boundaries and explicit dependencies.

## Features

- **Module Declarations**: Define named modules with hierarchical namespaces
- **Import Statements**: Import symbols from other modules with optional aliasing
- **Qualified Identifiers**: Reference symbols using `::` separator (e.g., `math::sqrt`)
- **Backward Compatibility**: Legacy programs without modules continue to work
- **Module Metadata**: Full module information preserved in IR for debugging and tooling

## Syntax

### Module Declaration

Declare a module at the beginning of a file (before any statements):

```null
module <module_name>
```

Examples:

```null
module math
```

```null
module std::collections::vector
```

The module name can be:
- A simple identifier: `math`, `utils`, `helpers`
- A qualified path: `std::io`, `company::product::feature`

### Import Statement

Import modules to use their symbols:

```null
import <module_name>
```

```null
import <module_name> as <alias>
```

Examples:

```null
import math
import std::io as io
import collections
```

Multiple imports:

```null
import math
import std::io as io
import std::collections::vector as vec
```

### Qualified Identifiers

Reference symbols from modules using the `::` separator:

```null
math::pi
std::io::println
vec::new
```

Use in expressions:

```null
SET x TO math::pi TIMES 2
CALL std::io::println WITH "Hello"
SET v TO vec::new()
```

## AST Structure

### New AST Nodes

#### `ModuleDeclaration`

Represents a module header:

```python
@dataclass
class ModuleDeclaration(ASTNode):
    """Represents a module declaration: module foo::bar."""
    name: QualifiedIdentifier
```

#### `ImportStatement`

Represents an import:

```python
@dataclass
class ImportStatement(ASTNode):
    """Represents an import statement: import foo or import foo as bar."""
    module_name: QualifiedIdentifier
    alias: Optional[str] = None
    annotations: List[Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]] = field(default_factory=list)
```

#### `QualifiedIdentifier`

Represents a qualified name like `math::sqrt`:

```python
@dataclass
class QualifiedIdentifier(ASTNode):
    """Represents a qualified identifier like math::add or std::io::println."""
    parts: List[str]
    
    @property
    def full_name(self) -> str:
        """Return the full qualified name as a string."""
        return "::".join(self.parts)
    
    @property
    def module_path(self) -> List[str]:
        """Return the module path (all parts except the last)."""
        return self.parts[:-1] if len(self.parts) > 1 else []
    
    @property
    def name(self) -> str:
        """Return the final name component."""
        return self.parts[-1] if self.parts else ""
```

#### `Program` (Enhanced)

The Program node now includes module information:

```python
@dataclass
class Program(ASTNode):
    """Represents a complete program (top-level AST node)."""
    module_declaration: Optional[ModuleDeclaration] = None
    imports: List[ImportStatement] = field(default_factory=list)
    statements: List[ASTNode] = field(default_factory=list)
```

## Grammar

### Module Header

```lark
program: module_header? import_section? statement*

module_header: "module" module_name

module_name: NAME ("::" NAME)*
```

### Import Section

```lark
import_section: import_statement+

import_statement: annotation* "import" module_name ("as" identifier)?
```

### Qualified Names

```lark
qualified_name.2: NAME ("::" NAME)+

identifier.1: NAME
```

The priority numbers ensure that qualified names (with `::`) are matched before simple identifiers.

## Compiler Behavior

### Module Metadata

The compiler tracks the current module and includes it in IR token metadata:

```python
class NullLangCompiler:
    def __init__(self):
        self.current_module: str = "__main__"
        self.imported_modules: Dict[str, str] = {}
    
    def _emit(self, opcode, operand=None, metadata=None):
        token_metadata = self.current_metadata.copy()
        if self.current_module != "__main__":
            token_metadata["module"] = self.current_module
        # ...
```

### Program Compilation

When compiling a Program node:

1. Extract module declaration → set `current_module`
2. Process imports → populate `imported_modules` mapping
3. Compile statements with module context

```python
def _visit_Program(self, node: Program) -> None:
    if hasattr(node, 'module_declaration') and node.module_declaration:
        self.current_module = node.module_declaration.name.full_name
    
    if hasattr(node, 'imports'):
        for import_stmt in node.imports:
            module_name = import_stmt.module_name.full_name
            alias = import_stmt.alias or module_name
            self.imported_modules[alias] = module_name
    
    for stmt in node.statements:
        self._visit(stmt)
```

## VM Execution

### Module Namespaces

The VM maintains separate namespaces for each module:

```python
class NullVM:
    def __init__(self):
        self.module_namespaces: Dict[str, Dict[str, Any]] = {"__main__": {}}
        self.current_module: str = "__main__"
```

### Variable Resolution

Variables are resolved using module-aware lookup:

1. Check if name is qualified (`::` present)
   - Extract module and local name
   - Look up in that module's namespace
2. Otherwise use current module context from token metadata
3. Fall back to global `variables` dict for backward compatibility

```python
def _resolve_variable_name(self, name: str, token: SuperBitToken) -> tuple[str, str]:
    """Resolve variable name to (module, local_name)."""
    if "::" in name:
        parts = name.split("::")
        module = "::".join(parts[:-1])
        local_name = parts[-1]
        return (module, local_name)
    
    module = token.metadata.get("module", self.current_module) if hasattr(token, 'metadata') else self.current_module
    return (module, name)
```

### LOAD_VAR

```python
elif token.opcode == SuperBitOpCode.LOAD_VAR:
    module, local_name = self._resolve_variable_name(token.operand, token)
    
    if module in self.module_namespaces and local_name in self.module_namespaces[module]:
        self.stack.append(self.module_namespaces[module][local_name])
    elif token.operand in self.variables:
        self.stack.append(self.variables[token.operand])
    else:
        raise RuntimeError(f"Undefined variable: {token.operand}")
```

### STORE_VAR

```python
elif token.opcode == SuperBitOpCode.STORE_VAR:
    value = self.stack.pop()
    module, local_name = self._resolve_variable_name(token.operand, token)
    
    if module not in self.module_namespaces:
        self.module_namespaces[module] = {}
    self.module_namespaces[module][local_name] = value
    
    # Also store in global dict for backward compat
    self.variables[token.operand] = value
```

## Validation

The `ASTValidator` enforces module constraints:

### Symbol Tables

- Per-module symbol tables track defined variables
- Imported modules are recorded
- Module aliases are mapped to full module names

```python
class ASTValidator:
    def __init__(self):
        self.current_module: Optional[str] = None
        self.module_symbols: Dict[str, Set[str]] = {}
        self.imported_modules: Set[str] = set()
        self.module_aliases: Dict[str, str] = {}
```

### Program Validation

```python
def _visit_Program(self, node: Program):
    # Set current module
    if hasattr(node, 'module_declaration') and node.module_declaration:
        module_name = node.module_declaration.name.full_name
        self.current_module = module_name
        if module_name not in self.module_symbols:
            self.module_symbols[module_name] = set()
    else:
        self.current_module = "__main__"
        if "__main__" not in self.module_symbols:
            self.module_symbols["__main__"] = set()
    
    # Track imports
    if hasattr(node, 'imports'):
        for import_stmt in node.imports:
            module_name = import_stmt.module_name.full_name
            self.imported_modules.add(module_name)
            if import_stmt.alias:
                self.module_aliases[import_stmt.alias] = module_name
    
    for stmt in node.statements:
        self._visit(stmt)
```

### Variable Tracking

Variables are added to the current module's symbol table:

```python
def _visit_SetCommand(self, node):
    self._visit(node.value)
    target = node.target
    if hasattr(target, 'name'):
        identifier = target.name
    else:
        identifier = str(target)
    self.defined_variables.add(identifier)
    if self.current_module and self.current_module in self.module_symbols:
        self.module_symbols[self.current_module].add(identifier)
```

## Examples

### Simple Module

**math.null**:
```null
module math

SET pi TO 3.14159265359
SET e TO 2.71828182846

DEFINE square WITH x
    SET result TO x TIMES x
END DEFINE
```

### Using Imports

**app.null**:
```null
module app
import math

SET radius TO 5
SET circumference TO 2 TIMES math::pi TIMES radius
SHOW circumference
```

### Nested Modules

**std/io/console.null**:
```null
module std::io::console

DEFINE println WITH message
    SHOW message
END DEFINE

DEFINE print WITH message
    # Print without newline (placeholder)
    SHOW message
END DEFINE
```

**main.null**:
```null
module main
import std::io::console as console

CALL console::println WITH "Hello, World!"
CALL console::println WITH "Module system working!"
```

### Multiple Imports

```null
module myapp
import math
import std::io as io
import std::collections::vector as vec

SET data TO vec::new()
SET pi_value TO math::pi
CALL io::println WITH "Starting computation..."
```

## Migration Guide

### Existing Programs

All existing single-file programs continue to work without modification:

**Before (and still works)**:
```null
SET x TO 42
SET y TO 10
SHOW x PLUS y
```

This is automatically treated as:
```null
module __main__

SET x TO 42
SET y TO 10
SHOW x PLUS y
```

### Converting to Modules

To convert an existing program to use modules:

1. **Add module declaration** at the top:
   ```null
   module mymodule
   ```

2. **Extract reusable code** into separate module files

3. **Add imports** where needed:
   ```null
   import helpers
   import utils
   ```

4. **Use qualified names** for cross-module references:
   ```null
   SET result TO helpers::process(data)
   ```

## Future Enhancements

### Planned Features

1. **Module Loading**: Dynamic module loading from files
2. **Visibility Modifiers**: Public/private symbol control
3. **Re-exports**: `export * from module`
4. **Relative Imports**: `import ./local_module`
5. **Standard Library**: Built-in `std` module hierarchy
6. **Package Management**: Module versioning and dependencies

### Tooling Integration

- **LSP**: Module-aware autocomplete and navigation
- **Debugger**: Step through module boundaries
- **Profiler**: Per-module performance metrics
- **Documentation**: Auto-generate module API docs

## Best Practices

1. **One Module Per File**: Keep modules in separate files for clarity
2. **Descriptive Names**: Use meaningful module names (e.g., `math`, `io`, `collections`)
3. **Hierarchical Organization**: Use `::` for logical grouping (e.g., `std::io::file`)
4. **Explicit Imports**: Always import modules explicitly
5. **Avoid Circular Imports**: Structure dependencies as a DAG
6. **Aliasing**: Use `as` to avoid name conflicts

## Testing

Comprehensive test suite in `tests/test_modules.py`:

- Module declaration parsing
- Import statement parsing
- Qualified identifier handling
- Validation with module tracking
- Compiler module metadata
- VM module namespace execution
- Backward compatibility verification

Run tests:
```bash
python -m pytest tests/test_modules.py -v
```

## See Also

- [Null v2 Language Specification](null_v2_language_spec.md)
- [Grammar Reference](../src/null_system/lang/grammar.lark)
- [AST Node Definitions](../src/null_system/lang/ast_nodes.py)
- [Compiler Implementation](../src/null_system/lang/compiler.py)
- [VM Implementation](../src/null_system/vm/vm.py)
