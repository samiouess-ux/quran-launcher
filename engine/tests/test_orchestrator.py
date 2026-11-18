"""Tests for the Quran-only review orchestrator."""
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import orchestrator
from orchestrator import build_plan, load_history, render_plan


class OrchestratorTests(unittest.TestCase):
    def test_selects_three_distinct_quran_manifests_without_dua_or_dhikr(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            manifests = []
            for index in range(3):
                path = folder / f"quran-{index}.json"
                path.write_text(json.dumps({
                    "id": f"quran-{index}",
                    "content_type": "quran",
                    "publishing": {"approval_required": True, "auto_publish": False},
                }), encoding="utf-8")
                manifests.append(path)

            def choose_many(_folder, kind, count, _recent, _key):
                self.assertEqual(kind, "quran")
                self.assertEqual(count, 3)
                return manifests

            with patch("orchestrator.choose_manifests", side_effect=choose_many) as choose, patch("orchestrator.validate_content_manifest") as validate:
                plan = build_plan(folder, {"content": []}, "test-day")

            self.assertEqual([item["content_type"] for item in plan], ["quran", "quran", "quran"])
            self.assertEqual(validate.call_count, 3)
            self.assertEqual(len({item["content_id"] for item in plan}), 3)

    def test_missing_quran_manifest_blocks_incomplete_three_video_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with patch("orchestrator.choose_manifests", side_effect=FileNotFoundError("only one Quran manifest")):
                with self.assertRaisesRegex(FileNotFoundError, "only one Quran"):
                    build_plan(folder, {"content": []}, "test-day")

    def test_manifest_must_explicitly_match_quran_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder / "quran.json"
            path.write_text(json.dumps({
                "id": "q1",
                "publishing": {"approval_required": True, "auto_publish": False},
            }), encoding="utf-8")
            with patch("orchestrator.choose_manifests", return_value=[path]), patch("orchestrator.validate_content_manifest"):
                with self.assertRaisesRegex(SystemExit, "must explicitly declare"):
                    build_plan(folder, {"content": []}, "test-day", video_count=1)

    def test_missing_history_starts_empty_without_creating_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            history = load_history(path)
            self.assertEqual(history, {"content": []})
            self.assertFalse(path.exists())

    def test_invalid_history_content_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            path.write_text('{"content":"not-a-list"}', encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "must be a list"):
                load_history(path)


    def test_render_plan_uses_one_batch_renderer_for_all_three_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            outputs = [folder / f"video-{index}.mp4" for index in range(3)]
            for output in outputs:
                output.write_bytes(b"mp4")
            plan = [
                {"content_type": "quran", "manifest": str(folder / f"quran-{i}.json"), "content_id": f"quran-{i}"}
                for i in range(3)
            ]
            batch_result = {
                "status": "multi_video_batch_rendered_for_manual_review",
                "videos": [{"video": str(path)} for path in outputs],
            }
            with patch("orchestrator.render_batch", return_value=batch_result) as render:
                result = render_plan(plan, folder / "out")
            render.assert_called_once_with([Path(item["manifest"]) for item in plan], folder / "out")
            self.assertEqual([item["output"] for item in result], [str(path) for path in outputs])

    def test_render_plan_rejects_partial_batch_before_rendering(self):
        plan = [{"content_type": "quran", "manifest": "one.json", "content_id": "one"}]
        with patch("orchestrator.render_batch") as render:
            with self.assertRaisesRegex(ValueError, "exactly 3 distinct manifests"):
                render_plan(plan, Path("output"))
            render.assert_not_called()

    def test_render_does_not_mark_content_as_delivered_or_mutate_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            history_path = folder / "history.json"
            original_history = {"content": ["previous-item"]}
            history_path.write_text(json.dumps(original_history), encoding="utf-8")
            plan = [{"content_type": "quran", "manifest": "quran.json", "content_id": "new-item"}]
            rendered = [{**plan[0], "output": "new-item.mp4"}]

            with patch.object(sys, "argv", [
                "orchestrator", "--history", str(history_path),
                "--output-dir", str(folder / "out"), "--render",
            ]), patch("orchestrator.build_plan", return_value=plan), patch(
                "orchestrator.render_plan", return_value=rendered
            ):
                self.assertEqual(orchestrator.main(), 0)

            self.assertEqual(json.loads(history_path.read_text(encoding="utf-8")), original_history)

if __name__ == "__main__":
    unittest.main()
