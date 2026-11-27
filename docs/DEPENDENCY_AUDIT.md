# Dependency Audit

Phase 0 requirement: "make every external dependency, library, packages port or
rebuild into null." This document is the ledger. Nothing here is closed until
there is a Null replacement with tests.

Measured by `grep -rlE "(from|import) <pkg>" src --include='*.py'` plus
`package.json`, on 2026-11-27.

## Python — declared vs used

`pyproject.toml` declares 6 runtime dependencies; `requirements.txt` declares 16.
Only 13 of those appear in `src/` at all.

| Package | Declared in | Files importing it | Phase 7 disposition |
| --- | --- | --- | --- |
| `lark` / `lark-parser` | pyproject + requirements | 3 | **Ported** — replaced by the bootstrap lexer/parser in Null |
| `numpy` | requirements | 7 | Ported or dropped — only used by ML/quantization |
| `rich` | pyproject + requirements | 1 | Dropped — terminal formatting, not language |
| `cryptography` | requirements | 1 | Ported — security module |
| `pygls` + `lsprotocol` | pyproject + requirements | 1 + 1 | Ported — LSP server |
| `fastapi` + `uvicorn` | pyproject + requirements | 2 + 2 | Ported — HTTP surface |
| `opentelemetry` | not declared | 2 | Dropped or ported — observability |
| `torch` + `torchvision` | requirements | 1 + 1 | Out of scope for the language |
| `sentry_sdk` | not declared | 1 | Dropped |
| `prometheus_client` | not declared | 1 | Dropped or ported |
| `psutil` | requirements | 1 | Ported — process info |
| `requests` | not declared | 1 | Ported — HTTP client |
| `typer` | pyproject + requirements | 1 | Ported — CLI framework |
| `scipy` | requirements | **0** | Remove from requirements |
| `onnxruntime` | requirements | **0** | Remove from requirements |
| `httpx` | requirements | **0** | Remove from requirements |

Three declared dependencies are imported nowhere. That is a real defect in the
manifest, independent of the porting effort.

Four packages are imported but **not declared** (`opentelemetry`, `sentry_sdk`,
`prometheus_client`, `requests`). A clean install from `pyproject.toml` will fail
at import time for those modules.

## Critical path

The dependency that actually matters for self-hosting is **`lark`**. It is the
parser generator behind all three Python front ends:

- `src/null_system/lang/parser.py` — `grammar.lark`, 237 lines, 50 rules
- `src/null_system/lang/modern/modern_rust.py` — `modern_rust.lark`, 145 lines
- `src/null_system/lang/modern/modern_python.py` — `modern_python.lark`, 142 lines

`bootstrap/lexer.null` (256 lines) and `bootstrap/parser.null` (2,286 lines) are
hand-written Null replacements that already exist and already work — the native
fixed point depends on them. So `lark` is not needed to self-host; it is only
needed by the Python front ends that Phase 1 retires. **Phase 1 removes this
dependency as a side effect**, which is why it is not a separate work item.

## Node

`package.json` declares:

- runtime: `tweetnacl@^1.0.3`, `uuid@^13.0.0`
- dev: `jest`, `ts-jest`, `ts-node`, `typescript`, `eslint` + two plugins,
  `prettier`, `@types/node`, `@types/jest`, `@types/uuid`

`tweetnacl` is a crypto library used by the TypeScript security module;
`uuid` for identifiers. Both would be replaced by Null equivalents in Phase 7.

Note: the TypeScript tree does not currently typecheck (97 errors), so no Node
dependency is load-bearing for a working artifact. See
[`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) § TypeScript VM.

## System dependencies

| Tool | Used by | Replaceable? |
| --- | --- | --- |
| `cc` / `gcc` | assembles the backend's `.s` output | Not in scope — an assembler is required for any native backend |
| `as` (GNU, Intel syntax) | implied by the emitted `.s` | Same |
| Python 3.11+ | `bench/stage_runner.py`, all `tests/`, the CLI | Yes — Phase 4 |
| Node 24 | TypeScript VM and its tests | Yes — the TS VM is not in the shipped path |
| `venv/` (3,676 tracked files) | every pytest run | Build hygiene, see below |

## Repository hygiene defects found during the audit

These are not dependency questions but they affect reproducibility:

1. **`venv/` is tracked.** 3,676 files under `venv/` are in Git, including
   `.pyc` files (1,067 tracked `.pyc` total), even though `.gitignore` lists
   `venv/` and `__pycache__/`. Every test run dirties the tree.
2. **A stray file named `=0.12.0` is tracked** at the repo root. It contains
   `pip install` output (`Collecting lark-parser`, `Downloading lark_parser-0.12.0…`)
   from a shell command where the version specifier was not quoted. 57 lines.
3. **`requirements.txt` and `pyproject.toml` disagree** on both membership and
   version floors, and neither matches actual imports.

## Porting order

1. `lark` — retires with Phase 1, not a port.
2. `typer` — the CLI is the entry point to everything else; port it with the
   `build/test/fmt/clean/add/doc/bench` commands in Phase 6.
3. `rich` — 1 file, and the CLI is being rewritten anyway.
4. `cryptography` — the security module is self-contained enough to port.
5. `numpy` — only the ML subsystem; decide whether ML ships at all before porting.
6. `torch` / `torchvision` / `onnxruntime` / `scipy` — remove unless ML is a
   stated deliverable. Nothing in the language depends on them.
7. `fastapi` / `uvicorn` / `pygls` / `lsprotocol` — tooling surfaces, port after
   the core toolchain works.
8. `opentelemetry` / `sentry_sdk` / `prometheus_client` / `psutil` / `requests`
   — infrastructure, last.

## Exit criteria for Phase 7

- `grep -rE "(from|import) (lark|numpy|…)" src --include='*.py'` returns nothing.
- `pyproject.toml` and `requirements.txt` declare the same set, and every entry is
  imported.
- `venv/` and `=0.12.0` are gone from Git.
- Each replacement has a Null test, not a Python test.
