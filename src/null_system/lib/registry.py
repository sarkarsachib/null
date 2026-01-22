from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..errors import NullArityError, NullLibNotFoundError
from ..runtime import NullCallContext
from ..types import NullValue
from . import array_ops, io_ops, math_ops, object_ops, text_ops, nlp_ops, ml_ops, option_ops, result_ops


LibImpl = Callable[[NullCallContext, list[NullValue]], NullValue]


@dataclass(frozen=True)
class LibFunction:
    path: str
    arity: int
    impl: LibImpl


class LibraryRegistry:
    def __init__(self, functions: dict[str, LibFunction]) -> None:
        self._functions = dict(functions)

    def available(self) -> list[str]:
        return sorted(self._functions.keys())

    def require(self, path: str, *, where: str = "runtime") -> None:
        if path in self._functions:
            return

        if "." not in path:
            raise NullLibNotFoundError(
                f"Invalid library path '{path}'. Expected <lib>.<FUNC>",
                code="NULL_LIB_NOT_FOUND",
                where=where,
                path=path,
            )

        lib, fn = path.split(".", 1)
        known_libs = sorted({p.split(".", 1)[0] for p in self._functions})
        known_fns = sorted(
            p.split(".", 1)[1] for p in self._functions if p.startswith(f"{lib}.")
        )

        if lib not in known_libs:
            raise NullLibNotFoundError(
                f"Unknown library '{lib}'. Known libraries: {', '.join(known_libs)}",
                code="NULL_LIB_NOT_FOUND",
                where=where,
                lib=lib,
                fn=fn,
                known_libs=known_libs,
            )

        raise NullLibNotFoundError(
            f"Unknown function '{fn}' in library '{lib}'. Known functions: {', '.join(known_fns)}",
            code="NULL_LIB_NOT_FOUND",
            where=where,
            lib=lib,
            fn=fn,
            known_functions=known_fns,
        )

    def resolve(self, path: str) -> LibFunction:
        self.require(path)
        return self._functions[path]

    def call(self, path: str, ctx: NullCallContext, args: list[NullValue]) -> NullValue:
        fn = self.resolve(path)
        if len(args) != fn.arity:
            raise NullArityError(
                f"{path} expects {fn.arity} args, got {len(args)}",
                code="NULL_ARITY_ERROR",
                path=path,
                expected=fn.arity,
                actual=len(args),
            )
        return fn.impl(ctx, args)


def _wrap(fn: Callable[..., NullValue]) -> LibImpl:
    def _impl(ctx: NullCallContext, args: list[NullValue]) -> NullValue:
        return fn(ctx, *args)

    return _impl


