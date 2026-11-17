"""CLI tests for the production review-manifest selector."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "select_review_manifest.py"


class SelectReviewManifestTests(unittest.TestCase):
    def write_manifest(self, folder, name, item_id, approved):
        path = folder / name
        path.write_text(json.dumps({
            "id": item_id,
            "content_type": "quran",
            "rotation_approved": approved,
            "publishing": {"approval_required": True, "auto_publish": False},
        }), encoding="utf-8")
        return path

    def run_selector(self, folder, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--content-dir", str(folder),
             "--content-type", "quran", "--rotation-key", "test-key", *extra],
            capture_output=True, text=True,
        )

    def test_selects_approved_manifest_and_prints_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            approved = self.write_manifest(folder, "approved.json", "approved", True)
            self.write_manifest(folder, "draft.json", "draft", False)
            result = self.run_selector(folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), approved.as_posix())

    def test_stops_when_only_manifest_is_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_manifest(folder, "approved.json", "approved", True)
            result = self.run_selector(folder, "--recent-id", "approved")
            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to repeat", result.stderr)


if __name__ == "__main__":
    unittest.main()
