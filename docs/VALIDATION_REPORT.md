# Validation report

`docs/PAPER.md` and the docx beside it are generated from `benchmarks/results/evaluation.json` and `benchmarks/results/dummy_evaluation.json`.

Thirty regeneration passes compared every recorded public metric, every Grey Harbor figure used in the draft, the package version, and a list of dataset names this repository does not run. Each pass reported 0 mismatches.

Package 0.2.5. The per-node bandwidth reading in `link_budget` is B / (N · S). At n = 64, S = 4627, and 1 Gbps that value is 422.1147611843527 decisions per second. The network reading is B / (N² · S) = 6.595543143505511.
