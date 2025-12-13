from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..errors import NullArityError, NullLibNotFoundError
from ..runtime import NullCallContext
from ..types import NullValue
from . import array_ops, io_ops, math_ops, object_ops, text_ops, nlp_ops


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
        "text.CONCAT": LibFunction("text.CONCAT", 2, _wrap(text_ops.CONCAT)),
        "text.SUBSTR": LibFunction("text.SUBSTR", 3, _wrap(text_ops.SUBSTR)),
        "array.PUSH": LibFunction("array.PUSH", 2, _wrap(array_ops.PUSH)),
        "array.POP": LibFunction("array.POP", 1, _wrap(array_ops.POP)),
        "array.MAP": LibFunction("array.MAP", 3, _wrap(array_ops.MAP)),
        "object.READ": LibFunction("object.READ", 2, _wrap(object_ops.READ)),
        "object.WRITE": LibFunction("object.WRITE", 3, _wrap(object_ops.WRITE)),
        "io.SHOW": LibFunction("io.SHOW", 1, _wrap(io_ops.SHOW)),
        "io.READ": LibFunction("io.READ", 0, _wrap(io_ops.READ)),
        "nlp.TOKENIZE": LibFunction("nlp.TOKENIZE", 1, _wrap(nlp_ops.TOKENIZE)),
        "nlp.INTENT": LibFunction("nlp.INTENT", 1, _wrap(nlp_ops.INTENT)),
        "nlp.ENTITIES": LibFunction("nlp.ENTITIES", 1, _wrap(nlp_ops.ENTITIES)),
        "nlp.TRANSLATE": LibFunction("nlp.TRANSLATE", 2, _wrap(nlp_ops.TRANSLATE)),
        "nlp.CODEGEN": LibFunction("nlp.CODEGEN", 2, _wrap(nlp_ops.CODEGEN)),
    }
    return LibraryRegistry(fns)
