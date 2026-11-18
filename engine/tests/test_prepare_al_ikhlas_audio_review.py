import io
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import prepare_al_ikhlas_audio_review as module


class FakeArchive:
    def __init__(self):
        self.members = [
            f"ayat-12-1-2020/112/10-11200{ayah}-A08.mp3"
            for ayah in range(1, 5)
        ]

    def namelist(self):
        return list(self.members)

    def open(self, member):
        if member not in self.members:
            raise KeyError(member)
        return io.BytesIO(f"mp3-verse-{member[-9:-7]}".encode())


def inventory():
    return {
        "mapped_verse_count": 6236,
        "expected_verse_count": 6236,
        "recitation": "Hafs",
        "reciter_internal": "Maher Al-Muaiqly",
        "expected_official_sha256": module.EXPECTED_ARCHIVE_SHA256,
        "source_url": "https://example.test/official.zip",
        "verses": {
            f"112:{ayah}": f"ayat-12-1-2020/112/10-11200{ayah}-A08.mp3"
            for ayah in range(1, 5)
        },
    }


class AlIkhlasAudioReviewTests(unittest.TestCase):
    def test_extracts_four_complete_ayahs_in_order_for_review_only(self):
        archive = FakeArchive()

        @contextmanager
        def fake_open(_inventory):
            yield archive

        durations = iter([3.1, 2.8, 3.4, 2.9, 12.2])

        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"combined-mp3")
            return None

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "audio"
            with patch.object(module, "open_verified_archive", fake_open):
                with patch.object(module, "probe_duration", side_effect=lambda _p: next(durations)):
                    with patch.object(module.subprocess, "run", side_effect=fake_run):
                        report = module.prepare_audio_review(inventory(), output)

            self.assertEqual(report["verses"], [1, 2, 3, 4])
            self.assertEqual(report["reciter"], "Maher Al-Muaiqly")
            self.assertEqual(report["riwaya"], "Hafs")
            self.assertEqual(report["combined_audio_duration_seconds"], 12.2)
            self.assertEqual(set(report["archive_members"]), {"1", "2", "3", "4"})
            self.assertTrue(all((output / f"al_ikhlas_112_{n:02d}.mp3").is_file() for n in range(1, 5)))
            self.assertTrue((output / "al_ikhlas_112_1_4_maher_hafs_review.mp3").is_file())
            self.assertFalse(report["audio_approved"])
            self.assertFalse(report["exact_recording_user_reviewed"])
            self.assertFalse(report["rendering_allowed"])
            self.assertFalse(report["telegram_sent"])
            self.assertFalse(report["tiktok_published"])
            concat_text = (output / "concat.txt").read_text(encoding="utf-8")
            self.assertLess(concat_text.index("112_01.mp3"), concat_text.index("112_04.mp3"))

    def test_rejects_wrong_reciter_or_riwaya(self):
        data = inventory()
        data["reciter_internal"] = "Different reciter"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "expected Maher"):
                module.prepare_audio_review(data, Path(tmp))

    def test_rejects_missing_ayah_mapping(self):
        data = inventory()
        del data["verses"]["112:3"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "missing 112:3"):
                with patch.object(module, "open_verified_archive") as open_archive:
                    open_archive.return_value.__enter__.return_value = FakeArchive()
                    module.prepare_audio_review(data, Path(tmp))


if __name__ == "__main__":
    unittest.main()
