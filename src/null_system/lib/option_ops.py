from ..runtime import NullCallContext
from ..types import NullValue, NullOption, none_val, some_val


def SOME(ctx: NullCallContext, value: NullValue) -> NullOption:
    return some_val(value)


def NONE(ctx: NullCallContext) -> NullOption:
    return none_val()


def IS_SOME(ctx: NullCallContext, opt: NullValue) -> NullValue:
    from ..types import NullNumber
    opt_val = opt.as_union()
    return NullNumber(1.0 if opt_val.tag == "Some" else 0.0)


def IS_NONE(ctx: NullCallContext, opt: NullValue) -> NullValue:
    from ..types import NullNumber
    opt_val = opt.as_union()
    return NullNumber(1.0 if opt_val.tag == "None" else 0.0)


def UNWRAP(ctx: NullCallContext, opt: NullValue) -> NullValue:
    opt_val = opt.as_union()
    if opt_val.tag == "None":
        from ..errors import NullTypeError
        raise NullTypeError(
            "Called unwrap on None",
            code="NULL_UNWRAP_ERROR",
            actual="None",
        )
    return opt_val.value
