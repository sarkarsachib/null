import json
import os
import select
import threading
import time
from dataclasses import dataclass

import pytest

from src.null_system.lang.syntax_router import SyntaxMode
from src.null_system.lsp.server import create_server


@dataclass
class LspClient:
    read_fd: int
    write_fd: int
    buffer: bytes = b""

    def send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        os.write(self.write_fd, header + body)

    def read_message(self, timeout: float = 2.0) -> dict:
        deadline = time.time() + timeout

        def read_more() -> None:
            chunk = os.read(self.read_fd, 4096)
            if not chunk:
                raise RuntimeError("LSP stream closed")
            self.buffer += chunk

        while b"\r\n\r\n" not in self.buffer:
            remaining = max(0.0, deadline - time.time())
            if remaining == 0:
                raise TimeoutError("Timed out waiting for LSP header")
            r, _, _ = select.select([self.read_fd], [], [], remaining)
            if not r:
                continue
            read_more()

        header, rest = self.buffer.split(b"\r\n\r\n", 1)
        content_length = None
        for line in header.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1].strip())
                break
        if content_length is None:
            raise RuntimeError("Missing Content-Length header")

        while len(rest) < content_length:
            remaining = max(0.0, deadline - time.time())
            if remaining == 0:
                raise TimeoutError("Timed out waiting for LSP body")
            r, _, _ = select.select([self.read_fd], [], [], remaining)
            if not r:
                continue
            read_more()
            header, rest = self.buffer.split(b"\r\n\r\n", 1)

        body = rest[:content_length]
        self.buffer = rest[content_length:]
        return json.loads(body.decode("utf-8"))

    def wait_for_response(self, msg_id: int, timeout: float = 2.0) -> dict:
        deadline = time.time() + timeout
        while True:
            remaining = max(0.01, deadline - time.time())
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for response id={msg_id}")
            msg = self.read_message(timeout=remaining)
            if msg.get("id") == msg_id:
                return msg

    def wait_for_notification(self, method: str, timeout: float = 2.0) -> dict:
        deadline = time.time() + timeout
        while True:
            remaining = max(0.01, deadline - time.time())
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for notification {method}")
            msg = self.read_message(timeout=remaining)
            if msg.get("method") == method:
                return msg


def _start_server(mode: SyntaxMode):
    server = create_server(default_mode=mode, hybrid_detection=True)

    c2s_r, c2s_w = os.pipe()  # client writes, server reads
    s2c_r, s2c_w = os.pipe()  # server writes, client reads

    server_in = os.fdopen(c2s_r, "rb", buffering=0)
    server_out = os.fdopen(s2c_w, "wb", buffering=0)

    thread = threading.Thread(target=server.start_io, args=(server_in, server_out), daemon=True)
    thread.start()

    client = LspClient(read_fd=s2c_r, write_fd=c2s_w)
    return server, client, thread


def _shutdown(client: LspClient, thread: threading.Thread) -> None:
    client.send({"jsonrpc": "2.0", "id": 99, "method": "shutdown", "params": None})
    client.wait_for_response(99, timeout=3.0)
    client.send({"jsonrpc": "2.0", "method": "exit", "params": None})
    thread.join(timeout=3.0)


def _initialize(client: LspClient, syntax: str) -> None:
    client.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": None,
                "capabilities": {},
                "initializationOptions": {"syntax": syntax, "hybrid_detection": True},
            },
        }
    )
    client.wait_for_response(1)
    client.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})


@pytest.mark.integration
@pytest.mark.parametrize(
    "mode,source,expected_completion,expected_actions,expected_snippet",
    [
        (
            SyntaxMode.english,
            "SET x TO 5\nSHOW x\n",
            "SET",
            ["Convert to Modern"],
            "let x = 5;",
        ),
        (
            SyntaxMode.modern,
            "let x = 5;\nprint(x);\n",
            "let",
            ["Convert to English"],
            "SET x TO 5",
        ),
        (
            SyntaxMode.hybrid,
            "SET x TO 5\nlet y = 10;\nSHOW y\n",
            "SET",
            ["Convert to English", "Convert to Modern"],
            "let x = 5;",
        ),
    ],
)
def test_lsp_end_to_end_modes(mode, source, expected_completion, expected_actions, expected_snippet):
    _server, client, thread = _start_server(mode)

    try:
        _initialize(client, mode.value)

        uri = f"file:///tmp/{mode.value}.null"
        client.send(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "null",
                        "version": 1,
                        "text": source,
                    }
                },
            }
        )

        diag = client.wait_for_notification("textDocument/publishDiagnostics", timeout=3.0)
        assert diag["params"]["uri"] == uri
        assert diag["params"]["diagnostics"] == []

        client.send(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/completion",
                "params": {"textDocument": {"uri": uri}, "position": {"line": 0, "character": 0}},
            }
        )
        completion = client.wait_for_response(2)
        result = completion["result"]
        items = result["items"] if isinstance(result, dict) else result
        labels = {item["label"] for item in items}
        assert expected_completion in labels

        lines = source.splitlines()
        end_line = len(lines) - 1
        end_char = len(lines[-1]) if lines else 0

        client.send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "textDocument/codeAction",
                "params": {
                    "textDocument": {"uri": uri},
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": end_line, "character": end_char},
                    },
                    "context": {"diagnostics": []},
                },
            }
        )
        actions = client.wait_for_response(3)["result"]
        titles = [a["title"] for a in actions]
        for expected in expected_actions:
            assert expected in titles

        edits = [a["edit"]["changes"][uri][0]["newText"] for a in actions if a.get("edit")]
        assert any(expected_snippet in e for e in edits)

    finally:
        _shutdown(client, thread)
