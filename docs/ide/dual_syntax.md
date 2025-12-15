# Dual-Syntax (English + Modern) Editor Mode

Null supports a dual-syntax workflow:

- **English syntax**: friendly, verbose, readable (`SET x TO 5`)
- **Modern syntax**: concise, Rust/Kotlin-inspired (`let x = 5;`)
- **Hybrid syntax**: mix both in the same document or project

This repository ships a basic Language Server Protocol (LSP) implementation that:

- Detects per-document syntax mode (`english`, `modern`, `hybrid`, `auto`)
- Produces syntax-aware diagnostics
- Provides keyword/operator completions
- Shows hovers with alternate-syntax snippets
- Offers code actions to rewrite code between syntaxes

## Running the LSP

Install the package (editable is fine):

```bash
pip install -e .
```

Start the server over stdio (recommended for most editors):

```bash
nullc lsp --syntax auto --stdio
```

Or run as a TCP server:

```bash
nullc lsp --syntax english --tcp --port 2087
```

### Initialization options

Clients can pass `initializationOptions`:

```json
{
  "syntax": "auto",
  "hybrid_detection": true
}
```

- `syntax`: `english` | `modern` | `hybrid` | `auto`
- `hybrid_detection`: when `true`, `auto` mode chooses a syntax per document

## Dual highlighting assets

Theme/token assets are published under:

- `tools/editor/themes/english.json`
- `tools/editor/themes/modern.json`
- `tools/editor/themes/hybrid.json`

Editor integrations can map these tokens to their own theming system.

## Suggested editor configuration

A typical workflow:

- `editor_mode = "dual"`: enable dual highlighting (English + modern markers)
- `transpile_on_save = true`: on save, run a rewrite action (e.g., convert modern to English)

Exact integration depends on the editor client; the shipped LSP exposes the rewrite operations as `textDocument/codeAction` items.

## Screenshots / GIFs

- `[placeholder]` dual highlighting in hybrid mode
- `[placeholder]` code action: “Convert to English”
