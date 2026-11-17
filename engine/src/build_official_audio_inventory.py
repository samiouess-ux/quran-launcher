"""Build the Maher Al-Muaiqly verse map from the pinned manifest without a full ZIP download.

The archive's published SHA-256 is pinned in the upstream metadata. We enumerate
its extracted file manifest, then RemoteZip fetches only selected ZIP members;
zipfile verifies each downloaded member's CRC before it is used.
"""
from __future__ import annotations

import json
import re
import sys
import hashlib
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ARCHIVE_URL = "https://download.qurancomplex.gov.sa/new-sounds/muaiqly-08/hafs/ayat-12-1-2020.zip"
MIRROR_ARCHIVE_URL = "https://cdn.quran.ws/KFGQPC/resources/quran-audios/ayat-12-1-2020/ayat-12-1-2020.zip"
METADATA_URL = "https://raw.githubusercontent.com/quran-ws/kfgqpc-resources/main/resources/quran-audios/ayat-12-1-2020/metadata.json"
EXPECTED_ARCHIVE_SHA256 = "3edcc70407f9d19c972c002c69a43cc245a62a0fcc497d3c719406a69965e18e"
EXPECTED_VERSES = 6236
EXPECTED_ARCHIVE_BYTES = 760867237
ENTRY_RE = re.compile(r"(?:^|/)10-(\d{3})(\d{3})-A08\.mp3$", re.IGNORECASE)


def create_archive_session() -> requests.Session:
    """Use bounded retries for archive and metadata requests."""
    retry = Retry(
        total=2, connect=2, read=2, status=2, backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=2)
    session = requests.Session()
    session.headers.update({"User-Agent": "IslamicTikTokAutomation/1.0"})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def preflight_archive(session: requests.Session, url: str = ARCHIVE_URL) -> bool:
    """Require real HTTP byte-range support before selecting an archive for RemoteZip."""
    response = None
    try:
        response = session.get(
            url, headers={"Range": "bytes=0-0"}, stream=True,
            allow_redirects=True, timeout=(10, 15),
        )
        response.raise_for_status()
        content_range = response.headers.get("Content-Range", "")
        if response.status_code == 206 and content_range.startswith("bytes 0-0/"):
            return True
        if response.status_code == 200:
            print("Archive endpoint ignores byte ranges; use bounded full-download with published SHA-256 verification.")
            return False
        raise RuntimeError(
            f"Unexpected archive range preflight response "
            f"(HTTP {response.status_code}, Content-Range={content_range or 'missing'})."
        )
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        detail = f" (HTTP {status})" if status is not None else ""
        raise RuntimeError(f"Quran archive unavailable during range preflight{detail}.") from exc
    finally:
        if response is not None:
            response.close()


def select_archive_url(session: requests.Session) -> tuple[str, bool]:
    """Prefer the Complex host; use its checksum-pinned mirror on outage."""
    try:
        supports_ranges = preflight_archive(session, ARCHIVE_URL)
        return ARCHIVE_URL, supports_ranges
    except RuntimeError as official_error:
        print(f"Official archive host unavailable: {official_error}")
        supports_ranges = preflight_archive(session, MIRROR_ARCHIVE_URL)
        print("Using the documented byte-for-byte KFGQPC archive mirror.")
        return MIRROR_ARCHIVE_URL, supports_ranges


def download_verified_archive(session: requests.Session, url: str, destination: Path) -> str:
    """Download the complete archive only when range requests are unavailable; verify size and SHA-256."""
    digest = hashlib.sha256()
    total = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with session.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            with destination.open("wb") as output:
                for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > EXPECTED_ARCHIVE_BYTES:
                        raise RuntimeError("Quran archive exceeded its pinned expected byte size.")
                    digest.update(chunk)
                    output.write(chunk)
                    if total % (64 * 1024 * 1024) < len(chunk):
                        print(f"Downloaded {total // (1024 * 1024)} MiB of Quran audio archive.")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    actual = digest.hexdigest()
    if total != EXPECTED_ARCHIVE_BYTES or actual != EXPECTED_ARCHIVE_SHA256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Full Quran archive verification failed: bytes={total}, sha256={actual}.")
    print(f"Full archive verified: {total} bytes; SHA-256 matches the published KFGQPC checksum.")
    return str(destination)


