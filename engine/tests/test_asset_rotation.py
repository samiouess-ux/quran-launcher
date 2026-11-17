"""Tests for approved asset selection and fail-closed repeat protection."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from asset_rotation import choose_asset


class AssetRotationTests(unittest.TestCase):
    def test_selects_approved_asset_not_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assets.json"
            entries = [
                {"id": "used", "approved": True, "user_approved": True,
                 "rights_verified": True, "source_url": "https://source.test",
                 "asset_url": "https://asset.test/1"},
                {"id": "fresh", "approved": True, "user_approved": True,
                 "rights_verified": True, "source_url": "https://source.test",
                 "asset_url": "https://asset.test/2"}
            ]
            path.write_text(json.dumps({"background": entries}), encoding="utf-8")
            self.assertEqual(choose_asset(path, "background", ["used"], "daily-1")["id"], "fresh")

    def test_rejects_unapproved_or_unlicensed_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assets.json"
            path.write_text(json.dumps({"audio": [
                {"id": "bad", "approved": True, "user_approved": True,
                 "rights_verified": False, "source_url": "https://source.test",
                 "asset_url": "https://asset.test/audio"}
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(LookupError, "refusing fallback"):
                choose_asset(path, "audio", rotation_key="daily-1")


if __name__ == "__main__":
    unittest.main()
