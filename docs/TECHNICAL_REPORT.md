# QH-BFT technical report

**Package version:** 0.1.0  
**Author:** Md Farhad Kabir

## Model

- Partial synchrony is assumed, not simulated. The round loop does not model GST or packet delay.
- \(n = 3f+1\). Byzantine seats are the \(f\) lowest reliability draws and cannot sit in the top tier.
- Tiers: \(T(i) = \lfloor R(i) \cdot k \rfloor\) with \(k = 3\).
- Quorum: sample from the top tier downward until \(2f+1\) validators are seated.
- Primary: round-robin inside the top tier.
- Empty-block fallback: a Byzantine or timed-out primary advances the view without an \(O(n^3)\) view-change exchange. The simulator counts that path; it does not exchange the messages.

## Safety check that is actually executed

For \(n=4, f=1\), every pair of 3-subsets intersects. The predicate used is

\[
|A \cap B| \ge |A| + |B| - n
\]

which is the pigeonhole lower bound and is tight. The \(n=16\) and \(n=64\) runs assert the same predicate against successive committed quorums and record `safety_violations`.

## What is not in this package

Full PBFT/HotStuff implementations, constant-time ML-DSA, NS-3, Kubernetes, or CPU profiles. Those remain the Phase-2 testbed in the concept paper. Cryptographic verification is a cost coefficient, not a call into liboqs.

## Reproduce

`python3 benchmarks/run_benchmark.py`