def fetch_archive_metadata(session: requests.Session) -> dict:
    """Fetch and validate the mirror's extracted-file manifest and pinned ZIP digest."""
    response = session.get(METADATA_URL, timeout=(10, 30))
    response.raise_for_status()
    metadata = response.json()
    if not isinstance(metadata, dict):
        raise RuntimeError("Quran audio metadata is not a JSON object.")
    checksum = metadata.get("checksums", {}).get("computed", {}).get("sha256")
    if metadata.get("slug") != "ayat-12-1-2020":
        raise RuntimeError("Unexpected Quran audio metadata resource.")
    if metadata.get("download", {}).get("url_cdn") != MIRROR_ARCHIVE_URL:
        raise RuntimeError("Metadata archive URL does not match the pinned mirror.")
    if checksum != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(
            f"Published archive SHA-256 changed: expected {EXPECTED_ARCHIVE_SHA256}, got {checksum}."
        )
    if metadata.get("available") is not True or metadata.get("archive_extracted") is not True:
        raise RuntimeError("The upstream archive manifest is not marked available and extracted.")
    files = metadata.get("files")
    if not isinstance(files, list) or not files:
        raise RuntimeError("The upstream archive manifest has no file list.")
    return metadata


def inventory_from_metadata(metadata: dict, archive_url: str, archive_path: str | None = None) -> dict:
    """Map all canonical verse members from the upstream extracted ZIP manifest."""
    mapped: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}
    unmatched: list[str] = []
    for item in metadata["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeError("Malformed entry in Quran audio metadata file list.")
        name = item["path"]
        match = ENTRY_RE.search(name)
        if not match:
            continue
        surah, ayah = map(int, match.groups())
        if not (1 <= surah <= 114 and 1 <= ayah <= 286):
            unmatched.append(name)
            continue
        key = f"{surah}:{ayah}"
        if key in mapped:
            duplicates.setdefault(key, [mapped[key]]).append(name)
        else:
            mapped[key] = name

    counts = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
    if len(counts) != 114:
        raise RuntimeError("Internal surah verse-count table is invalid.")
    missing = [
        f"{surah}:{ayah}"
        for surah, count in enumerate(counts, 1)
        for ayah in range(1, count + 1)
        if f"{surah}:{ayah}" not in mapped
    ]
    if duplicates or missing or len(mapped) != EXPECTED_VERSES:
        raise RuntimeError(
            "Quran audio manifest did not validate: "
            f"mapped={len(mapped)}, missing={len(missing)}, duplicates={len(duplicates)}."
        )

    return {
        "source_url": archive_url,
        "archive_path": archive_path,
        "official_source_url": ARCHIVE_URL,
        "metadata_url": METADATA_URL,
        "expected_official_sha256": EXPECTED_ARCHIVE_SHA256,
        "archive_integrity_status": "published_archive_sha256_pinned; selected_zip_members_crc_checked_on_download",
        "recitation": "Hafs",
        "reciter_internal": "Maher Al-Muaiqly",
        "mapping_status": "complete_upstream_archive_manifest_requires_selected_member_crc_and_human_audio_review",
        "expected_verse_count": EXPECTED_VERSES,
        "mapped_verse_count": len(mapped),
        "verses": dict(sorted(mapped.items(), key=lambda item: tuple(map(int, item[0].split(":"))))),
    }


def verify_cached_archive(path: Path) -> str | None:
    """Reuse a cached archive only when its exact size and pinned SHA-256 match."""
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as source:
        while chunk := source.read(8 * 1024 * 1024):
            total += len(chunk)
            digest.update(chunk)
    if total != EXPECTED_ARCHIVE_BYTES or digest.hexdigest() != EXPECTED_ARCHIVE_SHA256:
        path.unlink(missing_ok=True)
        print("Cached Quran audio archive failed its pinned size/SHA-256 check; it will be downloaded again.")
        return None
    print(f"Reusing checksum-verified cached Quran audio archive: {path}")
    return str(path)


def build_inventory(archive_destination: Path | None = None) -> dict:
    session = create_archive_session()
    try:
        archive_url, supports_ranges = select_archive_url(session)
        metadata = fetch_archive_metadata(session)
        archive_destination = archive_destination or Path("output/kfgqpc_maher_verified.zip")
        archive_path = verify_cached_archive(archive_destination)
        if archive_path is None and not supports_ranges:
            archive_path = download_verified_archive(session, archive_url, archive_destination)
        return inventory_from_metadata(metadata, archive_url, archive_path)
    finally:
        session.close()


if __name__ == "__main__":
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "output/official_verse_audio_inventory.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(destination.parent / 'kfgqpc_maher_verified.zip')
    destination.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Validated metadata mapping for {inventory['mapped_verse_count']} verses. "
        "Only selected audio members will be range-downloaded and CRC-checked."
    )
