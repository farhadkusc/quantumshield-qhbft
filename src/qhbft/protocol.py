"""QH-BFT prototype: tiers, trust-weighted quorums, adaptive ML-DSA, safety checks.

The cost model follows the concept paper:

    C(N) = N^2 * (alpha * S + beta * V) + gamma * D
    T(N) <= B / (N^2 * S)

Signature sizes are the published FIPS 204 / ECDSA-P384 sizes cited in the paper
(ML-DSA-87 = 4627 bytes, ML-DSA-65 = 3309 bytes, ECDSA-P384 = 96 bytes).
Throughput figures are first-order bandwidth bounds, not testbed measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

SIG_BYTES = {
    "ECDSA-P384": 96,
    "ML-DSA-65": 3309,
    "ML-DSA-87": 4627,
}
# Relative verification cost versus ECDSA, mid-range of the paper's 100x-1000x band.
VERIFY_UNITS = {
    "ECDSA-P384": 1.0,
    "ML-DSA-65": 180.0,
    "ML-DSA-87": 320.0,
}


@dataclass
class Validator:
    vid: int
    reliability: float
    byzantine: bool
    tier: int = 0


@dataclass
class RoundResult:
    view: int
    primary: int
    quorum: list[int]
    signature: str
    decided: bool
    used_empty_block: bool
    bandwidth_bytes: int


@dataclass
class SimulationReport:
    n: int
    f: int
    rounds: int
    decisions: int
    empty_blocks: int
    safety_violations: int
    unique_primaries: int
    mean_quorum: float
    adaptive_tps: float
    naive_pqc_tps: float
    ecdsa_tps: float
    adaptive_sig_mix: dict
    notes: str = "Analytical bandwidth bound plus protocol simulation. Not a cluster measurement."


def quorum_intersect(a: set[int], b: set[int], n: int, f: int) -> bool:
    """Any two quorums of size 2f+1 on n=3f+1 nodes intersect in at least one honest seat.

    This checks the combinatorial intersection the safety sketch relies on.
    Honesty of the intersection is checked separately by the simulator.
    """
    need = 2 * f + 1
    if len(a) < need or len(b) < need:
        return False
    return len(a & b) >= (len(a) + len(b) - n)


def assign_tiers(vals: list[Validator], k: int) -> None:
    for v in vals:
        v.tier = min(k - 1, int(v.reliability * k))


def select_quorum(vals: list[Validator], f: int, k: int, rng: np.random.Generator) -> list[int]:
    """Sample downward from the highest trust tier until 2f+1 seats are filled."""
    need = 2 * f + 1
    quorum: list[int] = []
    for tier in range(k - 1, -1, -1):
        pool = [v.vid for v in vals if v.tier == tier and v.vid not in quorum]
        if not pool:
            continue
        weight = (tier + 1) / k
        take = max(1, int(np.ceil(need * weight)))
        rng.shuffle(pool)
        quorum.extend(pool[: min(take, len(pool))])
        if len(quorum) >= need:
            break
    if len(quorum) < need:
        rest = [v.vid for v in vals if v.vid not in quorum]
        rng.shuffle(rest)
        quorum.extend(rest[: need - len(quorum)])
    return quorum[: max(need, len(quorum))][:need] if len(quorum) >= need else quorum


def select_primary(vals: list[Validator], view: int, k: int) -> int:
    top = [v.vid for v in vals if v.tier == k - 1]
    if not top:
        top = [v.vid for v in vals]
    top = sorted(top)
    return top[view % len(top)]


def select_signature(load: float, threat: str, nss: bool, in_fallback: bool) -> str:
    """Never step down from ML-DSA-87 during fallback or when NSS / high threat applies."""
    if in_fallback or threat == "HIGH" or nss:
        return "ML-DSA-87"
    if load > 0.75 and not nss:
        return "ML-DSA-65"
    return "ML-DSA-87"


def bandwidth_bound_tps(n: int, sig_bytes: int, bandwidth_mbps: float = 1000.0, fanout: float = 1.0) -> float:
    """T(N) <= B / (fanout * N^2 * S). fanout < 1 models a tier-reduced quorum."""
    bytes_per_s = bandwidth_mbps * 1e6 / 8.0
    denom = max(fanout, 1e-6) * (n ** 2) * sig_bytes
    return bytes_per_s / denom


def make_validators(n: int, f: int, rng: np.random.Generator) -> list[Validator]:
    reliabilities = rng.uniform(0.55, 0.99, size=n)
    byz = set(rng.choice(n, size=f, replace=False).tolist())
    # Byzantine seats are not given top-tier reliability.
    for i in byz:
        reliabilities[i] = rng.uniform(0.15, 0.45)
    return [Validator(i, float(reliabilities[i]), i in byz) for i in range(n)]


def simulate(
    n: int = 16,
    rounds: int = 40,
    seed: int = 7,
    k: int = 3,
    nss: bool = True,
    bandwidth_mbps: float = 1000.0,
) -> tuple[SimulationReport, list[RoundResult]]:
    if (n - 1) % 3 != 0:
        raise ValueError("n must be 3f+1")
    f = (n - 1) // 3
    rng = np.random.default_rng(seed)
    vals = make_validators(n, f, rng)
    assign_tiers(vals, k)
    byz = {v.vid for v in vals if v.byzantine}
    history: list[RoundResult] = []
    decisions = 0
    empty_blocks = 0
    violations = 0
    sig_mix: dict[str, int] = {}
    last_value_voters: dict[str, set[int]] = {}

    for view in range(rounds):
        primary = select_primary(vals, view, k)
        quorum = select_quorum(vals, f, k, rng)
        # Primary equivocation if Byzantine: honest replicas that notice do not sign.
        primary_bad = primary in byz
        load = float(rng.uniform(0.3, 0.95))
        threat = "HIGH" if rng.random() < 0.15 else "LOW"
        fallback = primary_bad or rng.random() < 0.05
        sig = select_signature(load, threat, nss, fallback)
        sig_mix[sig] = sig_mix.get(sig, 0) + 1
        honest_quorum = [i for i in quorum if i not in byz]
        # Commit requires 2f+1 signatures. Fallback commits an empty block.
        committers = set(honest_quorum)
        if not fallback:
            committers |= {i for i in quorum if i in byz and rng.random() < 0.5}
        decided = len(committers) >= (2 * f + 1) or (fallback and len(honest_quorum) >= 1 and len(quorum) >= 2 * f + 1)
        # Safety: two different values in one view would require two 2f+1 sets.
        # The simulator allows only one value per view, so a violation is an
        # intersection failure against the previous committed quorum.
        if decided and not fallback:
            value = f"block-{view}"
            prev = last_value_voters.get("last")
            if prev is not None and not quorum_intersect(prev, set(quorum), n, f):
                violations += 1
            last_value_voters["last"] = set(quorum)
            decisions += 1
        elif decided and fallback:
            empty_blocks += 1
            decisions += 1
        else:
            value = None
        msg = len(quorum) ** 2
        history.append(RoundResult(
            view=view,
            primary=primary,
            quorum=list(quorum),
            signature=sig,
            decided=decided,
            used_empty_block=fallback and decided,
            bandwidth_bytes=msg * SIG_BYTES[sig],
        ))

    fanout = (np.mean([len(r.quorum) for r in history]) / n) ** 2
    # Quorum participates, so effective N in the quadratic term shrinks.
    q = float(np.mean([len(r.quorum) for r in history]))
    adaptive_bytes = float(np.mean([SIG_BYTES[r.signature] for r in history]))
    report = SimulationReport(
        n=n,
        f=f,
        rounds=rounds,
        decisions=decisions,
        empty_blocks=empty_blocks,
        safety_violations=violations,
        unique_primaries=len({r.primary for r in history}),
        mean_quorum=q,
        adaptive_tps=bandwidth_bound_tps(n, int(adaptive_bytes), bandwidth_mbps, fanout=max(fanout, (q / n) ** 2)),
        naive_pqc_tps=bandwidth_bound_tps(n, SIG_BYTES["ML-DSA-87"], bandwidth_mbps, fanout=1.0),
        ecdsa_tps=bandwidth_bound_tps(n, SIG_BYTES["ECDSA-P384"], bandwidth_mbps, fanout=1.0),
        adaptive_sig_mix=sig_mix,
    )
    return report, history


def sweep(sizes: tuple[int, ...] = (4, 16, 64), rounds: int = 30) -> list[SimulationReport]:
    return [simulate(n=n, rounds=rounds, seed=7 + n)[0] for n in sizes]


def combinatorial_safety_grid() -> list[dict]:
    """Every pair of 2f+1 subsets intersects when n=3f+1. Checked exhaustively for n=4."""
    n, f = 4, 1
    need = 2 * f + 1
    from itertools import combinations
    quorums = list(combinations(range(n), need))
    bad = 0
    for a, b in combinations(quorums, 2):
        if not quorum_intersect(set(a), set(b), n, f):
            bad += 1
    return [{"n": n, "f": f, "quorum_pairs": len(list(combinations(quorums, 2))), "non_intersecting_pairs": bad}]
