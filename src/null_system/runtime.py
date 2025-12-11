from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lib.registry import LibraryRegistry


class NullIO:
    def read_line(self) -> str:
        return input()

    def write(self, text: str) -> None:
        print(text)


@dataclass(frozen=True)
class NullCallContext:
    registry: "LibraryRegistry"
    io: NullIO
