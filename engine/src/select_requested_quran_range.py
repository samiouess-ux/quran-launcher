"""Choose the longest opening contiguous Quran passage that fits 40 seconds.

Used only when a Telegram user asks for a surah without specifying ayahs.
It probes the exact official archive files; it never trims or alters audio.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from remotezip import RemoteZip
from prepare_quran_review_batch_audio import DEFAULT_ARCHIVE

# Every Quran video, including manual Telegram requests, has the same hard 40-second maximum.
MAX_SECONDS = 40.0
from parse_telegram_quran_request import SURAH_AYAH_COUNTS


def probe(path: Path) -> float:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ], text=True).strip()
    duration = float(raw)
    if duration <= 0:
        raise ValueError(f"Invalid audio duration: {path}")
    return duration


def choose_range_from_durations(
    surah: int, start_ayah: int, durations: dict[int, float],
    max_ayahs: int = 10, max_seconds: float = MAX_SECONDS,
) -> dict:
    if not 1 <= surah <= 114 or not 1 <= start_ayah <= SURAH_AYAH_COUNTS[surah - 1]:
        raise ValueError("Invalid surah or starting ayah.")
    selected = []
    total = 0.0
    last = min(SURAH_AYAH_COUNTS[surah - 1], start_ayah + max_ayahs - 1)
    for ayah in range(start_ayah, last + 1):
        duration = durations.get(ayah)
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"Missing or invalid probed duration for ayah {surah}:{ayah}.")
        if total + duration > max_seconds:
            if not selected:
                raise ValueError(f"The first ayah {surah}:{ayah} alone exceeds {max_seconds:g} seconds.")
            break
        selected.append(ayah)
        total += duration
    if not selected:
        raise ValueError("No complete ayah fits the video duration limit.")
    return {
        "surah_number": surah,
        "start_ayah": selected[0],
        "end_ayah": selected[-1],
        "selected_ayahs": selected,
        "duration_seconds": round(total, 3),
        "selection_policy": "longest_opening_contiguous_whole_ayah_range_up_to_10_and_40_seconds",
    }


def select_from_archive(inventory: dict, surah: int, start_ayah: int = 1) -> dict:
    if inventory.get("mapped_verse_count") != 6236 or not isinstance(inventory.get("verses"), dict):
        raise ValueError("Complete official audio inventory is required.")
    members = inventory["verses"]
    durations = {}
    upper = min(SURAH_AYAH_COUNTS[surah - 1], start_ayah + 9)
    with tempfile.TemporaryDirectory(prefix="quran-request-probe-") as temporary:
        temp = Path(temporary)
        with RemoteZip(inventory.get("source_url", DEFAULT_ARCHIVE)) as archive:
            for ayah in range(start_ayah, upper + 1):
                member = members.get(f"{surah}:{ayah}")
                if not member:
                    raise ValueError(f"Official audio mapping missing for {surah}:{ayah}.")
                target = temp / f"{surah:03d}_{ayah:03d}.mp3"
                with archive.open(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
                durations[ayah] = probe(target)
                # Stop as soon as the next complete ayah would exceed 40 sec.
                if sum(durations.values()) > MAX_SECONDS:
                    break
    return choose_range_from_durations(surah, start_ayah, durations)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--surah", type=int, required=True)
    parser.add_argument("--start-ayah", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("output/quran_requested_range.json"))
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    result = select_from_archive(inventory, args.surah, args.start_ayah)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
