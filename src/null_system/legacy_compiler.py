from __future__ import annotations

import ast
from dataclasses import dataclass

from .errors import NullNameError, NullParseError, SourceLocation
from .lib.registry import LibraryRegistry
from .types import NullFunctionRef, NullValue, to_null


@dataclass(frozen=True)
class Instruction:
    op: str
    args: tuple[object, ...] = ()
    loc: SourceLocation | None = None


@dataclass
class CompiledProgram:
    instructions: list[Instruction]
    functions: dict[str, str]


def _parse_int(text: str, *, line: int, what: str) -> int:
    try:
        return int(text)
    except ValueError as e:
        raise NullParseError(
            f"Invalid integer for {what}: {text}",
            code="NULL_PARSE_ERROR",
            line=line,
            value=text,
            what=what,
        ) from e


def compile_program(source: str, *, registry: LibraryRegistry) -> CompiledProgram:
    instructions: list[Instruction] = []
    functions: dict[str, str] = {}

    lines = source.splitlines()
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        op = parts[0].upper()
        loc = SourceLocation(line=idx, column=1)

        try:
            if op == "PUSH":
                literal_text = raw_line.split(None, 1)[1]
                try:
                    literal = ast.literal_eval(literal_text)
                except Exception as e:  # noqa: BLE001
                    raise NullParseError(
                        f"Invalid literal: {literal_text}",
                        code="NULL_PARSE_ERROR",
                        line=idx,
                        literal=literal_text,
                    ) from e
                value: NullValue = to_null(literal)
                instructions.append(Instruction("PUSH", (value,), loc))
                continue

            if op == "DEFINE":
                # DEFINE <name> USE LIB <lib>.<FUNC>
                if len(parts) != 5 or parts[2].upper() != "USE" or parts[3].upper() != "LIB":
                    raise NullParseError(
                        "Invalid DEFINE syntax. Expected: DEFINE <name> USE LIB <lib>.<FUNC>",
                        code="NULL_PARSE_ERROR",
                        line=idx,
                    )
                name = parts[1]
                lib_path = parts[4]
                registry.require(lib_path, where="compiler")
                functions[name] = lib_path
                continue

            if op == "PUSH_REF":
                if len(parts) != 2:
                    raise NullParseError(
                        "Invalid PUSH_REF syntax. Expected: PUSH_REF <name>",
                        code="NULL_PARSE_ERROR",
                        line=idx,
                    )
                name = parts[1]
                if name not in functions:
                    raise NullNameError(
                        f"Unknown function alias '{name}'",
                        code="NULL_UNKNOWN_NAME",
                        name=name,
                        line=idx,
                    )
                instructions.append(
                    Instruction("PUSH", (NullFunctionRef(functions[name]),), loc)
                )
                continue

            if op == "CALL":
                if len(parts) != 3:
                    raise NullParseError(
                        "Invalid CALL syntax. Expected: CALL <name> <arg_count>",
                        code="NULL_PARSE_ERROR",
                        line=idx,
                    )
                name = parts[1]
                if name not in functions:
                    raise NullNameError(
                        f"Unknown function alias '{name}'",
                        code="NULL_UNKNOWN_NAME",
                        name=name,
                        line=idx,
                    )
                argc = _parse_int(parts[2], line=idx, what="arg_count")
                instructions.append(Instruction("LIBCALL", (functions[name], argc), loc))
                continue

            if op == "LIBCALL":
                if len(parts) != 3:
                    raise NullParseError(
                        "Invalid LIBCALL syntax. Expected: LIBCALL <lib>.<FUNC> <arg_count>",
                        code="NULL_PARSE_ERROR",
                        line=idx,
                    )
                lib_path = parts[1]
                argc = _parse_int(parts[2], line=idx, what="arg_count")
                registry.require(lib_path, where="compiler")
                instructions.append(Instruction("LIBCALL", (lib_path, argc), loc))
                continue

            if op == "SHOW":
                instructions.append(Instruction("SHOW", (), loc))
                continue

            if op == "READ":
                instructions.append(Instruction("READ", (), loc))
                continue

            if op == "HALT":
                instructions.append(Instruction("HALT", (), loc))
                continue

            raise NullParseError(
                f"Unknown opcode '{op}'",
                code="NULL_PARSE_ERROR",
                line=idx,
                opcode=op,
            )
        except Exception as e:
            if isinstance(e, NullParseError):
                raise
            if isinstance(e, NullNameError):
                raise
            raise

    return CompiledProgram(instructions=instructions, functions=functions)
