from __future__ import annotations

from ..runtime import NullCallContext
from ..types import NullString, NullValue


def CONCAT(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullString:
    return NullString(a.as_string() + b.as_string())


def SUBSTR(ctx: NullCallContext, text: NullValue, start: NullValue, length: NullValue) -> NullString:
    s = text.as_string()
    st = int(start.as_number())
    ln = int(length.as_number())
    if ln < 0:
        ln = 0
    return NullString(s[st : st + ln])
