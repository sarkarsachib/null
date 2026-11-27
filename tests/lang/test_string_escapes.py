"""String-literal escape decoding.

The decoder used to be a chain of ``str.replace`` calls, which decoded in the
wrong order: ``\\t`` (backslash + ``t``, which the emitter writes as an IR
separator) came out as a backslash plus a real tab and split an IR row in two.
It also dropped the backslash on escapes it did not recognize, silently
changing string contents.
"""

import pytest

from null_system.lang.parser import decode_escapes

BACKSLASH = chr(92)


@pytest.mark.parametrize(
    "source, expected",
    [
        (BACKSLASH + "n", "\n"),
        (BACKSLASH + "t", "\t"),
        (BACKSLASH + '"', '"'),
        (BACKSLASH + "'", "'"),
        (BACKSLASH + BACKSLASH, BACKSLASH),
        # An unrecognized escape keeps its backslash instead of being dropped.
        (BACKSLASH + "a", BACKSLASH + "a"),
        (BACKSLASH + "r", BACKSLASH + "r"),
        (BACKSLASH + "0", BACKSLASH + "0"),
        ("x" + BACKSLASH + "a", "x" + BACKSLASH + "a"),
        # The order-dependent case: a real tab survives, an escaped tab does not.
        ("a" + BACKSLASH + "tb", "a\tb"),
        (BACKSLASH + BACKSLASH + "t", BACKSLASH + "t"),
        ("plain text", "plain text"),
    ],
)
def test_decode_escapes(source, expected):
    assert decode_escapes(source) == expected


def test_trailing_backslash_is_preserved():
    assert decode_escapes("abc" + BACKSLASH) == "abc" + BACKSLASH
