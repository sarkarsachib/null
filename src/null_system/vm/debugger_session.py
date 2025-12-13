from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..binary.generator import BinaryFrame
from ..superbit.ir import SuperBitIRToken, SuperBitStream
from .vm import NullVM


@dataclass(frozen=True)
class InstructionSnapshot:
    step: int
    pc: int
    opcode: str
    operand: Any
    source_line: Optional[int]
    binary_bytes_hex: str


@dataclass(frozen=True)
class ExecutionFrame:
    step: int
    pc: int
    opcode: str
    operand: Any
    source_line: Optional[int]
    stack: List[Any]
    variables: Dict[str, Any]
    output: List[str]
    binary_bytes_hex: str


class NullDebuggerSession:
    """Captures per-instruction execution snapshots for visualization."""

    def __init__(
        self,
        *,
        source: str,
        superbit_stream: SuperBitStream,
        binary_frames: List[BinaryFrame],
        program_path: str | None = None,
    ) -> None:
        self.source = source
        self.source_lines = source.splitlines()
        self.superbit_stream = superbit_stream
        self.binary_frames = binary_frames
        self.program_path = program_path

        self._frames: List[ExecutionFrame] = []
        self._timeline: List[InstructionSnapshot] = []

    @property
    def steps(self) -> int:
        return len(self._frames)

    def run(self) -> "NullDebuggerSession":
        vm = NullVM()
        vm.stack = []
        vm.variables = {}
        vm.output = []

        pc = 0
        tokens = self.superbit_stream.tokens
        token_bytes = self.superbit_stream.token_bytes()

        frames: List[ExecutionFrame] = []
        timeline: List[InstructionSnapshot] = []

        while pc < len(tokens):
            token = tokens[pc]
            vm.pc = pc
            before_output_len = len(vm.output)

            vm._execute_token(token)  # noqa: SLF001

            next_pc = vm.pc + 1

            opcode = token.opcode.name
            operand = token.operand
            source_line = token.source_line
            bhex = token_bytes[pc].hex()

            timeline.append(
                InstructionSnapshot(
                    step=len(frames),
                    pc=pc,
                    opcode=opcode,
                    operand=operand,
                    source_line=source_line,
                    binary_bytes_hex=bhex,
                )
            )

            frames.append(
                ExecutionFrame(
                    step=len(frames),
                    pc=pc,
                    opcode=opcode,
                    operand=operand,
                    source_line=source_line,
                    stack=list(vm.stack),
                    variables=dict(vm.variables),
                    output=list(vm.output[before_output_len:]),
                    binary_bytes_hex=bhex,
                )
            )

            pc = next_pc

        self._frames = frames
        self._timeline = timeline
        return self

    def timeline_json(self) -> dict[str, Any]:
        if not self._timeline:
            raise RuntimeError("Session not run")

        return {
            "version": 1,
            "program": {"path": self.program_path},
            "source": {
                "text": self.source,
                "lines": [
                    {"line": i + 1, "text": line}
                    for i, line in enumerate(self.source_lines)
                ],
            },
            "steps": len(self._timeline),
            "instructions": [asdict(s) for s in self._timeline],
            "binary": {
                "frames": [
                    {
                        "header_hex": frame.header.hex(),
                        "code_hex": frame.code.hex(),
                        "constants_hex": frame.constants.hex(),
                    }
                    for frame in self.binary_frames
                ]
            },
        }

    def frame_json(self, step: int) -> dict[str, Any]:
        if not self._frames:
            raise RuntimeError("Session not run")
        if step < 0 or step >= len(self._frames):
            raise IndexError("Step out of range")
        frame = self._frames[step]
        return asdict(frame)

    def dump_json(self, path: Path) -> None:
        payload = {
            "timeline": self.timeline_json(),
            "frames": [self.frame_json(i) for i in range(self.steps)],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    @staticmethod
    def load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text())
