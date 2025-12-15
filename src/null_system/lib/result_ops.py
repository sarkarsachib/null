from ..runtime import NullCallContext
from ..types import NullValue, NullResult, ok_val, err_val


def OK(ctx: NullCallContext, value: NullValue) -> NullResult:
    return ok_val(value)


def ERR(ctx: NullCallContext, error: NullValue) -> NullResult:
    return err_val(error)


def IS_OK(ctx: NullCallContext, res: NullValue) -> NullValue:
    from ..types import NullNumber
    res_val = res.as_union()
    return NullNumber(1.0 if res_val.tag == "Ok" else 0.0)


def IS_ERR(ctx: NullCallContext, res: NullValue) -> NullValue:
    from ..types import NullNumber
    res_val = res.as_union()
    return NullNumber(1.0 if res_val.tag == "Err" else 0.0)


def UNWRAP(ctx: NullCallContext, res: NullValue) -> NullValue:
    res_val = res.as_union()
    if res_val.tag == "Err":
        from ..errors import NullTypeError
        raise NullTypeError(
            f"Called unwrap on Err: {res_val.value.display()}",
            code="NULL_UNWRAP_ERROR",
            actual="Err",
        )
    return res_val.value


def UNWRAP_ERR(ctx: NullCallContext, res: NullValue) -> NullValue:
    res_val = res.as_union()
    if res_val.tag == "Ok":
        from ..errors import NullTypeError
        raise NullTypeError(
            "Called unwrap_err on Ok",
            code="NULL_UNWRAP_ERROR",
            actual="Ok",
        )
    return res_val.value
