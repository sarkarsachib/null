import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ExecutionVisualizer } from './ExecutionVisualizer';
import type { ExecutionFrame, Timeline } from '../types';

const timeline: Timeline = {
  version: 1,
  steps: 4,
  source: {
    text: 'set x to 1\nprint x\n',
    lines: [
      { line: 1, text: 'set x to 1' },
      { line: 2, text: 'print x' },
    ],
  },
  instructions: [
    {
      step: 0,
      pc: 0,
      opcode: 'LOAD_CONST',
      operand: 1,
      source_line: 1,
      binary_bytes_hex: '010200000001',
    },
    {
      step: 1,
      pc: 1,
      opcode: 'STORE_VAR',
      operand: 'x',
      source_line: 1,
      binary_bytes_hex: '03040178',
    },
    {
      step: 2,
      pc: 2,
      opcode: 'LOAD_VAR',
      operand: 'x',
      source_line: 2,
      binary_bytes_hex: '02040178',
    },
    {
      step: 3,
      pc: 3,
      opcode: 'PRINT',
      operand: null,
      source_line: 2,
      binary_bytes_hex: '1e00',
    },
  ],
};

const frames: ExecutionFrame[] = [
  {
    step: 0,
    pc: 0,
    opcode: 'LOAD_CONST',
    operand: 1,
    source_line: 1,
    stack: [1],
    variables: {},
    output: [],
    binary_bytes_hex: '010200000001',
  },
  {
    step: 1,
    pc: 1,
    opcode: 'STORE_VAR',
    operand: 'x',
    source_line: 1,
    stack: [],
    variables: { x: 1 },
    output: [],
    binary_bytes_hex: '03040178',
  },
  {
    step: 2,
    pc: 2,
    opcode: 'LOAD_VAR',
    operand: 'x',
    source_line: 2,
    stack: [1],
    variables: { x: 1 },
    output: [],
    binary_bytes_hex: '02040178',
  },
  {
    step: 3,
    pc: 3,
    opcode: 'PRINT',
    operand: null,
    source_line: 2,
    stack: [],
    variables: { x: 1 },
    output: ['1'],
    binary_bytes_hex: '1e00',
  },
];

test('panes stay in sync when stepping forward', async () => {
  const user = userEvent.setup();
  render(<ExecutionVisualizer timeline={timeline} frames={frames} />);

  expect(screen.getByTestId('active-instruction')).toHaveTextContent('LOAD_CONST');
  expect(screen.getByTestId('active-source-line')).toHaveTextContent('set x to 1');
  expect(screen.getByTestId('hex-viewer')).toHaveTextContent('010200000001');

  await user.click(screen.getByTestId('step-forward'));

  expect(screen.getByTestId('active-instruction')).toHaveTextContent('STORE_VAR');
  expect(screen.getByTestId('active-source-line')).toHaveTextContent('set x to 1');
  expect(screen.getByTestId('hex-viewer')).toHaveTextContent('03040178');

  await user.click(screen.getByTestId('step-forward'));

  expect(screen.getByTestId('active-instruction')).toHaveTextContent('LOAD_VAR');
  expect(screen.getByTestId('active-source-line')).toHaveTextContent('print x');
  expect(screen.getByTestId('hex-viewer')).toHaveTextContent('02040178');
});

test('clicking an instruction updates all panes', async () => {
  const user = userEvent.setup();
  render(<ExecutionVisualizer timeline={timeline} frames={frames} />);

  await user.click(screen.getByText(/003 PRINT/i));

  expect(screen.getByTestId('active-instruction')).toHaveTextContent('PRINT');
  expect(screen.getByTestId('active-source-line')).toHaveTextContent('print x');
  expect(screen.getByTestId('hex-viewer')).toHaveTextContent('1e00');
});
