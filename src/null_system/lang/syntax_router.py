from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from .errors import LexerError, NullLangError, SyntaxError
from .parser import NullLangParser
from .ast_nodes import SourceSpan


class SyntaxMode(str, Enum):
    english = "english"
    modern = "modern"
    hybrid = "hybrid"
    auto = "auto"


@dataclass(frozen=True)
class DiagnosticIssue:
    message: str
    span: Optional[SourceSpan] = None
    source: str = "null"


class SyntaxAdvisor:
    _english_markers = re.compile(r"\b(SET|SHOW|ADD|IF|THEN|ELSE|REPEAT|DEFINE|CALL|RETURN|END)\b", re.IGNORECASE)
    _modern_markers = re.compile(r"\b(let|fn|match|return|print|true|false)\b|\{|\}|;|::|=>", re.IGNORECASE)
    _syntax_directive = re.compile(r"^\s*@syntax\s+(english|modern|hybrid|auto)\s*$", re.IGNORECASE | re.MULTILINE)

    def detect_mode(self, source: str) -> SyntaxMode:
        directive = self._syntax_directive.search(source)
        if directive:
            try:
                declared = SyntaxMode(directive.group(1).lower())
            except ValueError:
                declared = None
            if declared and declared != SyntaxMode.auto:
                return declared

        has_english = bool(self._english_markers.search(source))
        has_modern = bool(self._modern_markers.search(source))
        if has_english and has_modern:
            return SyntaxMode.hybrid
        if has_modern:
            return SyntaxMode.modern
        return SyntaxMode.english


class ParserDispatcher:
    def __init__(self) -> None:
        self.english_parser = NullLangParser()

    def check(self, source: str, mode: SyntaxMode) -> tuple[SyntaxMode, list[DiagnosticIssue]]:
        if mode == SyntaxMode.auto:
            mode = SyntaxAdvisor().detect_mode(source)

        if mode == SyntaxMode.english:
            return mode, list(check_english(source, self.english_parser))
        if mode == SyntaxMode.modern:
            return mode, list(check_modern(source))
        if mode == SyntaxMode.hybrid:
            return mode, list(check_hybrid(source, self.english_parser))
        return mode, [DiagnosticIssue(message=f"Unknown syntax mode: {mode}")]


class HybridParser:
    def __init__(self) -> None:
        self.dispatcher = ParserDispatcher()

    def check(self, source: str, mode: SyntaxMode = SyntaxMode.auto) -> tuple[SyntaxMode, list[DiagnosticIssue]]:
        return self.dispatcher.check(source, mode)


def check_english(source: str, parser: Optional[NullLangParser] = None) -> Iterable[DiagnosticIssue]:
    parser = parser or NullLangParser()
    source = SyntaxAdvisor._syntax_directive.sub("", source)
    try:
        parser.parse(source)
        return
    except (SyntaxError, LexerError) as e:
        yield DiagnosticIssue(message=e.message, span=e.span, source="english")
    except NullLangError as e:
        yield DiagnosticIssue(message=e.message, span=e.span, source="english")
    except Exception as e:  # pragma: no cover
        yield DiagnosticIssue(message=str(e), span=None, source="english")


_MODERN_LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*let\s+(mut\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*.+;\s*$"), "let"),
    (re.compile(r"^\s*print\s*\(.*\)\s*;\s*$"), "print"),
    (re.compile(r"^\s*fn\s+[A-Za-z_][A-Za-z0-9_]*\s*\(.*\)\s*(->\s*\w+\s*)?\{?\s*$"), "fn"),
    (re.compile(r"^\s*}\s*$"), "}"),
    (re.compile(r"^\s*\{\s*$"), "{"),
]


def _span_for_line(source: str, line_no_1: int, start_col_1: int, end_col_1: int) -> SourceSpan:
    lines = source.splitlines()
    text = ""
    if 0 <= line_no_1 - 1 < len(lines):
        text = lines[line_no_1 - 1]
    return SourceSpan(line_no_1, start_col_1, line_no_1, end_col_1, text)


def check_modern(source: str) -> Iterable[DiagnosticIssue]:
    lines = source.splitlines() or [""]
    brace_balance = 0
    paren_balance = 0

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.lower().startswith("@syntax"):
            continue

        brace_balance += line.count("{") - line.count("}")
        paren_balance += line.count("(") - line.count(")")

        if any(pat.match(line) for pat, _ in _MODERN_LINE_PATTERNS):
            continue

        if stripped.endswith(";") or stripped.endswith("{") or stripped == "}":
            yield DiagnosticIssue(
                message="Unrecognized modern syntax statement",
                span=_span_for_line(source, idx, 1, max(2, len(line) + 1)),
                source="modern",
            )
        else:
            yield DiagnosticIssue(
                message="Missing ';' or unsupported modern syntax",
                span=_span_for_line(source, idx, max(1, len(line)), max(2, len(line) + 1)),
                source="modern",
            )

    if brace_balance != 0:
        yield DiagnosticIssue(
            message="Unbalanced braces in modern syntax",
            span=_span_for_line(source, len(lines), 1, 2),
            source="modern",
        )

    if paren_balance != 0:
        yield DiagnosticIssue(
            message="Unbalanced parentheses in modern syntax",
            span=_span_for_line(source, len(lines), 1, 2),
            source="modern",
        )


_BLOCK_STARTERS = {
    "IF": "END IF",
    "REPEAT": "END REPEAT",
    "DEFINE": "END DEFINE",
    "MATCH": "END MATCH",
}


def check_hybrid(source: str, english_parser: Optional[NullLangParser] = None) -> Iterable[DiagnosticIssue]:
    english_parser = english_parser or NullLangParser()
    lines = source.splitlines() or [""]
    idx = 0

    def is_modern_line(line: str) -> bool:
        return bool(SyntaxAdvisor._modern_markers.search(line)) and not bool(
            SyntaxAdvisor._english_markers.search(line)
        )

    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx]
        stripped = line.strip()

        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("//")
            or stripped.lower().startswith("@syntax")
        ):
            idx += 1
            continue

        upper = stripped.split(maxsplit=1)[0].upper()
        if upper in _BLOCK_STARTERS:
            end_marker = _BLOCK_STARTERS[upper]
            block_lines = [line]
            idx += 1
            while idx < len(lines):
                block_lines.append(lines[idx])
                if lines[idx].strip().upper().startswith(end_marker):
                    idx += 1
                    break
                idx += 1
            block_source = "\n".join(block_lines)
            for issue in check_english(block_source, english_parser):
                yield issue
            continue

        if is_modern_line(line):
            yield from check_modern(line)
        else:
            try:
                english_parser.parse_statement(stripped)
            except (SyntaxError, LexerError) as e:
                yield DiagnosticIssue(message=e.message, span=e.span, source="hybrid")
            except Exception as e:  # pragma: no cover
                yield DiagnosticIssue(
                    message=str(e),
                    span=_span_for_line(source, line_no, 1, max(2, len(line) + 1)),
                    source="hybrid",
                )

        idx += 1
