"""Safe Quran-only daily orchestrator for a manual-review batch.

Preflight is read-only. Rendering is opt-in and only starts after all three
Quran manifests pass validation. Dua/dhikr remain optional future extensions.
No Telegram or TikTok actions.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from content_rotation import choose_manifests
from render_quran_review_batch import render_batch
from validate_content_manifest import validate_content_manifest

DAILY_CONTENT_TYPE = "quran"
DEFAULT_DAILY_VIDEO_COUNT = 3


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}.")
    return value


def load_history(path: Path) -> dict:
    if not path.exists():
        return {"content": []}
    value = read_json(path)
    if not isinstance(value.get("content", []), list):
        raise SystemExit("History field 'content' must be a list.")
    return value


def build_plan(
    content_dir: Path, history: dict, day_key: str,
    video_count: int = DEFAULT_DAILY_VIDEO_COUNT,
) -> list[dict]:
    """Validate a Quran-only daily batch; duas/dhikr are optional future extensions."""
    recent = list(history.get("content", []))
    manifest_paths = choose_manifests(
        content_dir, DAILY_CONTENT_TYPE, video_count, recent, day_key
    )
    plan: list[dict] = []
    for manifest_path in manifest_paths:
        manifest = read_json(manifest_path)
        if manifest.get("content_type") != DAILY_CONTENT_TYPE:
            raise SystemExit(
                f"Manifest {manifest_path} must explicitly declare content_type={DAILY_CONTENT_TYPE}."
            )
        validate_content_manifest(manifest)
        publishing = manifest.get("publishing", {})
        if publishing.get("approval_required") is not True:
            raise SystemExit(f"Manual review must be required: {manifest_path}")
        if publishing.get("auto_publish", False):
            raise SystemExit(f"Auto-publish must remain disabled: {manifest_path}")
        item_id = manifest.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise SystemExit(f"Manifest has no stable id: {manifest_path}")
        plan.append({
            "content_type": DAILY_CONTENT_TYPE,
            "manifest": str(manifest_path),
            "content_id": item_id,
        })
        recent.append(item_id)
    return plan


def render_plan(plan: list[dict], output_dir: Path) -> list[dict]:
    """Render the whole selected batch through the original diversity-checking batch renderer."""
    if len(plan) != DEFAULT_DAILY_VIDEO_COUNT:
        raise ValueError(
            f"Daily Quran rendering requires exactly {DEFAULT_DAILY_VIDEO_COUNT} distinct manifests; "
            f"received {len(plan)}."
        )
    manifest_paths = [Path(item["manifest"]) for item in plan]
    result = render_batch(manifest_paths, output_dir)
    videos = result.get("videos", [])
    if result.get("status") != "multi_video_batch_rendered_for_manual_review":
        raise RuntimeError("Batch renderer did not confirm a complete manual-review batch.")
    if len(videos) != len(plan):
        raise RuntimeError("Batch renderer returned an incomplete video list.")
    rendered = []
    for item, video in zip(plan, videos):
        output = Path(video["video"])
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"Renderer did not produce a non-empty MP4: {output}")
        rendered.append({**item, "output": str(output)})
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coordinate a Quran-only daily review batch."
    )
    parser.add_argument("--content-dir", type=Path, default=Path("content"))
    parser.add_argument("--history", type=Path, default=Path("content/rotation_history.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/daily"))
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--video-count", type=int, default=DEFAULT_DAILY_VIDEO_COUNT)
    parser.add_argument(
        "--render", action="store_true",
        help="Render only after the full Quran batch passes preflight.",
    )
    args = parser.parse_args()

    try:
        history = load_history(args.history)
        plan = build_plan(args.content_dir, history, args.day, args.video_count)
    except (FileNotFoundError, ValueError, LookupError, SystemExit) as exc:
        print(json.dumps({
            "status": "blocked",
            "stage": "preflight",
            "reason": str(exc),
            "required_types": [DAILY_CONTENT_TYPE],
            "required_video_count": args.video_count,
            "rendered": [],
            "telegram_sent": False,
            "tiktok_published": False,
        }, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps({
        "status": "ready_to_render" if args.render else "preflight_passed",
        "day": args.day,
        "videos": plan,
        "telegram_sent": False,
        "tiktok_published": False,
    }, ensure_ascii=False, indent=2))
    if not args.render:
        print("Preflight only. Use --render to create the Quran review batch.")
        return 0

    rendered = render_plan(plan, args.output_dir)
    # Rendering is not delivery. Do not consume rotation history here:
    # the production Telegram workflow records ayahs only after API confirmation.
    print(json.dumps({
        "status": "rendered_for_manual_review",
        "videos": rendered,
        "history_updated": False,
        "telegram_sent": False,
        "tiktok_published": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
