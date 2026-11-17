"""Safety and deterministic behavior tests for approved background rotation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from background_rotation import (load_eligible_backgrounds, select_background,
                                 select_background_sequence)


class BackgroundRotationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ROOT / "data" / "background_candidates.json"

    def test_only_verified_portrait_backgrounds_are_rotation_eligible(self):
        items = load_eligible_backgrounds(self.catalog)
        self.assertEqual(len(items), 11)
        self.assertTrue(all(x["approved"] and x["user_approved"] and x["download_verified"] for x in items))
        original = {
            "pexels-ocean-shore-35036280",
            "pexels-mountain-lake-37675265",
            "pexels-sunset-sky-35477402",
        }
        self.assertTrue(original.issubset({x["id"] for x in items}))
        self.assertTrue(all(x.get("aspect_ratio") == "9:16" for x in items))
        self.assertNotIn("pexels-mountain-bridge-5903759", {x["id"] for x in items})
        self.assertNotIn("pexels-illuminated-mosque-night-34928699", {x["id"] for x in items})

    def test_selection_is_deterministic_and_avoids_recent_ids(self):
        first = select_background(self.catalog, "stable-video-key")
        again = select_background(self.catalog, "stable-video-key")
        self.assertEqual(first["id"], again["id"])
        remaining = select_background(self.catalog, "stable-video-key", [first["id"]])
        self.assertNotEqual(first["id"], remaining["id"])

    def test_sequence_covers_duration_without_repeating_clips(self):
        items = select_background_sequence(self.catalog, "sequence-key", 35)
        self.assertGreaterEqual(sum(x["duration_seconds"] for x in items), 35)
        self.assertEqual(len(items), len({x["id"] for x in items}))
        self.assertTrue(all(x["aspect_ratio"] == "9:16" for x in items))

    def test_sequence_rejects_impossible_duration(self):
        with self.assertRaisesRegex(ValueError, "short of the required"):
            select_background_sequence(self.catalog, "sequence-key", 1000)

    def test_sequence_rejects_nonpositive_duration(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            select_background_sequence(self.catalog, "sequence-key", 0)

    def test_rejects_empty_rotation_key(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            select_background(self.catalog, " ")

    def test_unverified_and_unapproved_items_never_enter_rotation(self):
        data = json.loads(self.catalog.read_text(encoding="utf-8"))
        data["candidates"].append({
            "id": "unapproved-test", "approved": True, "user_approved": True,
            "download_verified": False, "direct_video_url": "https://example.com/test.mp4",
            "source_page_url": "https://example.com/source"
        })
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            ids = {x["id"] for x in load_eligible_backgrounds(path)}
        self.assertNotIn("unapproved-test", ids)


if __name__ == "__main__":
    unittest.main()
