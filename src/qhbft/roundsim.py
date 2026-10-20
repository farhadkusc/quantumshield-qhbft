"""Honest execution of the QH-BFT normal case and the empty-block fallback.

Message counts follow the concept paper's broadcast steps: the primary
sends PRE-PREPARE, every validator sends PREPARE, every validator sends
COMMIT after 2f+1 prepares. The throughput bound is the paper's
T(N) <= B / (N^2 * S) with B = 1 Gbps and S the FIPS signature length.
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
    """Paper section 7.3. B is 1 Gbps, converted to bytes per second."""
    return (bandwidth_bps / 8.0) / (n * n * signature_bytes)


def complexity(n: int, signature_bytes: int, verify_seconds: float, one_way_seconds: float) -> dict:
    """C(N) = N^2 * (S + V) + D with alpha = beta = gamma = 1, in bytes, seconds, seconds."""
    messages = n * n
    return {
        "n": n,
        "signature_bytes": signature_bytes,
        "n_squared_messages": messages,
        "byte_term": messages * signature_bytes,
        "verify_term_seconds": messages * verify_seconds,
        "delay_seconds": one_way_seconds,
        "throughput_bound_per_s": throughput_bound(n, signature_bytes),
    }
