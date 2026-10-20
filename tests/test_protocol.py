import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qhbft.protocol import (
    combinatorial_safety_grid,
    quorum_intersect,
    select_signature,
    simulate,
)


class ProtocolTests(unittest.TestCase):
    def test_quorums_of_2f_plus_1_intersect(self):
        grid = combinatorial_safety_grid()
        self.assertEqual(grid[0]["non_intersecting_pairs"], 0)
        self.assertTrue(quorum_intersect({0, 1, 2}, {1, 2, 3}, n=4, f=1))

    def test_signature_policy(self):
        self.assertEqual(select_signature(0.99, "LOW", nss=False, in_fallback=False), "ML-DSA-65")
        self.assertEqual(select_signature(0.99, "LOW", nss=True, in_fallback=False), "ML-DSA-87")
        self.assertEqual(select_signature(0.1, "LOW", nss=False, in_fallback=True), "ML-DSA-87")
        self.assertEqual(select_signature(0.1, "HIGH", nss=False, in_fallback=False), "ML-DSA-87")

    def test_simulation_respects_n_equals_3f_plus_1(self):
        report, rounds = simulate(n=16, rounds=12, seed=2, nss=False)
        self.assertEqual(report.f, 5)
        self.assertEqual(report.safety_violations, 0)
        self.assertGreater(report.decisions, 0)
        self.assertTrue(all(len(r.quorum) == 2 * 5 + 1 for r in rounds))

    def test_rejects_bad_n(self):
        with self.assertRaises(ValueError):
            simulate(n=5)


if __name__ == "__main__":
    unittest.main()
