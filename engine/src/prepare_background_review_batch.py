"""Build a separate visual review pack for unapproved Pexels background candidates."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
USER_AGENT = "IslamicTikTokAutomation/1.0 (background-review-only)"


def download(url: str, destination: Path) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as target:
        content_type = response.headers.get("Content-Type", "").lower()
        if "video" not in content_type and "octet-stream" not in content_type:
            raise RuntimeError(f"Unexpected video content type: {content_type}")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("Candidate exceeds the 100 MiB review-download limit.")
            target.write(chunk)
    if total == 0:
        raise RuntimeError("Downloaded candidate is empty.")
    return total


def inspect_video(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path)
    ], text=True)
    data = json.loads(raw)
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not stream or not stream.get("width") or not stream.get("height"):
        raise RuntimeError(f"No valid video stream: {path.name}")
    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError(f"Invalid duration: {path.name}")
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration_seconds": round(duration, 3),
        "video_codec": stream.get("codec_name"),
    }


def make_crop(video: Path, image: Path, duration: float) -> None:
    timestamp = max(0.1, duration / 2)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(timestamp), "-i", str(video), "-frames:v", "1",
        "-vf", "scale=540:960:force_original_aspect_ratio=increase,crop=540:960",
        "-q:v", "2", str(image)
    ], check=True, capture_output=True, text=True)
    with Image.open(image) as result:
        if result.size != (540, 960):
            raise RuntimeError(f"Unexpected crop dimensions for {image.name}: {result.size}")


def contact_sheet(items: list[dict], destination: Path) -> None:
    columns, tile_w, tile_h = 3, 540, 960
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_w, rows * tile_h), (12, 18, 24))
    draw = ImageDraw.Draw(sheet)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title_font = ImageFont.truetype(font_path, 21)
    detail_font = ImageFont.truetype(font_path, 15)
    for index, item in enumerate(items):
        x, y = (index % columns) * tile_w, (index // columns) * tile_h
        with Image.open(item["preview_path"]) as crop:
            sheet.paste(crop.convert("RGB"), (x, y))
        draw.rectangle((x, y, x + tile_w, y + 78), fill=(0, 0, 0))
        draw.text((x + 14, y + 10), item["description"][:43], font=title_font, fill="white")
        details = f'{item["width"]}x{item["height"]} | {item["duration_seconds"]}s | NOT APPROVED'
        draw.text((x + 14, y + 45), details, font=detail_font, fill=(245, 215, 160))
    sheet.save(destination, quality=91)


def prepare(catalog_path: Path, output_dir: Path) -> dict:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    candidates = catalog.get("candidates", [])
    if not candidates:
        raise RuntimeError("Review batch is empty.")
    # Validate the entire manifest before creating output files or downloading anything.
    seen = set()
    for candidate in candidates:
        asset_id = candidate.get("id")
        if not isinstance(asset_id, str) or not asset_id or asset_id in seen:
            raise RuntimeError("Candidate IDs must be unique, non-empty strings.")
        seen.add(asset_id)
        if candidate.get("approved") is not False or candidate.get("user_approved") is not False:
            raise RuntimeError("This review-only batch must contain only explicitly unapproved candidates.")
        source_url = candidate.get("source_page_url", "")
        video_url = candidate.get("direct_video_url", "")
        if not source_url.startswith("https://www.pexels.com/video/"):
            raise RuntimeError(f"Untrusted source page for {asset_id}")
        if not video_url.startswith("https://videos.pexels.com/video-files/"):
            raise RuntimeError(f"Untrusted direct video URL for {asset_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for candidate in candidates:
        asset_id = candidate["id"]
        source_url = candidate["source_page_url"]
        video_url = candidate["direct_video_url"]
        video = output_dir / f"{asset_id}.mp4"
        crop = output_dir / f"{asset_id}_vertical_crop.jpg"
        byte_count = download(video_url, video)
        metadata = inspect_video(video)
        make_crop(video, crop, metadata["duration_seconds"])
        items.append({
            "id": asset_id,
            "category": candidate.get("category", "uncategorized"),
            "description": candidate.get("description", asset_id),
            "creator": candidate.get("creator", "unknown"),
            "source_page_url": source_url,
            "page_license": candidate.get("page_license", "recheck required"),
            "download_bytes": byte_count,
            "preview_path": str(crop),
            **metadata,
            "download_probe_verified": True,
            "approved": False,
            "user_approved": False,
            "production_enabled": False,
        })
    sheet = output_dir / "background_candidates_contact_sheet.jpg"
    contact_sheet(items, sheet)
    report = {
        "status": "downloaded_and_probe_verified_waiting_for_user_visual_review",
        "candidate_count": len(items),
        "contact_sheet": str(sheet),
        "production_enabled": False,
        "telegram_delivery": False,
        "auto_publish": False,
        "user_approval_required": True,
        "items": [{key: value for key, value in item.items() if key != "preview_path"} for item in items],
    }
    (output_dir / "background_review_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared {len(items)} unapproved background candidates for visual review.")
    print("No production catalog or Telegram delivery was changed.")
    return report


if __name__ == "__main__":
    prepare(Path("data/background_review_candidates_batch_01.json"),
            Path("output/background_review_batch_01"))
