"""Download staged background clips into a temporary review-only preview package."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


MAX_DOWNLOAD_BYTES = 1024 * 1024 * 1024  # 1 GiB per source clip; Pexels 4K/60fps files can exceed 100 MiB
USER_AGENT = "IslamicTikTokAutomation/1.0 (background-review-only)"


def download_candidate(url: str, destination: Path) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.pexels.com/", "Accept": "video/mp4,application/octet-stream,*/*"})
    total = 0
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as target:
        content_type = response.headers.get("Content-Type", "").lower()
        if "video" not in content_type and "octet-stream" not in content_type:
            raise RuntimeError(f"Unexpected content type for video download: {content_type}")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("Background candidate exceeds the 1 GiB review-download limit.")
            target.write(chunk)
    if total == 0:
        raise RuntimeError("Downloaded background candidate is empty.")
    return total


def resolve_pexels_direct_url(page_url: str) -> str:
    """Resolve the primary Pexels download for this page (not a related-video tile)."""
    video_id = page_url.rstrip("/").split("-")[-1]
    if not video_id.isdigit():
        raise RuntimeError(f"Could not read Pexels video ID from {page_url}")
    download_url = f"https://www.pexels.com/download/video/{video_id}/"
    req = urllib.request.Request(download_url, headers={
        "User-Agent": USER_AGENT,
        "Referer": page_url,
        "Accept": "video/mp4,application/octet-stream,*/*",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        final_url = response.geturl()
    if (final_url.startswith("https://videos.pexels.com/video-files/")
            and re.search(r"\.mp4(?:\?|$)", final_url)):
        return final_url
    raise RuntimeError(f"Pexels primary download did not redirect to an MP4: {final_url}")

def probe_video(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path)
    ], text=True)
    data = json.loads(raw)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video or not video.get("width") or not video.get("height"):
        raise RuntimeError(f"No valid video stream found in {path.name}")
    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError(f"Invalid duration in {path.name}")
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_seconds": round(duration, 3),
        "video_codec": video.get("codec_name"),
    }


def extract_vertical_crop(source: Path, destination: Path, duration: float) -> None:
    timestamp = max(0.1, duration / 2)
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(timestamp), "-i", str(source),
        "-frames:v", "1", "-vf",
        "scale=540:960:force_original_aspect_ratio=increase,crop=540:960",
        "-q:v", "2", str(destination)
    ], check=True, capture_output=True, text=True)
    with Image.open(destination) as image:
        if image.size != (540, 960):
            raise RuntimeError(f"Vertical crop has unexpected dimensions: {image.size}")


def build_contact_sheet(items: list[dict], output: Path) -> None:
    rows = (len(items) + 1) // 2
    sheet = Image.new("RGB", (1080, max(1, rows) * 960), (10, 16, 22))
    draw = ImageDraw.Draw(sheet)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title_font = ImageFont.truetype(font_path, 22)
    note_font = ImageFont.truetype(font_path, 16)
    for index, item in enumerate(items):
        x = (index % 2) * 540
        y = (index // 2) * 960
        with Image.open(item["preview_path"]) as image:
            sheet.paste(image.convert("RGB"), (x, y))
        draw.rectangle((x, y, x + 540, y + 86), fill=(0, 0, 0))
        draw.text((x + 16, y + 12), item["description"][:42], font=title_font, fill=(255, 255, 255))
        dims = f'{item["width"]}x{item["height"]}  |  {item["duration_seconds"]}s  |  center crop 9:16'
        draw.text((x + 16, y + 48), dims, font=note_font, fill=(238, 211, 153))
    sheet.save(output, quality=90)


def composite_overlay_preview(background_crop: Path, overlay_frame: Path, destination: Path) -> None:
    """Composite the real transparent Quran layout over a candidate crop for legibility review."""
    with Image.open(background_crop) as background, Image.open(overlay_frame) as overlay:
        base = background.convert("RGBA").resize((540, 960), Image.Resampling.LANCZOS)
        layer = overlay.convert("RGBA").resize((540, 960), Image.Resampling.LANCZOS)
        if layer.getbbox() is None:
            raise RuntimeError("Quran overlay frame is empty; refusing visual QA preview.")
        base.alpha_composite(layer)
        base.convert("RGB").save(destination, quality=92)


def prepare(catalog_path: Path, output_dir: Path, include_ids: set[str] | None = None) -> dict:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    candidates = catalog.get("candidates", [])
    if not candidates:
        raise RuntimeError("Background review catalog contains no candidates.")
    output_dir.mkdir(parents=True, exist_ok=True)
    items = []
    production_catalog_path = catalog_path.with_name("background_candidates.json")
    production_catalog = json.loads(production_catalog_path.read_text(encoding="utf-8")) if production_catalog_path.exists() else {"candidates": []}
    production_verified_ids = {
        item.get("id") for item in production_catalog.get("candidates", [])
        if item.get("download_verified") is True and item.get("user_approved") is True
    }
    selected_candidates = [candidate for candidate in candidates if include_ids is None or candidate.get("id") in include_ids]
    if include_ids is not None and {item.get("id") for item in selected_candidates} != include_ids:
        raise RuntimeError("One or more requested background IDs are missing from the catalog.")
    for candidate in selected_candidates:
        # Skip already-integrated candidates when reviewing the staged additions list.
        # An explicit include_ids list requests a fresh overlay preview.
        if include_ids is None and candidate.get("id") in production_verified_ids:
            continue
        if candidate.get("approved") and not candidate.get("user_approved"):
            raise RuntimeError("An approved background must carry explicit user approval.")
        if candidate.get("download_verified") and not candidate.get("user_approved"):
            raise RuntimeError("A previously verified download without user approval is not eligible.")
        url = candidate.get("direct_video_url") or ""
        video_path = output_dir / f'{candidate["id"]}.mp4'
        preview_path = output_dir / f'{candidate["id"]}_vertical_crop.jpg'
        try:
            if not url and candidate.get("source_page_url", "").startswith("https://www.pexels.com/video/"):
                url = resolve_pexels_direct_url(candidate["source_page_url"])
            if not url:
                items.append({
                    "id": candidate["id"],
                    "description": candidate["description"],
                    "creator": candidate.get("creator"),
                    "source_page_url": candidate["source_page_url"],
                    "download_probe_verified": False,
                    "production_enabled": False,
                    "user_approved": candidate.get("user_approved", False),
                    "review_status": "missing_direct_video_url",
                })
                continue
            if not url.startswith(("https://videos.pexels.com/video-files/", "https://cdn.pixabay.com/")):
                raise RuntimeError(f"Untrusted candidate media URL: {candidate.get('id')}")
            byte_count = download_candidate(url, video_path)
            metadata = probe_video(video_path)
            extract_vertical_crop(video_path, preview_path, metadata["duration_seconds"])
        except Exception as exc:
            # A failed resolver, probe or crop must not leave a misleading partial review package.
            video_path.unlink(missing_ok=True)
            preview_path.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to prepare review candidate {candidate['id']}: {exc}") from exc
        items.append({
            "id": candidate["id"],
            "description": candidate["description"],
            "creator": candidate["creator"],
            "source_page_url": candidate["source_page_url"],
            "direct_video_url": url,
            "license_note": candidate["license"],
            "download_bytes": byte_count,
            "preview_path": str(preview_path),
            **metadata,
            "download_probe_verified": True,
            "visual_approval": candidate.get("user_approved", False),
            "production_enabled": False,
            "user_approved": candidate.get("user_approved", False),
        })
    verified_items = [item for item in items if item.get("download_probe_verified")]
    contact_sheet = output_dir / "background_candidates_contact_sheet.jpg"
    if verified_items:
        build_contact_sheet(verified_items, contact_sheet)
    report = {
        "status": "downloaded_and_probe_verified_requires_user_visual_review" if verified_items else "source_candidates_registered_media_urls_pending",
        "source_candidate_count": len(items),
        "candidate_count": len(verified_items),
        "unresolved_count": len(items) - len(verified_items),
        "unresolved_candidates": [item["id"] for item in items if not item.get("download_probe_verified")],
        "contact_sheet": str(contact_sheet) if verified_items else None,
        "production_enabled": False,
        "user_approval_required": True,
        "items": [{k: v for k, v in item.items() if k != "preview_path"} for item in items],
    }
    (output_dir / "background_review_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/background_candidates.json")
    parser.add_argument("--output-dir", default="output/background_review")
    parser.add_argument("--overlay-frame", type=Path, help="Actual transparent Quran PNG frame from the current review render.")
    parser.add_argument("--include-id", action="append", dest="include_ids", help="Only prepare this candidate ID; may be repeated.")
    args = parser.parse_args()
    report = prepare(Path(args.catalog), Path(args.output_dir), set(args.include_ids) if args.include_ids else None)
    if args.overlay_frame:
        if not report["candidate_count"]:
            raise RuntimeError("Cannot composite Quran overlays: no candidates have verified downloadable media URLs.")
        if not args.overlay_frame.is_file():
            raise FileNotFoundError(f"Actual Quran overlay frame not found: {args.overlay_frame}")
        overlaid_items = []
        for item in report["items"]:
            if not item.get("download_probe_verified"):
                continue
            crop = Path(args.output_dir) / (item["id"] + "_vertical_crop.jpg")
            destination = Path(args.output_dir) / (item["id"] + "_quran_overlay.jpg")
            composite_overlay_preview(crop, args.overlay_frame, destination)
            overlaid_items.append({**item, "preview_path": str(destination),
                                   "description": item["description"] + " — Quran text overlay"})
        overlay_sheet = Path(args.output_dir) / "background_quran_overlay_contact_sheet.jpg"
        build_contact_sheet(overlaid_items, overlay_sheet)
        report["quran_overlay_contact_sheet"] = str(overlay_sheet)
        report["quran_overlay_frame_source"] = str(args.overlay_frame)
        report["overlay_legibility_review_required"] = True
        (Path(args.output_dir) / "background_review_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Prepared {report['candidate_count']} review-only background crops from {report['source_candidate_count']} source candidates.")
    if report["unresolved_count"]:
        print(f"{report['unresolved_count']} candidates still need verified direct media URLs.")
    print("No background was activated; explicit user approval is still required.")


if __name__ == "__main__":
    main()
