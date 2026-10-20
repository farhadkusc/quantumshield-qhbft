#!/usr/bin/env python3
"""Sweep QH-BFT at N=4, 16, 64 and write the analytical + simulation report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qhbft.protocol import combinatorial_safety_grid, sweep  # noqa: E402


def main() -> None:
    reports = sweep()
    safety = combinatorial_safety_grid()
    payload = {
        "disclaimer": (
            "Throughput is the first-order bandwidth bound T(N) <= B / (fanout * N^2 * S) "
            "at B = 1 Gbps. It is not a measured transactions-per-second from a cluster."
        ),
        "safety_grid": safety,
        "configurations": [
            {
                "n": r.n,
                "f": r.f,
                "rounds": r.rounds,
                "decisions": r.decisions,
                "empty_blocks": r.empty_blocks,
                "safety_violations": r.safety_violations,
                "unique_primaries": r.unique_primaries,
                "mean_quorum": round(r.mean_quorum, 2),
                "adaptive_tps_bound": round(r.adaptive_tps, 3),
                "naive_mldsa87_tps_bound": round(r.naive_pqc_tps, 3),
                "ecdsa_tps_bound": round(r.ecdsa_tps, 3),
                "signature_mix": r.adaptive_sig_mix,
            }
            for r in reports
        ],
    }
    out = ROOT / "benchmarks" / "results" / "simulation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"{'N':>4} {'f':>3} {'decisions':>10} {'empty':>6} {'viol':>5} {'Q':>6} {'adapt TPS':>10} {'naive TPS':>10}")
    for r in reports:
        print(
            f"{r.n:4d} {r.f:3d} {r.decisions:10d} {r.empty_blocks:6d} {r.safety_violations:5d} "
            f"{r.mean_quorum:6.1f} {r.adaptive_tps:10.2f} {r.naive_pqc_tps:10.2f}"
        )
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
