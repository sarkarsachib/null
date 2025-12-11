from __future__ import annotations

from ..runtime import NullCallContext
from ..types import NULL, NullString, NullValue


def SHOW(ctx: NullCallContext, value: NullValue) -> NullValue:
    ctx.io.write(value.display())
    return NULL


def READ(ctx: NullCallContext) -> NullString:
    return NullString(ctx.io.read_line().rstrip("\n"))
