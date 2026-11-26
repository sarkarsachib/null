"""Runtime error reporting: function names and source lines from the VM."""

import textwrap

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM


def _run(source: str):
    stream = NullLangCompiler().compile(
        ModernRustParser().parse(textwrap.dedent(source))
    )
    return NullVM().execute(stream)


def test_runtime_error_reports_nested_frames_with_lines():
    result = _run(
        """\
        fn inner(index: Num) -> Num {
            let data = [1, 2, 3];
            return data[index];
        }

        fn outer(index: Num) -> Num {
            return inner(index);
        }

        fn main() {
            let value = outer(9);
            println(value);
        }
        """
    )

    assert result.success is False
    assert "Invalid index 9" in result.error
    assert result.trace == [
        "  in inner at line 3",
        "  in outer at line 7",
        "  in main at line 11",
    ]
    assert "stack trace (innermost first):" in result.error


def test_successful_run_has_no_trace():
    result = _run(
        """\
        fn add(a: Num, b: Num) -> Num {
            return a + b;
        }

        fn main() {
            println(add(2, 3));
        }
        """
    )

    assert result.success is True, result.error
    assert result.trace == []
