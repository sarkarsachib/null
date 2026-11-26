"""Run one bootstrap stage (a .null file) on the host VM.

This is benchmark/CI tooling, not part of the language: it exists so scripts can
execute `bootstrap/*.null` without repeating the host bootstrapping.  The stages
themselves are written in Null.
"""
import sys
import time

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM


def main(argv):
    if len(argv) < 2:
        print("usage: stage_runner.py <stage.null>")
        return 2
    path = argv[1]
    started = time.perf_counter()
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    result = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(source)))
    print(f"{path} success={result.success} secs={time.perf_counter() - started:.2f} out={len(result.output)}")
    if result.error:
        print("error:", str(result.error)[:2000])
    for line in result.output[:40]:
        print(line)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
