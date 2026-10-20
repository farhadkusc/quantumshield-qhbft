"""Synthetic deployment scenarios.

See data/dummy/README.md. Cryptographic microseconds come from
data/published_costs.json. One-way delays in the fixture are assumptions.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from . import __version__
from .costs import decision_cost
from .protocol import select_signature

ROOT = Path(__file__).resolve().parents[2]
DUMMY = ROOT / "data" / "dummy"
STRICT = {"nss", "cnsa-aligned"}

STATEMENT = "Synthetic fixture. Organization names are scenario labels. assumed_one_way_ms is the delay input."


def load_organizations() -> list[dict]:
    with (DUMMY / "organizations.csv").open(newline="") as f:
        return list(csv.DictReader(f))


def score_attack_scenario() -> dict:
    """Grey Harbor inject: threat goes HIGH, so every blue-cell row locks to ML-DSA-87."""
    scenario = json.loads((DUMMY / "attack_scenario.json").read_text())
    phase = next(item for item in scenario["phases"] if item["id"] == "PH1")
    orgs = {org["org_id"]: org for org in load_organizations()}
    blue = []
    for org_id in scenario["blue_cell"]:
        org = orgs[org_id]
        nss = org["policy_profile"] in STRICT
        load = float(org["scenario_load"])
        fallback = org["scenario_fallback"] == "1"
        baseline = select_signature(load, org["scenario_threat"], nss, fallback)
        inject = select_signature(load, phase["threat"], nss, fallback)
        delay = float(org["assumed_one_way_ms"])
        n = int(org["committee_n"])
        before = decision_cost("qh-quorum", n, baseline, one_way_ms=delay)
        after = decision_cost("qh-quorum", n, inject, one_way_ms=delay)
        blue.append(
            {
                "org_id": org_id,
                "baseline_scheme": baseline,
                "inject_scheme": inject,
                "bytes_baseline": before["bytes"],
                "bytes_inject": after["bytes"],
                "critical_path_baseline_ms": before["critical_path_ms"],
                "critical_path_inject_ms": after["critical_path_ms"],
            }
        )
    return {
        "exercise_id": scenario["exercise_id"],
        "title": scenario["title"],
        "kind": scenario["kind"],
        "statement": scenario["statement"],
        "phase": phase["id"],
        "threat": phase["threat"],
        "signature_lock": phase["signature_lock"],
        "blue_cell": blue,
        "out_of_scope": scenario["out_of_scope"],
        "sites": [site["id"] for site in scenario["sites"]],
        "n_step_ups": sum(row["baseline_scheme"] != row["inject_scheme"] for row in blue),
    }


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
        "attack_scenario": score_attack_scenario(),
    }
