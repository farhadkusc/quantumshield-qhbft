# QH-BFT / QuantumShield

This repository is an analytical model of message counts, bytes, and critical-path time. It contains no consensus implementation and no network run. Signature lengths are FIPS 204 Table 2. Timings are PQShield medians, not remeasured. It was written after the petition was filed. Implementation and benchmarking on the federal algorithms is the first phase of the proposed work and has not been done. `benchmarks/run_benchmark.py` evaluates formulas and measures nothing.

Author: **Md Farhad Kabir**. Package **0.2.6**. The research draft is [docs/PAPER.md](docs/PAPER.md), generated from `benchmarks/results/evaluation.json`.

Signature lengths are FIPS 204 Table 2 (13 August 2024): ML-DSA-44 is 2,420 bytes, ML-DSA-65 is 3,309, ML-DSA-87 is 4,627. Sign and verify times are the medians published by the [PQShield NIST Signature Zoo](https://pqshield.github.io/nist-sigs-zoo) for an Intel Xeon Platinum 8488C on 22 September 2026 (1,000 iterations): ML-DSA-87 signs in 96.7 µs and verifies in 54.1 µs. Those times were not remeasured here. ECDSA-P384 is carried as a 96-byte signature only. No ECDSA timing from that host is cited, so the ECDSA rows have a byte count and a null critical path.

## Bandwidth, ML-DSA-87, 1 Gbps

The two bandwidth readings are `B / (N · S)` per node and `B / (N² · S)` for the whole exchange. `B` is 125,000,000 bytes per second on a 1 Gbps link. `S` is 4,627 bytes.

| n | Per-node B/(N·S) | Whole-exchange B/(N²·S) |
| ---: | ---: | ---: |
| 4 | 6,753.836179 /s | 1,688.459045 /s |
| 16 | 1,688.459045 /s | 105.528690 /s |
| 64 | 422.114761 /s | 6.595543 /s |

At n = 64 the whole-exchange reading is B/(N² · S) = 6.6 and the per-node reading is B/(N · S) = 422. The values in the table are the quotients, 6.595543 and 422.114761. The per-node figure is N times the whole-exchange figure.

The critical path at n = 64 is 0.0648886 s under the assumed 20 ms one-way delay: three hops, three signatures, and `1 + 2(q − 1)` verifications, using the PQShield medians of 96.7 µs to sign and 54.1 µs to verify.

## View-change against the empty-block fallback

Leading order at n = 64, ML-DSA-87, 1 Gbps. A PBFT view-change is N³ signatures. The empty-block fallback is N² signatures. The exact count of that broadcast is n(n − 1).

| | Signatures | Bytes | Whole exchange | Per node |
| --- | ---: | ---: | ---: | ---: |
| View-change, N³ | 262,144 | 1,212,940,288 (about 1.2 GB) | 9.703522304 s (9.7 s) | 0.151617536 s (0.15 s) |
| Empty-block fallback, N² | 4,096 | 18,952,192 (about 19 MB) | 0.151617536 s (0.15 s) | 0.002369024 s (2.4 ms) |
| Exact empty-block count, n(n − 1) | 4,032 | | | |

For a round in which a replica holds a prepared value, the fallback carries it forward and adds signatures. The figures are for the round in which none does.

## What is counted

Normal case, after GST, no faults on the critical path. One-way delay is a parameter, default 20 ms.

| Protocol | Who speaks | Signatures on the critical path |
| --- | --- | --- |
| `pbft` | all \(n\) | 3 hops; each replica verifies \(1+2(2f)\) signatures |
| `qh-quorum` | a quorum of \(2f+1\), highest trust tier first | same shape, smaller \(n\) |
| `hotstuff-linear` | leader and \(n\) votes, one aggregated QC | 2 hops. Aggregation is **assumed**. FIPS 204 does not define it. |
| `hotstuff-raw-qc` | same, QC is \(2f+1\) raw ML-DSA signatures | the honest linear pattern without an aggregate |

At \(n=64\), one decision (20 ms one-way). Crypto time is a few milliseconds. Three hops of 20 ms are 60 ms, so the critical path is delay-dominated. The thing that moves by an order of magnitude is the byte count.

| Protocol | Scheme | Megabytes | Critical path | Of which crypto |
| --- | --- | ---: | ---: | ---: |
| pbft | ECDSA-P384 | 0.78 | not timed | not timed |
| pbft | ML-DSA-87 | 37.61 | 64.9 ms | 4.9 ms |
| qh-quorum | ML-DSA-87 | 16.91 | 64.9 ms | 4.9 ms |
| qh-quorum | ML-DSA-65 | 12.09 | 63.2 ms | 3.2 ms |
| hotstuff-linear | ML-DSA-87 | 0.89 | 42.6 ms | 2.6 ms |
| hotstuff-raw-qc | ML-DSA-87 | 13.33 | 42.6 ms | 2.6 ms |

The same formulas at smaller committees, from `benchmarks/results/evaluation.json`: PBFT with ML-DSA-87 is 130 KB and 60.6 ms at \(n=4\) (0.56 ms of that is crypto), and 2.29 MB and 61.4 ms at \(n=16\). Quorum participation cuts the ML-DSA-87 byte count by about half versus all-to-all PBFT. It does not change the critical path, because a quorum of \(2f+1\) at \(n=64\) is 43 and the replica still verifies \(O(f)\) signatures. The large drop in bytes requires a linear pattern. The raw-QC row shows that most of that drop disappears if the quorum certificate is a bundle of ML-DSA signatures rather than one aggregate.

## Safety

For \(n=3f+1\), any two sets of size \(2f+1\) intersect in at least \(f+1\) seats, so in at least one honest seat when at most \(f\) seats are Byzantine. The \(n=4\) case is checked exhaustively (6 pairs, 0 failures). See `src/qhbft/safety.py`.

Signature policy: ML-DSA-87 by default. ML-DSA-65 only when the deployment is non-NSS, the round is not an empty-block fallback, threat is not high, and load is above 0.75.

## Reproduce

```bash
python3 -m unittest tests/test_protocol.py
python3 benchmarks/run_benchmark.py
python3 benchmarks/plot_results.py
```

The byte chart is [docs/figures/results.svg](docs/figures/results.svg).

## Synthetic fixtures

`data/dummy/organizations.csv` is a deployment scenario for every U.S. cabinet department, the 17 DOE national laboratories, selected federal components, IBM research and security units, and a fixed list of universities and research centers. `policy_profile=nss` or `cnsa-aligned` stays on ML-DSA-87. Commercial and academic rows step down to ML-DSA-65 only when the rule in `select_signature` says so. One-way delays in that file are assumptions.

`benchmarks/results/dummy_evaluation.json` is written by `python3 benchmarks/run_dummy.py`, including Grey Harbor.

Grey Harbor sets `threat=HIGH` on the blue cell for the inject window. Every row locks to ML-DSA-87. In the quiet baseline only `IBM-XFORCE` is on ML-DSA-65; the inject steps that row back up.

## NJIT Wulver

`lab/njit/` samples 200,000 quorum pairs at four committee sizes, including n = 4096, and writes the ML-DSA-87 cost grid. Submit with `sbatch lab/njit/wulver.sbatch`. Instructions are in [lab/njit/README.md](lab/njit/README.md).
