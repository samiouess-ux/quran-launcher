"""Safety checks for staged, review-only background candidates."""
import json
import re
import unittest
from pathlib import Path


class BackgroundCandidateTests(unittest.TestCase):
    def test_four_candidates_have_matching_pexels_direct_mp4_sources(self):
        catalog = json.loads(Path("data/background_candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["candidates"]), 15)
        original_ids = {"pexels-ocean-shore-35036280", "pexels-mountain-lake-37675265", "pexels-sunset-sky-35477402", "pexels-mountain-bridge-5903759"}
        original = [item for item in catalog["candidates"] if item["id"] in original_ids]
        additions = [item for item in catalog["candidates"] if item["id"] not in original_ids]
        self.assertEqual(len(original), 4)
        self.assertEqual(len(additions), 11)
        for item in catalog["candidates"]:
            source_id = item["id"].rsplit("-", 1)[-1]
            url = item["direct_video_url"]
            self.assertTrue(url.startswith("https://videos.pexels.com/video-files/"))
            self.assertRegex(url, rf"/video-files/{re.escape(source_id)}/[^/]+\.mp4$")
            self.assertIn(source_id, item["source_page_url"])

    def test_candidates_are_user_approved_and_verified_for_rotation_integration(self):
        catalog = json.loads(Path("data/background_candidates.json").read_text(encoding="utf-8"))
        for item in catalog["candidates"]:
            self.assertTrue(item["download_verified"])
            self.assertTrue(item["approved"])
            self.assertTrue(item["user_approved"])


if __name__ == "__main__":
    unittest.main()
