import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import prepare_quran_review_batch_audio as module


class FakeArchive:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def namelist(self):
        counts = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
        return [f"actual/10-{s:03d}{a:03d}-A08.mp3" for s, count in enumerate(counts, 1) for a in range(1, count + 1)]

    def open(self, member):
        return io.BytesIO(b"fake-mp3")


class QuranBatchAudioTests(unittest.TestCase):
    def test_downloads_and_verifies_archive_when_server_rejects_range_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_zip = root / "source.zip"
            with ZipFile(source_zip, "w") as archive:
                archive.writestr("audio/001.mp3", b"official-audio")
            def fake_download(url, destination):
                module.shutil.copyfile(source_zip, destination)
                return str(destination), None

            with patch.object(module, "RemoteZip", side_effect=module.remotezip.RangeNotSupported), \
                 patch.object(module.urllib.request, "urlretrieve", side_effect=fake_download):
                with module.open_audio_archive({"source_url": "https://example.invalid/audio.zip"}) as archive:
                    self.assertEqual(archive.namelist(), ["audio/001.mp3"])
                    self.assertEqual(archive.read("audio/001.mp3"), b"official-audio")

    def test_falls_back_when_range_fails_only_when_reading_a_member(self):
        class LateRangeFailureArchive:
            def namelist(self):
                return ["audio/001.mp3"]
            def open(self, member):
                raise module.remotezip.RangeNotSupported("range rejected during member read")
            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_zip = root / "source.zip"
            with ZipFile(source_zip, "w") as archive:
                archive.writestr("audio/001.mp3", b"official-audio-1")
                archive.writestr("audio/002.mp3", b"official-audio-2")
            def fake_download(url, destination):
                module.shutil.copyfile(source_zip, destination)
                return str(destination), None

            with patch.object(module, "RemoteZip", return_value=LateRangeFailureArchive()), \
                 patch.object(module.urllib.request, "urlretrieve", side_effect=fake_download):
                with module.open_audio_archive({"source_url": "https://example.invalid/audio.zip"}) as archive:
                    with archive.open("audio/001.mp3") as source:
                        self.assertEqual(source.read(), b"official-audio-1")
                    # RemoteZip is closed after fallback; subsequent members
                    # must continue to come from the verified local archive.
                    with archive.open("audio/002.mp3") as source:
                        self.assertEqual(source.read(), b"official-audio-2")

    def test_rejects_corrupt_fallback_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            corrupt_zip = Path(tmp) / "corrupt.zip"
            corrupt_zip.write_bytes(b"not-a-zip")
            with patch.object(module, "RemoteZip", side_effect=module.remotezip.RangeNotSupported), \
                 patch.object(module.urllib.request, "urlretrieve", side_effect=lambda url, path: module.shutil.copyfile(corrupt_zip, path)):
                with self.assertRaisesRegex(ValueError, "archive is invalid"):
                    with module.open_audio_archive({"source_url": "https://example.invalid/audio.zip"}):
                        self.fail("A corrupt archive must never be yielded")

    def test_resolves_manifest_member_with_mojibake_directory_by_unique_basename(self):
        actual = "ayat-12-1-2020/045 Al-Jathiyah العربية/10-045001-A08.mp3"
        requested = "ayat-12-1-2020/045 Al-Jathiyah \ufffd\ufffd/10-045001-A08.mp3"
        self.assertEqual(module.resolve_archive_member([actual], requested), actual)

    def test_rejects_ambiguous_duplicate_audio_basenames(self):
        names = ["one/10-045001-A08.mp3", "two/10-045001-A08.mp3"]
        with self.assertRaisesRegex(ValueError, "found 2"):
            module.resolve_archive_member(names, "broken/path/10-045001-A08.mp3")

    def test_prepares_distinct_surahs_without_approving_or_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = {
                "batch_status": "review_candidates_only",
                "rendering_allowed": False,
                "auto_publish": False,
                "passages": [
                    {"candidate_id": "s1", "surah_number": 1, "verses": [{"ayah": 1}, {"ayah": 2}]},
                    {"candidate_id": "s2", "surah_number": 2, "verses": [{"ayah": 1}, {"ayah": 2}]},
                    {"candidate_id": "s3", "surah_number": 3, "verses": [{"ayah": 1}, {"ayah": 2}, {"ayah": 3}]},
                ],
            }
            inventory = {
                "mapped_verse_count": 6236,
                "verses": {f"{s}:{a}": f"manifest/10-{s:03d}{a:03d}-A08.mp3" for s in (1, 2, 3) for a in (1, 2, 3)},
            }
            batch_path, inventory_path = root / "batch.json", root / "inventory.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            def fake_run(command, **kwargs):
                Path(command[-1]).write_bytes(b"combined")
                return None

            def fake_trim(source, destination, source_duration):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"trimmed")
                return source_duration

            with patch.object(module, "RemoteZip", return_value=FakeArchive()), \
                 patch.object(module, "probe", side_effect=lambda p: ({"s1": 33.0, "s2": 39.0, "s3": 40.0}[Path(p).parents[1].name] if Path(p).name == "passage.mp3" else {"001_001.mp3": 16.0, "001_002.mp3": 17.0, "002_001.mp3": 26.0, "002_002.mp3": 13.0, "003_001.mp3": 20.0, "003_002.mp3": 20.0, "003_003.mp3": 40.0}[Path(p).name])), \
                 patch.object(module, "trim_edge_silence", side_effect=fake_trim), \
                 patch.object(module.subprocess, "run", side_effect=fake_run):
                report = module.prepare_batch(batch_path, inventory_path, root / "out")

            self.assertEqual(report["audio_prepared_count"], 3)
            self.assertEqual(report["preview_part_count"], 3)
            partials = [item for item in report["items"] if item["source_candidate_id"] == "s3"]
            self.assertEqual([item["selected_verses"] for item in partials], [[1, 2]])
            self.assertEqual(partials[0]["requested_verses"], [1, 2, 3])
            self.assertEqual(partials[0]["remaining_verses"], [3])
            self.assertFalse(partials[0]["passage_complete"])
            self.assertEqual(partials[0]["part_count"], 1)
            self.assertEqual(partials[0]["duration_seconds"], 40.0)
            self.assertEqual(partials[0]["processed_verse_durations_seconds"], {1: 20.0, 2: 20.0})
            self.assertIn("only confirmed delivery advances the sequence", report["continuation_policy"])
            self.assertTrue((root / "out" / "s3" / "processed" / "003_003.mp3").is_file())
            self.assertTrue(Path(partials[0]["processed_audio_files"]["1"]).is_file())
            self.assertEqual(report["distinct_surah_count"], 3)
            self.assertFalse(report["rendering_allowed"])
            self.assertFalse(report["telegram_delivery"])
            self.assertFalse(report["auto_publish"])
            self.assertTrue(all(not item.get("audio_approved", True) for item in report["items"]))

    def test_selects_longest_contiguous_processed_ayah_prefix_up_to_40_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = {
                "batch_status": "review_candidates_only",
                "rendering_allowed": False,
                "auto_publish": False,
                "passages": [{
                    "candidate_id": "variable-length",
                    "surah_number": 41,
                    "verses": [{"ayah": 1}, {"ayah": 2}, {"ayah": 3}],
                }],
            }
            inventory = {
                "mapped_verse_count": 6236,
                "verses": {f"41:{n}": f"manifest/10-{41:03d}{n:03d}-A08.mp3" for n in (1, 2, 3)},
            }
            batch_path, inventory_path = root / "batch.json", root / "inventory.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            def fake_run(command, **kwargs):
                Path(command[-1]).write_bytes(b"combined")
                return None

            trimmed = iter([18.0, 17.0, 11.0])
            def fake_trim(source, destination, source_duration):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"trimmed")
                return next(trimmed)

            with patch.object(module, "RemoteZip", return_value=FakeArchive()), \
                 patch.object(module, "probe", side_effect=[20.0, 18.0, 10.0, 35.0]), \
                 patch.object(module, "trim_edge_silence", side_effect=fake_trim), \
                 patch.object(module.subprocess, "run", side_effect=fake_run):
                report = module.prepare_batch(batch_path, inventory_path, root / "out", target_count=1)

            item = report["items"][0]
            self.assertEqual(item["selected_verses"], [1, 2])
            self.assertEqual(item["duration_seconds"], 35.0)
            self.assertEqual(item["processed_verse_durations_seconds"], {1: 18.0, 2: 17.0})
            self.assertEqual(set(item["processed_audio_files"]), {"1", "2"})

    def test_accepts_short_complete_surah_without_artificial_30_second_minimum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = {
                "batch_status": "review_candidates_only",
                "rendering_allowed": False,
                "auto_publish": False,
                "passages": [{
                    "candidate_id": "short-surah",
                    "surah_number": 112,
                    "verses": [{"ayah": 1}, {"ayah": 2}, {"ayah": 3}, {"ayah": 4}],
                }],
            }
            inventory = {
                "mapped_verse_count": 6236,
                "verses": {f"112:{n}": f"manifest/10-{112:03d}{n:03d}-A08.mp3" for n in (1, 2, 3, 4)},
            }
            batch_path, inventory_path = root / "batch.json", root / "inventory.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            def fake_run(command, **kwargs):
                Path(command[-1]).write_bytes(b"combined")
                return None

            trimmed = iter([3.0, 3.0, 3.0, 3.0])
            def fake_trim(source, destination, source_duration):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"trimmed")
                return next(trimmed)

            with patch.object(module, "RemoteZip", return_value=FakeArchive()), \
                 patch.object(module, "probe", side_effect=[3.0, 3.0, 3.0, 3.0, 12.0]), \
                 patch.object(module, "trim_edge_silence", side_effect=fake_trim), \
                 patch.object(module.subprocess, "run", side_effect=fake_run):
                report = module.prepare_batch(batch_path, inventory_path, root / "out", target_count=1)

            item = report["items"][0]
            self.assertEqual(item["selected_verses"], [1, 2, 3, 4])
            self.assertEqual(item["duration_seconds"], 12.0)
            self.assertEqual(report["minimum_seconds"], 0.0)
            self.assertEqual(report["maximum_seconds"], 40.0)

    def test_defers_a_single_ayah_that_exceeds_40_seconds_without_truncating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = {
                "batch_status": "review_candidates_only",
                "rendering_allowed": False,
                "auto_publish": False,
                "passages": [{"candidate_id": "long-ayah", "surah_number": 2, "verses": [{"ayah": 1}]}],
            }
            inventory = {"mapped_verse_count": 6236, "verses": {"2:1": "manifest/10-002001-A08.mp3"}}
            batch_path, inventory_path = root / "batch.json", root / "inventory.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

            def fake_run(command, **kwargs):
                Path(command[-1]).write_bytes(b"combined")
                return None

            def fake_trim(source, destination, source_duration):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"trimmed")
                return 66.0

            with (
                patch.object(module, "RemoteZip", return_value=FakeArchive()),
                patch.object(module, "probe", side_effect=[66.0, 66.0]),
                patch.object(module, "trim_edge_silence", side_effect=fake_trim),
                patch.object(module.subprocess, "run", side_effect=fake_run),
            ):
                report = module.prepare_batch(batch_path, inventory_path, root / "out", target_count=1)

            item = report["items"][0]
            self.assertEqual(item["status"], "deferred_single_ayah_exceeds_40_seconds")
            self.assertEqual(item["selected_verses"], [])
            self.assertEqual(item["remaining_verses"], [1])
            self.assertFalse(item["passage_complete"])
            self.assertEqual(report["audio_prepared_count"], 0)
            self.assertEqual(report["maximum_seconds"], 40.0)

    def test_trim_edge_silence_keeps_mp3_and_preserves_the_recitation_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.mp3"
            destination = root / "trimmed.mp3"
            module.subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=0.8",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=1.0",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1.0",
                "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-q:a", "2", str(source)
            ], check=True)
            original_duration = module.probe(source)
            trimmed_duration = module.trim_edge_silence(source, destination, original_duration)
            codec = module.subprocess.check_output([
                "ffprobe", "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1",
                str(destination)
            ], text=True).strip()
            self.assertEqual(codec, "mp3")
            self.assertLess(trimmed_duration, original_duration - 1.0)
            self.assertGreater(trimmed_duration, 1.0)
            check = module.subprocess.run([
                "ffmpeg", "-hide_banner", "-i", str(destination),
                "-af", "silencedetect=noise=-50dB:d=0.25", "-f", "null", "-"
            ], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0)
            self.assertNotIn("silence_start: 0", check.stderr)
            self.assertNotIn("silence_end:", check.stderr)

    def test_rejects_non_review_only_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_path, inventory_path = root / "batch.json", root / "inventory.json"
            batch_path.write_text(json.dumps({"batch_status": "approved", "rendering_allowed": True}))
            inventory_path.write_text(json.dumps({"mapped_verse_count": 6236, "verses": {}}))
            with self.assertRaisesRegex(ValueError, "review-only"):
                module.prepare_batch(batch_path, inventory_path, root / "out")


if __name__ == "__main__":
    unittest.main()
