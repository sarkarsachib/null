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


def ABS(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(abs(_num(x)))


def MIN(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    import math
    return NullNumber(min(_num(a), _num(b)))


def MAX(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullNumber:
    import math
    return NullNumber(max(_num(a), _num(b)))


def SQRT(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    val = _num(x)
    if val < 0:
        raise NullRuntimeError(
            "Square root of negative number",
            code="NULL_NEGATIVE_SQRT",
        )
    return NullNumber(math.sqrt(val))


def POW(ctx: NullCallContext, base: NullValue, exp: NullValue) -> NullNumber:
    import math
    return NullNumber(_num(base) ** _num(exp))


def SIN(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(math.sin(_num(x)))


def COS(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(math.cos(_num(x)))


def FLOOR(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(math.floor(_num(x)))


def CEIL(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(math.ceil(_num(x)))


def ROUND(ctx: NullCallContext, x: NullValue) -> NullNumber:
    import math
    return NullNumber(round(_num(x)))


def GT(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) > _num(b))


def LT(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) < _num(b))


def GTE(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) >= _num(b))


def LTE(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) <= _num(b))


def EQ(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) == _num(b))


def NEQ(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullBoolean:
    from ..types import NullBoolean
    return NullBoolean(_num(a) != _num(b))
