/**
 * Binary bridge for emitting binary frames from VM execution
 */

export interface BinaryFrame {
  frameType: string;
  data: Buffer;
  timestamp: number;
}

export class BinaryBridge {
  private frames: BinaryFrame[] = [];

  /**
   * Emit a binary frame
   */
  emitFrame(frameType: string, data: Buffer): void {
    this.frames.push({
      frameType,
      data: Buffer.from(data),
      timestamp: Date.now(),
    });
  }

  /**
   * Emit output data (converts string to buffer)
   */
  emitOutput(label: string, value: number): void {
    const buffer = Buffer.alloc(64);
    let offset = 0;

    // Write label length and label
    const labelBuf = Buffer.from(label, 'utf-8');
    buffer.writeUInt32BE(labelBuf.length, offset);
    offset += 4;
    labelBuf.copy(buffer, offset);
    offset += labelBuf.length;

    // Write value
    buffer.writeInt32BE(value, offset);

    this.emitFrame('OUTPUT', buffer.slice(0, offset + 4));
  }

  /**
   * Emit a register state frame
   */
  emitRegisterState(name: string, value: number): void {
    const buffer = Buffer.alloc(64);
    let offset = 0;

    // Write register name length and name
    const nameBuf = Buffer.from(name, 'utf-8');
    buffer.writeUInt32BE(nameBuf.length, offset);
    offset += 4;
    nameBuf.copy(buffer, offset);
    offset += nameBuf.length;

    // Write value
    buffer.writeInt32BE(value, offset);

    this.emitFrame('REGISTER', buffer.slice(0, offset + 4));
  }

  /**
   * Emit a control flow event
   */
  emitControlFlow(event: string, data?: Record<string, unknown>): void {
    const jsonData = JSON.stringify({ event, ...data });
    const buffer = Buffer.from(jsonData, 'utf-8');
    this.emitFrame('CONTROL', buffer);
  }

  /**
   * Emit a proof transcript (for ZK proofs)
   */
  emitProofTranscript(proofId: string, transcript: string): void {
    const buffer = Buffer.alloc(256);
    let offset = 0;

    const idBuf = Buffer.from(proofId, 'utf-8');
    buffer.writeUInt32BE(idBuf.length, offset);
    offset += 4;
    idBuf.copy(buffer, offset);
    offset += idBuf.length;

    const transcriptBuf = Buffer.from(transcript.substring(0, 200), 'utf-8');
    buffer.writeUInt32BE(transcriptBuf.length, offset);
    offset += 4;
    transcriptBuf.copy(buffer, offset);
    offset += transcriptBuf.length;

    this.emitFrame('PROOF_TRANSCRIPT', buffer.slice(0, offset));
  }

  /**
   * Emit secure channel metadata
   */
  emitChannelMetadata(
    channelId: string,
    metadata: Record<string, unknown>
  ): void {
    const jsonData = JSON.stringify({
      channelId,
      ...metadata,
      timestamp: Date.now(),
    });
    const buffer = Buffer.from(jsonData, 'utf-8');
    this.emitFrame('CHANNEL_METADATA', buffer);
  }

  /**
   * Emit key exchange event
   */
  emitKeyExchange(party1: string, party2: string, success: boolean): void {
    const jsonData = JSON.stringify({
      event: 'KEY_EXCHANGE',
      party1,
      party2,
      success,
      timestamp: Date.now(),
    });
    const buffer = Buffer.from(jsonData, 'utf-8');
    this.emitFrame('KEY_EXCHANGE', buffer);
  }

  /**
   * Get all emitted frames
   */
  getFrames(): BinaryFrame[] {
    return [...this.frames];
  }

  /**
   * Clear all frames
   */
  clearFrames(): void {
    this.frames = [];
  }

  /**
   * Get frame count
   */
  getFrameCount(): number {
    return this.frames.length;
  }
}
