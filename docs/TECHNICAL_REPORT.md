# Technical report

**Version 0.2.6.** Author: Md Farhad Kabir.

## Cost model

Let \(S\) be the signature length and \(V\) the published verify time.

PBFT normal-case messages: \(n + 2n(n-1)\).

QH-BFT with a speaking quorum \(q=2f+1\): \(q + 2q(q-1)\).

HotStuff with an aggregated quorum certificate: \(3n\) signatures (proposal, vote, certificate).

HotStuff whose certificate is the raw list of \(q\) ML-DSA signatures: \(2n\) individual signatures plus \(n \cdot q \cdot S\) bytes of certificate.

Critical path, in milliseconds:

\[
h \cdot d + (s_{\text{sign}} \cdot t_{\text{sign}} + s_{\text{verify}} \cdot t_{\text{verify}}) / 1000
\]

\(d = 20\) ms unless the caller changes it. \(h\) is 3 for the PBFT-shaped protocols and 2 for the HotStuff-shaped ones. \(t_{\text{sign}}\) and \(t_{\text{verify}}\) are the PQShield medians cited in `data/published_costs.json`. When those fields are null (ECDSA-P384), the critical path is null rather than filled in.

## Bandwidth

On a 1 Gbps link, B = 125000000 bytes per second. With signature length S the per-node bound is B / (N · S) and the whole-exchange bound is B / (N² · S). For ML-DSA-87, S = 4627. At N = 64 the quotients are 422.1147611843527 and 6.595543143505511, recorded as 422 and 6.6. The per-node reading is N times the whole-exchange reading.

At the same n and S, a PBFT view-change of N³ = 262144 signatures is set against an empty-block fallback of N² = 4096 signatures. The exact empty-block count is n(n − 1) = 4032. The byte pair is 1212940288 and 18952192, about 1.2 GB and about 19 MB. Whole-exchange time is 9.703522304 s and 0.151617536 s. Per-node time is 0.151617536 s and 0.002369024 s. For a round in which a replica holds a prepared value, the fallback carries it forward and adds signatures. The figures are for the round in which none does.

## Why the quorum does not shorten the critical path

At \(n=64\), \(f=21\) and \(q=43\). A replica on the PBFT path verifies \(1+2(q-1)\) signatures either way. The byte count falls because silent validators do not transmit. Latency on the critical path falls only if the number of verifies on that path falls, which is what the linear patterns do.

## Policy

`select_signature` is the rule from the concept paper, with the safety side pinned down: fallback, NSS, and high threat stay on ML-DSA-87. There is no silent downgrade.

## Not shown

View-change under delay, GST estimation, constant-time signing, or a comparison against liboqs on this machine. Those need a benchmark host. The formulas are in `src/qhbft/costs.py` so a later host-specific timing file can replace the PQShield medians without touching the message accounting.

## Synthetic fixtures

`data/dummy/organizations.csv` runs `select_signature` and `decision_cost` once per scenario label. The labels cover cabinet departments, DOE laboratories, IBM units, and research centers. `nss` and `cnsa-aligned` take the strict ML-DSA-87 branch. `assumed_one_way_ms` is the delay input. Output is `benchmarks/results/dummy_evaluation.json`.

Grey Harbor is the same registry under `threat=HIGH`. The selector locks the blue cell to ML-DSA-87. The only step-up in that cell is the row that was on ML-DSA-65 in the quiet baseline.
