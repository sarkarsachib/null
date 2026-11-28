"""A small, dependency-free command framework for the Null toolchain.

This module is the CLI framework itself. It intentionally uses only the Python
standard library: the toolchain commands it hosts are being moved to Null, and
a framework that still needs Typer/Rich cannot be part of that path.

A command is a callable plus a declarative list of parameters. ``main`` parses
``sys.argv`` style argument lists, dispatches to the command, and renders help
and errors in a stable format that can be tested without a terminal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence


class CLIError(Exception):
    """A user-facing command-line error."""


@dataclass(frozen=True)
class Option:
    """A named flag or value option.

    ``flags`` contains the accepted spellings, e.g. ``("-o", "--output")``.
    ``is_flag`` marks a switch that takes no value. ``default`` supplies the
    value when the option is absent. ``multiple`` collects repeated options
    into a list.
    """

    name: str
    flags: tuple[str, ...]
    help: str = ""
    is_flag: bool = False
    default: Any = None
    multiple: bool = False


@dataclass(frozen=True)
class Argument:
    """A positional argument."""

    name: str
    help: str = ""
    default: Any = None
    required: bool = True
    variadic: bool = False


@dataclass
class Command:
    """One command in the toolchain."""

    name: str
    callback: Callable[..., Any]
    help: str = ""
    arguments: tuple[Argument, ...] = ()
    options: tuple[Option, ...] = ()
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def invoke(self, argv: Sequence[str]) -> Any:
        values, rest = parse_arguments(self, argv)
        if rest:
            raise CLIError(f"unexpected argument: {rest[0]}")
        return self.callback(**values)


@dataclass
class CLI:
    """A named collection of commands."""

    name: str
    help: str = ""
    commands: dict[str, Command] = field(default_factory=dict)

    def add(self, command: Command) -> Command:
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
        return command

    def command(
        self,
        name: str,
        *,
        help: str = "",
        arguments: Iterable[Argument] = (),
        options: Iterable[Option] = (),
        aliases: Iterable[str] = (),
    ) -> Callable[[Callable[..., Any]], Command]:
        def decorate(callback: Callable[..., Any]) -> Command:
            return self.add(
                Command(
                    name=name,
                    callback=callback,
                    help=help,
                    arguments=tuple(arguments),
                    options=tuple(options),
                    aliases=tuple(aliases),
                )
            )

        return decorate

    def help_text(self) -> str:
        lines = [f"{self.name} — {self.help}".rstrip(" —"), "", "Commands:"]
        seen: set[int] = set()
        for command in sorted(self.commands.values(), key=lambda c: c.name):
            if id(command) in seen:
                continue
            seen.add(id(command))
            lines.append(f"  {command.name:<16} {command.help}")
        lines.extend(["", f"Run '{self.name} <command> --help' for details."])
        return "\n".join(lines)

    def command_help(self, command: Command) -> str:
        lines = [f"{self.name} {command.name} — {command.help}".rstrip(" —")]
        if command.arguments:
            lines.extend(["", "Arguments:"])
            for argument in command.arguments:
                suffix = "" if argument.required else " (optional)"
                lines.append(f"  {argument.name:<16} {argument.help}{suffix}")
        if command.options:
            lines.extend(["", "Options:"])
            for option in command.options:
                flags = ", ".join(option.flags)
                lines.append(f"  {flags:<16} {option.help}")
        return "\n".join(lines)

    def main(self, argv: Sequence[str]) -> int:
        """Dispatch ``argv``, returning a process exit code."""
        args = list(argv)
        if not args or args[0] in ("-h", "--help", "help"):
            print(self.help_text())
            return 0
        name = args.pop(0)
        command = self.commands.get(name)
        if command is None:
            print(f"error: unknown command: {name}", file=__import__("sys").stderr)
            print(self.help_text(), file=__import__("sys").stderr)
            return 2
        if "--help" in args or "-h" in args:
            print(self.command_help(command))
            return 0
        try:
            result = command.invoke(args)
        except CLIError as error:
            print(f"error: {error}", file=__import__("sys").stderr)
            return 2
        return int(result) if isinstance(result, int) else 0


def parse_arguments(command: Command, argv: Sequence[str]) -> tuple[dict[str, Any], list[str]]:
    """Parse one command's arguments.

    Returns the keyword values for the callback and any unconsumed tokens.
    Options may appear before, between, or after positional arguments; ``--``
    ends option parsing. Unknown options are an error rather than being silently
    treated as positionals.
    """
    import sys

    values: dict[str, Any] = {}
    positionals: list[str] = []
    seen: set[str] = set()
    option_by_flag: dict[str, Option] = {}
    for option in command.options:
        for flag in option.flags:
            option_by_flag[flag] = option
        if option.is_flag:
            values[option.name] = bool(option.default)
        elif option.multiple:
            values[option.name] = list(option.default or ())
        else:
            values[option.name] = option.default

    tokens = list(argv)
    allow_options = True
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if allow_options and token == "--":
            allow_options = False
            index += 1
            continue
        if allow_options and token.startswith("-") and token != "-":
            parts = token.split("=", 1)
            option = option_by_flag.get(parts[0])
            if option is None:
                raise CLIError(f"unknown option: {parts[0]}")
            if option.is_flag:
                if len(parts) == 2:
                    raise CLIError(f"option {parts[0]} takes no value")
                values[option.name] = True
                index += 1
                continue
            if len(parts) == 2:
                value: Any = parts[1]
                index += 1
            else:
                if index + 1 >= len(tokens):
                    raise CLIError(f"option {parts[0]} requires a value")
                value = tokens[index + 1]
                index += 2
            if option.multiple:
                values[option.name].append(value)
            else:
                if option.name in seen:
                    raise CLIError(f"option {parts[0]} given more than once")
                seen.add(option.name)
                values[option.name] = value
            continue
        positionals.append(token)
        index += 1

    for argument in command.arguments:
        if argument.variadic:
            values[argument.name] = list(positionals)
            positionals = []
            if argument.required and not values[argument.name]:
                raise CLIError(f"missing argument: {argument.name}")
            continue
        if positionals:
            values[argument.name] = positionals.pop(0)
        elif argument.required and argument.default is None:
            raise CLIError(f"missing argument: {argument.name}")
        else:
            values[argument.name] = argument.default

    return values, positionals
