export interface TimelineSourceLine {
  line: number;
  text: string;
}

export interface Timeline {
  version: number;
  steps: number;
  source: {
    text: string;
    lines: TimelineSourceLine[];
  };
  instructions: Array<{
    step: number;
    pc: number;
    opcode: string;
    operand: unknown;
    source_line: number | null;
    binary_bytes_hex: string;
  }>;
}

export interface ExecutionFrame {
  step: number;
  pc: number;
  opcode: string;
  operand: unknown;
  source_line: number | null;
  stack: unknown[];
  variables: Record<string, unknown>;
  output: string[];
  binary_bytes_hex: string;
}
