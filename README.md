# QH-BFT / QuantumShield

Closed-form cost of Byzantine consensus once signatures are ML-DSA instead of ECDSA-P384.

Author: **Md Farhad Kabir**. Package **0.2.3**.

Signature lengths are FIPS 204 Table 2 (13 August 2024): ML-DSA-44 is 2,420 bytes, ML-DSA-65 is 3,309, ML-DSA-87 is 4,627. Sign and verify times are the medians published by the [PQShield NIST Signature Zoo](https://pqshield.github.io/nist-sigs-zoo) for an Intel Xeon Platinum 8488C on 22 September 2026 (1,000 iterations): ML-DSA-87 signs in 96.7 µs and verifies in 54.1 µs. Those times were not remeasured here. ECDSA-P384 is carried as a 96-byte signature only. No ECDSA timing from that host is cited, so the ECDSA rows have a byte count and a null critical path.

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
