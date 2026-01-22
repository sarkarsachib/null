from __future__ import annotations

from ..runtime import NullCallContext
from ..types import NullBoolean, NullNumber, NullString, NullValue


def CONCAT(ctx: NullCallContext, a: NullValue, b: NullValue) -> NullString:
    return NullString(a.as_string() + b.as_string())


def SUBSTR(ctx: NullCallContext, text: NullValue, start: NullValue, length: NullValue) -> NullString:
    s = text.as_string()
    st = int(start.as_number())
    ln = int(length.as_number())
    if ln < 0:
        ln = 0
    return NullString(s[st : st + ln])


def UPPERCASE(ctx: NullCallContext, text: NullValue) -> NullString:
    return NullString(text.as_string().upper())


def LOWERCASE(ctx: NullCallContext, text: NullValue) -> NullString:
    return NullString(text.as_string().lower())


def TRIM(ctx: NullCallContext, text: NullValue) -> NullString:
    return NullString(text.as_string().strip())


def LENGTH(ctx: NullCallContext, text: NullValue) -> NullNumber:
    return NullNumber(len(text.as_string()))


def CONTAINS(ctx: NullCallContext, text: NullValue, substr: NullValue) -> NullBoolean:
    return NullBoolean(substr.as_string() in text.as_string())


def STARTS_WITH(ctx: NullCallContext, text: NullValue, prefix: NullValue) -> NullBoolean:
    return NullBoolean(text.as_string().startswith(prefix.as_string()))


def ENDS_WITH(ctx: NullCallContext, text: NullValue, suffix: NullValue) -> NullBoolean:
    return NullBoolean(text.as_string().endswith(suffix.as_string()))


def SPLIT(ctx: NullCallContext, text: NullValue, delimiter: NullValue):
    from ..types import NullArray
    parts = text.as_string().split(delimiter.as_string())
    return NullArray([NullString(part) for part in parts])


def JOIN(ctx: NullCallContext, array: NullValue, delimiter: NullValue) -> NullString:
    arr = array.as_array()
    parts = [item.as_string() if hasattr(item, 'as_string') else str(item.display())
              for item in arr.items]
    return NullString(delimiter.as_string().join(parts))


def REPLACE(ctx: NullCallContext, text: NullValue, old: NullValue, new: NullValue) -> NullString:
    return NullString(text.as_string().replace(old.as_string(), new.as_string()))


def REPEAT(ctx: NullCallContext, text: NullValue, count: NullValue) -> NullString:
    return NullString(text.as_string() * int(count.as_number()))


def SLICE(ctx: NullCallContext, text: NullValue, start: NullValue, length: NullValue) -> NullString:
    s = text.as_string()
    st = int(start.as_number())
    ln = int(length.as_number())
    if ln < 0:
        ln = 0
    return NullString(s[st:st+ln])


def GET_CHAR(ctx: NullCallContext, text: NullValue, index: NullValue) -> NullString:
    s = text.as_string()
    idx = int(index.as_number())
    if 0 <= idx < len(s):
        return NullString(s[idx])
    else:
        return NullString("")

