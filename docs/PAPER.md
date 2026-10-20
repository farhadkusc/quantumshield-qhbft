# QH-BFT

Byte, latency, and bandwidth bounds for one Byzantine consensus decision when signatures are FIPS 204 ML-DSA.

Md Farhad Kabir

Research draft for package 0.2.4, aligned with `benchmarks/results/evaluation.json` and `benchmarks/results/dummy_evaluation.json`. Repository farhadkusc/quantumshield-qhbft.

## Abstract

An honest round follows PRE-PREPARE, PREPARE, and COMMIT. At n = 64 the round sends 8127 messages. With ML-DSA-87 those messages are 37603629 bytes. The critical path at a 20 ms one-way delay is 0.0648886 seconds, which is 15.411027514848524 decisions per second. A 1 Gbps link that has to carry every signature byte in the round supports 3.3241472518516764 decisions per second. The primary, sending only its own egress on a 1 Gbps link, supports 142.9383318296221. The formula B / (N² · S) at B = 1 Gbps and S = 4627 is 6.595543143505511. Bytes, seconds, and decisions per second are separate fields.

## 1. Parameters

Signature lengths are FIPS 204 Table 2, 13 August 2024: ML-DSA-44 is 2420 bytes, ML-DSA-65 is 3309, ML-DSA-87 is 4627. ECDSA-P384 is carried as 96 bytes. Sign and verify medians used on the critical path are the PQShield NIST Signature Zoo values stored in `data/published_costs.json`: ML-DSA-87 sign 96.7 microseconds, verify 54.1 microseconds. The default one-way delay is 20 ms.

For n = 3f + 1 the quorum is q = 2f + 1. Any two sets of size q intersect in at least f + 1 seats. At n = 4, f = 1, the exhaustive check has 6 pairs and 0 non-intersecting pairs.

## 2. Signature rule

`select_signature` in `src/qhbft/protocol.py` returns ML-DSA-87 when the round is an empty-block fallback, when threat is HIGH, or when the deployment is NSS. It returns ML-DSA-65 when none of those hold and load is above 0.75. Otherwise it returns ML-DSA-87.

## 3. Honest round

The primary sends PRE-PREPARE to the other n − 1 validators. Every validator sends PREPARE to the other n − 1. Every validator sends COMMIT to the other n − 1. The empty-block fallback is one PREPARE broadcast from each validator, n(n − 1) messages.

| n | f | Quorum | PRE-PREPARE | PREPARE | COMMIT | Messages | Empty-block messages |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1 | 3 | 3 | 12 | 12 | 27 | 12 |
| 16 | 5 | 11 | 15 | 240 | 240 | 495 | 240 |
| 64 | 21 | 43 | 63 | 4032 | 4032 | 8127 | 4032 |

## 4. Link budget, ML-DSA-87

The critical path is three hops, three signatures, and 1 + 2(q − 1) verifications. A 1 Gbps link is 125000000 bytes per second. The primary bound divides that by the bytes the primary sends, which is 3(n − 1) signatures. The aggregate bound divides it by every signature byte in the round. The quorum bound uses q + 2q(q − 1) messages. The N² bound uses N² · S in the denominator.

| n | Messages | Quorum messages | Aggregate bytes | Quorum bytes | Primary bytes | Replica bytes | Latency s | Latency bound | Primary bound | Aggregate bound | Quorum bound | N² bound |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 27 | 15 | 124929 | 69405 | 41643 | 27762 | 0.0605606 | 16.512385940694116 | 3001.7049684220638 | 1000.5683228073545 | 1801.0229810532383 | 1688.4590447374107 |
| 16 | 495 | 231 | 2290365 | 1068837 | 208215 | 138810 | 0.0614262 | 16.279698239513433 | 600.3409936844128 | 54.57645397131025 | 116.94954422423625 | 105.52869029608817 |
| 64 | 8127 | 3655 | 37603629 | 16911685 | 874503 | 583002 | 0.0648886 | 15.411027514848524 | 142.9383318296221 | 3.3241472518516764 | 7.391339183529022 | 6.595543143505511 |

Checks at n = 64. Messages = (64 − 1) + 2 · 64 · (64 − 1) = 8127. Aggregate bytes = 8127 · 4627 = 37603629. Primary bytes = 3 · 63 · 4627 = 874503. Verifications on the path = 1 + 2 · 42 = 85.

## 5. Closed-form message patterns

`decision_cost` in `src/qhbft/costs.py` uses a second message count, n + 2n(n − 1) for PBFT, which is 8128 at n = 64 rather than 8127. HotStuff linear uses 3n messages and one certificate signature. The raw-certificate row adds n · q signature bytes. Critical-path milliseconds use the same sign and verify medians. ECDSA rows have a byte count and a null critical path.

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

## 6. Grey Harbor

Exercise SYN-EXERCISE-GREY-HARBOR. Threat is HIGH, so the signature rule returns ML-DSA-87 on the blue cell. IBM-XFORCE is the row that changes: baseline ML-DSA-65, 764379 bytes, critical path 15.957 ms; inject ML-DSA-87, 1068837 bytes, critical path 16.426 ms. The organization file has 106 scenario labels.

## 7. Reproduce

python3 benchmarks/run_benchmark.py

python3 benchmarks/run_dummy.py

Code: `src/qhbft/roundsim.py` for the honest round and the link budget, and `src/qhbft/costs.py` for the closed-form rows.
