"""break/continue lowering for both syntaxes.

`break` and `continue` inside loops must jump to the loop end / loop
increment. Unpatched jumps used to send the VM back to instruction 0.
"""

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.lang.parser import NullLangParser
from null_system.vm.vm import NullVM


def _run(parser, source: str) -> list[str]:
    stream = NullLangCompiler().compile(parser.parse(source))
    result = NullVM().execute(stream)
    assert result.success, result.error
    return result.output


def test_modern_break_and_continue_in_while():
    source = """
    let words = ["aa", "bb", "cc", "dd"];
    let i = 0;
    let hits = [];
    while i < LEN(words) {
        let w = words[i];
        i = i + 1;
        if w == "bb" {
            continue;
        }
        hits = APPEND(hits, w);
        if LEN(hits) >= 2 {
            break;
        }
    }
    println(TO_STRING(LEN(hits)));
    println(hits[0]);
    println(hits[1]);
    """
    assert _run(ModernRustParser(), source) == ["2", "aa", "cc"]


def test_modern_continue_in_for_runs_the_increment():
    source = """
    let total = 0;
    for i in 0..6 {
        if i == 2 {
            continue;
        }
        if i == 5 {
            break;
        }
        total = total + i;
    }
    println(TO_STRING(total));
    """
    # 0 + 1 + 3 + 4
    assert _run(ModernRustParser(), source) == ["8"]


def test_english_break_and_continue_in_while():
    source = """
SET words TO ARRAY ["aa", "bb", "cc", "dd"]
SET i TO 0
SET hits TO ARRAY []
WHILE i IS LESS THAN LEN(words)
    SET w TO words[i]
    SET i TO i PLUS 1
    IF w IS "bb" THEN
        CONTINUE
    END IF
    SET hits TO APPEND(hits, w)
    IF LEN(hits) IS GREATER THAN 1 THEN
        BREAK
    END IF
END WHILE
SHOW LEN(hits)
SHOW hits[0]
"""
    assert _run(NullLangParser(), source) == ["2", "aa"]
