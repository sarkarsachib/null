/**
 * Quantum Gate Library for SuperBit VM
 */

export interface Complex {
  re: number;
  im: number;
}

export const C = (re: number, im: number): Complex => ({ re, im });

export const addC = (a: Complex, b: Complex): Complex => ({ re: a.re + b.re, im: a.im + b.im });
export const subC = (a: Complex, b: Complex): Complex => ({ re: a.re - b.re, im: a.im - b.im });
export const mulC = (a: Complex, b: Complex): Complex => ({
  re: a.re * b.re - a.im * b.im,
  im: a.re * b.im + a.im * b.re,
});
export const absC = (a: Complex): number => Math.sqrt(a.re * a.re + a.im * a.im);

export type GateMatrix = Complex[][];

export const MATRIX_X: GateMatrix = [
  [C(0, 0), C(1, 0)],
  [C(1, 0), C(0, 0)],
];

export const MATRIX_H: GateMatrix = [
  [C(1 / Math.sqrt(2), 0), C(1 / Math.sqrt(2), 0)],
  [C(1 / Math.sqrt(2), 0), C(-1 / Math.sqrt(2), 0)],
];

export const MATRIX_Z: GateMatrix = [
  [C(1, 0), C(0, 0)],
  [C(0, 0), C(-1, 0)],
];

export const MATRIX_I: GateMatrix = [
    [C(1, 0), C(0, 0)],
    [C(0, 0), C(1, 0)],
];

export const MATRIX_CNOT: GateMatrix = [
  [C(1, 0), C(0, 0), C(0, 0), C(0, 0)],
  [C(0, 0), C(1, 0), C(0, 0), C(0, 0)],
  [C(0, 0), C(0, 0), C(0, 0), C(1, 0)],
  [C(0, 0), C(0, 0), C(1, 0), C(0, 0)],
];

export const GateLibrary: Record<string, GateMatrix> = {
  X: MATRIX_X,
  H: MATRIX_H,
  Z: MATRIX_Z,
  I: MATRIX_I,
  CNOT: MATRIX_CNOT
};
