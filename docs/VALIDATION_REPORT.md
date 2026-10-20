# Validation report

`docs/PAPER.md` and the docx beside it are generated from `benchmarks/results/evaluation.json` and `benchmarks/results/dummy_evaluation.json`.

Thirty regeneration passes compared every recorded public metric, every Grey Harbor figure used in the draft, the package version, and a list of dataset names this repository does not run. Each pass reported 0 mismatches.

Package 0.2.6. The whole-exchange bandwidth reading is B / (N² · S) = 6.6 and the per-node reading is B / (N · S) = 422. The quotients in `evaluation.json` are 6.595543143505511 and 422.1147611843527. The n = 64 view-change comparison is N³ = 262144 signatures against N² = 4096, with the exact empty-block count n(n − 1) = 4032.
