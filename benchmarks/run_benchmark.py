#!/usr/bin/env python3
"""Write the closed-form cost table parameterized by published ML-DSA timings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qhbft.costs import load_costs, sweep  # noqa: E402
from qhbft.roundsim import complexity, empty_block_fallback, honest_round  # noqa: E402
from qhbft.safety import exhaustive_n4  # noqa: E402


def main() -> None:
    payload = {
        "package": "quantumshield-qhbft",
        "version": "0.2.3",
        "safety_n4": exhaustive_n4(),
        "cost_sources": load_costs()["sources"],
        "one_way_delay_ms": 20,
        "honest_rounds": [honest_round(n) for n in (4, 16, 64)],
        "empty_block": [empty_block_fallback(n) for n in (4, 16, 64)],
        "complexity": [
            complexity(n, 4627, verify_seconds=54.1e-6, one_way_seconds=0.020) for n in (4, 16, 64)
        ],
        "rows": sweep(),
        "disclaimer": (
            "Bytes are message-pattern times FIPS signature length. "
            "Milliseconds add published PQShield verify/sign medians on the critical path."
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
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
