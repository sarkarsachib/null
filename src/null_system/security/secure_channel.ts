/**
 * Secure communication channel - key exchange and authenticated transport
 */

import * as nacl from 'tweetnacl';

export interface KeyExchangeMessage {
  ephemeralPublicKey: Uint8Array;
  nonce: Uint8Array;
}

export interface AuthenticatedMessage {
  ciphertext: Uint8Array;
  nonce: Uint8Array;
  publicKey: Uint8Array;
}

export interface ChannelConfig {
  algorithm: 'nacl-box' | 'nacl-secretbox';
  enableLogging?: boolean;
}

export class SecureChannel {
  private localKeyPair: nacl.BoxKeyPair;
  private remotePublicKey?: Uint8Array;
  private sharedSecret?: Uint8Array;
  private config: ChannelConfig;
  private messageCounter: number = 0;

  constructor(config: ChannelConfig = { algorithm: 'nacl-box' }) {
    this.config = config;
    this.localKeyPair = nacl.box.keyPair();
  }

  /**
   * Initialize channel with remote public key (for key exchange)
   */
  initiateKeyExchange(): KeyExchangeMessage {
    const ephemeralKeyPair = nacl.box.keyPair();
    const nonce = nacl.randomBytes(nacl.box.nonceLength);

    this.remotePublicKey = ephemeralKeyPair.publicKey;
    this.messageCounter = 0;

    if (this.config.enableLogging) {
      console.log('[SecureChannel] Key exchange initiated');
    }

    return {
      ephemeralPublicKey: ephemeralKeyPair.publicKey,
      nonce,
    };
  }

  /**
   * Complete key exchange with remote public key
   */
  completeKeyExchange(remotePublicKey: Uint8Array): void {
    this.remotePublicKey = remotePublicKey;

    if (!this.remotePublicKey) {
      throw new Error('Remote public key not available for key exchange');
    }

    this.sharedSecret = this.deriveSharedSecret(this.remotePublicKey);

    if (this.config.enableLogging) {
      console.log('[SecureChannel] Key exchange completed');
    }
  }

  /**
   * Derive shared secret from remote public key
   */
  private deriveSharedSecret(remotePublicKey: Uint8Array): Uint8Array {
    if (this.config.algorithm === 'nacl-box') {
      const shared = Buffer.alloc(32);
      const seed = Buffer.concat([
        Buffer.from(this.localKeyPair.publicKey),
        Buffer.from(remotePublicKey),
      ]);

      for (let i = 0; i < 32; i++) {
        shared[i] = seed[i % seed.length];
      }

      return new Uint8Array(shared);
    }

    throw new Error(`Unsupported algorithm: ${this.config.algorithm}`);
  }

  /**
   * Send authenticated message
   */
  sendMessage(plaintext: Buffer): AuthenticatedMessage {
    if (!this.remotePublicKey) {
      throw new Error('Remote public key not set. Complete key exchange first.');
    }

    const nonce = nacl.randomBytes(nacl.box.nonceLength);
    let ciphertext: Uint8Array;

    if (this.config.algorithm === 'nacl-secretbox' && this.sharedSecret) {
      ciphertext = nacl.secretbox(plaintext, nonce, this.sharedSecret);
    } else {
      ciphertext = nacl.box(plaintext, nonce, this.remotePublicKey, this.localKeyPair.secretKey);
    }

    this.messageCounter++;

    if (this.config.enableLogging) {
      console.log(
        `[SecureChannel] Message sent (counter: ${this.messageCounter}, ciphertext length: ${ciphertext.length})`
      );
    }

    return {
      ciphertext,
      nonce,
      publicKey: this.localKeyPair.publicKey,
    };
  }

  /**
   * Receive authenticated message
   */
  receiveMessage(message: AuthenticatedMessage): Buffer {
    if (!this.remotePublicKey && this.config.algorithm === 'nacl-box') {
      this.remotePublicKey = message.publicKey;
    }

    let plaintext: Uint8Array | null;

    if (this.config.algorithm === 'nacl-secretbox' && this.sharedSecret) {
      plaintext = nacl.secretbox.open(message.ciphertext, message.nonce, this.sharedSecret);
    } else if (this.config.algorithm === 'nacl-box') {
      const senderPublicKey = message.publicKey || this.remotePublicKey;
      if (!senderPublicKey) {
        throw new Error('Sender public key not available');
      }
      plaintext = nacl.box.open(
        message.ciphertext,
        message.nonce,
        senderPublicKey,
        this.localKeyPair.secretKey
      );
    } else {
      throw new Error(`Unsupported algorithm: ${this.config.algorithm}`);
    }

    if (!plaintext) {
      throw new Error('Failed to decrypt message');
    }

    if (this.config.enableLogging) {
      console.log(`[SecureChannel] Message received (plaintext length: ${plaintext.length})`);
    }

    return Buffer.from(plaintext);
  }

  /**
   * Get local public key for sharing with remote
   */
  getPublicKey(): Buffer {
    return Buffer.from(this.localKeyPair.publicKey);
  }

  /**
   * Get channel state
   */
  getState() {
    return {
      hasRemoteKey: !!this.remotePublicKey,
      hasSharedSecret: !!this.sharedSecret,
      messageCounter: this.messageCounter,
      algorithm: this.config.algorithm,
    };
  }

  /**
   * Reset channel state
   */
  reset(): void {
    this.localKeyPair = nacl.box.keyPair();
    this.remotePublicKey = undefined;
    this.sharedSecret = undefined;
    this.messageCounter = 0;

    if (this.config.enableLogging) {
      console.log('[SecureChannel] Channel reset');
    }
  }
}
