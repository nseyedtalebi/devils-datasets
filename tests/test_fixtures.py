from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "pathological_csv"


class FixtureSmokeTests(unittest.TestCase):
    def test_expected_csv_fixture_count(self) -> None:
        self.assertEqual(len(list(FIXTURES.glob("*.csv"))), 29)

    def test_generator_rebuilds_fixture_count(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_pathological_csv.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("generated 29 CSV files", proc.stdout)
        self.assertEqual(len(list(FIXTURES.glob("*.csv"))), 29)


if __name__ == "__main__":
    unittest.main()
