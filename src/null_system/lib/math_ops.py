from __future__ import annotations

from ..errors import NullRuntimeError
from ..runtime import NullCallContext
from ..types import NullNumber, NullValue


def _num(v: NullValue) -> float:
    return v.as_number()


def ADD(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    return NullNumber(_num(a) + _num(b))


def SUB(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    return NullNumber(_num(a) - _num(b))


def MUL(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    return NullNumber(_num(a) * _num(b))


def DIV(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    denom = _num(b)
    if denom == 0:
        raise NullRuntimeError(
            "Division by zero",
            code="NULL_DIV_ZERO",
        )
    return NullNumber(_num(a) / denom)
