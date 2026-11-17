"""Regression tests for separate, duration-controlled dua/dhikr screens."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import render_dua_video


class DuaRendererTests(unittest.TestCase):
    def test_each_item_requires_explicit_positive_duration(self):
        self.assertEqual(render_dua_video.item_duration({"duration_seconds": 4}), 4.0)
        for value in (None, 0, -1, True, "4"):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                render_dua_video.item_duration({"duration_seconds": value})

    def test_slideshow_creates_one_overlay_per_item(self):
        items = [
            {"arabic": "الأول", "source_name": "المصدر الأول", "duration_seconds": 3},
            {"arabic": "الثاني", "source_name": "المصدر الثاني", "duration_seconds": 5},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            with patch.object(render_dua_video, "create_overlay") as draw:
                duration = render_dua_video.build_slideshow(items, "ذكر", work)
            self.assertEqual(duration, 8.0)
            self.assertEqual(draw.call_count, 2)
            self.assertEqual([call.args[1] for call in draw.call_args_list], items)
            playlist = (work / "overlays.ffconcat").read_text(encoding="utf-8")
            self.assertIn("item_000.png", playlist)
            self.assertIn("item_001.png", playlist)
            self.assertEqual(playlist.count("duration "), 2)

    def test_audio_duration_mismatch_fails_closed(self):
        audio = Path('audio.mp3')
        with patch.object(render_dua_video, 'probe_duration', return_value=9.0):
            self.assertEqual(render_dua_video.validate_audio_duration(audio, 9.5), 9.0)
        with patch.object(render_dua_video, 'probe_duration', return_value=12.0):
            with self.assertRaises(SystemExit):
                render_dua_video.validate_audio_duration(audio, 9.5)

    def test_renderer_does_not_silently_pad_audio(self):
        source = (ROOT / 'src' / 'render_dua_video.py').read_text(encoding='utf-8')
        self.assertIn('validate_audio_duration(audio_file, duration)', source)
        self.assertNotIn('apad', source)

    def test_duration_policy_targets_under_one_minute_and_fails_above_65(self):
        self.assertEqual(render_dua_video.TARGET_MAX_DURATION_SECONDS, 60.0)
        self.assertEqual(render_dua_video.HARD_MAX_DURATION_SECONDS, 65.0)
        items = [{"arabic": "ذكر", "source_name": "مصدر", "duration_seconds": 66}]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(render_dua_video, "create_overlay"):
                with self.assertRaises(SystemExit):
                    render_dua_video.build_slideshow(items, "ذكر", Path(tmp))

    def test_renderer_keeps_validation_and_separate_content_type_gate(self):
        source = (ROOT / "src" / "render_dua_video.py").read_text(encoding="utf-8")
        self.assertIn("validate_content_manifest(data)", source)
        self.assertIn('not in {"dua", "dhikr"}', source)
        self.assertIn("audio is checked as a whole, not synced per item", source)

    def test_overlay_rejects_missing_source_and_text(self):
        with self.assertRaises(SystemExit):
            render_dua_video.create_overlay("ذكر", {"arabic": "نص"}, Path("unused.png"))


if __name__ == "__main__":
    unittest.main()
