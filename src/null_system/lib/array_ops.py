from __future__ import annotations

from typing import Callable
from ..errors import NullRuntimeError
from ..runtime import NullCallContext, NullIO
from ..types import NullArray, NullBoolean, NullNumber, NullValue


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


def LENGTH(ctx: NullCallContext, array: NullValue) -> NullNumber:
    arr = array.as_array()
    return NullNumber(len(arr.items))


def SORT(ctx: NullCallContext, array: NullValue) -> NullArray:
    arr = array.as_array()
    def sort_key(item: NullValue):
        if isinstance(item, NullNumber):
            return item.value
        return str(item.display())
    sorted_items = sorted(arr.items, key=sort_key)
    return NullArray(sorted_items)


def REVERSE(ctx: NullCallContext, array: NullValue) -> NullArray:
    arr = array.as_array()
    reversed_items = list(reversed(arr.items))
    return NullArray(reversed_items)


def FILTER(ctx: NullCallContext, array: NullValue, fn_ref: NullValue, bound_arg: NullValue) -> NullArray:
    arr = array.as_array()
    fn = fn_ref.as_function_ref()

    lib_fn = ctx.registry.resolve(fn.lib_path)

    if lib_fn.arity != 2:
        raise NullRuntimeError(
            f"array.FILTER requires function of arity 2 (got {lib_fn.arity})",
            code="NULL_FILTER_ARITY",
            path=fn.lib_path,
            arity=lib_fn.arity,
        )

    filtered: list[NullValue] = []
    for item in arr.items:
        result = ctx.registry.call(fn.lib_path, ctx, [item, bound_arg])
        if isinstance(result, NullBoolean) and result.value:
            filtered.append(item)

    return NullArray(filtered)


def REDUCE(ctx: NullCallContext, array: NullValue, fn_ref: NullValue, initial: NullValue) -> NullValue:
    arr = array.as_array()
    fn = fn_ref.as_function_ref()

    lib_fn = ctx.registry.resolve(fn.lib_path)

    if lib_fn.arity != 2:
        raise NullRuntimeError(
            f"array.REDUCE requires function of arity 2 (got {lib_fn.arity})",
            code="NULL_REDUCE_ARITY",
            path=fn.lib_path,
            arity=lib_fn.arity,
        )

    accumulator = initial
    for item in arr.items:
        accumulator = ctx.registry.call(fn.lib_path, ctx, [accumulator, item])

    return accumulator


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


def FOR_EACH(ctx: NullCallContext, array: NullValue, fn_ref: NullValue, bound_arg: NullValue) -> NullValue:
    arr = array.as_array()
    fn = fn_ref.as_function_ref()

    lib_fn = ctx.registry.resolve(fn.lib_path)

    if lib_fn.arity != 2:
        raise NullRuntimeError(
            f"array.FOR_EACH requires function of arity 2 (got {lib_fn.arity})",
            code="NULL_FOREACH_ARITY",
            path=fn.lib_path,
            arity=lib_fn.arity,
        )

    for item in arr.items:
        ctx.registry.call(fn.lib_path, ctx, [item, bound_arg])

    from ..types import NULL
    return NULL


def SLICE(ctx: NullCallContext, array: NullValue, start: NullValue, length: NullValue) -> NullArray:
    arr = array.as_array()
    st = int(start.as_number())
    ln = int(length.as_number())
    if ln < 0:
        ln = 0
    sliced = arr.items[st:st+ln]
    return NullArray(sliced)
