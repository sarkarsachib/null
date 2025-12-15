from __future__ import annotations

import re


def to_english(source: str) -> str:
    source = _modern_let_to_english(source)
    source = _modern_print_to_english(source)
    return source


def to_modern(source: str) -> str:
    source = _english_set_to_modern(source)
    source = _english_show_to_modern(source)
    return source


_LET_RE = re.compile(
    r"(?m)^\s*let\s+(?P<mut>mut\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<expr>.+?)\s*;\s*$"
)


def _modern_let_to_english(source: str) -> str:
    def repl(m: re.Match[str]) -> str:
        name = m.group("name")
        expr = m.group("expr").strip()
        return f"SET {name} TO {expr}"

    return _LET_RE.sub(repl, source)


_PRINT_RE = re.compile(r"(?m)^\s*print\s*\(\s*(?P<expr>.*?)\s*\)\s*;\s*$")


def _modern_print_to_english(source: str) -> str:
    return _PRINT_RE.sub(lambda m: f"SHOW {m.group('expr').strip()}", source)


_SET_RE = re.compile(r"(?m)^\s*SET\s+(?P<name>[A-Za-z_][A-Za-z0-9_\.\[\]]*)\s+TO\s+(?P<expr>.+?)\s*$", re.IGNORECASE)


def _english_set_to_modern(source: str) -> str:
    def repl(m: re.Match[str]) -> str:
        name = m.group("name")
        expr = m.group("expr").strip()
        return f"let {name} = {expr};"

    return _SET_RE.sub(repl, source)


_SHOW_RE = re.compile(r"(?m)^\s*SHOW\s+(?P<expr>.+?)\s*$", re.IGNORECASE)


def _english_show_to_modern(source: str) -> str:
    return _SHOW_RE.sub(lambda m: f"print({m.group('expr').strip()});", source)
