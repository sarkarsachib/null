"""Tests for the dependency-free Null toolchain CLI framework."""

import pytest

from null_system.toolchain.cli import Argument, CLI, CLIError, Command, Option, parse_arguments
from null_system.toolchain.commands import create_cli


def test_parses_positional_and_named_options():
    command = Command(
        name="build",
        callback=lambda **kwargs: kwargs,
        arguments=(Argument("source", "Source"),),
        options=(
            Option("output", ("-o", "--output"), "Output"),
            Option("verbose", ("-v", "--verbose"), "Verbose", is_flag=True),
        ),
    )
    values, rest = parse_arguments(command, ["--verbose", "file.null", "-o", "out.ir"])
    assert values == {
        "output": "out.ir",
        "verbose": True,
        "source": "file.null",
    }
    assert rest == []


def test_supports_equals_and_repeated_options():
    command = Command(
        name="test",
        callback=lambda **kwargs: kwargs,
        options=(Option("mark", ("-m", "--mark"), "Marker", multiple=True),),
    )
    values, rest = parse_arguments(command, ["-m=one", "--mark", "two"])
    assert values == {"mark": ["one", "two"]}
    assert rest == []


def test_rejects_unknown_options_and_missing_arguments():
    command = Command(
        name="build",
        callback=lambda **kwargs: kwargs,
        arguments=(Argument("source", "Source"),),
    )
    with pytest.raises(CLIError, match="unknown option"):
        parse_arguments(command, ["--missing", "file.null"])
    with pytest.raises(CLIError, match="missing argument"):
        parse_arguments(command, [])


def test_cli_dispatches_and_reports_errors(capsys):
    cli = CLI("demo", "A demonstration")
    seen = []

    @cli.command(
        "echo",
        help="Echo a value",
        arguments=(Argument("value", "Value"),),
        options=(Option("upper", ("-u", "--upper"), "Uppercase", is_flag=True),),
    )
    def echo(value, upper):
        seen.append((value, upper))
        return 0

    assert cli.main(["echo", "-u", "hello"]) == 0
    assert seen == [("hello", True)]
    assert cli.main(["missing"]) == 2
    assert "unknown command" in capsys.readouterr().err
    assert cli.main([]) == 0
    assert "Commands:" in capsys.readouterr().out


def test_toolchain_exposes_the_roadmap_verbs():
    commands = create_cli().commands
    for name in ("build", "test", "fmt", "clean", "bench"):
        assert name in commands
