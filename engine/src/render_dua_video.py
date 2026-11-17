"""Separate, fail-closed renderer for sourced dua/dhikr review videos."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, features

from validate_content_manifest import validate_content_manifest


WIDTH, HEIGHT, FPS = 1080, 1920, 30
AUDIO_DURATION_TOLERANCE_SECONDS = 0.75
TARGET_MAX_DURATION_SECONDS = 60.0
HARD_MAX_DURATION_SECONDS = 65.0


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe_duration(path: Path) -> float:
    """Read the actual media duration; fail rather than silently pad or trim."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise SystemExit(f"Unable to read media duration: {path}") from exc
    if duration <= 0:
        raise SystemExit(f"Media has an invalid duration: {path}")
    return duration


def validate_audio_duration(path: Path, expected: float,
                            tolerance: float = AUDIO_DURATION_TOLERANCE_SECONDS) -> float:
    actual = probe_duration(path)
    difference = abs(actual - expected)
    if difference > tolerance:
        raise SystemExit(
            f"Audio duration mismatch: expected {expected:.3f}s, got {actual:.3f}s "
            f"(difference {difference:.3f}s; allowed {tolerance:.2f}s). "
            "Refusing to pad or truncate audio automatically."
        )
    return actual


def item_duration(item: dict) -> float:
    value = item.get("duration_seconds")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise SystemExit("Every item needs a positive duration_seconds; timings are never guessed.")
    return float(value)


def create_overlay(title: str, item: dict, destination: Path) -> None:
    """Render exactly one sourced Arabic item; never combine multiple items."""
    if not features.check("raqm"):
        raise SystemExit("Arabic rendering blocked: Pillow libraqm/RAQM is unavailable.")
    try:
        font_path = subprocess.check_output(
            ["fc-match", "-f", "%{file}", "Amiri:style=Bold"], text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit("Unable to locate Amiri Bold font.") from exc
    if not font_path or not Path(font_path).is_file():
        raise SystemExit("Required Arabic font is missing.")
    text = item.get("arabic")
    source = item.get("source_name")
    if not isinstance(text, str) or not text.strip() or not source:
        raise SystemExit("Each screen needs exact Arabic text and its named source.")

    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    gold, faint = (231, 190, 103, 255), (231, 190, 103, 115)
    outer = [(540,392),(575,410),(785,410),(815,430),(845,475),(815,520),
             (785,540),(575,540),(540,558),(505,540),(295,540),(265,520),
             (235,475),(265,430),(295,410),(505,410)]
    inner = [(540,405),(568,420),(780,420),(802,437),(829,475),(802,513),
             (780,530),(568,530),(540,545),(512,530),(300,530),(278,513),
             (251,475),(278,437),(300,420),(512,420)]
    draw.line(outer + [outer[0]], fill=gold, width=4, joint="curve")
    draw.line(inner + [inner[0]], fill=faint, width=2, joint="curve")
    title_font = ImageFont.truetype(font_path, 58)
    draw.text((540, 475), title, font=title_font, fill=gold, anchor="mm",
              direction="rtl", language="ar")

    font_size = 64
    while font_size >= 42:
        font = ImageFont.truetype(font_path, font_size)
        lines, current = [], ""
        for word in text.split():
            candidate = (current + " " + word).strip()
            width = draw.textbbox((0, 0), candidate, font=font,
                                  direction="rtl", language="ar")[2]
            if width <= 900:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = int(font_size * 1.65)
        if len(lines) <= 8 and len(lines) * line_height <= 760:
            break
        font_size -= 4
    else:
        raise SystemExit("This sourced item is too long for the approved layout.")
    start_y = 930 - (len(lines) - 1) * line_height / 2
    for index, line in enumerate(lines):
        draw.text((540, start_y + index * line_height), line, font=font,
                  fill=(255, 255, 255, 255), anchor="mm",
                  direction="rtl", language="ar")
    source_font = ImageFont.truetype(font_path, 27)
    draw.text((540, 1450), str(source), font=source_font, fill=gold,
              anchor="mm", direction="rtl", language="ar")
    image.save(destination)


def build_slideshow(items: list[dict], title: str, work: Path) -> float:
    if not items:
        raise SystemExit("No sourced dua/dhikr text.")
    total = sum(item_duration(item) for item in items)
    if total > HARD_MAX_DURATION_SECONDS:
        raise SystemExit(
            f"Video duration {total:.2f}s exceeds the hard limit "
            f"of {HARD_MAX_DURATION_SECONDS:.0f}s."
        )
    if total > TARGET_MAX_DURATION_SECONDS:
        print(
            f"Warning: video duration {total:.2f}s exceeds the "
            f"{TARGET_MAX_DURATION_SECONDS:.0f}s target."
        )
    lines = []
    for index, item in enumerate(items):
        duration = item_duration(item)
        overlay = work / f"item_{index:03d}.png"
        create_overlay(title, item, overlay)
        lines.extend([f"file '{overlay.resolve().as_posix()}'",
                      f"duration {duration:.3f}"])
    lines.append(f"file '{(work / f'item_{len(items)-1:03d}.png').resolve().as_posix()}'")
    playlist = work / "overlays.ffconcat"
    playlist.write_text("ffconcat version 1.0\n" + "\n".join(lines) + "\n",
                        encoding="utf-8")
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="output/dua-review.mp4")
    args = parser.parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    validate_content_manifest(data)
    if data.get("content_type") not in {"dua", "dhikr"}:
        raise SystemExit("This renderer accepts dua/dhikr manifests only.")
    visual, audio = data["visual"], data["audio"]
    bg = visual.get("approved_background_url") or visual.get("background_candidate", {}).get("direct_video_url")
    parsed = urlparse(bg or "")
    if parsed.scheme != "https" or not parsed.netloc:
        raise SystemExit("An approved HTTPS background URL is required.")
    if data.get("publishing", {}).get("auto_publish", False):
        raise SystemExit("Auto-publishing is disabled.")

    work = Path("build/dua")
    work.mkdir(parents=True, exist_ok=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    title = data.get("title_ar", "دعاء" if data["content_type"] == "dua" else "ذكر")
    duration = build_slideshow(data["items"], title, work)

    bg_file = work / "background.mp4"
    subprocess.run(["curl", "--fail", "--location", "--retry", "3",
                    "--proto", "=https", "--tlsv1.2", bg, "-o", str(bg_file)],
                   check=True)
    kind = audio["kind"]
    inputs = ["-stream_loop", "-1", "-i", str(bg_file)]
    if kind == "silent":
        inputs += ["-f", "lavfi", "-t", f"{duration:.3f}",
                   "-i", "anullsrc=r=44100:cl=stereo"]
    else:
        audio_file = Path(audio.get("production_audio_file", ""))
        if not audio_file.is_file():
            raise SystemExit("Approved spoken/ambient audio file is missing.")
        validate_audio_duration(audio_file, duration)
        inputs += ["-i", str(audio_file)]
    inputs += ["-f", "concat", "-safe", "0", "-i", str(work / "overlays.ffconcat")]
    graph = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
             "crop=1080:1920,setsar=1,fps=30,"
             "drawbox=x=55:y=380:w=970:h=1200:color=black@0.30:t=fill[v0];"
             "[v0][2:v]overlay=0:0:shortest=1[v]")
    # Durations control screen changes only; audio is checked as a whole, not synced per item.
    run(["ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", graph,
         "-map", "[v]", "-map", "1:a", "-t", f"{duration:.3f}",
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(output)])
    print(f"Rendered dua/dhikr review video: {output} ({duration:.2f}s)")


if __name__ == "__main__":
    main()
