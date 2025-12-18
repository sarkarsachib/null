/**
 * Type definitions for ownership and memory safety features
 */

export interface ReferenceCountedValue {
  value: any;
  refCount: number;
}

export interface BorrowInfo {
  variableName: string;
  borrowType: 'immutable' | 'mutable';
  startLine: number;
  endLine?: number;
}

export interface VariableInfo {
  name: string;
  mutable: boolean;
  lifetimeStart: number;
  lifetimeEnd?: number;
  activeBorrows: number;
  mutableBorrows: number;
  isBorrowed: boolean;
  isDropped: boolean;
}