from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from pygls.server import LanguageServer

try:  # pygls>=1.0
    from lsprotocol.types import (
        CodeAction,
        CodeActionKind,
        CodeActionParams,
        CompletionItem,
        CompletionItemKind,
        CompletionList,
        CompletionOptions,
        CompletionParams,
        Diagnostic,
        DiagnosticSeverity,
        DidChangeTextDocumentParams,
        DidOpenTextDocumentParams,
        Hover,
        HoverParams,
        InitializeParams,
        InitializeResult,
        MarkupContent,
        MarkupKind,
        Position,
        Range,
        ServerCapabilities,
        TextDocumentSyncKind,
        TextDocumentSyncOptions,
        TextEdit,
        WorkspaceEdit,
    )
except Exception:  # pragma: no cover
    from pygls.lsp.types import (  # type: ignore
        CodeAction,
        CodeActionKind,
        CodeActionParams,
        CompletionItem,
        CompletionItemKind,
        CompletionList,
        CompletionOptions,
        CompletionParams,
        Diagnostic,
        DiagnosticSeverity,
        DidChangeTextDocumentParams,
        DidOpenTextDocumentParams,
        Hover,
        HoverParams,
        InitializeParams,
        InitializeResult,
        MarkupContent,
        MarkupKind,
        Position,
        Range,
        ServerCapabilities,
        TextDocumentSyncKind,
        TextDocumentSyncOptions,
        TextEdit,
        WorkspaceEdit,
    )

from ..lang.syntax_router import HybridParser, SyntaxMode
from ..lang.transpiler import to_english, to_modern

INITIALIZE = "initialize"
TEXT_DOCUMENT_DID_OPEN = "textDocument/didOpen"
TEXT_DOCUMENT_DID_CHANGE = "textDocument/didChange"
TEXT_DOCUMENT_COMPLETION = "textDocument/completion"
TEXT_DOCUMENT_HOVER = "textDocument/hover"
TEXT_DOCUMENT_CODE_ACTION = "textDocument/codeAction"


@dataclass
class DocumentState:
    uri: str
    text: str
    mode: SyntaxMode


class NullLspServer(LanguageServer):
    def __init__(
        self,
        default_mode: SyntaxMode = SyntaxMode.auto,
        hybrid_detection: bool = True,
    ) -> None:
        super().__init__("null-lsp", "0.1.0")
        self.default_mode = default_mode
        self.hybrid_detection = hybrid_detection
        self._parser = HybridParser()
        self._documents: dict[str, DocumentState] = {}

    def resolve_mode_for_document(self, text: str) -> SyntaxMode:
        if self.default_mode != SyntaxMode.auto:
            return self.default_mode
        if not self.hybrid_detection:
            return SyntaxMode.english
        mode, _ = self._parser.check(text, SyntaxMode.auto)
        return mode

    def analyze_and_publish(self, uri: str) -> None:
        doc = self._documents.get(uri)
        if not doc:
            return

        mode, issues = self._parser.check(doc.text, doc.mode)
        doc.mode = mode

        diagnostics: list[Diagnostic] = []
        for issue in issues:
            span = issue.span
            if span is None:
                rng = Range(start=Position(line=0, character=0), end=Position(line=0, character=1))
            else:
                rng = Range(
                    start=Position(line=max(0, span.start_line - 1), character=max(0, span.start_col - 1)),
                    end=Position(line=max(0, span.end_line - 1), character=max(0, span.end_col - 1)),
                )

            diagnostics.append(
                Diagnostic(
                    range=rng,
                    message=issue.message,
                    severity=DiagnosticSeverity.Error,
                    source=f"null/{doc.mode.value}",
                )
            )

        self.publish_diagnostics(uri, diagnostics)


def _range_to_offsets(text: str, rng: Range) -> tuple[int, int]:
    lines = text.splitlines(keepends=True)

    def to_offset(pos: Position) -> int:
        line = max(0, min(pos.line, len(lines)))
        if line >= len(lines):
            return len(text)
        base = sum(len(l) for l in lines[:line])
        return base + max(0, min(pos.character, len(lines[line])))

    start = to_offset(rng.start)
    end = to_offset(rng.end)
    if end < start:
        start, end = end, start
    return start, end


