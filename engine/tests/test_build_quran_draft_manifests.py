import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_quran_draft_manifests import build_draft_manifests


def candidate(cid, surah):
    return {
        "candidate_id": cid,
        "surah_number": surah,
        "verses": [
            {"ayah": 4, "reference": f"{surah}:4", "arabic_uthmani": "نَصٌّ عَرَبِيٌّ", "english_saheeh_international": "Translation one"},
            {"ayah": 5, "reference": f"{surah}:5", "arabic_uthmani": "نَصٌّ ثَانٍ", "english_saheeh_international": "Translation two"},
        ],
    }


class DraftManifestTests(unittest.TestCase):
    def test_builds_distinct_review_only_manifests(self):
        batch = {"batch_status": "review_candidates_only", "passages": [candidate("a", 19), candidate("b", 88)]}
        report = {
            "rendering_allowed": False,
            "auto_publish": False,
            "items": [
                {"candidate_id": "a", "surah_number": 19, "status": "audio_prepared_requires_exact_recording_listen_and_user_review", "requested_verses": [4, 5], "selected_verses": [4, 5], "verse_durations_seconds": {4: 15.2, 5: 17.1}, "processed_verse_durations_seconds": {"4": 13.2, "5": 14.7}, "edge_silence_removed_seconds": {"4": 2.0, "5": 2.4}, "inter_verse_silence_seconds": 0.24, "audio_file": "a.mp3", "duration_seconds": 27.9},
                {"candidate_id": "b", "surah_number": 88, "status": "audio_prepared_requires_exact_recording_listen_and_user_review", "requested_verses": [4, 5], "selected_verses": [4, 5], "verse_durations_seconds": {4: 13.0, 5: 15.0}, "audio_file": "b.mp3", "duration_seconds": 28.0},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = build_draft_manifests(batch, report, Path(tmp))
            self.assertEqual(len(result), 2)
            for item in result:
                data = json.loads(Path(item["manifest"]).read_text(encoding="utf-8"))
                self.assertFalse(data["audio"]["approved"])
                self.assertFalse(data["audio"]["rights_verified"])
                self.assertFalse(data["rotation_approved"])
                self.assertFalse(data["publishing"]["auto_publish"])
                self.assertFalse(data["preflight"]["rendering_allowed"])
                self.assertEqual([v["number"] for v in data["verses"]], [4, 5])
                if data["id"] == "a":
                    self.assertEqual(data["audio"]["source_verse_durations_seconds"], {"4": 15.2, "5": 17.1})
                    self.assertEqual(data["audio"]["processed_verse_durations_seconds"], {"4": 13.2, "5": 14.7})
                    self.assertEqual(data["audio"]["edge_silence_removed_seconds"], {"4": 2.0, "5": 2.4})
                    self.assertEqual(data["audio"]["inter_verse_silence_seconds"], 0.24)
                    self.assertIn("leading/trailing silence", data["audio"]["notes"])
            self.assertEqual(data["source"]["surah_name_ar"], "الغاشية")
            self.assertIn("سورة الغاشية", data["caption"]["text"])

    def test_builds_single_review_only_manifest_for_one_video_slot(self):
        batch = {"batch_status": "review_candidates_only", "passages": [candidate("slot", 47)]}
        report = {
            "rendering_allowed": False,
            "auto_publish": False,
            "items": [
                {"candidate_id": "slot", "surah_number": 47, "status": "audio_prepared_requires_exact_recording_listen_and_user_review", "requested_verses": [4, 5], "selected_verses": [4, 5], "verse_durations_seconds": {4: 12.0, 5: 13.0}, "audio_file": "slot.mp3", "duration_seconds": 25.0},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = build_draft_manifests(batch, report, Path(tmp))
            self.assertEqual(len(result), 1)
            data = json.loads(Path(result[0]["manifest"]).read_text(encoding="utf-8"))
            self.assertFalse(data["audio"]["approved"])
            self.assertFalse(data["audio"]["rights_verified"])
            self.assertFalse(data["rotation_approved"])
            self.assertFalse(data["publishing"]["auto_publish"])
            self.assertFalse(data["publishing"]["telegram_delivery"])
            self.assertFalse(data["preflight"]["rendering_allowed"])

    def test_builds_later_part_from_contiguous_slice_of_same_candidate(self):
        batch = {"batch_status": "review_candidates_only", "passages": [candidate("source", 19)]}
        report = {"rendering_allowed": False, "auto_publish": False, "items": [
            {"candidate_id": "source_part_002", "source_candidate_id": "source",
             "part_index": 2, "part_count": 2, "surah_number": 19,
             "status": "audio_prepared_requires_review", "requested_verses": [4, 5],
             "selected_verses": [5], "verse_durations_seconds": {5: 12.0},
             "audio_file": "part2.mp3", "duration_seconds": 12.0},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            result = build_draft_manifests(batch, report, Path(tmp))
            data = json.loads(Path(result[0]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(data["id"], "source_part_002")
            self.assertEqual(data["source_candidate_id"], "source")
            self.assertEqual(data["part_index"], 2)
            self.assertEqual([v["number"] for v in data["verses"]], [5])
            self.assertEqual(data["audio"]["production_audio_file"], "part2.mp3")
            self.assertFalse(data["preflight"]["rendering_allowed"])

    def test_rejects_missing_ayah_from_audio(self):
        batch = {"batch_status": "review_candidates_only", "passages": [candidate("a", 19), candidate("b", 88)]}
        report = {"rendering_allowed": False, "auto_publish": False, "items": [
            {"candidate_id": "a", "surah_number": 19, "status": "audio_prepared", "requested_verses": [4, 5], "selected_verses": [5], "verse_durations_seconds": {4: 12}, "audio_file": "a.mp3", "duration_seconds": 12},
            {"candidate_id": "b", "surah_number": 88, "status": "audio_prepared", "selected_verses": [4, 5], "verse_durations_seconds": {4: 6, 5: 6}, "audio_file": "b.mp3", "duration_seconds": 12},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "request must match|contiguous slice"):
                build_draft_manifests(batch, report, Path(tmp))


if __name__ == "__main__":
    unittest.main()
