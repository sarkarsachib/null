# Null-Lang Developer Tools

This document describes the development tools and setup for the Null-Lang programming language, including the Language Server Protocol (LSP) implementation and VS Code extension.

## Table of Contents

- [Language Server Protocol (LSP)](#language-server-protocol-lsp)
  - [Installation](#installation)
  - [Running the Server](#running-the-server)
  - [Features](#features)
- [VS Code Extension](#vs-code-extension)
  - [Installation](#installation-1)
  - [Features](#features-1)
  - [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Language Server Protocol (LSP)

The Null-Lang LSP provides IDE-like features for editing Null-Lang source files, including:

- Syntax error diagnostics
- Code completion
- Hover documentation
- Semantic analysis

### Installation

The LSP server is included with the main Null-Lang package. To install dependencies:

```bash
pip install -e .
```

This installs `pygls` and `orjson` for fast JSON serialization.

### Running the Server

#### Standalone Execution

Start the LSP server directly as a Python module:

```bash
python -m tools.null_lsp.server
```

The server will start on `127.0.0.1:8080` and wait for client connections.

#### Via Language Client

The VS Code extension automatically spawns the server when you open a `.null` file.

### Features

#### Code Completion

Provides intelligent code completion for:
- **Keywords**: `SET`, `SHOW`, `IF`, `THEN`, `ELSE`, `REPEAT`, `TIMES`, `DEFINE`, `WITH`, `DOES`, `AND`, `OR`, `NOT`, `IS`, `EQUALS`, `GREATER`, `LESS`, `THAN`
- **Defined Variables**: All variables defined in the current document
- **Library Functions**: Functions from the Null-Lang standard library (e.g., `math.ADD`, `text.CONCAT`, `array.PUSH`)

**Trigger**: Completion is triggered automatically or with `Ctrl+Space` (or `Cmd+Space` on macOS)

#### Diagnostics

The analyzer provides real-time diagnostics:
- **Parse Errors**: Syntax errors with line and column information
- **Undefined Variables**: Warnings when referencing undefined variables
- **Validation Errors**: Semantic errors in the program

Diagnostics are displayed as squiggles in the editor and in the Problems panel.

#### Hover Information

Hover over language constructs to see documentation:
- Keywords display their syntax and usage
- Variables show their names
- Library functions display their documentation

**Trigger**: Hover with your mouse or press `Ctrl+K Ctrl+I` (or `Cmd+K Cmd+I` on macOS)

## VS Code Extension

The Null-Lang VS Code extension provides a complete IDE experience for editing Null-Lang programs.

### Installation

#### From Source

1. Navigate to the extension directory:
   ```bash
   cd tools/vscode-null
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the extension:
   ```bash
   npm run build
   ```

4. Launch VS Code with the extension:
   ```bash
   code --extensionDevelopmentPath=. /path/to/workspace
   ```

#### Development Mode

For active development with auto-recompilation:

```bash
cd tools/vscode-null
npm run watch
```

Then press `F5` in VS Code to launch the debug window.

### Features

#### Syntax Highlighting

The extension includes a TextMate grammar that highlights Null-Lang syntax:
- **Keywords**: Colored in bold
- **Strings**: Green colored
- **Numbers**: Blue colored
- **Comments**: Gray colored

#### Code Snippets

Snippets provide templates for common constructs:

| Snippet | Prefix | Description |
|---------|--------|-------------|
| Set Variable | `set` | `SET variable TO value` |
| Show Output | `show` | `SHOW expression` |
| If Statement | `if` | `IF condition THEN statement` |
| If-Else | `if-else` | `IF condition THEN ... ELSE ...` |
| Repeat Loop | `repeat` | `REPEAT count TIMES statement` |
| Define Function | `define` | `DEFINE name WITH params DOES body` |
| Add Operation | `add` | `ADD left AND right` |
| Comparison | `compare` | `left IS GREATER/LESS THAN right` |

**Usage**: Type the prefix and press `Tab` to insert the snippet.

#### Commands

Two main commands are available:

- **Null: Run File** (`Ctrl+Alt+N`): Execute the current file via the Null runtime
- **Null: Compile File** (`Ctrl+Alt+C`): Compile the current file with the Null compiler

Both commands open a terminal and display the output.

### Configuration

Configure the extension through VS Code settings:

```json
{
  "null.pythonPath": "python",
  "null.lspPath": "127.0.0.1:8080"
}
```

- `pythonPath`: Path to Python executable (default: `python`)
- `lspPath`: LSP server address (default: `127.0.0.1:8080`)

## Testing

### LSP Analyzer Tests

Unit tests for the LSP analyzer are located in `tests/test_null_lsp_analyzer.py`.

Run tests with pytest:

```bash
pytest tests/test_null_lsp_analyzer.py -v
```

Test coverage includes:
- Document state creation and updates
- Parsing and diagnostics
- Identifier collection and validation
- Completion generation
- Hover information
- Complex program analysis

### Extension Tests

The VS Code extension currently has no automated tests. Future versions may include:
- Language client integration tests
- Grammar validation tests
- Snippet validation tests

## Troubleshooting

### LSP Server Won't Start

**Problem**: `ModuleNotFoundError: No module named 'pygls'`

**Solution**: Install dependencies:
```bash
pip install -e .
```

### Extension Not Connecting to Server

**Problem**: VS Code extension shows "Language server failed to initialize"

**Solution**:
1. Check that the Python environment is correct in settings
2. Verify the server is running: `python -m tools.null_lsp.server`
3. Check the extension logs: View → Output → Null-Lang Language Server
4. Ensure port 8080 is available

### Syntax Highlighting Not Working

**Problem**: `.null` files not being recognized

**Solution**:
1. Reload VS Code: `Ctrl+Shift+P` → Reload Window
2. Verify the grammar file: `tools/vscode-null/syntaxes/null.tmLanguage.json`
3. Check file association: Files should have `.null` extension

### Completions Not Showing

**Problem**: Code completion not triggered

**Solution**:
1. Press `Ctrl+Space` to manually trigger completions
2. Check LSP diagnostics in the console
3. Verify document is recognized as Null language: Bottom right of editor

## Architecture

### LSP Server Components

- **server.py**: Main LSP server using pygls library
- **document_state.py**: Document state management, parsing, and analysis
- **completion.py**: Code completion provider
- **diagnostics.py**: Diagnostic collection and reporting

### Extension Components

- **extension.ts**: VS Code extension activation and command handling
- **null.tmLanguage.json**: TextMate grammar for syntax highlighting
- **language-configuration.json**: Language-specific editor settings
- **snippets/null.json**: Code snippet definitions

## Future Enhancements

- [ ] Semantic token provider for enhanced syntax highlighting
- [ ] Go to definition / Find references
- [ ] Rename symbol refactoring
- [ ] Signature help for function calls
- [ ] Formatting with nullc compiler
- [ ] Debugging support (Debug Adapter Protocol)
- [ ] Performance optimizations for large files
- [ ] WebAssembly-based incremental parser

## Development Workflow

### Setting up Development Environment

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Install extension dependencies:
   ```bash
   cd tools/vscode-null
   npm install
   ```

### Running Tests

```bash
pytest tests/ -v
npm test --prefix tools/vscode-null
```

### Making Changes

1. Edit source files
2. Test changes (run unit tests, manual testing)
3. Build the extension: `npm run build` (in `tools/vscode-null/`)
4. Reload the extension in VS Code

### Contributing

Follow these guidelines:
- Write unit tests for new features
- Maintain documentation
- Use type hints in Python
- Follow existing code style (PEP 8, Prettier for TypeScript)
