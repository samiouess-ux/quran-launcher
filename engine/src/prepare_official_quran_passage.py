"""Prepare contiguous, duration-checked verse audio from the official Hafs archive.

The archive inventory is a filename map only. This tool downloads exact verse
files, probes their real durations, and never trims, speeds up, or reorders them.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from remotezip import RemoteZip

ARCHIVE_URL = "https://download.qurancomplex.gov.sa/new-sounds/muaiqly-08/hafs/ayat-12-1-2020.zip"
TARGET_SECONDS = 60.0
MAX_SECONDS = 65.0


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise ValueError(f"Cannot read audio duration for {path}") from exc
    if duration <= 0:
        raise ValueError(f"Invalid audio duration for {path}: {duration}")
    return duration


def choose_contiguous_passage(durations: dict[int, float], start_ayah: int,
                              target: float = TARGET_SECONDS,
                              maximum: float = MAX_SECONDS) -> list[int]:
    """Choose consecutive complete ayahs, preferring target without crossing cap."""
    if start_ayah not in durations:
        raise ValueError(f"Missing duration for starting ayah {start_ayah}")
    selected: list[int] = []
    total = 0.0
    ayah = start_ayah
    while ayah in durations:
        duration = durations[ayah]
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"Invalid duration for ayah {ayah}")
        if duration > maximum:
            if not selected:
                raise ValueError(f"Ayah {ayah} alone exceeds the {maximum:.0f}s maximum")
            break
        if total + duration > maximum:
            break
        if selected and total >= target:
            break
        selected.append(ayah)
        total += float(duration)
        ayah += 1
    if not selected:
        raise ValueError("No complete ayah fits the duration limits")
    return selected


def prepare_passage(inventory_path: Path, surah: int, start_ayah: int,
                    output_dir: Path) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory.get("mapped_verse_count") != 6236 or inventory.get("expected_verse_count") != 6236:
        raise ValueError("Official audio inventory is not a complete 6,236-verse mapping")
    verses = inventory.get("verses", {})
    if not isinstance(verses, dict):
        raise ValueError("Inventory verses must be an object")
    output_dir.mkdir(parents=True, exist_ok=True)
    durations: dict[int, float] = {}
    downloaded: dict[int, Path] = {}
    # Probe forward until target/cap is reached. At most a small number of
    # adjacent files are downloaded; no entire archive extraction is needed.
    with RemoteZip(inventory.get("source_url", ARCHIVE_URL)) as archive:
        ayah = start_ayah
        total = 0.0
        while f"{surah}:{ayah}" in verses:
            member = verses[f"{surah}:{ayah}"]
            destination = output_dir / f"{surah:03d}_{ayah:03d}.mp3"
            with archive.open(member) as source, destination.open("wb") as target_file:
                shutil.copyfileobj(source, target_file)
            duration = probe_duration(destination)
            if duration > MAX_SECONDS:
                if ayah == start_ayah:
                    raise ValueError(f"Ayah {ayah} alone exceeds {MAX_SECONDS:.0f}s")
                destination.unlink(missing_ok=True)
                break
            if total + duration > MAX_SECONDS:
                destination.unlink(missing_ok=True)
                break
            durations[ayah] = duration
            downloaded[ayah] = destination
            total += duration
            ayah += 1
            if total >= TARGET_SECONDS:
                break
    selected = choose_contiguous_passage(durations, start_ayah)
    selected_total = sum(durations[n] for n in selected)
    # Remove any downloaded look-ahead file not in the selected range.
    for number, path in downloaded.items():
        if number not in selected:
            path.unlink(missing_ok=True)
    return {
        "surah": surah,
        "verses": selected,
        "duration_seconds": round(selected_total, 3),
        "target_seconds": TARGET_SECONDS,
        "maximum_seconds": MAX_SECONDS,
        "audio_files": [str(downloaded[n]) for n in selected],
        "source": inventory.get("source_url", ARCHIVE_URL),
        "recitation": inventory.get("recitation"),
        "status": "audio_downloaded_duration_probed_requires_text_translation_rights_and_user_review",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--surah", required=True, type=int)
    parser.add_argument("--start-ayah", required=True, type=int)
    parser.add_argument("--output-dir", default="output/quran_passage", type=Path)
    parser.add_argument("--report", default="output/quran_passage.json", type=Path)
    args = parser.parse_args()
    report = prepare_passage(args.inventory, args.surah, args.start_ayah, args.output_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
