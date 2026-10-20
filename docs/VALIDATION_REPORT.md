# Validation report

**Paper.** QH-BFT concept summary, April 2026, `docs/QuantumShield_Concept_Summary_v3.docx`.

**Repository.** Package 0.2.4. Figures are `benchmarks/results/evaluation.json`.

Bytes, seconds, and decisions per second are separate fields. At n = 64, ML-DSA-87, 20 ms one-way delay:

| Bound | Value |
| --- | ---: |
| Messages in one honest round | 8,127 |
| Aggregate signature bytes | 37,603,629 |
| Quorum-only signature bytes | 16,911,685 |
| Critical-path latency | 0.0649 s |
| Latency bound | 15.41 /s |
| Primary egress bound, own 1 Gbps link | 142.94 /s |
| Aggregate bound, one shared 1 Gbps link | 3.324 /s |
| Quorum bound, one shared 1 Gbps link | 7.391 /s |
| `B / (N² · S)` with S = 4,627 | 6.596 /s |

The n = 4 exhaustive check still has 0 non-intersecting quorums. FIPS 204 lengths are 2,420, 3,309, and 4,627.
