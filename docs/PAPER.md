# QH-BFT

Byte, latency, and bandwidth accounting for one Byzantine consensus decision when the signature is FIPS 204 ML-DSA.

Md Farhad Kabir

Research draft for package 0.2.5. Every figure in this draft is taken from `benchmarks/results/evaluation.json` or `benchmarks/results/dummy_evaluation.json` in farhadkusc/quantumshield-qhbft. Bytes and seconds stay in their own fields. The bandwidth readings are B / (N · S) per node and B / (N² · S) for the network.

## Abstract

An honest round has three broadcasts. The primary sends PRE-PREPARE to the other n − 1 validators. Every validator sends PREPARE to the other n − 1. Every validator sends COMMIT to the other n − 1 after it has seen q = 2f + 1 prepares. At n = 64 that is 8127 messages. With an ML-DSA-87 signature of 4627 bytes the round moves 37603629 signature bytes.

The critical path is three network hops, three signatures, and 85 verifications. At a 20 ms one-way delay, using the published medians of 96.7 microseconds to sign and 54.1 microseconds to verify, the path is 0.0648886 seconds.

A 1 Gbps link carries 125000000 bytes per second. The per-node bound is B / (N · S). At n = 64 and S = 4627 it is 422.1147611843527 decisions per second, which is about 420. The network bound is B / (N² · S) with the same B and S, which is 6.595543143505511 decisions per second. The per-node figure is N times the network figure.

## 1. Cryptographic sizes

Lengths are FIPS 204 Table 2, dated 13 August 2024, as stored in `data/published_costs.json`.

| Scheme | Public key bytes | Signature bytes | Sign, microseconds | Verify, microseconds | NIST category |
| --- | ---: | ---: | ---: | ---: | ---: |
| ML-DSA-44 | 1312 | 2420 | 46.7 | 21.6 | 2 |
| ML-DSA-65 | 1952 | 3309 | 76.1 | 34.7 | 3 |
| ML-DSA-87 | 2592 | 4627 | 96.7 | 54.1 | 5 |
| ECDSA-P384 | 49 | 96 | none | none | none |

The microsecond columns are medians published by the PQShield NIST Signature Zoo for an Intel Xeon Platinum 8488C, benchmark dated 22 September 2026, median of 1000 iterations. They are inputs to the arithmetic in this repository. They were not remeasured here. ECDSA-P384 is carried as a 96-byte signature because that is the length used in the comparison. No ECDSA timing from that host is in the cost file, so every ECDSA critical path is null.

The ratio of signature lengths ML-DSA-87 / ECDSA-P384 is 4627 / 96. The byte tables below scale with that ratio wherever the message count is the same.

## 2. Quorum intersection

A deployment size in this repository satisfies n = 3f + 1 and n ≥ 4. The quorum size is q = 2f + 1. Any two subsets of size q intersect in at least f + 1 seats. If at most f seats are Byzantine, that intersection contains at least one honest seat. The predicate is `intersects_honestly` in `src/qhbft/safety.py`.

At n = 4, f = 1, every 3-subset of a 4-set is a quorum. There are 6 unordered pairs of such quorums. The exhaustive count of pairs that fail the intersection test is 0.

## 3. Who may use the shorter signature

`select_signature(load, threat, nss, in_fallback)` in `src/qhbft/protocol.py` returns ML-DSA-87 when any of the following holds: the round is the empty-block fallback, the threat level is HIGH, or the deployment is marked NSS. If none of those holds and load is strictly above 0.75, the function returns ML-DSA-65. In every remaining case it returns ML-DSA-87. ML-DSA-44 is a stored length. It is not a return value of this rule.

Tier assignment and quorum membership are separate from the byte arithmetic. `assign_tiers` maps a reliability score R in [0, 1] to floor(R · k) clipped to k − 1, with k = 3. `quorum_ids` fills 2f + 1 seats from the highest tier downward. The sample size at a tier is the ceiling of (2f + 1) times (tier + 1) / k. `primary_id` rotates through the top tier with the view index. The byte tables do not depend on which identifiers are chosen. They depend on how many validators speak.

## 4. Honest round

The message count in `honest_round` is

M(n) = (n − 1) + 2 · n · (n − 1) = (n − 1) · (2n + 1).

The first term is PRE-PREPARE. The two remaining terms are PREPARE and COMMIT. The empty-block fallback is a single PREPARE broadcast from each validator, E(n) = n · (n − 1). Both functions require n = 3f + 1.

| n | f | Quorum | PRE-PREPARE | PREPARE | COMMIT | Messages | Empty-block messages |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1 | 3 | 3 | 12 | 12 | 27 | 12 |
| 16 | 5 | 11 | 15 | 240 | 240 | 495 | 240 |
| 64 | 21 | 43 | 63 | 4032 | 4032 | 8127 | 4032 |

