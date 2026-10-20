"""Honest execution of one QH-BFT decision, and dimensionally separate bounds.

Message counts follow the broadcast steps: the primary sends PRE-PREPARE,
every validator sends PREPARE, every validator sends COMMIT after 2f+1
prepares. Bytes, seconds, and decisions per second are reported as separate
quantities.
"""

from __future__ import annotations


def honest_round(n: int) -> dict:
    if (n - 1) % 3 != 0 or n < 4:
        raise ValueError("n must be 3f+1 and at least 4")
    f = (n - 1) // 3
    q = 2 * f + 1
    preprepare = n - 1
    prepare = n * (n - 1)
    commit = n * (n - 1)
    return {
        "n": n,
        "f": f,
        "quorum": q,
        "preprepare": preprepare,
        "prepare": prepare,
        "commit": commit,
        "messages": preprepare + prepare + commit,
        "decided": True,
    }


def empty_block_fallback(n: int) -> dict:
    """Each validator broadcasts one PREPARE for the empty block."""
    if (n - 1) % 3 != 0 or n < 4:
        raise ValueError("n must be 3f+1 and at least 4")
    f = (n - 1) // 3
    return {
        "n": n,
        "f": f,
        "quorum": 2 * f + 1,
        "messages": n * (n - 1),
        "advanced": True,
    }


def throughput_bound(n: int, signature_bytes: int, bandwidth_bps: float = 1_000_000_000) -> float:
    """B / (N^2 * S) at B = 1 Gbps, in decisions per second."""
    return (bandwidth_bps / 8.0) / (n * n * signature_bytes)


def link_budget(
    n: int,
    signature_bytes: int,
    sign_seconds: float,
    verify_seconds: float,
    one_way_seconds: float = 0.020,
    bandwidth_bps: float = 1_000_000_000,
) -> dict:
    """One honest decision.

    The critical path is three hops. The primary signs once per hop. A replica
    verifies one PRE-PREPARE and q-1 messages in each of PREPARE and COMMIT.
    A 1 Gbps link is 125,000,000 bytes per second. The primary bound divides
    that by the bytes the primary sends. The aggregate bound divides it by
    every signature byte in the round. The N^2 bound uses N^2 instead of the
    message count. None of these is a measured transaction rate.
    """
    if sign_seconds is None or verify_seconds is None:
        raise ValueError("sign and verify times are required")
    round_ = honest_round(n)
    q = round_["quorum"]
    messages = round_["messages"]
    q_messages = q + 2 * q * (q - 1)
    primary_bytes = 3 * (n - 1) * signature_bytes
    replica_bytes = 2 * (n - 1) * signature_bytes
    aggregate_bytes = messages * signature_bytes
    quorum_bytes = q_messages * signature_bytes
    latency = 3 * one_way_seconds + 3 * sign_seconds + (1 + 2 * (q - 1)) * verify_seconds
    bytes_per_s = bandwidth_bps / 8.0
    return {
        "n": n,
        "quorum": q,
        "messages": messages,
        "quorum_messages": q_messages,
        "signature_bytes": signature_bytes,
        "aggregate_bytes": aggregate_bytes,
        "quorum_bytes": quorum_bytes,
        "primary_egress_bytes": primary_bytes,
        "replica_egress_bytes": replica_bytes,
        "critical_path_verifies": 1 + 2 * (q - 1),
        "critical_path_signs": 3,
        "latency_seconds": latency,
        "latency_bound_per_s": 1.0 / latency,
        "primary_bandwidth_bound_per_s": bytes_per_s / primary_bytes,
        "replica_bandwidth_bound_per_s": bytes_per_s / replica_bytes,
        "aggregate_bandwidth_bound_per_s": bytes_per_s / aggregate_bytes,
        "quorum_bandwidth_bound_per_s": bytes_per_s / quorum_bytes,
        "paper_n2_bound_per_s": bytes_per_s / (n * n * signature_bytes),
    }
