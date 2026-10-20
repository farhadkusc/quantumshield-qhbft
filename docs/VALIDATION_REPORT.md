# Validation report

**Paper.** QH-BFT concept summary, April 2026, in `docs/QuantumShield_Concept_Summary_v3.docx`.

**Repository.** Package 0.2.3. Figures below are `benchmarks/results/evaluation.json`.

The signature rule, the `2f+1` quorum, and the n = 4 exhaustive intersection check match the paper. An honest round of the paper's broadcast steps produces 27, 495, and 8,127 messages at n = 4, 16, and 64. The empty-block fallback produces n(n−1) messages.

Section 7.3 with B = 1 Gbps and S = 4,627 evaluates to 6.5955 decisions per second at n = 64. The byte term N²·S is 18,952,192. FIPS lengths are 2,420, 3,309, and 4,627. The length ratio against a 96-byte ECDSA-P384 signature is 48.20.

The message-pattern table (PBFT, quorum, HotStuff) is the same closed form as before. At n = 64, PBFT with ML-DSA-87 is 37,608,256 bytes and 64.889 ms.

The concept paper's Table 8.4 is not copied into this file. The numbers above are the run of this repository.
