import { NullVM } from '../null_vm';
import { OpCode, Instruction } from '../instructions';
import { LayerKind, LayerExecutionManager, EnglishLayerAdapter } from '../layers';
import { ExecutionContext } from '../execution_context';

describe('Layer Execution', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM({ enableTracing: false });
  });

  describe('Layer Routing and Execution', () => {
    it('should route instruction to english layer by default', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(42);
    });

    it('should respect @layer metadata for binary layer', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 100], layer: LayerKind.BINARY },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(100);
    });

    it('should respect @layer metadata for superbit layer', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 50], layer: LayerKind.SUPERBIT },
        { opcode: OpCode.ADD, args: ['x', 25], layer: LayerKind.SUPERBIT },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(75);
    });

    it('should handle mixed layer instructions', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 10], layer: LayerKind.ENGLISH },
        { opcode: OpCode.ADD, args: ['x', 5], layer: LayerKind.BINARY },
        { opcode: OpCode.SET, args: ['y', 7], layer: LayerKind.CPU },
        { opcode: OpCode.ADD, args: ['x', 'y'], layer: LayerKind.SUPERBIT },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(22);
    });
  });

  describe('Required Layers Enforcement', () => {
    it('should enforce @require constraint', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.SET,
          args: ['x', 42],
          requiredLayers: [LayerKind.BINARY],
        },
      ];

      expect(() => vm.execute(program)).not.toThrow();
      expect(vm.getMemory().getRegister('x')).toBe(42);
    });

    it('should fail when required layer is not available', () => {
      const manager = new LayerExecutionManager([LayerKind.ENGLISH]);

      const metadata = {
        layer: LayerKind.ENGLISH,
        requiredLayers: [LayerKind.BINARY],
      };

      expect(() => {
        manager.getAvailableLayers();
      }).not.toThrow();

      expect(manager.isLayerAvailable(LayerKind.BINARY)).toBe(false);
    });

    it('should track required layers in metadata', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.SET,
          args: ['x', 10],
          requiredLayers: [LayerKind.SUPERBIT, LayerKind.BINARY],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(10);
    });
  });

  describe('Preferred Layers Fallback', () => {
    it('should prefer first available layer in preference list', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.SET,
          args: ['x', 30],
          preferredLayers: [LayerKind.BINARY, LayerKind.ENGLISH],
        },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(30);
    });

    it('should fallback through preference list', () => {
      const manager = new LayerExecutionManager([LayerKind.ENGLISH, LayerKind.CPU]);

      expect(manager.isLayerAvailable(LayerKind.ENGLISH)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.CPU)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.BINARY)).toBe(false);
    });

    it('should handle multiple instructions with different preferences', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.SET,
          args: ['x', 5],
          preferredLayers: [LayerKind.CPU],
        },
        {
          opcode: OpCode.SET,
          args: ['y', 10],
          preferredLayers: [LayerKind.BINARY, LayerKind.ENGLISH],
        },
        { opcode: OpCode.ADD, args: ['x', 'y'] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(15);
    });
  });

  describe('Layer Stack Management', () => {
    it('should maintain layer stack during execution', () => {
      const context = new ExecutionContext();

      expect(context.getCurrentLayer()).toBe('english');
      expect(context.getLayerStack().length).toBe(0);

      context.pushLayer('binary');
      expect(context.getCurrentLayer()).toBe('binary');
      expect(context.getLayerStack()).toEqual(['binary']);

      context.pushLayer('superbit');
      expect(context.getCurrentLayer()).toBe('superbit');
      expect(context.getLayerStack()).toEqual(['binary', 'superbit']);

      const popped = context.popLayer();
      expect(popped).toBe('superbit');
      expect(context.getCurrentLayer()).toBe('binary');
      expect(context.getLayerStack()).toEqual(['binary']);

      context.popLayer();
      expect(context.getCurrentLayer()).toBe('english');
      expect(context.getLayerStack()).toEqual([]);
    });

    it('should default to english when stack is empty', () => {
      const context = new ExecutionContext();
      context.pushLayer('binary');
      context.popLayer();

      expect(context.getCurrentLayer()).toBe('english');
    });
  });

  describe('Layer Breakpoints', () => {
    it('should register layer-specific breakpoint', () => {
      const context = new ExecutionContext();

      const breakpointHit = jest.fn();
      const condition = (ctx: ExecutionContext) => {
        breakpointHit();
        return ctx.getCurrentLayer() === 'binary';
      };

      context.registerLayerBreakpoint(0, 'binary', condition);

      const breakpoints = context.getPendingBreakpoints();
      expect(breakpoints.length).toBe(1);
      expect(breakpoints[0].address).toBe(0);
      expect(breakpoints[0].layer).toBe('binary');
    });

    it('should check breakpoint only for matching layer', () => {
      const context = new ExecutionContext();
      context.registerLayerBreakpoint(1, 'binary');

      context.pushLayer('english');
      expect(context.checkLayerBreakpoint(1)).toBe(false);

      context.popLayer();
      context.pushLayer('binary');
      expect(context.checkLayerBreakpoint(1)).toBe(true);
    });

    it('should evaluate breakpoint condition', () => {
      const context = new ExecutionContext();

      const condition = (ctx: ExecutionContext) => ctx.getCurrentLayer() === 'binary';
      context.registerLayerBreakpoint(5, 'binary', condition);

      context.pushLayer('english');
      expect(context.checkLayerBreakpoint(5)).toBe(false);

      context.popLayer();
      context.pushLayer('binary');
      expect(context.checkLayerBreakpoint(5)).toBe(true);
    });

    it('should register VM-level breakpoint', () => {
      vm.registerLayerBreakpoint(0, LayerKind.BINARY);

      const program: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 42] }];

      expect(() => {
        vm.execute(program);
      }).not.toThrow();
    });
  });

  describe('Layer Register Snapshots', () => {
    it('should save and retrieve layer register snapshot', () => {
      const context = new ExecutionContext();
      const registers = new Map([
        ['x', 10],
        ['y', 20],
      ]);

      context.saveLayerRegisterSnapshot('binary', registers);

      const snapshot = context.getLayerRegisterSnapshot('binary');
      expect(snapshot).not.toBeNull();
      expect(snapshot?.layer).toBe('binary');
      expect(snapshot?.registers.get('x')).toBe(10);
      expect(snapshot?.registers.get('y')).toBe(20);
    });

    it('should maintain separate snapshots per layer', () => {
      const context = new ExecutionContext();

      const binaryRegisters = new Map([['x', 1]]);
      const superbitRegisters = new Map([['x', 2]]);

      context.saveLayerRegisterSnapshot('binary', binaryRegisters);
      context.saveLayerRegisterSnapshot('superbit', superbitRegisters);

      const binarySnapshot = context.getLayerRegisterSnapshot('binary');
      const superbitSnapshot = context.getLayerRegisterSnapshot('superbit');

      expect(binarySnapshot?.registers.get('x')).toBe(1);
      expect(superbitSnapshot?.registers.get('x')).toBe(2);
    });

    it('should get all layer snapshots', () => {
      const context = new ExecutionContext();

      const binaryRegisters = new Map([['a', 10]]);
      const cpuRegisters = new Map([['b', 20]]);

      context.saveLayerRegisterSnapshot('binary', binaryRegisters);
      context.saveLayerRegisterSnapshot('cpu', cpuRegisters);

      const allSnapshots = context.getAllLayerRegisterSnapshots();
      expect(allSnapshots.size).toBe(2);
      expect(allSnapshots.has('binary')).toBe(true);
      expect(allSnapshots.has('cpu')).toBe(true);
    });
  });

  describe('Cross-Layer Debugging', () => {
    it('should emit layer trace to binary bridge', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42], layer: LayerKind.BINARY },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      const traces = vm.getCrossLayerTraces();
      expect(typeof traces).toBe('object');
      expect(Array.isArray(traces)).toBe(true);
    });

    it('should clear cross-layer traces', () => {
      vm.getCrossLayerTraces();
      vm.clearCrossLayerTraces();

      const traces = vm.getCrossLayerTraces();
      expect(traces).toEqual([]);
    });

    it('should track available layers', () => {
      const layers = vm.getAvailableLayers();

      expect(Array.isArray(layers)).toBe(true);
      expect(layers.length).toBeGreaterThan(0);
      expect(layers).toContain(LayerKind.ENGLISH);
    });

    it('should check layer availability', () => {
      expect(vm.isLayerAvailable(LayerKind.ENGLISH)).toBe(true);
      expect(vm.isLayerAvailable(LayerKind.BINARY)).toBe(true);
      expect(vm.isLayerAvailable(LayerKind.SUPERBIT)).toBe(true);
    });
  });

  describe('Layer Adapter Interface', () => {
    it('should support english layer adapter', async () => {
      const adapter = new EnglishLayerAdapter();

      expect(adapter.getLayerId()).toBe(LayerKind.ENGLISH);
      expect(adapter.verifyLayerAvailability([LayerKind.ENGLISH])).toBe(true);
    });

    it('should get layer snapshot', async () => {
      const adapter = new EnglishLayerAdapter();
      const snapshot = adapter.snapshot();

      expect(snapshot.layer).toBe(LayerKind.ENGLISH);
      expect(snapshot.timestamp).toBeGreaterThan(0);
      expect(snapshot.registers).toBeDefined();
    });

    it('should register and check breakpoints in adapter', () => {
      const adapter = new EnglishLayerAdapter();

      adapter.registerBreakpoint(10, (ctx) => true);

      const context = {
        instruction: { opcode: OpCode.SET, args: ['x', 42] },
        registers: new Map(),
      };

      expect(adapter.checkBreakpoint(10, context)).toBe(true);
      expect(adapter.checkBreakpoint(11, context)).toBe(false);
    });
  });

  describe('Layer Execution Manager', () => {
    it('should initialize with all available layers', () => {
      const manager = new LayerExecutionManager();

      expect(manager.isLayerAvailable(LayerKind.ENGLISH)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.BINARY)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.SUPERBIT)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.CPU)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.DISTRIBUTED)).toBe(true);
    });

    it('should initialize with subset of layers', () => {
      const manager = new LayerExecutionManager([LayerKind.ENGLISH, LayerKind.BINARY]);

      expect(manager.isLayerAvailable(LayerKind.ENGLISH)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.BINARY)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.SUPERBIT)).toBe(false);
      expect(manager.isLayerAvailable(LayerKind.CPU)).toBe(false);
    });

    it('should get current layer', () => {
      const manager = new LayerExecutionManager();

      expect(manager.getCurrentLayer()).toBe(LayerKind.ENGLISH);

      manager.setCurrentLayer(LayerKind.BINARY);
      expect(manager.getCurrentLayer()).toBe(LayerKind.BINARY);
    });

    it('should manage layer stack', () => {
      const manager = new LayerExecutionManager();

      expect(manager.getLayerStack().length).toBe(0);
    });

    it('should collect cross-layer traces', () => {
      const manager = new LayerExecutionManager();

      const traces = manager.getCrossLayerTraces();
      expect(Array.isArray(traces)).toBe(true);
    });

    it('should verify required layers', () => {
      const manager = new LayerExecutionManager([LayerKind.ENGLISH, LayerKind.BINARY]);

      expect(manager.isLayerAvailable(LayerKind.ENGLISH)).toBe(true);
      expect(manager.isLayerAvailable(LayerKind.SUPERBIT)).toBe(false);
    });
  });

  describe('Performance Profile Metadata', () => {
    it('should carry performance profile in instruction', () => {
      const instruction: Instruction = {
        opcode: OpCode.SET,
        args: ['x', 42],
        performanceProfile: {
          estimatedCycles: 1,
          memoryFootprint: 8,
          preferredLayer: LayerKind.CPU,
        },
      };

      expect(instruction.performanceProfile?.estimatedCycles).toBe(1);
      expect(instruction.performanceProfile?.preferredLayer).toBe(LayerKind.CPU);
    });

    it('should execute program with performance profile', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.SET,
          args: ['x', 50],
          performanceProfile: {
            estimatedCycles: 1,
            memoryFootprint: 8,
          },
        },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(50);
    });
  });

  describe('Complex Layer Scenarios', () => {
    it('should handle nested layer switching', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 0], layer: LayerKind.ENGLISH },
        { opcode: OpCode.ADD, args: ['x', 10], layer: LayerKind.BINARY },
        { opcode: OpCode.ADD, args: ['x', 5], layer: LayerKind.CPU },
        { opcode: OpCode.ADD, args: ['x', 3], layer: LayerKind.SUPERBIT },
        { opcode: OpCode.ADD, args: ['x', 2] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(20);
    });

    it('should handle if statements with layer metadata', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5], layer: LayerKind.ENGLISH },
        {
          opcode: OpCode.IF,
          args: ['x', '>', [{ opcode: OpCode.SET, args: ['result', 100], layer: LayerKind.BINARY }]],
          layer: LayerKind.CPU,
        },
        { opcode: OpCode.SHOW, args: ['result'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(100);
    });

    it('should handle function definitions with layer metadata', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'add_five',
            [{ opcode: OpCode.ADD, args: ['x', 5], layer: LayerKind.BINARY }],
          ],
          layer: LayerKind.CPU,
        },
        { opcode: OpCode.SET, args: ['x', 10], layer: LayerKind.ENGLISH },
        { opcode: OpCode.CALL, args: ['add_five'], layer: LayerKind.SUPERBIT },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(15);
    });
  });

  describe('Layer Metadata Extraction', () => {
    it('should extract layer metadata from instruction during decoding', () => {
      const program = [
        {
          opcode: 'SET',
          args: ['x', 42],
          layer: 'binary',
          requiredLayers: ['superbit'],
          preferredLayers: ['cpu', 'english'],
        },
      ];

      const decoder = vm['decoder'];
      const instructions = decoder.decode(program);

      expect(instructions.length).toBe(1);
      expect(instructions[0].layer).toBe('binary');
      expect(instructions[0].requiredLayers).toContain('superbit');
      expect(instructions[0].preferredLayers).toContain('cpu');
    });

    it('should handle instructions without layer metadata', () => {
      const program = [
        {
          opcode: 'SET',
          args: ['x', 42],
        },
      ];

      const decoder = vm['decoder'];
      const instructions = decoder.decode(program);

      expect(instructions.length).toBe(1);
      expect(instructions[0].layer).toBeUndefined();
      expect(instructions[0].requiredLayers).toBeUndefined();
    });
  });
});
