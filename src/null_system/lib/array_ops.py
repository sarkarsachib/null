from __future__ import annotations

from ..errors import NullRuntimeError
from ..runtime import NullCallContext
from ..types import NullArray, NullValue


def PUSH(ctx: NullCallContext, array: NullValue, value: NullValue) -> NullArray:
    arr = array.as_array()
    arr.items.append(value)
    return arr


def POP(ctx: NullCallContext, array: NullValue) -> NullValue:
    arr = array.as_array()
    if not arr.items:
        raise NullRuntimeError(
            "Cannot POP from empty array",
            code="NULL_EMPTY_ARRAY",
        )
    return arr.items.pop()


def MAP(ctx: NullCallContext, array: NullValue, fn_ref: NullValue, bound_arg: NullValue) -> NullArray:
    arr = array.as_array()
    fn = fn_ref.as_function_ref()

    lib_fn = ctx.registry.resolve(fn.lib_path)

    if lib_fn.arity < 1:
        raise NullRuntimeError(
            f"Cannot MAP with function of arity {lib_fn.arity}",
            code="NULL_MAP_ARITY",
            path=fn.lib_path,
            arity=lib_fn.arity,
        )
    if lib_fn.arity != 2:
        raise NullRuntimeError(
            f"array.MAP currently supports mapping a binary function over an array (got arity {lib_fn.arity})",
            code="NULL_MAP_ARITY",
            path=fn.lib_path,
            arity=lib_fn.arity,
        )

    out: list[NullValue] = []
    for item in arr.items:
        out.append(ctx.registry.call(fn.lib_path, ctx, [item, bound_arg]))
    return NullArray(out)
