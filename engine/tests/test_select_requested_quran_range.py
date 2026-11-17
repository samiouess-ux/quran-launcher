import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from select_requested_quran_range import choose_range_from_durations


class RequestedRangeSelectionTests(unittest.TestCase):
    def test_selects_longest_contiguous_opening_range_under_40_seconds(self):
        result = choose_range_from_durations(18, 1, {1: 12.0, 2: 20.0, 3: 9.0, 4: 10.0})
        self.assertEqual(result["selected_ayahs"], [1, 2])
        self.assertEqual(result["end_ayah"], 2)
        self.assertEqual(result["duration_seconds"], 32.0)

    def test_stops_at_first_ayah_that_would_exceed_limit(self):
        result = choose_range_from_durations(18, 4, {4: 25.0, 5: 20.0, 6: 5.0})
        self.assertEqual(result["selected_ayahs"], [4])

    def test_rejects_single_ayah_over_limit(self):
        with self.assertRaisesRegex(ValueError, "alone exceeds"):
            choose_range_from_durations(2, 282, {282: 80.0})

    def test_does_not_skip_missing_ayah(self):
        with self.assertRaisesRegex(ValueError, "Missing or invalid"):
            choose_range_from_durations(18, 1, {1: 10.0, 3: 10.0})

    def test_caps_selection_at_ten_ayahs(self):
        durations = {ayah: 1.0 for ayah in range(1, 13)}
        result = choose_range_from_durations(18, 1, durations)
        self.assertEqual(len(result["selected_ayahs"]), 10)
        self.assertEqual(result["end_ayah"], 10)


if __name__ == "__main__":
    unittest.main()
