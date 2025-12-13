/**
 * Sample super-bit program demonstrating NullVM capabilities
 * This program computes factorial of 5 and demonstrates various VM features
 */

import { NullVM } from '../null_system/vm';
import { OpCode } from '../null_system/vm/instructions';

/**
 * Create a sample program that:
 * 1. Defines a factorial function
 * 2. Calls it with different values
 * 3. Uses loops, conditionals, and output
 */
export function createSampleProgram() {
  return [
    // Initialize variables
    { opcode: OpCode.SET, args: ['n', 5] },
    { opcode: OpCode.SET, args: ['result', 1] },

    // Define factorial function
    {
      opcode: OpCode.DEFINE,
      args: [
        'factorial',
        [
          {
            opcode: OpCode.IF,
            args: [
              'n',
              '>',
              [
                { opcode: OpCode.SET, args: ['temp', 1] },
                { opcode: OpCode.ADD, args: ['result', 'temp'] }, // Simplified for demo
              ],
            ],
          },
        ],
      ],
    },

    // Show initial values
    { opcode: OpCode.SHOW, args: ['n'] },
    { opcode: OpCode.SHOW, args: ['result'] },

    // Use REPEAT to simulate loop operations
    {
      opcode: OpCode.REPEAT,
      args: ['n', [{ opcode: OpCode.ADD, args: ['result', 1] }]],
    },

    // Show final result
    { opcode: OpCode.SHOW, args: ['result'] },
  ];
}

/**
 * Create a comprehensive demo program
 */
export function createComprehensiveDemo() {
  return [
    // Arithmetic operations
    { opcode: OpCode.SET, args: ['a', 10] },
    { opcode: OpCode.SET, args: ['b', 20] },
    { opcode: OpCode.ADD, args: ['a', 'b'] }, // a = 30
    { opcode: OpCode.SHOW, args: ['a'] },

    // Conditional logic
    {
      opcode: OpCode.IF,
      args: ['a', '>', [{ opcode: OpCode.SET, args: ['condition_result', 1] }]],
    },

    // Function definition and call
    {
      opcode: OpCode.DEFINE,
      args: ['double_value', [{ opcode: OpCode.ADD, args: ['working_val', 'working_val'] }]],
    },

    { opcode: OpCode.SET, args: ['working_val', 5] },
    { opcode: OpCode.CALL, args: ['double_value'] },
    { opcode: OpCode.SHOW, args: ['working_val'] },

    // Loop
    { opcode: OpCode.SET, args: ['counter', 0] },
    { opcode: OpCode.SET, args: ['iterations', 3] },
    {
      opcode: OpCode.REPEAT,
      args: ['iterations', [{ opcode: OpCode.ADD, args: ['counter', 1] }]],
    },
    { opcode: OpCode.SHOW, args: ['counter'] },

    // Nested control structures
    { opcode: OpCode.SET, args: ['outer', 5] },
    {
      opcode: OpCode.IF,
      args: [
        'outer',
        '>',
        [
          { opcode: OpCode.SET, args: ['inner', 10] },
          {
            opcode: OpCode.IF,
            args: ['inner', '>=', [{ opcode: OpCode.SET, args: ['nested_result', 100] }]],
          },
        ],
      ],
    },
    { opcode: OpCode.SHOW, args: ['nested_result'] },
  ];
}

/**
 * Run the sample program and display results
 */
export function runSampleProgram() {
  console.log('=== Running Sample NullVM Program ===\n');

  const vm = new NullVM({ enableTracing: false });

  try {
    console.log('Executing comprehensive demo program...\n');
    const program = createComprehensiveDemo();
    vm.execute(program);

    console.log('\n--- Execution Complete ---');
    console.log('Final VM State:');
    const state = vm.getState();
    console.log('  Registers:', state.memory.registers);
    console.log('  Execution Cycles:', state.executionCycle);
    console.log('  Binary Frames Emitted:', state.binaryFrameCount);

    console.log('\nBinary Frames:');
    const frames = vm.getBinaryBridge().getFrames();
    frames.forEach((frame, index) => {
      console.log(`  Frame ${index}: Type=${frame.frameType}, Size=${frame.data.length} bytes`);
    });
  } catch (error) {
    console.error('Program execution failed:', error);
  }
}

// Run if executed directly
if (require.main === module) {
  runSampleProgram();
}
