from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from null_system.compiler import NullCompiler
from null_system.vm import NullDebuggerSession


def _load_session_from_env() -> dict[str, Any]:
    session_json = os.environ.get("NULL_VISUALIZER_SESSION_JSON")
    if session_json:
        return NullDebuggerSession.load_json(Path(session_json))

    source_path = os.environ.get("NULL_VISUALIZER_SOURCE")
    if source_path:
        source = Path(source_path).read_text()
        artifact = NullCompiler().compile(source)
        session = NullDebuggerSession(
            source=source,
            superbit_stream=artifact.superbit_stream,
            binary_frames=artifact.binary_frames,
            program_path=source_path,
        ).run()
        return {
            "timeline": session.timeline_json(),
            "frames": [session.frame_json(i) for i in range(session.steps)],
        }

    fallback = Path(__file__).resolve().parents[3] / "examples" / "visualizer" / "sample.session.json"
    if fallback.exists():
        return NullDebuggerSession.load_json(fallback)

    raise RuntimeError(
        "Visualizer backend requires NULL_VISUALIZER_SOURCE or NULL_VISUALIZER_SESSION_JSON"
    )


def create_app(*, session_payload: Optional[dict[str, Any]] = None) -> FastAPI:
    payload = session_payload or _load_session_from_env()

    timeline = payload["timeline"]
    frames = payload["frames"]

    app = FastAPI(title="Null Visualizer Backend", version="0.1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/timeline")
    def get_timeline() -> JSONResponse:
        return JSONResponse(timeline)

    @app.get("/state/{step}")
    def get_state(step: int) -> JSONResponse:
        if step < 0 or step >= len(frames):
            return JSONResponse({"error": "step_out_of_range"}, status_code=404)
        return JSONResponse(frames[step])

    @app.websocket("/ws")
    async def ws(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text(json.dumps({"type": "timeline", "payload": timeline}))

        while True:
            msg = await websocket.receive_text()
            try:
                cmd = json.loads(msg)
            except json.JSONDecodeError:
                continue

            if cmd.get("type") == "get" and isinstance(cmd.get("step"), int):
                step = int(cmd["step"])
                if 0 <= step < len(frames):
                    await websocket.send_text(
                        json.dumps({"type": "frame", "payload": frames[step]})
                    )
                continue

            if cmd.get("type") == "play":
                start = int(cmd.get("from", 0))
                delay_ms = int(cmd.get("delay_ms", 250))
                for step in range(start, len(frames)):
                    await websocket.send_text(
                        json.dumps({"type": "frame", "payload": frames[step]})
                    )
                    await asyncio.sleep(delay_ms / 1000)

    project_root = Path(__file__).resolve().parents[3]
    dist = project_root / "tools" / "visualizer" / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")

    return app


app = create_app()