def _whole_document_range(text: str) -> Range:
    lines = text.splitlines() or [""]
    end_line = len(lines) - 1
    end_char = len(lines[-1])
    return Range(start=Position(line=0, character=0), end=Position(line=end_line, character=end_char))


def _keyword_sets(mode: SyntaxMode) -> list[str]:
    english = [
        "SET",
        "SHOW",
        "ADD",
        "IF",
        "THEN",
        "ELSE",
        "END IF",
        "REPEAT",
        "END REPEAT",
        "DEFINE",
        "END DEFINE",
        "CALL",
        "RETURN",
        "TRUE",
        "FALSE",
    ]

    modern = [
        "let",
        "mut",
        "fn",
        "if",
        "else",
        "for",
        "match",
        "return",
        "true",
        "false",
        "print",
    ]

    if mode == SyntaxMode.english:
        return english
    if mode == SyntaxMode.modern:
        return modern
    return english + modern


def _hover_markdown(word: str) -> Optional[str]:
    mapping = {
        "SET": ("SET x TO 5", "let x = 5;"),
        "SHOW": ("SHOW x", "print(x);"),
        "ADD": ("ADD 1 AND 2", "1 + 2"),
        "let": ("SET x TO 5", "let x = 5;"),
        "fn": (
            "DEFINE greet WITH name\n    SHOW name\nEND DEFINE",
            "fn greet(name) {\n    print(name);\n}",
        ),
        "print": ("SHOW x", "print(x);"),
        "IF": (
            "IF x IS 1 THEN\n    SHOW \"yes\"\nEND IF",
            "if x == 1 {\n    print(\"yes\");\n}",
        ),
        "if": (
            "IF x IS 1 THEN\n    SHOW \"yes\"\nEND IF",
            "if x == 1 {\n    print(\"yes\");\n}",
        ),
    }

    key = word
    if key.upper() in mapping:
        key = key.upper()
    if key not in mapping:
        return None

    english, modern = mapping[key]
    return (
        f"**English**\n```null\n{english}\n```\n\n"
        f"**Modern**\n```null\n{modern}\n```"
    )


def _word_at_position(text: str, pos: Position) -> str:
    lines = text.splitlines()
    if pos.line >= len(lines):
        return ""
    line = lines[pos.line]
    if pos.character > len(line):
        return ""

    left = pos.character
    right = pos.character
    while left > 0 and (line[left - 1].isalnum() or line[left - 1] in "_-"):
        left -= 1
    while right < len(line) and (line[right].isalnum() or line[right] in "_-"):
        right += 1
    return line[left:right]


def initialize(ls: NullLspServer, params: InitializeParams) -> InitializeResult:
    init_opts: dict[str, Any] = {}
    if params.initialization_options is not None:
        try:
            init_opts = dict(params.initialization_options)
        except Exception:
            try:
                init_opts = json.loads(params.initialization_options)
            except Exception:  # pragma: no cover
                init_opts = {}

    syntax_raw = str(init_opts.get("syntax", SyntaxMode.auto.value))
    hybrid_detection = bool(init_opts.get("hybrid_detection", True))

    try:
        ls.default_mode = SyntaxMode(syntax_raw)
    except ValueError:
        ls.default_mode = SyntaxMode.auto
    ls.hybrid_detection = hybrid_detection

    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncOptions(
                open_close=True,
                change=TextDocumentSyncKind.Incremental,
            ),
            completion_provider=CompletionOptions(
                trigger_characters=[" ", "."],
            ),
            hover_provider=True,
            code_action_provider=True,
        )
    )


