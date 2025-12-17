/**
 * Distributed-first value wrappers for the hybrid runtime.
 */

export type ConsistencyLevel = 'local' | 'eventual' | 'strong';
export type EvolvedValueKind = 'distributed' | 'consensus' | 'partial';

export interface EvolvedNumericValue {
  readonly kind: EvolvedValueKind;
  readonly id: string;

  toNumber(): number;
  setNumber(value: number): void;
  addNumber(delta: number): void;

  getVersion(): number;
  getConsistency(): ConsistencyLevel;
  setConsistency(level: ConsistencyLevel): void;

  getMetadata(): Record<string, unknown>;
}

export function isEvolvedNumericValue(value: unknown): value is EvolvedNumericValue {
  return (
    typeof value === 'object' &&
    value !== null &&
    'kind' in value &&
    typeof (value as any).toNumber === 'function' &&
    typeof (value as any).setNumber === 'function'
  );
}

export interface DistributedValueOptions {
  id?: string;
  consistency?: ConsistencyLevel;
}

export class DistributedValue implements EvolvedNumericValue {
  readonly kind: EvolvedValueKind = 'distributed';
  readonly id: string;

  private value: number;
  private version = 0;
  private consistency: ConsistencyLevel;

  constructor(initialValue: number, options: DistributedValueOptions = {}) {
    this.id = options.id ?? `dist-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    this.value = initialValue;
    this.consistency = options.consistency ?? 'eventual';
  }

  toNumber(): number {
    return this.value;
  }

  setNumber(value: number): void {
    this.value = value;
    this.version++;
  }

  addNumber(delta: number): void {
    this.value += delta;
    this.version++;
  }

  getVersion(): number {
    return this.version;
  }

  getConsistency(): ConsistencyLevel {
    return this.consistency;
  }

  setConsistency(level: ConsistencyLevel): void {
    this.consistency = level;
  }

  getMetadata(): Record<string, unknown> {
    return {
      kind: this.kind,
      id: this.id,
      version: this.version,
      consistency: this.consistency,
    };
  }
}

export interface ConsensusValueOptions extends DistributedValueOptions {
  quorum?: number;
}

interface ConsensusWaiter {
  quorum: number;
  resolve: (met: boolean) => void;
  timeoutId?: NodeJS.Timeout;
}

export class ConsensusValue extends DistributedValue {
  readonly kind: EvolvedValueKind = 'consensus';
  private acknowledgements: Set<string> = new Set();
  private waiters: ConsensusWaiter[] = [];
  private configuredQuorum: number | null;

  constructor(initialValue: number, options: ConsensusValueOptions = {}) {
    super(initialValue, { id: options.id, consistency: options.consistency ?? 'strong' });
    this.configuredQuorum = options.quorum ?? null;
  }

  setConfiguredQuorum(quorum: number): void {
    this.configuredQuorum = quorum;
  }

  getConfiguredQuorum(): number | null {
    return this.configuredQuorum;
  }

  noteAcknowledgement(vmId: string): void {
    this.acknowledgements.add(vmId);
    this.maybeResolveWaiters();
  }

  getAcknowledgementCount(): number {
    return this.acknowledgements.size;
  }

  clearAcknowledgements(): void {
    this.acknowledgements.clear();
  }

  awaitQuorum(quorum: number, timeoutMs: number): Promise<boolean> {
    const effectiveQuorum = Math.max(1, quorum);

    if (this.getAcknowledgementCount() >= effectiveQuorum) {
      return Promise.resolve(true);
    }

    return new Promise<boolean>((resolve) => {
      const waiter: ConsensusWaiter = { quorum: effectiveQuorum, resolve };

      if (timeoutMs > 0) {
        waiter.timeoutId = setTimeout(() => {
          this.waiters = this.waiters.filter((w) => w !== waiter);
          resolve(false);
        }, timeoutMs);
        waiter.timeoutId.unref();
      }

      this.waiters.push(waiter);
    });
  }

  private maybeResolveWaiters(): void {
    const resolved: ConsensusWaiter[] = [];

    for (const waiter of this.waiters) {
      if (this.getAcknowledgementCount() >= waiter.quorum) {
        resolved.push(waiter);
      }
    }

    if (resolved.length === 0) {
      return;
    }

    this.waiters = this.waiters.filter((w) => !resolved.includes(w));

    for (const waiter of resolved) {
      if (waiter.timeoutId) {
        clearTimeout(waiter.timeoutId);
      }
      waiter.resolve(true);
    }
  }

  override getMetadata(): Record<string, unknown> {
    return {
      ...super.getMetadata(),
      kind: this.kind,
      acknowledgements: this.getAcknowledgementCount(),
      quorum: this.configuredQuorum,
    };
  }
}

export class PartialValue extends DistributedValue {
  readonly kind: EvolvedValueKind = 'partial';
  private resumed = false;

  resume(): void {
    this.resumed = true;
  }

  isResumed(): boolean {
    return this.resumed;
  }

  override getMetadata(): Record<string, unknown> {
    return {
      ...super.getMetadata(),
      kind: this.kind,
      resumed: this.resumed,
    };
  }
}
