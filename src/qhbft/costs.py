"""Closed-form cost of one consensus decision.

Communication counts follow the normal case, after GST, with no faults on
the critical path. Cryptographic microseconds are the published medians in
data/published_costs.json. A decision's critical-path time is

    hops * one_way_delay + sign_us * signers_on_path + verify_us * verifies_on_path

all converted to milliseconds. This is not a measured testbed latency.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_costs() -> dict:
    return json.loads((ROOT / "data" / "published_costs.json").read_text())


def scheme(name: str) -> dict:
    return load_costs()["schemes"][name]


def quorum(n: int) -> int:
    if (n - 1) % 3 != 0 or n < 4:
        raise ValueError("n must be 3f+1 and at least 4")
    return 2 * ((n - 1) // 3) + 1


def decision_cost(protocol: str, n: int, scheme_name: str, one_way_ms: float = 20.0) -> dict:
    """Byte and critical-path cost of one decision.

    protocols:
      pbft: classical three-phase all-to-all
      qh-quorum: same three phases, but only a 2f+1 quorum speaks
      hotstuff-linear: proposal, n votes to the leader, QC of one signature
        broadcast. Aggregation is assumed. ML-DSA has no FIPS aggregate, so
        this row is an upper bound on what aggregation would have to deliver.
      hotstuff-raw-qc: same, but the QC carries 2f+1 raw ML-DSA signatures
    """
    q = quorum(n)
    sig = scheme(scheme_name)["signature_bytes"]
    sign_us = scheme(scheme_name)["sign_us"]
    verify_us = scheme(scheme_name)["verify_us"]
    if protocol == "pbft":
        messages = n + 2 * n * (n - 1)
        hops = 3
        # Replica verifies the primary plus 2f prepares and 2f commits.
        verifies_on_path = 1 + 2 * (q - 1)
        signs_on_path = 3
    elif protocol == "qh-quorum":
        messages = q + 2 * q * (q - 1)
        hops = 3
        verifies_on_path = 1 + 2 * (q - 1)
        signs_on_path = 3
    elif protocol == "hotstuff-linear":
        messages = 3 * n
        hops = 2
        verifies_on_path = 1 + q  # followers verify proposal; leader verifies q votes; counted on the leader path
        signs_on_path = 2
    elif protocol == "hotstuff-raw-qc":
        messages = 2 * n  # proposal + votes
        qc_bytes_each = q * sig
        # QC broadcast is not one signature. Count it separately.
        extra_bytes = n * qc_bytes_each
        hops = 2
        verifies_on_path = 1 + q
        signs_on_path = 2
        total_bytes = messages * sig + extra_bytes
        cpu_ms = None
        if sign_us is not None and verify_us is not None:
            cpu_ms = (signs_on_path * sign_us + verifies_on_path * verify_us) / 1000.0
        return {
            "protocol": protocol,
            "n": n,
            "quorum": q,
            "scheme": scheme_name,
            "messages": messages,
            "bytes": int(total_bytes),
            "critical_path_ms": None if cpu_ms is None else round(hops * one_way_ms + cpu_ms, 3),
            "crypto_critical_path_ms": None if cpu_ms is None else round(cpu_ms, 3),
            "one_way_ms": one_way_ms,
        }
    else:
        raise ValueError(protocol)
    total_bytes = messages * sig
    cpu_ms = None
    if sign_us is not None and verify_us is not None:
        cpu_ms = (signs_on_path * sign_us + verifies_on_path * verify_us) / 1000.0
    return {
        "protocol": protocol,
        "n": n,
        "quorum": q,
        "scheme": scheme_name,
        "messages": messages,
        "bytes": int(total_bytes),
        "critical_path_ms": None if cpu_ms is None else round(hops * one_way_ms + cpu_ms, 3),
        "crypto_critical_path_ms": None if cpu_ms is None else round(cpu_ms, 3),
        "one_way_ms": one_way_ms,
    }


def sweep() -> list[dict]:
    rows = []
    for n in (4, 16, 64):
        for protocol, sch in (
            ("pbft", "ECDSA-P384"),
            ("pbft", "ML-DSA-87"),
            ("qh-quorum", "ML-DSA-87"),
            ("qh-quorum", "ML-DSA-65"),
            ("hotstuff-linear", "ML-DSA-87"),
            ("hotstuff-raw-qc", "ML-DSA-87"),
        ):
            rows.append(decision_cost(protocol, n, sch))
    return rows
