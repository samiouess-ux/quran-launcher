#!/usr/bin/env python3
"""Build a review-only HTML gallery/contact sheet from checked-in Quran photo assets.

This tool never changes approval flags or production manifests.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    candidates = catalog.get("candidates", [])
    if not candidates:
        raise SystemExit("No photo candidates found.")

    out = args.output_dir
    thumbs = out / "thumbnails"
    thumbs.mkdir(parents=True, exist_ok=True)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title_font = ImageFont.truetype(font_path, 18)
    small_font = ImageFont.truetype(font_path, 13)

    cards = []
    sheet_tiles = []
    for index, item in enumerate(candidates, start=1):
        candidate_id = str(item.get("id", f"candidate-{index}"))
        rel = str(item.get("local_path", ""))
        source = args.repo_root / "engine" / rel
        status = "READY"
        thumb_name = f"{candidate_id}.jpg"
        thumb_path = thumbs / thumb_name
        width = height = 0
        if not rel or not source.is_file() or source.stat().st_size < 1024:
            status = "MISSING_OR_EMPTY"
        else:
            try:
                with Image.open(source) as image:
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    width, height = image.size
                    # Match the intended 9:16 framing without modifying source assets.
                    crop = ImageOps.fit(image, (360, 640), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    crop.save(thumb_path, "JPEG", quality=88, optimize=True)
                    tile = Image.new("RGB", (380, 700), (15, 20, 28))
                    tile.paste(crop, (10, 10))
                    draw = ImageDraw.Draw(tile)
                    draw.text((12, 655), f"{index:02d}. {candidate_id}", font=title_font, fill="white")
                    draw.text((12, 680), f"{width}x{height} | {status}", font=small_font, fill=(238, 211, 153))
                    sheet_tiles.append(tile)
            except Exception as exc:
                status = "UNREADABLE"
                item["review_error"] = str(exc)[:180]

        cards.append({
            "index": index,
            "id": candidate_id,
            "description": str(item.get("description", "")),
            "creator": str(item.get("creator", "")),
            "source_page_url": str(item.get("source_page_url", "")),
            "license": str(item.get("license", "")),
            "local_path": rel,
            "status": status,
            "width": width,
            "height": height,
            "thumbnail": f"thumbnails/{thumb_name}" if status == "READY" else "",
            "production_enabled": False,
            "user_approved": bool(item.get("user_approved", False)),
        })

    # A single long contact sheet plus individual thumbnails for phone-friendly review.
    cols = 3
    rows = (len(sheet_tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 380, max(1, rows) * 700), (9, 13, 20))
    for i, tile in enumerate(sheet_tiles):
        sheet.paste(tile, ((i % cols) * 380, (i // cols) * 700))
    sheet.save(out / "photo_contact_sheet.jpg", "JPEG", quality=88, optimize=True)

    html_cards = []
    for card in cards:
        if card["thumbnail"]:
            visual = f'<img loading="lazy" src="{html.escape(card["thumbnail"])}" alt="{html.escape(card["description"])}">'
        else:
            visual = '<div class="missing">Image file missing or unreadable</div>'
        source_link = ""
        if card["source_page_url"].startswith("https://"):
            source_link = f'<a href="{html.escape(card["source_page_url"], quote=True)}" target="_blank" rel="noopener">Source / licence page</a>'
        html_cards.append(f"""
        <article class="card">
          {visual}
          <div class="meta">
            <b>{card['index']:02d}. {html.escape(card['id'])}</b>
            <p>{html.escape(card['description'])}</p>
            <small>{card['width']} × {card['height']} · {card['status']}</small>
            <p>{source_link}</p>
            <small>Preview only — not approved for production</small>
          </div>
        </article>""")

    ready = sum(c["status"] == "READY" for c in cards)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quran background photo review</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#10151d;color:#f4f4f4;font:16px system-ui,sans-serif}}
header{{padding:20px;position:sticky;top:0;background:#10151dee;backdrop-filter:blur(8px);z-index:2}}
h1{{font-size:21px;margin:0 0 8px}}.note{{color:#e9c77d;font-size:14px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;padding:14px}}
.card{{background:#202936;border-radius:12px;overflow:hidden}}img{{display:block;width:100%;aspect-ratio:9/16;object-fit:cover;background:#080b10}}
.meta{{padding:12px}}p{{margin:8px 0}}small{{color:#c6cfdb}}a{{color:#e9c77d}}.missing{{aspect-ratio:9/16;display:grid;place-items:center;color:#ffbd9f;padding:20px;text-align:center}}
</style></head><body>
<header><h1>Quran background photos — visual review</h1>
<div>{ready} of {len(cards)} candidates have readable local image files.</div>
<div class="note">Review gallery only. No image is approved or enabled for production by this workflow.</div>
<p><a href="photo_contact_sheet.jpg">Open full contact sheet</a></p></header>
<main>{''.join(html_cards)}</main></body></html>"""
    (out / "index.html").write_text(page, encoding="utf-8")
    report = {
        "candidate_count": len(cards),
        "ready_count": ready,
        "missing_or_unreadable_count": len(cards) - ready,
        "production_enabled": False,
        "user_approval_required": True,
        "items": cards,
    }
    (out / "photo_review_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Photo review package: {ready}/{len(cards)} readable local images; production remains disabled.")


if __name__ == "__main__":
    main()
