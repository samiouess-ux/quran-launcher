import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from render_quran_review_batch import render_batch


def manifest(surah, background, template="ornate_gold_classic"):
    return {
        "id": f"surah-{surah}",
        "content_type": "quran",
        "source": {"surah_number": surah, "surah_name_ar": "الفاتحة", "verses": [1]},
        "visual": {
            "template": template,
            "template_approved": True,
            "background_candidate": {
                "direct_video_url": background,
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


class QuranBatchRendererTests(unittest.TestCase):
    def test_requires_at_least_two_manifests(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            render_batch([Path("one.json")], Path("out"))

    def test_rejects_repeated_surah_before_rendering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for index, bg in enumerate(("https://example.test/a.mp4", "https://example.test/b.mp4")):
                path = root / f"{index}.json"
                path.write_text(json.dumps(manifest(94, bg)), encoding="utf-8")
                paths.append(path)
            with self.assertRaisesRegex(ValueError, "distinct surahs"):
                render_batch(paths, root / "out")

    def test_rejects_repeated_visual_combination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for surah in (1, 2):
                path = root / f"{surah}.json"
                path.write_text(json.dumps(manifest(surah, "https://example.test/same.mp4")), encoding="utf-8")
                paths.append(path)
            with self.assertRaisesRegex(ValueError, "distinct approved"):
                render_batch(paths, root / "out")


if __name__ == "__main__":
    unittest.main()
