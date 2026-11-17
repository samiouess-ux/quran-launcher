"""Regression coverage for the Al-Ikhlas candidate against the reviewed reference."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from validate_quran_text import validate

MANIFEST = ROOT / "content/candidate_surah_al_ikhlas_112_1_4.json"
REFERENCE = ROOT / "data/reference/quran_text_uthmani.json"


class AlIkhlasReferenceTests(unittest.TestCase):
    def test_candidate_matches_all_four_reviewed_verses_exactly(self):
        validate(MANIFEST, REFERENCE)

    def test_reference_contains_exactly_expected_candidate_verses(self):
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expected_keys = [f"112:{n}" for n in (1, 2, 3, 4)]
        self.assertEqual(
            [f"112:{n}" for n in manifest["source"]["verses"]],
            expected_keys,
        )
        for verse in manifest["verses"]:
            self.assertEqual(
                reference["verses"][f"112:{verse['number']}"],
                verse["arabic"],
            )


if __name__ == "__main__":
    unittest.main()
