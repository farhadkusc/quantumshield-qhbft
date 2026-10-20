"""Combinatorial quorum intersection, checked rather than assumed.

For n = 3f+1, any two sets of size 2f+1 intersect in at least f+1 seats,
hence in at least one honest seat if at most f seats are Byzantine.
"""

from __future__ import annotations

from itertools import combinations


def f_of(n: int) -> int:
    if (n - 1) % 3 != 0 or n < 4:
        raise ValueError("n must be 3f+1")
    return (n - 1) // 3


def intersects_honestly(a: set[int], b: set[int], n: int) -> bool:
    f = f_of(n)
    need = 2 * f + 1
    if len(a) < need or len(b) < need:
        return False
    return len(a & b) >= f + 1


def exhaustive_n4() -> dict:
    n, f = 4, 1
    quorums = [set(q) for q in combinations(range(n), 2 * f + 1)]
    pairs = list(combinations(quorums, 2))
    bad = sum(1 for a, b in pairs if not intersects_honestly(a, b, n))
    return {"n": n, "f": f, "pairs": len(pairs), "non_intersecting": bad}
