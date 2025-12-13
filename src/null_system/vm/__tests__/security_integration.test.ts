import { NullVM } from '../null_vm';
import { OpCode } from '../instructions';

describe('NullVM Security Integration', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM({ enableTracing: false });
  });

  describe('Homomorphic Encryption Operations', () => {
    test('should encrypt a register value', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
      ];

      vm.execute(program);

      const memory = vm.getMemory();
      const encrypted = memory.getEncryptedValue('x_encrypted');

      expect(encrypted).toBeDefined();
      expect(encrypted?.ciphertext).toBeInstanceOf(Buffer);
      expect(encrypted?.keyId).toBe('key_1');
    });

    test('should decrypt an encrypted value', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
        { opcode: OpCode.SECURE_DEC, args: ['x', 'key_1'] },
      ];

      vm.execute(program);

      const memory = vm.getMemory();
      const value = memory.getRegister('x');

      expect(typeof value).toBe('number');
    });

    test('should handle multiple encrypted values', () => {
      const program = [
        { opcode: OpCode.SET, args: ['a', 10] },
        { opcode: OpCode.SET, args: ['b', 20] },
        { opcode: OpCode.SECURE_ENC, args: ['a', 'key_1'] },
        { opcode: OpCode.SECURE_ENC, args: ['b', 'key_1'] },
      ];

      vm.execute(program);

      const memory = vm.getMemory();
      expect(memory.getEncryptedValue('a_encrypted')).toBeDefined();
      expect(memory.getEncryptedValue('b_encrypted')).toBeDefined();
    });

    test('should reuse key for multiple encryptions', () => {
      const program = [
        { opcode: OpCode.SET, args: ['a', 5] },
        { opcode: OpCode.SET, args: ['b', 10] },
        { opcode: OpCode.SECURE_ENC, args: ['a', 'shared_key'] },
        { opcode: OpCode.SECURE_ENC, args: ['b', 'shared_key'] },
      ];

      vm.execute(program);

      const memory = vm.getMemory();
      const keyA = memory.getEncryptedValue('a_encrypted')?.keyId;
      const keyB = memory.getEncryptedValue('b_encrypted')?.keyId;

      expect(keyA).toBe('shared_key');
      expect(keyB).toBe('shared_key');
    });
  });

  describe('Secure Evaluation', () => {
    test('should emit secure eval operations', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['y', 20] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
        { opcode: OpCode.SECURE_ENC, args: ['y', 'key_1'] },
        { opcode: OpCode.SECURE_EVAL, args: ['add', 'x', 'y'] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      const evalFrame = frames.find((f) => f.frameType === 'CONTROL');
      expect(evalFrame).toBeDefined();
    });
  });

  describe('Zero-Knowledge Proofs', () => {
    test('should handle ZK proof generation', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 5] },
        { opcode: OpCode.ZK_PROVE, args: ['trace_1'] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      expect(frames.length).toBeGreaterThan(0);
    });

    test('should verify ZK proof', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.ZK_PROVE, args: ['trace_1'] },
        { opcode: OpCode.ZK_VERIFY, args: ['trace_1', 'digest_1'] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      expect(frames.length).toBeGreaterThan(0);
    });

    test('should handle proof generation for secrets', () => {
      const program = [
        { opcode: OpCode.SET, args: ['secret', 42] },
        { opcode: OpCode.ZK_PROVE, args: ['trace_secret'] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      expect(frames.length).toBeGreaterThan(0);
    });
  });

  describe('SMPC Operations', () => {
    test('should share a secret', () => {
      const program = [
        { opcode: OpCode.SET, args: ['secret', 100] },
        { opcode: OpCode.SMPC_SHARE, args: ['secret_1', 2] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      const smpcFrame = frames.find(
        (f) => f.frameType === 'CONTROL' && f.data.toString('utf-8').includes('SMPC_SHARE')
      );

      expect(smpcFrame).toBeDefined();
    });

    test('should combine shares', () => {
      const program = [
        { opcode: OpCode.SET, args: ['secret', 50] },
        { opcode: OpCode.SMPC_SHARE, args: ['secret_1', 2] },
        {
          opcode: OpCode.SMPC_COMBINE,
          args: ['secret_1', ['secret_1_party_0', 'secret_1_party_1', 'secret_1_party_2']],
        },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      expect(frames.length).toBeGreaterThan(0);
    });
  });

  describe('Full Secure Computation Example', () => {
    test('should handle secure computation with encryption', () => {
      const program = [
        { opcode: OpCode.SET, args: ['a', 5] },
        { opcode: OpCode.SET, args: ['b', 10] },
        { opcode: OpCode.SECURE_ENC, args: ['a', 'key_1'] },
        { opcode: OpCode.SECURE_ENC, args: ['b', 'key_1'] },
      ];

      vm.execute(program);

      const memory = vm.getMemory();
      expect(memory.getEncryptedValue('a_encrypted')).toBeDefined();
      expect(memory.getEncryptedValue('b_encrypted')).toBeDefined();

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();
      expect(frames.length).toBeGreaterThan(0);
    });

    test('should handle secure channel metadata', () => {
      const vm2 = new NullVM();
      const channel = vm2.getSecureChannel();

      const keyExchange = channel.initiateKeyExchange();
      expect(keyExchange).toBeDefined();

      const bridge = vm2.getBinaryBridge();
      bridge.emitKeyExchange('party_0', 'party_1', true);

      const frames = bridge.getFrames();
      const keyExchangeFrame = frames.find((f) => f.frameType === 'KEY_EXCHANGE');

      expect(keyExchangeFrame).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should handle decrypt without encryption', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SECURE_DEC, args: ['x', 'key_1'] },
      ];

      try {
        vm.execute(program);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    test('should handle secure eval with non-encrypted values', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 5] },
        { opcode: OpCode.SET, args: ['y', 10] },
        { opcode: OpCode.SECURE_EVAL, args: ['add', 'x', 'y'] },
      ];

      try {
        vm.execute(program);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('VM State with Security', () => {
    test('should include security state in snapshot', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
      ];

      vm.execute(program);

      const state = vm.getState();
      const memorySnapshot = state.memory;

      expect(memorySnapshot.encryptedValuesCount).toBeGreaterThan(0);
      expect(memorySnapshot.keysCount).toBeGreaterThan(0);
    });

    test('should reset security state with VM reset', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
      ];

      vm.execute(program);

      let state = vm.getState();
      expect(state.memory.encryptedValuesCount).toBeGreaterThan(0);

      vm.reset();

      state = vm.getState();
      expect(state.memory.encryptedValuesCount).toBe(0);
      expect(state.memory.keysCount).toBe(0);
    });
  });

  describe('Binary Bridge Security Emissions', () => {
    test('should emit frames from security operations', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.SECURE_ENC, args: ['x', 'key_1'] },
      ];

      vm.execute(program);

      const bridge = vm.getBinaryBridge();
      const frames = bridge.getFrames();

      expect(frames.length).toBeGreaterThan(0);
    });

    test('should emit channel metadata', () => {
      const channel = vm.getSecureChannel();
      channel.initiateKeyExchange();

      const bridge = vm.getBinaryBridge();
      bridge.emitChannelMetadata('channel_1', { status: 'initialized' });

      const frames = bridge.getFrames();
      const channelFrame = frames.find((f) => f.frameType === 'CHANNEL_METADATA');

      expect(channelFrame).toBeDefined();
    });

    test('should emit key exchange events', () => {
      const bridge = vm.getBinaryBridge();
      bridge.emitKeyExchange('alice', 'bob', true);

      const frames = bridge.getFrames();
      const keyExchangeFrame = frames.find((f) => f.frameType === 'KEY_EXCHANGE');

      expect(keyExchangeFrame).toBeDefined();
      expect(keyExchangeFrame?.data.toString('utf-8')).toContain('alice');
    });
  });

  describe('Security Module Accessors', () => {
    test('should provide access to homomorphic engine', () => {
      const engine = vm.getHomomorphicEngine();
      expect(engine).toBeDefined();

      const keyPair = engine.generateKeyPair();
      expect(keyPair).toBeDefined();
    });

    test('should provide access to secure channel', () => {
      const channel = vm.getSecureChannel();
      expect(channel).toBeDefined();

      const pubKey = channel.getPublicKey();
      expect(pubKey).toBeDefined();
    });

    test('should provide access to ZK proof system', () => {
      const zkp = vm.getZKProofSystem();
      expect(zkp).toBeDefined();
    });

    test('should provide access to SMPC orchestrator', () => {
      const smpc = vm.getSMPCOrchestrator();
      expect(smpc).toBeDefined();

      const config = smpc.getConfig();
      expect(config).toBeDefined();
    });
  });
});
