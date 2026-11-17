import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quran_social_caption import build_social_caption, detect_theme


class QuranSocialCaptionTests(unittest.TestCase):
    def manifest(self, english):
        return {
            "source": {"surah_name_ar": "الشرح", "surah_name_en": "Ash-Sharh", "verses": [5, 6]},
            "verses": [{"english": english}],
        }

    def test_exactly_five_hashtags_and_thematic_caption(self):
        result = build_social_caption(self.manifest("For indeed, with hardship will be ease."), "video-a")
        tags = result["hashtags_ar"] + result["hashtags_en"]
        self.assertEqual(len(tags), 5)
        self.assertEqual(len(set(tags)), 5)
        self.assertEqual(result["theme"], "patience")
        self.assertIn("الصبر والثبات", result["arabic_caption"])
        self.assertIn("Verses 5-6", result["english_caption"])

    def test_rotation_changes_sets_between_video_ids(self):
        first = build_social_caption(self.manifest("Allah is One, the Eternal Refuge."), "video-a")
        second = build_social_caption(self.manifest("Allah is One, the Eternal Refuge."), "video-b")
        first_tags = first["hashtags_ar"] + first["hashtags_en"]
        second_tags = second["hashtags_ar"] + second["hashtags_en"]
        self.assertEqual(len(first_tags), 5)
        self.assertEqual(len(second_tags), 5)
        self.assertNotEqual(first_tags, second_tags)

    def test_unknown_topic_uses_honest_general_description(self):
        result = build_social_caption(self.manifest("A verse with uncommon wording."), "video-c")
        self.assertEqual(result["theme"], "general")
        self.assertIn("تدعونا الآيات", result["arabic_caption"])


if __name__ == "__main__":
    unittest.main()
