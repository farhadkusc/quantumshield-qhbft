#!/usr/bin/env python3
"""Quorum-intersection sampling and a signature-cost grid.

Any two quorums of size 2f+1 in a committee of 3f+1 intersect in at least
f+1 seats. The sampler does not prove that. It checks randomly drawn pairs.
A non-zero violation count means the sampler is wrong, not that the bound failed.
Costs stay on the closed form in qhbft.costs. Smoke is not a Wulver result.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from qhbft import __version__  # noqa: E402
from qhbft.costs import decision_cost  # noqa: E402

LAB_COMMITTEES = (64, 256, 1024, 4096)
LAB_PAIRS = 200_000
SMOKE_COMMITTEES = (16, 64)
SMOKE_PAIRS = 4_000
CHUNK = 8_000
PROTOCOLS = ("pbft", "qh-quorum", "hotstuff-linear", "hotstuff-raw-qc")
DELAYS_MS = (5.0, 20.0, 40.0)


def _valid(n: int) -> None:
    if n < 4 or (n - 1) % 3 != 0:
        raise ValueError(f"n={n} is not 3f+1")


def sample_intersections(n: int, n_pairs: int, seed: int) -> dict:
    _valid(n)
    f = (n - 1) // 3
    q = 2 * f + 1
    bound = f + 1
    rng = np.random.default_rng(seed)
    violations = 0
    min_inter = q
    done = 0
    while done < n_pairs:
        m = min(CHUNK, n_pairs - done)
        left = np.argpartition(rng.random((m, n)), q - 1, axis=1)[:, :q]
        right = np.argpartition(rng.random((m, n)), q - 1, axis=1)[:, :q]
        mark_l = np.zeros((m, n), dtype=np.bool_)
        mark_r = np.zeros((m, n), dtype=np.bool_)
        mark_l[np.arange(m)[:, None], left] = True
        mark_r[np.arange(m)[:, None], right] = True
        inter = np.count_nonzero(mark_l & mark_r, axis=1)
        violations += int(np.count_nonzero(inter < bound))
        min_inter = min(min_inter, int(inter.min()))
        done += m
    return {
        "n": n,
        "f": f,
        "quorum": q,
        "intersection_bound": bound,
        "n_pairs": n_pairs,
        "violations": violations,
        "min_intersection": min_inter,
    }


def cost_grid(committees: tuple[int, ...]) -> list[dict]:
    rows = []
    for n in committees:
        for protocol in PROTOCOLS:
            for delay in DELAYS_MS:
                row = decision_cost(protocol, n, "ML-DSA-87", one_way_ms=delay)
                rows.append(
                    {
                        "protocol": protocol,
                        "n": n,
                        "one_way_ms": delay,
                        "bytes": row["bytes"],
                        "critical_path_ms": row["critical_path_ms"],
                        "quorum": row["quorum"],
                    }
                )
    return rows


def _worker(job: tuple) -> dict:
    n, n_pairs, seed = job
    return sample_intersections(int(n), int(n_pairs), int(seed))


def main() -> None:
    parser = argparse.ArgumentParser(description="NJIT Wulver sweep for QH-BFT")
    parser.add_argument("--profile", choices=("smoke", "lab"), default="smoke")
    parser.add_argument("--workers", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    args = parser.parse_args()
    if args.profile == "smoke":
        committees = SMOKE_COMMITTEES
        n_pairs = SMOKE_PAIRS
    else:
        committees = LAB_COMMITTEES
        n_pairs = LAB_PAIRS
    jobs = [(n, n_pairs, 20261020 + n) for n in committees]
    started = time.perf_counter()
    workers = max(1, min(args.workers, len(jobs)))
    if workers == 1:
        sampled = [_worker(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            sampled = list(pool.map(_worker, jobs))
    elapsed = round(time.perf_counter() - started, 3)
    report = {
        "package": "quantumshield-qhbft",
        "package_version": __version__,
        "profile": args.profile,
        "host": socket.gethostname(),
        "ran_on_wulver": False,
        "purpose": "Monte Carlo check of quorum intersection, plus the closed-form ML-DSA-87 cost grid.",
        "not_a_measurement_of": "NJIT hardware, a cluster consensus run, NS-3, or IBM Quantum.",
        "n_pairs_per_committee": n_pairs,
        "workers": workers,
        "elapsed_sec": elapsed,
        "intersection": sampled,
        "violations": int(sum(row["violations"] for row in sampled)),
        "cost_grid": cost_grid(committees),
    }
    out_dir = ROOT / "lab" / "njit" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "smoke.json" if args.profile == "smoke" else "lab.json"
    path = out_dir / name
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"committees {len(sampled)} violations {report['violations']} elapsed {elapsed}s -> {path}")


if __name__ == "__main__":
    main()