Check for n = 64. PRE-PREPARE is 63. PREPARE is 64 · 63 = 4032. COMMIT is 4032. The sum is 63 + 4032 + 4032 = 8127. The empty-block count is 64 · 63 = 4032.

## 5. Critical path

`link_budget` places three signatures and 1 + 2(q − 1) verifications on the path, plus three one-way delays. For ML-DSA-87,

L(n) = 3 · 0.020 + 3 · 96.7 · 10^(−6) + (1 + 2(q − 1)) · 54.1 · 10^(−6) seconds.

At n = 64, q = 43, the verification count is 1 + 2 · 42 = 85. Then

L(64) = 0.060 + 0.0002901 + 85 · 0.0000541 = 0.060 + 0.0002901 + 0.0045985 = 0.0648886 seconds.

The same arithmetic at n = 4, where the path verifies 5 signatures, gives 0.0605606 seconds. At n = 16 the path verifies 21 signatures and takes 0.0614262 seconds.

The path moves slowly with n because the 60 ms of propagation dominates the cryptographic term. The bandwidth readings move as 1/N and 1/N².

## 6. Bandwidth bounds

A 1 Gbps link is 125000000 bytes per second. Two denominators are reported, both with S = 4627.

The per-node bound is B / (N · S). The network bound is B / (N² · S).

| n | Per-node bound | N² bound |
| ---: | ---: | ---: |
| 4 | 6753.836178949643 | 1688.4590447374107 |
| 16 | 1688.4590447374107 | 105.52869029608817 |
| 64 | 422.1147611843527 | 6.595543143505511 |

Identities at n = 64, S = 4627.

N · S = 64 · 4627 = 296128. Dividing 125000000 by 296128 gives 422.1147611843527.

N² · S = 64 · 64 · 4627 = 18952192. Dividing 125000000 by 18952192 gives 6.595543143505511.

422.1147611843527 / 6.595543143505511 = 64, so the per-node reading is the network reading multiplied by N. At n = 64 the per-node reading is about 420 decisions per second.

At n = 4 the two bounds are 6753.836178949643 and 1688.4590447374107. At n = 16 they are 1688.4590447374107 and 105.52869029608817.

## 7. Second message count

`decision_cost` in `src/qhbft/costs.py` uses a PBFT count of n + 2n(n − 1). At n = 64 that is 64 + 2 · 64 · 63 = 8128, one message above the 8127 of `honest_round`. The extra message is the difference between a pre-prepare fan-out of n and a fan-out of n − 1. Both counts are in the result file. The link-budget section uses 8127. The table in this section uses 8128 for the PBFT rows.

The qh-quorum pattern speaks with q validators: q + 2q(q − 1) messages. HotStuff-linear uses 3n messages and treats the quorum certificate as one signature. HotStuff-raw-qc uses 2n messages and then adds n · q raw signatures for the certificate broadcast. The linear row is the byte count that would follow if a certificate were a single ML-DSA signature. FIPS 204 does not define that aggregate. The raw-certificate row is the byte count when the certificate carries q ML-DSA signatures.

Critical-path milliseconds use the same sign and verify medians and a 20 ms hop. ECDSA rows have a byte count and a null critical path.

| Protocol | n | Scheme | Messages | Quorum | Bytes | Critical path ms |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| pbft | 4 | ECDSA-P384 | 28 | 3 | 2688 | none |
| pbft | 4 | ML-DSA-87 | 28 | 3 | 129556 | 60.561 |
| qh-quorum | 4 | ML-DSA-87 | 15 | 3 | 69405 | 60.561 |
| qh-quorum | 4 | ML-DSA-65 | 15 | 3 | 49635 | 60.402 |
| hotstuff-linear | 4 | ML-DSA-87 | 12 | 3 | 55524 | 40.41 |
| hotstuff-raw-qc | 4 | ML-DSA-87 | 8 | 3 | 92540 | 40.41 |
| pbft | 16 | ECDSA-P384 | 496 | 11 | 47616 | none |
| pbft | 16 | ML-DSA-87 | 496 | 11 | 2294992 | 61.426 |
| qh-quorum | 16 | ML-DSA-87 | 231 | 11 | 1068837 | 61.426 |
| qh-quorum | 16 | ML-DSA-65 | 231 | 11 | 764379 | 60.957 |
| hotstuff-linear | 16 | ML-DSA-87 | 48 | 11 | 222096 | 40.843 |
| hotstuff-raw-qc | 16 | ML-DSA-87 | 32 | 11 | 962416 | 40.843 |
| pbft | 64 | ECDSA-P384 | 8128 | 43 | 780288 | none |
| pbft | 64 | ML-DSA-87 | 8128 | 43 | 37608256 | 64.889 |
| qh-quorum | 64 | ML-DSA-87 | 3655 | 43 | 16911685 | 64.889 |
| qh-quorum | 64 | ML-DSA-65 | 3655 | 43 | 12094395 | 63.178 |
| hotstuff-linear | 64 | ML-DSA-87 | 192 | 43 | 888384 | 42.574 |
| hotstuff-raw-qc | 64 | ML-DSA-87 | 128 | 43 | 13325760 | 42.574 |

