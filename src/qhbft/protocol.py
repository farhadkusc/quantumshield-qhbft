"""Quorum rotation and signature policy, exercised by the tests.

The byte and latency numbers live in costs.py. This module only decides
who speaks and which FIPS 204 parameter set is allowed.
"""

from __future__ import annotations

import numpy as np


def select_signature(load: float, threat: str, nss: bool, in_fallback: bool) -> str:
    """ML-DSA-87 unless the context is non-NSS, not in fallback, and loaded.

    High threat, NSS, and empty-block fallback never step down. Category 5
    stays the default. ML-DSA-65 is the only step-down, and only then.
    """
    if in_fallback or threat == "HIGH" or nss:
        return "ML-DSA-87"
    if load > 0.75:
        return "ML-DSA-65"
    return "ML-DSA-87"


def assign_tiers(reliability: np.ndarray, k: int = 3) -> np.ndarray:
    tiers = np.minimum(k - 1, np.floor(reliability * k).astype(int))
    return tiers


def quorum_ids(reliability: np.ndarray, n_faulty: int, rng: np.random.Generator, k: int = 3) -> list[int]:
    """Fill 2f+1 seats from the highest tier downward."""
    n = len(reliability)
    if n != 3 * n_faulty + 1:
        raise ValueError("n must equal 3f+1")
    need = 2 * n_faulty + 1
    tiers = assign_tiers(reliability, k)
    chosen: list[int] = []
    for tier in range(k - 1, -1, -1):
        pool = [i for i in range(n) if tiers[i] == tier and i not in chosen]
        rng.shuffle(pool)
        weight = (tier + 1) / k
        take = max(1, int(np.ceil(need * weight)))
        chosen.extend(pool[: min(take, len(pool))])
        if len(chosen) >= need:
            break
    if len(chosen) < need:
        rest = [i for i in range(n) if i not in chosen]
        rng.shuffle(rest)
        chosen.extend(rest[: need - len(chosen)])
    return chosen[:need]


def primary_id(reliability: np.ndarray, view: int, k: int = 3) -> int:
    tiers = assign_tiers(reliability, k)
    top = sorted(i for i in range(len(reliability)) if tiers[i] == k - 1)
    if not top:
        top = list(range(len(reliability)))
    return top[view % len(top)]
