"""Unit tests for the production background-reel builder."""
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from render_video_scenes import (build_background_reel, build_photo_background_reel,
                                 infer_background_tags, select_photo_for_scene)


class BackgroundReelTests(unittest.TestCase):
    def _candidate(self, name):
        return {
            "id": name,
            "direct_video_url": f"https://cdn.example/{name}.mp4",
        }

    def test_loops_one_short_clip_to_cover_full_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            destination = work / "background.mp4"

            def fake_download(url, path):
                path.write_bytes(b"mock video")

            def fake_run(command):
                Path(command[-1]).write_bytes(b"mock output")

            with (
                patch("render_video_scenes.download", side_effect=fake_download),
                patch("render_video_scenes.probe_media_duration", side_effect=[6.0, 10.0]),
                patch("render_video_scenes.run", side_effect=fake_run) as run,
            ):
                selected = build_background_reel(
                    [self._candidate("clip-a"), self._candidate("clip-b")],
                    10.0, work, destination
                )

            self.assertEqual(selected, "clip-a")
            self.assertTrue(destination.is_file())
            self.assertEqual(run.call_count, 1)
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("-stream_loop") + 1], "-1")
            self.assertEqual(command[command.index("-t") + 1],
                "10.000000",
            )
            self.assertFalse((work / "background_concat.txt").exists())

    def test_arabic_keyword_tags_are_literal_and_conservative(self):
        self.assertEqual(infer_background_tags("وَإِلَى الْجِبَالِ كَيْفَ نُصِبَتْ"), {"mountains"})
        self.assertEqual(infer_background_tags("نص لا يحتوي كلمات طبيعية"), set())

    def test_scene_photo_prefers_matching_tags_and_falls_back(self):
        pool = [{"id":"sea","tags":["sea"]},{"id":"mountain","tags":["mountains"]}]
        self.assertEqual(select_photo_for_scene(pool, "هذا البحر", "seed", 0, set())["id"], "sea")
        self.assertEqual(select_photo_for_scene(pool, "كلمات عامة", "seed", 0, set())["id"], "mountain")

    def test_photo_reel_uses_one_photo_per_timed_scene_and_crossfades(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            photos = []
            for name, tag in (("sea","sea"),("mountain","mountains")):
                path = work / f"{name}.jpg"
                path.write_bytes(b"x" * 60000)
                photos.append({"id":name,"tags":[tag],"local_path":str(path)})
            scenes = [
                {"verses":[{"arabic":"هذا البحر"}],"duration":5.0},
                {"verses":[{"arabic":"هذه الجبال"}],"duration":5.0},
            ]
            destination = work / "photo-reel.mp4"
            def fake_run(command):
                Path(command[-1]).write_bytes(b"mock output")
            with patch("render_video_scenes.run", side_effect=fake_run) as run:
                with patch("render_video_scenes.probe_media_duration", return_value=10.0):
                    chosen = build_photo_background_reel(photos, scenes, 10.0, work, destination, "stable-test-key")
            self.assertEqual(chosen, ["sea","mountain"])
            graph = run.call_args.args[0][run.call_args.args[0].index("-filter_complex") + 1]
            self.assertIn("zoompan=", graph)
            self.assertIn("xfade=transition=fade", graph)

    def test_photo_reel_rejects_missing_local_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            candidate = {"id": "missing", "local_path": str(work / "missing.jpg")}
            with self.assertRaisesRegex(SystemExit, "No downloaded and verified photo"):
                build_photo_background_reel([candidate], [{"verses":[{"arabic":"نص"}],"duration":5.0}], 5.0, work, work / "photo-reel.mp4", "test")
    def test_rejects_empty_candidate_list(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with self.assertRaisesRegex(SystemExit, "No approved backgrounds"):
                build_background_reel([], 10.0, work, work / "background.mp4")

    def test_rejects_candidates_with_no_usable_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            destination = work / "background.mp4"

            def fake_download(url, path):
                path.write_bytes(b"mock video")

            with patch("render_video_scenes.download", side_effect=fake_download), \
                 patch("render_video_scenes.probe_media_duration", return_value=0.0), \
                 patch("render_video_scenes.run") as run:
                with self.assertRaisesRegex(SystemExit, "No approved background has a usable"):
                    build_background_reel(
                        [self._candidate("empty-clip")], 10.0, work, destination
                    )
            run.assert_not_called()

    def test_rejects_non_finite_or_non_positive_target_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for duration in (0.0, -1.0, math.nan, math.inf, -math.inf):
                with self.subTest(duration=duration):
                    with self.assertRaisesRegex(SystemExit, "finite positive"):
                        build_background_reel([], duration, work, work / "background.mp4")

    def test_rejects_final_reel_shorter_than_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            destination = work / "background.mp4"

            def fake_download(url, path):
                path.write_bytes(b"mock video")

            def fake_run(command):
                Path(command[-1]).write_bytes(b"mock output")

            with patch("render_video_scenes.download", side_effect=fake_download), \
                 patch("render_video_scenes.probe_media_duration", side_effect=[9.8, 9.8]), \
                 patch("render_video_scenes.run", side_effect=fake_run):
                with self.assertRaisesRegex(SystemExit, "Looped background"):
                    build_background_reel([self._candidate("clip-a")], 10.0, work, destination)


if __name__ == "__main__":
    unittest.main()
