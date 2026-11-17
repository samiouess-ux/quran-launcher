import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from build_quran_translation_catalog import validate_surah_payload


class TranslationCatalogTests(unittest.TestCase):
    def test_accepts_complete_surah_and_preserves_verbatim_text(self):
        payload = {
            "code": 200,
            "data": {
                "ayahs": [
                    {"numberInSurah": 1, "text": "In the Name of Allah."},
                    {"numberInSurah": 2, "text": "All praise is due to Allah."},
                ]
            },
        }
        self.assertEqual(
            validate_surah_payload(payload, 1, 2),
            {"1:1": "In the Name of Allah.", "1:2": "All praise is due to Allah."},
        )

    def test_rejects_missing_ayah(self):
        payload = {"code": 200, "data": {"ayahs": [{"numberInSurah": 1, "text": "text"}]}}
        with self.assertRaisesRegex(ValueError, "incomplete translation"):
            validate_surah_payload(payload, 1, 2)

    def test_rejects_duplicate_ayah(self):
        payload = {"code": 200, "data": {"ayahs": [
            {"numberInSurah": 1, "text": "one"},
            {"numberInSurah": 1, "text": "duplicate"},
        ]}}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_surah_payload(payload, 1, 1)

    def test_rejects_empty_translation(self):
        payload = {"code": 200, "data": {"ayahs": [{"numberInSurah": 1, "text": "  "}]}}
        with self.assertRaisesRegex(ValueError, "empty translation"):
            validate_surah_payload(payload, 1, 1)

    def test_rejects_wrong_api_status(self):
        with self.assertRaisesRegex(ValueError, "HTTP 200"):
            validate_surah_payload({"code": 500}, 1, 1)


if __name__ == "__main__":
    unittest.main()
