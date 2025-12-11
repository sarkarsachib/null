from __future__ import annotations

from ..runtime import NullCallContext
from ..types import NULL, NullValue


def READ(ctx: NullCallContext, obj: NullValue, key: NullValue) -> NullValue:
    o = obj.as_object()
    k = key.as_string()
    return o.items.get(k, NULL)


def WRITE(ctx: NullCallContext, obj: NullValue, key: NullValue, value: NullValue) -> NullValue:
    o = obj.as_object()
    k = key.as_string()
    o.items[k] = value
    return value
