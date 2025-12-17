from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from .ast_nodes import SourceSpan


class SyntaxMode(str, Enum):
    english = "english"
    modern = "modern"
    hybrid = "hybrid"
    auto = "auto"


class DiagnosticLevel(str, Enum):
    hint = "hint"
    warning = "warning"
    error = "error"


@dataclass(frozen=True)
class SyntaxDiagnostic:
    level: DiagnosticLevel
    message: str
    span: Optional[SourceSpan] = None
    code: str = ""
    source: str = "syntax_advisor"


@dataclass(frozen=True)
class SyntaxConfig:
    mode: SyntaxMode = SyntaxMode.auto
    allow_hybrid_mode: bool = False
    english_warnings: bool = True
    lint_level: DiagnosticLevel = DiagnosticLevel.warning


@dataclass(frozen=True)
class SyntaxSegment:
    mode: SyntaxMode
    span: SourceSpan
    text: str


class SyntaxAdvisor:
    _english_markers = re.compile(
        r"\b(SET|SHOW|ADD|SUBTRACT|MULTIPLY|DIVIDE|IF|THEN|ELSE|MATCH|CASE|WHEN|REPEAT|DEFINE|CALL|RETURN|END|PRINT)\b",
        re.IGNORECASE,
    )
    _modern_markers = re.compile(
        r"\b(let|fn|match|return|print|true|false)\b|\{|\}|;|::|=>",
        re.IGNORECASE,
    )

    _directive_re = re.compile(r"^\s*@syntax\s+(english|modern|hybrid|auto)\s*$", re.IGNORECASE)

    def detect_mode(self, source: str) -> SyntaxMode:
        has_english = bool(self._english_markers.search(source))
        has_modern = bool(self._modern_markers.search(source))
        if has_english and has_modern:
            return SyntaxMode.hybrid
        if has_modern:
            return SyntaxMode.modern
        return SyntaxMode.english

    def extract_declared_mode(self, source: str) -> Optional[SyntaxMode]:
        for line in source.splitlines():
            m = self._directive_re.match(line)
            if not m:
                continue
            try:
                return SyntaxMode(m.group(1).lower())
            except ValueError:
                return None
        return None

    def advise(
        self,
        *,
        segments: Iterable[SyntaxSegment],
        config: SyntaxConfig,
        declared_mode: Optional[SyntaxMode] = None,
    ) -> tuple[SyntaxMode, list[SyntaxDiagnostic]]:
        segs = list(segments)
        has_english = any(seg.mode == SyntaxMode.english for seg in segs)
        has_modern = any(seg.mode == SyntaxMode.modern for seg in segs)

        if declared_mode and declared_mode != SyntaxMode.auto:
            effective_mode = declared_mode
        elif config.mode != SyntaxMode.auto:
            effective_mode = config.mode
        else:
            effective_mode = self.detect_mode("\n".join(seg.text for seg in segs))

        allow_hybrid = config.allow_hybrid_mode or declared_mode == SyntaxMode.hybrid
        mixing = has_english and has_modern

        diagnostics: list[SyntaxDiagnostic] = []

        if mixing and not allow_hybrid:
            span = next((seg.span for seg in segs if seg.mode == SyntaxMode.modern), None)
            diagnostics.append(
                SyntaxDiagnostic(
                    level=DiagnosticLevel.error,
                    code="E_HYBRID_DISABLED",
                    message=(
                        "Hybrid syntax is disabled. Add '@syntax hybrid' or enable allow_hybrid_mode to mix English and modern code."
                    ),
                    span=span,
                )
            )

        if mixing and allow_hybrid and declared_mode != SyntaxMode.hybrid:
            diagnostics.append(
                SyntaxDiagnostic(
                    level=DiagnosticLevel.hint,
                    code="H_DECLARE_HYBRID",
                    message="Mixed English and modern syntax detected. Add '@syntax hybrid' to make this explicit.",
                    span=None,
                )
            )

        if effective_mode == SyntaxMode.english and has_modern:
            diagnostics.append(
                SyntaxDiagnostic(
                    level=config.lint_level,
                    code="W_MODERN_IN_ENGLISH",
                    message=(
                        "Modern syntax detected in an English-mode file. Rewrite to English or enable '@syntax hybrid'."
                    ),
                    span=next((seg.span for seg in segs if seg.mode == SyntaxMode.modern), None),
                )
            )

        if effective_mode == SyntaxMode.modern and has_english:
            diagnostics.append(
                SyntaxDiagnostic(
                    level=config.lint_level,
                    code="W_ENGLISH_IN_MODERN",
                    message=(
                        "English syntax detected in a modern-mode file. Rewrite to modern or enable '@syntax hybrid'."
                    ),
                    span=next((seg.span for seg in segs if seg.mode == SyntaxMode.english), None),
                )
            )

        if config.english_warnings and effective_mode in {SyntaxMode.modern, SyntaxMode.hybrid}:
            if any(seg.mode == SyntaxMode.english and re.search(r"\bSET\b", seg.text, re.IGNORECASE) for seg in segs):
                diagnostics.append(
                    SyntaxDiagnostic(
                        level=DiagnosticLevel.hint,
                        code="H_PREFER_LET",
                        message="In modern syntax, prefer 'let' over 'SET' for variable declarations.",
                    )
                )
            if any(seg.mode == SyntaxMode.english and re.search(r"\bSHOW\b", seg.text, re.IGNORECASE) for seg in segs):
                diagnostics.append(
                    SyntaxDiagnostic(
                        level=DiagnosticLevel.hint,
                        code="H_PREFER_PRINT",
                        message="In modern syntax, prefer 'print(expr);' over 'SHOW expr'.",
                    )
                )

        if effective_mode == SyntaxMode.english:
            if any(seg.mode == SyntaxMode.modern and re.search(r"\blet\b", seg.text) for seg in segs):
                diagnostics.append(
                    SyntaxDiagnostic(
                        level=DiagnosticLevel.hint,
                        code="H_PREFER_SET",
                        message="In English syntax, prefer 'SET x TO expr' over 'let x = expr;'.",
                    )
                )
            if any(seg.mode == SyntaxMode.modern and re.search(r"\bprint\s*\(", seg.text) for seg in segs):
                diagnostics.append(
                    SyntaxDiagnostic(
                        level=DiagnosticLevel.hint,
                        code="H_PREFER_SHOW",
                        message="In English syntax, prefer 'SHOW expr' over 'print(expr);'.",
                    )
                )

        return effective_mode, diagnostics
