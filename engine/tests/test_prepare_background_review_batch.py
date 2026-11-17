"""Tests for the isolated, unapproved background review batch."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.prepare_background_review_batch import prepare


class BackgroundReviewBatchTests(unittest.TestCase):
    def candidates(self, count=6):
        return [{
            "id": f"candidate-{index}",
            "category": "nature",
            "description": f"Candidate {index}",
            "creator": "Test creator",
            "source_page_url": f"https://www.pexels.com/video/sample-{index}/",
            "direct_video_url": f"https://videos.pexels.com/video-files/{index}/sample.mp4",
            "page_license": "Free",
            "approved": False,
            "user_approved": False,
        } for index in range(count)]

    @patch("src.prepare_background_review_batch.download", return_value=12345)
    @patch("src.prepare_background_review_batch.inspect_video", return_value={
        "width": 2160, "height": 3840, "duration_seconds": 8.0, "video_codec": "h264"
    })
    @patch("src.prepare_background_review_batch.make_crop")
    def test_prepares_six_candidates_without_approving_them(self, make_crop, _inspect, _download):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "candidates.json"
            output = root / "output"
            catalog.write_text(json.dumps({"candidates": self.candidates()}), encoding="utf-8")

            def fake_crop(_video, image_path, _duration):
                Image.new("RGB", (540, 960), (30, 50, 70)).save(image_path)

            make_crop.side_effect = fake_crop
            report = prepare(catalog, output)
            self.assertEqual(report["candidate_count"], 6)
            self.assertFalse(report["production_enabled"])
            self.assertFalse(report["telegram_delivery"])
            self.assertFalse(report["auto_publish"])
            self.assertTrue(report["user_approval_required"])
            self.assertTrue(all(not item["approved"] and not item["user_approved"]
                                and not item["production_enabled"] for item in report["items"]))
            with Image.open(report["contact_sheet"]) as sheet:
                self.assertEqual(sheet.size, (1620, 1920))
            self.assertEqual(make_crop.call_count, 6)

    def test_rejects_any_candidate_marked_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = self.candidates(1)
            candidates[0]["approved"] = True
            catalog = root / "candidates.json"
            catalog.write_text(json.dumps({"candidates": candidates}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "explicitly unapproved"):
                prepare(catalog, root / "output")

    @patch("src.prepare_background_review_batch.download")
    def test_rejects_duplicate_ids_before_any_download(self, download):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = self.candidates(2)
            candidates[1]["id"] = candidates[0]["id"]
            catalog = root / "candidates.json"
            catalog.write_text(json.dumps({"candidates": candidates}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unique"):
                prepare(catalog, root / "output")
            download.assert_not_called()
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
