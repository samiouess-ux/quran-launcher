"""Render a batch of distinct, pre-approved Quran manifests for manual review.

This production entry point accepts only individually approved manifests, checks
surah and visual diversity before rendering, and never sends or publishes files.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from validate_content_manifest import validate_content_manifest


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load manifest {path}: {exc}") from exc
    validate_content_manifest(data)
    if data.get("content_type", "quran") != "quran":
        raise ValueError(f"Only Quran manifests are accepted: {path}")
    if data.get("publishing", {}).get("approval_required") is not True:
        raise ValueError(f"Manual review gate missing: {path}")
    if data.get("publishing", {}).get("auto_publish", False):
        raise ValueError(f"Auto-publishing is forbidden: {path}")
    return data


def render_batch(manifest_paths: list[Path], output_dir: Path,
                 renderer: Path = Path("src/render_video_scenes.py")) -> dict:
    if len(manifest_paths) < 2:
        raise ValueError("A real multi-video batch must contain at least two manifests.")
    manifests = [(path, load_manifest(path)) for path in manifest_paths]
    surahs = [int(data["source"]["surah_number"]) for _, data in manifests]
    if len(set(surahs)) != len(surahs):
        raise ValueError("Batch must contain distinct surahs; repeated examples are blocked.")
    visual_signatures = []
    for _, data in manifests:
        visual = data["visual"]
        background = visual.get("approved_background_url") or visual["background_candidate"]["direct_video_url"]
        visual_signatures.append((visual.get("template", "ornate_gold_classic"), background))
    if len(set(visual_signatures)) != len(visual_signatures):
        raise ValueError("Every video in the batch must have a distinct approved template/background combination.")

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for (manifest_path, data), surah in zip(manifests, surahs):
        content_id = str(data.get("id") or f"surah-{surah:03d}")
        safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in content_id)
        output = output_dir / f"quran-{surah:03d}-{safe_id}.mp4"
        if output.exists():
            raise ValueError(f"Refusing to overwrite an existing review video: {output}")
        subprocess.run(
            [sys.executable, str(renderer), "--manifest", str(manifest_path),
             "--output", str(output)],
            check=True,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"Renderer produced no MP4 for {manifest_path}")
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(output)],
            check=True, capture_output=True, text=True,
        )
        streams = json.loads(probe.stdout).get("streams", [])
        if not streams or streams[0].get("width") != 1080 or streams[0].get("height") != 1920:
            raise RuntimeError(f"Output is not 1080x1920 vertical video: {output}")
        results.append({
            "surah_number": surah,
            "manifest": str(manifest_path),
            "video": str(output),
            "bytes": output.stat().st_size,
            "status": "rendered_for_manual_review",
        })
    return {
        "status": "multi_video_batch_rendered_for_manual_review",
        "video_count": len(results),
        "distinct_surah_count": len(set(surahs)),
        "videos": results,
        "telegram_sent": False,
        "tiktok_published": False,
        "approval_required_before_publishing": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", action="append", type=Path, required=True,
                        help="Repeat once per distinct, fully approved Quran manifest.")
    parser.add_argument("--output-dir", type=Path, default=Path("output/quran-review-batch"))
    args = parser.parse_args()
    result = render_batch(args.manifest, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
