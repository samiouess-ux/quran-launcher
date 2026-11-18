import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import render_cover_template_previews as covers


class OpeningCoverPreviewTests(unittest.TestCase):
    def test_four_preview_designs_render_and_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.png"
            Image.new("RGB", (720, 1280), (36, 48, 62)).save(reference)
            output = root / "covers"
            with patch.object(covers, "REFERENCE_IMAGE", reference):
                paths = covers.render_all("سُورَةُ الْفَاتِحَةِ", 1, 7, output)
            self.assertEqual(len(paths), 4)
            self.assertEqual(
                {p.stem for p in paths},
                {"blue_royal", "emerald_arch", "ivory_classic", "midnight_cinematic"},
            )
            images = [Image.open(p).convert("RGB") for p in paths]
            for image in images:
                self.assertEqual(image.size, (1080, 1920))
            for i in range(len(images)):
                for j in range(i + 1, len(images)):
                    self.assertIsNotNone(
                        ImageChops.difference(images[i], images[j]).getbbox()
                    )

    def test_requires_vocalized_title_and_valid_ayah_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.png"
            Image.new("RGB", (720, 1280), (36, 48, 62)).save(reference)
            target = root / "invalid.png"
            with patch.object(covers, "REFERENCE_IMAGE", reference):
                with self.assertRaisesRegex(ValueError, "title"):
                    covers.render_cover("", 1, 7, "blue_royal", target)
                with self.assertRaisesRegex(ValueError, "range"):
                    covers.render_cover("سُورَةُ الْفَاتِحَةِ", 7, 1, "blue_royal", target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
