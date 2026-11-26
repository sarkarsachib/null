#!/usr/bin/env python3
"""Wall-time and peak-RSS measurement for the Null benchmark harness.

Prints one "wall_ms rss_kb" line per run on stdout so run_bench.sh can take the
median of both.

Two things the obvious implementations get wrong on this host:

* Polling /proc from bash costs a `sleep` fork per poll (10 ms of quantisation),
  which is more than a whole short workload. Timing here uses
  time.perf_counter_ns around subprocess.run with no sampling at all.
* ru_maxrss (RUSAGE_CHILDREN or wait4) reports the forked copy of the
  interpreter's address space on gVisor, so a 2 MB binary showed up as 22 MB.
  Peak RSS is therefore sampled from the child's /proc/<pid>/status in a
  separate, untimed run, and VmHWM is used when the kernel provides it.

    python3 bench/measure.py --runs 5 ./bench/build/sum_loop.null
"""

import argparse
import os
import subprocess
import sys
import time


def sample_peak_rss(binary: str) -> int:
    """Run once, tracking the child's resident set; returns peak KiB."""
    hwm = 0
    rss = 0
    path = "/proc/{}/status"
    with open(os.devnull, "wb") as devnull:
        child = subprocess.Popen([binary], stdout=devnull, stderr=devnull)
        status = path.format(child.pid)
        while True:
            try:
                with open(status, "r") as fh:
                    for line in fh:
                        if line.startswith("VmHWM:"):
                            hwm = max(hwm, int(line.split()[1]))
                        elif line.startswith("VmRSS:"):
                            rss = max(rss, int(line.split()[1]))
            except OSError:
                # Process gone: /proc entry removed. Whatever we saw stands.
                break
            if child.poll() is not None:
                break
        child.wait()
    return hwm if hwm else rss


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("binary")
    args = ap.parse_args()

    if not os.path.exists(args.binary):
        print(f"measure.py: no such binary: {args.binary}", file=sys.stderr)
        return 2

    rss = sample_peak_rss(args.binary)
    worst_rc = 0
    for _ in range(args.runs):
        start = time.perf_counter_ns()
        proc = subprocess.run(
            [args.binary],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        elapsed_ms = (time.perf_counter_ns() - start) / 1e6
        if proc.returncode != 0:
            worst_rc = proc.returncode
        print(f"{elapsed_ms:.1f} {rss}")
    return worst_rc


if __name__ == "__main__":
    raise SystemExit(main())
