import { VMCapabilities } from './transport_adapter';

export interface WorkItem {
  id: string;
  payload: unknown;
  priority: number;
  createdAt: number;
  assignedTo?: string;
}

export type LoadBalancingStrategy = 'round-robin' | 'work-stealing' | 'least-loaded';

export interface WorkSchedulerConfig {
  strategy?: LoadBalancingStrategy;
  maxTasksPerWorker?: number;
}

export class WorkScheduler {
  private strategy: LoadBalancingStrategy;
  private maxTasksPerWorker: number;
  private workQueue: WorkItem[] = [];
  private vmWorkloads: Map<string, number> = new Map();
  private currentRoundRobinIndex = 0;
  private availableVMs: VMCapabilities[] = [];

  constructor(config: WorkSchedulerConfig = {}) {
    this.strategy = config.strategy ?? 'round-robin';
    this.maxTasksPerWorker = config.maxTasksPerWorker ?? 10;
  }

  updateAvailableVMs(vms: VMCapabilities[]): void {
    this.availableVMs = vms;
    for (const vm of vms) {
      if (!this.vmWorkloads.has(vm.vmId)) {
        this.vmWorkloads.set(vm.vmId, 0);
      }
    }
  }

  enqueueWork(workItem: WorkItem): void {
    this.workQueue.push(workItem);
    this.workQueue.sort((a, b) => b.priority - a.priority);
  }

  scheduleNext(): WorkItem | null {
    if (this.workQueue.length === 0) {
      return null;
    }

    const targetVm = this.selectTargetVM();
    if (!targetVm) {
      return null;
    }

    const workItem = this.workQueue.shift()!;
    workItem.assignedTo = targetVm;
    
    const currentLoad = this.vmWorkloads.get(targetVm) ?? 0;
    this.vmWorkloads.set(targetVm, currentLoad + 1);

    return workItem;
  }

  private selectTargetVM(): string | null {
    if (this.availableVMs.length === 0) {
      return null;
    }

    switch (this.strategy) {
      case 'round-robin':
        return this.selectRoundRobin();
      case 'work-stealing':
        return this.selectWorkStealing();
      case 'least-loaded':
        return this.selectLeastLoaded();
      default:
        return this.selectRoundRobin();
    }
  }

  private selectRoundRobin(): string {
    const vm = this.availableVMs[this.currentRoundRobinIndex];
    this.currentRoundRobinIndex =
      (this.currentRoundRobinIndex + 1) % this.availableVMs.length;
    return vm.vmId;
  }

  private selectWorkStealing(): string {
    const leastLoaded = this.selectLeastLoaded();
    const mostLoaded = this.findMostLoadedVM();

    if (!mostLoaded) return leastLoaded;

    const leastLoad = this.vmWorkloads.get(leastLoaded) ?? 0;
    const mostLoad = this.vmWorkloads.get(mostLoaded) ?? 0;

    if (mostLoad - leastLoad > 2 && leastLoad < this.maxTasksPerWorker) {
      return leastLoaded;
    }

    return this.selectRoundRobin();
  }

  private selectLeastLoaded(): string {
    let minLoad = Infinity;
    let selectedVm = this.availableVMs[0].vmId;

    for (const vm of this.availableVMs) {
      const load = this.vmWorkloads.get(vm.vmId) ?? 0;
      if (load < minLoad && load < this.maxTasksPerWorker) {
        minLoad = load;
        selectedVm = vm.vmId;
      }
    }

    return selectedVm;
  }

  private findMostLoadedVM(): string | null {
    let maxLoad = -1;
    let selectedVm: string | null = null;

    for (const [vmId, load] of this.vmWorkloads.entries()) {
      if (load > maxLoad) {
        maxLoad = load;
        selectedVm = vmId;
      }
    }

    return selectedVm;
  }

  completeWork(vmId: string): void {
    const currentLoad = this.vmWorkloads.get(vmId) ?? 0;
    this.vmWorkloads.set(vmId, Math.max(0, currentLoad - 1));
  }

  getWorkload(vmId: string): number {
    return this.vmWorkloads.get(vmId) ?? 0;
  }

  getQueueLength(): number {
    return this.workQueue.length;
  }

  isBackpressureNeeded(): boolean {
    const totalWorkload = Array.from(this.vmWorkloads.values()).reduce(
      (sum, load) => sum + load,
      0
    );
    const avgLoad = totalWorkload / Math.max(1, this.availableVMs.length);
    return avgLoad > this.maxTasksPerWorker * 0.8;
  }

  getStats() {
    return {
      queueLength: this.workQueue.length,
      availableVMs: this.availableVMs.length,
      totalWorkload: Array.from(this.vmWorkloads.values()).reduce(
        (sum, load) => sum + load,
        0
      ),
      vmWorkloads: Object.fromEntries(this.vmWorkloads),
      backpressureActive: this.isBackpressureNeeded(),
    };
  }
}
