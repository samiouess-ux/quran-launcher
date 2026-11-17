"""Tests for the staged background preview workflow."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
from src.prepare_background_review_previews import build_contact_sheet, composite_overlay_preview, prepare


class BackgroundReviewPreviewTests(unittest.TestCase):
    def test_contact_sheet_is_vertical_and_contains_four_tiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = []
            for index in range(4):
                path = root / f"{index}.jpg"
                Image.new("RGB", (540, 960), (index * 40, 30, 60)).save(path)
                items.append({
                    "preview_path": str(path),
                    "description": f"Candidate {index}",
                    "width": 2160,
                    "height": 3840,
                    "duration_seconds": 5,
                })
            output = root / "sheet.jpg"
            build_contact_sheet(items, output)
            with Image.open(output) as image:
                self.assertEqual(image.size, (1080, 1920))

    def test_actual_quran_overlay_is_composited_over_candidate_crop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            background = root / "background.jpg"
            overlay = root / "overlay.png"
            output = root / "composite.jpg"
            Image.new("RGB", (540, 960), (20, 80, 120)).save(background)
            layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            from PIL import ImageDraw
            ImageDraw.Draw(layer).rectangle((100, 100, 980, 1800), fill=(0, 0, 0, 160))
            layer.save(overlay)
            composite_overlay_preview(background, overlay, output)
            with Image.open(output) as result:
                self.assertEqual(result.size, (540, 960))
                self.assertNotEqual(result.getpixel((270, 480)), (20, 80, 120))


    def test_prepare_accepts_twelve_source_only_candidates_without_claiming_download(self):
        catalog = json.loads(Path("data/background_additions_review.json").read_text(encoding="utf-8"))
        # This test covers the source-only path; current production review catalog
        # also contains staged direct URLs, so remove them from this isolated fixture.
        for candidate in catalog["candidates"]:
            candidate.pop("direct_video_url", None)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            with patch("src.prepare_background_review_previews.resolve_pexels_direct_url", return_value=""):
                report = prepare(catalog_path, root / "output")
            self.assertEqual(report["source_candidate_count"], 12)
            self.assertEqual(report["candidate_count"], 0)
            self.assertEqual(report["unresolved_count"], 12)
            self.assertFalse(report["production_enabled"])
            self.assertIsNone(report["contact_sheet"])

    def test_failed_probe_removes_downloaded_clip_and_partial_preview(self):
        catalog = {
            "candidates": [{
                "id": "candidate-probe-failure",
                "description": "Test candidate",
                "creator": "Test",
                "source_page_url": "https://www.pexels.com/video/test/",
                "license": "Pexels License",
                "direct_video_url": "https://videos.pexels.com/video-files/test.mp4",
                "approved": False,
                "user_approved": False,
                "download_verified": False,
            }]
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "catalog.json"
            output = root / "output"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

            def fake_download(_url, destination):
                destination.write_bytes(b"not-a-real-video")
                return 16

            with patch("src.prepare_background_review_previews.download_candidate", side_effect=fake_download):
                with patch("src.prepare_background_review_previews.probe_video", side_effect=RuntimeError("ffprobe failed")):
                    with self.assertRaisesRegex(RuntimeError, "candidate-probe-failure"):
                        prepare(catalog_path, output)

            self.assertFalse((output / "candidate-probe-failure.mp4").exists())
            self.assertFalse((output / "candidate-probe-failure_vertical_crop.jpg").exists())

    def test_prepare_rejects_approved_candidate_without_explicit_user_approval(self):
        catalog = json.loads(Path("data/background_candidates.json").read_text(encoding="utf-8"))
        catalog["candidates"][0]["approved"] = True
        catalog["candidates"][0]["user_approved"] = False
        catalog["candidates"][0]["download_verified"] = True
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "explicit user approval"):
                prepare(catalog_path, root / "output")


if __name__ == "__main__":
    unittest.main()
