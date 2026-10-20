"""Honest execution of one QH-BFT decision, and the two bandwidth readings.

Message counts follow the broadcast steps: the primary sends PRE-PREPARE,
every validator sends PREPARE, every validator sends COMMIT after 2f+1
prepares. Bandwidth is reported only as B/(N·S) per node and B/(N²·S)
for the network. B is the byte rate of the link and S is the signature
length.
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


def per_node_bound(n: int, signature_bytes: int, bandwidth_bps: float = 1_000_000_000) -> float:
    """B / (N * S) at B = 1 Gbps, in decisions per second."""
    return (bandwidth_bps / 8.0) / (n * signature_bytes)


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
    Bandwidth uses two denominators. The per-node bound is B/(N·S). The
    network bound is B/(N²·S). At 1 Gbps, B is 125,000,000 bytes per second.
    """
    if sign_seconds is None or verify_seconds is None:
        raise ValueError("sign and verify times are required")
    round_ = honest_round(n)
    q = round_["quorum"]
    messages = round_["messages"]
    q_messages = q + 2 * q * (q - 1)
    bytes_per_s = bandwidth_bps / 8.0
    latency = 3 * one_way_seconds + 3 * sign_seconds + (1 + 2 * (q - 1)) * verify_seconds
    return {
        "n": n,
        "quorum": q,
        "messages": messages,
        "quorum_messages": q_messages,
        "signature_bytes": signature_bytes,
        "aggregate_bytes": messages * signature_bytes,
        "quorum_bytes": q_messages * signature_bytes,
        "critical_path_verifies": 1 + 2 * (q - 1),
        "critical_path_signs": 3,
        "latency_seconds": latency,
        "per_node_bound_per_s": bytes_per_s / (n * signature_bytes),
        "paper_n2_bound_per_s": bytes_per_s / (n * n * signature_bytes),
    }


def fallback_comparison(
    n: int = 64,
    signature_bytes: int = 4627,
    bandwidth_bps: float = 1_000_000_000,
) -> dict:
    """PBFT view-change against the empty-block fallback, leading order.

    View-change is N^3 signatures. The empty-block fallback is N^2 signatures.
    The exact broadcast count is n(n - 1), reported beside the N^2 term.
    Byte and time figures use S and a 1 Gbps link. They are for the round in
    which no replica holds a prepared value.
    """
    byte_rate = bandwidth_bps / 8.0
    view_signatures = n ** 3
    fallback_signatures = n ** 2
    exact_messages = n * (n - 1)

    def side(signatures: int) -> dict:
        nbytes = signatures * signature_bytes
        whole = nbytes / byte_rate
        return {
            "signatures": signatures,
            "bytes": nbytes,
            "whole_exchange_s": whole,
            "per_node_s": whole / n,
        }

    view = side(view_signatures)
    fallback = side(fallback_signatures)
    return {
        "n": n,
        "signature_bytes": signature_bytes,
        "bytes_per_s": byte_rate,
        "view_change": view,
        "empty_block_leading": fallback,
        "empty_block_exact_messages": exact_messages,
        "qualification": (
            "For a round in which a replica holds a prepared value, the fallback "
            "carries it forward and adds signatures. The figures are for the round "
            "in which none does."
        ),
    }