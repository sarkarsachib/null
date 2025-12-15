from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class HealthState:
    started_at: float = field(default_factory=time.time)
    ready: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "ready": self.ready,
            "uptime_s": time.time() - self.started_at,
        }


def create_health_router(state: HealthState):
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/healthz")
    def healthz() -> Dict[str, Any]:
        return state.as_dict()

    @router.get("/readyz")
    def readyz() -> Dict[str, Any]:
        if not state.ready:
            return {"status": "not_ready"}
        return {"status": "ready"}

    return router
