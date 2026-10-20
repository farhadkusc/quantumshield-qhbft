"""Synthetic deployment scenarios. Not a measurement and not an IBM Quantum run.

See data/dummy/README.md. Cryptographic microseconds still come only from
data/published_costs.json. One-way delays in the fixture are assumptions.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from . import __version__
from .costs import decision_cost
from .protocol import select_signature

ROOT = Path(__file__).resolve().parents[2]
DUMMY = ROOT / "data" / "dummy"
STRICT = {"nss", "cnsa-aligned"}

STATEMENT = (
    "Synthetic fixture. Organization names are scenario labels, not sources. "
    "assumed_one_way_ms is not a measured latency. Do not cite this object as an experimental result."
)


def load_organizations() -> list[dict]:
    with (DUMMY / "organizations.csv").open(newline="") as f:
        return list(csv.DictReader(f))


def run_dummy() -> dict:
    rows = []
    for org in load_organizations():
        nss = org["policy_profile"] in STRICT
        load = float(org["scenario_load"])
        threat = org["scenario_threat"]
        fallback = org["scenario_fallback"] == "1"
        scheme = select_signature(load, threat, nss, fallback)
        delay = float(org["assumed_one_way_ms"])
        cost = decision_cost("qh-quorum", int(org["committee_n"]), scheme, one_way_ms=delay)
        rows.append(
            {
                "org_id": org["org_id"],
                "display_name": org["display_name"],
                "klass": org["klass"],
                "policy_profile": org["policy_profile"],
                "selector_nss_input": nss,
                "scenario_threat": threat,
                "scenario_load": load,
                "scenario_fallback": fallback,
                "scheme": scheme,
                "committee_n": cost["n"],
                "assumed_one_way_ms": delay,
                "bytes": cost["bytes"],
                "critical_path_ms": cost["critical_path_ms"],
                "notes": org["notes"],
            }
        )
    return {
        "kind": "synthetic-fixture",
        "package": "quantumshield-qhbft",
        "package_version": __version__,
        "statement": STATEMENT,
        "n_organizations": len(rows),
        "counts": dict(Counter(r["klass"] for r in rows)),
        "scheme_counts": dict(Counter(r["scheme"] for r in rows)),
        "rows": rows,
    }
