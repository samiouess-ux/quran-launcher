"""Fail-closed tests for reviewed Quran manifest rotation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from content_rotation import choose_manifest, choose_manifests


class ContentRotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)

    def write_manifest(self, filename, item_id, **overrides):
        data = {
            "id": item_id,
            "content_type": "quran",
            "rotation_approved": True,
            "publishing": {"approval_required": True, "auto_publish": False},
        }
        data.update(overrides)
        (self.directory / filename).write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_only_explicitly_reviewed_manifests_are_eligible(self):
        self.write_manifest("approved.json", "approved")
        self.write_manifest("not-reviewed.json", "not-reviewed",
                            rotation_approved=False)
        self.write_manifest("auto-publish.json", "auto-publish",
                            publishing={"approval_required": True, "auto_publish": True})
        self.write_manifest("no-user-review.json", "no-user-review",
                            publishing={"approval_required": False, "auto_publish": False})
        chosen = choose_manifest(self.directory, "quran", rotation_key="key")
        self.assertEqual(chosen.name, "approved.json")

    def test_recent_content_is_never_selected_again(self):
        self.write_manifest("one.json", "one")
        self.write_manifest("two.json", "two")
        chosen = choose_manifest(self.directory, "quran",
                                 recent_ids={"one"}, rotation_key="key")
        self.assertEqual(json.loads(chosen.read_text())["id"], "two")

    def test_batch_contains_distinct_manifests_and_excludes_recent_ids(self):
        for number in range(4):
            self.write_manifest(f"{number}.json", f"item-{number}")
        chosen = choose_manifests(
            self.directory, "quran", 3,
            recent_ids={"item-0"}, rotation_key="batch-key"
        )
        ids = [json.loads(path.read_text())["id"] for path in chosen]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)
        self.assertNotIn("item-0", ids)

    def test_insufficient_pool_fails_without_claiming_partial_batch(self):
        self.write_manifest("only.json", "only")
        with self.assertRaisesRegex(FileNotFoundError, "complete batch of 2"):
            choose_manifests(self.directory, "quran", 2, rotation_key="key")

    def test_unsupported_content_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            choose_manifest(self.directory, "hadith", rotation_key="key")

    def test_malformed_json_and_root_types_are_ignored(self):
        (self.directory / "broken.json").write_text("{", encoding="utf-8")
        (self.directory / "array.json").write_text("[]", encoding="utf-8")
        self.write_manifest("valid.json", "valid")
        chosen = choose_manifest(self.directory, "quran", rotation_key="key")
        self.assertEqual(chosen.name, "valid.json")

    def test_malformed_approval_metadata_is_ignored(self):
        self.write_manifest("string-publishing.json", "bad-string",
                            publishing="approved")
        self.write_manifest("list-publishing.json", "bad-list",
                            publishing=["approval_required", True])
        self.write_manifest("missing-publishing.json", "missing",
                            publishing=None)
        self.write_manifest("valid.json", "valid")
        chosen = choose_manifest(self.directory, "quran", rotation_key="key")
        self.assertEqual(chosen.name, "valid.json")

    def test_missing_content_type_is_not_assumed_to_be_quran(self):
        self.write_manifest("missing-type.json", "missing-type",
                            content_type=None)
        self.write_manifest("valid.json", "valid")
        # Explicit null is not a valid type; the valid manifest remains eligible.
        chosen = choose_manifest(self.directory, "quran", rotation_key="key")
        self.assertEqual(chosen.name, "valid.json")

    def test_missing_auto_publish_flag_is_not_assumed_safe(self):
        self.write_manifest("missing-auto.json", "missing-auto",
                            publishing={"approval_required": True})
        with self.assertRaisesRegex(FileNotFoundError, "No eligible"):
            choose_manifest(self.directory, "quran", rotation_key="key")

    def test_boolean_batch_size_is_rejected(self):
        self.write_manifest("valid.json", "valid")
        with self.assertRaisesRegex(ValueError, "positive integer"):
            choose_manifests(self.directory, "quran", True)


if __name__ == "__main__":
    unittest.main()
