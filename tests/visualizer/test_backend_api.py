from __future__ import annotations

from fastapi.testclient import TestClient

from null_system.compiler import NullCompiler
from null_system.vm import NullDebuggerSession
from tools.visualizer.backend.server import create_app


def _build_payload(source: str):
    artifact = NullCompiler().compile(source)
    session = NullDebuggerSession(
        source=source,
        superbit_stream=artifact.superbit_stream,
        binary_frames=artifact.binary_frames,
        program_path="<test>",
    ).run()
    return {
        "timeline": session.timeline_json(),
        "frames": [session.frame_json(i) for i in range(session.steps)],
    }


def test_timeline_json_schema():
    payload = _build_payload("set x to 1\nprint x\n")
    app = create_app(session_payload=payload)
    client = TestClient(app)

    res = client.get("/timeline")
    assert res.status_code == 200
    data = res.json()

    assert data["version"] == 1
    assert data["steps"] == len(payload["frames"])
    assert len(data["instructions"]) == data["steps"]
    assert "source" in data and "lines" in data["source"]
    assert data["source"]["lines"][0]["line"] == 1


def test_step_transitions_are_consistent():
    payload = _build_payload("set x to 1\nprint x\n")
    app = create_app(session_payload=payload)
    client = TestClient(app)

    f0 = client.get("/state/0").json()
    f1 = client.get("/state/1").json()
    f2 = client.get("/state/2").json()
    f3 = client.get("/state/3").json()

    assert f0["step"] == 0
    assert f1["step"] == 1

    assert f0["opcode"] == "LOAD_CONST"
    assert f0["stack"] == [1]
    assert f0["variables"] == {}

    assert f1["opcode"] == "STORE_VAR"
    assert f1["stack"] == []
    assert f1["variables"]["x"] == 1

    assert f2["opcode"] == "LOAD_VAR"
    assert f2["stack"] == [1]

    assert f3["opcode"] == "PRINT"
    assert f3["output"] == ["1"]

    missing = client.get("/state/999")
    assert missing.status_code == 404
