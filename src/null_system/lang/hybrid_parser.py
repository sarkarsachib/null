from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..ast.nodes import ASTNode, IfStatement, Program
from ..parser.lexer import Lexer
from ..parser.parser import ParseError, Parser
from .advisor import (
    DiagnosticLevel,
    SyntaxAdvisor,
    SyntaxConfig,
    SyntaxDiagnostic,
    SyntaxMode,
    SyntaxSegment,
)
from .ast_nodes import SourceSpan


@dataclass(frozen=True)
class HybridParseResult:
    ast: Program
    segments: list[SyntaxSegment]
    diagnostics: list[SyntaxDiagnostic]
    effective_mode: SyntaxMode
    normalized_source: str
    declared_mode: Optional[SyntaxMode] = None


class HybridParser:
    _let_re = re.compile(
        r"^\s*let\s+(?:mut\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<expr>.+?)\s*;\s*$",
        re.IGNORECASE,
    )
    _print_re = re.compile(r"^\s*print\s*\(\s*(?P<expr>.*?)\s*\)\s*;\s*$", re.IGNORECASE)

    _modern_markers = re.compile(r"\b(let|fn|match|return|print)\b|\{|\}|;", re.IGNORECASE)
    _english_markers = re.compile(r"\b(SET|SHOW|ADD|SUBTRACT|MULTIPLY|DIVIDE|IF|THEN|ELSE|PRINT)\b", re.IGNORECASE)
    _directive_re = re.compile(r"^\s*@syntax\s+(english|modern|hybrid|auto)\s*$", re.IGNORECASE)

    def __init__(self) -> None:
        self.advisor = SyntaxAdvisor()

    def parse(self, source: str, *, config: Optional[SyntaxConfig] = None) -> HybridParseResult:
        config = config or SyntaxConfig()

        declared_mode = self.advisor.extract_declared_mode(source)
        segments, normalized_source, translation_diagnostics = self._segment_and_normalize(source)

        effective_mode, advisor_diagnostics = self.advisor.advise(
            segments=segments,
            config=config,
            declared_mode=declared_mode,
        )

        diagnostics = translation_diagnostics + advisor_diagnostics
        if any(d.level == DiagnosticLevel.error for d in diagnostics):
            message = "\n".join(d.message for d in diagnostics if d.level == DiagnosticLevel.error)
            raise ParseError(message)

        lexer = Lexer(normalized_source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        self._attach_segments(ast, segments)

        return HybridParseResult(
            ast=ast,
            segments=segments,
            diagnostics=diagnostics,
            effective_mode=effective_mode,
            normalized_source=normalized_source,
            declared_mode=declared_mode,
        )

    def check(self, source: str, *, config: Optional[SyntaxConfig] = None) -> tuple[SyntaxMode, list[SyntaxDiagnostic]]:
        config = config or SyntaxConfig()
        declared_mode = self.advisor.extract_declared_mode(source)
        segments, _normalized, translation_diagnostics = self._segment_and_normalize(source)
        effective_mode, advisor_diagnostics = self.advisor.advise(
            segments=segments,
            config=config,
            declared_mode=declared_mode,
        )
        return effective_mode, translation_diagnostics + advisor_diagnostics

    def _segment_and_normalize(self, source: str) -> tuple[list[SyntaxSegment], str, list[SyntaxDiagnostic]]:
        lines = source.splitlines()
        segments: list[SyntaxSegment] = []
        normalized_lines: list[str] = []
        diagnostics: list[SyntaxDiagnostic] = []

        brace_balance = 0

        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")
            stripped = line.strip()

            directive_match = self._directive_re.match(line)
            if directive_match:
                normalized_lines.append("")
                continue

            if stripped.startswith("//"):
                normalized_lines.append("# " + stripped[2:].lstrip())
                continue

            if not stripped or stripped.startswith("#"):
                normalized_lines.append(line)
                continue

            is_modern = False
            if self._let_re.match(line) or self._print_re.match(line):
                is_modern = True
            elif brace_balance > 0:
                is_modern = True
            elif self._modern_markers.search(line) and re.search(r"[{};]", line):
                is_modern = True

            brace_balance += line.count("{") - line.count("}")

            mode = SyntaxMode.modern if is_modern else SyntaxMode.english
            span = SourceSpan(idx, 1, idx, max(1, len(line) + 1), line)
            segments.append(SyntaxSegment(mode=mode, span=span, text=line))

            if mode == SyntaxMode.modern:
                normalized, line_diags = self._normalize_modern_line(line, span)
                diagnostics.extend(line_diags)
                normalized_lines.append(normalized)
            else:
                normalized_lines.append(line)

        if brace_balance != 0:
            diagnostics.append(
                SyntaxDiagnostic(
                    level=DiagnosticLevel.error,
                    code="E_UNBALANCED_BRACES",
                    message="Unbalanced braces in modern syntax.",
                    span=None,
                )
            )

        normalized_source = "\n".join(normalized_lines)
        return segments, normalized_source, diagnostics

    def _normalize_modern_line(self, line: str, span: SourceSpan) -> tuple[str, list[SyntaxDiagnostic]]:
        m = self._let_re.match(line)
        if m:
            name = m.group("name")
            expr = m.group("expr").strip()
            expr_diag = self._validate_modern_expr(expr, span)
            return f"set {name} to {expr}", expr_diag

        m = self._print_re.match(line)
        if m:
            expr = m.group("expr").strip()
            expr_diag = self._validate_modern_expr(expr, span)
            return f"print {expr}", expr_diag

        return (
            "# [hybrid] unsupported modern syntax",
            [
                SyntaxDiagnostic(
                    level=DiagnosticLevel.error,
                    code="E_UNSUPPORTED_MODERN",
                    message="Unsupported modern syntax statement.",
                    span=span,
                )
            ],
        )

    def _validate_modern_expr(self, expr: str, span: SourceSpan) -> list[SyntaxDiagnostic]:
        if re.search(r"[+\-*/]", expr):
            return [
                SyntaxDiagnostic(
                    level=DiagnosticLevel.error,
                    code="E_UNSUPPORTED_MODERN_EXPR",
                    message=(
                        "Unsupported modern expression. Use English operators (ADD/SUBTRACT/MULTIPLY/DIVIDE) or simplify the expression."
                    ),
                    span=span,
                )
            ]
        if expr.startswith("(") or expr.endswith(")"):
            return [
                SyntaxDiagnostic(
                    level=DiagnosticLevel.error,
                    code="E_UNSUPPORTED_MODERN_EXPR",
                    message=(
                        "Unsupported modern expression. Parenthesized expressions are not supported in the hybrid compiler yet."
                    ),
                    span=span,
                )
            ]
        return []

    def _attach_segments(self, program: Program, segments: list[SyntaxSegment]) -> None:
        segment_by_line: dict[int, SyntaxSegment] = {}
        for seg in segments:
            for line in range(seg.span.start_line, seg.span.end_line + 1):
                segment_by_line[line] = seg

        def attach(node: ASTNode) -> None:
            seg = segment_by_line.get(getattr(node, "line", 0))
            if seg is not None:
                setattr(node, "syntax_segment", seg)

            if isinstance(node, Program):
                for stmt in node.statements:
                    attach(stmt)
            elif isinstance(node, IfStatement):
                if node.condition:
                    attach(node.condition)
                for stmt in node.then_branch:
                    attach(stmt)
                if node.else_branch:
                    for stmt in node.else_branch:
                        attach(stmt)

        attach(program)
