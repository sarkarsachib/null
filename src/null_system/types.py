from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .errors import NullTypeError


class NullValue:
    def type_name(self) -> str:
        raise NotImplementedError

    def display(self) -> str:
        return str(self)

    def as_number(self) -> float:
        raise NullTypeError(
            f"Expected number, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="number",
            actual=self.type_name(),
        )

    def as_string(self) -> str:
        raise NullTypeError(
            f"Expected string, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="string",
            actual=self.type_name(),
        )

    def as_array(self) -> "NullArray":
        raise NullTypeError(
            f"Expected array, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="array",
            actual=self.type_name(),
        )

    def as_object(self) -> "NullObject":
        raise NullTypeError(
            f"Expected object, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="object",
            actual=self.type_name(),
        )

    def as_function_ref(self) -> "NullFunctionRef":
        raise NullTypeError(
            f"Expected function_ref, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="function_ref",
            actual=self.type_name(),
        )

    def as_union(self) -> "NullUnion":
        raise NullTypeError(
            f"Expected union, got {self.type_name()}",
            code="NULL_TYPE_ERROR",
            expected="union",
            actual=self.type_name(),
        )


@dataclass
class NullNumber(NullValue):
    value: float

    def type_name(self) -> str:
        return "number"

    def as_number(self) -> float:
        return self.value

    def __str__(self) -> str:
        if self.value.is_integer():
            return str(int(self.value))
        return str(self.value)


@dataclass
class NullString(NullValue):
    value: str

    def type_name(self) -> str:
        return "string"

    def as_string(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass
class NullArray(NullValue):
    items: list[NullValue]

    def type_name(self) -> str:
        return "array"

    def as_array(self) -> "NullArray":
        return self

    def __str__(self) -> str:
        return "[" + ", ".join(item.display() for item in self.items) + "]"


@dataclass
class NullObject(NullValue):
    items: dict[str, NullValue]

    def type_name(self) -> str:
        return "object"

    def as_object(self) -> "NullObject":
        return self

    def __str__(self) -> str:
        inner = ", ".join(f"{k}: {v.display()}" for k, v in self.items.items())
        return "{" + inner + "}"


@dataclass(frozen=True)
class NullFunctionRef(NullValue):
    lib_path: str

    def type_name(self) -> str:
        return "function_ref"

    def as_function_ref(self) -> "NullFunctionRef":
        return self

    def __str__(self) -> str:
        return f"<fn {self.lib_path}>"


class _NullNull(NullValue):
    def type_name(self) -> str:
        return "null"

    def __str__(self) -> str:
        return "null"


NULL = _NullNull()


@dataclass
class NullUnion(NullValue):
    tag: str
    value: NullValue

    def type_name(self) -> str:
        return f"union({self.tag})"

    def as_union(self) -> "NullUnion":
        return self

    def __str__(self) -> str:
        return f"{self.tag}({self.value.display()})"


@dataclass
class NullOption(NullUnion):
    def __post_init__(self):
        if self.tag not in ("Some", "None"):
            raise NullTypeError(
                f"Invalid Option tag: {self.tag}",
                code="NULL_TYPE_ERROR",
                expected="Some|None",
                actual=self.tag,
            )

    def type_name(self) -> str:
        return "option"

    def is_some(self) -> bool:
        return self.tag == "Some"

    def is_none(self) -> bool:
        return self.tag == "None"

    def unwrap(self) -> NullValue:
        if self.tag == "None":
            raise NullTypeError(
                "Called unwrap on None",
                code="NULL_UNWRAP_ERROR",
                actual="None",
            )
        return self.value

    def __str__(self) -> str:
        if self.tag == "None":
            return "None"
        return f"Some({self.value.display()})"


@dataclass
class NullResult(NullUnion):
    def __post_init__(self):
        if self.tag not in ("Ok", "Err"):
            raise NullTypeError(
                f"Invalid Result tag: {self.tag}",
                code="NULL_TYPE_ERROR",
                expected="Ok|Err",
                actual=self.tag,
            )

    def type_name(self) -> str:
        return "result"

    def is_ok(self) -> bool:
        return self.tag == "Ok"

    def is_err(self) -> bool:
        return self.tag == "Err"

    def unwrap(self) -> NullValue:
        if self.tag == "Err":
            raise NullTypeError(
                f"Called unwrap on Err: {self.value.display()}",
                code="NULL_UNWRAP_ERROR",
                actual="Err",
            )
        return self.value

    def unwrap_err(self) -> NullValue:
        if self.tag == "Ok":
            raise NullTypeError(
                "Called unwrap_err on Ok",
                code="NULL_UNWRAP_ERROR",
                actual="Ok",
            )
        return self.value

    def __str__(self) -> str:
        if self.tag == "Ok":
            return f"Ok({self.value.display()})"
        return f"Err({self.value.display()})"


def to_null(value: Any) -> NullValue:
    if isinstance(value, NullValue):
        return value
    if value is None:
        return NULL
    if isinstance(value, bool):
        return NullNumber(1.0 if value else 0.0)
    if isinstance(value, (int, float)):
        return NullNumber(float(value))
    if isinstance(value, str):
        return NullString(value)
    if isinstance(value, list):
        return NullArray([to_null(v) for v in value])
    if isinstance(value, dict):
        out: dict[str, NullValue] = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise NullTypeError(
                    "Object keys must be strings",
                    code="NULL_TYPE_ERROR",
                    expected="string_key",
                    actual=type(k).__name__,
                )
            out[k] = to_null(v)
        return NullObject(out)
    if isinstance(value, Iterable):
        return NullArray([to_null(v) for v in value])
    raise NullTypeError(
        f"Cannot convert {type(value).__name__} to NullValue",
        code="NULL_TYPE_ERROR",
        expected="null_value",
        actual=type(value).__name__,
    )


def none_val() -> NullOption:
    return NullOption(tag="None", value=NULL)


def some_val(value: NullValue) -> NullOption:
    return NullOption(tag="Some", value=value)


def ok_val(value: NullValue) -> NullResult:
    return NullResult(tag="Ok", value=value)


def err_val(value: NullValue) -> NullResult:
    return NullResult(tag="Err", value=value)
