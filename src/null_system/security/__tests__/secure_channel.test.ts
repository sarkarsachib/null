import { SecureChannel } from '../secure_channel';

describe('SecureChannel', () => {
  let channel1: SecureChannel;
  let channel2: SecureChannel;

  beforeEach(() => {
    channel1 = new SecureChannel({ algorithm: 'nacl-box' });
    channel2 = new SecureChannel({ algorithm: 'nacl-box' });
  });

  describe('Initialization', () => {
    test('should create a secure channel', () => {
      expect(channel1).toBeDefined();
    });

    test('should have a public key', () => {
      const pubKey = channel1.getPublicKey();
      expect(pubKey).toBeInstanceOf(Buffer);
      expect(pubKey.length).toBeGreaterThan(0);
    });

    test('should initialize with default config', () => {
      const channel = new SecureChannel();
      const state = channel.getState();

      expect(state.algorithm).toBe('nacl-box');
      expect(state.hasRemoteKey).toBe(false);
      expect(state.messageCounter).toBe(0);
    });
  });

  describe('Key Exchange', () => {
    test('should initiate key exchange', () => {
      const message = channel1.initiateKeyExchange();

      expect(message.ephemeralPublicKey).toBeInstanceOf(Uint8Array);
      expect(message.nonce).toBeInstanceOf(Uint8Array);
      expect(message.nonce.length).toBeGreaterThan(0);
    });

    test('should complete key exchange', () => {
      const pubKey2 = channel2.getPublicKey();
      channel1.completeKeyExchange(pubKey2);

      const state = channel1.getState();
      expect(state.hasRemoteKey).toBe(true);
    });

    test('should establish shared secret after key exchange', () => {
      const pubKey1 = channel1.getPublicKey();
      const pubKey2 = channel2.getPublicKey();

      channel1.completeKeyExchange(pubKey2);
      channel2.completeKeyExchange(pubKey1);

      const state1 = channel1.getState();
      const state2 = channel2.getState();

      expect(state1.hasRemoteKey).toBe(true);
      expect(state2.hasRemoteKey).toBe(true);
    });
  });

  describe('Message Encryption and Decryption', () => {
    beforeEach(() => {
      const pubKey1 = channel1.getPublicKey();
      const pubKey2 = channel2.getPublicKey();

      channel1.completeKeyExchange(pubKey2);
      channel2.completeKeyExchange(pubKey1);
    });

    test('should send and receive message', () => {
      const plaintext = Buffer.from('Hello, World!', 'utf-8');
      const message = channel1.sendMessage(plaintext);

      expect(message.ciphertext).toBeInstanceOf(Uint8Array);
      expect(message.nonce).toBeInstanceOf(Uint8Array);
      expect(message.publicKey).toBeInstanceOf(Uint8Array);
    });

    test('should decrypt message sent from peer', () => {
      const plaintext = Buffer.from('Secret message', 'utf-8');
      const message = channel1.sendMessage(plaintext);

      const decrypted = channel2.receiveMessage(message);

      expect(decrypted).toEqual(plaintext);
    });

    test('should bidirectional communication', () => {
      const msg1 = Buffer.from('Message 1');
      const msg2 = Buffer.from('Message 2');

      const encrypted1 = channel1.sendMessage(msg1);
      const decrypted1 = channel2.receiveMessage(encrypted1);

      const encrypted2 = channel2.sendMessage(msg2);
      const decrypted2 = channel1.receiveMessage(encrypted2);

      expect(decrypted1).toEqual(msg1);
      expect(decrypted2).toEqual(msg2);
    });

    test('should increment message counter', () => {
      const state0 = channel1.getState();
      expect(state0.messageCounter).toBe(0);

      channel1.sendMessage(Buffer.from('msg1'));
      const state1 = channel1.getState();
      expect(state1.messageCounter).toBe(1);

      channel1.sendMessage(Buffer.from('msg2'));
      const state2 = channel1.getState();
      expect(state2.messageCounter).toBe(2);
    });

    test('should handle multiple messages', () => {
      const messages = [
        Buffer.from('msg1'),
        Buffer.from('msg2'),
        Buffer.from('msg3'),
      ];

      for (const plaintext of messages) {
        const encrypted = channel1.sendMessage(plaintext);
        const decrypted = channel2.receiveMessage(encrypted);
        expect(decrypted).toEqual(plaintext);
      }
    });
  });

  describe('Logging Configuration', () => {
    test('should support logging configuration', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

      const channelWithLogging = new SecureChannel({
        algorithm: 'nacl-box',
        enableLogging: true,
      });

      channelWithLogging.initiateKeyExchange();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[SecureChannel] Key exchange initiated')
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Channel Reset', () => {
    test('should reset channel state', () => {
      const pubKey2 = channel2.getPublicKey();
      channel1.completeKeyExchange(pubKey2);

      let state = channel1.getState();
      expect(state.hasRemoteKey).toBe(true);
      expect(state.messageCounter).toBeGreaterThan(-1);

      channel1.reset();

      state = channel1.getState();
      expect(state.hasRemoteKey).toBe(false);
      expect(state.messageCounter).toBe(0);
    });

    test('should generate new keys after reset', () => {
      const pubKey1 = channel1.getPublicKey();

      channel1.reset();

      const pubKey2 = channel1.getPublicKey();

      expect(pubKey1).not.toEqual(pubKey2);
    });
  });

  describe('Error Handling', () => {
    test('should reject message before key exchange', () => {
      const message = {
        ciphertext: new Uint8Array(32),
        nonce: new Uint8Array(24),
        publicKey: new Uint8Array(32),
      };

      expect(() => {
        channel1.receiveMessage(message);
      }).toThrow();
    });

    test('should handle corrupted ciphertext', () => {
      const pubKey1 = channel1.getPublicKey();
      const pubKey2 = channel2.getPublicKey();

      channel1.completeKeyExchange(pubKey2);
      channel2.completeKeyExchange(pubKey1);

      const plaintext = Buffer.from('Original');
      const encrypted = channel1.sendMessage(plaintext);

      encrypted.ciphertext[0] ^= 0xff;

      expect(() => {
        channel2.receiveMessage(encrypted);
      }).toThrow();
    });
  });

  describe('Supported Algorithms', () => {
    test('should support nacl-box algorithm', () => {
      const channel = new SecureChannel({ algorithm: 'nacl-box' });
      const state = channel.getState();

      expect(state.algorithm).toBe('nacl-box');
    });

    test('should support nacl-secretbox algorithm', () => {
      const channel = new SecureChannel({ algorithm: 'nacl-secretbox' });
      const state = channel.getState();

      expect(state.algorithm).toBe('nacl-secretbox');
    });
  });

  describe('Large Messages', () => {
    beforeEach(() => {
      const pubKey1 = channel1.getPublicKey();
      const pubKey2 = channel2.getPublicKey();

      channel1.completeKeyExchange(pubKey2);
      channel2.completeKeyExchange(pubKey1);
    });

    test('should handle large messages', () => {
      const largeMessage = Buffer.alloc(1024);
      largeMessage.fill('x');

      const encrypted = channel1.sendMessage(largeMessage);
      const decrypted = channel2.receiveMessage(encrypted);

      expect(decrypted).toEqual(largeMessage);
    });
  });
});
