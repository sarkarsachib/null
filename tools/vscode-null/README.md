# Null-Lang VS Code Extension

This extension provides complete IDE support for Null-Lang, including syntax highlighting, code completion, diagnostics, and code snippets.

## Features

- **Syntax Highlighting**: Automatic highlighting for Null-Lang keywords, strings, numbers, and comments
- **Code Completion**: Intelligent completions for keywords, variables, and library functions
- **Diagnostics**: Real-time error detection and validation
- **Hover Information**: View documentation by hovering over keywords and identifiers
- **Code Snippets**: Quick templates for common programming patterns
- **Language Commands**: Run and compile Null-Lang files with integrated terminal support

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone <repository-url>
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

4. Install in VS Code:
   ```bash
   code --install-extension vscode-null-0.1.0.vsix
   ```

### Development Installation

For active development with auto-recompilation:

```bash
cd tools/vscode-null
npm run watch
```

Then press `F5` in VS Code to launch the debug window with the extension loaded.

## Configuration

Configure the extension through VS Code settings (`settings.json`):

```json
{
  "null.pythonPath": "python",
  "null.lspServerAddress": "127.0.0.1:8080"
}
```

- `pythonPath`: Path to Python executable (default: `python`)
- `lspServerAddress`: LSP server network address (default: `127.0.0.1:8080`)

## Usage

### Syntax Highlighting

Open any `.null` file to automatically enable syntax highlighting:

```null
SET x TO 10
SHOW x
```

### Code Completion

Type to trigger completions automatically, or press `Ctrl+Space` (or `Cmd+Space` on macOS):

- Keywords: `SET`, `SHOW`, `IF`, `REPEAT`, etc.
- Variables: All defined variables in the current file
- Library functions: Functions from the Null-Lang standard library

### Hover Documentation

Hover over keywords, variables, or functions to see documentation:

```null
SET x TO 10  # Hover over "SET" to see syntax
SHOW x       # Hover over "x" to see variable info
```

### Code Snippets

Use snippets for quick code templates:

| Snippet | Prefix | Example |
|---------|--------|---------|
| Set Variable | `set` | `SET variable TO value` |
| Show Output | `show` | `SHOW expression` |
| If Statement | `if` | `IF condition THEN ... END IF` |
| If-Else | `if-else` | `IF ... THEN ... ELSE ... END IF` |
| Repeat Loop | `repeat` | `REPEAT count TIMES ... END REPEAT` |
| Define Function | `define` | `DEFINE name WITH params ... END DEFINE` |
| Add Operation | `add` | `ADD left AND right` |
| Comparison | `compare` | `left IS GREATER THAN right` |

Type the prefix and press `Tab` to expand the snippet.

### Commands

- **Null: Run File** (`Ctrl+Alt+N`): Execute the current file
- **Null: Compile File** (`Ctrl+Alt+C`): Compile the current file

Both commands open a terminal and show the output.

## Requirements

- VS Code 1.60.0 or higher
- Python 3.11+ with Null-Lang installed
- pygls and orjson Python packages (installed automatically with Null-Lang)

## Troubleshooting

### Extension not activating

**Issue**: Extension doesn't activate when opening `.null` files

**Solution**:
1. Reload VS Code: `Ctrl+Shift+P` → "Reload Window"
2. Check extension status: View → Extensions, search for "Null-Lang"
3. Enable the extension if disabled

### Language server not connecting

**Issue**: "Language server failed to initialize" error

**Solution**:
1. Check Python installation: `python --version`
2. Verify Null-Lang is installed: `python -m null_system --help`
3. Check LSP server is running: `python -m tools.null_lsp.server`
4. View logs: Output panel → "Null-Lang Language Server"

### Syntax highlighting not working

**Issue**: `.null` files not being highlighted

**Solution**:
1. Verify file extension is `.null`
2. Set language mode: Click language selector (bottom right) → select "Null-Lang"
3. Check grammar file exists: `syntaxes/null.tmLanguage.json`

### Completions not showing

**Issue**: Code completion not triggered

**Solution**:
1. Press `Ctrl+Space` to manually trigger completions
2. Check extension settings for LSP configuration
3. Verify language server is running and connected
4. Check the Output panel for error messages

## Development

### Project Structure

```
tools/vscode-null/
├── src/
│   └── extension.ts          # Extension entry point
├── syntaxes/
│   └── null.tmLanguage.json  # Syntax highlighting grammar
├── snippets/
│   └── null.json             # Code snippets
├── language-configuration.json
├── package.json
└── tsconfig.json
```

### Building

```bash
npm run build      # Build the extension
npm run watch      # Watch for changes and rebuild
```

### Testing

Currently, no automated tests are implemented. To manually test:

1. Build the extension: `npm run build`
2. Press `F5` in VS Code to launch the debug window
3. Test features in the debug VS Code instance

## Contributing

Contributions are welcome! Please follow these guidelines:

- Write TypeScript code with strict type checking
- Follow existing code style and patterns
- Update documentation for new features
- Test changes manually before submitting

## License

MIT
