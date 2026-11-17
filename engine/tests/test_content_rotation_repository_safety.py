"""Repository-level safety check for the real content rotation catalogue.

The current repository contains review/draft Quran manifests only. Until a
manifest is explicitly approved for rotation, the production selector must
fail closed rather than silently choosing a draft or repeating a prototype.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "select_review_manifest.py"
BATCH_SCRIPT = ROOT / "src" / "select_review_batch.py"
CONTENT = ROOT / "content"


class RepositoryRotationSafetyTests(unittest.TestCase):
    def test_real_quran_catalogue_fails_closed_until_review_approval(self):
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--content-dir", str(CONTENT),
                "--content-type", "quran",
                "--rotation-key", "repository-safety-check",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("No eligible non-recent quran manifest", result.stderr)
        self.assertIn("refusing to repeat or invent content", result.stderr)


if __name__ == "__main__":
    unittest.main()
