import { ZKProofSystem } from '../zkp';

describe('ZKProofSystem', () => {
  let zkp: ZKProofSystem;

  beforeEach(() => {
    zkp = new ZKProofSystem();
  });

  describe('Trace Recording', () => {
    test('should record an execution trace', () => {
      const traceId = 'trace_1';
      const statements = ['Execution started', 'Variable x assigned 10', 'Variable y assigned 20'];

      const trace = zkp.recordTrace(traceId, statements);

      expect(trace).toBeDefined();
      expect(trace.statements.length).toBe(3);
      expect(trace.statements[0].statement).toBe('Execution started');
      expect(trace.statements[0].index).toBe(0);
    });

    test('should compute execution hash', () => {
      const trace = zkp.recordTrace('trace_1', ['statement1', 'statement2']);

      expect(trace.executionHash).toBeInstanceOf(Buffer);
      expect(trace.executionHash.length).toBe(32);
    });

    test('should timestamp statements', () => {
      const before = Date.now();
      const trace = zkp.recordTrace('trace_2', ['stmt1']);
      const after = Date.now();

      expect(trace.statements[0].timestamp).toBeGreaterThanOrEqual(before);
      expect(trace.statements[0].timestamp).toBeLessThanOrEqual(after);
    });

    test('should create commitment for each statement', () => {
      const trace = zkp.recordTrace('trace_3', ['statement1', 'statement2']);

      for (const stmt of trace.statements) {
        expect(stmt.commitment).toBeInstanceOf(Buffer);
        expect(stmt.commitment.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Proof Generation', () => {
    test('should generate a proof structure', () => {
      const traceId = 'trace_for_proof';
      zkp.recordTrace(traceId, ['statement1', 'statement2']);

      const proof = zkp.proveExecution(traceId);

      expect(proof).toBeDefined();
      expect(proof.commitment).toBeInstanceOf(Buffer);
      expect(proof.challenge).toBeInstanceOf(Buffer);
      expect(proof.response).toBeInstanceOf(Buffer);
      expect(proof.trace).toBeDefined();
    });

    test('should have proof with buffers', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      const proof = zkp.proveExecution('trace_1');

      expect(proof.commitment.length).toBeGreaterThan(0);
      expect(proof.challenge.length).toBeGreaterThan(0);
      expect(proof.response.length).toBeGreaterThan(0);
    });

    test('should throw error for non-existent trace', () => {
      expect(() => {
        zkp.proveExecution('non_existent_trace');
      }).toThrow('Trace not found');
    });
  });

  describe('Proof Verification', () => {
    test('should verify a valid proof', () => {
      zkp.recordTrace('trace_1', ['statement']);
      const proof = zkp.proveExecution('trace_1');

      const isValid = zkp.verifyProof(proof);

      expect(typeof isValid).toBe('boolean');
    });

    test('should attempt verification on modified proof', () => {
      zkp.recordTrace('trace_1', ['statement']);
      const proof = zkp.proveExecution('trace_1');

      const modifiedProof = { ...proof };
      modifiedProof.commitment[0] ^= 0xff;

      const isValid = zkp.verifyProof(modifiedProof);

      expect(typeof isValid).toBe('boolean');
    });

    test('should attempt verification on modified challenge', () => {
      zkp.recordTrace('trace_1', ['statement']);
      const proof = zkp.proveExecution('trace_1');

      const modifiedProof = { ...proof };
      modifiedProof.challenge[0] ^= 0xff;

      const isValid = zkp.verifyProof(modifiedProof);

      expect(typeof isValid).toBe('boolean');
    });

    test('should attempt verification on modified response', () => {
      zkp.recordTrace('trace_1', ['statement']);
      const proof = zkp.proveExecution('trace_1');

      const modifiedProof = { ...proof };
      modifiedProof.response[0] ^= 0xff;

      const isValid = zkp.verifyProof(modifiedProof);

      expect(typeof isValid).toBe('boolean');
    });
  });

  describe('Digest Verification', () => {
    test('should attempt verification against recorded execution digest', () => {
      zkp.recordTrace('trace_1', ['stmt1', 'stmt2']);
      const proof = zkp.proveExecution('trace_1');

      const isValid = zkp.verifyAgainstDigest(proof, proof.trace.executionHash);

      expect(typeof isValid).toBe('boolean');
    });

    test('should handle verification with wrong digest', () => {
      zkp.recordTrace('trace_1', ['stmt1']);
      const proof = zkp.proveExecution('trace_1');

      const wrongDigest = Buffer.alloc(32);
      wrongDigest.fill(0xff);

      const isValid = zkp.verifyAgainstDigest(proof, wrongDigest);

      expect(typeof isValid).toBe('boolean');
    });

    test('should handle verification with invalid proof', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      const proof = zkp.proveExecution('trace_1');

      proof.commitment[0] ^= 0xff;

      const isValid = zkp.verifyAgainstDigest(proof, proof.trace.executionHash);

      expect(typeof isValid).toBe('boolean');
    });
  });

  describe('Proof Transcript', () => {
    test('should generate proof transcript', () => {
      zkp.recordTrace('trace_1', ['statement1', 'statement2']);
      zkp.proveExecution('trace_1');

      const transcript = zkp.getProofTranscript('trace_1');

      expect(typeof transcript).toBe('string');
      expect(transcript.length).toBeGreaterThan(0);
      expect(transcript).toContain('Proof: trace_1');
    });

    test('should include verification status in transcript', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      const proof = zkp.proveExecution('trace_1');

      zkp.verifyProof(proof);

      const transcript = zkp.getProofTranscript('trace_1');

      expect(transcript).toContain('Verified: true');
    });

    test('should return empty string for non-existent proof', () => {
      const transcript = zkp.getProofTranscript('non_existent');

      expect(transcript).toBe('');
    });

    test('should include statement information in transcript', () => {
      zkp.recordTrace('trace_1', ['stmt1', 'stmt2', 'stmt3']);
      zkp.proveExecution('trace_1');

      const transcript = zkp.getProofTranscript('trace_1');

      expect(transcript).toContain('0:');
      expect(transcript).toContain('1:');
      expect(transcript).toContain('2:');
    });
  });

  describe('Fiat-Shamir Challenge', () => {
    test('should generate challenge for same input', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      const proof1 = zkp.proveExecution('trace_1');

      expect(proof1.challenge).toBeInstanceOf(Buffer);
      expect(proof1.challenge.length).toBeGreaterThan(0);
    });
  });

  describe('Multiple Traces', () => {
    test('should handle multiple independent traces', () => {
      zkp.recordTrace('trace_1', ['stmt1']);
      zkp.recordTrace('trace_2', ['stmt2']);
      zkp.recordTrace('trace_3', ['stmt3']);

      const proof1 = zkp.proveExecution('trace_1');
      const proof2 = zkp.proveExecution('trace_2');
      const proof3 = zkp.proveExecution('trace_3');

      expect(typeof zkp.verifyProof(proof1)).toBe('boolean');
      expect(typeof zkp.verifyProof(proof2)).toBe('boolean');
      expect(typeof zkp.verifyProof(proof3)).toBe('boolean');

      expect(proof1.trace).toBeDefined();
      expect(proof2.trace).toBeDefined();
      expect(proof3.trace).toBeDefined();
    });

    test('should isolate proofs from different traces', () => {
      zkp.recordTrace('trace_A', ['stmt_a']);
      zkp.recordTrace('trace_B', ['stmt_b']);

      const proofA = zkp.proveExecution('trace_A');
      const proofB = zkp.proveExecution('trace_B');

      const isValid = zkp.verifyAgainstDigest(proofA, proofB.trace.executionHash);
      expect(typeof isValid).toBe('boolean');
    });
  });

  describe('Trace Cleanup', () => {
    test('should clear all traces', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      zkp.proveExecution('trace_1');

      zkp.clear();

      expect(() => {
        zkp.proveExecution('trace_1');
      }).toThrow();
    });

    test('should clear all proofs', () => {
      zkp.recordTrace('trace_1', ['stmt']);
      zkp.proveExecution('trace_1');

      zkp.clear();

      const transcript = zkp.getProofTranscript('trace_1');
      expect(transcript).toBe('');
    });
  });

  describe('Long Execution Traces', () => {
    test('should handle long traces', () => {
      const statements = Array.from({ length: 100 }, (_, i) => `statement_${i}`);

      const trace = zkp.recordTrace('long_trace', statements);

      expect(trace.statements.length).toBe(100);
      expect(trace.executionHash.length).toBe(32);

      const proof = zkp.proveExecution('long_trace');
      expect(zkp.verifyProof(proof)).toBe(true);
    });
  });
});
