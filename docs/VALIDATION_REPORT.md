# Validation report

**Paper.** QH-BFT: A Quantum-Adaptive Hierarchical Byzantine Fault-Tolerant Consensus Framework with Trust-Weighted Quorum Rotation and Adaptive Verification for U.S. Critical Infrastructure. Research concept paper, Md Farhad Kabir, April 2026. Project name QuantumShield.

**Repository.** [farhadkusc/quantumshield-qhbft](https://github.com/farhadkusc/quantumshield-qhbft), package 0.2.3, commit `20f465e` (`uploaded as public`).

**Checked against.** `benchmarks/results/evaluation.json`, `src/qhbft/costs.py`, `src/qhbft/protocol.py`, `src/qhbft/safety.py`, `data/published_costs.json`, README.

**Report date.** 20 October 2026.

## 1. Purpose

This report checks the concept paper against the public repository. The paper states that empirical results are not yet available and leaves Table 8.4 empty. This report does not fill that table. It checks the formulas and the parameter table that the paper does give.

## 2. What the paper specifies

Section 5 specifies a round with PRE-PREPARE, PREPARE, and COMMIT, an empty-block fallback, trust-tier quorum rotation, and a signature rule: ML-DSA-87 by default, ML-DSA-65 only under high load in a non-NSS setting, and never during view change.

Section 6 sketches safety, liveness, and Byzantine tolerance for `N ≥ 3f+1` and quorum `2f+1`, and defers the trust-weighted proof.

Section 7 writes the cost model

`C(N) = N² · (α · S + β · V) + γ · D`

and the bandwidth bound `T(N) ≤ B / (N² · S)`. It states a signature-size ratio of about 48:1 (4,627 / 96) and a first-order throughput of about 5.4 transactions per second at N = 64, ML-DSA-87, and 1 Gbps.

Section 8 plans a Docker and Kubernetes testbed with NS-3 delay, at N = 4, 16, and 64, against PBFT-ECDSA, naive PBFT with ML-DSA, and HotStuff with ML-DSA. The reported columns are transactions per second, latency, CPU percent, bandwidth in MB/s, and recovery time.

## 3. What the repository computes

A closed-form byte count and critical-path time for one decision. There is no network, no container cluster, and no consensus loop.

Signature lengths are FIPS 204 Table 2 (13 August 2024): ML-DSA-44 = 2,420 bytes, ML-DSA-65 = 3,309, ML-DSA-87 = 4,627. Sign and verify times are the PQShield NIST Signature Zoo medians for an Intel Xeon Platinum 8488C, published 22 September 2026, 1,000 iterations: ML-DSA-87 sign 96.7 µs, verify 54.1 µs. Those times are cited, not remeasured. ECDSA-P384 is carried as 96 bytes. Its critical path is null because no ECDSA timing from that host is in the file.

One-way delay defaults to 20 ms. Critical path is `hops × delay + sign time + verify time`.

| Pattern | Messages | Hops | Verifies on the path |
| --- | --- | ---: | --- |
| `pbft` | `n + 2n(n−1)` | 3 | `1 + 2(q−1)` |
| `qh-quorum` | same, with `q = 2f+1` in place of `n` | 3 | same in `q` |
| `hotstuff-linear` | `3n`. Quorum certificate is one signature. Aggregation is assumed. FIPS 204 does not define it. | 2 | `1 + q` |
| `hotstuff-raw-qc` | proposal and votes, plus a certificate of `q` raw signatures broadcast to `n` | 2 | `1 + q` |

`select_signature` follows Section 5.5: ML-DSA-87 if fallback, threat HIGH, or NSS; otherwise ML-DSA-65 only when load is above 0.75.

`evaluation.json` is stamped `version` 0.2.0. The package version is 0.2.3.

## 4. Numerical results

From `benchmarks/results/evaluation.json`. Bytes are exact. Times are milliseconds.

| Protocol | N | Scheme | Bytes | MB | Critical path | Crypto on that path |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| pbft | 4 | ECDSA-P384 | 2,688 | 0.003 | — | — |
| pbft | 4 | ML-DSA-87 | 129,556 | 0.130 | 60.561 | 0.561 |
| qh-quorum | 4 | ML-DSA-87 | 69,405 | 0.069 | 60.561 | 0.561 |
| qh-quorum | 4 | ML-DSA-65 | 49,635 | 0.050 | 60.402 | 0.402 |
| hotstuff-linear | 4 | ML-DSA-87 | 55,524 | 0.056 | 40.410 | 0.410 |
| hotstuff-raw-qc | 4 | ML-DSA-87 | 92,540 | 0.093 | 40.410 | 0.410 |
| pbft | 16 | ECDSA-P384 | 47,616 | 0.048 | — | — |
| pbft | 16 | ML-DSA-87 | 2,294,992 | 2.295 | 61.426 | 1.426 |
| qh-quorum | 16 | ML-DSA-87 | 1,068,837 | 1.069 | 61.426 | 1.426 |
| qh-quorum | 16 | ML-DSA-65 | 764,379 | 0.764 | 60.957 | 0.957 |
| hotstuff-linear | 16 | ML-DSA-87 | 222,096 | 0.222 | 40.843 | 0.843 |
| hotstuff-raw-qc | 16 | ML-DSA-87 | 962,416 | 0.962 | 40.843 | 0.843 |
| pbft | 64 | ECDSA-P384 | 780,288 | 0.780 | — | — |
| pbft | 64 | ML-DSA-87 | 37,608,256 | 37.608 | 64.889 | 4.889 |
| qh-quorum | 64 | ML-DSA-87 | 16,911,685 | 16.912 | 64.889 | 4.889 |
| qh-quorum | 64 | ML-DSA-65 | 12,094,395 | 12.094 | 63.178 | 3.178 |
| hotstuff-linear | 64 | ML-DSA-87 | 888,384 | 0.888 | 42.574 | 2.574 |
| hotstuff-raw-qc | 64 | ML-DSA-87 | 13,325,760 | 13.326 | 42.574 | 2.574 |

Safety check in the same file: `n = 4`, `f = 1`, 6 quorum pairs, 0 pairs that fail to intersect.

At N = 64 the quorum pattern cuts the ML-DSA-87 byte count from 37.61 MB to 16.91 MB and leaves the critical path unchanged, because `q = 43` and the replica still verifies `O(f)` signatures. The linear HotStuff row is 0.89 MB. The raw-certificate row is 13.33 MB, so most of that reduction depends on treating the certificate as one signature.

## 5. Arithmetic check

**Sizes.** 4,627 / 96 = 48.20. The paper's "approximately 48-fold" matches FIPS 204.

**PBFT, N = 64, ML-DSA-87.** Messages = 64 + 2 × 64 × 63 = 8,128. Bytes = 8,128 × 4,627 = 37,608,256. Matches the file.

**Quorum, N = 64.** `f = 21`, `q = 43`. Messages = 43 + 2 × 43 × 42 = 3,655. Bytes = 3,655 × 4,627 = 16,911,685. Matches the file.

**HotStuff linear, N = 64.** 3 × 64 × 4,627 = 888,384. Matches the file.

**Critical path, PBFT, N = 64.** Verifies = 1 + 2 × 42 = 85. Signs = 3. Crypto = (3 × 96.7 + 85 × 54.1) / 1,000 = 4.889 ms. Path = 3 × 20 + 4.889 = 64.889 ms. Matches the file.

**Paper throughput line.** Section 7.3 states about 5.4 transactions per second from `T ≤ B / (N² · S)` at 1 Gbps, N = 64, S = 4,627.

`N² · S` = 4,096 × 4,627 = 18,952,192 bytes. One gigabit per second is 125,000,000 bytes per second. The quotient is 6.60, not 5.4. The paper's stated 5.4 does not follow from the formula and the inputs printed next to it.

The repository does not use `N²` as the message count. Its PBFT pattern has 8,128 signatures, 37.61 MB. At 125 MB/s that volume takes 0.301 s to move, about 3.3 decisions per second if a node had to absorb the whole pattern. That figure is not a measured throughput.

## 6. Claim check

| Paper claim | Repository | Result |
| --- | --- | --- |
| FIPS 204 sizes for ML-DSA-44, 65, 87 | Same integers | Match |
| ML-DSA-87 versus ECDSA-P384 ≈ 48× | 48.20× on length | Match |
| Signature rule in §5.5 | `select_signature` | Match |
| Any two quorums of `2f+1` intersect in at least `f+1` | Stated, and exhaustive at N = 4 | Match for the unweighted quorum |
| Trust-weighted quorum proof | Rotation helper exists. The deferred proof is still deferred. | Open, as the paper says |
| PRE-PREPARE / PREPARE / COMMIT execution | Cost formulas only | Absent |
| ML-KEM session keys | Not in the cost model | Absent |
| Empty-block fallback as a running path | Flag on the signature rule only | Partial |
| Docker, Kubernetes, NS-3, N = 4 / 16 / 64 deployment | N enters the formula. No testbed. | Absent |
| TPS, CPU percent, recovery time | Not measured | Absent |
| Latency | Critical-path sum of assumed delay and cited microbenchmarks | Partial. Not an end-to-end measurement. |
| Verification 100× to 1,000× versus ECDSA | ECDSA time is null in the file | Not tested |
| Section 4.2 attacks: flooding, verification DoS, withheld quorum, leader targeting, harvest-now, side channel | Not implemented. Grey Harbor sets threat to HIGH on a synthetic roster so the selector stays on ML-DSA-87. | Absent |
| Table 8.4 | Columns in the paper are not the columns in `evaluation.json` | Do not copy these numbers into Table 8.4 |

## 7. Finding

The repository confirms the FIPS sizes, the 48× length ratio, the signature-selection rule, the classical quorum intersection, and the byte arithmetic of four message patterns. At a 20 ms one-way delay the critical path is the network term. Cryptographic time on the cited microbenchmark is a few milliseconds.

The repository does not confirm throughput, CPU, recovery, or the paper's 5.4 transactions per second. That 5.4 does not follow from the formula in Section 7.3. The paper's statement that testbed results are not yet available remains accurate.

## 8. Source of the numbers

Regenerate with:

```bash
python3 benchmarks/run_benchmark.py
```

Lengths and cited timings are in `data/published_costs.json`.
