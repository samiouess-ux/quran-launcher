"""Duration-selection tests for official contiguous Quran audio passages."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prepare_official_quran_passage import (
    MAX_SECONDS, TARGET_SECONDS, choose_contiguous_passage,
)


class PassageDurationTests(unittest.TestCase):
    def test_production_target_and_hard_cap_are_35_and_40_seconds(self):
        self.assertEqual(TARGET_SECONDS, 35.0)
        self.assertEqual(MAX_SECONDS, 40.0)

    def test_selects_complete_contiguous_verses_near_35_seconds(self):
        durations = {5: 12.0, 6: 13.0, 7: 12.0, 8: 9.0}
        selected = choose_contiguous_passage(durations, 5)
        self.assertEqual(selected, [5, 6, 7])
        self.assertLessEqual(sum(durations[n] for n in selected), 40.0)
        self.assertGreaterEqual(sum(durations[n] for n in selected), 35.0)

    def test_never_adds_an_ayah_that_would_exceed_40_seconds(self):
        durations = {10: 24.0, 11: 18.0, 12: 8.0}
        selected = choose_contiguous_passage(durations, 10)
        # The next complete ayah would take the passage from 24s to 42s;
        # preserve the 40s hard cap rather than satisfying the 35s target by overflow.
        self.assertEqual(selected, [10])
        self.assertLessEqual(sum(durations[n] for n in selected), 40.0)

    def test_allows_a_single_long_ayah_without_trimming_it(self):
        durations = {3: 31.0, 4: 20.0}
        selected = choose_contiguous_passage(durations, 3)
        self.assertEqual(selected, [3])
        self.assertEqual(sum(durations[n] for n in selected), 31.0)

    def test_rejects_an_ayah_longer_than_the_hard_cap(self):
        with self.assertRaisesRegex(ValueError, "exceeds the 40s maximum"):
            choose_contiguous_passage({2: 41.0}, 2)


if __name__ == "__main__":
    unittest.main()
