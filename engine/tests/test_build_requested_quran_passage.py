import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_requested_quran_passage import build_requested_batch, save_batch


class RequestedPassageTests(unittest.TestCase):
    # Keep this isolated request path fail-closed and independent of the daily batch.
    def setUp(self):
        self.joined = {"rendering_allowed": False,
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "verses": {f"67:{n}": {"arabic_uthmani": f"عربي {n}",
                "english_saheeh_international": f"English {n}",
                "audio_archive_member": f"audio/067{n:03d}.mp3"} for n in range(1, 6)}}

    def test_builds_exact_requested_range_without_approving_it(self):
        batch = build_requested_batch(self.joined, 67, 2, 4)
        passage = batch["passages"][0]
        self.assertEqual(passage["verse_numbers"], [2, 3, 4])
        self.assertEqual([v["reference"] for v in passage["verses"]], ["67:2", "67:3", "67:4"])
        self.assertFalse(batch["rendering_allowed"])
        self.assertFalse(passage["approval"]["ready_to_render"])
        self.assertFalse(batch["auto_publish"])

    def test_saved_batch_is_valid_json_with_real_newline(self):
        batch = build_requested_batch(self.joined, 67, 1, 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "request.json"
            save_batch(batch, path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), batch)
            self.assertTrue(path.read_bytes().endswith(b"\n"))

    def test_rejects_missing_ayah(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            build_requested_batch(self.joined, 67, 4, 6)

    def test_rejects_ayah_beyond_actual_surah_length(self):
        with self.assertRaisesRegex(ValueError, "30 ayahs"):
            build_requested_batch(self.joined, 67, 22, 31)

    def test_rejects_invalid_or_oversized_range(self):
        for args in ((67, 0, 2), (67, 4, 3), (67, 1, 11), (115, 1, 2)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                build_requested_batch(self.joined, *args)

    def test_rejects_catalog_with_open_rendering_gate(self):
        self.joined["rendering_allowed"] = True
        with self.assertRaises(ValueError):
            build_requested_batch(self.joined, 67, 1, 2)


if __name__ == "__main__":
    unittest.main()
