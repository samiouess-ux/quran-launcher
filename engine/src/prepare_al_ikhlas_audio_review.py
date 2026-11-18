"""Extract the complete Al-Ikhlas 112:1-4 Maher Al-Muaiqly Hafs audio for private review.

This is an audio-only review artifact. It does not render a video, approve the
recording, send Telegram messages, or publish anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile

from remotezip import RemoteZip

EXPECTED_ARCHIVE_SHA256 = "3edcc70407f9d19c972c002c69a43cc245a62a0fcc497d3c719406a69965e18e"
SURAH = 112
AYAHS = (1, 2, 3, 4)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_duration(path: Path) -> float:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip()
    duration = float(raw)
    if duration <= 0:
        raise ValueError(f"Invalid audio duration for {path}: {duration}")
    return round(duration, 3)


@contextmanager
def open_verified_archive(inventory: dict):
    if inventory.get("expected_official_sha256") != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Official audio archive checksum does not match the pinned Maher Hafs archive.")
    local_path = inventory.get("archive_path")
    if local_path:
        path = Path(local_path)
        if not path.is_file() or sha256_file(path) != EXPECTED_ARCHIVE_SHA256:
            raise ValueError("Cached official audio archive is missing or failed SHA-256 verification.")
        with ZipFile(path) as archive:
            yield archive
        return
    source_url = inventory.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("Official audio archive URL is missing or invalid.")
    with RemoteZip(source_url) as archive:
        yield archive


def resolve_member(archive_names: list[str], requested: str) -> str:
    basename = requested.rsplit("/", 1)[-1].casefold()
    matches = [
        name for name in archive_names
        if name.rsplit("/", 1)[-1].casefold() == basename
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one official ZIP member for {basename}; found {len(matches)}."
        )
    return matches[0]


def prepare_audio_review(inventory: dict, output_dir: Path) -> dict:
    if inventory.get("mapped_verse_count") != 6236 or inventory.get("expected_verse_count") != 6236:
        raise ValueError("A complete 6,236-ayah official Hafs inventory is required.")
    if inventory.get("recitation") != "Hafs" or inventory.get("reciter_internal") != "Maher Al-Muaiqly":
        raise ValueError("Audio inventory is not the expected Maher Al-Muaiqly Hafs collection.")
    verse_map = inventory.get("verses")
    if not isinstance(verse_map, dict):
        raise ValueError("Official audio inventory has no verse mapping.")
    requested_members: dict[int, str] = {}
    for ayah in AYAHS:
        reference = f"{SURAH}:{ayah}"
        requested = verse_map.get(reference)
        if not isinstance(requested, str) or not requested:
            raise ValueError(f"Official Maher Hafs inventory is missing {reference}.")
        requested_members[ayah] = requested

    output_dir.mkdir(parents=True, exist_ok=True)
    durations: dict[str, float] = {}
    hashes: dict[str, str] = {}
    members: dict[str, str] = {}
    audio_files: list[Path] = []

    with open_verified_archive(inventory) as archive:
        names = archive.namelist()
        for ayah in AYAHS:
            member = resolve_member(names, requested_members[ayah])
            destination = output_dir / f"al_ikhlas_112_{ayah:02d}.mp3"
            with archive.open(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
            # Reading each member to EOF makes zipfile/RemoteZip validate its CRC.
            duration = probe_duration(destination)
            durations[str(ayah)] = duration
            hashes[str(ayah)] = sha256_file(destination)
            members[str(ayah)] = member
            audio_files.append(destination)

    concat_list = output_dir / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{path.resolve().as_posix()}'\n" for path in audio_files),
        encoding="utf-8",
    )
    combined = output_dir / "al_ikhlas_112_1_4_maher_hafs_review.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-map", "0:a:0", "-c:a", "copy", str(combined),
    ], check=True)
    combined_duration = probe_duration(combined)

    report = {
        "status": "audio_extracted_for_user_review_only",
        "surah_number": SURAH,
        "surah_name_ar": "سورة الإخلاص",
        "surah_name_en": "Al-Ikhlas",
        "verses": list(AYAHS),
        "reciter": "Maher Al-Muaiqly",
        "riwaya": "Hafs",
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "archive_members": members,
        "verse_durations_seconds": durations,
        "verse_sha256": hashes,
        "combined_audio_file": str(combined),
        "combined_audio_duration_seconds": combined_duration,
        "processing": "original_mp3_frames_concatenated_in_order; no speed_change; no verse_cut; no added_inter_verse_silence",
        "audio_approved": False,
        "exact_recording_user_reviewed": False,
        "rendering_allowed": False,
        "telegram_sent": False,
        "tiktok_published": False,
        "manual_audio_review_required": True,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("output/al_ikhlas_audio_review"), type=Path)
    parser.add_argument("--report", default=Path("output/al_ikhlas_audio_review/report.json"), type=Path)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    report = prepare_audio_review(inventory, args.output_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
