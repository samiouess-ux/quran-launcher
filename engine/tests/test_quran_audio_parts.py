import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from quran_audio_parts import partition_contiguous_ayahs

class PartsTests(unittest.TestCase):
    def test_default_keeps_long_ayah_and_full_sequence_together(self):
        verses = [{'ayah': n} for n in range(1, 5)]
        parts, rest = partition_contiguous_ayahs(verses, {1: 30, 2: 66, 3: 10, 4: 10})
        self.assertEqual([[v['ayah'] for v in p] for p in parts], [[1, 2, 3, 4]])
        self.assertEqual(rest, [])
    def test_explicit_limit_defers_overflow_ayahs_without_splitting(self):
        verses = [{'ayah': n} for n in range(1, 5)]
        parts, rest = partition_contiguous_ayahs(verses, {1: 30, 2: 66, 3: 10, 4: 10}, 40)
        self.assertEqual([[v['ayah'] for v in p] for p in parts], [[1]])
        self.assertEqual([v['ayah'] for v in rest], [2, 3, 4])
    def test_gap_rejected(self):
        with self.assertRaisesRegex(ValueError, 'contiguous'):
            partition_contiguous_ayahs([{'ayah': 1}, {'ayah': 3}], {1: 10, 3: 10})
if __name__ == '__main__':
    unittest.main()
