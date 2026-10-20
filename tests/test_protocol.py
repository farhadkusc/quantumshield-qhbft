import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from qhbft.costs import decision_cost, quorum
from qhbft.protocol import primary_id, quorum_ids, select_signature
from qhbft.roundsim import fallback_comparison, link_budget
from qhbft.safety import exhaustive_n4, intersects_honestly


class ResearchTests(unittest.TestCase):
    def test_n4_quorums_all_intersect_in_an_honest_seat(self):
        grid = exhaustive_n4()
        self.assertEqual(grid["non_intersecting"], 0)
        self.assertTrue(intersects_honestly({0, 1, 2}, {0, 2, 3}, 4))

    def test_signature_policy_matches_the_safety_rule(self):
        self.assertEqual(select_signature(0.99, "LOW", nss=False, in_fallback=False), "ML-DSA-65")
        self.assertEqual(select_signature(0.99, "LOW", nss=True, in_fallback=False), "ML-DSA-87")
        self.assertEqual(select_signature(0.2, "LOW", nss=False, in_fallback=True), "ML-DSA-87")
        self.assertEqual(select_signature(0.2, "HIGH", nss=False, in_fallback=False), "ML-DSA-87")

    def test_quorum_size_and_published_sizes(self):
        rng = np.random.default_rng(1)
        rel = rng.uniform(0.2, 1.0, size=16)
        self.assertEqual(len(quorum_ids(rel, n_faulty=5, rng=rng)), 11)
        row = decision_cost("pbft", 4, "ML-DSA-87")
        self.assertEqual(row["quorum"], quorum(4))
        # FIPS 204 Table 2: ML-DSA-87 signatures are 4627 bytes.
        self.assertEqual(row["bytes"] % 4627, 0)
        naive = decision_cost("pbft", 64, "ML-DSA-87")
        tiered = decision_cost("qh-quorum", 64, "ML-DSA-87")
        self.assertLess(tiered["bytes"], naive["bytes"])
        raw = decision_cost("hotstuff-raw-qc", 64, "ML-DSA-87")
        ideal = decision_cost("hotstuff-linear", 64, "ML-DSA-87")
        self.assertGreater(raw["bytes"], ideal["bytes"])

    def test_primary_stays_in_the_top_tier(self):
        rel = np.array([0.1, 0.2, 0.95, 0.99])
        self.assertIn(primary_id(rel, view=0), (2, 3))

    def test_link_budget_uses_the_two_bandwidth_readings(self):
        row = link_budget(64, 4627, sign_seconds=96.7e-6, verify_seconds=54.1e-6)
        per_node = 125_000_000 / (64 * 4627)
        network = 125_000_000 / (64 * 64 * 4627)
        self.assertGreater(row["latency_seconds"], 0.06)
        self.assertLess(row["latency_seconds"], 0.08)
        self.assertAlmostEqual(row["per_node_bound_per_s"], per_node)
        self.assertAlmostEqual(row["paper_n2_bound_per_s"], network)
        self.assertAlmostEqual(row["per_node_bound_per_s"], 64 * row["paper_n2_bound_per_s"])
        self.assertNotIn("primary_bandwidth_bound_per_s", row)
        self.assertNotIn("aggregate_bandwidth_bound_per_s", row)
        self.assertNotIn("quorum_bandwidth_bound_per_s", row)
        self.assertNotIn("byte_term", row)
        row = decision_cost("pbft", 4, "ECDSA-P384")
        self.assertIsNone(row["critical_path_ms"])
        self.assertEqual(row["bytes"] % 96, 0)

    def test_view_change_against_empty_block_at_n64(self):
        row = fallback_comparison()
        self.assertEqual(row["view_change"]["signatures"], 262_144)
        self.assertEqual(row["empty_block_leading"]["signatures"], 4_096)
        self.assertEqual(row["empty_block_exact_messages"], 4_032)
        self.assertEqual(row["view_change"]["bytes"], 262_144 * 4627)
        self.assertEqual(row["empty_block_leading"]["bytes"], 4_096 * 4627)
        self.assertEqual(round(row["view_change"]["bytes"] / 1_000_000_000, 1), 1.2)
        self.assertEqual(round(row["empty_block_leading"]["bytes"] / 1_000_000), 19)
        self.assertEqual(round(row["view_change"]["whole_exchange_s"], 1), 9.7)
        self.assertEqual(round(row["empty_block_leading"]["whole_exchange_s"], 2), 0.15)
        self.assertEqual(round(row["view_change"]["per_node_s"], 2), 0.15)
        self.assertEqual(round(row["empty_block_leading"]["per_node_s"] * 1000, 1), 2.4)


if __name__ == "__main__":
    unittest.main()
