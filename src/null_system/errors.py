from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class NullError(Exception):
    code: str
    details: dict[str, Any]

    def __init__(self, message: str, *, code: str = "NULL_ERROR", **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class NullCompileError(NullError):
    pass


class NullParseError(NullCompileError):
    pass


class NullRuntimeError(NullError):
    pass


class NullTypeError(NullRuntimeError):
    pass


class NullArityError(NullRuntimeError):
    pass


class NullNameError(NullRuntimeError):
    pass


class NullLibNotFoundError(NullError):
    pass


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int = 1
