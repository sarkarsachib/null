import React, { useEffect, useState } from 'react';

import { ExecutionVisualizer } from './components/ExecutionVisualizer';
import type { ExecutionFrame, Timeline } from './types';

const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export function App() {
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [frames, setFrames] = useState<ExecutionFrame[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const tl = await fetchJson<Timeline>('/timeline');
        const fs = await Promise.all(
          Array.from({ length: tl.steps }, (_, i) => fetchJson<ExecutionFrame>(`/state/${i}`))
        );

        if (!cancelled) {
          setTimeline(tl);
          setFrames(fs);
        }
      } catch (e) {
        if (!cancelled) {
          setError(String(e));
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h1>Null Visualizer</h1>
        <p>Failed to connect to backend at {apiBase}.</p>
        <pre>{error}</pre>
      </div>
    );
  }

  if (!timeline || !frames) {
    return (
      <div style={{ padding: 24 }}>
        <h1>Null Visualizer</h1>
        <p>Loading timeline…</p>
      </div>
    );
  }

  return <ExecutionVisualizer timeline={timeline} frames={frames} />;
}
