#!/usr/bin/env python3
"""Evaluate the closed-form cost formulas and write evaluation.json.

This script measures nothing. It substitutes published lengths and medians
into the message, byte, and critical-path formulas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qhbft.costs import load_costs, sweep  # noqa: E402
from qhbft.roundsim import empty_block_fallback, fallback_comparison, honest_round, link_budget  # noqa: E402
from qhbft.safety import exhaustive_n4  # noqa: E402


def main() -> None:
    payload = {
        "package": "quantumshield-qhbft",
        "version": "0.2.6",
        "safety_n4": exhaustive_n4(),
        "cost_sources": load_costs()["sources"],
        "one_way_delay_ms": 20,
        "honest_rounds": [honest_round(n) for n in (4, 16, 64)],
        "empty_block": [empty_block_fallback(n) for n in (4, 16, 64)],
        "link_budget_ml_dsa_87": [
            link_budget(
                n,
                signature_bytes=4627,
                sign_seconds=96.7e-6,
                verify_seconds=54.1e-6,
            )
            for n in (4, 16, 64)
        ],
        "fallback_comparison_n64": fallback_comparison(),
        "rows": sweep(),
        "disclaimer": (
            "benchmarks/run_benchmark.py evaluates formulas and measures nothing. "
            "Bytes are message-pattern times FIPS signature length. "
            "Milliseconds add published PQShield verify/sign medians on the critical path. "
            "The 20 ms one-way delay is an assumption."
        ),
    }
    out = ROOT / "benchmarks" / "results" / "evaluation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"{'protocol':<18} {'N':>4} {'scheme':<12} {'MB':>10} {'crit ms':>10}")
    for row in payload["rows"]:
        if row["n"] not in (4, 64):
            continue
        mb = row["bytes"] / 1e6
        crit = "" if row["critical_path_ms"] is None else f"{row['critical_path_ms']:.1f}"
        print(f"{row['protocol']:<18} {row['n']:4d} {row['scheme']:<12} {mb:10.2f} {crit:>10}")
    comp = payload["fallback_comparison_n64"]
    view = comp["view_change"]
    fallback = comp["empty_block_leading"]
    print(
        "n=64 view-change N^3 signatures",
        view["signatures"],
        "empty-block N^2 signatures",
        fallback["signatures"],
        "exact n(n-1)",
        comp["empty_block_exact_messages"],
    )
    print(
        "bytes",
        view["bytes"],
        fallback["bytes"],
        "whole-exchange s",
        view["whole_exchange_s"],
        fallback["whole_exchange_s"],
        "per-node s",
        view["per_node_s"],
        fallback["per_node_s"],
    )
    print(comp["qualification"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
