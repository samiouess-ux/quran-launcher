"""Regression tests for the manifest-based Maher Al-Muaiqly audio inventory."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_official_audio_inventory import (
    ARCHIVE_URL, MIRROR_ARCHIVE_URL, EXPECTED_ARCHIVE_SHA256,
    ENTRY_RE, create_archive_session, preflight_archive, select_archive_url,
    fetch_archive_metadata, inventory_from_metadata,
)


def sample_metadata():
    counts = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
    files = []
    for surah, count in enumerate(counts, 1):
        for ayah in range(1, count + 1):
            files.append({"path": f"ayat-12-1-2020/{surah:03d}/10-{surah:03d}{ayah:03d}-A08.mp3"})
    return {
        "slug": "ayat-12-1-2020",
        "download": {"url_cdn": MIRROR_ARCHIVE_URL},
        "checksums": {"computed": {"sha256": EXPECTED_ARCHIVE_SHA256}},
        "available": True,
        "archive_extracted": True,
        "files": files,
    }


class OfficialAudioInventoryTests(unittest.TestCase):
    def test_archive_filename_mapping_pattern(self):
        match = ENTRY_RE.search("ayat-12-1-2020/010/10-011001-A08.mp3")
        self.assertIsNotNone(match)
        self.assertEqual(match.groups(), ("011", "001"))

    def test_preflight_requires_successful_byte_range_response(self):
        session = Mock()
        response = Mock(status_code=206)
        response.headers = {"Content-Range": "bytes 0-0/760867237"}
        session.get.return_value = response
        preflight_archive(session)
        session.get.assert_called_once()
        self.assertEqual(session.get.call_args.kwargs["headers"], {"Range": "bytes=0-0"})
        response.raise_for_status.assert_called_once()
        response.close.assert_called_once()

    def test_preflight_rejects_endpoint_that_ignores_byte_range(self):
        session = Mock()
        response = Mock(status_code=200)
        response.headers = {}
        session.get.return_value = response
        self.assertFalse(preflight_archive(session))
        response.close.assert_called_once()

    def test_preflight_fails_closed_on_http_503(self):
        session = Mock()
        response = Mock(status_code=503)
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "503 Server Error", response=response
        )
        session.get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
            preflight_archive(session)
        response.close.assert_called_once()

    def test_select_archive_url_uses_pinned_mirror_only_after_official_outage(self):
        session = Mock()
        with patch("build_official_audio_inventory.preflight_archive") as check:
            check.side_effect = [RuntimeError("official HTTP 503"), False]
            self.assertEqual(select_archive_url(session), (MIRROR_ARCHIVE_URL, False))

    def test_select_archive_url_prefers_official_host(self):
        session = Mock()
        with patch("build_official_audio_inventory.preflight_archive") as check:
            check.return_value = True
            self.assertEqual(select_archive_url(session), (ARCHIVE_URL, True))
            check.assert_called_once_with(session, ARCHIVE_URL)

    def test_manifest_builds_complete_exact_verse_mapping_without_archive_download(self):
        inventory = inventory_from_metadata(sample_metadata(), MIRROR_ARCHIVE_URL)
        self.assertEqual(inventory["mapped_verse_count"], 6236)
        self.assertEqual(inventory["verses"]["1:1"], "ayat-12-1-2020/001/10-001001-A08.mp3")
        self.assertEqual(inventory["verses"]["86:1"], "ayat-12-1-2020/086/10-086001-A08.mp3")
        self.assertIn("crc_checked_on_download", inventory["archive_integrity_status"])

    def test_manifest_rejects_changed_published_checksum(self):
        session = Mock()
        response = Mock()
        response.json.return_value = sample_metadata()
        response.json.return_value["checksums"]["computed"]["sha256"] = "0" * 64
        session.get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "SHA-256 changed"):
            fetch_archive_metadata(session)

    def test_manifest_rejects_missing_ayah(self):
        metadata = sample_metadata()
        metadata["files"].pop()
        with self.assertRaisesRegex(RuntimeError, "did not validate"):
            inventory_from_metadata(metadata, MIRROR_ARCHIVE_URL)

    def test_archive_session_retries_transient_http_failures(self):
        session = create_archive_session()
        try:
            retry = session.get_adapter("https://").max_retries
            self.assertEqual(retry.total, 2)
            self.assertIn(503, retry.status_forcelist)
            self.assertFalse(retry.respect_retry_after_header)
            self.assertIn("GET", retry.allowed_methods)
            self.assertIn("HEAD", retry.allowed_methods)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
