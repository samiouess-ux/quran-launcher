"""Duration safety tests for the Quran renderer."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from render_video_scenes import validate_video_duration, validate_quran_audio_approval
from background_rotation import order_backgrounds, select_background


class BackgroundRotationTests(unittest.TestCase):
    def test_sequence_starts_with_selected_background_and_contains_all_eligible_once(self):
        import json
        import tempfile
        catalog = {"candidates": [
            {"id": f"bg-{i}", "direct_video_url": f"https://cdn.example/{i}.mp4",
             "source_page_url": f"https://example/{i}", "aspect_ratio": "9:16", "approved": True,
             "user_approved": True, "download_verified": True}
            for i in range(5)
        ]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            sequence = order_backgrounds(path, "video-001")
            self.assertEqual(sequence[0]["id"], select_background(path, "video-001")["id"])
            self.assertEqual({item["id"] for item in sequence}, {f"bg-{i}" for i in range(5)})
            self.assertEqual(len({item["id"] for item in sequence}), 5)
            self.assertEqual(sequence, order_backgrounds(path, "video-001"))
            self.assertNotEqual(sequence, order_backgrounds(path, "video-002"))

    def test_unapproved_or_unverified_candidates_are_excluded(self):
        import json
        import tempfile
        catalog = {"candidates": [
            {"id": "good", "direct_video_url": "https://cdn.example/good.mp4",
             "source_page_url": "https://example/good", "aspect_ratio": "9:16", "approved": True,
             "user_approved": True, "download_verified": True},
            {"id": "not-approved", "direct_video_url": "https://cdn.example/no.mp4",
             "source_page_url": "https://example/no", "aspect_ratio": "9:16", "approved": False,
             "user_approved": True, "download_verified": True},
            {"id": "not-verified", "direct_video_url": "https://cdn.example/no2.mp4",
             "source_page_url": "https://example/no2", "aspect_ratio": "9:16", "approved": True,
             "user_approved": True, "download_verified": False},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            self.assertEqual([item["id"] for item in order_backgrounds(path, "key")], ["good"])

    def test_recent_backgrounds_are_deferred_until_fresh_candidates(self):
        import json
        import tempfile
        catalog = {"candidates": [
            {"id": f"bg-{i}", "direct_video_url": f"https://cdn.example/{i}.mp4",
             "source_page_url": f"https://example/{i}", "aspect_ratio": "9:16", "approved": True,
             "user_approved": True, "download_verified": True}
            for i in range(6)
        ]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            first = select_background(path, "video-003", ["bg-1", "bg-2"])
            sequence = order_backgrounds(path, "video-003", ["bg-1", "bg-2"])
            self.assertEqual(sequence[0]["id"], first["id"])
            self.assertNotIn(sequence[1]["id"], {"bg-1", "bg-2"})
            self.assertNotIn(sequence[2]["id"], {"bg-1", "bg-2"})


class ManifestBackgroundVerificationTests(unittest.TestCase):
    def _manifest(self, download_verified):
        return {
            "content_type": "dua",
            "source": {},
            "visual": {
                "background_candidate": {
                    "direct_video_url": "https://cdn.example/background.mp4",
                    "source_url": "https://example.com/background",
                    "approved": True,
                    "user_approved": True,
                    "download_verified": download_verified,
                }
            },
            "audio": {"kind": "silent"},
            "publishing": {"approval_required": True, "auto_publish": False},
            "items": [{
                "arabic": "ذكر تجريبي",
                "source_name": "مصدر موثّق",
                "source_url": "https://example.com/dhikr",
            }],
        }

    def test_manifest_rejects_background_without_download_verification(self):
        from validate_content_manifest import validate_content_manifest
        for verified in (False, None):
            with self.subTest(download_verified=verified):
                with self.assertRaisesRegex(SystemExit, "downloaded and technically verified"):
                    validate_content_manifest(self._manifest(verified))

    def test_manifest_rejects_missing_download_verification_flag(self):
        from validate_content_manifest import validate_content_manifest
        manifest = self._manifest(True)
        del manifest["visual"]["background_candidate"]["download_verified"]
        with self.assertRaisesRegex(SystemExit, "downloaded and technically verified"):
            validate_content_manifest(manifest)

    def test_manifest_accepts_approved_user_reviewed_verified_background(self):
        from validate_content_manifest import validate_content_manifest
        validate_content_manifest(self._manifest(True))


class VideoDurationTests(unittest.TestCase):
    def test_duration_over_40_seconds_is_allowed_like_original_renderer(self):
        validate_video_duration(50.948)

    def test_short_duration_is_allowed(self):
        validate_video_duration(9.5)

    def test_approved_reviewed_recording_passes(self):
        validate_quran_audio_approval({"approved": True, "exact_recording_user_reviewed": True, "rights_verified": True})

    def test_rights_cleared_preview_only_recording_passes_without_user_approval(self):
        validate_quran_audio_approval({"approved": False, "preview_only": True, "exact_recording_user_reviewed": False, "rights_verified": True})

    def test_unapproved_recording_without_preview_flag_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "not marked approved"):
            validate_quran_audio_approval({"approved": False, "exact_recording_user_reviewed": False, "rights_verified": True})

    def test_preview_only_recording_cannot_be_production_approved(self):
        with self.assertRaisesRegex(SystemExit, "cannot be marked production-approved"):
            validate_quran_audio_approval({"approved": True, "preview_only": True, "rights_verified": True})

    def test_preview_only_recording_still_requires_rights(self):
        with self.assertRaisesRegex(SystemExit, "Reuse permission"):
            validate_quran_audio_approval({"approved": False, "preview_only": True, "rights_verified": False})

    def test_zero_or_negative_duration_is_rejected(self):
        for duration in (0, -1):
            with self.subTest(duration=duration):
                with self.assertRaisesRegex(SystemExit, "must be positive"):
                    validate_video_duration(duration)

    def test_non_finite_duration_is_rejected(self):
        for duration in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(duration=duration):
                with self.assertRaisesRegex(SystemExit, "finite number"):
                    validate_video_duration(duration)


if __name__ == "__main__":
    unittest.main()
