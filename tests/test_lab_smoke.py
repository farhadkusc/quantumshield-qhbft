import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WulverSmokeTests(unittest.TestCase):
    def test_smoke_profile_finds_no_quorum_violation(self):
        subprocess.check_call(
            [sys.executable, str(ROOT / "lab" / "njit" / "run_lab.py"), "--profile", "smoke", "--workers", "2"],
            cwd=ROOT,
        )
        report = json.loads((ROOT / "lab" / "njit" / "results" / "smoke.json").read_text())
        self.assertEqual(report["profile"], "smoke")
        self.assertFalse(report["ran_on_wulver"])
        self.assertEqual(report["violations"], 0)
        self.assertEqual([row["n"] for row in report["intersection"]], [16, 64])
        self.assertEqual(report["n_pairs_per_committee"], 4000)
        for row in report["intersection"]:
            self.assertGreaterEqual(row["min_intersection"], row["intersection_bound"])


if __name__ == "__main__":
    unittest.main()
