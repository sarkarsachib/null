import { BinaryBridge } from '../binary_bridge';

describe('BinaryBridge', () => {
  let bridge: BinaryBridge;

  beforeEach(() => {
    bridge = new BinaryBridge();
  });

  describe('Frame Emission', () => {
    it('should emit frames', () => {
      const data = Buffer.from('test data');
      bridge.emitFrame('TEST', data);

      const frames = bridge.getFrames();
      expect(frames).toHaveLength(1);
      expect(frames[0].frameType).toBe('TEST');
    });

    it('should emit multiple frames', () => {
      bridge.emitFrame('TYPE1', Buffer.from('data1'));
      bridge.emitFrame('TYPE2', Buffer.from('data2'));

      const frames = bridge.getFrames();
      expect(frames).toHaveLength(2);
    });

    it('should record frame timestamps', () => {
      bridge.emitFrame('TEST', Buffer.from('data'));

      const frames = bridge.getFrames();
      expect(frames[0].timestamp).toBeLessThanOrEqual(Date.now());
      expect(frames[0].timestamp).toBeGreaterThan(Date.now() - 1000);
    });

    it('should copy emitted data', () => {
      const original = Buffer.from('test');
      bridge.emitFrame('TEST', original);
      original[0] = 99;

      const frames = bridge.getFrames();
      expect(frames[0].data[0]).not.toBe(99);
    });
  });

  describe('Output Emission', () => {
    it('should emit output frames', () => {
      bridge.emitOutput('result', 42);

      const frames = bridge.getFrames();
      expect(frames.some(f => f.frameType === 'OUTPUT')).toBe(true);
    });

    it('should emit output with label and value', () => {
      bridge.emitOutput('x', 100);
      bridge.emitOutput('y', 200);

      expect(bridge.getFrameCount()).toBe(2);
    });

    it('should handle negative values', () => {
      bridge.emitOutput('neg', -42);

      expect(bridge.getFrameCount()).toBe(1);
    });

    it('should handle zero', () => {
      bridge.emitOutput('zero', 0);

      expect(bridge.getFrameCount()).toBe(1);
    });
  });

  describe('Register State Emission', () => {
    it('should emit register state frames', () => {
      bridge.emitRegisterState('r1', 42);

      const frames = bridge.getFrames();
      expect(frames.some(f => f.frameType === 'REGISTER')).toBe(true);
    });

    it('should emit multiple register states', () => {
      bridge.emitRegisterState('a', 1);
      bridge.emitRegisterState('b', 2);
      bridge.emitRegisterState('c', 3);

      expect(bridge.getFrameCount()).toBe(3);
    });
  });

  describe('Control Flow Emission', () => {
    it('should emit control flow events', () => {
      bridge.emitControlFlow('branch_taken');

      const frames = bridge.getFrames();
      expect(frames.some(f => f.frameType === 'CONTROL')).toBe(true);
    });

    it('should emit control flow with data', () => {
      bridge.emitControlFlow('loop_start', { iterations: 10 });

      expect(bridge.getFrameCount()).toBe(1);
    });

    it('should emit multiple control flow events', () => {
      bridge.emitControlFlow('event1');
      bridge.emitControlFlow('event2');

      expect(bridge.getFrameCount()).toBe(2);
    });
  });

  describe('Frame Management', () => {
    it('should get all frames', () => {
      bridge.emitFrame('A', Buffer.from('1'));
      bridge.emitFrame('B', Buffer.from('2'));

      const frames = bridge.getFrames();
      expect(frames).toHaveLength(2);
      expect(frames[0].frameType).toBe('A');
      expect(frames[1].frameType).toBe('B');
    });

    it('should clear frames', () => {
      bridge.emitFrame('TEST', Buffer.from('data'));
      expect(bridge.getFrameCount()).toBe(1);

      bridge.clearFrames();
      expect(bridge.getFrameCount()).toBe(0);
    });

    it('should get frame count', () => {
      bridge.emitFrame('A', Buffer.from('1'));
      expect(bridge.getFrameCount()).toBe(1);

      bridge.emitFrame('B', Buffer.from('2'));
      expect(bridge.getFrameCount()).toBe(2);

      bridge.clearFrames();
      expect(bridge.getFrameCount()).toBe(0);
    });

    it('should return independent frame array copy', () => {
      bridge.emitFrame('TEST', Buffer.from('data'));
      const frames1 = bridge.getFrames();
      const frames2 = bridge.getFrames();

      expect(frames1).toEqual(frames2);
      expect(frames1).not.toBe(frames2);
    });
  });

  describe('Mixed Operations', () => {
    it('should handle mixed frame types', () => {
      bridge.emitFrame('CUSTOM', Buffer.from('custom'));
      bridge.emitOutput('x', 10);
      bridge.emitRegisterState('y', 20);
      bridge.emitControlFlow('done');

      const frames = bridge.getFrames();
      expect(frames).toHaveLength(4);
      expect(frames.map(f => f.frameType)).toContain('CUSTOM');
      expect(frames.map(f => f.frameType)).toContain('OUTPUT');
      expect(frames.map(f => f.frameType)).toContain('REGISTER');
      expect(frames.map(f => f.frameType)).toContain('CONTROL');
    });
  });
});
