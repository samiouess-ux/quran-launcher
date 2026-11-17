"""Safety checks for staged Islamic background additions."""
import json
import unittest
from pathlib import Path


class BackgroundAdditionReviewTests(unittest.TestCase):
    def test_twelve_new_candidates_are_separate_and_fail_closed(self):
        catalog = json.loads(Path("data/background_additions_review.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["candidates"]), 12)
        self.assertIn("not production-enabled", catalog["purpose"])
        self.assertIn("not active in the renderer", catalog["activation_policy"])
        ids = [item["id"] for item in catalog["candidates"]]
        self.assertEqual(len(ids), len(set(ids)))
        resolved = [item for item in catalog["candidates"] if item["direct_video_url"]]
        unresolved = [item for item in catalog["candidates"] if not item["direct_video_url"]]
        self.assertEqual(len(resolved), 11)
        self.assertTrue(all(item["direct_video_url"].startswith("https://videos.pexels.com/") for item in resolved))
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(
            {item["id"] for item in unresolved},
            {"pixabay-chain-dome-rock-131292"},
        )
        for item in catalog["candidates"]:
            self.assertTrue(item["source_page_url"].startswith(("https://www.pexels.com/", "https://pixabay.com/")))
            if item["id"] == "pixabay-chain-dome-rock-131292":
                self.assertFalse(item["approved"])
                self.assertFalse(item["user_approved"])
                self.assertFalse(item["download_verified"])
            else:
                self.assertTrue(item["approved"])
                self.assertTrue(item["user_approved"])
                if item["id"].startswith("pexels-mosque-") or item["id"] == "pexels-waterfall-forest-12110531":
                    self.assertTrue(item["direct_video_url"])
                    self.assertFalse(item["download_verified"])
                else:
                    self.assertFalse(item["download_verified"])

    def test_existing_four_candidate_catalog_is_unchanged(self):
        catalog = json.loads(Path("data/background_candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["candidates"]), 15)
        self.assertTrue(all(item["user_approved"] and item["download_verified"] for item in catalog["candidates"]))
        original_ids = {
                "pexels-ocean-shore-35036280",
                "pexels-mountain-lake-37675265",
                "pexels-sunset-sky-35477402",
                "pexels-mountain-bridge-5903759",
            }
        self.assertTrue(original_ids.issubset({item["id"] for item in catalog["candidates"]}))
        self.assertEqual(
            {item["id"] for item in catalog["candidates"] if item["id"] in original_ids},
            {
                "pexels-ocean-shore-35036280",
                "pexels-mountain-lake-37675265",
                "pexels-sunset-sky-35477402",
                "pexels-mountain-bridge-5903759",
            },
        )


if __name__ == "__main__":
    unittest.main()
