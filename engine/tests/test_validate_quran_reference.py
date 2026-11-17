"""Tests for Quran reference snapshot structure validation."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from validate_quran_reference import validate_reference


class QuranReferenceTests(unittest.TestCase):
    def test_current_reference_structure_passes(self):
        validate_reference(ROOT / "data/reference/quran_text_uthmani.json")

    def test_unreviewed_snapshot_fails(self):
        data = json.loads((ROOT / "data/reference/quran_text_uthmani.json").read_text(encoding="utf-8"))
        data["review_status"] = "draft"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reference.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "not marked reviewed"):
                validate_reference(path)

    def test_invalid_verse_key_fails(self):
        data = json.loads((ROOT / "data/reference/quran_text_uthmani.json").read_text(encoding="utf-8"))
        data["verses"] = {"94-x": "نص"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reference.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "Invalid verse key"):
                validate_reference(path)


if __name__ == "__main__":
    unittest.main()
