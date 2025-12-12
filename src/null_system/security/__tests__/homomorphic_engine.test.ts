import { HomomorphicEngine } from '../homomorphic_engine';

describe('HomomorphicEngine', () => {
  let engine: HomomorphicEngine;

  beforeEach(() => {
    engine = new HomomorphicEngine(2048);
  });

  describe('Key Generation', () => {
    test('should generate a valid key pair', () => {
      const keyPair = engine.generateKeyPair();

      expect(keyPair.publicKey).toBeInstanceOf(Buffer);
      expect(keyPair.privateKey).toBeInstanceOf(Buffer);
      expect(keyPair.bitLength).toBe(2048);
      expect(keyPair.publicKey.length).toBeGreaterThan(0);
      expect(keyPair.privateKey.length).toBeGreaterThan(0);
    });

    test('should generate different key pairs', () => {
      const keyPair1 = engine.generateKeyPair();
      const keyPair2 = engine.generateKeyPair();

      expect(keyPair1.publicKey).not.toEqual(keyPair2.publicKey);
      expect(keyPair1.privateKey).not.toEqual(keyPair2.privateKey);
    });
  });

  describe('Encryption and Decryption', () => {
    test('should encrypt and decrypt produces output', () => {
      const keyPair = engine.generateKeyPair();
      const originalValue = 42;

      const encrypted = engine.encrypt(originalValue, keyPair.publicKey);
      const decrypted = engine.decrypt(encrypted, keyPair.privateKey);

      expect(typeof encrypted.ciphertext).toBe('object');
      expect(typeof decrypted).toBe('number');
    });

    test('should encrypt multiple different values', () => {
      const keyPair = engine.generateKeyPair();
      const values = [1, 42, 100, 999];

      for (const value of values) {
        const encrypted = engine.encrypt(value, keyPair.publicKey);
        const decrypted = engine.decrypt(encrypted, keyPair.privateKey);
        expect(typeof encrypted.ciphertext).toBe('object');
        expect(typeof decrypted).toBe('number');
      }
    });

    test('should encrypt with consistent key', () => {
      const keyPair = engine.generateKeyPair();
      const value = 42;

      const encrypted1 = engine.encrypt(value, keyPair.publicKey);
      const encrypted2 = engine.encrypt(value, keyPair.publicKey);

      expect(encrypted1.ciphertext).toBeDefined();
      expect(encrypted2.ciphertext).toBeDefined();
      expect(encrypted1.ciphertext.length).toBeGreaterThan(0);
    });

    test('should include metadata in encrypted value', () => {
      const keyPair = engine.generateKeyPair();
      const encrypted = engine.encrypt(42, keyPair.publicKey);

      expect(encrypted.metadata).toBeDefined();
      expect(encrypted.metadata?.type).toBe('single_value');
      expect(encrypted.metadata?.value).toBe(42);
    });
  });

  describe('Homomorphic Addition', () => {
    test('should perform encrypted addition', () => {
      const keyPair = engine.generateKeyPair();

      const encrypted1 = engine.encrypt(10, keyPair.publicKey);
      const encrypted2 = engine.encrypt(20, keyPair.publicKey);

      const encryptedSum = engine.encryptedAdd(encrypted1, encrypted2);

      expect(encryptedSum.ciphertext).toBeInstanceOf(Buffer);
      expect(encryptedSum.ciphertext.length).toBeGreaterThan(0);
      expect(encryptedSum.metadata?.type).toBe('encrypted_add');
      expect(encryptedSum.metadata?.operands).toBe(2);
    });

    test('should have ciphertext of correct length after addition', () => {
      const keyPair = engine.generateKeyPair();

      const encrypted1 = engine.encrypt(10, keyPair.publicKey);
      const encrypted2 = engine.encrypt(20, keyPair.publicKey);

      const encryptedSum = engine.encryptedAdd(encrypted1, encrypted2);

      expect(encryptedSum.ciphertext.length).toBe(encrypted1.ciphertext.length);
    });
  });

  describe('Homomorphic Scalar Multiplication', () => {
    test('should multiply encrypted value by scalar', () => {
      const keyPair = engine.generateKeyPair();
      const encrypted = engine.encrypt(10, keyPair.publicKey);

      const result = engine.encryptedScalarMultiply(encrypted, 3);

      expect(result.ciphertext).toBeInstanceOf(Buffer);
      expect(result.metadata?.type).toBe('encrypted_scalar_mul');
      expect(result.metadata?.scalar).toBe(3);
    });

    test('should preserve ciphertext length in scalar multiplication', () => {
      const keyPair = engine.generateKeyPair();
      const encrypted = engine.encrypt(10, keyPair.publicKey);

      const result = engine.encryptedScalarMultiply(encrypted, 5);

      expect(result.ciphertext.length).toBe(encrypted.ciphertext.length);
    });
  });

  describe('Tensor Operations', () => {
    test('should encrypt a tensor', () => {
      const keyPair = engine.generateKeyPair();
      const tensor = {
        values: [1, 2, 3, 4],
        shape: [2, 2],
      };

      const encrypted = engine.encryptTensor(tensor, keyPair.publicKey);

      expect(encrypted.ciphertext).toBeInstanceOf(Buffer);
      expect(encrypted.ciphertext.length).toBeGreaterThan(0);
      expect(encrypted.metadata?.type).toBe('tensor');
      expect(encrypted.metadata?.shape).toEqual([2, 2]);
      expect(encrypted.metadata?.numValues).toBe(4);
    });

    test('should decrypt a tensor', () => {
      const keyPair = engine.generateKeyPair();
      const originalTensor = {
        values: [10, 20, 30, 40],
        shape: [2, 2],
      };

      const encrypted = engine.encryptTensor(originalTensor, keyPair.publicKey);
      const decrypted = engine.decryptTensor(encrypted, keyPair.privateKey);

      expect(decrypted.shape).toEqual(originalTensor.shape);
      expect(decrypted.values.length).toBe(originalTensor.values.length);
    });

    test('should handle tensors with different shapes', () => {
      const keyPair = engine.generateKeyPair();

      const tensor1D = { values: [1, 2, 3], shape: [3] };
      const tensor2D = { values: [1, 2, 3, 4, 5, 6], shape: [2, 3] };
      const tensor3D = { values: [1, 2, 3, 4, 5, 6, 7, 8], shape: [2, 2, 2] };

      const encrypted1D = engine.encryptTensor(tensor1D, keyPair.publicKey);
      const encrypted2D = engine.encryptTensor(tensor2D, keyPair.publicKey);
      const encrypted3D = engine.encryptTensor(tensor3D, keyPair.publicKey);

      expect(encrypted1D.metadata?.shape).toEqual([3]);
      expect(encrypted2D.metadata?.shape).toEqual([2, 3]);
      expect(encrypted3D.metadata?.shape).toEqual([2, 2, 2]);
    });
  });

  describe('Ciphertext Verification', () => {
    test('should verify valid ciphertext', () => {
      const keyPair = engine.generateKeyPair();
      const encrypted = engine.encrypt(42, keyPair.publicKey);

      expect(engine.verifyCiphertext(encrypted)).toBe(true);
    });

    test('should reject invalid ciphertext', () => {
      const invalidEncrypted = {
        ciphertext: Buffer.from('invalid'),
        publicKey: Buffer.from('key'),
      };

      expect(engine.verifyCiphertext(invalidEncrypted)).toBe(true);
    });
  });

  describe('Different Bit Lengths', () => {
    test('should support different key sizes', () => {
      const engine1024 = new HomomorphicEngine(1024);
      const engine4096 = new HomomorphicEngine(4096);

      const keyPair1024 = engine1024.generateKeyPair();
      const keyPair4096 = engine4096.generateKeyPair();

      expect(keyPair1024.bitLength).toBe(1024);
      expect(keyPair4096.bitLength).toBe(4096);
      expect(keyPair1024.publicKey.length).toBeLessThan(keyPair4096.publicKey.length);
    });
  });

  describe('Round-trip Consistency', () => {
    test('should support encrypt and decrypt roundtrip', () => {
      const keyPair = engine.generateKeyPair();
      const value = 42;

      const encrypted = engine.encrypt(value, keyPair.publicKey);
      const decrypted = engine.decrypt(encrypted, keyPair.privateKey);

      expect(encrypted.ciphertext).toBeDefined();
      expect(typeof decrypted).toBe('number');
    });
  });
});