def did_open(ls: NullLspServer, params: DidOpenTextDocumentParams) -> None:
    uri = params.text_document.uri
    text = params.text_document.text
    mode = ls.resolve_mode_for_document(text)
    ls._documents[uri] = DocumentState(uri=uri, text=text, mode=mode)
    ls.analyze_and_publish(uri)


def did_change(ls: NullLspServer, params: DidChangeTextDocumentParams) -> None:
    uri = params.text_document.uri
    doc = ls._documents.get(uri)
    if not doc:
        return

    for change in params.content_changes:
        rng = getattr(change, "range", None)
        if rng is not None:
            start, end = _range_to_offsets(doc.text, rng)
            doc.text = doc.text[:start] + change.text + doc.text[end:]
        else:
            doc.text = getattr(change, "text", "")

    if ls.default_mode == SyntaxMode.auto and ls.hybrid_detection:
        doc.mode = ls.resolve_mode_for_document(doc.text)

    ls.analyze_and_publish(uri)


def completion(ls: NullLspServer, params: CompletionParams) -> CompletionList:
    uri = params.text_document.uri
    doc = ls._documents.get(uri)
    mode = doc.mode if doc else ls.default_mode

    items = [
        CompletionItem(label=kw, kind=CompletionItemKind.Keyword, insert_text=kw)
        for kw in _keyword_sets(mode)
    ]
    return CompletionList(is_incomplete=False, items=items)


def hover(ls: NullLspServer, params: HoverParams) -> Optional[Hover]:
    uri = params.text_document.uri
    doc = ls._documents.get(uri)
    if not doc:
        return None

    word = _word_at_position(doc.text, params.position)
    if not word:
        return None

    md = _hover_markdown(word)
    if not md:
        return None

    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=md))


def code_action(ls: NullLspServer, params: CodeActionParams) -> list[CodeAction]:
    uri = params.text_document.uri
    doc = ls._documents.get(uri)
    if not doc:
        return []

    rng = params.range
    if rng.start == rng.end:
        rng = _whole_document_range(doc.text)

    start, end = _range_to_offsets(doc.text, rng)
    selected = doc.text[start:end]

    actions: list[CodeAction] = []

    if doc.mode in {SyntaxMode.modern, SyntaxMode.hybrid}:
        new_text = to_english(selected)
        actions.append(
            CodeAction(
                title="Convert to English",
                kind=CodeActionKind.RefactorRewrite,
                edit=WorkspaceEdit(changes={uri: [TextEdit(range=rng, new_text=new_text)]}),
            )
        )

    if doc.mode in {SyntaxMode.english, SyntaxMode.hybrid}:
        new_text = to_modern(selected)
        actions.append(
            CodeAction(
                title="Convert to Modern",
                kind=CodeActionKind.RefactorRewrite,
                edit=WorkspaceEdit(changes={uri: [TextEdit(range=rng, new_text=new_text)]}),
            )
        )

    return actions


def create_server(
    *,
    default_mode: SyntaxMode = SyntaxMode.auto,
    hybrid_detection: bool = True,
) -> NullLspServer:
    ls = NullLspServer(default_mode=default_mode, hybrid_detection=hybrid_detection)
    ls.feature(INITIALIZE)(initialize)
    ls.feature(TEXT_DOCUMENT_DID_OPEN)(did_open)
    ls.feature(TEXT_DOCUMENT_DID_CHANGE)(did_change)
    ls.feature(TEXT_DOCUMENT_COMPLETION)(completion)
    ls.feature(TEXT_DOCUMENT_HOVER)(hover)
    ls.feature(TEXT_DOCUMENT_CODE_ACTION)(code_action)
    return ls


def run_lsp_server(
    *,
    syntax: str = SyntaxMode.auto.value,
    port: int = 2087,
    stdio: bool = True,
    host: str = "127.0.0.1",
) -> None:
    try:
        default_mode = SyntaxMode(syntax)
    except ValueError:
        default_mode = SyntaxMode.auto

    ls = create_server(default_mode=default_mode, hybrid_detection=True)

    if stdio:
        ls.start_io()
    else:
        ls.start_tcp(host, port)
