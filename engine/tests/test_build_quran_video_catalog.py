import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from build_quran_video_catalog import build_joined_catalog


def catalogs():
    return (
        {"edition": "quran-uthmani", "script": "uthmani",
         "review_status": "source_fetched_not_human_reviewed", "rendering_allowed": False,
         "source_url": "https://example.test/arabic", "verses": {"1:1": "بِسْمِ اللَّهِ", "1:2": "الْحَمْدُ"}},
        {"edition": "en.sahih",
         "status": "complete_source_corpus_requires_rights_confirmation_and_verse_level_review",
         "source_url": "https://example.test/translation", "verses": {"1:1": "In the name of Allah", "1:2": "All praise"}},
        {"mapped_verse_count": 2, "source_url": "https://example.test/audio",
         "verses": {"1:1": "001_001.mp3", "1:2": "001_002.mp3"}},
    )


class QuranVideoCatalogTests(unittest.TestCase):
    def test_joins_all_sources_by_exact_verse_key_and_keeps_rendering_blocked(self):
        result = build_joined_catalog(*catalogs(), expected_count=2)
        self.assertEqual(result["joined_verse_count"], 2)
        self.assertEqual(result["verses"]["1:2"]["arabic_uthmani"], "الْحَمْدُ")
        self.assertFalse(result["rendering_allowed"])
        self.assertEqual(result["review_gates"]["audio"], "exact_recording_must_be_listened_to_and_approved_for_each_selected_passage")

    def test_rejects_missing_verse_key(self):
        arabic, translation, audio = catalogs()
        del translation["verses"]["1:2"]
        with self.assertRaisesRegex(ValueError, "exactly 2 entries"):
            build_joined_catalog(arabic, translation, audio, expected_count=2)

    def test_rejects_unreviewed_arabic_being_marked_renderable(self):
        arabic, translation, audio = catalogs()
        arabic["rendering_allowed"] = True
        with self.assertRaisesRegex(ValueError, "unreviewed and blocked"):
            build_joined_catalog(arabic, translation, audio, expected_count=2)

    def test_rejects_missing_audio_reference(self):
        arabic, translation, audio = catalogs()
        audio["verses"]["1:2"] = ""
        with self.assertRaisesRegex(ValueError, "Missing official audio"):
            build_joined_catalog(arabic, translation, audio, expected_count=2)


if __name__ == "__main__":
    unittest.main()
