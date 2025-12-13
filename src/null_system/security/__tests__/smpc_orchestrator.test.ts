import { SMPCOrchestrator } from '../smpc_orchestrator';

describe('SMPCOrchestrator', () => {
  let orchestrator: SMPCOrchestrator;

  beforeEach(() => {
    orchestrator = new SMPCOrchestrator({
      partyId: 'party_0',
      threshold: 2,
      totalParties: 3,
    });
  });

  describe('Initialization', () => {
    test('should create orchestrator with valid config', () => {
      expect(orchestrator).toBeDefined();
      const config = orchestrator.getConfig();
      expect(config.partyId).toBe('party_0');
      expect(config.threshold).toBe(2);
      expect(config.totalParties).toBe(3);
    });

    test('should throw error if threshold exceeds total parties', () => {
      expect(() => {
        new SMPCOrchestrator({
          partyId: 'party_0',
          threshold: 5,
          totalParties: 3,
        });
      }).toThrow('Threshold');
    });

    test('should support 2-of-3 threshold scheme', () => {
      const orch = new SMPCOrchestrator({
        partyId: 'party_1',
        threshold: 2,
        totalParties: 3,
      });

      expect(orch).toBeDefined();
    });

    test('should support 3-of-5 threshold scheme', () => {
      const orch = new SMPCOrchestrator({
        partyId: 'party_0',
        threshold: 3,
        totalParties: 5,
      });

      expect(orch).toBeDefined();
    });
  });

  describe('Secret Sharing', () => {
    test('should share a secret', () => {
      const secret = Buffer.from('mysecret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      expect(shares).toBeInstanceOf(Map);
      expect(shares.size).toBe(3);
    });

    test('should create shares for each party', () => {
      const secret = Buffer.from('test_secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (let i = 0; i < 3; i++) {
        const partyId = `party_${i}`;
        expect(shares.has(partyId)).toBe(true);
        expect(shares.get(partyId)).toBeInstanceOf(Buffer);
      }
    });

    test('should produce different shares for same secret', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      const share0 = shares.get('party_0');
      const share1 = shares.get('party_1');
      const share2 = shares.get('party_2');

      expect(share0).not.toEqual(share1);
      expect(share1).not.toEqual(share2);
      expect(share0).not.toEqual(share2);
    });

    test('should handle multiple secrets', () => {
      const secret1 = Buffer.from('secret1');
      const secret2 = Buffer.from('secret2');

      orchestrator.shareSecret('secret_1', secret1);
      orchestrator.shareSecret('secret_2', secret2);

      const shares1 = orchestrator.getSecretShares('secret_1');
      const shares2 = orchestrator.getSecretShares('secret_2');

      expect(shares1?.size).toBe(3);
      expect(shares2?.size).toBe(3);
    });
  });

  describe('Share Submission', () => {
    test('should submit a share', () => {
      const share = Buffer.from('share_data');
      orchestrator.submitShare('secret_1_party_0', share);

      const submitted = orchestrator.getShareInfo('secret_1_party_0');
      expect(submitted).toBeDefined();
      expect(submitted?.value).toEqual(share);
    });

    test('should store share metadata', () => {
      const share = Buffer.from('share_data');
      orchestrator.submitShare('secret_1_party_1', share);

      const submitted = orchestrator.getShareInfo('secret_1_party_1');
      expect(submitted?.shareId).toBe('secret_1_party_1');
      expect(submitted?.partyId).toBe('party_0');
    });

    test('should handle multiple shares', () => {
      orchestrator.submitShare('secret_1_party_0', Buffer.from('share1'));
      orchestrator.submitShare('secret_1_party_1', Buffer.from('share2'));
      orchestrator.submitShare('secret_1_party_2', Buffer.from('share3'));

      expect(orchestrator.getShareInfo('secret_1_party_0')).toBeDefined();
      expect(orchestrator.getShareInfo('secret_1_party_1')).toBeDefined();
      expect(orchestrator.getShareInfo('secret_1_party_2')).toBeDefined();
    });
  });

  describe('Share Combination', () => {
    test('should combine shares to reconstruct secret', () => {
      const secret = Buffer.from('my_secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      const shareIds = Array.from(shares.keys()).map((partyId) => `secret_1_${partyId}`);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const reconstructed = orchestrator.combineShares('secret_1', shareIds);

      expect(reconstructed).toBeInstanceOf(Buffer);
      expect(reconstructed.length).toBe(secret.length);
    });

    test('should require minimum threshold shares', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const shareIds = Array.from(shares.keys()).map((partyId) => `secret_1_${partyId}`);

      expect(() => {
        orchestrator.combineShares('secret_1', shareIds.slice(0, 1));
      }).toThrow('Not enough shares');
    });

    test('should combine with exactly threshold shares', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const shareIds = Array.from(shares.keys())
        .slice(0, 2)
        .map((partyId) => `secret_1_${partyId}`);

      const reconstructed = orchestrator.combineShares('secret_1', shareIds);

      expect(reconstructed).toBeInstanceOf(Buffer);
    });

    test('should combine with more than threshold shares', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const shareIds = Array.from(shares.keys()).map((partyId) => `secret_1_${partyId}`);

      const reconstructed = orchestrator.combineShares('secret_1', shareIds);

      expect(reconstructed).toBeInstanceOf(Buffer);
    });

    test('should mark secret as reconstructed', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      expect(orchestrator.isReconstructed('secret_1')).toBe(false);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const shareIds = Array.from(shares.keys()).map((partyId) => `secret_1_${partyId}`);

      orchestrator.combineShares('secret_1', shareIds);

      expect(orchestrator.isReconstructed('secret_1')).toBe(true);
    });
  });

  describe('Computation on Shares', () => {
    beforeEach(() => {
      const secret = Buffer.from([10, 20, 30, 40]);
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }
    });

    test('should compute sum of shares', () => {
      const shareIds = ['secret_1_party_0', 'secret_1_party_1', 'secret_1_party_2'];

      const sum = orchestrator.computeSum(shareIds);

      expect(typeof sum).toBe('number');
      expect(sum).toBeGreaterThan(0);
    });

    test('should compute product of shares', () => {
      const shareIds = ['secret_1_party_0', 'secret_1_party_1'];

      const product = orchestrator.computeProduct(shareIds);

      expect(typeof product).toBe('number');
    });

    test('should return zero for empty share list', () => {
      expect(orchestrator.computeSum([])).toBe(0);
      expect(orchestrator.computeProduct([])).toBe(0);
    });

    test('should handle computation on subset of shares', () => {
      const shareIds1 = ['secret_1_party_0', 'secret_1_party_1'];
      const shareIds2 = ['secret_1_party_1', 'secret_1_party_2'];

      const sum1 = orchestrator.computeSum(shareIds1);
      const sum2 = orchestrator.computeSum(shareIds2);

      expect(sum1).toBeGreaterThan(0);
      expect(sum2).toBeGreaterThan(0);
    });
  });

  describe('Two-Party Example', () => {
    test('should support simple two-party computation', () => {
      const party0 = new SMPCOrchestrator({
        partyId: 'alice',
        threshold: 2,
        totalParties: 2,
      });

      const party1 = new SMPCOrchestrator({
        partyId: 'bob',
        threshold: 2,
        totalParties: 2,
      });

      const secret0 = Buffer.from([5]);
      const secret1 = Buffer.from([3]);

      const shares0 = party0.shareSecret('value_0', secret0);
      const shares1 = party1.shareSecret('value_1', secret1);

      const aliceShare0 = shares0.get('alice');
      const bobShare0 = shares0.get('bob');
      const aliceShare1 = shares1.get('alice');
      const bobShare1 = shares1.get('bob');

      if (aliceShare0 && bobShare0 && aliceShare1 && bobShare1) {
        party0.submitShare('value_0_alice', aliceShare0);
        party0.submitShare('value_1_alice', aliceShare1);

        party1.submitShare('value_0_bob', bobShare0);
        party1.submitShare('value_1_bob', bobShare1);

        expect(party0.getShareInfo('value_0_alice')).toBeDefined();
        expect(party1.getShareInfo('value_0_bob')).toBeDefined();
      }

      expect(shares0.size).toBe(2);
      expect(shares1.size).toBe(2);
    });
  });

  describe('State Management', () => {
    test('should get orchestrator state', () => {
      const state = orchestrator.getState();

      expect(state.partyId).toBe('party_0');
      expect(state.threshold).toBe(2);
      expect(state.totalParties).toBe(3);
      expect(state.totalSecrets).toBe(0);
      expect(state.totalShares).toBe(0);
    });

    test('should update state with shares and secrets', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      const state = orchestrator.getState();

      expect(state.totalSecrets).toBe(1);
      expect(state.totalShares).toBe(3);
    });

    test('should reset state', () => {
      const secret = Buffer.from('secret');
      const shares = orchestrator.shareSecret('secret_1', secret);

      for (const [partyId, shareData] of shares) {
        orchestrator.submitShare(`secret_1_${partyId}`, shareData);
      }

      orchestrator.reset();

      const state = orchestrator.getState();

      expect(state.totalSecrets).toBe(0);
      expect(state.totalShares).toBe(0);

      expect(orchestrator.getSecretShares('secret_1')).toBeUndefined();
    });
  });

  describe('Edge Cases', () => {
    test('should handle empty secret', () => {
      const secret = Buffer.alloc(0);
      const shares = orchestrator.shareSecret('empty_secret', secret);

      expect(shares.size).toBe(3);
    });

    test('should handle large secret', () => {
      const secret = Buffer.alloc(1024);
      secret.fill(0xff);

      const shares = orchestrator.shareSecret('large_secret', secret);

      expect(shares.size).toBe(3);

      for (const share of shares.values()) {
        expect(share.length).toBe(1024);
      }
    });

    test('should error on invalid share ID', () => {
      expect(() => {
        orchestrator.combineShares('invalid_secret', ['nonexistent_share']);
      }).toThrow();
    });
  });
});
