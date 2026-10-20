# QH-BFT / QuantumShield

Quantum-adaptive hierarchical Byzantine fault-tolerant consensus prototype for U.S. critical infrastructure under CNSA 2.0.

Author: **Md Farhad Kabir**

## Package

| Path | Role |
| --- | --- |
| `src/qhbft/protocol.py` | Tiers, trust-weighted quorum, primary rotation, adaptive ML-DSA selection, bandwidth bound, round simulation |
| `benchmarks/run_benchmark.py` | Sweep at N = 4, 16, 64 |
| `docs/TECHNICAL_REPORT.md` | What is proved here and what is only bounded |
| `docs/PROTOCOL.md` | Round structure |
| `tests/test_protocol.py` | Intersection, signature policy, quorum size |

## Run

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest tests/test_protocol.py
python3 benchmarks/run_benchmark.py
```

## What the numbers mean

`adaptive_tps_bound` is

\[
T(N) \le \frac{B}{\mathrm{fanout}\cdot N^2 \cdot S}
\]

at \(B = 1\,\mathrm{Gbps}\). \(S\) is the FIPS 204 signature size used that round (4627 bytes for ML-DSA-87, 3309 for ML-DSA-65). Fanout shrinks when only the \(2f+1\) quorum speaks. The ECDSA and naive-ML-DSA columns use fanout 1, i.e. every validator speaks.

This is the complexity argument from the concept paper, evaluated numerically. It is not a Docker/NS-3 testbed result. Safety in the simulator is the combinatorial quorum intersection (any two sets of size \(2f+1\) on \(n=3f+1\) intersect), which the unit test checks exhaustively for \(n=4\).

## Signature policy

- NSS required, threat HIGH, or empty-block fallback: **ML-DSA-87**
- Otherwise, under high load and non-NSS: **ML-DSA-65**
- Default: **ML-DSA-87**

## License

MIT. See `LICENSE`.
