import React, { useEffect, useMemo, useRef, useState } from 'react';

import type { ExecutionFrame, Timeline } from '../types';

export interface ExecutionVisualizerProps {
  timeline: Timeline;
  frames: ExecutionFrame[];
  initialStep?: number;
}

const speeds = [0.25, 0.5, 1, 2, 4] as const;

export function ExecutionVisualizer({
  timeline,
  frames,
  initialStep = 0,
}: ExecutionVisualizerProps) {
  const maxStep = frames.length - 1;
  const [step, setStep] = useState(() => Math.max(0, Math.min(initialStep, maxStep)));
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<(typeof speeds)[number]>(1);
  const [showOverlay, setShowOverlay] = useState(false);

  const current = frames[step];

  const activeSourceLine = current?.source_line ?? null;

  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const delayMs = 250 / speed;
    intervalRef.current = window.setInterval(() => {
      setStep((s) => {
        if (s >= maxStep) {
          return s;
        }
        return s + 1;
      });
    }, delayMs);

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPlaying, maxStep, speed]);

  useEffect(() => {
    if (step >= maxStep) {
      setIsPlaying(false);
    }
  }, [step, maxStep]);

  const currentInstruction = useMemo(() => timeline.instructions[step], [timeline.instructions, step]);

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 12 }}>
      <header style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
        <button
          type="button"
          onClick={() => setIsPlaying((p) => !p)}
          data-testid="toggle-play"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          data-testid="step-back"
        >
          ◀
        </button>
        <button
          type="button"
          onClick={() => setStep((s) => Math.min(maxStep, s + 1))}
          disabled={step === maxStep}
          data-testid="step-forward"
        >
          ▶
        </button>
        <span data-testid="step-indicator">
          Step {step + 1} / {frames.length}
        </span>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          Speed
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value) as (typeof speeds)[number])}
            data-testid="speed"
          >
            {speeds.map((s) => (
              <option key={s} value={s}>
                {s}x
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => setShowOverlay(true)} data-testid="show-overlay">
          Layers
        </button>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <section style={{ border: '1px solid #ddd', borderRadius: 6, padding: 10 }}>
          <h2 style={{ marginTop: 0 }}>English source</h2>
          <pre style={{ margin: 0, overflow: 'auto' }} data-testid="source-pane">
            {timeline.source.lines.map((l) => {
              const active = activeSourceLine === l.line;
              return (
                <div
                  key={l.line}
                  data-testid={active ? 'active-source-line' : undefined}
                  style={{
                    background: active ? '#fff3bf' : undefined,
                    padding: '2px 4px',
                    borderRadius: 4,
                  }}
                >
                  <span style={{ color: '#666', display: 'inline-block', width: 32 }}>
                    {l.line}
                  </span>
                  {l.text}
                </div>
              );
            })}
          </pre>
        </section>

        <section style={{ border: '1px solid #ddd', borderRadius: 6, padding: 10 }}>
          <h2 style={{ marginTop: 0 }}>Super-bit instructions</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: 340, overflow: 'auto' }}>
            {timeline.instructions.map((inst) => {
              const active = inst.step === step;
              return (
                <li
                  key={inst.step}
                  style={{
                    padding: '4px 6px',
                    borderRadius: 4,
                    background: active ? '#d3f9d8' : undefined,
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 8,
                  }}
                  data-testid={active ? 'active-instruction' : undefined}
                  onClick={() => setStep(inst.step)}
                >
                  <span>
                    {inst.step.toString().padStart(3, '0')} {inst.opcode}
                  </span>
                  <span style={{ color: '#666' }}>{inst.operand ?? ''}</span>
                </li>
              );
            })}
          </ul>
        </section>

        <section style={{ border: '1px solid #ddd', borderRadius: 6, padding: 10 }}>
          <h2 style={{ marginTop: 0 }}>Binary / hex</h2>
          <div style={{ marginBottom: 8 }}>
            <div>
              <strong data-testid="binary-opcode">{currentInstruction.opcode}</strong>
              <span style={{ marginLeft: 8, color: '#666' }}>
                pc={currentInstruction.pc}
              </span>
            </div>
          </div>
          <pre style={{ margin: 0, overflow: 'auto' }} data-testid="hex-viewer">
            {current.binary_bytes_hex}
          </pre>
        </section>

        <section style={{ gridColumn: '1 / span 3', border: '1px solid #eee', borderRadius: 6, padding: 10 }}>
          <h2 style={{ marginTop: 0 }}>Inspectors</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div>
              <h3 style={{ marginTop: 0 }}>Stack</h3>
              <pre data-testid="stack-inspector">{JSON.stringify(current.stack, null, 2)}</pre>
            </div>
            <div>
              <h3 style={{ marginTop: 0 }}>Variables</h3>
              <pre data-testid="vars-inspector">{JSON.stringify(current.variables, null, 2)}</pre>
            </div>
            <div>
              <h3 style={{ marginTop: 0 }}>Output</h3>
              <pre data-testid="output-inspector">{JSON.stringify(current.output, null, 2)}</pre>
            </div>
          </div>
        </section>
      </main>

      {showOverlay ? (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.45)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: 24,
          }}
        >
          <div style={{ background: 'white', borderRadius: 8, padding: 16, maxWidth: 720 }}>
            <h2 style={{ marginTop: 0 }}>The five abstraction layers</h2>
            <ol>
              <li>
                <strong>English source</strong> — the human-readable program.
              </li>
              <li>
                <strong>AST</strong> — structured syntax tree produced by the parser.
              </li>
              <li>
                <strong>Super-bit IR</strong> — opcode/operand stream executed by the VM.
              </li>
              <li>
                <strong>Binary frames</strong> — serialized bytes written as the executable payload.
              </li>
              <li>
                <strong>Runtime state</strong> — stack/variables/output evolving per instruction.
              </li>
            </ol>
            <button type="button" onClick={() => setShowOverlay(false)} data-testid="close-overlay">
              Close
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
