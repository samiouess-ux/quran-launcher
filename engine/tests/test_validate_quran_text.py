"""Regression tests for fail-closed Quran text validation."""
import json
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from validate_quran_text import validate


REFERENCE = ROOT / "data" / "reference" / "quran_text_uthmani.json"
BASE_MANIFEST = ROOT / "content" / "first_video.json"


class QuranValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
        self.manifest_path = Path(self.temp_dir.name) / "manifest.json"

    def run_validation(self):
        self.manifest_path.write_text(
            json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8"
        )
        validate(self.manifest_path, REFERENCE)

    def test_exact_reviewed_text_passes(self):
        self.run_validation()

    def test_single_diacritic_change_fails(self):
        self.manifest["verses"][0]["arabic"] = "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا"
        self.manifest["verses"][0]["arabic"] = self.manifest["verses"][0]["arabic"].replace("فَ", "فُ", 1)
        with self.assertRaisesRegex(SystemExit, "Exact Unicode comparison failed"):
            self.run_validation()

    def test_missing_verse_fails(self):
        self.manifest["verses"] = self.manifest["verses"][:1]
        with self.assertRaisesRegex(SystemExit, "same order"):
            self.run_validation()

    def test_reordered_verses_fail(self):
        self.manifest["verses"].reverse()
        with self.assertRaisesRegex(SystemExit, "same order"):
            self.run_validation()

    def test_duplicate_requested_verse_fails(self):
        self.manifest["source"]["verses"] = [5, 5]
        with self.assertRaisesRegex(SystemExit, "duplicate verse"):
            self.run_validation()


if __name__ == "__main__":
    unittest.main()