At n = 64 the PBFT ML-DSA-87 row is 8128 · 4627 = 37608256 bytes, with critical path 64.889 ms. The qh-quorum ML-DSA-87 row is 16911685 bytes. The qh-quorum ML-DSA-65 row is 12094395 bytes, which is the same message count times 3309. The HotStuff-linear ML-DSA-87 row is 888384 bytes. The HotStuff-raw-qc row is 13325760 bytes. The PBFT ECDSA-P384 row is 780288 bytes and its critical path is none.

## 8. Grey Harbor

Exercise SYN-EXERCISE-GREY-HARBOR. Phase PH1. Threat is HIGH. Under the signature rule a HIGH threat locks every participant to ML-DSA-87. The sites are SYN-SITE-RIVER-SWITCH, SYN-SITE-LOCK-METER. The organization file contains 106 scenario labels.

| Organization | Baseline scheme | Baseline bytes | Baseline path ms | Inject scheme | Inject bytes | Inject path ms |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| FED-DOE | ML-DSA-87 | 1068837 | 61.426 | ML-DSA-87 | 1068837 | 61.426 |
| FED-CISA | ML-DSA-87 | 1068837 | 61.426 | ML-DSA-87 | 1068837 | 61.426 |
| FEDLAB-INL | ML-DSA-87 | 1068837 | 31.426 | ML-DSA-87 | 1068837 | 31.426 |
| IBM-XFORCE | ML-DSA-65 | 764379 | 15.957 | ML-DSA-87 | 1068837 | 16.426 |
| IBM-FEDERAL | ML-DSA-87 | 1068837 | 61.426 | ML-DSA-87 | 1068837 | 61.426 |
| RES-CMU-SEI | ML-DSA-87 | 1068837 | 46.426 | ML-DSA-87 | 1068837 | 46.426 |

IBM-XFORCE is the row whose scheme changes. The baseline is ML-DSA-65, 764379 bytes, critical path 15.957 ms. The inject is ML-DSA-87, 1068837 bytes, critical path 16.426 ms. The other listed organizations already sit on ML-DSA-87, so the inject does not change their byte count.

## 9. Signature rule, case by case

The function is a total map on the four arguments used by the tests.

| Fallback | Threat | NSS | Load | Return |
| --- | --- | --- | --- | --- |
| yes | any | any | any | ML-DSA-87 |
| no | HIGH | any | any | ML-DSA-87 |
| no | not HIGH | yes | any | ML-DSA-87 |
| no | not HIGH | no | above 0.75 | ML-DSA-65 |
| no | not HIGH | no | 0.75 or below | ML-DSA-87 |

The comparison with 0.75 is strict. A load of 0.75 stays on ML-DSA-87. Grey Harbor sets the threat to HIGH, so the first applicable row is the HIGH row and every blue-cell inject uses ML-DSA-87 even when the baseline for that organization was ML-DSA-65.

## 10. One decision at n = 4

f = 1 and q = 3. PRE-PREPARE is 3 messages, PREPARE is 12, COMMIT is 12, and the round is 27 messages. The empty-block fallback is 12 messages. Aggregate ML-DSA-87 bytes are 27 · 4627 = 124929. The path verifies 5 signatures and signs 3. Latency is 0.0605606 seconds. The per-node bound is 6753.836178949643 decisions per second. The network bound is 1688.4590447374107 decisions per second.

## 11. Software

| Path | Role |
| --- | --- |
| src/qhbft/roundsim.py | Honest round, empty block, link budget |
| src/qhbft/costs.py | Closed-form patterns and the sweep |
| src/qhbft/protocol.py | Signature rule, tiers, quorum identifiers, primary |
| src/qhbft/safety.py | Intersection predicate and the n = 4 enumeration |
| data/published_costs.json | FIPS lengths and the PQShield medians |
| benchmarks/run_benchmark.py | Writes evaluation.json |
| lab/njit/run_lab.py | Monte Carlo of committee draws for the NJIT Wulver cluster |

## 12. Reproduce

python3 -m unittest tests/test_protocol.py tests/test_dummy.py tests/test_lab_smoke.py

python3 benchmarks/run_benchmark.py

python3 benchmarks/run_dummy.py

Package version recorded in the result file: 0.2.5.
