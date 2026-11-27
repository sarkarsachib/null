"""Execution tests for REPEAT ... TIMES.

REPEAT used to emit its count, then the body, then an unconditional JUMP back
to the body start. Nothing ever tested the count and nothing decremented it, so
every REPEAT looped forever. The bug was invisible while the parser refused
`SET x TO <value>`, because no REPEAT program got as far as the VM; fixing the
grammar turned those parse errors into hangs.
"""

import pytest

from src.null_system.lang import NullLangCompiler, NullLangParser
from src.null_system.vm import NullVM


def run(source: str):
    program = NullLangParser().parse(source)
    return NullVM().execute(NullLangCompiler().compile(program))


def test_repeat_runs_the_body_the_requested_number_of_times():
    result = run(
        """
        SET count TO 0
        REPEAT 3 TIMES
            SET count TO count PLUS 1
        END REPEAT
        SHOW count
        """
    )
    assert result.success is True
    assert result.final_state["count"] == 3


def test_repeat_zero_times_runs_the_body_not_at_all():
    result = run(
        """
        SET count TO 0
        REPEAT 0 TIMES
            SET count TO count PLUS 1
        END REPEAT
        SHOW count
        """
    )
    assert result.success is True
    assert result.final_state["count"] == 0


def test_nested_repeats_use_separate_counters():
    result = run(
        """
        SET count TO 0
        REPEAT 2 TIMES
            REPEAT 3 TIMES
                SET count TO count PLUS 1
            END REPEAT
        END REPEAT
        SHOW count
        """
    )
    assert result.success is True
    assert result.final_state["count"] == 6


def test_repeat_count_is_evaluated_at_runtime():
    """The count is a value, not the literal spelled in the source.

    REPEAT only accepts an atom, so a variable is how a non-constant count is
    expressed; this checks the loop reads it instead of ignoring it.
    """
    result = run(
        """
        SET n TO 4
        SET count TO 0
        REPEAT n TIMES
            SET count TO count PLUS 1
        END REPEAT
        SHOW count
        """
    )
    assert result.success is True
    assert result.final_state["count"] == 4
