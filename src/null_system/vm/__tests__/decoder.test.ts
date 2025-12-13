import { Decoder } from '../decoder';
import { OpCode } from '../instructions';

describe('Decoder', () => {
  let decoder: Decoder;

  beforeEach(() => {
    decoder = new Decoder();
  });

  describe('Valid Instructions', () => {
    it('should decode SET instruction', () => {
      const program = [{ opcode: OpCode.SET, args: ['x', 42] }];
      const decoded = decoder.decode(program);

      expect(decoded).toHaveLength(1);
      expect(decoded[0].opcode).toBe(OpCode.SET);
      expect(decoded[0].args).toEqual(['x', 42]);
    });

    it('should decode ADD instruction with immediate', () => {
      const program = [{ opcode: OpCode.ADD, args: ['x', 5] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.ADD);
      expect(decoded[0].args).toEqual(['x', 5]);
    });

    it('should decode ADD instruction with register', () => {
      const program = [{ opcode: OpCode.ADD, args: ['x', 'y'] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].args).toEqual(['x', 'y']);
    });

    it('should decode SHOW instruction', () => {
      const program = [{ opcode: OpCode.SHOW, args: ['x'] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.SHOW);
    });

    it('should decode IF instruction', () => {
      const program = [
        {
          opcode: OpCode.IF,
          args: ['x', '>', [{ opcode: OpCode.SET, args: ['y', 1] }]],
        },
      ];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.IF);
      expect(decoded[0].args).toHaveLength(3);
    });

    it('should decode REPEAT instruction', () => {
      const program = [
        {
          opcode: OpCode.REPEAT,
          args: ['count', [{ opcode: OpCode.SET, args: ['x', 1] }]],
        },
      ];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.REPEAT);
    });

    it('should decode DEFINE instruction', () => {
      const program = [
        {
          opcode: OpCode.DEFINE,
          args: ['func', [{ opcode: OpCode.SET, args: ['x', 1] }]],
        },
      ];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.DEFINE);
    });

    it('should decode CALL instruction', () => {
      const program = [{ opcode: OpCode.CALL, args: ['func'] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.CALL);
    });

    it('should decode RETURN instruction', () => {
      const program = [{ opcode: OpCode.RETURN, args: [] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.RETURN);
    });

    it('should decode NOP instruction', () => {
      const program = [{ opcode: OpCode.NOP, args: [] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.NOP);
    });

    it('should decode JMP instruction', () => {
      const program = [{ opcode: OpCode.JMP, args: [10] }];
      const decoded = decoder.decode(program);

      expect(decoded[0].opcode).toBe(OpCode.JMP);
      expect(decoded[0].args).toEqual([10]);
    });

    it('should preserve line numbers', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.SET, args: ['y', 2] },
      ];
      const decoded = decoder.decode(program);

      expect(decoded[0].lineno).toBe(0);
      expect(decoded[1].lineno).toBe(1);
    });
  });

  describe('Error Handling', () => {
    it('should reject non-object instructions', () => {
      const program = [42];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject instructions with missing opcode', () => {
      const program = [{ args: ['x', 1] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject invalid opcodes', () => {
      const program = [{ opcode: 'INVALID', args: [] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject SET with missing arguments', () => {
      const program = [{ opcode: OpCode.SET, args: ['x'] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject SET with non-string register', () => {
      const program = [{ opcode: OpCode.SET, args: [42, 1] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject SET with non-numeric value', () => {
      const program = [{ opcode: OpCode.SET, args: ['x', 'not_a_number'] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject ADD with missing arguments', () => {
      const program = [{ opcode: OpCode.ADD, args: ['x'] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject SHOW with missing register', () => {
      const program = [{ opcode: OpCode.SHOW, args: [] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject IF with missing arguments', () => {
      const program = [{ opcode: OpCode.IF, args: ['x', '>'] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject IF with non-array block', () => {
      const program = [{ opcode: OpCode.IF, args: ['x', '>', 'invalid'] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject REPEAT with missing count', () => {
      const program = [{ opcode: OpCode.REPEAT, args: [[]] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject DEFINE with missing function name', () => {
      const program = [{ opcode: OpCode.DEFINE, args: [[]] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should reject CALL with missing function name', () => {
      const program = [{ opcode: OpCode.CALL, args: [] }];

      expect(() => decoder.decode(program)).toThrow();
    });

    it('should accept programs as arrays or objects', () => {
      const arrayProgram = [{ opcode: OpCode.NOP, args: [] }];
      const objectProgram = {
        instructions: [{ opcode: OpCode.NOP, args: [] }],
      };

      expect(() => decoder.decode(arrayProgram)).not.toThrow();
      expect(() => decoder.decode(objectProgram)).not.toThrow();
    });

    it('should reject invalid program structure', () => {
      const invalidProgram = { invalid: 'structure' } as unknown;

      expect(() => decoder.decode(invalidProgram as unknown[])).toThrow();
    });
  });

  describe('Complex Programs', () => {
    it('should decode nested instructions', () => {
      const program = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'func',
            [
              { opcode: OpCode.SET, args: ['x', 1] },
              {
                opcode: OpCode.IF,
                args: ['x', '>', [{ opcode: OpCode.SET, args: ['y', 2] }]],
              },
            ],
          ],
        },
      ];

      expect(() => decoder.decode(program)).not.toThrow();
    });

    it('should decode multi-instruction programs', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['y', 20] },
        { opcode: OpCode.ADD, args: ['x', 'y'] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      const decoded = decoder.decode(program);

      expect(decoded).toHaveLength(4);
      expect(decoded[0].opcode).toBe(OpCode.SET);
      expect(decoded[1].opcode).toBe(OpCode.SET);
      expect(decoded[2].opcode).toBe(OpCode.ADD);
      expect(decoded[3].opcode).toBe(OpCode.SHOW);
    });
  });
});
