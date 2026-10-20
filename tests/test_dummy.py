import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qhbft.costs import quorum
from qhbft.dummy import load_organizations, run_dummy

ROOT = Path(__file__).resolve().parents[1]


class DummyDeploymentTests(unittest.TestCase):
    def test_registry_covers_the_declared_scope(self):
        orgs = load_organizations()
        counts = {}
        for org in orgs:
            counts[org["klass"]] = counts.get(org["klass"], 0) + 1
            n = int(org["committee_n"])
            self.assertLess(quorum(n), n)
        self.assertEqual(counts["federal-department"], 15)
        self.assertEqual(counts["national-laboratory"], 17)
        self.assertGreaterEqual(counts["ibm"], 8)
        self.assertGreaterEqual(counts["research-center"], 40)

    def test_policy_rule_on_every_scenario_row(self):
        report = run_dummy()
        self.assertEqual(report["kind"], "synthetic-fixture")
        by_id = {row["org_id"]: row for row in report["rows"]}
        self.assertIn("Not an IBM Quantum", by_id["IBM-QUANTUM"]["notes"])
        self.assertEqual(by_id["IBM-QUANTUM"]["scheme"], "ML-DSA-87")
        self.assertEqual(by_id["IBM-XFORCE"]["scheme"], "ML-DSA-65")
        self.assertEqual(by_id["IBM-FEDERAL"]["scheme"], "ML-DSA-87")
        self.assertGreater(by_id["IBM-FEDERAL"]["scenario_load"], 0.75)
        self.assertEqual(by_id["IBM-ZURICH"]["scheme"], "ML-DSA-87")
        self.assertTrue(by_id["IBM-ZURICH"]["scenario_fallback"])
        strict = 0
        stepped = 0
        for row in report["rows"]:
            self.assertGreater(row["bytes"], 0)
            self.assertIsNotNone(row["critical_path_ms"])
            if row["policy_profile"] in ("nss", "cnsa-aligned"):
                strict += 1
                self.assertEqual(row["scheme"], "ML-DSA-87")
            if row["scheme"] == "ML-DSA-65":
                stepped += 1
                self.assertNotIn(row["policy_profile"], ("nss", "cnsa-aligned"))
                self.assertFalse(row["scenario_fallback"])
                self.assertGreater(row["scenario_load"], 0.75)
                self.assertNotEqual(row["scenario_threat"], "HIGH")
        self.assertGreater(strict, 40)
        self.assertGreater(stepped, 5)

    def test_public_evaluation_is_untouched(self):
        public = json.loads((ROOT / "benchmarks" / "results" / "evaluation.json").read_text())
        self.assertEqual(public["package"], "quantumshield-qhbft")
        self.assertNotEqual(public.get("kind"), "synthetic-fixture")
        self.assertIn("FIPS", public["disclaimer"])
        saved = json.loads((ROOT / "benchmarks" / "results" / "dummy_evaluation.json").read_text())
        self.assertEqual(saved["kind"], "synthetic-fixture")
        self.assertEqual(saved["n_organizations"], 106)
        self.assertEqual(saved["scheme_counts"]["ML-DSA-87"] + saved["scheme_counts"]["ML-DSA-65"], 106)


if __name__ == "__main__":
    unittest.main()
