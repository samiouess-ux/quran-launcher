import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PIL import Image, ImageChops
from render_video_scenes import create_arabic_overlay
from validate_content_manifest import validate_content_manifest


class QuranTemplateTests(unittest.TestCase):
    def test_four_templates_create_genuinely_distinct_overlays(self):
        verse = [{"number": 1, "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}]
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for template in ("ornate_gold_classic", "nature_clean", "minimal_mushaf", "cinematic_landscape"):
                path = Path(directory) / f"{template}.png"
                create_arabic_overlay("سورة الفاتحة", verse, path, template)
                self.assertTrue(path.is_file())
                paths.append(path)
            images = [Image.open(path).convert("RGBA") for path in paths]
            for i in range(len(images)):
                for j in range(i + 1, len(images)):
                    self.assertIsNotNone(ImageChops.difference(images[i].convert("RGB"), images[j].convert("RGB")).getbbox())

    def test_new_templates_require_explicit_approval(self):
        manifest = {
            "content_type": "quran",
            "source": {"surah_number": 1, "verses": [1]},
            "visual": {
                "template": "nature_clean",
                "background_candidate": {
                    "direct_video_url": "https://example.test/bg.mp4",
                    "source_url": "https://example.test/license",
                    "approved": True,
                    "user_approved": True,
                    "download_verified": True,
                },
            },
            "audio": {
                "kind": "quran_recitation",
                "approved": True,
                "exact_recording_user_reviewed": True,
                "rights_verified": True,
                "music_allowed": False,
            },
            "publishing": {"approval_required": True, "auto_publish": False},
            "verses": [{"number": 1, "arabic": "بِسْمِ اللَّهِ", "english": "In the name of Allah"}],
        }
        with self.assertRaisesRegex(SystemExit, "explicitly approved"):
            validate_content_manifest(manifest)
        manifest["visual"]["template_approved"] = True
        validate_content_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
