"""Regression tests for content-type-specific safety gates."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from validate_content_manifest import validate_content_manifest


class ContentManifestTests(unittest.TestCase):
    def review_preview_manifest(self):
        data = json.loads((ROOT / "content/second_video_ash_sharh_94_1_8_draft.json").read_text(encoding="utf-8"))
        # Unit-test fixture: isolate audio policy from the separate technical
        # background-download gate. The real manifest remains unmodified.
        data["visual"]["background_candidate"]["download_verified"] = True
        return data

    def test_quran_manifest_without_technical_background_verification_is_rejected(self):
        data = json.loads((ROOT / "content/first_video.json").read_text(encoding="utf-8"))
        self.assertTrue(data["visual"]["background_candidate"].get("downloaded"))
        self.assertIsNot(data["visual"]["background_candidate"].get("download_verified"), True)
        with self.assertRaisesRegex(SystemExit, "downloaded and technically verified"):
            validate_content_manifest(data)

    def test_unapproved_quran_audio_is_allowed_only_as_review_preview(self):
        data = self.review_preview_manifest()
        self.assertFalse(data["audio"]["approved"])
        self.assertTrue(data["audio"]["preview_only"])
        self.assertFalse(data["audio"]["exact_recording_user_reviewed"])
        validate_content_manifest(data)

    def test_preview_only_quran_audio_still_requires_reuse_rights(self):
        data = self.review_preview_manifest()
        data["audio"]["rights_verified"] = False
        with self.assertRaisesRegex(SystemExit, "Reuse permission"):
            validate_content_manifest(data)

    def test_unapproved_quran_audio_without_preview_gate_is_rejected(self):
        data = self.review_preview_manifest()
        data["audio"]["preview_only"] = False
        with self.assertRaisesRegex(SystemExit, "only an explicit preview_only"):
            validate_content_manifest(data)

    def test_preview_only_quran_audio_cannot_be_marked_production_approved(self):
        data = self.review_preview_manifest()
        data["audio"]["approved"] = True
        with self.assertRaisesRegex(SystemExit, "cannot also be marked"):
            validate_content_manifest(data)

    def dua_manifest(self):
        return {
            "content_type": "dua",
            "source": {"collection": "review_pending"},
            "items": [{
                "arabic": "نص دعاء تجريبي غير مخصص للإنتاج",
                "source_name": "Test source",
                "source_url": "https://example.org/test"
            }],
            "audio": {
                "kind": "ambient_nature", "approved": True,
                "rights_verified": True, "user_approved": True,
                "music_allowed": False
            },
            "visual": {
                "template": "ornate_gold_classic",
                "background_candidate": {
                    "source_url": "https://example.org/background",
                    "direct_video_url": "https://example.org/background.mp4",
                    "approved": True, "user_approved": True,
                    "download_verified": True
                }
            },
            "publishing": {"approval_required": True, "auto_publish": False}
        }

    def test_sourced_dua_with_approved_ambient_audio_passes(self):
        validate_content_manifest(self.dua_manifest())

    def test_dua_without_source_is_rejected(self):
        data = self.dua_manifest()
        data["items"][0]["source_url"] = ""
        with self.assertRaisesRegex(SystemExit, "HTTPS religious source"):
            validate_content_manifest(data)

    def test_dua_cannot_use_quran_recitation_audio_kind(self):
        data = self.dua_manifest()
        data["audio"]["kind"] = "quran_recitation"
        with self.assertRaisesRegex(SystemExit, "must not be mislabeled"):
            validate_content_manifest(data)

    def test_unapproved_background_is_rejected(self):
        data = self.dua_manifest()
        data["visual"]["background_candidate"]["user_approved"] = False
        with self.assertRaisesRegex(SystemExit, "Background must be approved"):
            validate_content_manifest(data)

    def test_missing_content_type_is_rejected(self):
        data = self.dua_manifest()
        del data["content_type"]
        with self.assertRaisesRegex(SystemExit, "content_type must be explicitly"):
            validate_content_manifest(data)

    def test_missing_auto_publish_setting_is_rejected(self):
        data = self.dua_manifest()
        del data["publishing"]["auto_publish"]
        with self.assertRaisesRegex(SystemExit, "Auto-publishing"):
            validate_content_manifest(data)

    def test_missing_audio_kind_is_rejected(self):
        data = self.dua_manifest()
        del data["audio"]["kind"]
        with self.assertRaisesRegex(SystemExit, "audio.kind must explicitly"):
            validate_content_manifest(data)

    def test_auto_publish_is_always_rejected(self):
        data = self.dua_manifest()
        data["publishing"]["auto_publish"] = True
        with self.assertRaisesRegex(SystemExit, "Auto-publishing"):
            validate_content_manifest(data)


if __name__ == "__main__":
    unittest.main()