def default_registry() -> LibraryRegistry:
    fns: dict[str, LibFunction] = {
        "math.ADD": LibFunction("math.ADD", 2, _wrap(math_ops.ADD)),
        "math.SUB": LibFunction("math.SUB", 2, _wrap(math_ops.SUB)),
        "math.MUL": LibFunction("math.MUL", 2, _wrap(math_ops.MUL)),
        "math.DIV": LibFunction("math.DIV", 2, _wrap(math_ops.DIV)),
        "math.ABS": LibFunction("math.ABS", 1, _wrap(math_ops.ABS)),
        "math.MIN": LibFunction("math.MIN", 2, _wrap(math_ops.MIN)),
        "math.MAX": LibFunction("math.MAX", 2, _wrap(math_ops.MAX)),
        "math.SQRT": LibFunction("math.SQRT", 1, _wrap(math_ops.SQRT)),
        "math.POW": LibFunction("math.POW", 2, _wrap(math_ops.POW)),
        "math.SIN": LibFunction("math.SIN", 1, _wrap(math_ops.SIN)),
        "math.COS": LibFunction("math.COS", 1, _wrap(math_ops.COS)),
        "math.FLOOR": LibFunction("math.FLOOR", 1, _wrap(math_ops.FLOOR)),
        "math.CEIL": LibFunction("math.CEIL", 1, _wrap(math_ops.CEIL)),
        "math.ROUND": LibFunction("math.ROUND", 1, _wrap(math_ops.ROUND)),
        "math.GT": LibFunction("math.GT", 2, _wrap(math_ops.GT)),
        "math.LT": LibFunction("math.LT", 2, _wrap(math_ops.LT)),
        "math.GTE": LibFunction("math.GTE", 2, _wrap(math_ops.GTE)),
        "math.LTE": LibFunction("math.LTE", 2, _wrap(math_ops.LTE)),
        "math.EQ": LibFunction("math.EQ", 2, _wrap(math_ops.EQ)),
        "math.NEQ": LibFunction("math.NEQ", 2, _wrap(math_ops.NEQ)),
        "text.CONCAT": LibFunction("text.CONCAT", 2, _wrap(text_ops.CONCAT)),
        "text.SUBSTR": LibFunction("text.SUBSTR", 3, _wrap(text_ops.SUBSTR)),
        "text.UPPERCASE": LibFunction("text.UPPERCASE", 1, _wrap(text_ops.UPPERCASE)),
        "text.LOWERCASE": LibFunction("text.LOWERCASE", 1, _wrap(text_ops.LOWERCASE)),
        "text.TRIM": LibFunction("text.TRIM", 1, _wrap(text_ops.TRIM)),
        "text.LENGTH": LibFunction("text.LENGTH", 1, _wrap(text_ops.LENGTH)),
        "text.CONTAINS": LibFunction("text.CONTAINS", 2, _wrap(text_ops.CONTAINS)),
        "text.STARTS_WITH": LibFunction("text.STARTS_WITH", 2, _wrap(text_ops.STARTS_WITH)),
        "text.ENDS_WITH": LibFunction("text.ENDS_WITH", 2, _wrap(text_ops.ENDS_WITH)),
        "text.SPLIT": LibFunction("text.SPLIT", 2, _wrap(text_ops.SPLIT)),
        "text.JOIN": LibFunction("text.JOIN", 2, _wrap(text_ops.JOIN)),
        "text.REPLACE": LibFunction("text.REPLACE", 3, _wrap(text_ops.REPLACE)),
        "text.REPEAT": LibFunction("text.REPEAT", 2, _wrap(text_ops.REPEAT)),
        "text.SLICE": LibFunction("text.SLICE", 3, _wrap(text_ops.SLICE)),
        "text.GET_CHAR": LibFunction("text.GET_CHAR", 2, _wrap(text_ops.GET_CHAR)),
        "array.PUSH": LibFunction("array.PUSH", 2, _wrap(array_ops.PUSH)),
        "array.POP": LibFunction("array.POP", 1, _wrap(array_ops.POP)),
        "array.LENGTH": LibFunction("array.LENGTH", 1, _wrap(array_ops.LENGTH)),
        "array.SORT": LibFunction("array.SORT", 1, _wrap(array_ops.SORT)),
        "array.REVERSE": LibFunction("array.REVERSE", 1, _wrap(array_ops.REVERSE)),
        "array.MAP": LibFunction("array.MAP", 3, _wrap(array_ops.MAP)),
        "array.FILTER": LibFunction("array.FILTER", 3, _wrap(array_ops.FILTER)),
        "array.REDUCE": LibFunction("array.REDUCE", 3, _wrap(array_ops.REDUCE)),
        "array.FOR_EACH": LibFunction("array.FOR_EACH", 3, _wrap(array_ops.FOR_EACH)),
        "array.SLICE": LibFunction("array.SLICE", 3, _wrap(array_ops.SLICE)),
        "object.READ": LibFunction("object.READ", 2, _wrap(object_ops.READ)),
        "object.WRITE": LibFunction("object.WRITE", 3, _wrap(object_ops.WRITE)),
        "io.SHOW": LibFunction("io.SHOW", 1, _wrap(io_ops.SHOW)),
        "io.READ": LibFunction("io.READ", 0, _wrap(io_ops.READ)),
        "nlp.TOKENIZE": LibFunction("nlp.TOKENIZE", 1, _wrap(nlp_ops.TOKENIZE)),
        "nlp.INTENT": LibFunction("nlp.INTENT", 1, _wrap(nlp_ops.INTENT)),
        "nlp.ENTITIES": LibFunction("nlp.ENTITIES", 1, _wrap(nlp_ops.ENTITIES)),
        "nlp.TRANSLATE": LibFunction("nlp.TRANSLATE", 2, _wrap(nlp_ops.TRANSLATE)),
        "nlp.CODEGEN": LibFunction("nlp.CODEGEN", 2, _wrap(nlp_ops.CODEGEN)),
        "ml.LOAD_MODEL": LibFunction("ml.LOAD_MODEL", 1, _wrap(ml_ops.LOAD_MODEL)),
        "ml.INFER": LibFunction("ml.INFER", 2, _wrap(ml_ops.INFER)),
        "ml.EMBED": LibFunction("ml.EMBED", 2, _wrap(ml_ops.EMBED)),
        "ml.ATTEND": LibFunction("ml.ATTEND", 3, _wrap(ml_ops.ATTEND)),
        "ml.TUNE": LibFunction("ml.TUNE", 2, _wrap(ml_ops.TUNE)),
        "option.SOME": LibFunction("option.SOME", 1, _wrap(option_ops.SOME)),
        "option.NONE": LibFunction("option.NONE", 0, _wrap(option_ops.NONE)),
        "option.IS_SOME": LibFunction("option.IS_SOME", 1, _wrap(option_ops.IS_SOME)),
        "option.IS_NONE": LibFunction("option.IS_NONE", 1, _wrap(option_ops.IS_NONE)),
        "option.UNWRAP": LibFunction("option.UNWRAP", 1, _wrap(option_ops.UNWRAP)),
        "result.OK": LibFunction("result.OK", 1, _wrap(result_ops.OK)),
        "result.ERR": LibFunction("result.ERR", 1, _wrap(result_ops.ERR)),
        "result.IS_OK": LibFunction("result.IS_OK", 1, _wrap(result_ops.IS_OK)),
        "result.IS_ERR": LibFunction("result.IS_ERR", 1, _wrap(result_ops.IS_ERR)),
        "result.UNWRAP": LibFunction("result.UNWRAP", 1, _wrap(result_ops.UNWRAP)),
        "result.UNWRAP_ERR": LibFunction("result.UNWRAP_ERR", 1, _wrap(result_ops.UNWRAP_ERR)),
    }
    return LibraryRegistry(fns)
